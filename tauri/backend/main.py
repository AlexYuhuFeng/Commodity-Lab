from pathlib import Path
import re
import os
import sys
from typing import Any, List, Dict

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BACKEND_HOST = "127.0.0.1"
DEFAULT_BACKEND_PORT = 8000

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

app = FastAPI(title="Commodity Lab Backend")


class PingResp(BaseModel):
    message: str


class OrderSpec(BaseModel):
    order_id: str
    ticker: str
    side: str
    quantity: float
    open_date: str
    close_date: str
    open_price: float | None = None
    close_price: float | None = None
    hedge_type: str | None = "short_hedge"


class AttemptRequest(BaseModel):
    scenario_id: str
    locale: str = "en"
    order: dict[str, Any]
    rationale: str = ""


class AdvisorRequest(AttemptRequest):
    evaluation: dict[str, Any]


class ExamRequest(BaseModel):
    scenario_id: str
    locale: str = "en"
    attempt_history: list[dict[str, Any]] = Field(default_factory=list)


class AITrainingRequest(BaseModel):
    capability: str
    locale: str = "en"
    scenario_id: str | None = None
    source: str = "yfinance"
    evaluation: dict[str, Any] | None = None
    order: dict[str, Any] | None = None
    rationale: str = ""
    attempt_history: list[dict[str, Any]] = Field(default_factory=list)
    event_context: str = ""
    concept: str = ""
    commercial_goal: str = ""
    learner_level: str = "intermediate"
    market_context: dict[str, Any] | None = None
    user_request: str = ""


class HainengProviderSettingsRequest(BaseModel):
    api_key: str
    base_url: str
    model: str = "V4-Flash"
    streaming: bool = False
    function_calling: bool = True


def _backend_host() -> str:
    return os.getenv("COMMODITY_LAB_BACKEND_HOST", DEFAULT_BACKEND_HOST).strip() or DEFAULT_BACKEND_HOST


def _backend_port() -> int:
    raw_value = os.getenv("COMMODITY_LAB_BACKEND_PORT", str(DEFAULT_BACKEND_PORT)).strip()
    try:
        port = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"Invalid COMMODITY_LAB_BACKEND_PORT: {raw_value!r}") from exc
    if not 1 <= port <= 65535:
        raise RuntimeError(f"COMMODITY_LAB_BACKEND_PORT out of range: {port}")
    return port


@app.get("/api/ping", response_model=PingResp)
async def ping():
    return {"message": "pong from Tauri Python backend"}


@app.get("/api/health")
def health():
    return {"ok": True, "service": "commodity-lab-backend"}


@app.get("/api/instruments")
def list_instruments(limit: int = Query(default=100, ge=1, le=1000)):
    from core.db import default_db_path, get_conn, init_db

    db_path = default_db_path(PROJECT_ROOT)
    con = get_conn(db_path)
    init_db(con)
    df = con.execute(
        "SELECT ticker, name, exchange, currency, unit, is_watched FROM instruments LIMIT ?",
        [limit],
    ).df()
    return df.to_dict(orient="records")


@app.post("/api/simulate")
def simulate_portfolio(orders: List[OrderSpec], source: str = "yfinance"):
    from core.hedge import VirtualOrder, simulate_virtual_order, score_hedge_result
    from core.hedge import summarize_hedge_performance

    results = []
    for o in orders:
        tk = (o.ticker or "").strip()
        if not tk:
            raise HTTPException(status_code=400, detail="Ticker missing in order")
        try:
            if source == "platts":
                from core.platts_connector import fetch_platts_history
                prices = fetch_platts_history(tk)
            else:
                from core.yf_prices import fetch_history_daily
                prices = fetch_history_daily(tk)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Price fetch failed for {tk}: {exc}")

        vo = VirtualOrder(
            order_id=o.order_id,
            ticker=tk,
            side=o.side,
            quantity=o.quantity,
            open_date=pd.to_datetime(o.open_date).date(),
            close_date=pd.to_datetime(o.close_date).date(),
            open_price=o.open_price,
            close_price=o.close_price,
            hedge_type=o.hedge_type or "short_hedge",
        )
        try:
            row = simulate_virtual_order(prices, vo)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        row["score"] = score_hedge_result(row)
        results.append(row)

    df = pd.DataFrame(results)
    perf = summarize_hedge_performance([], df)
    overall = float(df["score"].mean()) if not df.empty else 0.0
    return {"results": df.to_dict(orient="records"), "summary": perf, "score": overall}


