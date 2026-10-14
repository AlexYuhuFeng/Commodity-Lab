"""Crude cash-flow references derived separately from the shared engine."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal as D
import json
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from core.crude_training import REFINERY, INVENTORY, PACKS
from core.training_contracts import CommodityDecision, ScenarioPack, ScenarioPolicy, ScenarioSessionRequest, PriceFixing, weighted_price
from core.training_engine import create_state, collateral, swap_receipt, submit_pack, settle_pack, visible_pack
from core.risk_training_store import SessionStore
from tauri.backend.main import app
from tauri.backend.risk_training_api import coach_messages


def decision(pack=REFINERY, checkpoint=0, target="480000", **changes):
    values = {k: getattr(pack.conventions, k) for k in ("commodity", "instrument", "unit", "currency", "delivery_period", "pricing_period", "pricing_window_start", "pricing_window_end")}
    values.update(checkpoint=checkpoint, target_quantity=target,
                  rationale="Protect the trading-company commercial margin while retaining grade and freight risk and a collateral reserve.",
                  exposure_answer="rising_purchase_cost" if pack.physical.hedge_sign == 1 else "falling_sales_revenue",
                  basis_answer="basis_remains", liquidity_answer="collateral_needed")
    values.update(changes)
    return CommodityDecision(**values)


def state(pack=REFINERY, policy=None):
    return create_state(ScenarioSessionRequest(scenario_id=pack.version, policy=policy or ScenarioPolicy()))


def finish(pack=REFINERY, first="480000", second="400000"):
    s, a = submit_pack(state(pack), decision(pack, 0, first))
    assert a["compliance"]["permitted"]
    s, a = submit_pack(s, decision(pack, 1, second))
    assert a["compliance"]["permitted"]
    return s


def test_refinery_independent_financial_reference():
    # Average Brent=(84+90+96)/3=90; grade=(1+3+5)/3=3.
    # Swap: released 80k*(86-80)=480k plus 400k*(90-80)=4m.
    # Sale=500k*94=47m; purchase=500k*93=46.5m; freight=500k*2.5=1.25m.
    f = settle_pack(finish())
    assert f["physical_sales_cash_flow"] == 47000000
    assert f["physical_purchase_cash_flow"] == -46500000
    assert f["freight_cash_flow"] == -1250000
    assert f["derivative_cash_flow"] == 4480000
    assert f["unhedged_physical_margin"] == -750000
    assert f["commercial_margin_before_costs"] == 3730000
    assert f["net_procurement_cost"] == 43270000
    assert f["volume_adjusted_baseline_physical_margin"] == 5500000
    assert f["margin_variance"] == -1770000
    assert f["adverse_margin_shock_offset_pct"] == 71.68
    assert f["peak_collateral_estimate"] == 4128000
    assert f["settlement_net_cash_flow"] == 3730000
    assert sum(row["amount"] for row in f["cash_flows"]) == f["commercial_margin_before_costs"]


def test_inventory_independent_financial_reference_and_payment_timing():
    # Sales=300k*(74+1)=22.5m, historical cost=300k*77=23.1m,
    # freight=300k*1.5=450k, short receipts=240k*(80-74)=1.44m.
    # Lifecycle margin=390k; today cash=22.5m-450k+1.44m=23.49m.
    f = settle_pack(finish(INVENTORY, "-240000", "-240000"))
    assert f["physical_sales_cash_flow"] == 22500000
    assert f["physical_purchase_cash_flow"] == -23100000
    assert f["freight_cash_flow"] == -450000
    assert f["derivative_cash_flow"] == 1440000
    assert f["unhedged_physical_margin"] == -1050000
    assert f["commercial_margin_before_costs"] == 390000
    assert f["settlement_net_cash_flow"] == 23490000
    assert f["volume_adjusted_baseline_physical_margin"] == 1200000
    assert f["adverse_margin_shock_offset_pct"] == 64
    assert f["peak_collateral_estimate"] == 1920000
    assert "net_procurement_cost" not in f
    purchase = next(r for r in f["cash_flows"] if r["kind"] == "physical_purchase")
    assert purchase["date"] == "2026-09-15"
    assert sum(row["amount"] for row in f["cash_flows"] if row["date"] == "2026-11-30") == f["settlement_net_cash_flow"]
    assert sum(row["amount"] for row in f["cash_flows"]) == f["commercial_margin_before_costs"]


@pytest.mark.parametrize("pack,first,second,margin", [(REFINERY,"0","0",-750000), (REFINERY,"300000","250000",2050000), (REFINERY,"480000","400000",3730000), (INVENTORY,"0","0",-1050000), (INVENTORY,"-150000","-150000",-150000), (INVENTORY,"-240000","-240000",390000)])
def test_multiple_defensible_solutions_do_not_grade_by_profit(pack, first, second, margin):
    s = finish(pack, first, second)
    assert settle_pack(s)["commercial_margin_before_costs"] == margin
    assert all(r["assessment"]["decision_quality"]["diagnostic_score"] == 100 for r in s["decisions"])


def test_short_rally_collateral_and_fractional_signed_swaps():
    trades = [{"delta_quantity": "-240000", "entry_price": "80"}]
    assert swap_receipt(trades, D(90)) == -2400000
    assert collateral(trades, D(90)) == 4560000
    assert swap_receipt([{"delta_quantity":"1.25","entry_price":"80.10"}], D("80.30")) == D("0.25")


def test_weighted_fixings_normalize_weights_and_round_settlement_rate():
    fixings = tuple(PriceFixing(date=f"2026-11-{day}", benchmark_price=p, grade_basis="0", weight=w)
                    for day, p, w in [("05","80","0.2"),("15","82","0.3"),("25","84","0.5")])
    assert weighted_price(fixings, "benchmark_price") == D("82.600000")
    repeated = tuple(PriceFixing(date=f"2026-11-{day}", benchmark_price=p, grade_basis="0", weight="1")
                     for day,p in [("05","80"),("15","80"),("25","81")])
    assert weighted_price(repeated, "benchmark_price") == D("80.333333")


def test_current_volume_eligibility_and_negative_inventory_hedge():
    s, _ = submit_pack(state(), decision())
    assert not visible_pack(s)["current_compliance"]["permitted"]
    blocked, a = submit_pack(s, decision(checkpoint=1, target="480000"))
    assert blocked["checkpoint"] == 1
    assert "maximum_hedge_ratio_exceeded" in a["compliance"]["reasons"]
    assert blocked["trades"] == s["trades"]
    corrected, _ = submit_pack(blocked, decision(checkpoint=1, target="400000"))
    assert corrected["checkpoint"] == 2 and len(corrected["proposals"]) == 3
    _, wrong = submit_pack(state(INVENTORY), decision(INVENTORY, target="100000"))
    assert "physical_backing_required" in wrong["compliance"]["reasons"]
    _, right = submit_pack(state(INVENTORY), decision(INVENTORY, target="-240000"))
    assert right["compliance"]["permitted"]
    assert right["risk"]["net_index_delta_quantity"] == "60000"


def test_policy_currency_instrument_approval_liquidity_and_profiles():
    with pytest.raises(ValueError, match="policy_currency_mismatch"):
        state(policy=ScenarioPolicy(currency="EUR"))
    _, instrument = submit_pack(state(policy=ScenarioPolicy(permitted_instruments=("ttf_swap",))), decision())
    assert instrument["compliance"]["reasons"] == ["instrument_not_permitted"]
    s = state(policy=ScenarioPolicy(approval_ratio="0.5"))
    _, approval = submit_pack(s, decision())
    assert "approval_required" in approval["compliance"]["reasons"]
    _, approved = submit_pack(s, decision(approval_obtained=True))
    assert approved["compliance"]["permitted"]
    _, margin = submit_pack(state(policy=ScenarioPolicy(liquidity_limit="3000000")), decision())
    assert "liquidity_limit_exceeded" in margin["compliance"]["reasons"]
    academy = ScenarioPolicy(profile="academy", physical_backing_required=False, maximum_hedge_ratio="2", approval_ratio="2")
    _, result = submit_pack(state(policy=academy), decision(target="-100000"))
    assert result["compliance"]["permitted"]


@pytest.mark.parametrize("field,value", [("commodity","european_gas"),("unit","MWh"),("currency","EUR"),("instrument","ttf_swap"),("pricing_period","2026-12"),("delivery_period","2026-12"),("pricing_window_start","2026-11-06"),("pricing_window_end","2026-11-24")])
def test_decision_conventions_must_match_registered_contract(field,value):
    with pytest.raises(ValueError,match="decision_conventions_mismatch"):
        submit_pack(state(), decision(**{field:value}))


@pytest.mark.parametrize("bad", [True,"NaN","Infinity","1000001","0.000000000000001"])
def test_malformed_quantities_cannot_enter_the_ledger(bad):
    with pytest.raises(ValidationError): decision(target=bad)


@pytest.mark.parametrize("corruption", ["chronology","fixing_date","benchmark","basis","volume","historical_date","role","unit","window"])
def test_candidate_packs_fail_schema_or_financial_consistency(corruption):
    pack = (INVENTORY if corruption=="historical_date" else REFINERY).model_dump(mode="json")
    if corruption=="chronology": pack["observations"][1]["date"]="2026-10-01"
    if corruption=="fixing_date": pack["fixings"][0]["date"]="2026-10-01"
    if corruption=="benchmark": pack["observations"][2]["benchmark_price"]="91"
    if corruption=="basis": pack["observations"][2]["grade_basis"]="2"
    if corruption=="volume": pack["observations"][2]["eligible_quantity"]="400000"
    if corruption=="historical_date": pack["physical"]["historical_purchase_date"]="2026-10-15"
    if corruption=="role": pack["conventions"]["role"]="utility_company"
    if corruption=="unit": pack["conventions"]["unit"]="MWh"
    if corruption=="window": pack["conventions"]["pricing_window_end"]="2026-12-01"
    with pytest.raises(ValidationError): ScenarioPack(**pack)


def test_future_fixings_and_outcomes_hidden_until_settlement():
    s = state()
    v = visible_pack(s)
    assert v["visible_fixings"] == [] and "financial" not in v
    assert "2026-11-15" not in json.dumps(coach_messages(v,"en"))
    with pytest.raises(ValueError,match="settlement_not_available"): settle_pack(s)
    s,_ = submit_pack(s,decision())
    v = visible_pack(s)
    assert "2026-11-15" not in json.dumps(v) and v["visible_fixings"] == []
    # Contract window/settlement dates are known; fixing values and future facts are not.
    assert len(v["visible_timeline"]) == 2
    assert not any(o["date"]=="2026-11-30" for o in v["visible_timeline"])
    final = visible_pack(finish())
    assert len(final["visible_fixings"]) == 3
    assert final["open_position_quantity"] == "0" and final["post_settlement_collateral"] == 0


def test_shared_store_preserves_gas_and_crude_restart_and_atomicity(tmp_path):
    from core.risk_training import Policy
    from tests.test_risk_training import decision as gas_decision
    store=SessionStore(tmp_path/"sessions.sqlite")
    gas=store.create(Policy()); crude=store.create_scenario(ScenarioSessionRequest(scenario_id=REFINERY.version))
    assert store.decide(gas["id"],gas_decision())["checkpoint"]==1
    def act():
        try:return store.decide(crude["id"],decision())["checkpoint"]
        except ValueError:return "stale"
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _:act(),range(2)),key=str)==[1,"stale"]
    resumed=SessionStore(tmp_path/"sessions.sqlite").view(crude["id"])
    assert resumed["checkpoint"]==1 and resumed["decisions"][0]["information_snapshot"]["eligible_quantity"]=="600000"
    with pytest.raises(ValueError,match="decision_contract_mismatch"):store.decide(crude["id"],gas_decision(cp=1))
    with pytest.raises(ValueError,match="decision_contract_mismatch"):store.decide(gas["id"],decision(checkpoint=1))


def test_api_registered_catalog_cannot_publish_ai_packs_and_coaching_is_bounded(tmp_path,monkeypatch):
    from core.haineng_client import HainengClient
    monkeypatch.setenv("COMMODITY_LAB_TRAINING_DB",str(tmp_path/"api.sqlite"))
    monkeypatch.setattr(HainengClient,"is_configured",lambda self:False)
    c=TestClient(app)
    assert len(c.get('/api/v1/risk-training/catalog').json()["scenarios"])==3
    malicious={"scenario_id":REFINERY.version,"pack":REFINERY.model_dump(mode="json")}
    assert c.post('/api/v1/risk-training/scenario-sessions',json=malicious).status_code==422
    assert c.post('/api/v1/risk-training/scenario-sessions',json={"scenario_id":"carbon-v1"}).status_code==422
    v=c.post('/api/v1/risk-training/scenario-sessions',json={"scenario_id":INVENTORY.version}).json()
    url=f'/api/v1/risk-training/sessions/{v["id"]}'
    assert "short benchmark hedge" in c.post(url+'/coach',json={"locale":"en"}).json()["answer"]
    assert "历史采购" in c.post(url+'/coach',json={"locale":"zh"}).json()["answer"]
    assert c.post(url+'/decisions',json=decision(INVENTORY,target="-240000").model_dump(mode="json")).json()["checkpoint"]==1
    assert c.post(url+'/decisions',json=decision(INVENTORY,target="-240000").model_dump(mode="json")).status_code==409
    final=c.post(url+'/decisions',json=decision(INVENTORY,1,"-240000").model_dump(mode="json")).json()
    assert final["financial"]["commercial_margin_before_costs"]==390000
    assert c.get(url).json()["financial"]["settlement_net_cash_flow"]==23490000
    captured=[]
    monkeypatch.setattr(HainengClient,"is_configured",lambda self:True)
    monkeypatch.setattr(HainengClient,"complete",lambda self,messages:captured.append(messages) or "Explain grade and freight risk.")
    before=c.get(url).json()
    assert c.post(url+'/coach',json={"locale":"en"}).json()["graded"] is False
    assert c.get(url).json()==before
