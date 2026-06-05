from copy import deepcopy

import pandas as pd
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


def test_list_categories_excludes_grains_and_marks_non_gas_constructing():
    categories = list_categories(locale="en")
    by_id = {category["id"]: category for category in categories}

    assert "grains" not in by_id
    assert set(by_id) == {"natural_gas", "oil_products", "metals"}
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


def test_mandarin_catalog_labels_are_available_without_grains():
    categories = {category["id"]: category for category in list_categories(locale="zh")}
    scenarios = {scenario["id"]: scenario for scenario in list_scenarios(locale="zh")}

    assert categories["natural_gas"]["label"] == "天然气"
    assert categories["oil_products"]["label"] == "油品"
    assert categories["metals"]["label"] == "金属"
    assert "grains" not in categories
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
    assert context["data_source"] == "simulated"
    assert context["data_source_label"] == "Simulated"
    assert context["symbol"] == "NG=F"
    assert len(context["price_series"]) >= 6
    assert context["price_points"] == context["price_series"]
    assert context["latest_price"] == context["price_series"][-1]["close"]
    assert all("date" in point and "close" in point for point in context["price_series"])


def test_yahoo_finance_source_uses_live_data_before_fallback(monkeypatch):
    def fake_fetch_history_daily(ticker, period_if_no_start="3mo", start=None):
        assert ticker == "NG=F"
        assert period_if_no_start == "3mo"
        return pd.DataFrame(
            [
                {"date": pd.Timestamp("2026-05-01").date(), "close": 3.1111},
                {"date": pd.Timestamp("2026-05-02").date(), "close": 3.2222},
            ]
        )

    monkeypatch.setattr("core.yf_prices.fetch_history_daily", fake_fetch_history_daily)

    context = get_market_context("winter_load_spike", source="Yahoo Finance")

    assert context["source"] == "yfinance"
    assert context["source_label"] == "Yahoo Finance"
    assert context["data_source"] == "yfinance"
    assert context["data_source_label"] == "Yahoo Finance"
    assert context["price_series"] == [
        {"date": "2026-05-01", "close": 3.1111},
        {"date": "2026-05-02", "close": 3.2222},
    ]
    assert context["latest_price"] == 3.2222
    assert context["metadata"]["returned_source"] == "yfinance"
    assert context["metadata"]["returned_source_label"] == "Yahoo Finance"
    assert context["metadata"]["is_fallback"] is False


def test_yahoo_finance_empty_response_falls_back_to_simulated(monkeypatch):
    monkeypatch.setattr("core.yf_prices.fetch_history_daily", lambda *args, **kwargs: pd.DataFrame())

    context = get_market_context("winter_load_spike", source="yfinance")

    assert context["source"] == "yfinance"
    assert context["source_label"] == "Yahoo Finance"
    assert context["data_source"] == "simulated"
    assert context["data_source_label"] == "Simulated"
    assert context["price_series"]
    assert context["metadata"]["requested_source"] == "yfinance"
    assert context["metadata"]["returned_source"] == "simulated"
    assert context["metadata"]["is_fallback"] is True
    assert "Yahoo Finance returned no usable close prices" in context["metadata"]["fallback_reason"]


def test_platts_source_uses_simulated_fallback_until_adapter_exists():
    context = get_market_context("winter_load_spike", source="platts")

    assert context["source"] == "platts"
    assert context["source_label"] == "Platts"
    assert context["data_source"] == "simulated"
    assert context["data_source_label"] == "Simulated"
    assert context["price_series"]
    assert context["latest_price"] == context["price_series"][-1]["close"]
    assert context["metadata"]["requested_source"] == "platts"
    assert context["metadata"]["returned_source"] == "simulated"
    assert context["metadata"]["is_fallback"] is True