@app.post("/api/score_portfolio")
def score_portfolio_endpoint(rows: List[Dict]):
    from core.hedge import score_portfolio

    df = pd.DataFrame(rows)
    try:
        score = score_portfolio(df)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"score": score}


@app.post("/api/assistant")
def assistant_query(payload: Dict):
    question = payload.get("question", "")
    mode = payload.get("mode", "Performance review")
    context = payload.get("context")
    history = payload.get("history")
    try:
        from core.deepseek import ask_deepseek
        answer = ask_deepseek(question, context=context, mode=mode, history=history)
        return {"answer": answer}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _platts_is_configured() -> bool:
    return any(
        bool(os.getenv(name, "").strip())
        for name in ("PLATTS_API_KEY", "PLATTS_KEY", "SPGLOBAL_API_KEY", "SP_GLOBAL_API_KEY")
    )


def _unknown_scenario(exc: KeyError) -> HTTPException:
    detail = exc.args[0] if exc.args else str(exc)
    return HTTPException(status_code=404, detail=str(detail))


def _haineng_failure(exc: Exception) -> HTTPException:
    message = re.sub(
        r"(?i)\b(api[_-]?key|apikey|authorization|password|secret|token)\s*[:=]\s*[^,\s;]+",
        r"\1=[REDACTED]",
        str(exc),
    )
    return HTTPException(
        status_code=502,
        detail={"code": "haineng_request_failed", "message": "海能 request failed.", "provider_message": message},
    )


def _require_haineng_client():
    from core.haineng_client import HainengClient

    client = HainengClient()
    if not client.is_configured():
        raise HTTPException(status_code=428, detail="海能 is required for AI Full Power Mode.")
    return client


def _scenario_bundle(scenario_id: str | None, locale: str, source: str, provided_market: dict[str, Any] | None):
    from core.gas_scenarios import get_capacity_context, get_market_context, get_scenario, list_scenarios

    sid = scenario_id or (list_scenarios(locale=locale)[0]["id"] if list_scenarios(locale=locale) else None)
    if not sid:
        raise HTTPException(status_code=404, detail="No scenario available.")
    try:
        scenario = get_scenario(sid, locale=locale)
        market = provided_market or get_market_context(sid, source=source)
        capacity = get_capacity_context(sid)
    except KeyError as exc:
        raise _unknown_scenario(exc)
    return scenario, {"market": market, "capacity": capacity}


@app.get("/api/v1/provider-status")
def v1_provider_status():
    from core.haineng_client import HainengClient

    platts_configured = _platts_is_configured()
    return {
        "haineng": HainengClient().health_check(),
        "platts": {"configured": platts_configured},
        "data_sources": [
            {"id": "platts", "label": "Platts", "configured": platts_configured},
            {"id": "yfinance", "label": "Yahoo Finance", "configured": True},
            {"id": "simulated", "label": "Simulated", "configured": True},
        ],
    }


@app.post("/api/v1/provider-settings")
def v1_provider_settings(payload: HainengProviderSettingsRequest):
    from core.haineng_client import HainengClient, HainengSettings, set_runtime_settings

    if not payload.api_key.strip() or not payload.base_url.strip():
        raise HTTPException(status_code=400, detail="海能 API key and base URL are required.")
    set_runtime_settings(
        HainengSettings(
            api_key=payload.api_key.strip(),
            base_url=payload.base_url.strip(),
            model=payload.model.strip() or "V4-Flash",
            streaming=payload.streaming,
            function_calling=payload.function_calling,
        )
    )
    return {"haineng": HainengClient().health_check()}


