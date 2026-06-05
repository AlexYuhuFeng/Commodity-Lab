"""Generic scenario registry for Commodity Lab.

The registry is intentionally commodity-agnostic. V1 enables Europe natural gas
scenarios first, while crude oil, refined products, carbon, and power can add
scenarios through the same contract later.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from core.energy_models import LocalizedText, TrainingScenario


@dataclass
class ScenarioRegistry:
    scenarios: dict[str, TrainingScenario] = field(default_factory=dict)

    def register(self, scenario: TrainingScenario) -> None:
        if scenario.scenario_id in self.scenarios:
            raise ValueError(f"Duplicate scenario id: {scenario.scenario_id}")
        self.scenarios[scenario.scenario_id] = scenario

    def register_many(self, scenarios: Iterable[TrainingScenario]) -> None:
        for scenario in scenarios:
            self.register(scenario)

    def get(self, scenario_id: str) -> TrainingScenario:
        try:
            return self.scenarios[scenario_id]
        except KeyError as exc:
            raise KeyError(f"Unknown scenario '{scenario_id}'.") from exc

    def list(
        self,
        *,
        commodity: str | None = None,
        region: str | None = None,
        status: str | None = None,
        locale: str = "en",
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for scenario in self.scenarios.values():
            if commodity and scenario.commodity != commodity:
                continue
            if region and scenario.region != region:
                continue
            if status and scenario.status != status:
                continue
            rows.append(scenario.localized(locale=locale))
        return rows

    def enabled(self, *, commodity: str | None = None, region: str | None = None, locale: str = "en") -> list[dict[str, Any]]:
        return self.list(commodity=commodity, region=region, status="enabled", locale=locale)

    def ids(self) -> list[str]:
        return list(self.scenarios)


EUROPE_GAS_SCENARIOS: tuple[TrainingScenario, ...] = (
    TrainingScenario(
        scenario_id="europe_ttf_nbp_spread",
        commodity="natural_gas",
        status="enabled",
        region="europe",
        title=LocalizedText("Europe TTF/NBP Spread", "欧洲 TTF/NBP 价差"),
        summary=LocalizedText(
            "A trader manages hub-spread risk before locking a delivered European gas margin.",
            "交易员在锁定欧洲天然气到岸利润前，管理不同枢纽之间的价差风险。",
        ),
        difficulty="intermediate",
        primary_asset_id="ttf_nbp_spread_proxy",
        exposure={
            "direction": "long",
            "volume_mmbtu": 70000,
            "risk": {
                "en": "Cross-market gas exposure to TTF/NBP spread, units, FX, and hub basis.",
                "zh": "跨市场天然气头寸面临 TTF/NBP 价差、单位、汇率和枢纽基差风险。",
            },
        },
        recommended_tool="basis_hedge",
        recommended_side="sell",
        learning_objectives={
            "en": [
                "Separate outright gas price risk from hub-spread risk.",
                "Recognize why NBP and TTF require unit and FX normalization.",
                "Use a basis hedge when exposure is location or hub-spread driven.",
            ],
            "zh": [
                "区分单边气价风险与枢纽价差风险。",
                "理解 NBP 与 TTF 比较需要单位和汇率归一化。",
                "在商业敞口来自地点或枢纽价差时使用基差套保。",
            ],
        },
        tags=("europe_gas", "ttf", "nbp", "basis", "spread", "units_fx"),
        metadata={
            "region_label": {"en": "Europe", "zh": "欧洲"},
            "default_symbol": "NG=F",
            "route_type": "hub_spread_proxy",
            "v1_focus": True,
        },
    ),
    TrainingScenario(
        scenario_id="europe_storage_calendar_spread",
        commodity="natural_gas",
        status="enabled",
        region="europe",
        title=LocalizedText("Europe Storage Calendar Spread", "欧洲储气库月差"),
        summary=LocalizedText(
            "A storage operator manages injection and withdrawal margin with calendar spreads.",
            "储气库运营商通过月差管理注气与采气利润。",
        ),
        difficulty="advanced",
        primary_asset_id="europe_gas_calendar_spread_proxy",
        exposure={
            "direction": "long",
            "volume_mmbtu": 75000,
            "risk": {
                "en": "Storage value depends on seasonal spreads, carrying cost, and deliverability.",
                "zh": "储气价值取决于季节性价差、持有成本和可交付能力。",
            },
        },
        recommended_tool="calendar_spread",
        recommended_side="spread",
        learning_objectives={
            "en": [
                "Relate storage value to nearby/deferred spreads.",
                "Check injection, withdrawal, and carry assumptions.",
                "Use spread hedges to manage seasonal margin risk.",
            ],
            "zh": [
                "将储气价值与近远月价差联系起来。",
                "检查注气、采气和持有成本假设。",
                "使用价差工具管理季节性利润风险。",
            ],
        },
        tags=("europe_gas", "storage", "calendar_spread", "seasonality"),
        metadata={"region_label": {"en": "Europe", "zh": "欧洲"}, "default_symbol": "NG=F", "v1_focus": True},
    ),
)

NORTH_AMERICA_GAS_PLACEHOLDERS: tuple[TrainingScenario, ...] = (
    TrainingScenario(
        scenario_id="north_america_henry_hub_short_hedge",
        commodity="natural_gas",
        status="constructing",
        region="north_america",
        title=LocalizedText("North America Producer Short Hedge", "北美生产商卖出套保"),
        summary=LocalizedText(
            "Future regional extension for Henry Hub producer hedging.",
            "后续北美区域扩展：亨利港生产商套保。",
        ),
        difficulty="intro",
        primary_asset_id="henry_hub_front_month",
        exposure={"direction": "long", "volume_mmbtu": 100000},
        recommended_tool="short_hedge",
        recommended_side="sell",
        learning_objectives={"en": ["Match production risk with short futures."], "zh": ["将产量风险与期货空头匹配。"]},
        tags=("north_america_gas", "henry_hub", "producer"),
        metadata={"region_label": {"en": "North America", "zh": "北美"}, "default_symbol": "NG=F"},
    ),
)


def build_default_registry() -> ScenarioRegistry:
    registry = ScenarioRegistry()
    registry.register_many(EUROPE_GAS_SCENARIOS)
    registry.register_many(NORTH_AMERICA_GAS_PLACEHOLDERS)
    return registry


DEFAULT_SCENARIO_REGISTRY = build_default_registry()


def list_registered_scenarios(locale: str = "en", commodity: str | None = None, region: str | None = None, enabled_only: bool = True) -> list[dict[str, Any]]:
    if enabled_only:
        return DEFAULT_SCENARIO_REGISTRY.enabled(commodity=commodity, region=region, locale=locale)
    return DEFAULT_SCENARIO_REGISTRY.list(commodity=commodity, region=region, locale=locale)
