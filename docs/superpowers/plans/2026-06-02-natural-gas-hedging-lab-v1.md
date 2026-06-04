# Commodity Lab V1 Natural Gas Hedging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the V1 natural gas hedging module in Commodity Lab, with bilingual English/Mandarin UI, mandatory 海能 setup, natural-gas-only guided practice, deterministic hedge/capacity metrics, 海能 coaching, and exam generation.

**Architecture:** Keep deterministic trading behavior in Python core modules, expose V1 endpoints from the existing FastAPI backend, bridge them through Tauri, and replace the current three-button React prototype with a professional guided terminal workspace. 海能 is treated as an OpenAI-compatible local provider branded only as 海能 in the client.

**Tech Stack:** Python 3.12, FastAPI, pandas, yFinance/sample data, optional Platts, OpenAI-compatible `openai` Python SDK, Tauri v1 Rust bridge, React 18 + Vite, Vitest + Testing Library for frontend checks, pytest for backend/core checks.

---

## File Structure

Create or modify these files:

- Create `core/gas_scenarios.py`: natural gas scenario catalog, bilingual scenario copy, sample market series, sample pipeline capacity model.
- Create `core/learning_session.py`: deterministic attempt evaluation, order validation, mistake tags, score inputs, exam answer summaries.
- Create `core/haineng_client.py`: OpenAI-compatible 海能 settings, health check, safe prompt builders, function-call tool schemas, mocked-friendly request wrappers.
- Modify `tauri/backend/requirements.txt`: add `openai`.
- Modify `requirements.txt`: add `openai` for root test/runtime parity.
- Modify `tauri/backend/main.py`: add V1 request/response models and endpoints while keeping existing endpoints compatible.
- Modify `tauri/src-tauri/src/main.rs`: add a generic backend request command and register it.
- Modify `tauri/tauri-frontend/index.html`: remove duplicate document and keep one Vite root.
- Modify `tauri/tauri-frontend/package.json`: add `test`, `vitest`, Testing Library, and `jsdom`.
- Create `tauri/tauri-frontend/src/i18n.js`: translation dictionaries and locale helpers.
- Create `tauri/tauri-frontend/src/api.js`: Tauri backend request helper with browser-dev fallback.
- Create `tauri/tauri-frontend/src/App.test.jsx`: frontend behavior tests.
- Create `tauri/tauri-frontend/src/styles.css`: professional terminal visual system.
- Replace `tauri/tauri-frontend/src/App.jsx`: app shell and composed V1 workflow.
- Modify `tauri/tauri-frontend/src/main.jsx`: import `styles.css`.
- Create `tests/test_gas_scenarios.py`: scenario and capacity unit tests.
- Create `tests/test_learning_session.py`: deterministic evaluation tests.
- Create `tests/test_haineng_client.py`: prompt safety and locale tests.
- Create `tests/test_tauri_backend_v1.py`: backend endpoint tests with mocked 海能.

---

### Task 1: Natural Gas Scenario Catalog And Sample Capacity Model

**Files:**
- Create: `core/gas_scenarios.py`
- Test: `tests/test_gas_scenarios.py`

- [ ] **Step 1: Write the failing scenario tests**

Create `tests/test_gas_scenarios.py`:

```python
from __future__ import annotations

from core.gas_scenarios import (
    get_capacity_context,
    get_market_context,
    get_scenario,
    list_categories,
    list_scenarios,
)


def test_only_natural_gas_enabled_for_v1() -> None:
    scenarios = list_scenarios(locale="en")
    assert len(scenarios) >= 5
    assert {item["commodity"] for item in scenarios} == {"natural_gas"}
    assert all(item["enabled"] for item in scenarios)


def test_other_categories_are_constructing() -> None:
    categories = list_categories(locale="en")
    disabled = [item for item in categories if item["id"] != "natural_gas"]
    assert disabled
    assert all(item["status"] == "constructing" for item in disabled)


def test_scenario_returns_bilingual_copy() -> None:
    scenario = get_scenario("pipeline_capacity_constraint", locale="zh")
    assert scenario["id"] == "pipeline_capacity_constraint"
    assert scenario["title"]
    assert scenario["guided_steps"][0]["id"] == "understand_exposure"
    assert scenario["learning_objectives"]


def test_capacity_context_has_visual_flow_fields() -> None:
    capacity = get_capacity_context("pipeline_capacity_constraint")
    assert capacity["receipt_point"] == "Permian Receipt"
    assert capacity["delivery_point"] == "Gulf Coast Delivery"
    assert capacity["available_capacity_mmbtu"] > 0
    assert capacity["nominated_mmbtu"] > 0
    assert 0 < capacity["utilization_pct"] <= 100
    assert capacity["congestion_status"] in {"normal", "watch", "constrained"}


def test_market_context_has_sample_series_and_fallback_metadata() -> None:
    market = get_market_context("winter_load_spike", source="sample")
    assert market["source"] == "sample"
    assert market["symbol"] == "NG=F"
    assert len(market["price_series"]) >= 6
    assert {"date", "close"}.issubset(market["price_series"][0])
```

- [ ] **Step 2: Run tests and verify they fail for missing module**

Run:

```bash
pytest tests/test_gas_scenarios.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'core.gas_scenarios'`.

- [ ] **Step 3: Implement scenario catalog**

Create `core/gas_scenarios.py`:

