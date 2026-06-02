from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher, t
from core.hedge import HEDGE_TYPES, ORDER_SIDES
from core.practice import get_practice_categories, get_scenarios, evaluate_plan

init_language()
st.set_page_config(page_title="Hedge Lab - Practice", layout="wide")
render_language_switcher()
lang = get_language()

def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title("🎓 Hedge Practice")
st.caption(l("Work through scenario-based questions across multiple hedge categories.", "通过情景题训练对冲逻辑，覆盖多个风险类别。"))

category = st.selectbox(l("Practice category", "练习类别"), options=get_practice_categories())
questions = get_scenarios(category)

if not questions:
    st.warning(l("No scenarios are available for this category.", "该类别暂无情景题。"))
    st.stop()

scenario_options = {q["title"]: q for q in questions}
selected_title = st.selectbox(l("Choose a scenario", "选择情景"), options=list(scenario_options.keys()))
selected_scenario = scenario_options[selected_title]

with st.container():
    st.markdown("---")
    st.subheader(selected_scenario["title"])
    st.write(selected_scenario["description"])
    st.markdown(l("**Key learning objective:**", "**关键学习目标：**"))
    st.write(l(
        "Match the hedge structure to the dominant risk exposure in this scenario.",
        "根据场景中的主要风险暴露选择合适的对冲结构。",
    ))

with st.form("practice_form"):
    hedge_type = st.selectbox(l("Recommended hedge type", "建议对冲类型"), options=HEDGE_TYPES)
    side = st.selectbox(l("Expected position side", "预计持仓方向"), options=ORDER_SIDES)
    quantity = st.number_input(l("Notional quantity", "名义数量"), value=1.0, min_value=0.1, step=0.1)
    rationale = st.text_area(l("Explain your rationale", "解释你的理由"), height=120)
    submit = st.form_submit_button(l("Submit answer", "提交答案"))

if submit:
    result = evaluate_plan(category, hedge_type, side)
    st.success(l(f"Practice score: {result['score']}/100", f"练习得分：{result['score']}/100"))
    st.write(result["feedback"])
    st.markdown(l(
        "Use the Hedge Simulator to validate your chosen structure with virtual orders.",
        "使用对冲模拟器验证你的对冲结构是否合理。",
    ))

st.markdown("---")
st.subheader(l("Why this matters", "为什么这很重要"))
st.write(l(
    "Learning multiple question types helps you understand why some hedges protect cash flow, while others manage basis or seasonal risk.",
    "练习多种题型有助于理解某些对冲是保护现金流，另一些则是管理基差或季节性风险。",
))
