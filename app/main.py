import re
import subprocess
import sys
from pathlib import Path

import streamlit as st

# Add the workspace root to the Python path so pages and core modules can be imported
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import init_language, t
from app.assistant import render_assistant_sidebar

init_language()

st.set_page_config(
    page_title="Hedge Lab Terminal",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _inject_terminal_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            color-scheme: dark;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .main, .stApp, .css-1y4p8pa, .block-container {
            background: #060b17 !important;
            color: #e7eef8 !important;
        }

        .stSidebar {
            background: #081123 !important;
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        .block-container {
            padding: 1.6rem 1.8rem 2rem;
            max-width: 1350px;
            margin: 0 auto;
        }

        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            color: #f8fafc !important;
            font-weight: 700;
        }

        .stButton>button, .stDownloadButton>button {
            border-radius: 999px !important;
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%) !important;
            color: #ffffff !important;
            border: none !important;
            min-height: 46px;
            box-shadow: 0 18px 45px rgba(37, 99, 235, 0.18);
        }

        .stButton>button:hover, .stDownloadButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 22px 48px rgba(37, 99, 235, 0.2);
        }

        .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div>select, .stNumberInput>div>div>input {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            color: #e7eef8 !important;
            border-radius: 12px !important;
        }

        .stDataFrame div.row {
            background: rgba(255,255,255,0.02);
        }

        .stAlert {
            border-radius: 18px !important;
            padding: 18px !important;
            background: rgba(14, 30, 65, 0.88) !important;
        }

        .css-1o72pil, .css-1siy2j7, .css-13sdmh0 {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            box-shadow: 0 24px 48px rgba(0,0,0,0.12);
            border-radius: 22px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


_inject_terminal_theme()

pages = {
    "Welcome": [
        st.Page("pages/0_GettingStarted.py", title="Welcome", icon="🚀", default=True),
    ],
    "Market": [
        st.Page("pages/1_MarketExplorer.py", title="Market Explorer", icon="📈"),
    ],
    "Simulator": [
        st.Page("pages/2_HedgeSimulator.py", title="Hedge Simulator", icon="🧠"),
    ],
    "Practice": [
        st.Page("pages/5_Practice.py", title="Practice", icon="🎓"),
    ],
    "Settings": [
        st.Page("pages/4_Settings.py", title="Settings", icon="⚙️"),
    ],
}

pg = st.navigation(pages, position="sidebar")

with st.sidebar:
    st.markdown("---")
    version = "dev"
    try:
        pp = (workspace_root / "pyproject.toml").read_text(encoding="utf-8")
        m = re.search(r'^version\s*=\s*"([^"]+)"', pp, re.MULTILINE)
        if m:
            version = m.group(1)
    except Exception:
        pass

    commit = "unknown"
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=workspace_root).decode().strip()
    except Exception:
        pass

    st.caption(f"Hedge Lab Terminal v{version} · {commit}")
    st.caption("Desktop-style learning experience")
    render_assistant_sidebar(workspace_root)

pg.run()
