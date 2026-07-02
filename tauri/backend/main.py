from pathlib import Path
import re
import os
import sys
import threading
import time
import json
from typing import Any, List, Dict
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BACKEND_HOST = "127.0.0.1"
DEFAULT_BACKEND_PORT = 8000

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

app = FastAPI(title="Commodity Lab Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "tauri://localhost",
    ],
    allow_origin_regex=r"http://(127\.0\.0\.1|localhost):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from core.learner_profile import LearnerProfile

    _LEARNER_PROFILE = LearnerProfile.create_default()
except Exception:
    _LEARNER_PROFILE = None


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
    strategy_legs: list[dict[str, Any]] = Field(default_factory=list)
    rationale: str = ""


class AdvisorRequest(AttemptRequest):
    evaluation: dict[str, Any]


class ExamRequest(BaseModel):
    scenario_id: str
    locale: str = "en"
    attempt_history: list[dict[str, Any]] = Field(default_factory=list)
    curriculum_context: dict[str, Any] | None = None


class AITrainingRequest(BaseModel):
    capability: str
    locale: str = "en"
    scenario_id: str | None = None
    source: str = "ai_generated"
    evaluation: dict[str, Any] | None = None
    order: dict[str, Any] | None = None
    rationale: str = ""
    attempt_history: list[dict[str, Any]] = Field(default_factory=list)
    event_context: str = ""
    concept: str = ""
    curriculum_context: dict[str, Any] | None = None
    commercial_goal: str = ""
    learner_level: str = "intermediate"
    market_context: dict[str, Any] | None = None
    user_request: str = ""
    learner_message: str = ""


class TrainingCaseGenerateRequest(BaseModel):
    template_id: str
    locale: str = "en"
    user_request: str = ""
    knowledge_coverage: list[dict[str, Any]] = Field(default_factory=list)
    gas_trading_models: list[dict[str, Any]] = Field(default_factory=list)


class LiveAssistantRequest(BaseModel):
    locale: str = "en"
    message: str
    workspace_state: dict[str, Any] = Field(default_factory=dict)


class HainengProviderSettingsRequest(BaseModel):
    api_key: str
    provider: str = "haineng"
    base_url: str = ""
    model: str = "DeepSeek-V4-Flash"
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


