from __future__ import annotations

from core.energy_models import (
    AI_CAPABILITIES,
    ENERGY_MODULES,
    EnergyAsset,
    LocalizedText,
    TrainingScenario,
    list_ai_capabilities,
    list_energy_modules,
)
from core.learner_profile import LearnerProfile


def test_energy_modules_are_europe_gas_first_and_extensible() -> None:
    modules = {module["id"]: module for module in list_energy_modules(locale="en")}

    assert set(modules) == {"natural_gas", "crude_oil", "oil_products", "carbon", "power"}
    assert modules["natural_gas"]["status"] == "enabled"
    assert modules["natural_gas"]["enabled_regions"] == ["europe"]
    assert modules["crude_oil"]["status"] == "constructing"
    assert modules["oil_products"]["status"] == "constructing"
    assert modules["carbon"]["status"] == "constructing"
    assert modules["power"]["status"] == "constructing"


def test_ai_capabilities_are_commodity_agnostic() -> None:
    capability_ids = {capability["id"] for capability in list_ai_capabilities(locale="en")}

    assert capability_ids >= {
        "case_generation",
        "event_drill",
        "concept_tutor",
        "trade_playbook",
        "advisor_review",
        "exam",
    }
    for capability in AI_CAPABILITIES:
        assert "natural_gas" in capability.supported_commodities
        assert "crude_oil" in capability.supported_commodities
        assert "oil_products" in capability.supported_commodities
        assert "carbon" in capability.supported_commodities
        assert "power" in capability.supported_commodities


def test_energy_asset_contract_supports_future_power_and_carbon() -> None:
    eua = EnergyAsset(
        asset_id="eua_dec_2027",
        commodity="carbon",
        region="europe",
        hub="EUA",
        display_name="EUA Dec-2027",
        currency="EUR",
        unit="tCO2e",
        pricing_index="EUA Dec future",
        exchange="ICE Endex",
        data_symbol="EUA_DEC_2027",
    )
    power = EnergyAsset(
        asset_id="germany_baseload_q1_2027",
        commodity="power",
        region="europe",
        hub="Germany",
        display_name="German Baseload Q1-2027",
        currency="EUR",
        unit="MWh",
        pricing_index="German Power Baseload",
        exchange="EEX",
    )

    assert eua.as_dict()["commodity"] == "carbon"
    assert eua.as_dict()["unit"] == "tCO2e"
    assert power.as_dict()["commodity"] == "power"
    assert power.as_dict()["unit"] == "MWh"


def test_training_scenario_localizes_without_being_gas_specific() -> None:
    scenario = TrainingScenario(
        scenario_id="brent_dubai_spread_training",
        commodity="crude_oil",
        status="constructing",
        region="global",
        title=LocalizedText("Brent-Dubai Spread", "Brent-Dubai 价差"),
        summary=LocalizedText("Crude spread training placeholder.", "原油价差训练占位。"),
        difficulty="intermediate",
        primary_asset_id="brent_dubai_spread",
        exposure={"direction": "spread", "volume": 100000},
        recommended_tool="spread",
        recommended_side="spread",
        learning_objectives={"en": ["Explain crude spread risk."], "zh": ["解释原油价差风险。"]},
        metadata={"region_label": {"en": "Global", "zh": "全球"}, "default_symbol": "BZ=F"},
    )

    localized = scenario.localized(locale="zh")

    assert localized["commodity"] == "crude_oil"
    assert localized["title"] == "Brent-Dubai 价差"
    assert localized["region_label"] == "全球"
    assert localized["default_symbol"] == "BZ=F"


def test_learner_profile_updates_weak_skills_from_evaluation() -> None:
    profile = LearnerProfile.create_default()

    payload = profile.apply_evaluation(
        {
            "baseline_score": 62,
            "mistake_tags": ["basis_risk", "unit_conversion"],
            "score_inputs": {"actual_hedge_type": "basis_hedge"},
        }
    )

    assert payload["attempt_count"] == 1
    assert payload["skills"]["basis"]["score"] < 50
    assert payload["skills"]["units_fx"]["score"] < 50
    assert payload["weakest_skills"][0]["score"] <= payload["weakest_skills"][-1]["score"]


def test_energy_module_registry_has_no_grains_or_metals() -> None:
    module_ids = {module.id for module in ENERGY_MODULES}

    assert "grains" not in module_ids
    assert "metals" not in module_ids
