from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import get_language, init_language, render_language_switcher, t

init_language()
st.set_page_config(page_title="Hedge Lab - Settings", layout="wide")
render_language_switcher()
lang = get_language()


def l(en: str, zh: str) -> str:
    return zh if lang == "zh" else en

st.title("⚙️ Settings")
st.caption(l("Configure API keys and environment settings for Platts and DEEPSEEK.", "配置 Platts 和 DEEPSEEK API 密钥。"))

platts_key = st.text_input(l("Platts API key", "Platts API 密钥"), value=os.getenv("PLATTS_API_KEY", ""), type="password")
deepseek_key = st.text_input(l("DEEPSEEK API key", "DEEPSEEK API 密钥"), value=os.getenv("DEEPSEEK_API_KEY", ""), type="password")
deepseek_url = st.text_input(l("DEEPSEEK API URL", "DEEPSEEK API URL"), value=os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.ai/v1/analysis"))

if st.button(l("Save to .env", "保存到 .env")):
    env_path = workspace_root / ".env"
    lines = [
        f"PLATTS_API_KEY={platts_key}\n",
        f"DEEPSEEK_API_KEY={deepseek_key}\n",
        f"DEEPSEEK_API_URL={deepseek_url}\n",
    ]
    env_path.write_text("".join(lines), encoding="utf-8")
    st.success(l("Saved API settings to .env. Restart the app to pick them up.", "已保存 API 配置到 .env。重启应用以生效。"))

st.markdown(
    l(
        "Use these settings to activate live Platts quotes and DEEPSEEK analysis. If you prefer, export the same variables into your shell environment.",
        "使用这些设置启用 Platts 实时数据和 DEEPSEEK 分析。也可以将相同变量导出至 shell 环境。",
    )
)

st.code(
    """
export PLATTS_API_KEY=your_platts_key
export DEEPSEEK_API_KEY=your_deepseek_key
export DEEPSEEK_API_URL=https://api.deepseek.ai/v1/analysis
""",
    language="bash",
)
