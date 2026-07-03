"""Shared energy domain models for Commodity Lab.

The product is gas-first with an added crude-oil hedging course, but the domain model is deliberately generic so
future refined products, carbon, and power modules can reuse the same
asset, scenario, market-context, and AI-capability contracts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Commodity = Literal["natural_gas", "crude_oil", "oil_products", "carbon", "power"]
ModuleStatus = Literal["enabled", "constructing", "disabled"]
ScenarioStatus = Literal["enabled", "constructing", "disabled"]


@dataclass(frozen=True)
class LocalizedText:
    """Minimal bilingual text block used by catalog objects."""

    en: str
    zh: str

    def get(self, locale: str = "en") -> str:
        return self.zh if (locale or "").lower().startswith("zh") else self.en

    def as_dict(self) -> dict[str, str]:
        return {"en": self.en, "zh": self.zh}


@dataclass(frozen=True)
class EnergyModule:
    """Top-level training module shown in the product navigation."""

    id: Commodity
    status: ModuleStatus
    label: LocalizedText
    description: LocalizedText
    rollout_phase: str
    enabled_regions: tuple[str, ...] = ()

    def localized(self, locale: str = "en") -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "label": self.label.get(locale),
            "description": self.description.get(locale),
            "rollout_phase": self.rollout_phase,
            "enabled_regions": list(self.enabled_regions),
        }


@dataclass(frozen=True)
class EnergyAsset:
    """Tradable or risk-bearing energy asset definition.

    Examples:
    - TTF front-month gas future proxy.
    - NBP hub spread leg.
    - Brent future.
    - EUA Dec contract.
    - German baseload power product.
    """

    asset_id: str
    commodity: Commodity
    region: str
    hub: str
    display_name: str
    currency: str
    unit: str
    pricing_index: str
    exchange: str | None = None
    settlement_type: str = "financial"
    contract_type: str = "future"
    data_symbol: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrainingScenario:
    """Generic scenario contract reused across all energy commodities."""

    scenario_id: str
    commodity: Commodity
    status: ScenarioStatus
    region: str
    title: LocalizedText
    summary: LocalizedText
    difficulty: str
    primary_asset_id: str
    exposure: dict[str, Any]
    recommended_tool: str
    recommended_side: str
    learning_objectives: dict[str, list[str]]
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def localized(self, locale: str = "en") -> dict[str, Any]:
        active_locale = "zh" if (locale or "").lower().startswith("zh") else "en"
        return {
            "id": self.scenario_id,
            "status": self.status,
            "commodity_id": self.commodity,
            "commodity": self.commodity,
            "enabled": self.status == "enabled",
            "region": self.region,
            "region_label": self.metadata.get("region_label", {}).get(active_locale, self.region),
            "difficulty": self.difficulty,
            "title": self.title.get(active_locale),
            "summary": self.summary.get(active_locale),
            "exposure": self.exposure,
            "recommended_hedge_type": self.recommended_tool,
            "recommended_side": self.recommended_side,
            "primary_asset_id": self.primary_asset_id,
            "default_symbol": self.metadata.get("default_symbol", ""),
            "learning_objectives": self.learning_objectives.get(active_locale, []),
            "tags": list(self.tags),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AICapability:
    """AI capability registration independent of commodity type."""

    id: str
    label: LocalizedText
    description: LocalizedText
    requires_llm: bool = True
    supported_commodities: tuple[Commodity, ...] = (
        "natural_gas",
        "crude_oil",
        "oil_products",
        "carbon",
        "power",
    )

    def localized(self, locale: str = "en") -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label.get(locale),
            "description": self.description.get(locale),
            "requires_llm": self.requires_llm,
            "supported_commodities": list(self.supported_commodities),
        }


ENERGY_MODULES: tuple[EnergyModule, ...] = (
    EnergyModule(
        id="natural_gas",
        status="enabled",
        label=LocalizedText("Natural Gas", "天然气"),
        description=LocalizedText(
            "V1 enabled module focused on Europe gas, with North America gas as the next regional extension.",
            "V1 已启用模块，优先聚焦欧洲天然气，并为北美天然气扩展预留。",
        ),
        rollout_phase="v1",
        enabled_regions=("europe",),
    ),
    EnergyModule(
        id="crude_oil",
        status="enabled",
        label=LocalizedText("Crude Oil", "原油"),
        description=LocalizedText("Enabled course track for Brent, WTI, Dubai, calendar/basis spreads, physical cargoes, inventory, and freight risk.", "已启用课程轨道，覆盖 Brent、WTI、Dubai、月差/基差、实货船货、库存和运费风险。"),
        rollout_phase="v1.2",
        enabled_regions=("global",),
    ),
    EnergyModule(
        id="oil_products",
        status="constructing",
        label=LocalizedText("Oil Products", "成品油"),
        description=LocalizedText("Future module for gasoline, gasoil, jet, fuel oil, cracks, and regional arbitrage.", "后续模块，预留汽油、柴油/柴油组分、航煤、燃料油、裂解价差和区域套利训练。"),
        rollout_phase="v4",
    ),
    EnergyModule(
        id="carbon",
        status="constructing",
        label=LocalizedText("Carbon", "碳"),
        description=LocalizedText("Future module for EUA, UKA, CEA, compliance risk, and carbon-power linkages.", "后续模块，预留 EUA、UKA、CEA、履约风险和碳电联动训练。"),
        rollout_phase="v4",
    ),
    EnergyModule(
        id="power",
        status="constructing",
        label=LocalizedText("Power", "电力"),
        description=LocalizedText("Future module for baseload, peakload, spark spread, clean dark/spark, and regional power risk.", "后续模块，预留基荷、峰荷、spark spread、clean spread 和区域电力风险训练。"),
        rollout_phase="v4",
    ),
)

AI_CAPABILITIES: tuple[AICapability, ...] = (
    AICapability(
        id="case_generation",
        label=LocalizedText("Case generation", "案例生成"),
        description=LocalizedText("Generate realistic training cases from commodity, region, market, event, and user request context.", "基于商品、区域、市场、事件和用户需求生成贴近业务的训练案例。"),
    ),
    AICapability(
        id="event_drill",
        label=LocalizedText("Event drill", "事件演练"),
        description=LocalizedText("Turn market events into structured trading drills with verification warnings.", "将市场事件转化为结构化交易演练，并提示需要核实的事实。"),
    ),
    AICapability(
        id="concept_tutor",
        label=LocalizedText("Concept tutor", "概念教学"),
        description=LocalizedText("Explain futures, basis, spread, storage, capacity, route economics, carbon, and power concepts.", "讲解期货、基差、价差、储气、运力、路径经济性、碳和电力概念。"),
    ),
    AICapability(
        id="trade_playbook",
        label=LocalizedText("Trade playbook", "交易预案"),
        description=LocalizedText("Draft pre-trade checklists, execution plans, risk triggers, and post-trade review points.", "生成交易前检查清单、执行计划、风险触发条件和交易后复盘要点。"),
    ),
    AICapability(
        id="advisor_review",
        label=LocalizedText("Advisor review", "AI 复盘"),
        description=LocalizedText("Review a learner decision against deterministic scoring and scenario risk.", "结合确定性评分和场景风险复盘用户决策。"),
    ),
    AICapability(
        id="exam",
        label=LocalizedText("Adaptive exam", "自适应测验"),
        description=LocalizedText("Generate targeted questions from scenario context and prior mistakes.", "根据场景和历史错误生成针对性测验。"),
    ),
)


def list_energy_modules(locale: str = "en") -> list[dict[str, Any]]:
    return [module.localized(locale) for module in ENERGY_MODULES]


def list_ai_capabilities(locale: str = "en") -> list[dict[str, Any]]:
    return [capability.localized(locale) for capability in AI_CAPABILITIES]
