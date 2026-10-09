"""Independent arithmetic references and information/policy boundaries."""
from decimal import Decimal as D
from concurrent.futures import ThreadPoolExecutor
import json
import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from core.risk_training import (Decision, Policy, collateral, initial_state, policy_check,
                                settlement, submit, swap_cash_flow, visible_state)
from core.risk_training_store import SessionStore
from tauri.backend.main import app
from tauri.backend.risk_training_api import coach_messages


def decision(cp=0, target="8000", **changes):
    return Decision(checkpoint=cp, target_mwh=target,
                    rationale="Hedge rising purchase costs while preserving basis and collateral capacity.",
                    exposure_answer="rising_purchase_cost", basis_answer="basis_remains",
                    liquidity_answer="collateral_needed", **changes)


def complete(first="8000", second="6400", policy=None):
    s, _ = submit(initial_state(policy or Policy()), decision(target=first))
    s, _ = submit(s, decision(cp=1, target=second))
    return s


def test_independently_derived_resize_and_cash_flows():
    # Buy 8k at 40; close 1.6k at 50: realized 16k + remaining 6.4k*(55-40)=96k.
    # Physical: 8k*(55+5)=480k. Budget: 8k*(40+2)=336k.
    # Net cost=480k-112k=368k; budget saving=-32k; shock offset=112/144.
    result = settlement(complete())
    assert result["physical_sales_cash_flow_eur"] == 480000
    assert result["unhedged_physical_margin_eur"] == 0
    assert result["commercial_margin_before_costs_eur"] == 112000
    assert result["physical_cash_flow_eur"] == -480000
    assert result["derivative_cash_flow_eur"] == 112000
    assert result["net_procurement_cost_eur"] == 368000
    assert result["volume_adjusted_budget_eur"] == 336000
    assert result["budget_variance_eur"] == -32000
    assert result["basis_cost_eur"] == 40000
    assert result["cost_shock_offset_pct"] == 77.78
    assert result["peak_collateral_estimate_eur"] == 40000
    assert result["realized_commercial_pnl"] is None


@pytest.mark.parametrize("first,second,cash,cost", [("0", "0", 0, 480000), ("5000", "4000", 70000, 410000), ("8000", "6400", 112000, 368000)])
def test_multiple_defensible_strategies(first, second, cash, cost):
    s = complete(first, second)
    assert settlement(s)["derivative_cash_flow_eur"] == cash
    assert settlement(s)["net_procurement_cost_eur"] == cost
    assert all(r["assessment"]["decision_quality"]["diagnostic_score"] == 100 for r in s["decisions"])


def test_falling_price_reference_long_losses_short_receipts_and_collateral():
    trades = [{"delta_mwh": "8000", "entry_eur_mwh": "40"}]
    assert swap_cash_flow(trades, D(30)) == -80000
    assert collateral(trades, D(30), D(8000)) == 104000  # 24k initial + 80k adverse MTM
    assert swap_cash_flow([{"delta_mwh": "-8000", "entry_eur_mwh": "40"}], D(30)) == 80000
    assert not policy_check(Policy(), D(8000), D(10000), D(104000))["permitted"]


def test_fractional_quantities_and_exact_limit():
    p = Policy(maximum_hedge_ratio="0.8")
    assert policy_check(p, D("0.08"), D("0.1"), D(0))["permitted"]
    assert not policy_check(p, D("0.08000000001"), D("0.1"), D(0))["permitted"]
    assert swap_cash_flow([{"delta_mwh": "1.25", "entry_eur_mwh": "40.10"}], D("40.30")) == D("0.2500")


def test_policy_checks_cumulative_target_not_incremental_trade_and_new_nomination():
    s, a = submit(initial_state(Policy()), decision())
    assert a["compliance"]["permitted"]
    assert not visible_state(s)["current_compliance"]["permitted"]
    refused, a = submit(s, decision(cp=1, target="8000"))
    assert not a["compliance"]["permitted"]
    assert refused["checkpoint"] == 1 and refused["trades"] == s["trades"]
    revised, a = submit(refused, decision(cp=1, target="6400"))
    assert a["compliance"]["permitted"] and revised["checkpoint"] == 2
    assert len(revised["proposals"]) == 3


def test_policy_direction_backing_approval_and_instrument():
    assert "physical_backing_required" in policy_check(Policy(), D(-100), D(10000), D(0))["reasons"]
    assert "physical_backing_required" in policy_check(Policy(), D(1), D(0), D(0))["reasons"]
    p = Policy(approval_ratio="0.5")
    assert "approval_required" in policy_check(p, D(8000), D(10000), D(0))["reasons"]
    assert policy_check(p, D(8000), D(10000), D(0), True)["permitted"]
    assert not policy_check(Policy(permitted_instruments=()), D(100), D(10000), D(0))["permitted"]
    academy = Policy(profile="academy", maximum_hedge_ratio="1.5", approval_ratio="2", physical_backing_required=False)
    assert policy_check(academy, D(-1000), D(10000), D(0))["permitted"]


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity", True, "20001"])
def test_invalid_quantities(bad):
    with pytest.raises(ValidationError):
        decision(target=bad)


@pytest.mark.parametrize("field,value", [("instrument", "call"), ("unit", "MMBtu"), ("currency", "USD"), ("delivery_period", "2026-12"), ("pricing_period", "2026-12"), ("commodity", "crude_oil")])
def test_convention_mismatch_rejected(field, value):
    data = decision().model_dump(); data[field] = value
    with pytest.raises(ValidationError):
        Decision(**data)