```python
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from typing import Any

Locale = str

CATEGORY_LABELS = {
    "natural_gas": {"en": "Natural Gas", "zh": "天然气"},
    "oil_products": {"en": "Oil Products", "zh": "油品"},
    "metals": {"en": "Metals", "zh": "金属"},
    "grains": {"en": "Grains", "zh": "谷物"},
}

GUIDED_STEPS = [
    {"id": "understand_exposure", "label": {"en": "Understand exposure", "zh": "识别风险敞口"}},
    {"id": "inspect_market", "label": {"en": "Inspect market", "zh": "观察市场"}},
    {"id": "place_hedge", "label": {"en": "Place hedge", "zh": "建立套保"}},
    {"id": "review_score", "label": {"en": "Review score", "zh": "复盘评分"}},
    {"id": "exam", "label": {"en": "Exam", "zh": "测验"}},
]

SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "producer_short_hedge",
        "commodity": "natural_gas",
        "enabled": True,
        "title": {"en": "Producer Short Hedge", "zh": "生产商卖出套保"},
        "summary": {
            "en": "A gas producer wants to protect revenue before a potential Henry Hub selloff.",
            "zh": "天然气生产商担心 Henry Hub 下跌，需要保护未来销售收入。",
        },
        "exposure": {"direction": "long_physical", "volume_mmbtu": 100000, "risk": "falling_price"},
        "default_symbol": "NG=F",
        "recommended_hedge_type": "short_hedge",
        "recommended_side": "sell",
        "learning_objectives": ["hedge_direction", "hedge_ratio", "futures_pnl"],
    },
    {
        "id": "winter_load_spike",
        "commodity": "natural_gas",
        "enabled": True,
        "title": {"en": "Winter Load Spike", "zh": "冬季负荷上涨"},
        "summary": {
            "en": "A utility faces winter demand risk and needs protection against rising gas prices.",
            "zh": "公用事业公司面临冬季需求上升风险，需要防范天然气价格上涨。",
        },
        "exposure": {"direction": "short_physical", "volume_mmbtu": 80000, "risk": "rising_price"},
        "default_symbol": "NG=F",
        "recommended_hedge_type": "long_hedge",
        "recommended_side": "buy",
        "learning_objectives": ["consumer_hedge", "seasonality", "cost_protection"],
    },
    {
        "id": "pipeline_capacity_constraint",
        "commodity": "natural_gas",
        "enabled": True,
        "title": {"en": "Pipeline Capacity Constraint", "zh": "管道运力约束"},
        "summary": {
            "en": "A shipper must hedge basis risk when nominations approach available pipeline capacity.",
            "zh": "托运方提名量接近管道可用运力，需要管理基差风险。",
        },
        "exposure": {"direction": "basis_exposure", "volume_mmbtu": 60000, "risk": "basis_blowout"},
        "default_symbol": "NG=F",
        "recommended_hedge_type": "basis_hedge",
        "recommended_side": "sell",
        "learning_objectives": ["capacity_utilization", "basis_risk", "congestion"],
    },
    {
        "id": "regional_basis_blowout",
        "commodity": "natural_gas",
        "enabled": True,
        "title": {"en": "Regional Basis Blowout", "zh": "区域基差扩大"},
        "summary": {
            "en": "A regional marketer faces local hub weakness versus Henry Hub.",
            "zh": "区域营销商面临本地枢纽相对 Henry Hub 走弱的风险。",
        },
        "exposure": {"direction": "basis_exposure", "volume_mmbtu": 45000, "risk": "local_basis"},
        "default_symbol": "NG=F",
        "recommended_hedge_type": "basis_hedge",
        "recommended_side": "sell",
        "learning_objectives": ["basis", "regional_prices", "hedge_fit"],
    },
    {
        "id": "storage_calendar_spread",
        "commodity": "natural_gas",
        "enabled": True,
        "title": {"en": "Storage Calendar Spread", "zh": "储气库月差套保"},
        "summary": {
            "en": "A storage operator evaluates nearby versus winter-month exposure.",
            "zh": "储气库运营方评估近月与冬季合约之间的风险敞口。",
        },
        "exposure": {"direction": "spread_exposure", "volume_mmbtu": 70000, "risk": "calendar_spread"},
        "default_symbol": "NG=F",
        "recommended_hedge_type": "calendar_spread",
        "recommended_side": "sell",
        "learning_objectives": ["spread", "storage_value", "seasonality"],
    },
]

CAPACITY_CONTEXTS: dict[str, dict[str, Any]] = {
    "pipeline_capacity_constraint": {
        "receipt_point": "Permian Receipt",
        "pipeline_segment": "Permian-Gulf Mainline",
        "delivery_point": "Gulf Coast Delivery",
        "available_capacity_mmbtu": 75000,
        "nominated_mmbtu": 69000,
        "operational_capacity_mmbtu": 72000,
        "utilization_pct": 92.0,
        "congestion_status": "constrained",
        "basis_impact_usd": -0.42,
        "events": [
            {"date": "2026-01-08", "label": "Maintenance notice", "severity": "watch"},
            {"date": "2026-01-11", "label": "Nomination cut risk", "severity": "high"},
        ],
    }
}


def _localize(value: Any, locale: Locale) -> Any:
    if isinstance(value, dict) and "en" in value and "zh" in value:
        return value.get(locale, value["en"])
    if isinstance(value, dict):
        return {key: _localize(item, locale) for key, item in value.items()}
    if isinstance(value, list):
        return [_localize(item, locale) for item in value]
    return value


def list_categories(locale: Locale = "en") -> list[dict[str, Any]]:
    return [
        {
            "id": category_id,
            "label": labels.get(locale, labels["en"]),
            "status": "enabled" if category_id == "natural_gas" else "constructing",
        }
        for category_id, labels in CATEGORY_LABELS.items()
    ]


def list_scenarios(locale: Locale = "en") -> list[dict[str, Any]]:
    return [
        {
            "id": scenario["id"],
            "commodity": scenario["commodity"],
            "enabled": scenario["enabled"],
            "title": scenario["title"].get(locale, scenario["title"]["en"]),
            "summary": scenario["summary"].get(locale, scenario["summary"]["en"]),
            "default_symbol": scenario["default_symbol"],
            "learning_objectives": scenario["learning_objectives"],
        }
        for scenario in SCENARIOS
        if scenario["commodity"] == "natural_gas"
    ]


def get_scenario(scenario_id: str, locale: Locale = "en") -> dict[str, Any]:
    for scenario in SCENARIOS:
        if scenario["id"] == scenario_id:
            output = _localize(deepcopy(scenario), locale)
            output["guided_steps"] = _localize(GUIDED_STEPS, locale)
            return output
    raise KeyError(f"Unknown scenario: {scenario_id}")


def _sample_price_series() -> list[dict[str, Any]]:
    start = date(2026, 1, 2)
    closes = [3.08, 3.14, 3.22, 3.36, 3.31, 3.48, 3.57, 3.52]
    return [
        {"date": (start + timedelta(days=index)).isoformat(), "close": close}
        for index, close in enumerate(closes)
    ]


def get_market_context(scenario_id: str, source: str = "sample") -> dict[str, Any]:
    scenario = get_scenario(scenario_id, locale="en")
    return {
        "scenario_id": scenario_id,
        "source": "sample" if source not in {"yfinance", "platts"} else source,
        "symbol": scenario["default_symbol"],
        "unit": "USD/MMBtu",
        "price_series": _sample_price_series(),
        "latest_price": _sample_price_series()[-1]["close"],
    }


def get_capacity_context(scenario_id: str) -> dict[str, Any]:
    if scenario_id in CAPACITY_CONTEXTS:
        return deepcopy(CAPACITY_CONTEXTS[scenario_id])
    return {
        "receipt_point": "Sample Receipt",
        "pipeline_segment": "Sample Mainline",
        "delivery_point": "Sample Delivery",
        "available_capacity_mmbtu": 80000,
        "nominated_mmbtu": 52000,
        "operational_capacity_mmbtu": 80000,
        "utilization_pct": 65.0,
        "congestion_status": "normal",
        "basis_impact_usd": -0.08,
        "events": [],
    }
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
pytest tests/test_gas_scenarios.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core/gas_scenarios.py tests/test_gas_scenarios.py
git commit -m "feat: add natural gas scenario catalog"
```

---

### Task 2: Deterministic Learning Session Evaluation

**Files:**
- Create: `core/learning_session.py`
- Test: `tests/test_learning_session.py`

- [ ] **Step 1: Write failing evaluator tests**

Create `tests/test_learning_session.py`:

```python
from __future__ import annotations

from core.gas_scenarios import get_capacity_context, get_scenario
from core.learning_session import evaluate_attempt, validate_order


def test_validate_order_rejects_missing_quantity() -> None:
    errors = validate_order({"side": "sell", "quantity": 0, "hedge_type": "short_hedge"})
    assert "quantity" in errors


def test_evaluate_attempt_scores_recommended_producer_hedge() -> None:
    scenario = get_scenario("producer_short_hedge", locale="en")
    result = evaluate_attempt(
        scenario=scenario,
        capacity_context=get_capacity_context("producer_short_hedge"),
        order={
            "side": "sell",
            "quantity": 80000,
            "hedge_type": "short_hedge",
            "price": 3.5,
        },
        rationale="I sell futures to offset falling price risk on expected production.",
    )
    assert result["valid"] is True
    assert result["score_inputs"]["direction_match"] is True
    assert result["score_inputs"]["hedge_type_match"] is True
    assert result["metrics"]["hedge_ratio"] == 0.8
    assert result["baseline_score"] >= 80


def test_evaluate_attempt_tags_capacity_blind_spot() -> None:
    scenario = get_scenario("pipeline_capacity_constraint", locale="en")
    result = evaluate_attempt(
        scenario=scenario,
        capacity_context=get_capacity_context("pipeline_capacity_constraint"),
        order={
            "side": "buy",
            "quantity": 60000,
            "hedge_type": "long_hedge",
            "price": 3.4,
        },
        rationale="I buy futures because prices may rise.",
    )
    assert "wrong_direction" in result["mistake_tags"]
    assert "ignores_capacity" in result["mistake_tags"]
    assert result["baseline_score"] < 70
```

