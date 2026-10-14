"""Reviewed commodity-neutral contracts and financial consistency validation."""
from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from pydantic import Field, field_validator, model_validator
from core.risk_training import Contract, LocalizedFact

D = Decimal
Commodity = Literal["european_gas", "crude_oil"]
Instrument = Literal["ttf_swap", "brent_swap"]


class Text(Contract):
    en: str = Field(min_length=3)
    zh: str = Field(min_length=3)


class Conventions(Contract):
    role: Literal["trading_company"] = "trading_company"
    settlement_price_decimals: Literal[6] = 6
    commodity: Commodity
    benchmark: Literal["TTF", "Brent"]
    unit: Literal["MWh", "bbl"]
    currency: Literal["EUR", "USD"]
    instrument: Instrument
    delivery_period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    pricing_period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    pricing_window_start: date
    pricing_window_end: date
    settlement_date: date

    @model_validator(mode="after")
    def coherent_domain(self):
        expected = {"crude_oil": ("Brent", "bbl", "USD", "brent_swap"),
                    "european_gas": ("TTF", "MWh", "EUR", "ttf_swap")}[self.commodity]
        if (self.benchmark, self.unit, self.currency, self.instrument) != expected:
            raise ValueError("commodity_conventions_mismatch")
        if not self.pricing_window_start <= self.pricing_window_end <= self.settlement_date:
            raise ValueError("invalid_pricing_window")
        if any(d.strftime("%Y-%m") != self.pricing_period for d in (self.pricing_window_start, self.pricing_window_end)):
            raise ValueError("pricing_window_period_mismatch")
        if self.settlement_date.strftime("%Y-%m") != self.delivery_period:
            raise ValueError("settlement_delivery_period_mismatch")
        return self


class PhysicalTerms(Contract):
    kind: Literal["fixed_sale_indexed_purchase", "owned_inventory_indexed_sale"]
    fixed_price: Decimal = Field(ge=0, le=100000, allow_inf_nan=False, decimal_places=6)
    historical_purchase_date: date | None = None

    @model_validator(mode="after")
    def acquisition_timing(self):
        if (self.kind == "owned_inventory_indexed_sale") != (self.historical_purchase_date is not None):
            raise ValueError("historical_purchase_date_required_only_for_inventory")
        return self

    @property
    def hedge_sign(self) -> int:
        return 1 if self.kind == "fixed_sale_indexed_purchase" else -1


class MarketObservation(Contract):
    date: date
    benchmark_price: Decimal = Field(ge=0, le=100000, allow_inf_nan=False, decimal_places=6)
    grade_basis: Decimal = Field(ge=-100000, le=100000, allow_inf_nan=False, decimal_places=6)
    freight_per_unit: Decimal = Field(ge=0, le=100000, allow_inf_nan=False, decimal_places=6)
    eligible_quantity: Decimal = Field(gt=0, le=1000000, allow_inf_nan=False, decimal_places=6)
    fact: LocalizedFact


class PriceFixing(Contract):
    date: date
    benchmark_price: Decimal = Field(ge=0, le=100000, allow_inf_nan=False, decimal_places=6)
    grade_basis: Decimal = Field(ge=-100000, le=100000, allow_inf_nan=False, decimal_places=6)
    weight: Decimal = Field(gt=0, le=1, allow_inf_nan=False, decimal_places=6)


def weighted_price(fixings: tuple[PriceFixing, ...], field: str) -> Decimal:
    if field not in {"benchmark_price", "grade_basis"}:
        raise ValueError("unsupported_price_field")
    total_weight = sum((fixing.weight for fixing in fixings), D(0))
    if not total_weight:
        raise ValueError("fixings_required")
    return (sum((getattr(f, field) * f.weight for f in fixings), D(0)) / total_weight).quantize(D("0.000001"), rounding=ROUND_HALF_UP)