def _ensure_stdio_for_windowed_runtime() -> None:
    """PyInstaller windowed apps can start with missing stdio handles on Windows."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def _start_parent_watchdog() -> None:
    parent_pid_text = os.getenv("COMMODITY_LAB_PARENT_PID", "").strip()
    if not parent_pid_text:
        return
    try:
        parent_pid = int(parent_pid_text)
    except ValueError:
        return

    def exit_when_windows_parent_exits() -> None:
        import ctypes
        from ctypes import wintypes

        synchronize = 0x00100000
        infinite = 0xFFFFFFFF
        wait_object_0 = 0x00000000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(synchronize, False, parent_pid)
        if not handle:
            os._exit(0)
        try:
            result = kernel32.WaitForSingleObject(wintypes.HANDLE(handle), infinite)
            if result == wait_object_0:
                os._exit(0)
        finally:
            kernel32.CloseHandle(wintypes.HANDLE(handle))

    def exit_when_parent_pid_disappears() -> None:
        while True:
            try:
                os.kill(parent_pid, 0)
            except OSError:
                os._exit(0)
            time.sleep(2)

    target = exit_when_windows_parent_exits if os.name == "nt" else exit_when_parent_pid_disappears
    threading.Thread(target=target, name="commodity-lab-parent-watchdog", daemon=True).start()


def _apply_profile_update(evaluation: dict[str, Any]) -> dict[str, Any] | None:
    if _LEARNER_PROFILE is None:
        return None
    return _LEARNER_PROFILE.apply_evaluation(evaluation)


def _profile_payload() -> dict[str, Any]:
    return _LEARNER_PROFILE.as_dict() if _LEARNER_PROFILE is not None else {"profile_available": False}


@app.get("/api/ping", response_model=PingResp)
async def ping():
    return {"message": "pong from Tauri Python backend"}


@app.get("/api/health")
def health():
    return {"ok": True, "service": "commodity-lab-backend"}


@app.get("/api/v1/version")
def v1_version():
    return {
        "current_version": "1.1.7",
        "organization": "天然气中心",
        "project_lead": "杨敏",
        "repository": "AlexYuhuFeng/Commodity-Lab",
    }


@app.get("/api/v1/update-check")
def v1_update_check():
    current_version = "1.1.7"
    request = Request(
        "https://api.github.com/repos/AlexYuhuFeng/Commodity-Lab/releases/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Commodity-Lab"},
    )
    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Update check failed: {exc}") from exc

    tag = str(payload.get("tag_name", "")).lstrip("v")
    release_url = payload.get("html_url", "")
    assets = [asset.get("name", "") for asset in payload.get("assets", []) if isinstance(asset, dict)]
    return {
        "current_version": current_version,
        "latest_version": tag or current_version,
        "up_to_date": not tag or tag == current_version,
        "release_url": release_url,
        "assets": assets,
    }


@app.get("/api/v1/catalog")
def v1_catalog(locale: str = "en"):
    from core.energy_models import list_ai_capabilities, list_energy_modules

    return {
        "modules": list_energy_modules(locale=locale),
        "ai_capabilities": list_ai_capabilities(locale=locale),
        "current_focus": {"commodity": "natural_gas", "region": "europe", "status": "enabled"},
        "future_modules": ["crude_oil", "oil_products", "carbon", "power"],
    }


@app.get("/api/v1/business-templates")
def v1_business_templates(locale: str = "en"):
    from core.training_templates import list_business_groups, list_knowledge_points, list_templates

    return {
        "groups": list_business_groups(locale=locale),
        "knowledge_points": list_knowledge_points(locale=locale),
        "templates": list_templates(locale=locale),
    }


@app.get("/api/v1/learner-profile")
def v1_learner_profile():
    return _profile_payload()


@app.get("/api/v1/learning-journey")
def v1_learning_journey(locale: str = "en"):
    from core.learning_journey import build_learning_journey

    return build_learning_journey(_profile_payload(), locale=locale)


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
def simulate_portfolio(orders: List[OrderSpec]):
    from core.hedge import VirtualOrder, simulate_virtual_order, score_hedge_result
    from core.hedge import summarize_hedge_performance
    from core.db import default_db_path, get_conn

    results = []
    con = get_conn(default_db_path(PROJECT_ROOT))
    for o in orders:
        tk = (o.ticker or "").strip()
        if not tk:
            raise HTTPException(status_code=400, detail="Ticker missing in order")
        try:
            prices = con.execute(
                "SELECT date, open, high, low, close FROM prices WHERE ticker = ? ORDER BY date",
                [tk],
            ).df()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Local training price fetch failed for {tk}: {exc}")
        if prices.empty:
            raise HTTPException(status_code=404, detail=f"No local training prices available for {tk}.")

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
        from core.haineng_client import HainengClient

        client = HainengClient()
        if not client.is_configured():
            raise HTTPException(status_code=428, detail="AI provider is required for AI mode.")
        history_text = "\n".join(
            f"Q: {entry.get('question', '')}\nA: {entry.get('answer', '')}"
            for entry in (history or [])[-5:]
            if isinstance(entry, dict)
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Haineng, an AI energy trading training coach for Commodity Lab. "
                    "Provide practical hedge training guidance grounded in the supplied context. "
                    "Do not request, reveal, or repeat credentials."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Mode: {mode}\n"
                    f"Question: {question}\n"
                    f"Context: {context or 'No additional context provided.'}\n"
                    f"Recent exchange:\n{history_text or 'None'}"
                ),
            },
        ]
        answer = client.complete(messages)
        return {"answer": answer}
    except HTTPException:
        raise
    except Exception as exc:
        raise _haineng_failure(exc) from exc


def _parse_json_response(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start >= 0 and end > start:
            return json.loads(stripped[start : end + 1])
        raise


def _sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _unknown_scenario(exc: KeyError) -> HTTPException:
    detail = exc.args[0] if exc.args else str(exc)
    return HTTPException(status_code=404, detail=str(detail))


def _haineng_failure(exc: Exception) -> HTTPException:
    message = _redact_provider_error(str(exc))
    return HTTPException(
        status_code=502,
        detail={"code": "ai_provider_request_failed", "message": "AI provider request failed.", "provider_message": message},
    )


def _redact_provider_error(message: str) -> str:
    redacted = re.sub(
        r"(?i)\b(api[\s_-]?key|apikey|authorization|password|secret|token)\s*[:=]\s*[^,\s;\}\]]+",
        lambda match: f"{match.group(1)}=[REDACTED]",
        message,
    )
    redacted = re.sub(r"(?i)\bsk-[A-Za-z0-9_-]{8,}\b", "[REDACTED]", redacted)
    redacted = re.sub(r"\*{2,}[A-Za-z0-9_-]{2,}", "[REDACTED]", redacted)
    return redacted


def _require_haineng_client():
    from core.haineng_client import HainengClient

    client = HainengClient()
    if not client.is_configured():
        raise HTTPException(status_code=428, detail="AI provider is required for AI Full Power Mode.")
    return client


def _scenario_bundle(scenario_id: str | None, locale: str, source: str, provided_market: dict[str, Any] | None):
    from core.gas_scenarios import get_capacity_context, get_market_context, get_scenario, list_scenarios

    scenario_list = list_scenarios(locale=locale)
    sid = scenario_id or (scenario_list[0]["id"] if scenario_list else None)
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
    from core.haineng_client import HainengClient, provider_catalog

    client = HainengClient()
    return {
        "haineng": client.health_check(),
        "ai_providers": provider_catalog(),
        "training_data": {"mode": "ai_generated", "configured": client.is_configured()},
    }


@app.post("/api/v1/provider-settings")
def v1_provider_settings(payload: HainengProviderSettingsRequest):
    from core.haineng_client import (
        HainengClient,
        HainengSettings,
        normalize_provider,
        provider_catalog,
        save_persisted_settings,
        set_runtime_settings,
    )

    if not payload.api_key.strip():
        raise HTTPException(status_code=400, detail="AI provider API key is required.")
    provider = normalize_provider(payload.provider, payload.base_url)
    catalog = provider_catalog()
    provider_config = catalog.get(provider) or catalog["haineng"]
    settings = HainengSettings(
        api_key=payload.api_key.strip(),
        provider=provider,
        base_url="",
        model=provider_config["default_model"],
        streaming=payload.streaming,
        function_calling=payload.function_calling,
    )
    if not HainengClient(settings).is_configured():
        raise HTTPException(status_code=400, detail="AI provider base URL is required.")
    save_persisted_settings(settings)
    set_runtime_settings(settings)
    return {"haineng": HainengClient().health_check()}


@app.get("/api/v1/scenarios")
def v1_list_scenarios(locale: str = "en"):
    from core.gas_scenarios import list_categories, list_scenarios

    return {"categories": list_categories(locale=locale), "scenarios": list_scenarios(locale=locale)}


@app.get("/api/v1/scenarios/{scenario_id}/context")
def v1_scenario_context(scenario_id: str, locale: str = "en", source: str = "ai_generated_training"):
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
    order = _primary_order_from_strategy(payload.order, payload.strategy_legs)
    evaluation = evaluate_attempt(scenario, capacity, order, payload.rationale)
    if payload.strategy_legs:
        evaluation.setdefault("metrics", {}).update(_strategy_leg_metrics(payload.strategy_legs))
        evaluation["strategy_legs"] = payload.strategy_legs
    profile = _apply_profile_update(evaluation)
    journey = None
    if profile is not None:
        from core.learning_journey import build_learning_journey
        journey = build_learning_journey(profile, locale=payload.locale)
    return {"evaluation": evaluation, "profile": profile, "journey": journey}


def _primary_order_from_strategy(order: dict[str, Any], strategy_legs: list[dict[str, Any]]) -> dict[str, Any]:
    if not strategy_legs:
        return order
    preferred_types = {"swap", "future", "basis", "paper"}
    preferred_leg = next(
        (
            leg
            for leg in strategy_legs
            if str(leg.get("leg_type", leg.get("type", ""))).strip().lower() in preferred_types
        ),
        strategy_legs[0],
    )
    return {
        "side": preferred_leg.get("side", order.get("side")),
        "quantity": preferred_leg.get("quantity", order.get("quantity")),
        "hedge_type": preferred_leg.get("hedge_type", order.get("hedge_type")),
        "price": preferred_leg.get("price", order.get("price")),
    }


def _strategy_leg_metrics(strategy_legs: list[dict[str, Any]]) -> dict[str, Any]:
    buckets = {"physical": 0, "paper": 0, "fx": 0, "capacity": 0}
    total_quantity = 0.0
    for leg in strategy_legs:
        leg_type = str(leg.get("leg_type", leg.get("type", ""))).strip().lower()
        quantity = leg.get("quantity")
        try:
            total_quantity += float(quantity)
        except (TypeError, ValueError):
            pass
        if leg_type in {"physical", "gsa", "lng", "efet"}:
            buckets["physical"] += 1
        elif leg_type in {"swap", "future", "basis", "paper", "option"}:
            buckets["paper"] += 1
        elif leg_type == "fx":
            buckets["fx"] += 1
        elif leg_type == "capacity":
            buckets["capacity"] += 1
    return {
        "strategy_leg_count": len(strategy_legs),
        "physical_leg_count": buckets["physical"],
        "paper_leg_count": buckets["paper"],
        "fx_leg_count": buckets["fx"],
        "capacity_leg_count": buckets["capacity"],
        "strategy_total_quantity": round(total_quantity, 4),
    }


@app.post("/api/v1/ai/generate")
def v1_ai_generate(payload: AITrainingRequest):
    from core.haineng_client import (
        build_advisor_messages,
        build_case_generation_messages,
        build_concept_tutor_messages,
        build_event_drill_messages,
        build_exam_messages,
        build_socratic_coach_messages,
        build_trade_playbook_messages,
    )

    client = _require_haineng_client()
    scenario, context = _scenario_bundle(payload.scenario_id, payload.locale, payload.source, payload.market_context)
    capability = payload.capability.strip().lower()

    if capability == "advisor_review":
        messages = build_advisor_messages(payload.locale, scenario, payload.evaluation or {}, payload.rationale)
    elif capability == "exam":
        messages = build_exam_messages(payload.locale, scenario, payload.attempt_history, payload.curriculum_context)
    elif capability == "case_generation":
        enriched_context = {**context, "user_request": payload.user_request}
        messages = build_case_generation_messages(payload.locale, scenario, enriched_context, payload.learner_level)
    elif capability == "event_drill":
        messages = build_event_drill_messages(payload.locale, scenario, payload.event_context or payload.user_request, context)
    elif capability == "concept_tutor":
        messages = build_concept_tutor_messages(payload.locale, payload.concept or payload.user_request, scenario, payload.learner_level)
    elif capability == "trade_playbook":
        messages = build_trade_playbook_messages(payload.locale, scenario, context, payload.commercial_goal or payload.user_request)
    elif capability == "socratic_coach":
        messages = build_socratic_coach_messages(
            payload.locale,
            scenario,
            payload.learner_message or payload.user_request or payload.rationale,
            context,
            _profile_payload(),
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported AI capability: {payload.capability}")

    try:
        answer = client.complete(messages)
    except Exception as exc:
        raise _haineng_failure(exc) from exc
    return {"capability": capability, "scenario": scenario, "answer": answer}


@app.post("/api/v1/ai/training-case")
def v1_ai_training_case(payload: TrainingCaseGenerateRequest):
    from core.haineng_client import build_training_case_messages
    from core.training_templates import get_template

    client = _require_haineng_client()
    try:
        template = get_template(payload.template_id, locale=payload.locale)
    except KeyError as exc:
        raise _unknown_scenario(exc)
    messages = build_training_case_messages(
        payload.locale,
        template,
        payload.user_request,
        knowledge_coverage=payload.knowledge_coverage,
        gas_trading_models=payload.gas_trading_models,
    )
    try:
        answer = client.complete(messages)
        case = _parse_json_response(answer)
    except Exception as exc:
        raise _haineng_failure(exc) from exc
    return {"template": template, "case": case}


@app.post("/api/v1/ai/training-case/stream")
def v1_ai_training_case_stream(payload: TrainingCaseGenerateRequest):
    def stream():
        yield _sse_event("stage", {"id": "read_template", "label": "Reading business template"})
        try:
            from core.haineng_client import build_training_case_messages
            from core.training_templates import get_template

            client = _require_haineng_client()
            template = get_template(payload.template_id, locale=payload.locale)
            yield _sse_event("template", template)
            yield _sse_event("stage", {"id": "generate_market", "label": "Generating AI training curves"})
            messages = build_training_case_messages(
                payload.locale,
                template,
                payload.user_request,
                knowledge_coverage=payload.knowledge_coverage,
                gas_trading_models=payload.gas_trading_models,
            )
            answer = client.complete(messages)
            yield _sse_event("stage", {"id": "parse_case", "label": "Building scenario, target actions, and rubric"})
            case = _parse_json_response(answer)
            yield _sse_event("case", {"template": template, "case": case})
            yield _sse_event("done", {"ok": True})
        except Exception as exc:
            yield _sse_event("error", {"message": str(_haineng_failure(exc).detail)})

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/v1/ai/live-assistant")
def v1_ai_live_assistant(payload: LiveAssistantRequest):
    from core.haineng_client import build_live_assistant_messages

    client = _require_haineng_client()
    available_actions = {
        "navigate_page": {"page": "home|caseLab|workbench|library|review|knowledge|progress|settings"},
        "generate_case": {"track_id": "foundation|procurement|sales|integrated", "template_id": "foundation_hedging_basics", "user_request": "short training goal"},
        "select_template": {"template_id": "foundation_hedging_basics", "user_request": "optional training goal"},
        "patch_case": {
            "scenario": {"title": "short title", "summary": "updated scenario summary", "exposure": {"direction": "buy|sell|spread", "risk": "key risk"}},
            "market": {"unit": "training index", "events": [{"date": "2026-01-07", "label": "event"}]},
            "target_actions": [{"leg_type": "physical|swap|basis|fx|capacity", "market": "TTF", "side": "buy|sell", "quantity": 10000, "tenor": "M+1"}],
            "rubric": [{"id": "risk", "label": "Risk explanation", "points": 25, "rule": "what earns points"}],
            "prompt": "Markdown decision task",
            "rationale": "draft rationale",
            "chart_fields": ["close", "high", "low"],
        },
        "set_market_curves": {
            "curves": [{"id": "TTF", "label": "TTF", "color": "#38bdf8", "points": [{"date": "2026-01-05", "open": 31, "high": 33, "low": 30, "close": 32}]}],
            "events": [{"date": "2026-01-07", "label": "shock"}],
            "unit": "training index",
        },
        "set_learning_goal": {"goal": "short goal", "focus": ["basis", "fx", "capacity"]},
        "set_chart_fields": {"fields": ["high", "low", "close"]},
        "set_strategy_legs": {"legs": [{"leg_type": "physical|swap|future|basis|fx|capacity|option", "market": "TTF", "side": "sell", "quantity": 10000}]},
        "fill_rationale": {"text": "string"},
        "set_exam": {"exam": "Markdown quiz content"},
        "run_ai_capability": {"capability": "concept_tutor|exam|trade_playbook|advisor_review"},
    }
    messages = build_live_assistant_messages(
        payload.locale,
        payload.message,
        payload.workspace_state,
        available_actions,
    )
    try:
        answer = client.complete(messages)
        try:
            parsed = _parse_json_response(answer)
        except Exception:
            parsed = {"answer": answer, "actions": []}
    except Exception as exc:
        raise _haineng_failure(exc) from exc
    return {
        "answer": parsed.get("answer", ""),
        "actions": parsed.get("actions", []),
    }


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
            curriculum_context=payload.curriculum_context,
        )
    )
    return {"exam": result["answer"]}


if __name__ == "__main__":
    import uvicorn
    _ensure_stdio_for_windowed_runtime()
    _start_parent_watchdog()
    uvicorn.run(app, host=_backend_host(), port=_backend_port(), log_config=None)
