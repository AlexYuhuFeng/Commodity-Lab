from __future__ import annotations

import streamlit as st

from app.i18n import get_language, init_language, render_language_switcher

init_language()
st.set_page_config(page_title="Hedge Lab - Welcome", layout="wide")
render_language_switcher()
lang = get_language()

def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title(l("🚀 Hedge Lab Terminal", "🚀 对冲学习终端"))
st.caption(l("Practice hedge strategies on live contracts and get AI feedback.", "基于真实合约练习对冲策略，并获得 AI 反馈。"))

st.markdown(
    l(
        """
### What you can do here

- Discover contracts from Yahoo Finance or Platts.
- Watch and load contract data into the local simulator.
- Build virtual hedge orders and inspect P&L performance.
- Use the sidebar AI Assistant for analysis, risk commentary, and next-step suggestions.
""",
        """
### 您可以在这里完成的任务

- 从 Yahoo Finance 或 Platts 发现合约。
- 关注并加载合约历史数据到本地模拟器。
- 构建虚拟对冲订单并检查盈亏表现。
- 向 DEEPSEEK 提问，获取分析、风险评论与后续建议。
""",
    )
)

st.info(
    l(
        "Suggested workflow: Market Explorer → Hedge Simulator → Sidebar AI Assistant → Settings.",
        "建议流程：市场探索 → 对冲模拟 → 侧边栏 AI 助手 → 设置。",
    )
)
