from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher

init_language()
st.set_page_config(page_title="Commodity Lab - Getting Started", layout="wide")
render_language_switcher()
lang = get_language()

def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title(l("🚀 Getting Started", "🚀 新手指引"))
st.caption(l("One-page map of what each page does and when to use it.", "一页看懂每个页面做什么、何时使用。"))

items = [
    ("1) Data Management", "搜索并关注标的；支持CSV上传原始序列；刷新本地库。", "Search/watch tickers, upload CSV raw series, refresh local data."),
    ("2) Data Showcase", "看K线与QC，维护元数据和派生序列。", "Inspect chart/QC, manage metadata and derived series."),
    ("3) Analytics", "可比较raw与derived，做单位换算后生成并保存spread序列。", "Compare raw/derived with normalization and persist spread series."),
    ("4) Monitoring", "配置告警规则、通知渠道与调度。", "Configure alert rules, notification channels, and scheduler."),
    ("5) Strategies & Backtest", "在主页面配置参数并回测，查看指标与成交。", "Configure on-page controls, run backtests, inspect metrics/trades."),
    ("6) Auto Strategy Lab", "批量策略实验、评分与历史追踪。", "Batch strategy experiments, scoring, and run history tracking."),
]

for title, zh_desc, en_desc in items:
    with st.container(border=True):
        st.subheader(title)
        st.write(zh_desc if lang == "zh" else en_desc)

st.info(l("Suggested order: Data Management → Data Showcase → Analytics → Monitoring/Backtest.", "建议顺序：数据管理 → 数据展示 → 分析 → 监控/回测。"))
