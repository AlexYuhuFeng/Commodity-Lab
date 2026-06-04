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

    assert len(scenarios) >= 5
    assert {scenario["status"] for scenario in scenarios} == {"enabled"}
    assert {scenario["commodity_id"] for scenario in scenarios} == {"natural_gas"}
    assert {scenario["commodity"] for scenario in scenarios} == {"natural_gas"}
    assert all(scenario["enabled"] is True for scenario in scenarios)


def test_list_scenarios_filters_disabled_or_non_natural_gas_entries(monkeypatch):
    disabled_gas = deepcopy(gas_scenarios._SCENARIO_DATA[0])
    disabled_gas["id"] = "disabled_gas"
    disabled_gas["status"] = "constructing"
    disabled_gas["enabled"] = False

    enabled_metals = deepcopy(gas_scenarios._SCENARIO_DATA[0])
    enabled_metals["id"] = "enabled_metals"
    enabled_metals["commodity_id"] = "metals"
    enabled_metals["commodity"] = "metals"

    monkeypatch.setattr(
        gas_scenarios,
        "_SCENARIO_DATA",
        [*gas_scenarios._SCENARIO_DATA, disabled_gas, enabled_metals],
    )

    scenario_ids = {scenario["id"] for scenario in list_scenarios(locale="en")}

    assert "disabled_gas" not in scenario_ids
    assert "enabled_metals" not in scenario_ids


def test_list_categories_marks_non_natural_gas_categories_constructing():
    categories = list_categories(locale="en")
    by_id = {category["id"]: category for category in categories}

    assert {"natural_gas", "oil_products", "metals", "grains"}.issubset(by_id)
    assert by_id["natural_gas"]["status"] == "enabled"
    for category_id, category in by_id.items():
        if category_id != "natural_gas":
            assert category["status"] == "constructing"


def test_get_pipeline_capacity_scenario_is_localized_in_mandarin():
    scenario = get_scenario("pipeline_capacity_constraint", locale="zh")

    assert scenario["id"] == "pipeline_capacity_constraint"
    assert scenario["title"] == "管道运力约束"
    assert scenario["commodity_label"] == "天然气"
    assert scenario["title"]
    assert scenario["guided_steps"][0]["id"] == "understand_exposure"
    assert scenario["guided_steps"][0]["label"] == "识别风险敞口"
    assert scenario["guided_steps"][1]["label"] == "观察市场"
    assert scenario["guided_steps"][2]["label"] == "建立套保"
    assert scenario["guided_steps"][3]["label"] == "复盘评分"
    assert scenario["guided_steps"][4]["label"] == "测验"
    assert scenario["learning_objectives"]


def test_mandarin_catalog_labels_are_available():
    categories = {category["id"]: category for category in list_categories(locale="zh")}
    scenarios = {scenario["id"]: scenario for scenario in list_scenarios(locale="zh")}

    assert categories["natural_gas"]["label"] == "天然气"
    assert categories["oil_products"]["label"] == "油品"
    assert categories["metals"]["label"] == "金属"
    assert categories["grains"]["label"] == "谷物"
    assert scenarios["producer_short_hedge"]["title"] == "生产商卖出套保"
    assert scenarios["winter_load_spike"]["title"] == "冬季负荷上升"
    assert scenarios["pipeline_capacity_constraint"]["title"] == "管道运力约束"
    assert scenarios["regional_basis_blowout"]["title"] == "区域基差扩大"
    assert scenarios["storage_calendar_spread"]["title"] == "储气库月差套保"


def test_producer_short_hedge_includes_task_two_contract_fields():
    scenario = get_scenario("producer_short_hedge", locale="en")

    assert scenario["commodity"] == "natural_gas"
    assert scenario["enabled"] is True
    assert scenario["recommended_side"] == "sell"
    assert scenario["recommended_hedge_type"] == "short_hedge"
    assert scenario["default_symbol"] == "NG=F"
    assert scenario["exposure"]["direction"] == "long"
    assert scenario["exposure"]["volume_mmbtu"] == 100000
    assert scenario["exposure"]["risk"]


def test_pipeline_capacity_constraint_uses_sell_basis_hedge_contract():
    scenario = get_scenario("pipeline_capacity_constraint", locale="en")

    assert scenario["recommended_side"] == "sell"
    assert scenario["recommended_hedge_type"] == "basis_hedge"
    assert scenario["exposure"]["volume_mmbtu"] == 60000


def test_capacity_context_for_pipeline_constraint_has_visual_flow_fields():
    context = get_capacity_context("pipeline_capacity_constraint")

    assert context["receipt_point"] == "Permian Receipt"
    assert context["delivery_point"] == "Gulf Coast Delivery"
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


def test_sample_market_context_for_winter_load_spike_has_prices():
    context = get_market_context("winter_load_spike", source="sample")

    assert context["source"] == "sample"
    assert context["source_label"] == "Simulated"
    assert context["symbol"] == "NG=F"
    assert len(context["price_series"]) >= 6
    assert context["price_points"] == context["price_series"]
    assert context["latest_price"] == context["price_series"][-1]["close"]
    assert all("date" in point and "close" in point for point in context["price_series"])


@pytest.mark.parametrize(
    ("source", "source_label"),
    [
        ("yfinance", "Yahoo Finance"),
        ("platts", "Platts"),
    ],
)
def test_external_market_sources_are_labeled_with_simulated_fallback(source, source_label):
    context = get_market_context("winter_load_spike", source=source)

    assert context["source"] == source
    assert context["source_label"] == source_label
    assert context["data_source"] == "simulated"
    assert context["data_source_label"] == "Simulated"
    assert context["price_series"]
    assert context["latest_price"] == context["price_series"][-1]["close"]
    assert context["metadata"]["requested_source"] == source
    assert context["metadata"]["requested_source_label"] == source_label
    assert context["metadata"]["returned_source"] == "simulated"
    assert context["metadata"]["returned_source_label"] == "Simulated"
    assert context["metadata"]["is_fallback"] is True


def test_literal_yahoo_finance_source_uses_yahoo_finance_label_with_simulated_fallback():
    context = get_market_context("winter_load_spike", source="Yahoo Finance")

    assert context["source"] == "yfinance"
    assert context["source_label"] == "Yahoo Finance"
    assert context["data_source"] == "simulated"
    assert context["data_source_label"] == "Simulated"
    assert context["metadata"]["requested_source"] == "yfinance"
    assert context["metadata"]["requested_source_label"] == "Yahoo Finance"
    assert context["metadata"]["returned_source"] == "simulated"
    assert context["metadata"]["returned_source_label"] == "Simulated"
    assert context["metadata"]["is_fallback"] is True