@app.get("/api/v1/scenarios")
def v1_list_scenarios(locale: str = "en"):
    from core.gas_scenarios import list_categories, list_scenarios

    return {"categories": list_categories(locale=locale), "scenarios": list_scenarios(locale=locale)}


@app.get("/api/v1/scenarios/{scenario_id}/context")
def v1_scenario_context(scenario_id: str, locale: str = "en", source: str = "sample"):
    from core.gas_scenarios import get_capacity_context, get_market_context, get_scenario

    try:
        scenario = get_scenario(scenario_id, locale=locale)
        market = get_market_context(scenario_id, source=source)
        capacity = get_capacity_context(scenario_id)
    except KeyError as exc:
        raise _unknown_scenario(exc)
    return {"scenario": scenario, "market": market, "capacity": capacity}


@app.post("/api/v1/attempts/evaluate")
def v1_evaluate_attempt(payload: AttemptRequest):
    from core.gas_scenarios import get_capacity_context, get_scenario
    from core.learning_session import evaluate_attempt

    try:
        scenario = get_scenario(payload.scenario_id, locale=payload.locale)
        capacity = get_capacity_context(payload.scenario_id)
    except KeyError as exc:
        raise _unknown_scenario(exc)
    return {"evaluation": evaluate_attempt(scenario, capacity, payload.order, payload.rationale)}


@app.post("/api/v1/ai/generate")
def v1_ai_generate(payload: AITrainingRequest):
    from core.haineng_client import (
        build_advisor_messages,
        build_case_generation_messages,
        build_concept_tutor_messages,
        build_event_drill_messages,
        build_exam_messages,
        build_trade_playbook_messages,
    )

    client = _require_haineng_client()
    scenario, context = _scenario_bundle(payload.scenario_id, payload.locale, payload.source, payload.market_context)
    capability = payload.capability.strip().lower()

    if capability == "advisor_review":
        messages = build_advisor_messages(payload.locale, scenario, payload.evaluation or {}, payload.rationale)
    elif capability == "exam":
        messages = build_exam_messages(payload.locale, scenario, payload.attempt_history)
    elif capability == "case_generation":
        enriched_context = {**context, "user_request": payload.user_request}
        messages = build_case_generation_messages(payload.locale, scenario, enriched_context, payload.learner_level)
    elif capability == "event_drill":
        messages = build_event_drill_messages(payload.locale, scenario, payload.event_context or payload.user_request, context)
    elif capability == "concept_tutor":
        messages = build_concept_tutor_messages(payload.locale, payload.concept or payload.user_request, scenario, payload.learner_level)
    elif capability == "trade_playbook":
        messages = build_trade_playbook_messages(payload.locale, scenario, context, payload.commercial_goal or payload.user_request)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported AI capability: {payload.capability}")

    try:
        answer = client.complete(messages)
    except Exception as exc:
        raise _haineng_failure(exc) from exc
    return {"capability": capability, "scenario": scenario, "answer": answer}


@app.post("/api/v1/advisor/review")
def v1_advisor_review(payload: AdvisorRequest):
    return v1_ai_generate(
        AITrainingRequest(
            capability="advisor_review",
            locale=payload.locale,
            scenario_id=payload.scenario_id,
            evaluation=payload.evaluation,
            order=payload.order,
            rationale=payload.rationale,
        )
    )


@app.post("/api/v1/exam/generate")
def v1_generate_exam(payload: ExamRequest):
    result = v1_ai_generate(
        AITrainingRequest(
            capability="exam",
            locale=payload.locale,
            scenario_id=payload.scenario_id,
            attempt_history=payload.attempt_history,
        )
    )
    return {"exam": result["answer"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=_backend_host(), port=_backend_port())
