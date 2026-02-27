import re
import subprocess
import sys
from pathlib import Path

import streamlit as st

# Add the workspace root to the Python path so core module can be imported
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import init_language, t

init_language()

st.set_page_config(
    page_title="Commodity Lab",
    layout="wide",
    initial_sidebar_state="collapsed",
)

pages = {
    "Start Here": [
        st.Page("pages/0_GettingStarted.py", title="Getting Started", icon="🚀", default=True),
    ],
    "Data Workspace": [
        st.Page("pages/1_DataManagement.py", title=t("nav.data_management"), icon="📊"),
        st.Page("pages/2_DataShowcase.py", title=t("nav.data_showcase"), icon="🔍"),
<<<<<<< HEAD
        st.Page("pages/9_DerivedManagement.py", title="Derived Management", icon="🔗"),
=======
        st.Page("pages/9_DerivedManagement.py", title="Synthetic Series Studio", icon="🔗"),
>>>>>>> origin/codex/resolve-project-issues-y7ic9g
    ],
    "Monitoring": [
        st.Page("pages/3_MonitoringAlerts.py", title=t("nav.monitoring"), icon="🚨"),
        st.Page("pages/3_NotificationSetup.py", title="Notification Setup", icon="📧"),
        st.Page("pages/6_SchedulerNotifications.py", title="Scheduler & Notifications", icon="⏱️"),
        st.Page("pages/4_ConditionEditor.py", title="Condition Editor", icon="🧩"),
    ],
    "Research & Strategies": [
        st.Page("pages/4_Analytics.py", title=t("nav.analytics"), icon="📈"),
        st.Page("pages/5_StrategiesBacktest.py", title=t("nav.strategies"), icon="🎯"),
        st.Page("pages/7_AutoStrategyLab.py", title="Auto Strategy Lab", icon="🤖"),
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

    st.caption(f"Commodity Lab v{version} · {commit}")
    st.caption("Developer: Commodity Lab Contributors")

pg.run()
