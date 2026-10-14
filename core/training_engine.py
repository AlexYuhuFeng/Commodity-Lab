"""Shared session dispatch with pure financial/policy functions for reviewed packs."""
from copy import deepcopy
from decimal import Decimal
from core import risk_training as gas
from core.crude_training import PACKS
from core.training_contracts import CommodityDecision, ScenarioPack, ScenarioPolicy, ScenarioSessionRequest, weighted_price

D = Decimal
RUBRIC_VERSION = "commercial-diagnostic-v2"


def pack_for(version: str) -> ScenarioPack:
    try:
        return PACKS[version]
    except KeyError as exc:
        raise ValueError("unsupported_scenario_version") from exc


def catalog() -> dict:
    return {"scenarios": [{"id": gas.VERSION, "commodity": "european_gas", "currency": "EUR", "unit": "MWh",
                            "title": {"en": "European gas physical book", "zh": "欧洲天然气实货业务"}}] +
                         [{"id": p.version, "commodity": p.conventions.commodity, "currency": p.conventions.currency,
                           "unit": p.conventions.unit, "title": p.title.model_dump()} for p in PACKS.values()]}


def create_state(request: ScenarioSessionRequest) -> dict:
    pack = pack_for(request.scenario_id)
    if request.policy.currency != pack.conventions.currency:
        raise ValueError("policy_currency_mismatch")
    return {"scenario_version": pack.version, "policy": request.policy.model_dump(mode="json"),
            "checkpoint": 0, "trades": [], "decisions": [], "proposals": [], "peak_collateral": "0"}


def swap_receipt(trades: list[dict], benchmark: Decimal) -> Decimal:
    return sum((D(t["delta_quantity"]) * (benchmark - D(t["entry_price"])) for t in trades), D(0))


def position(trades: list[dict]) -> Decimal:
    return sum((D(t["delta_quantity"]) for t in trades), D(0))


def collateral(trades: list[dict], benchmark: Decimal) -> Decimal:
    return abs(position(trades)) * benchmark * D("0.10") + max(D(0), -swap_receipt(trades, benchmark))


def policy_check(pack: ScenarioPack, policy: ScenarioPolicy, target: Decimal, eligible: Decimal,
                 estimated_collateral: Decimal, approval: bool) -> dict:
    reasons = []
    if policy.currency != pack.conventions.currency:
        reasons.append("policy_currency_mismatch")
    if target and pack.conventions.instrument not in policy.permitted_instruments:
        reasons.append("instrument_not_permitted")
    if policy.physical_backing_required and (target * pack.physical.hedge_sign < 0 or abs(target) > eligible):
        reasons.append("physical_backing_required")
    if abs(target) > eligible * policy.maximum_hedge_ratio:
        reasons.append("maximum_hedge_ratio_exceeded")
    if abs(target) > eligible * policy.approval_ratio and not approval:
        reasons.append("approval_required")
    if estimated_collateral > policy.liquidity_limit:
        reasons.append("liquidity_limit_exceeded")
    return {"permitted": not reasons, "reasons": reasons, "hedge_ratio": float(abs(target) / eligible) if eligible else None}


def diagnose(pack: ScenarioPack, decision: CommodityDecision) -> dict:
    expected = "rising_purchase_cost" if pack.physical.hedge_sign == 1 else "falling_sales_revenue"
    evidence = {"exposure": decision.exposure_answer == expected,
                "basis": decision.basis_answer == "basis_remains",
                "liquidity": decision.liquidity_answer == "collateral_needed"}
    return {"rubric_version": RUBRIC_VERSION, "evidence": evidence,
            "diagnostic_score": round(sum(evidence.values()) / 3 * 100),
            "reasoning_status": "requires_instructor_review", "remediation": [k for k, v in evidence.items() if not v]}


def submit_pack(state: dict, decision: CommodityDecision) -> tuple[dict, dict]:
    pack = pack_for(state["scenario_version"])
    if not isinstance(decision, CommodityDecision):
        raise ValueError("decision_contract_mismatch")
    for field in ("commodity", "instrument", "unit", "currency", "delivery_period", "pricing_period", "pricing_window_start", "pricing_window_end"):
        if getattr(decision, field) != getattr(pack.conventions, field):
            raise ValueError("decision_conventions_mismatch")
    if state["checkpoint"] == 2 or decision.checkpoint != state["checkpoint"]:
        raise ValueError("stale_checkpoint")
    updated = deepcopy(state)
    current = pack.observations[state["checkpoint"]]
    trades = state["trades"] + [{"delta_quantity": str(decision.target_quantity - position(state["trades"])),
                                 "entry_price": str(current.benchmark_price), "date": current.date.isoformat()}]
    margin = collateral(trades, current.benchmark_price)
    compliance = policy_check(pack, ScenarioPolicy(**state["policy"]), decision.target_quantity,
                              current.eligible_quantity, margin, decision.approval_obtained)
    assessment = {"compliance": compliance, "decision_quality": diagnose(pack, decision),
                  "risk": {"net_index_delta_quantity": str(-pack.physical.hedge_sign * current.eligible_quantity + decision.target_quantity),
                           "grade_basis_exposed_quantity": str(current.eligible_quantity),
                           "freight_exposed_quantity": str(current.eligible_quantity),
                           "collateral_estimate": gas.number(margin), "currency": pack.conventions.currency}}
    record = {"decision": decision.model_dump(mode="json"), "information_snapshot": current.model_dump(mode="json"),
              "policy_snapshot": deepcopy(state["policy"]), "assessment": assessment}
    updated["proposals"].append(record)
    if compliance["permitted"]:
        updated["trades"] = trades
        updated["decisions"].append(record)
        updated["checkpoint"] += 1
        next_quote = pack.observations[updated["checkpoint"]].benchmark_price
        updated["peak_collateral"] = str(max(D(state["peak_collateral"]), margin, collateral(trades, next_quote)))
    return updated, assessment


