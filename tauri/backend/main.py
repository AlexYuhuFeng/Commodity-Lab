from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import re
import os
import sys
import threading
import time
import json
from typing import Any, List, Dict
from urllib.request import Request, urlopen
from uuid import uuid4

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
    product_scope: str = "natural_gas"
    locale: str = "en"
    user_request: str = ""
    knowledge_coverage: list[dict[str, Any]] = Field(default_factory=list)
    gas_trading_models: list[dict[str, Any]] = Field(default_factory=list)
    market_mode: str = "ai_simulated"
    market_regime: str = "contango"
    market_seed: int = 42
    market_as_of: str | None = None
    replay_id: str | None = None


class SimulatedMarketRequest(BaseModel):
    commodity: str = "natural_gas"
    regime: str = "contango"
    seed: int = 42
    as_of: str | None = None
    locale: str = "en"
    base_price: float | None = Field(default=None, gt=0)


class ReplaySessionRequest(BaseModel):
    checkpoint: int = Field(default=0, ge=0)
    locale: str = "en"


class ReplayDecisionRequest(BaseModel):
    checkpoint: int = Field(default=0, ge=0)
    locale: str = "en"
    strategy_legs: list[dict[str, Any]] = Field(default_factory=list)
    rationale: str = Field(default="", max_length=12000)


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
        "current_version": "1.5.3",
        "organization": "天然气中心",
        "project_lead": "杨敏",
        "repository": "AlexYuhuFeng/Commodity-Lab",
    }


@app.get("/api/v1/update-check")
def v1_update_check():
    current_version = "1.5.3"
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
        "current_focus": {"commodities": ["natural_gas", "crude_oil"], "region": "europe_global", "status": "enabled"},
        "future_modules": ["oil_products", "carbon", "power"],
    }


@app.get("/api/v1/market/capabilities")
def v1_market_capabilities(locale: str = "en"):
    from core.market_learning import market_capability_catalog

    return market_capability_catalog(locale=locale)


