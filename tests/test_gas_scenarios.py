from copy import deepcopy

import pytest

import core.gas_scenarios as gas_scenarios
from core.gas_scenarios import (
    get_capacity_context,
    get_market_context,
    get_scenario,
    list_categories,
    list_scenarios,
)


def test_list_scenarios_returns_enabled_natural_gas_only():
    scenarios = list_scenarios(locale="en")

    assert len(scenarios) >= 3
    assert {scenario["status"] for scenario in scenarios} == {"enabled"}
    assert {scenario["commodity_id"] for scenario in scenarios} == {"natural_gas"}
    assert {scenario["commodity"] for scenario in scenarios} == {"natural_gas"}
    assert {scenario["region"] for scenario in scenarios} == {"europe"}
    assert all(scenario["enabled"] is True for scenario in scenarios)


def test_list_scenarios_filters_disabled_or_non_natural_gas_entries(monkeypatch):
    disabled_gas = deepcopy(gas_scenarios._SCENARIO_DATA[0])
    disabled_gas["id"] = "disabled_gas"
    disabled_gas["status"] = "constructing"
    disabled_gas["enabled"] = False

    enabled_crude = deepcopy(gas_scenarios._SCENARIO_DATA[0])
    enabled_crude["id"] = "enabled_crude"
    enabled_crude["commodity_id"] = "crude_oil"
    enabled_crude["commodity"] = "crude_oil"

    monkeypatch.setattr(
        gas_scenarios,
        "_SCENARIO_DATA",
        [*gas_scenarios._SCENARIO_DATA, disabled_gas, enabled_crude],
    )

    scenario_ids = {scenario["id"] for scenario in list_scenarios(locale="en")}

    assert "disabled_gas" not in scenario_ids
    assert "enabled_crude" not in scenario_ids


def test_list_categories_matches_energy_scope():
    categories = list_categories(locale="en")
    by_id = {category["id"]: category for category in categories}

    assert set(by_id) == {"natural_gas", "crude_oil", "oil_products", "carbon", "power"}
    assert by_id["natural_gas"]["status"] == "enabled"
    for category_id, category in by_id.items():
        if category_id != "natural_gas":
            assert category["status"] == "constructing"


def test_get_europe_route_capacity_scenario_is_localized_in_mandarin():
    scenario = get_scenario("europe_route_capacity_constraint", locale="zh")

    assert scenario["id"] == "europe_route_capacity_constraint"
    assert scenario["title"] == "欧洲路径运力约束"
    assert scenario["commodity_label"] == "天然气"
    assert scenario["region_label"] == "欧洲"
    assert scenario["guided_steps"][0]["id"] == "understand_exposure"
    assert scenario["guided_steps"][0]["label"] == "识别风险敞口"
    assert scenario["guided_steps"][1]["label"] == "观察市场"
    assert scenario["guided_steps"][2]["label"] == "建立套保"
    assert scenario["guided_steps"][3]["label"] == "复盘评分"
    assert scenario["guided_steps"][4]["label"] == "测验"
    assert scenario["learning_objectives"]


def test_mandarin_catalog_labels_are_available_for_energy_scope():
    categories = {category["id"]: category for category in list_categories(locale="zh")}
    scenarios = {scenario["id"]: scenario for scenario in list_scenarios(locale="zh")}

    assert categories["natural_gas"]["label"] == "天然气"
    assert categories["crude_oil"]["label"] == "原油"
    assert categories["oil_products"]["label"] == "成品油"
    assert categories["carbon"]["label"] == "碳"
    assert categories["power"]["label"] == "电力"
    assert scenarios["europe_ttf_nbp_spread"]["title"] == "欧洲 TTF/NBP 价差"
    assert scenarios["europe_route_capacity_constraint"]["title"] == "欧洲路径运力约束"
    assert scenarios["europe_storage_calendar_spread"]["title"] == "欧洲储气库月差套保"