class ScenarioPack(Contract):
    schema_version: Literal["reviewed-pack-v1"] = "reviewed-pack-v1"
    version: str = Field(pattern=r"^[a-z][a-z0-9-]+-v[1-9][0-9]*$")
    review_status: Literal["synthetic_reference_validated"] = "synthetic_reference_validated"
    title: Text
    conventions: Conventions
    physical: PhysicalTerms
    observations: tuple[MarketObservation, ...] = Field(min_length=3, max_length=3)
    fixings: tuple[PriceFixing, ...] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def financial_consistency(self):
        days = [o.date for o in self.observations]
        if days != sorted(set(days)):
            raise ValueError("checkpoints_must_be_strictly_increasing")
        if days[-1] != self.conventions.settlement_date:
            raise ValueError("terminal_checkpoint_must_be_settlement")
        if days[-2] >= self.conventions.pricing_window_start:
            raise ValueError("decision_checkpoints_must_precede_pricing_window")
        fixing_days = [f.date for f in self.fixings]
        if fixing_days != sorted(set(fixing_days)):
            raise ValueError("fixings_must_be_strictly_increasing")
        if any(not self.conventions.pricing_window_start <= day <= self.conventions.pricing_window_end for day in fixing_days):
            raise ValueError("fixing_outside_pricing_window")
        if self.observations[-1].benchmark_price != weighted_price(self.fixings, "benchmark_price"):
            raise ValueError("terminal_benchmark_must_match_fixings")
        if self.observations[-1].grade_basis != weighted_price(self.fixings, "grade_basis"):
            raise ValueError("terminal_basis_must_match_fixings")
        if self.observations[-1].eligible_quantity != self.observations[-2].eligible_quantity:
            raise ValueError("terminal_volume_change_requires_a_decision_checkpoint")
        if self.physical.historical_purchase_date and self.physical.historical_purchase_date >= days[0]:
            raise ValueError("inventory_must_be_acquired_before_first_checkpoint")
        if self.physical.kind == "owned_inventory_indexed_sale" and len({o.eligible_quantity for o in self.observations}) != 1:
            raise ValueError("inventory_volume_changes_require_an_inventory_ledger")
        if any(o.benchmark_price + o.grade_basis < 0 for o in self.observations):
            raise ValueError("negative_physical_price_unsupported_in_this_model")
        return self


class ScenarioPolicy(Contract):
    profile: Literal["corporate", "academy", "advanced"] = "corporate"
    version: Literal["illustrative-v1"] = "illustrative-v1"
    maximum_hedge_ratio: Decimal = Field(default=D("0.8"), ge=0, le=2, allow_inf_nan=False, max_digits=6, decimal_places=4)
    approval_ratio: Decimal = Field(default=D("0.8"), ge=0, le=2, allow_inf_nan=False, max_digits=6, decimal_places=4)
    currency: Literal["EUR", "USD"] = "USD"
    liquidity_limit: Decimal = Field(default=D("10000000"), gt=0, le=100000000, allow_inf_nan=False, max_digits=11, decimal_places=2)
    physical_backing_required: bool = True
    permitted_instruments: tuple[Instrument, ...] = ("brent_swap",)

    @field_validator("maximum_hedge_ratio", "approval_ratio", "liquidity_limit", mode="before")
    @classmethod
    def reject_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError("policy_number_cannot_be_boolean")
        return value


class CommodityDecision(Contract):
    checkpoint: int = Field(ge=0, le=1, strict=True)
    target_quantity: Decimal = Field(ge=-1000000, le=1000000, allow_inf_nan=False, max_digits=13, decimal_places=6)
    commodity: Commodity
    instrument: Instrument
    unit: Literal["MWh", "bbl"]
    currency: Literal["EUR", "USD"]
    delivery_period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    pricing_period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    pricing_window_start: date
    pricing_window_end: date
    approval_obtained: bool = False
    rationale: str = Field(min_length=20, max_length=4000)
    exposure_answer: Literal["rising_purchase_cost", "falling_sales_revenue"]
    basis_answer: Literal["basis_remains", "all_risk_removed"]
    liquidity_answer: Literal["collateral_needed", "profit_guarantees_cash"]

    @field_validator("target_quantity", mode="before")
    @classmethod
    def reject_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError("quantity_cannot_be_boolean")
        return value

    @field_validator("rationale")
    @classmethod
    def meaningful_text(cls, value):
        if len(value.strip()) < 20:
            raise ValueError("rationale_requires_20_non_padding_characters")
        return value.strip()


class ScenarioSessionRequest(Contract):
    scenario_id: Literal["crude-refinery-procurement-v1", "crude-merchant-inventory-v1"]
    policy: ScenarioPolicy = Field(default_factory=ScenarioPolicy)