- [ ] **Step 2: Run tests and verify they fail for missing module**

Run:

```bash
pytest tests/test_learning_session.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'core.learning_session'`.

- [ ] **Step 3: Implement deterministic evaluator**

Create `core/learning_session.py`:

```python
from __future__ import annotations

from typing import Any


def validate_order(order: dict[str, Any]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if order.get("side") not in {"buy", "sell"}:
        errors["side"] = "Order side must be buy or sell."
    try:
        quantity = float(order.get("quantity", 0))
    except (TypeError, ValueError):
        quantity = 0.0
    if quantity <= 0:
        errors["quantity"] = "Quantity must be greater than zero."
    if not order.get("hedge_type"):
        errors["hedge_type"] = "Hedge type is required."
    return errors


def _hedge_ratio(order: dict[str, Any], scenario: dict[str, Any]) -> float:
    exposure = float(scenario.get("exposure", {}).get("volume_mmbtu", 1) or 1)
    quantity = float(order.get("quantity", 0) or 0)
    return round(quantity / exposure, 4)


def _score_boolean(value: bool, points: int) -> int:
    return points if value else 0


def classify_mistakes(
    scenario: dict[str, Any],
    capacity_context: dict[str, Any],
    order: dict[str, Any],
    rationale: str,
) -> list[str]:
    tags: list[str] = []
    if order.get("side") != scenario.get("recommended_side"):
        tags.append("wrong_direction")
    if order.get("hedge_type") != scenario.get("recommended_hedge_type"):
        tags.append("wrong_hedge_type")

    ratio = _hedge_ratio(order, scenario)
    if ratio > 1.2:
        tags.append("over_hedged")
    if ratio < 0.5:
        tags.append("under_hedged")

    text = (rationale or "").lower()
    if "basis" in scenario.get("learning_objectives", []) and "basis" not in text:
        tags.append("ignores_basis")
    if (
        "capacity_utilization" in scenario.get("learning_objectives", [])
        and capacity_context.get("congestion_status") == "constrained"
        and "capacity" not in text
        and "pipeline" not in text
    ):
        tags.append("ignores_capacity")
    return tags


def evaluate_attempt(
    scenario: dict[str, Any],
    capacity_context: dict[str, Any],
    order: dict[str, Any],
    rationale: str,
) -> dict[str, Any]:
    errors = validate_order(order)
    if errors:
        return {"valid": False, "errors": errors}

    ratio = _hedge_ratio(order, scenario)
    direction_match = order.get("side") == scenario.get("recommended_side")
    hedge_type_match = order.get("hedge_type") == scenario.get("recommended_hedge_type")
    ratio_fit = 0.75 <= ratio <= 1.05
    mistake_tags = classify_mistakes(scenario, capacity_context, order, rationale)

    score = 35
    score += _score_boolean(direction_match, 25)
    score += _score_boolean(hedge_type_match, 20)
    score += _score_boolean(ratio_fit, 15)
    score -= min(25, len(mistake_tags) * 8)
    score = max(0, min(100, score))

    quantity = float(order.get("quantity", 0))
    price = float(order.get("price", 0) or 0)
    return {
        "valid": True,
        "errors": {},
        "metrics": {
            "hedge_ratio": ratio,
            "notional_usd": round(quantity * price, 2),
            "capacity_utilization_pct": capacity_context.get("utilization_pct", 0),
            "basis_impact_usd": capacity_context.get("basis_impact_usd", 0),
        },
        "score_inputs": {
            "direction_match": direction_match,
            "hedge_type_match": hedge_type_match,
            "ratio_fit": ratio_fit,
        },
        "mistake_tags": mistake_tags,
        "baseline_score": score,
    }
```

- [ ] **Step 4: Run evaluator tests**

Run:

```bash
pytest tests/test_learning_session.py tests/test_gas_scenarios.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add core/learning_session.py tests/test_learning_session.py
git commit -m "feat: add deterministic learning evaluator"
```

---

### Task 3: 海能 Provider Client And Prompt Contracts

**Files:**
- Create: `core/haineng_client.py`
- Modify: `requirements.txt`
- Modify: `tauri/backend/requirements.txt`
- Test: `tests/test_haineng_client.py`

- [ ] **Step 1: Add failing prompt-safety tests**

Create `tests/test_haineng_client.py`:

```python
from __future__ import annotations

from core.haineng_client import (
    HainengSettings,
    build_advisor_messages,
    build_exam_messages,
    build_haineng_tools,
    redact_settings,
)


def test_redact_settings_never_returns_api_key() -> None:
    settings = HainengSettings(
        api_key="secret-key",
        base_url="http://model.local/haineng/v1",
        model="V4-Flash",
    )
    redacted = redact_settings(settings)
    assert redacted["configured"] is True
    assert "secret-key" not in str(redacted)


def test_advisor_messages_include_locale_and_not_key() -> None:
    settings = HainengSettings(api_key="secret-key", base_url="http://local/v1")
    messages = build_advisor_messages(
        locale="zh",
        scenario={"id": "producer_short_hedge", "title": "生产商卖出套保"},
        evaluation={"baseline_score": 82, "mistake_tags": []},
        user_rationale="卖出期货保护价格下跌风险",
    )
    text = str(messages)
    assert "Respond in Mandarin Chinese" in text
    assert settings.api_key not in text


def test_exam_messages_request_three_to_five_questions() -> None:
    messages = build_exam_messages(
        locale="en",
        scenario={"id": "pipeline_capacity_constraint", "title": "Pipeline Capacity Constraint"},
        attempt_history=[{"baseline_score": 62, "mistake_tags": ["ignores_capacity"]}],
    )
    text = str(messages)
    assert "3 to 5" in text
    assert "pipeline_capacity_constraint" in text


def test_function_tools_have_required_shape() -> None:
    tools = build_haineng_tools()
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == "get_attempt_metrics"
    assert "parameters" in tools[0]["function"]
```

- [ ] **Step 2: Run tests and verify they fail for missing module**

Run:

```bash
pytest tests/test_haineng_client.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'core.haineng_client'`.

- [ ] **Step 3: Add `openai` dependency**

Modify `requirements.txt` and `tauri/backend/requirements.txt` by adding:

```text
openai>=1.40.0
```

- [ ] **Step 4: Implement 海能 client**

