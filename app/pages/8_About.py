from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher

init_language()
st.set_page_config(page_title="Commodity Lab - About", layout="wide")
render_language_switcher()
lang = get_language()

def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

version = "0.1.0"
commit = "unknown"
try:
    commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=workspace_root).decode().strip()
except Exception:
    pass

st.title(l("ℹ️ About Commodity Lab", "ℹ️ 关于 Commodity Lab"))

st.markdown(
    l(
        "Commodity Lab is a local-first commodity analytics and strategy research workbench.",
        "Commodity Lab 是一个本地优先的商品数据分析与策略研究工作台。",
    )
)

c1, c2, c3 = st.columns(3)
c1.metric(l("Version", "版本"), version)
c2.metric(l("Git Commit", "提交哈希"), commit)
c3.metric(l("Runtime", "运行环境"), "Streamlit")

st.subheader(l("Developer Information", "开发者信息"))
st.write(l("Team: Commodity Lab Contributors", "团队：Commodity Lab Contributors"))
st.write("Email: dev@commoditylab.local")

st.subheader(l("Open Source Components", "开源组件"))
st.write("- Streamlit")
st.write("- DuckDB")
st.write("- Pandas")
st.write("- Plotly")
st.write("- yfinance / tushare (optional)")