@app.post("/api/v1/market/simulate")
def v1_market_simulate(payload: SimulatedMarketRequest):
    from core.market_learning import build_simulated_market_context

    try:
        return build_simulated_market_context(
            commodity=payload.commodity,
            regime=payload.regime,
            seed=payload.seed,
            as_of=payload.as_of,
            locale=payload.locale,
            base_price=payload.base_price,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/market/live-preview")
def v1_market_live_preview(commodity: str = "natural_gas", locale: str = "en", force_refresh: bool = False):
    from core.platts_market import PlattsError, PlattsMarketClient

    try:
        return PlattsMarketClient().fetch_market_context(
            commodity,
            locale=locale,
            force_refresh=force_refresh,
        )
    except PlattsError as exc:
        raise HTTPException(
            status_code=424,
            detail={"code": exc.code, "message": "Entitled Platts market data is unavailable."},
        ) from exc


@app.get("/api/v1/replays")
def v1_replays(locale: str = "en"):
    from core.market_learning import list_replay_events

    return {"events": list_replay_events(locale=locale)}


@app.post("/api/v1/replays/{event_id}/session")
def v1_replay_session(event_id: str, payload: ReplaySessionRequest):
    from core.market_learning import build_replay_session

    try:
        return build_replay_session(event_id, checkpoint=payload.checkpoint, locale=payload.locale)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/replays/{event_id}/decision")
def v1_replay_decision(event_id: str, payload: ReplayDecisionRequest):
    from core.market_learning import evaluate_replay_decision

    try:
        return evaluate_replay_decision(
            event_id,
            checkpoint=payload.checkpoint,
            strategy_legs=payload.strategy_legs,
            rationale=payload.rationale,
            locale=payload.locale,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
    candidates = [stripped]
    extracted = _extract_first_json_object(stripped)
    if extracted and extracted not in candidates:
        candidates.append(extracted)
    for candidate in list(candidates):
        repaired = _repair_common_llm_json(candidate)
        if repaired not in candidates:
            candidates.append(repaired)

    last_error: json.JSONDecodeError | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("AI response JSON must be an object.")
        except json.JSONDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise ValueError("AI response did not include a JSON object.")


def _positive_quantity(*values: Any) -> int | float | None:
    for value in values:
        try:
            quantity = float(value)
        except (TypeError, ValueError):
            continue
        if quantity <= 0:
            continue
        return int(quantity) if quantity.is_integer() else quantity
    return None


def _stated_case_quantity(case: dict[str, Any]) -> tuple[int | float | None, str]:
    scenario = case.get("scenario", {})
    text = "\n".join(
        str(value or "")
        for value in (case.get("prompt"), scenario.get("summary"), scenario.get("title"))
    )
    pattern = re.compile(
        r"(?<![\d.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*"
        r"(\u4e07|\u5343|million|thousand)?\s*(bbl|barrels?|\u6876|MWh|MMBtu)(?![A-Za-z])",
        flags=re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return None, ""
    quantity = float(match.group(1).replace(",", ""))
    multiplier = (match.group(2) or "").lower()
    if multiplier in {"\u4e07", "million"}:
        quantity *= 10_000 if multiplier == "\u4e07" else 1_000_000
    elif multiplier in {"\u5343", "thousand"}:
        quantity *= 1_000
    raw_unit = match.group(3).lower()
    unit = "bbl" if raw_unit in {"bbl", "barrel", "barrels", "\u6876"} else "MWh" if raw_unit == "mwh" else "MMBtu"
    return (int(quantity) if quantity.is_integer() else quantity), unit


def _normalize_exposure_risk(exposure: dict[str, Any]) -> None:
    direction = str(exposure.get("direction") or "").strip().lower()
    risk = str(exposure.get("risk") or "").strip()
    if direction in {"long", "buy"}:
        replacements = {
            "flat price \u4e0b\u8dcc": "flat price \u4e0a\u6da8",
            "\u4ef7\u683c\u4e0b\u8dcc": "\u4ef7\u683c\u4e0a\u6da8",
            "price downside": "price upside",
            "price decline": "price increase",
            "falling price": "rising price",
        }
    elif direction in {"short", "sell"}:
        replacements = {
            "flat price \u4e0a\u6da8": "flat price \u4e0b\u8dcc",
            "\u4ef7\u683c\u4e0a\u6da8": "\u4ef7\u683c\u4e0b\u8dcc",
            "price upside": "price downside",
            "price increase": "price decline",
            "rising price": "falling price",
        }
    else:
        return
    for source, target in replacements.items():
        risk = re.sub(re.escape(source), target, risk, flags=re.IGNORECASE)
    exposure["risk"] = risk


def _normalize_training_case(case: dict[str, Any]) -> dict[str, Any]:
    scenario = case.setdefault("scenario", {})
    exposure = scenario.setdefault("exposure", {})
    target_actions = [item for item in case.get("target_actions", []) if isinstance(item, dict)]
    physical_quantities = [item.get("quantity") for item in target_actions if item.get("leg_type") == "physical"]
    target_quantities = [item.get("quantity") for item in target_actions]
    stated_volume, stated_unit = _stated_case_quantity(case)
    volume = _positive_quantity(
        stated_volume,
        exposure.get("volume_mmbtu"),
        exposure.get("volume"),
        exposure.get("quantity"),
        exposure.get("volume_bbl"),
        *physical_quantities,
        *target_quantities,
    )
    if volume is not None:
        exposure["volume_mmbtu"] = volume
        strict_match = bool(re.search(r"strict(?:ly)? match|match (?:the )?quantity|\u4e25\u683c\u5339\u914d|\u4e00\u4e00\u5339\u914d", str(case.get("prompt") or ""), flags=re.IGNORECASE))
        for action in target_actions:
            leg_type = str(action.get("leg_type") or "").lower()
            if (
                _positive_quantity(action.get("quantity")) is None
                or (stated_volume is not None and leg_type == "physical")
                or (stated_volume is not None and strict_match and leg_type in {"future", "swap", "basis"})
            ):
                action["quantity"] = volume

    volume_unit = str(stated_unit or exposure.get("volume_unit") or exposure.get("unit") or "").strip()
    if not volume_unit:
        market_unit = str(case.get("market", {}).get("unit") or "")
        if "bbl" in market_unit.lower():
            volume_unit = "bbl"
        elif "mwh" in market_unit.lower():
            volume_unit = "MWh"
        elif "mmbtu" in market_unit.lower():
            volume_unit = "MMBtu"
    if volume_unit:
        exposure["volume_unit"] = volume_unit
    _normalize_exposure_risk(exposure)

    direction = str(exposure.get("direction") or "").strip().lower()
    expected_side = "buy" if direction in {"long", "buy"} else "sell" if direction in {"short", "sell"} else ""
    if expected_side:
        for action in target_actions:
            leg_type = str(action.get("leg_type") or "").lower()
            market_name = str(action.get("market") or "").lower()
            side = str(action.get("side") or "").lower()
            is_spread = leg_type == "basis" or any(token in market_name for token in ("basis", "spread", "\u57fa\u5dee", "\u4ef7\u5dee"))
            if leg_type in {"physical", "future"} and side in {"", "buy", "sell"}:
                action["side"] = expected_side
            elif leg_type == "swap" and not is_spread and side in {"", "buy", "sell"}:
                action["side"] = expected_side
    return case


def _extract_first_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        return ""
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return text[start:]


def _repair_common_llm_json(text: str) -> str:
    repaired = text.strip()
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    repaired = re.sub(r'(?<=[}\]"0-9])\s*(\r?\n)\s*(?="[^"\r\n]+"\s*:)', r",\1", repaired)
    repaired = re.sub(r'\b(true|false|null)\s*(\r?\n)\s*(?="[^"\r\n]+"\s*:)', r"\1,\2", repaired)
    return repaired


def _sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _unknown_scenario(exc: KeyError) -> HTTPException:
    detail = exc.args[0] if exc.args else str(exc)
    return HTTPException(status_code=404, detail=str(detail))


def _haineng_failure(exc: Exception) -> HTTPException:
    if _is_ai_response_parse_error(exc):
        return HTTPException(
            status_code=502,
            detail={
                "code": "ai_response_parse_failed",
                "message": "AI response could not be converted into a training case. Please retry.",
                "provider_message": "AI returned incomplete structured content.",
            },
        )
    message = _redact_provider_error(str(exc))
    return HTTPException(
        status_code=502,
        detail={"code": "ai_provider_request_failed", "message": "AI provider request failed.", "provider_message": message},
    )


def _provider_settings_failure(exc: Exception) -> HTTPException:
    status_code = getattr(exc, "status_code", None)
    message = _redact_provider_error(str(exc))
    invalid_key = "authentication fails" in message.lower() or (
        "api key" in message.lower() and "invalid" in message.lower()
    )
    if status_code == 401 or invalid_key:
        return HTTPException(
            status_code=401,
            detail={
                "code": "invalid_ai_api_key",
                "message": "The AI provider rejected this API key.",
                "provider_message": message,
            },
        )
    return HTTPException(
        status_code=502,
        detail={
            "code": "ai_provider_connection_failed",
            "message": "The AI provider could not be reached while validating the key.",
            "provider_message": message,
        },
    )


def _is_ai_response_parse_error(exc: Exception) -> bool:
    if isinstance(exc, json.JSONDecodeError):
        return True
    if isinstance(exc, ValueError):
        message = str(exc)
        return "JSON object" in message or "AI response JSON" in message
    return False


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


def _resolve_training_market(payload: TrainingCaseGenerateRequest, template: dict[str, Any]) -> dict[str, Any]:
    from core.market_learning import (
        build_replay_session,
        build_simulated_market_context,
        list_replay_events,
    )

    commodity = "crude_oil" if payload.product_scope == "crude_oil" or template.get("group") == "crude" else "natural_gas"
    mode = (payload.market_mode or "ai_simulated").strip().lower()
    if mode == "historical_replay":
        replay_id = payload.replay_id or list_replay_events(locale=payload.locale)[0]["id"]
        session = build_replay_session(replay_id, checkpoint=0, locale=payload.locale)
        context = deepcopy(session["market"])
        context["replay"] = {
            "locale": payload.locale,
            "event": session["event"],
            "current_checkpoint": session["current_checkpoint"],
            "visible_timeline": session["visible_timeline"],
            "next_checkpoint": session["next_checkpoint"],
            "decision_rubric": session["decision_rubric"],
            "information_policy": session["information_policy"],
            "source_notes": session["source_notes"],
        }
        return context
    if mode not in {"ai_simulated", "live"}:
        raise HTTPException(status_code=400, detail=f"Unsupported market mode: {payload.market_mode}")

    if mode == "live":
        from core.platts_market import PlattsError, PlattsMarketClient

        try:
            return PlattsMarketClient().fetch_market_context(commodity, locale=payload.locale)
        except PlattsError as exc:
            fallback_reason = exc.code
    else:
        fallback_reason = None

    context = build_simulated_market_context(
        commodity=commodity,
        regime=payload.market_regime,
        seed=payload.market_seed,
        as_of=payload.market_as_of,
        locale=payload.locale,
    )
    if fallback_reason:
        fallback_label = "AI 模拟回退" if payload.locale.lower().startswith("zh") else "AI simulated fallback"
        context["provenance"].update(
            {
                "requested_mode": "live",
                "requested_provider": "platts",
                "fallback_reason": fallback_reason,
                "quality": "explicit_simulation_fallback",
                "evidence_components": [
                    {
                        "id": "forward_curve",
                        "mode": "ai_simulated",
                        "label": fallback_label,
                        "as_of": context["as_of"],
                    },
                    {
                        "id": "history",
                        "mode": "ai_simulated",
                        "label": fallback_label,
                        "as_of": context["as_of"],
                    },
                ],
            }
        )
    return context


def _sample_market_history(points: list[dict[str, Any]], count: int = 8) -> list[dict[str, Any]]:
    if len(points) <= count:
        return deepcopy(points)
    indexes = sorted({round(index * (len(points) - 1) / (count - 1)) for index in range(count)})
    return [deepcopy(points[index]) for index in indexes]


def _market_prompt_context(context: dict[str, Any]) -> dict[str, Any]:
    """Keep model context decision-relevant while the local engine owns full data."""
    compact = {
        key: deepcopy(context.get(key))
        for key in ("commodity", "benchmark", "label", "unit", "as_of", "curve_metrics", "market_narrative", "provenance", "replay")
        if context.get(key) is not None
    }
    compact["forward_curve"] = deepcopy(context.get("forward_curve", [])[:6])
    compact["history"] = _sample_market_history(context.get("history", []), count=6)
    return compact


def _advisor_workspace_context(default_scenario: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Keep advisor prompts grounded in the active workspace without full chart payloads."""
    if not isinstance(context.get("case"), dict) and isinstance(context.get("market"), dict):
        nested = context["market"]
        if isinstance(nested.get("case"), dict):
            context = nested
    case = context.get("case") if isinstance(context.get("case"), dict) else {}
    market = case.get("market") if isinstance(case.get("market"), dict) else {}
    replay = market.get("replay") if isinstance(market.get("replay"), dict) else {}
    return {
        "scenario": deepcopy(case.get("scenario") or default_scenario),
        "market": {
            key: deepcopy(market.get(key))
            for key in ("benchmark", "unit", "as_of", "curve_metrics", "provenance")
            if market.get(key) is not None
        },
        "forward_curve": [
            {key: point.get(key) for key in ("tenor", "delivery_month", "price", "bid", "ask") if point.get(key) is not None}
            for point in market.get("forward_curve", [])[:6]
            if isinstance(point, dict)
        ],
        "replay": {
            key: deepcopy(replay.get(key))
            for key in ("event", "current_checkpoint", "information_policy")
            if replay.get(key) is not None
        },
        "strategy_legs": deepcopy(context.get("strategy_legs", []))[:8],
        "replay_decision": deepcopy(context.get("replay_decision", {})),
    }


def _compact_live_workspace_context(context: dict[str, Any]) -> dict[str, Any]:
    """Reduce assistant latency without removing the evidence needed for safe UI actions."""
    case = context.get("case") if isinstance(context.get("case"), dict) else {}
    scenario = case.get("scenario") if isinstance(case.get("scenario"), dict) else {}
    market = case.get("market") if isinstance(case.get("market"), dict) else {}
    training_session = case.get("training_session") if isinstance(case.get("training_session"), dict) else {}
    replay = market.get("replay") if isinstance(market.get("replay"), dict) else {}
    curriculum = context.get("curriculum_context") if isinstance(context.get("curriculum_context"), dict) else {}
    lesson_plan = context.get("ai_lesson_plan") if isinstance(context.get("ai_lesson_plan"), dict) else {}
    evaluation = context.get("evaluation") if isinstance(context.get("evaluation"), dict) else {}
    progress = context.get("learning_progress") if isinstance(context.get("learning_progress"), dict) else {}
    replay_catalog = context.get("replay_catalog") if isinstance(context.get("replay_catalog"), list) else []

    curves = []
    for curve in market.get("curves", [])[:3]:
        if not isinstance(curve, dict):
            continue
        points = curve.get("points", [])
        latest = points[-1] if isinstance(points, list) and points and isinstance(points[-1], dict) else {}
        curves.append(
            {
                "id": curve.get("id"),
                "label": curve.get("label"),
                "latest": {
                    key: latest.get(key)
                    for key in ("date", "open", "high", "low", "close")
                    if latest.get(key) is not None
                },
            }
        )

    attempts = []
    for attempt in context.get("recent_attempts", [])[-3:]:
        if not isinstance(attempt, dict):
            continue
        attempt_evaluation = attempt.get("evaluation") if isinstance(attempt.get("evaluation"), dict) else {}
        attempts.append(
            {
                "template_id": attempt.get("template_id"),
                "score": attempt_evaluation.get("baseline_score"),
                "mistake_tags": deepcopy(attempt_evaluation.get("mistake_tags", []))[:5],
            }
        )

    return {
        "active_page": context.get("active_page"),
        "active_template_id": context.get("active_template_id"),
        "product_scope": context.get("product_scope"),
        "course": {
            key: deepcopy(curriculum.get(key))
            for key in ("track_id", "track_title", "lesson_id", "lesson_title", "learning_objective")
            if curriculum.get(key) is not None
        },
        "lesson_plan": {
            key: deepcopy(lesson_plan.get(key))
            for key in ("track_id", "lesson_id", "title", "objective", "steps", "practice_prompt")
            if lesson_plan.get(key) is not None
        },
        "scenario": {
            key: deepcopy(scenario.get(key))
            for key in ("title", "summary", "business_type", "knowledge_points", "exposure")
            if scenario.get(key) is not None
        },
        "task": str(case.get("prompt") or "")[:2000],
        "rubric": deepcopy(case.get("rubric", []))[:8],
        "training_session": {
            key: deepcopy(training_session.get(key))
            for key in ("id", "product_scope", "template_id", "learning_objective", "market", "replay", "scoring")
            if training_session.get(key) is not None
        },
        "replay_catalog": [
            {
                key: deepcopy(item.get(key))
                for key in ("id", "commodity", "title", "summary", "checkpoint_count")
                if item.get(key) is not None
            }
            for item in replay_catalog[:8]
            if isinstance(item, dict)
        ],
        "market": {
            "benchmark": market.get("benchmark"),
            "unit": market.get("unit"),
            "as_of": market.get("as_of"),
            "curve_metrics": deepcopy(market.get("curve_metrics", {})),
            "forward_curve": [
                {
                    key: point.get(key)
                    for key in ("tenor", "delivery_month", "price", "bid", "ask")
                    if point.get(key) is not None
                }
                for point in market.get("forward_curve", [])[:6]
                if isinstance(point, dict)
            ],
            "latest_curves": curves,
            "replay": {
                key: deepcopy(replay.get(key))
                for key in ("event", "current_checkpoint", "information_policy")
                if replay.get(key) is not None
            },
        },
        "strategy_legs": deepcopy(context.get("strategy_legs", []))[:8],
        "rationale": str(context.get("rationale") or "")[:1600],
        "evaluation": {
            "baseline_score": evaluation.get("baseline_score"),
            "mistake_tags": deepcopy(evaluation.get("mistake_tags", []))[:8],
            "dimensions": deepcopy(evaluation.get("dimensions", []))[:8],
        },
        "learning_progress": {
            key: deepcopy(progress.get(key))
            for key in ("attempts", "sessions", "averageScore", "latestScore", "marketModes", "replayCheckpoints", "weakest")
            if progress.get(key) is not None
        },
        "recent_attempts": attempts,
    }


def _build_training_session(
    payload: TrainingCaseGenerateRequest,
    template: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    provenance = context.get("provenance", {})
    replay = context.get("replay") or {}
    event = replay.get("event") or {}
    checkpoint = replay.get("current_checkpoint") or {}
    requested_mode = (payload.market_mode or "ai_simulated").strip().lower()
    effective_mode = str(provenance.get("mode") or requested_mode)
    return {
        "id": f"session-{uuid4().hex}",
        "schema_version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "product_scope": payload.product_scope,
        "template_id": payload.template_id,
        "learning_objective": payload.user_request.strip() or str(template.get("title") or ""),
        "market": {
            "requested_mode": requested_mode,
            "effective_mode": effective_mode,
            "regime": payload.market_regime,
            "benchmark": context.get("benchmark"),
            "as_of": context.get("as_of") or provenance.get("as_of"),
            "source_tier": provenance.get("source_tier"),
            "fallback_applied": bool(provenance.get("fallback_reason")),
            "fallback_reason": provenance.get("fallback_reason"),
        },
        "replay": {
            "event_id": event.get("id"),
            "checkpoint": checkpoint.get("index", 0),
            "checkpoint_count": event.get("checkpoint_count"),
        } if event.get("id") else None,
        "scoring": {
            "mode": "local_deterministic",
            "rubric_version": "case-rubric-v1",
        },
        "ai": {
            "case_generated": True,
            "workspace_control_enabled": True,
        },
    }


def _attach_market_context(
    case: dict[str, Any],
    context: dict[str, Any],
    training_session: dict[str, Any] | None = None,
) -> dict[str, Any]:
    market = case.setdefault("market", {})
    benchmark = context.get("benchmark", "MARKET")
    history = context.get("history", [])
    curves = market.setdefault("curves", [])
    benchmark_curve = None
    if history:
        benchmark_curve = {
            "id": benchmark,
            "label": context.get("label", benchmark),
            "color": "#0ea5e9",
            "points": _sample_market_history(history),
        }
        matched = False
        for index, curve in enumerate(curves):
            if str(curve.get("id", "")).upper() == str(benchmark).upper():
                curves[index] = {**curve, **benchmark_curve}
                matched = True
                break
        if not matched:
            curves.insert(0, benchmark_curve)
        reference_dates = [point.get("date") for point in benchmark_curve["points"] if point.get("date")]
        for curve in curves:
            if str(curve.get("id", "")).upper() == str(benchmark).upper():
                continue
            points = curve.get("points", []) if isinstance(curve, dict) else []
            if not isinstance(points, list) or not points or not reference_dates:
                continue
            for point_index, point in enumerate(points):
                if not isinstance(point, dict):
                    continue
                date_index = round(point_index * (len(reference_dates) - 1) / max(len(points) - 1, 1))
                point["date"] = reference_dates[date_index]
    market.update(
        {
            "unit": context.get("unit", market.get("unit", "training index")),
            "as_of": context.get("as_of"),
            "benchmark": benchmark,
            "forward_curve": deepcopy(context.get("forward_curve", [])),
            "curve_metrics": deepcopy(context.get("curve_metrics", {})),
            "provenance": deepcopy(context.get("provenance", {})),
        }
    )
    replay = context.get("replay")
    if replay:
        if benchmark_curve:
            market["curves"] = [benchmark_curve]
        market["replay"] = deepcopy(replay)
        market["events"] = [
            {"date": item["date"], "label": item["label"]}
            for item in replay.get("visible_timeline", [])
        ]
        current_checkpoint = replay.get("current_checkpoint", {})
        event = replay.get("event", {})
        scenario = case.setdefault("scenario", {})
        scenario.update(
            {
                "title": event.get("title", scenario.get("title", "Historical replay")),
                "summary": event.get("summary", scenario.get("summary", "")),
                "business_type": (
                    "天然气历史复盘"
                    if replay.get("locale", "").lower().startswith("zh") and event.get("commodity") == "natural_gas"
                    else "原油历史复盘"
                    if replay.get("locale", "").lower().startswith("zh")
                    else "Natural Gas Historical Replay"
                    if event.get("commodity") == "natural_gas"
                    else "Crude Oil Historical Replay"
                ),
                "knowledge_points": deepcopy(event.get("skills", scenario.get("knowledge_points", []))),
            }
        )
        replay_exposure = event.get("exposure", {})
        scenario["exposure"] = {
            **scenario.get("exposure", {}),
            "direction": replay_exposure.get("direction", scenario.get("exposure", {}).get("direction", "")),
            "volume_mmbtu": replay_exposure.get("volume", scenario.get("exposure", {}).get("volume_mmbtu", 0)),
            "risk": replay_exposure.get("risk", scenario.get("exposure", {}).get("risk", "")),
            "unit": replay_exposure.get("unit", scenario.get("exposure", {}).get("unit", "")),
        }
        case["target_actions"] = []
        case["rubric"] = deepcopy(replay.get("decision_rubric", []))
        facts = current_checkpoint.get("facts", [])
        facts_markdown = "\n".join(f"- {fact}" for fact in facts)
        decision_label = "决策" if str(replay.get("locale", "")).lower().startswith("zh") else "Decision"
        case["prompt"] = (
            f"### {current_checkpoint.get('label', 'Replay checkpoint')}\n\n"
            f"{facts_markdown}\n\n"
            f"**{decision_label}:** {current_checkpoint.get('decision_required', '')}"
        )
    if training_session:
        case["training_session"] = deepcopy(training_session)
    return case


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
    try:
        HainengClient(settings).validate_credentials()
    except Exception as exc:
        raise _provider_settings_failure(exc) from exc
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
        review_scenario = _advisor_workspace_context(scenario, context)
        messages = build_advisor_messages(payload.locale, review_scenario, payload.evaluation or {}, payload.rationale)
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


@app.post("/api/v1/ai/advisor-review/stream")
def v1_ai_advisor_review_stream(payload: AITrainingRequest):
    def stream():
        try:
            from core.haineng_client import build_advisor_messages

            client = _require_haineng_client()
            scenario, context = _scenario_bundle(payload.scenario_id, payload.locale, payload.source, payload.market_context)
            review_scenario = _advisor_workspace_context(scenario, context)
            messages = build_advisor_messages(payload.locale, review_scenario, payload.evaluation or {}, payload.rationale)
            yield _sse_event("stage", {"id": "review_decision", "label": "Reviewing the scored decision"})
            chunks: list[str] = []
            received = 0
            stream_complete = getattr(client, "stream_complete", None)
            if callable(stream_complete):
                for delta in stream_complete(messages):
                    if not delta:
                        continue
                    chunks.append(delta)
                    received += len(delta)
                    yield _sse_event("model_delta", {"delta": delta, "received": received})
            if not chunks:
                answer = client.complete(messages)
                chunks.append(answer)
                yield _sse_event("model_delta", {"delta": answer, "received": len(answer)})
            yield _sse_event("review", {"answer": "".join(chunks)})
            yield _sse_event("done", {"ok": True})
        except Exception as exc:
            failure = _haineng_failure(exc)
            detail = failure.detail if isinstance(failure.detail, dict) else {}
            yield _sse_event("error", {"message": detail.get("message", "AI advisor review failed.")})

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/v1/ai/training-case")
def v1_ai_training_case(payload: TrainingCaseGenerateRequest):
    from core.haineng_client import build_training_case_messages
    from core.training_templates import get_template

    client = _require_haineng_client()
    try:
        template = get_template(payload.template_id, locale=payload.locale)
    except KeyError as exc:
        raise _unknown_scenario(exc)
    market_context = _resolve_training_market(payload, template)
    training_session = _build_training_session(payload, template, market_context)
    messages = build_training_case_messages(
        payload.locale,
        template,
        payload.user_request,
        knowledge_coverage=payload.knowledge_coverage[:8],
        gas_trading_models=payload.gas_trading_models[:6],
        market_context=_market_prompt_context(market_context),
    )
    try:
        answer = client.complete(messages)
        case = _attach_market_context(
            _normalize_training_case(_parse_json_response(answer)),
            market_context,
            training_session,
        )
    except Exception as exc:
        raise _haineng_failure(exc) from exc
    return {
        "template": template,
        "case": case,
        "market_context": market_context,
        "training_session": training_session,
    }


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
            yield _sse_event("stage", {"id": "resolve_market", "label": "Resolving market evidence and provenance"})
            market_context = _resolve_training_market(payload, template)
            training_session = _build_training_session(payload, template, market_context)
            yield _sse_event("session", training_session)
            yield _sse_event("market", market_context)
            yield _sse_event("stage", {"id": "generate_market", "label": "Composing the training market and decision path"})
            messages = build_training_case_messages(
                payload.locale,
                template,
                payload.user_request,
                knowledge_coverage=payload.knowledge_coverage[:8],
                gas_trading_models=payload.gas_trading_models[:6],
                market_context=_market_prompt_context(market_context),
            )
            chunks: list[str] = []
            received = 0
            stream_complete = getattr(client, "stream_complete", None)
            if callable(stream_complete):
                try:
                    for delta in stream_complete(messages):
                        if not delta:
                            continue
                        chunks.append(delta)
                        received += len(delta)
                        yield _sse_event("model_delta", {"delta": delta, "received": received})
                    if chunks:
                        answer = "".join(chunks)
                    else:
                        yield _sse_event("stage", {"id": "stream_fallback", "label": "Provider stream was empty; continuing without restart"})
                        answer = client.complete(messages)
                except Exception:
                    if chunks:
                        raise
                    yield _sse_event("stage", {"id": "stream_fallback", "label": "Provider streaming unavailable; continuing without restart"})
                    answer = client.complete(messages)
            else:
                answer = client.complete(messages)
            yield _sse_event("stage", {"id": "parse_case", "label": "Building scenario, target actions, and rubric"})
            case = _attach_market_context(
                _normalize_training_case(_parse_json_response(answer)),
                market_context,
                training_session,
            )
            yield _sse_event("case", {"template": template, "case": case})
            yield _sse_event("done", {"ok": True})
        except Exception as exc:
            yield _sse_event("error", {"message": str(_haineng_failure(exc).detail)})

    return StreamingResponse(stream(), media_type="text/event-stream")


def _live_assistant_action_schema() -> dict[str, Any]:
    return {
        "navigate_page": {"page": "home|caseLab|workbench|library|review|knowledge|progress|settings"},
        "generate_case": {
            "track_id": "foundation|crude|procurement|sales|integrated",
            "template_id": "foundation_hedging_basics",
            "user_request": "short training goal",
            "market_mode": "ai_simulated|historical_replay|live",
            "market_regime": "contango|backwardation|flat|volatile",
            "replay_id": "optional replay event id",
        },
        "select_template": {"template_id": "foundation_hedging_basics", "user_request": "optional training goal"},
        "configure_market_session": {
            "market_mode": "ai_simulated|historical_replay|live",
            "market_regime": "contango|backwardation|flat|volatile",
            "replay_id": "optional replay event id",
            "user_request": "optional refinement of the current learning goal",
        },
        "patch_case": {
            "scenario": {"title": "short title", "summary": "updated scenario summary", "exposure": {"direction": "buy|sell|spread", "risk": "key risk"}},
            "market": {"unit": "training index", "events": [{"date": "2026-01-07", "label": "event"}]},
            "target_actions": [{"leg_type": "physical|swap|future|basis|fx|capacity", "market": "TTF", "side": "buy|sell", "quantity": 10000, "tenor": "M+1"}],
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
        "set_learning_plan": {
            "track_id": "foundation|crude|procurement|sales|integrated",
            "lesson_id": "optional lesson id",
            "title": "short visible title",
            "objective": "one sentence learning objective",
            "steps": ["step 1", "step 2", "step 3"],
            "practice_prompt": "prompt to generate the next drill",
        },
        "set_learning_goal": {"goal": "short goal", "focus": ["basis", "fx", "capacity"]},
        "set_chart_fields": {"fields": ["high", "low", "close"]},
        "set_strategy_legs": {"legs": [{"leg_type": "physical|swap|future|basis|fx|capacity|option", "market": "TTF", "side": "sell", "quantity": 10000}]},
        "fill_rationale": {"text": "string"},
        "set_exam": {"exam": {"id": "exam-1", "title": "Short quiz", "questions": [{"id": "q1", "prompt": "Question", "options": ["A", "B"], "correct_index": 0, "explanation": "Reason", "skills": ["instrument"]}]}},
        "submit_strategy": {},
        "run_ai_capability": {"capability": "concept_tutor|exam|trade_playbook|advisor_review"},
    }


def _live_assistant_messages(payload: LiveAssistantRequest) -> list[dict[str, str]]:
    from core.haineng_client import build_live_assistant_messages

    return build_live_assistant_messages(
        payload.locale,
        payload.message,
        _compact_live_workspace_context(payload.workspace_state),
        _live_assistant_action_schema(),
    )


def _normalize_live_assistant_result(parsed: dict[str, Any]) -> dict[str, Any]:
    allowed = set(_live_assistant_action_schema())
    actions = [
        action
        for action in parsed.get("actions", [])[:8]
        if isinstance(action, dict)
        and action.get("type") in allowed
        and isinstance(action.get("payload", {}), dict)
    ]
    return {
        "answer": str(parsed.get("answer", ""))[:6000],
        "actions": actions,
    }


@app.post("/api/v1/ai/live-assistant")
def v1_ai_live_assistant(payload: LiveAssistantRequest):
    client = _require_haineng_client()
    messages = _live_assistant_messages(payload)
    try:
        answer = client.complete(messages)
        try:
            parsed = _parse_json_response(answer)
        except Exception:
            parsed = {"answer": answer, "actions": []}
    except Exception as exc:
        raise _haineng_failure(exc) from exc
    return _normalize_live_assistant_result(parsed)


@app.post("/api/v1/ai/live-assistant/stream")
def v1_ai_live_assistant_stream(payload: LiveAssistantRequest):
    client = _require_haineng_client()
    messages = _live_assistant_messages(payload)

    def stream():
        yield _sse_event("stage", {"id": "read_workspace", "label": "Reading the current lesson and market state"})
        try:
            chunks: list[str] = []
            received = 0
            if hasattr(client, "stream_complete"):
                yield _sse_event("stage", {"id": "plan_workspace_actions", "label": "Planning concise teaching and workspace actions"})
                for chunk in client.stream_complete(messages):
                    if not chunk:
                        continue
                    chunks.append(chunk)
                    received += len(chunk)
                    yield _sse_event("model_delta", {"delta": chunk, "received": received})
                answer = "".join(chunks)
            else:
                answer = client.complete(messages)
                received = len(answer)
                yield _sse_event("model_delta", {"delta": answer, "received": received})
            yield _sse_event("stage", {"id": "apply_workspace_actions", "label": "Validating the proposed workspace changes"})
            try:
                parsed = _parse_json_response(answer)
            except Exception:
                parsed = {"answer": answer, "actions": []}
            yield _sse_event("result", _normalize_live_assistant_result(parsed))
            yield _sse_event("done", {"ok": True})
        except Exception as exc:
            yield _sse_event("error", {"message": str(_haineng_failure(exc).detail)})

    return StreamingResponse(stream(), media_type="text/event-stream")


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
    try:
        parsed = _parse_json_response(result["answer"])
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail="AI exam response was not valid structured JSON.") from exc

    allowed_skills = {"exposure", "instrument", "basis", "fx", "capacity", "timing", "control", "rationale"}
    questions: list[dict[str, Any]] = []
    for index, item in enumerate(parsed.get("questions", [])):
        if not isinstance(item, dict):
            continue
        prompt = str(item.get("prompt", "")).strip()
        options = [str(option).strip() for option in item.get("options", []) if str(option).strip()][:4]
        try:
            correct_index = int(item.get("correct_index"))
        except (TypeError, ValueError):
            continue
        if not prompt or len(options) < 2 or not 0 <= correct_index < len(options):
            continue
        skills = [str(skill) for skill in item.get("skills", []) if str(skill) in allowed_skills][:3]
        questions.append(
            {
                "id": str(item.get("id") or f"q{index + 1}"),
                "type": "single_choice",
                "prompt": prompt,
                "options": options,
                "correct_index": correct_index,
                "explanation": str(item.get("explanation", "")).strip(),
                "skills": skills or ["instrument"],
            }
        )
    if not 3 <= len(questions) <= 5:
        raise HTTPException(status_code=502, detail="AI exam response must contain 3 to 5 valid questions.")
    title = str(parsed.get("title") or ("课程测验" if payload.locale.lower().startswith("zh") else "Course Checkpoint")).strip()
    return {"exam": {"id": f"exam-{uuid4().hex[:12]}", "title": title, "questions": questions}}


if __name__ == "__main__":
    import uvicorn
    _ensure_stdio_for_windowed_runtime()
    _start_parent_watchdog()
    uvicorn.run(app, host=_backend_host(), port=_backend_port(), log_config=None)