Create `core/haineng_client.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HainengSettings:
    api_key: str = ""
    base_url: str = ""
    model: str = "V4-Flash"
    streaming: bool = False
    function_calling: bool = True


def settings_from_env() -> HainengSettings:
    return HainengSettings(
        api_key=os.getenv("HAINENG_API_KEY", "").strip(),
        base_url=os.getenv("HAINENG_BASE_URL", "").strip(),
        model=os.getenv("HAINENG_MODEL", "V4-Flash").strip() or "V4-Flash",
        streaming=os.getenv("HAINENG_STREAMING", "false").lower() == "true",
        function_calling=os.getenv("HAINENG_FUNCTION_CALLING", "true").lower() != "false",
    )


def redact_settings(settings: HainengSettings) -> dict[str, Any]:
    return {
        "configured": bool(settings.api_key and settings.base_url),
        "base_url": settings.base_url,
        "model": settings.model,
        "streaming": settings.streaming,
        "function_calling": settings.function_calling,
    }


def _language_instruction(locale: str) -> str:
    if locale == "zh":
        return "Respond in Mandarin Chinese. Keep trading terms clear and concise."
    return "Respond in English. Keep trading terms clear and concise."


def build_haineng_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_attempt_metrics",
                "description": "Return deterministic hedge metrics already computed by Commodity Lab.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scenario_id": {"type": "string"},
                        "attempt_id": {"type": "string"},
                    },
                    "required": ["scenario_id"],
                },
            },
        }
    ]


def build_advisor_messages(
    locale: str,
    scenario: dict[str, Any],
    evaluation: dict[str, Any],
    user_rationale: str,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are 海能, a natural gas hedging tutor. "
                f"{_language_instruction(locale)} "
                "Use deterministic metrics as evidence. Do not invent market prices. "
                "Give one actionable next step and classify the main mistake when applicable."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Scenario: {scenario}\n"
                f"User rationale: {user_rationale}\n"
                f"Computed evaluation: {evaluation}\n"
                "Provide feedback, score explanation, and next action."
            ),
        },
    ]


def build_exam_messages(
    locale: str,
    scenario: dict[str, Any],
    attempt_history: list[dict[str, Any]],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are 海能, generating a short natural gas hedging exam. "
                f"{_language_instruction(locale)} "
                "Generate 3 to 5 questions. Include answer key and explanation after the user submits answers."
            ),
        },
        {
            "role": "user",
            "content": f"Scenario: {scenario}\nAttempt history: {attempt_history}\nGenerate the exam questions now.",
        },
    ]


class HainengClient:
    def __init__(self, settings: HainengSettings | None = None):
        self.settings = settings or settings_from_env()

    def is_configured(self) -> bool:
        return bool(self.settings.api_key and self.settings.base_url)

    def _client(self):
        from openai import OpenAI

        return OpenAI(api_key=self.settings.api_key, base_url=self.settings.base_url)

    def health_check(self) -> dict[str, Any]:
        if not self.is_configured():
            return {"ok": False, "reason": "missing_haineng_settings", **redact_settings(self.settings)}
        return {"ok": True, **redact_settings(self.settings)}

    def complete(self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None) -> str:
        if not self.is_configured():
            raise RuntimeError("海能 is not configured.")
        kwargs: dict[str, Any] = {
            "model": self.settings.model,
            "messages": messages,
            "stream": False,
        }
        if tools and self.settings.function_calling:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        response = self._client().chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""
```

- [ ] **Step 5: Run prompt-safety tests**

Run:

```bash
pytest tests/test_haineng_client.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add core/haineng_client.py tests/test_haineng_client.py requirements.txt tauri/backend/requirements.txt
git commit -m "feat: add haineng provider client"
```

---

### Task 4: FastAPI V1 Backend Endpoints

**Files:**
- Modify: `tauri/backend/main.py`
- Test: `tests/test_tauri_backend_v1.py`

- [ ] **Step 1: Write failing backend endpoint tests**

Create `tests/test_tauri_backend_v1.py`:

```python
from __future__ import annotations

from fastapi.testclient import TestClient

from tauri.backend.main import app


client = TestClient(app)


def test_provider_status_reports_missing_haineng_without_secret() -> None:
    response = client.get("/api/v1/provider-status")
    assert response.status_code == 200
    payload = response.json()
    assert "haineng" in payload
    assert "api_key" not in str(payload).lower()


def test_scenarios_endpoint_returns_natural_gas_only() -> None:
    response = client.get("/api/v1/scenarios?locale=en")
    assert response.status_code == 200
    payload = response.json()
    assert payload["categories"][0]["id"] == "natural_gas"
    assert all(item["commodity"] == "natural_gas" for item in payload["scenarios"])


def test_context_endpoint_returns_market_and_capacity() -> None:
    response = client.get("/api/v1/scenarios/pipeline_capacity_constraint/context?locale=en")
    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario"]["id"] == "pipeline_capacity_constraint"
    assert payload["market"]["source"] == "sample"
    assert payload["capacity"]["congestion_status"] == "constrained"


def test_evaluate_endpoint_returns_deterministic_result() -> None:
    response = client.post(
        "/api/v1/attempts/evaluate",
        json={
            "scenario_id": "producer_short_hedge",
            "locale": "en",
            "order": {"side": "sell", "quantity": 80000, "hedge_type": "short_hedge", "price": 3.5},
            "rationale": "I sell futures to protect production revenue.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation"]["valid"] is True
    assert payload["evaluation"]["baseline_score"] >= 80
```

- [ ] **Step 2: Run tests and verify endpoint failures**

Run:

```bash
pytest tests/test_tauri_backend_v1.py -q
```

Expected: FAIL with 404 responses for `/api/v1/provider-status`.

- [ ] **Step 3: Add backend models and endpoints**

Modify `tauri/backend/main.py` by adding imports:

```python
from typing import Any
```

Add models below `OrderSpec`:

```python
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
    attempt_history: list[dict[str, Any]] = []
```

Add endpoints before the existing `if __name__ == "__main__"` block:

```python
@app.get("/api/v1/provider-status")
def provider_status():
    from core.haineng_client import HainengClient

    haineng = HainengClient().health_check()
    return {
        "haineng": haineng,
        "platts": {"configured": bool(__import__("os").getenv("PLATTS_API_KEY", "").strip())},
        "sample": {"configured": True},
        "yfinance": {"configured": True},
    }


@app.get("/api/v1/scenarios")
def v1_scenarios(locale: str = "en"):
    from core.gas_scenarios import list_categories, list_scenarios

    return {"categories": list_categories(locale=locale), "scenarios": list_scenarios(locale=locale)}


@app.get("/api/v1/scenarios/{scenario_id}/context")
def v1_scenario_context(scenario_id: str, locale: str = "en", source: str = "sample"):
    from core.gas_scenarios import get_capacity_context, get_market_context, get_scenario

    try:
        return {
            "scenario": get_scenario(scenario_id, locale=locale),
            "market": get_market_context(scenario_id, source=source),
            "capacity": get_capacity_context(scenario_id),
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/v1/attempts/evaluate")
def v1_evaluate_attempt(payload: AttemptRequest):
    from core.gas_scenarios import get_capacity_context, get_scenario
    from core.learning_session import evaluate_attempt

    try:
        scenario = get_scenario(payload.scenario_id, locale=payload.locale)
        capacity = get_capacity_context(payload.scenario_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"evaluation": evaluate_attempt(scenario, capacity, payload.order, payload.rationale)}


@app.post("/api/v1/advisor/review")
def v1_advisor_review(payload: AdvisorRequest):
    from core.gas_scenarios import get_scenario
    from core.haineng_client import HainengClient, build_advisor_messages, build_haineng_tools

    scenario = get_scenario(payload.scenario_id, locale=payload.locale)
    client = HainengClient()
    if not client.is_configured():
        raise HTTPException(status_code=428, detail="海能 is required before advisor review.")
    answer = client.complete(
        build_advisor_messages(payload.locale, scenario, payload.evaluation, payload.rationale),
        tools=build_haineng_tools(),
    )
    return {"answer": answer}


@app.post("/api/v1/exam/generate")
def v1_exam_generate(payload: ExamRequest):
    from core.gas_scenarios import get_scenario
    from core.haineng_client import HainengClient, build_exam_messages

    scenario = get_scenario(payload.scenario_id, locale=payload.locale)
    client = HainengClient()
    if not client.is_configured():
        raise HTTPException(status_code=428, detail="海能 is required before exam generation.")
    answer = client.complete(build_exam_messages(payload.locale, scenario, payload.attempt_history))
    return {"exam": answer}
```

- [ ] **Step 4: Run backend tests**

Run:

