"""Versioned, synthetic procurement training. No live execution or AI arithmetic."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

D = Decimal
VERSION = "gas-procurement-v1"
RUBRIC_VERSION = "diagnostic-v1"


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Policy(Contract):
    profile: Literal["corporate", "academy", "advanced"] = "corporate"
    version: Literal["illustrative-v1"] = "illustrative-v1"
    maximum_hedge_ratio: Decimal = Field(default=D("0.8"), ge=0, le=2, allow_inf_nan=False, max_digits=6, decimal_places=4)
    approval_ratio: Decimal = Field(default=D("0.8"), ge=0, le=2, allow_inf_nan=False, max_digits=6, decimal_places=4)
    liquidity_limit_eur: Decimal = Field(default=D("100000"), gt=0, le=10000000, allow_inf_nan=False, max_digits=10, decimal_places=2)
    physical_backing_required: bool = True
    permitted_instruments: tuple[Literal["ttf_swap"], ...] = ("ttf_swap",)


    @field_validator("maximum_hedge_ratio", "approval_ratio", "liquidity_limit_eur", mode="before")
    @classmethod
    def reject_bool(cls, value):
        if isinstance(value, bool):
            raise ValueError("policy number cannot be boolean")
        return value


class Decision(Contract):
    checkpoint: int = Field(ge=0, le=1, strict=True)
    target_mwh: Decimal = Field(ge=-20000, le=20000, allow_inf_nan=False, max_digits=12, decimal_places=6)
    instrument: Literal["ttf_swap"] = "ttf_swap"
    commodity: Literal["european_gas"] = "european_gas"
    unit: Literal["MWh"] = "MWh"
    currency: Literal["EUR"] = "EUR"
    delivery_period: Literal["2026-11"] = "2026-11"
    pricing_period: Literal["2026-11"] = "2026-11"
    approval_obtained: bool = False
    rationale: str = Field(min_length=20, max_length=4000)
    exposure_answer: Literal["rising_purchase_cost", "falling_sales_revenue"]
    basis_answer: Literal["basis_remains", "all_risk_removed"]
    liquidity_answer: Literal["collateral_needed", "profit_guarantees_cash"]

    @field_validator("target_mwh", mode="before")
    @classmethod
    def reject_bool(cls, value):
        if isinstance(value, bool):
            raise ValueError("quantity cannot be boolean")
        return value

    @field_validator("rationale")
    @classmethod
    def meaningful_text(cls, value):
        if len(value.strip()) < 20:
            raise ValueError("rationale must contain at least 20 non-padding characters")
        return value.strip()


class LocalizedFact(Contract):
    en: str = Field(min_length=20)
    zh: str = Field(min_length=20)


class Observation(Contract):
    date: date
    index_eur_mwh: Decimal = Field(ge=0, allow_inf_nan=False)
    basis_eur_mwh: Decimal = Field(allow_inf_nan=False)
    physical_mwh: Decimal = Field(ge=0, allow_inf_nan=False)
    fact: LocalizedFact


# Reviewed synthetic facts; these are deliberately private to the server.
CHECKPOINTS = (
    {"date": "2026-10-01", "index_eur_mwh": "40", "basis_eur_mwh": "2", "physical_mwh": "10000",
     "fact": {"en": "A utility must buy 10,000 MWh for November at the TTF monthly index plus regional basis. The sales tariff is fixed; rising purchase cost reduces commercial margin.",
              "zh": "公用事业公司须在11月按TTF月度指数加区域基差采购10,000 MWh。销售价格固定，采购成本上涨会侵蚀商业利润。"}},
    {"date": "2026-10-15", "index_eur_mwh": "50", "basis_eur_mwh": "3", "physical_mwh": "8000",
     "fact": {"en": "A pipeline disruption lifts TTF and regional basis. Customer nominations fall to 8,000 MWh. Recheck existing hedge eligibility before resizing.",
              "zh": "管道中断推高TTF及区域基差。客户提名量降至8,000 MWh，调整头寸前须重新核查现有套保资格。"}},
    {"date": "2026-11-30", "index_eur_mwh": "55", "basis_eur_mwh": "5", "physical_mwh": "8000",
     "fact": {"en": "The November training index settles at €55/MWh and regional basis at €5/MWh. Physical purchase and swap cash flows settle separately.",
              "zh": "11月训练指数以55欧元/MWh结算，区域基差为5欧元/MWh。实货采购与掉期现金流分别结算。"}},
)

# Validate the reviewed pack at load time; AI cannot replace this fixture.
CHECKPOINTS = tuple(Observation(**item).model_dump(mode="json") for item in CHECKPOINTS)
if [cp["date"] for cp in CHECKPOINTS] != sorted({cp["date"] for cp in CHECKPOINTS}):
    raise ValueError("scenario chronology must be strictly increasing")
if not CHECKPOINTS[-1]["date"].startswith("2026-11"):
    raise ValueError("settlement must match the pricing period")

COMPETENCIES = (
    {"id": "fundamentals", "prerequisites": []},
    {"id": "physical", "prerequisites": ["fundamentals"]},
    {"id": "derivatives", "prerequisites": ["physical"]},
    {"id": "pricing_hedging", "prerequisites": ["derivatives"]},
    {"id": "basis", "prerequisites": ["pricing_hedging"]},
    {"id": "portfolio_liquidity", "prerequisites": ["basis"]},
    {"id": "operations", "prerequisites": ["physical"]},
    {"id": "advanced", "prerequisites": ["portfolio_liquidity", "operations"]},
)


def number(value: Decimal) -> float:
    return float(value.quantize(D("0.01"), rounding=ROUND_HALF_UP))


def swap_cash_flow(trades: list[dict], index: Decimal) -> Decimal:
    """Positive = receipt. Incremental signed trades conserve resize economics."""
    return sum((D(t["delta_mwh"]) * (index - D(t["entry_eur_mwh"])) for t in trades), D(0))


def collateral(trades: list[dict], index: Decimal, target: Decimal) -> Decimal:
    # Simplified portfolio initial margin + adverse net MTM, not exchange margin.
    return abs(target) * index * D("0.10") + max(D(0), -swap_cash_flow(trades, index))


def policy_check(policy: Policy, target: Decimal, physical: Decimal, liquidity: Decimal,
                 approval: bool = False) -> dict:
    reasons = []
    if target != 0 and "ttf_swap" not in policy.permitted_instruments:
        reasons.append("instrument_not_permitted")
    if policy.physical_backing_required and (target < 0 or abs(target) > physical):
        reasons.append("physical_backing_required")
    if abs(target) > physical * policy.maximum_hedge_ratio:
        reasons.append("maximum_hedge_ratio_exceeded")
    if abs(target) > physical * policy.approval_ratio and not approval:
        reasons.append("approval_required")
    if liquidity > policy.liquidity_limit_eur:
        reasons.append("liquidity_limit_exceeded")
    return {"permitted": not reasons, "reasons": reasons,
            "hedge_ratio": float(abs(target) / physical) if physical else None}


def diagnostic(decision: Decision) -> dict:
    evidence = {"exposure": decision.exposure_answer == "rising_purchase_cost",
                "basis": decision.basis_answer == "basis_remains",
                "liquidity": decision.liquidity_answer == "collateral_needed"}
    return {"rubric_version": RUBRIC_VERSION, "evidence": evidence,
            "diagnostic_score": round(sum(evidence.values()) / 3 * 100),
            "reasoning_status": "requires_instructor_review",
            "remediation": [key for key, correct in evidence.items() if not correct]}


def initial_state(policy: Policy) -> dict:
    return {"scenario_version": VERSION, "policy": policy.model_dump(mode="json"),
            "checkpoint": 0, "trades": [], "decisions": [], "proposals": [], "peak_collateral_eur": "0"}


def validate_version(state: dict) -> None:
    if state.get("scenario_version") != VERSION:
        raise ValueError("unsupported_scenario_version")


def visible_state(state: dict) -> dict:
    validate_version(state)
    cp = state["checkpoint"]
    current = CHECKPOINTS[cp]
    target = sum((D(t["delta_mwh"]) for t in state["trades"]), D(0))
    margin = collateral(state["trades"], D(current["index_eur_mwh"]), target)
    payload = {"scenario_version": state["scenario_version"], "policy": state["policy"],
               "checkpoint": cp, "complete": cp == 2, "current": current,
               "visible_timeline": list(CHECKPOINTS[:cp + 1]),
               "conventions": {"commodity": "european_gas", "benchmark": "TTF", "unit": "MWh", "currency": "EUR",
                               "pricing_period": "2026-11", "delivery_period": "2026-11",
                               "instrument": "cash_settled_training_swap", "settlement": "monthly_index_at_final_checkpoint"},
               "provenance": {"mode": "synthetic", "version": VERSION, "licensed_data": False},
               "position_mwh": str(target), "collateral_estimate_eur": number(margin),
               "current_compliance": policy_check(Policy(**state["policy"]), target, D(current["physical_mwh"]), margin,
                                                  state["decisions"][-1]["decision"]["approval_obtained"] if state["decisions"] else False),
               "decisions": state["decisions"], "proposals": state["proposals"],
               "competencies": COMPETENCIES, "mastery_status": "provisional_single_case"}
    if cp == 2:
        payload["financial"] = settlement(state)
    return payload


def submit(state: dict, decision: Decision) -> tuple[dict, dict]:
    from copy import deepcopy
    validate_version(state)
    if decision.checkpoint != state["checkpoint"] or state["checkpoint"] == 2:
        raise ValueError("stale_checkpoint")
    updated = deepcopy(state)
    current = CHECKPOINTS[state["checkpoint"]]
    price, physical = D(current["index_eur_mwh"]), D(current["physical_mwh"])
    old_target = sum((D(t["delta_mwh"]) for t in state["trades"]), D(0))
    trades = state["trades"] + [{"delta_mwh": str(decision.target_mwh - old_target), "entry_eur_mwh": str(price)}]
    margin = collateral(trades, price, decision.target_mwh)
    compliance = policy_check(Policy(**state["policy"]), decision.target_mwh, physical, margin, decision.approval_obtained)
    assessment = {"compliance": compliance, "decision_quality": diagnostic(decision),
                  "risk": {"unhedged_index_mwh": str(physical - decision.target_mwh),
                           "basis_exposed_mwh": str(physical), "collateral_estimate_eur": number(margin)}}
    record = {"decision": decision.model_dump(mode="json"), "information_snapshot": deepcopy(current),
              "policy_snapshot": deepcopy(state["policy"]), "assessment": assessment}
    updated["proposals"].append(record)
    if compliance["permitted"]:
        updated["trades"] = trades
        updated["decisions"].append(record)
        updated["checkpoint"] += 1
        next_price = D(CHECKPOINTS[updated["checkpoint"]]["index_eur_mwh"])
        updated["peak_collateral_eur"] = str(max(D(state["peak_collateral_eur"]), margin,
                                               collateral(trades, next_price, decision.target_mwh)))
    return updated, assessment


def settlement(state: dict) -> dict:
    validate_version(state)
    if state["checkpoint"] != 2:
        raise ValueError("settlement_not_available")
    final = CHECKPOINTS[2]
    volume, index, basis = (D(final[k]) for k in ("physical_mwh", "index_eur_mwh", "basis_eur_mwh"))
    physical_cost = volume * (index + basis)
    swap = swap_cash_flow(state["trades"], index)
    budget = volume * (D(CHECKPOINTS[0]["index_eur_mwh"]) + D(CHECKPOINTS[0]["basis_eur_mwh"]))
    shock = physical_cost - budget
    return {"physical_cash_flow_eur": number(-physical_cost), "derivative_cash_flow_eur": number(swap),
            "net_procurement_cost_eur": number(physical_cost - swap), "unhedged_cost_eur": number(physical_cost),
            "volume_adjusted_budget_eur": number(budget), "budget_variance_eur": number(budget - physical_cost + swap),
            "basis_cost_eur": number(volume * basis), "peak_collateral_estimate_eur": number(D(state["peak_collateral_eur"])),
            "cost_shock_offset_pct": number(swap / shock * 100) if shock else None,
            "effectiveness_method": "ex_post_cost_shock_offset_not_statistical_effectiveness",
            "realized_commercial_pnl": None}