def test_europe_scenario_includes_region_and_spread_context():
    scenario = get_scenario("europe_ttf_nbp_spread", locale="en")
    capacity = get_capacity_context("europe_ttf_nbp_spread")

    assert scenario["region"] == "europe"
    assert scenario["region_label"] == "Europe"
    assert scenario["recommended_hedge_type"] == "basis_hedge"
    assert scenario["recommended_side"] == "sell"
    assert "TTF" in scenario["title"]
    assert capacity["receipt_point"] == "TTF Virtual Point"
    assert capacity["delivery_point"] == "NBP Virtual Point"


def test_constructing_north_america_scenarios_do_not_enter_v1_list():
    scenario = get_scenario("producer_short_hedge", locale="en")
    visible_ids = {item["id"] for item in list_scenarios(locale="en")}

    assert scenario["commodity"] == "natural_gas"
    assert scenario["region"] == "north_america"
    assert scenario["enabled"] is False
    assert scenario["status"] == "constructing"
    assert scenario["id"] not in visible_ids
    assert scenario["recommended_side"] == "sell"
    assert scenario["recommended_hedge_type"] == "short_hedge"
    assert scenario["default_symbol"] == "NG=F"
    assert scenario["exposure"]["direction"] == "long"
    assert scenario["exposure"]["volume_mmbtu"] == 100000
    assert scenario["exposure"]["risk"]


def test_europe_route_capacity_constraint_uses_sell_basis_hedge_contract():
    scenario = get_scenario("europe_route_capacity_constraint", locale="en")

    assert scenario["recommended_side"] == "sell"
    assert scenario["recommended_hedge_type"] == "basis_hedge"
    assert scenario["exposure"]["volume_mmbtu"] == 60000


def test_capacity_context_for_pipeline_constraint_has_visual_flow_fields():
    context = get_capacity_context("europe_route_capacity_constraint")

    assert context["receipt_point"] == "Zeebrugge Receipt"
    assert context["delivery_point"] == "THE Delivery"
    assert context["available_capacity_mmbtu"] > 0
    assert context["nominated_mmbtu"] > 0
    assert 0 < context["utilization_pct"] <= 100
    assert context["congestion_status"] in {"normal", "watch", "constrained"}
    assert context["flow_nodes"]
    assert context["flow_edges"]


def test_capacity_context_is_available_for_every_enabled_scenario():
    for scenario in list_scenarios(locale="en"):
        context = get_capacity_context(scenario["id"])

        assert context["scenario_id"] == scenario["id"]
        assert context["receipt_point"]
        assert context["delivery_point"]
        assert context["available_capacity_mmbtu"] > 0
        assert context["nominated_mmbtu"] > 0
        assert 0 < context["utilization_pct"] <= 100
        assert context["congestion_status"] in {"normal", "watch", "constrained"}
        assert context["flow_nodes"]
        assert context["flow_edges"]


def test_sample_market_context_for_route_capacity_has_prices():
    context = get_market_context("europe_route_capacity_constraint", source="sample")

    assert context["source"] == "ai_generated_training"
    assert context["source_label"] == "AI Generated Training Data"
    assert context["data_source"] == "ai_generated_training"
    assert context["data_source_label"] == "AI Generated Training Data"
    assert context["symbol"] == "NG=F"
    assert len(context["price_series"]) >= 6
    assert context["price_points"] == context["price_series"]
    assert context["latest_price"] == context["price_series"][-1]["close"]
    assert all("date" in point and "close" in point for point in context["price_series"])


def test_removed_external_source_argument_never_calls_market_providers():
    context = get_market_context("europe_route_capacity_constraint", source="removed_external_provider")

    assert context["source"] == "ai_generated_training"
    assert context["source_label"] == "AI Generated Training Data"
    assert context["data_source"] == "ai_generated_training"
    assert context["data_source_label"] == "AI Generated Training Data"
    assert context["price_series"]
    assert context["latest_price"] == context["price_series"][-1]["close"]
    assert context["metadata"]["requested_source"] == "ai_generated_training"
    assert context["metadata"]["returned_source"] == "ai_generated_training"
    assert context["metadata"]["is_fallback"] is False