```bash
pytest tests/test_tauri_backend_v1.py tests/test_pages_smoke.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tauri/backend/main.py tests/test_tauri_backend_v1.py
git commit -m "feat: expose natural gas lab backend endpoints"
```

---

### Task 5: Tauri Backend Bridge

**Files:**
- Modify: `tauri/src-tauri/src/main.rs`

- [ ] **Step 1: Add generic backend request command**

In `tauri/src-tauri/src/main.rs`, add this command after `simulate_backend`:

```rust
#[tauri::command]
fn backend_request(method: String, path: String, body: Option<Value>) -> Result<Value, String> {
    let client = Client::new();
    let normalized_path = if path.starts_with('/') { path } else { format!("/{}", path) };
    let url = format!("http://127.0.0.1:8000{}", normalized_path);
    let method_upper = method.to_uppercase();

    let response = match method_upper.as_str() {
        "GET" => client.get(&url).send(),
        "POST" => client.post(&url).json(&body.unwrap_or(Value::Null)).send(),
        _ => return Err(format!("unsupported method: {}", method)),
    }
    .map_err(|e| format!("request failed: {}", e))?;

    let status = response.status();
    let json: Value = response
        .json()
        .map_err(|e| format!("json decode failed: {}", e))?;

    if !status.is_success() {
        return Err(format!("backend status {}: {}", status.as_u16(), json));
    }
    Ok(json)
}
```

Update the handler:

```rust
.invoke_handler(tauri::generate_handler![ping_backend, simulate_backend, backend_request])
```

- [ ] **Step 2: Run Rust check if Rust toolchain is available**

Run:

```bash
cd tauri/src-tauri
cargo check
```

Expected: PASS. If the local machine lacks Rust dependencies, record the toolchain error and continue to frontend work.

- [ ] **Step 3: Commit**

```bash
git add tauri/src-tauri/src/main.rs
git commit -m "feat: add generic tauri backend bridge"
```

---

### Task 6: Frontend Test Harness, i18n, And API Helper

**Files:**
- Modify: `tauri/tauri-frontend/package.json`
- Modify: `tauri/tauri-frontend/index.html`
- Modify: `tauri/tauri-frontend/src/main.jsx`
- Create: `tauri/tauri-frontend/src/i18n.js`
- Create: `tauri/tauri-frontend/src/api.js`
- Create: `tauri/tauri-frontend/src/App.test.jsx`

- [ ] **Step 1: Add frontend dependencies and scripts**

Modify `tauri/tauri-frontend/package.json` so scripts and devDependencies include:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.8",
    "@testing-library/react": "^16.0.1",
    "@vitejs/plugin-react": "^4.0.0",
    "jsdom": "^24.1.1",
    "vite": "^5.0.0",
    "vitest": "^2.0.5"
  }
}
```

- [ ] **Step 2: Replace duplicate HTML with one Vite document**

Replace `tauri/tauri-frontend/index.html` with:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Commodity Lab</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 3: Add i18n tests**

Create `tauri/tauri-frontend/src/App.test.jsx`:

```jsx
import { describe, expect, it } from "vitest";
import { dictionaries, t } from "./i18n";

describe("i18n catalog", () => {
  it("has matching English and Mandarin keys", () => {
    expect(Object.keys(dictionaries.zh).sort()).toEqual(Object.keys(dictionaries.en).sort());
  });

  it("falls back to English for unknown locale", () => {
    expect(t("missingRequired", "fr")).toBe("Missing required settings");
  });
});
```

- [ ] **Step 4: Run frontend tests and verify they fail for missing i18n**

Run:

```bash
cd tauri/tauri-frontend
npm install
npm run test
```

Expected: FAIL with module resolution error for `./i18n`.

- [ ] **Step 5: Add i18n module**

Create `tauri/tauri-frontend/src/i18n.js`:

```js
export const dictionaries = {
  en: {
    appTitle: "Commodity Lab",
    setupTitle: "海能 Setup",
    setupSubtitle: "Configure 海能 before starting the guided training loop.",
    apiKey: "API Key",
    baseUrl: "Base URL",
    model: "Model",
    saveSettings: "Save settings",
    missingRequired: "Missing required settings",
    naturalGas: "Natural Gas",
    constructing: "Constructing",
    scenarioDeck: "Scenario Deck",
    marketContext: "Market Context",
    pipelineCapacity: "Pipeline Capacity",
    orderTicket: "Order Ticket",
    advisor: "海能 Advisor",
    exam: "Exam",
    understandExposure: "Understand exposure",
    inspectMarket: "Inspect market",
    placeHedge: "Place hedge",
    reviewScore: "Review score",
    side: "Side",
    quantity: "Quantity",
    hedgeType: "Hedge type",
    rationale: "Rationale",
    submitOrder: "Submit order",
    askHint: "Ask for hint",
    generateExam: "Generate exam",
    providerHealthy: "Provider healthy",
    providerRequired: "海能 required",
  },
  zh: {
    appTitle: "天然气套保训练实验室",
    setupTitle: "海能设置",
    setupSubtitle: "请先配置海能，再开始引导式训练。",
    apiKey: "API 密钥",
    baseUrl: "服务地址",
    model: "模型",
    saveSettings: "保存设置",
    missingRequired: "缺少必填设置",
    naturalGas: "天然气",
    constructing: "建设中",
    scenarioDeck: "场景列表",
    marketContext: "市场信息",
    pipelineCapacity: "管道运力",
    orderTicket: "下单面板",
    advisor: "海能顾问",
    exam: "测验",
    understandExposure: "识别风险敞口",
    inspectMarket: "观察市场",
    placeHedge: "建立套保",
    reviewScore: "复盘评分",
    side: "方向",
    quantity: "数量",
    hedgeType: "套保类型",
    rationale: "操作理由",
    submitOrder: "提交订单",
    askHint: "获取提示",
    generateExam: "生成测验",
    providerHealthy: "服务正常",
    providerRequired: "需要配置海能",
  },
};

export function normalizeLocale(locale) {
  return locale === "zh" ? "zh" : "en";
}

export function t(key, locale = "en") {
  const normalized = normalizeLocale(locale);
  return dictionaries[normalized][key] ?? dictionaries.en[key] ?? key;
}
```

- [ ] **Step 6: Add API helper**

Create `tauri/tauri-frontend/src/api.js`:

```js
import { invoke } from "@tauri-apps/api/tauri";

export async function backendRequest(method, path, body = null) {
  if (window.__COMMODITY_LAB_BACKEND__) {
    return window.__COMMODITY_LAB_BACKEND__(method, path, body);
  }
  return invoke("backend_request", { method, path, body });
}
```

- [ ] **Step 7: Import stylesheet entry**

Modify `tauri/tauri-frontend/src/main.jsx`:

```jsx
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

createRoot(document.getElementById("root")).render(<App />);
```

- [ ] **Step 8: Run frontend i18n tests**

Run:

```bash
cd tauri/tauri-frontend
npm run test
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add tauri/tauri-frontend/package.json tauri/tauri-frontend/package-lock.json tauri/tauri-frontend/index.html tauri/tauri-frontend/src/main.jsx tauri/tauri-frontend/src/i18n.js tauri/tauri-frontend/src/api.js tauri/tauri-frontend/src/App.test.jsx
git commit -m "feat: add frontend i18n and api foundation"
```

---

### Task 7: Professional Guided Terminal UI And Visual Aids

**Files:**
- Replace: `tauri/tauri-frontend/src/App.jsx`
- Create: `tauri/tauri-frontend/src/styles.css`
- Modify: `tauri/tauri-frontend/src/App.test.jsx`

- [ ] **Step 1: Extend frontend tests for shell behavior**

Append to `tauri/tauri-frontend/src/App.test.jsx`:

```jsx
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import App from "./App";