def physical_flows(pack: ScenarioPack, quantity: Decimal, benchmark: Decimal, basis: Decimal, freight: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    if pack.physical.kind == "fixed_sale_indexed_purchase":
        return quantity * pack.physical.fixed_price, -quantity * (benchmark + basis), -quantity * freight
    return quantity * (benchmark + basis), -quantity * pack.physical.fixed_price, -quantity * freight


def settle_pack(state: dict) -> dict:
    pack = pack_for(state["scenario_version"])
    if state["checkpoint"] != 2:
        raise ValueError("settlement_not_available")
    final, first = pack.observations[-1], pack.observations[0]
    benchmark, basis = weighted_price(pack.fixings, "benchmark_price"), weighted_price(pack.fixings, "grade_basis")
    sales, purchases, freight = physical_flows(pack, final.eligible_quantity, benchmark, basis, final.freight_per_unit)
    baseline = sum(physical_flows(pack, final.eligible_quantity, first.benchmark_price, first.grade_basis, first.freight_per_unit))
    swap = swap_receipt(state["trades"], benchmark)
    physical_margin = sales + purchases + freight
    day = pack.conventions.settlement_date.isoformat()
    entries = [{"kind": "physical_sales", "date": day, "amount": gas.number(sales)},
               {"kind": "physical_purchase", "date": pack.physical.historical_purchase_date.isoformat() if pack.physical.historical_purchase_date else day, "amount": gas.number(purchases)},
               {"kind": "freight", "date": day, "amount": gas.number(freight)},
               {"kind": "derivative", "date": day, "amount": gas.number(swap)}]
    shock = baseline - physical_margin
    result = {"currency": pack.conventions.currency, "physical_sales_cash_flow": gas.number(sales),
              "physical_purchase_cash_flow": gas.number(purchases), "freight_cash_flow": gas.number(freight),
              "derivative_cash_flow": gas.number(swap), "unhedged_physical_margin": gas.number(physical_margin),
              "commercial_margin_before_costs": gas.number(physical_margin + swap),
              "volume_adjusted_baseline_physical_margin": gas.number(baseline),
              "margin_variance": gas.number(physical_margin + swap - baseline),
              "settlement_net_cash_flow": gas.number(sales + freight + swap + (purchases if not pack.physical.historical_purchase_date else D(0))),
              "grade_basis_cash_component": gas.number(-pack.physical.hedge_sign * final.eligible_quantity * basis),
              "peak_collateral_estimate": gas.number(D(state["peak_collateral"])),
              "adverse_margin_shock_offset_pct": gas.number(swap / shock * 100) if shock > 0 else None,
              "effectiveness_method": "ex_post_adverse_margin_shock_offset_not_statistical_effectiveness",
              "cash_flows": entries}
    if pack.physical.kind == "fixed_sale_indexed_purchase":
        result["net_procurement_cost"] = gas.number(-purchases - freight - swap)
    return result


def visible_pack(state: dict) -> dict:
    pack = pack_for(state["scenario_version"])
    cp = state["checkpoint"]
    current = pack.observations[cp]
    target = position(state["trades"])
    margin = collateral(state["trades"], current.benchmark_price)
    approval = state["decisions"][-1]["decision"]["approval_obtained"] if state["decisions"] else False
    payload = {"scenario_version": pack.version, "scenario_id": pack.version, "title": pack.title.model_dump(),
               "schema_version": pack.schema_version, "policy": deepcopy(state["policy"]), "checkpoint": cp, "complete": cp == 2,
               "current": current.model_dump(mode="json"), "visible_timeline": [o.model_dump(mode="json") for o in pack.observations[:cp + 1]],
               "conventions": pack.conventions.model_dump(mode="json"), "physical_contract": pack.physical.model_dump(mode="json"),
               "provenance": {"mode": "synthetic", "version": pack.version, "licensed_data": False},
               "pricing_method": "three_weighted_synthetic_fixings_not_exchange_settlement",
               "visible_fixings": [f.model_dump(mode="json") for f in pack.fixings if f.date <= current.date],
               "position_quantity": str(target), "hedge_sign": pack.physical.hedge_sign,
               "open_position_quantity": "0" if cp == 2 else str(target),
               "collateral_estimate": gas.number(margin), "post_settlement_collateral": 0 if cp == 2 else None,
               "current_compliance": policy_check(pack, ScenarioPolicy(**state["policy"]), target, current.eligible_quantity, margin, approval),
               "decisions": deepcopy(state["decisions"]), "proposals": deepcopy(state["proposals"]),
               "competencies": gas.COMPETENCIES, "mastery_status": "provisional_single_case"}
    if state["proposals"]:
        payload["latest_assessment"] = deepcopy(state["proposals"][-1]["assessment"])
    if cp == 2:
        payload["financial"] = settle_pack(state)
    return payload


def view_state(state: dict) -> dict:
    return gas.visible_state(state) if state["scenario_version"] == gas.VERSION else visible_pack(state)


def submit_state(state: dict, decision) -> tuple[dict, dict]:
    if state["scenario_version"] == gas.VERSION:
        if not isinstance(decision, gas.Decision):
            raise ValueError("decision_contract_mismatch")
        return gas.submit(state, decision)
    return submit_pack(state, decision)
