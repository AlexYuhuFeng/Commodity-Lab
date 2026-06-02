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
    assert scenarios["regional_basis_blowout"]["title"] == "区域基差扩大"
    assert scenarios["storage_calendar_spread"]["title"] == "储气库月差套保"


def test_capacity_context_for_pipeline_constraint_has_visual_flow_fields():
    context = get_capacity_context("pipeline_capacity_constraint")

    assert context["receipt_point"] == "Permian Receipt"
    assert context["delivery_point"] == "Gulf Coast Delivery"
    assert context["available_capacity_mmbtu"] > 0
    assert context["nominated_mmbtu"] > 0
    assert 0 < context["utilization_pct"] <= 100
    assert context["congestion_status"] in {"normal", "watch", "constrained"}


def test_sample_market_context_for_winter_load_spike_has_prices():
    context = get_market_context("winter_load_spike", source="sample")

    assert context["source"] == "sample"
    assert context["symbol"] == "NG=F"
    assert len(context["price_points"]) >= 6
    assert all("date" in point and "close" in point for point in context["price_points"])