def test_settlement_and_ai_payload_have_no_future_information():
    s = initial_state(Policy())
    payload = visible_state(s)
    assert "financial" not in payload
    assert len(payload["visible_timeline"]) == 1
    serialized = json.dumps(coach_messages(payload, "en"))
    assert "2026-10-15" not in serialized and "2026-11-30" not in serialized
    with pytest.raises(ValueError):
        settlement(s)
    with pytest.raises(ValueError):
        submit(s, decision(cp=1))


def test_decision_evidence_is_separate_from_profit():
    s = complete()
    bad = decision().model_dump(); bad["basis_answer"] = "all_risk_removed"
    _, assessment = submit(initial_state(Policy()), Decision(**bad))
    assert assessment["decision_quality"]["remediation"] == ["basis"]
    assert assessment["decision_quality"]["reasoning_status"] == "requires_instructor_review"
    assert settlement(s)["budget_variance_eur"] < 0
    assert s["decisions"][0]["assessment"]["decision_quality"]["diagnostic_score"] == 100


def test_store_resume_snapshot_and_concurrent_submission(tmp_path):
    path = tmp_path / "training.sqlite"
    store = SessionStore(path)
    view = store.create(Policy())
    def act():
        try:
            return store.decide(view["id"], decision())["checkpoint"]
        except ValueError:
            return "stale"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: act(), range(2)), key=str) == [1, "stale"]
    resumed = SessionStore(path).view(view["id"])
    assert resumed["checkpoint"] == 1
    assert resumed["decisions"][0]["information_snapshot"]["physical_mwh"] == "10000"
    assert resumed["decisions"][0]["policy_snapshot"]["version"] == "illustrative-v1"
    assert "2026-11-30" not in json.dumps(resumed)


def test_api_end_to_end_rejects_tampering_and_resumes(tmp_path, monkeypatch):
    monkeypatch.setenv("COMMODITY_LAB_TRAINING_DB", str(tmp_path / "api.sqlite"))
    c = TestClient(app)
    v = c.post("/api/v1/risk-training/sessions", json={}).json()
    url = f'/api/v1/risk-training/sessions/{v["id"]}'
    malicious = decision().model_dump(mode="json"); malicious["settlement_price"] = 1000
    assert c.post(url + "/decisions", json=malicious).status_code == 422
    assert c.post(url + "/decisions", json=decision().model_dump(mode="json")).json()["checkpoint"] == 1
    assert c.post(url + "/decisions", json=decision().model_dump(mode="json")).status_code == 409
    assert c.get(url).json()["checkpoint"] == 1
    assert c.post(url + "/decisions", json=decision(cp=1, target="6400").model_dump(mode="json")).json()["financial"]["net_procurement_cost_eur"] == 368000
    assert c.get("/api/v1/risk-training/sessions/missing").status_code == 404


def test_coach_offline_and_mocked_provider_cannot_mutate_grade(tmp_path, monkeypatch):
    from core.haineng_client import HainengClient
    monkeypatch.setenv("COMMODITY_LAB_TRAINING_DB", str(tmp_path / "coach.sqlite"))
    c = TestClient(app); v = c.post("/api/v1/risk-training/sessions", json={}).json()
    url = f'/api/v1/risk-training/sessions/{v["id"]}'
    monkeypatch.setattr(HainengClient, "is_configured", lambda self: False)
    response = c.post(url + "/coach", json={"locale": "zh"}).json()
    assert response["mode"] == "offline" and "区域基差" in response["answer"]
    captured = []
    monkeypatch.setattr(HainengClient, "is_configured", lambda self: True)
    monkeypatch.setattr(HainengClient, "complete", lambda self, messages: captured.append(messages) or "Consider basis.")
    assert c.post(url + "/coach", json={"locale": "en"}).json() == {"mode": "ai", "answer": "Consider basis.", "graded": False}
    assert "2026-11-30" not in json.dumps(captured)
    assert c.get(url).json() == v
    def unavailable(self, messages):
        raise RuntimeError("secret")
    monkeypatch.setattr(HainengClient, "complete", unavailable)
    result = c.post(url + "/coach", json={}).json()
    assert result["mode"] == "offline_provider_unavailable" and "secret" not in json.dumps(result)


def test_pack_schema_and_version_cannot_silently_change_resume():
    from core.risk_training import Observation
    with pytest.raises(ValidationError):
        Observation(date="2026-10-01", index_eur_mwh="NaN", basis_eur_mwh="2", physical_mwh="10000", fact={"en": "short"})
    state = initial_state(Policy()); state["scenario_version"] = "unknown"
    with pytest.raises(ValueError, match="unsupported_scenario_version"):
        visible_state(state)


@pytest.mark.parametrize("number", [True, "NaN", "Infinity", "0.8000000000000000000000001"])
def test_policy_numbers_are_bounded_and_exact(number):
    with pytest.raises(ValidationError):
        Policy(maximum_hedge_ratio=number)


def test_trading_company_sales_and_margin_conservation():
    view = visible_state(initial_state(Policy()))
    assert view["conventions"]["role"] == "trading_company_physical_book"
    assert view["current"]["sale_price_eur_mwh"] == "60"
    assert "trading company" in view["current"]["fact"]["en"]
    assert "utility" not in view["current"]["fact"]["en"]
    for first, second, expected_margin in [("0", "0", 0), ("5000", "4000", 70000), ("8000", "6400", 112000)]:
        settled = visible_state(complete(first, second))
        f = settled["financial"]
        assert f["physical_sales_cash_flow_eur"] == 480000
        assert f["commercial_margin_before_costs_eur"] == expected_margin
        assert f["physical_sales_cash_flow_eur"] + f["physical_cash_flow_eur"] + f["derivative_cash_flow_eur"] == expected_margin
        assert settled["open_position_mwh"] == "0"
        assert settled["post_settlement_collateral_eur"] == 0
