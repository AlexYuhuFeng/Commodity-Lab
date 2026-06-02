from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher, t
from core.deepseek import ask_deepseek
from core.db import default_db_path, get_conn, init_db, list_instruments

init_language()
st.set_page_config(page_title="Hedge Lab - Advisor", layout="wide")
render_language_switcher()
lang = get_language()


def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title("🧭 DEEPSEEK Advisor")
st.caption(
    l(
        "The AI advisor now lives as a persistent sidebar assistant so you can keep market, order, and simulation context visible.",
        "AI 顾问现在作为持久侧边栏助手存在，您可以保持市场、订单和模拟上下文可见。",
    )
)

st.info(
    l(
        "Open the assistant from the sidebar while using Market Explorer and Hedge Simulator.",
        "在使用市场探索和对冲模拟时，请从侧边栏打开助手。",
    )
)

st.markdown(
    l(
        "This page is kept for reference, but the assistant is available during all workflows.",
        "此页面保留作为参考，但助手可在所有工作流中使用。",
    )
)

if "deepseek_history" not in st.session_state:
    st.session_state.deepseek_history = []

con = get_conn(default_db_path(workspace_root))
init_db(con)

st.markdown(
    l(
        "Use the dropdown menu to open the AI Assistant in the sidebar while you review market data and run hedge simulations.",
        "使用下拉菜单在侧边栏打开 AI 助手，同时查看市场数据并运行对冲模拟。",
    )
)

if st.session_state.deepseek_history:
    st.subheader(l("Recent assistant exchanges", "最近的助手互动"))
    for idx, entry in enumerate(reversed(st.session_state.deepseek_history), 1):
        st.markdown(f"**{idx}. {entry['mode']}** — {entry['question']}")
        st.info(entry["answer"])
else:
    st.info(
        l(
            "The assistant will store your latest questions and responses here when used from the sidebar.",
            "当从侧边栏使用助手时，它会在此存储您最近的问题和回答。",
        )
)

try:
    con.close()
except Exception:
    pass