describe("Commodity Lab shell", () => {
  it("renders the setup gate when 海能 is not healthy", async () => {
    window.__COMMODITY_LAB_BACKEND__ = async () => ({
      haineng: { ok: false, configured: false },
      sample: { configured: true },
      yfinance: { configured: true },
      platts: { configured: false },
    });
    render(<App />);
    expect(await screen.findByText("海能 Setup")).toBeInTheDocument();
  });

  it("renders constructing navigation for future categories", async () => {
    window.__COMMODITY_LAB_BACKEND__ = async (method, path) => {
      if (path === "/api/v1/provider-status") {
        return { haineng: { ok: true, configured: true }, sample: { configured: true } };
      }
      return {
        categories: [
          { id: "natural_gas", label: "Natural Gas", status: "enabled" },
          { id: "oil_products", label: "Oil Products", status: "constructing" },
        ],
        scenarios: [],
      };
    };
    render(<App />);
    expect(await screen.findByText("Oil Products")).toBeInTheDocument();
    expect(await screen.findByText("Constructing")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run frontend tests and verify App still fails expectations**

Run:

```bash
cd tauri/tauri-frontend
npm run test
```

Expected: FAIL because the current `App.jsx` has not yet rendered Commodity Lab with the required V1 module shell.

- [ ] **Step 3: Replace App with V1 shell and visual-aid components**

Replace `tauri/tauri-frontend/src/App.jsx` with:

```jsx
import React, { useEffect, useMemo, useState } from "react";
import { backendRequest } from "./api";
import { normalizeLocale, t } from "./i18n";

const defaultOrder = { side: "sell", quantity: 60000, hedge_type: "short_hedge", price: 3.5 };

function LanguageToggle({ locale, setLocale }) {
  return (
    <div className="segmented" aria-label="Language">
      <button className={locale === "en" ? "active" : ""} onClick={() => setLocale("en")}>EN</button>
      <button className={locale === "zh" ? "active" : ""} onClick={() => setLocale("zh")}>中文</button>
    </div>
  );
}

function SetupGate({ locale, providerStatus }) {
  const healthy = providerStatus?.haineng?.ok;
  return (
    <section className="setup-gate">
      <div>
        <h1>{t("setupTitle", locale)}</h1>
        <p>{t("setupSubtitle", locale)}</p>
      </div>
      <div className="setup-grid">
        <label>{t("apiKey", locale)}<input type="password" aria-label={t("apiKey", locale)} /></label>
        <label>{t("baseUrl", locale)}<input aria-label={t("baseUrl", locale)} /></label>
        <label>{t("model", locale)}<input defaultValue="V4-Flash" aria-label={t("model", locale)} /></label>
      </div>
      <div className={healthy ? "status ok" : "status warn"}>
        {healthy ? t("providerHealthy", locale) : t("providerRequired", locale)}
      </div>
    </section>
  );
}

function ConstructingView({ label, locale }) {
  return (
    <div className="constructing">
      <span>{label}</span>
      <strong>{t("constructing", locale)}</strong>
    </div>
  );
}

function ScenarioDeck({ locale, scenarios, categories, selectedId, setSelectedId }) {
  return (
    <aside className="panel scenario-deck">
      <h2>{t("scenarioDeck", locale)}</h2>
      {scenarios.map((scenario) => (
        <button
          key={scenario.id}
          className={scenario.id === selectedId ? "scenario active" : "scenario"}
          onClick={() => setSelectedId(scenario.id)}
        >
          <strong>{scenario.title}</strong>
          <span>{scenario.summary}</span>
        </button>
      ))}
      <div className="future-list">
        {categories.filter((category) => category.status === "constructing").map((category) => (
          <ConstructingView key={category.id} label={category.label} locale={locale} />
        ))}
      </div>
    </aside>
  );
}

function MarketChart({ locale, market }) {
  const points = market?.price_series ?? [];
  const max = Math.max(...points.map((point) => point.close), 1);
  return (
    <section className="panel">
      <h2>{t("marketContext", locale)}</h2>
      <div className="chart" role="img" aria-label={t("marketContext", locale)}>
        {points.map((point) => (
          <span key={point.date} style={{ height: `${(point.close / max) * 100}%` }} title={`${point.date}: ${point.close}`} />
        ))}
      </div>
      <p className="muted">{market?.symbol} · {market?.unit} · {market?.source}</p>
    </section>
  );
}

function CapacityDiagram({ locale, capacity }) {
  const utilization = capacity?.utilization_pct ?? 0;
  return (
    <section className="panel">
      <h2>{t("pipelineCapacity", locale)}</h2>
      <div className="capacity-flow">
        <span>{capacity?.receipt_point}</span>
        <div className="pipe"><i style={{ width: `${Math.min(100, utilization)}%` }} /></div>
        <span>{capacity?.delivery_point}</span>
      </div>
      <div className="metric-row">
        <span>Utilization</span>
        <strong>{utilization}%</strong>
      </div>
    </section>
  );
}

function GuidedStepper({ locale }) {
  const steps = ["understandExposure", "inspectMarket", "placeHedge", "reviewScore", "exam"];
  return (
    <ol className="stepper">
      {steps.map((step, index) => (
        <li key={step} className={index === 0 ? "active" : ""}>{t(step, locale)}</li>
      ))}
    </ol>
  );
}

function OrderTicket({ locale, order, setOrder, onSubmit }) {
  return (
    <section className="panel order-ticket">
      <h2>{t("orderTicket", locale)}</h2>
      <label>{t("side", locale)}
        <select value={order.side} onChange={(event) => setOrder({ ...order, side: event.target.value })}>
          <option value="sell">Sell</option>
          <option value="buy">Buy</option>
        </select>
      </label>
      <label>{t("quantity", locale)}
        <input type="number" value={order.quantity} onChange={(event) => setOrder({ ...order, quantity: Number(event.target.value) })} />
      </label>
      <label>{t("hedgeType", locale)}
        <select value={order.hedge_type} onChange={(event) => setOrder({ ...order, hedge_type: event.target.value })}>
          <option value="short_hedge">Short hedge</option>
          <option value="long_hedge">Long hedge</option>
          <option value="basis_hedge">Basis hedge</option>
          <option value="calendar_spread">Calendar spread</option>
        </select>
      </label>
      <button className="primary" onClick={onSubmit}>{t("submitOrder", locale)}</button>
    </section>
  );
}

function AdvisorRail({ locale, evaluation }) {
  return (
    <aside className="panel advisor">
      <h2>{t("advisor", locale)}</h2>
      <GuidedStepper locale={locale} />
      <div className="score-box">{evaluation?.baseline_score ?? "--"}</div>
      <button>{t("askHint", locale)}</button>
      <button>{t("generateExam", locale)}</button>
    </aside>
  );
}

export default function App() {
  const [locale, setLocaleState] = useState(() => normalizeLocale(localStorage.getItem("commodity-lab-locale")));
  const [providerStatus, setProviderStatus] = useState(null);
  const [categories, setCategories] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [context, setContext] = useState(null);
  const [order, setOrder] = useState(defaultOrder);
  const [evaluation, setEvaluation] = useState(null);

  function setLocale(nextLocale) {
    localStorage.setItem("commodity-lab-locale", nextLocale);
    setLocaleState(nextLocale);
  }

  useEffect(() => {
    backendRequest("GET", "/api/v1/provider-status").then(setProviderStatus).catch(() => setProviderStatus({ haineng: { ok: false } }));
  }, []);

  useEffect(() => {
    if (!providerStatus?.haineng?.ok) return;
    backendRequest("GET", `/api/v1/scenarios?locale=${locale}`).then((payload) => {
      setCategories(payload.categories ?? []);
      setScenarios(payload.scenarios ?? []);
      setSelectedId((payload.scenarios ?? [])[0]?.id ?? "");
    });
  }, [providerStatus, locale]);

  useEffect(() => {
    if (!selectedId) return;
    backendRequest("GET", `/api/v1/scenarios/${selectedId}/context?locale=${locale}`).then(setContext);
  }, [selectedId, locale]);

  const selectedScenario = useMemo(() => scenarios.find((scenario) => scenario.id === selectedId), [scenarios, selectedId]);

  async function submitOrder() {
    const payload = await backendRequest("POST", "/api/v1/attempts/evaluate", {
      scenario_id: selectedId,
      locale,
      order,
      rationale: "User submitted hedge order from V1 ticket.",
    });
    setEvaluation(payload.evaluation);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <h1>{t("appTitle", locale)}</h1>
        <LanguageToggle locale={locale} setLocale={setLocale} />
      </header>
      {!providerStatus?.haineng?.ok ? (
        <SetupGate locale={locale} providerStatus={providerStatus} />
      ) : (
        <div className="terminal-grid">
          <ScenarioDeck locale={locale} scenarios={scenarios} categories={categories} selectedId={selectedId} setSelectedId={setSelectedId} />
          <section className="workspace">
            <div className="workspace-title">
              <h2>{selectedScenario?.title}</h2>
              <p>{selectedScenario?.summary}</p>
            </div>
            <div className="workspace-grid">
              <MarketChart locale={locale} market={context?.market} />
              <CapacityDiagram locale={locale} capacity={context?.capacity} />
              <OrderTicket locale={locale} order={order} setOrder={setOrder} onSubmit={submitOrder} />
              <section className="panel">
                <h2>Metrics</h2>
                <pre>{JSON.stringify(evaluation?.metrics ?? {}, null, 2)}</pre>
              </section>
            </div>
          </section>
          <AdvisorRail locale={locale} evaluation={evaluation} />
        </div>
      )}
    </main>
  );
}
```

- [ ] **Step 4: Add visual system CSS**

Create `tauri/tauri-frontend/src/styles.css`:

```css
:root {
  color-scheme: dark;
  font-family: Inter, "Segoe UI", system-ui, sans-serif;
  background: #0c1116;
  color: #e9eef3;
}

* { box-sizing: border-box; }
body { margin: 0; min-width: 1024px; background: #0c1116; }
button, input, select { font: inherit; }
button { cursor: pointer; }

.app-shell { min-height: 100vh; padding: 18px; }
.topbar { display: flex; justify-content: space-between; align-items: center; height: 48px; }
.topbar h1 { margin: 0; font-size: 20px; font-weight: 650; }
.segmented { display: inline-flex; border: 1px solid #293744; border-radius: 6px; overflow: hidden; }
.segmented button { border: 0; padding: 7px 12px; color: #9fb1c1; background: #111922; }
.segmented button.active { color: #ffffff; background: #1f6feb; }

.setup-gate { max-width: 860px; margin: 72px auto; padding: 28px; border: 1px solid #24313d; border-radius: 8px; background: #111922; }
.setup-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
label { display: grid; gap: 6px; color: #9fb1c1; font-size: 12px; }
input, select { width: 100%; min-height: 36px; border: 1px solid #2a3947; border-radius: 6px; padding: 0 10px; color: #e9eef3; background: #0d141b; }
.status { margin-top: 16px; padding: 10px 12px; border-radius: 6px; }
.status.ok { background: #11351f; color: #8ee0a1; }
.status.warn { background: #3c2912; color: #ffc978; }

.terminal-grid { display: grid; grid-template-columns: 260px minmax(520px, 1fr) 300px; gap: 14px; align-items: start; }
.panel { border: 1px solid #24313d; border-radius: 8px; background: #111922; padding: 14px; min-height: 120px; }
.panel h2 { margin: 0 0 12px; font-size: 14px; color: #f4f7fa; }
.scenario-deck { display: grid; gap: 10px; }
.scenario { display: grid; gap: 5px; text-align: left; border: 1px solid #263542; border-radius: 6px; padding: 10px; color: #d8e3ea; background: #0d141b; }
.scenario span { color: #91a4b5; font-size: 12px; line-height: 1.35; }
.scenario.active { border-color: #1f6feb; background: #12243a; }
.future-list { display: grid; gap: 8px; margin-top: 8px; }
.constructing { display: flex; justify-content: space-between; gap: 8px; color: #8c9baa; font-size: 12px; border-top: 1px solid #253341; padding-top: 8px; }

.workspace { display: grid; gap: 12px; }
.workspace-title { border: 1px solid #24313d; border-radius: 8px; padding: 14px; background: #101821; }
.workspace-title h2 { margin: 0 0 4px; font-size: 18px; }
.workspace-title p { margin: 0; color: #9fb1c1; }
.workspace-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.chart { display: flex; align-items: end; gap: 6px; height: 120px; padding-top: 10px; border-bottom: 1px solid #324454; }
.chart span { flex: 1; min-height: 8px; background: linear-gradient(180deg, #58a6ff, #1f6feb); border-radius: 3px 3px 0 0; }
.muted { color: #91a4b5; font-size: 12px; }
.capacity-flow { display: grid; grid-template-columns: 1fr 2fr 1fr; align-items: center; gap: 10px; color: #cbd7e1; font-size: 12px; }
.pipe { height: 18px; border: 1px solid #37506a; border-radius: 999px; overflow: hidden; background: #0a1016; }
.pipe i { display: block; height: 100%; background: #f0883e; }
.metric-row { display: flex; justify-content: space-between; margin-top: 14px; color: #9fb1c1; }
.order-ticket { display: grid; gap: 10px; }
.primary { min-height: 38px; border: 0; border-radius: 6px; color: white; background: #238636; }
.advisor { display: grid; gap: 12px; }
.stepper { display: grid; gap: 8px; padding: 0; margin: 0; list-style: none; }
.stepper li { padding: 8px; border-left: 3px solid #314252; color: #9fb1c1; background: #0d141b; }
.stepper li.active { border-left-color: #1f6feb; color: #f4f7fa; }
.score-box { display: grid; place-items: center; height: 86px; font-size: 36px; font-weight: 700; border: 1px solid #2a3947; border-radius: 8px; background: #0d141b; }
pre { white-space: pre-wrap; color: #c8d3dc; font-size: 12px; }
```

- [ ] **Step 5: Run frontend tests and build**

Run:

```bash
cd tauri/tauri-frontend
npm run test
npm run build
```

Expected: PASS for both commands.

- [ ] **Step 6: Commit**

```bash
git add tauri/tauri-frontend/src/App.jsx tauri/tauri-frontend/src/styles.css tauri/tauri-frontend/src/App.test.jsx
git commit -m "feat: build guided natural gas lab shell"
```

---

### Task 8: 海能 Advisor And Exam Flow Wiring

**Files:**
- Modify: `tauri/tauri-frontend/src/App.jsx`
- Modify: `tauri/tauri-frontend/src/i18n.js`
- Modify: `tauri/tauri-frontend/src/App.test.jsx`

- [ ] **Step 1: Add UI strings for advisor and exam output**

Add these keys to both `en` and `zh` in `src/i18n.js`:

```js
advisorFeedback: "Advisor feedback",
examQuestions: "Exam questions",
retry: "Retry",
```

Mandarin values:

```js
advisorFeedback: "顾问反馈",
examQuestions: "测验题目",
retry: "重试",
```

- [ ] **Step 2: Add advisor/exam test**

Append to `App.test.jsx`:

```jsx
it("requests exam generation through backend helper", async () => {
  const calls = [];
  window.__COMMODITY_LAB_BACKEND__ = async (method, path, body) => {
    calls.push({ method, path, body });
    if (path === "/api/v1/provider-status") return { haineng: { ok: true, configured: true } };
    if (path.startsWith("/api/v1/scenarios?")) {
      return {
        categories: [{ id: "natural_gas", label: "Natural Gas", status: "enabled" }],
        scenarios: [{ id: "producer_short_hedge", title: "Producer Short Hedge", summary: "Protect revenue", commodity: "natural_gas" }],
      };
    }
    if (path.includes("/context")) {
      return { market: { price_series: [], symbol: "NG=F" }, capacity: { utilization_pct: 65 } };
    }
    if (path === "/api/v1/exam/generate") return { exam: "1. What is the exposure?" };
    return { evaluation: { valid: true, baseline_score: 80, metrics: {} } };
  };
  render(<App />);
  const button = await screen.findByText("Generate exam");
  button.click();
  expect(await screen.findByText("1. What is the exposure?")).toBeInTheDocument();
  expect(calls.some((call) => call.path === "/api/v1/exam/generate")).toBe(true);
});
```

- [ ] **Step 3: Wire advisor and exam state**

In `App.jsx`, add state:

```jsx
const [advisorFeedback, setAdvisorFeedback] = useState("");
const [exam, setExam] = useState("");
```

Add functions inside `App`:

```jsx
async function requestAdvisorReview(nextEvaluation = evaluation) {
  if (!nextEvaluation || !selectedId) return;
  const payload = await backendRequest("POST", "/api/v1/advisor/review", {
    scenario_id: selectedId,
    locale,
    order,
    rationale: "User submitted hedge order from V1 ticket.",
    evaluation: nextEvaluation,
  });
  setAdvisorFeedback(payload.answer);
}

async function generateExam() {
  const payload = await backendRequest("POST", "/api/v1/exam/generate", {
    scenario_id: selectedId,
    locale,
    attempt_history: evaluation ? [evaluation] : [],
  });
  setExam(payload.exam);
}
```

Update `submitOrder`:

```jsx
async function submitOrder() {
  const payload = await backendRequest("POST", "/api/v1/attempts/evaluate", {
    scenario_id: selectedId,
    locale,
    order,
    rationale: "User submitted hedge order from V1 ticket.",
  });
  setEvaluation(payload.evaluation);
  await requestAdvisorReview(payload.evaluation);
}
```

Pass props to `AdvisorRail`:

```jsx
<AdvisorRail
  locale={locale}
  evaluation={evaluation}
  advisorFeedback={advisorFeedback}
  exam={exam}
  generateExam={generateExam}
/>
```

Update `AdvisorRail` signature and body:

```jsx
function AdvisorRail({ locale, evaluation, advisorFeedback, exam, generateExam }) {
  return (
    <aside className="panel advisor">
      <h2>{t("advisor", locale)}</h2>
      <GuidedStepper locale={locale} />
      <div className="score-box">{evaluation?.baseline_score ?? "--"}</div>
      <button>{t("askHint", locale)}</button>
      <button onClick={generateExam}>{t("generateExam", locale)}</button>
      {advisorFeedback && (
        <section className="response-block">
          <h3>{t("advisorFeedback", locale)}</h3>
          <p>{advisorFeedback}</p>
        </section>
      )}
      {exam && (
        <section className="response-block">
          <h3>{t("examQuestions", locale)}</h3>
          <p>{exam}</p>
        </section>
      )}
    </aside>
  );
}
```

- [ ] **Step 4: Add response CSS**

Append to `styles.css`:

```css
.response-block { border-top: 1px solid #253341; padding-top: 10px; }
.response-block h3 { margin: 0 0 6px; font-size: 13px; }
.response-block p { margin: 0; color: #cbd7e1; font-size: 13px; line-height: 1.45; }
```

- [ ] **Step 5: Run frontend tests and build**

Run:

```bash
cd tauri/tauri-frontend
npm run test
npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tauri/tauri-frontend/src/App.jsx tauri/tauri-frontend/src/i18n.js tauri/tauri-frontend/src/App.test.jsx tauri/tauri-frontend/src/styles.css
git commit -m "feat: wire haineng advisor and exam flow"
```

---

### Task 9: End-To-End Verification And Documentation Update

**Files:**
- Modify: `README.md`
- Verify: backend tests, frontend tests, frontend build, optional Tauri check

- [ ] **Step 1: Update README V1 run instructions**

Add a concise V1 section to `README.md`:

````markdown
## Commodity Lab V1 Natural Gas Hedging

V1 is Commodity Lab's Tauri desktop natural gas hedging module. The training loop requires a user-provided 海能 API key and base URL. Platts is optional; sample/Yahoo Finance data keeps the natural gas scenarios usable when Platts is not configured.

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r tauri/backend/requirements.txt
python tauri/backend/main.py
```

### Frontend

```bash
cd tauri/tauri-frontend
npm install
npm run dev
```

### Checks

```bash
pytest tests/test_gas_scenarios.py tests/test_learning_session.py tests/test_haineng_client.py tests/test_tauri_backend_v1.py tests/test_pages_smoke.py -q
cd tauri/tauri-frontend
npm run test
npm run build
```
````

- [ ] **Step 2: Run backend focused tests**

Run:

```bash
pytest tests/test_gas_scenarios.py tests/test_learning_session.py tests/test_haineng_client.py tests/test_tauri_backend_v1.py tests/test_pages_smoke.py -q
```

Expected: PASS. If dependencies are missing, run:

```bash
python -m pip install -r requirements.txt -r tauri/backend/requirements.txt
```

Then rerun the same pytest command.

- [ ] **Step 3: Run frontend checks**

Run:

```bash
cd tauri/tauri-frontend
npm install
npm run test
npm run build
```

Expected: PASS.

- [ ] **Step 4: Run optional Rust check**

Run:

```bash
cd tauri/src-tauri
cargo check
```

Expected: PASS when Rust/Tauri dependencies are installed.

- [ ] **Step 5: Manual browser verification**

Run:

```bash
python tauri/backend/main.py
```

In another terminal:

```bash
cd tauri/tauri-frontend
npm run dev
```

Open the Vite URL. Verify:

- Setup gate appears when 海能 is not configured.
- English/Mandarin toggle changes all first-party UI text.
- With mocked or configured 海能 provider status, natural gas scenario deck appears.
- Future categories show `Constructing`.
- Market chart, capacity diagram, order ticket, score box, and guided rail are visible.
- Invalid quantity is rejected by backend evaluation.
- Valid order returns deterministic metrics.
- Advisor/exam requests call the backend and show returned text.

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs: document natural gas lab v1 checks"
```

---

## Plan Self-Review Notes

Spec coverage:

- Natural-gas-only scope: Tasks 1, 4, 7.
- Pipeline capacity sample mode: Tasks 1, 2, 7.
- Mandatory 海能 setup and provider branding: Tasks 3, 4, 7, 8.
- Bilingual English/Mandarin UI and locale-aware 海能 prompts: Tasks 3, 6, 7, 8.
- Professional visual aids: Tasks 7 and 9.
- Other tabs/categories as `Constructing`: Tasks 1, 7.
- Tests and delivery verification: Tasks 1 through 9.

Type consistency:

- Scenario identifiers use `scenario_id` in backend requests and `selectedId` in frontend state.
- Locale values are `en` and `zh`.
- Order fields are `side`, `quantity`, `hedge_type`, and `price`.
- Evaluation responses contain `valid`, `metrics`, `score_inputs`, `mistake_tags`, and `baseline_score`.
