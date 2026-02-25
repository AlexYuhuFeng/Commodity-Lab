import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Add the workspace root to the Python path so core module can be imported
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import init_language, render_language_switcher, t

init_language()

st.set_page_config(
    page_title="Commodity Lab",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_home() -> None:
    render_language_switcher()

    st.title("🌾 Commodity Lab")
    st.subheader("Internal commodity analytics workspace")

    st.markdown(
        """
> A practical platform for data ingestion, QC, monitoring, and strategy evaluation.
> Use **Getting Started** first if you are new to the product.
"""
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Data", "Management + Showcase")
    k2.metric("Alerts", "Rules + Event History")
    k3.metric("Backtest", "Strategy Simulation")
    k4.metric("Languages", "EN / 中文")

    st.divider()

    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("Workflow Maturity Overview")
        maturity_df = pd.DataFrame(
            {
                "module": [
                    "Data Management",
                    "Data Showcase",
                    "Monitoring",
                    "Backtest",
                    "Automation",
                ],
                "maturity": [90, 88, 78, 80, 65],
            }
        )
        fig = px.bar(
            maturity_df,
            x="module",
            y="maturity",
            range_y=[0, 100],
            color="maturity",
            color_continuous_scale="Viridis",
            title="Current Product Maturity by Module",
        )
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=55, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Interactive Quick Guide")

        steps = [
            ("step_import", f"1) {t('data_management')}: import watched instruments"),
            ("step_qc", f"2) {t('data_showcase')}: verify QC + metadata"),
            ("step_alert", f"3) {t('monitoring')}: test and enable alert rules"),
            ("step_backtest", f"4) {t('strategies')}: run backtest with realistic costs"),
            ("step_auto", "5) Auto Strategy Lab: generate and rank candidates"),
        ]
        done = 0
        for key, label in steps:
            if st.checkbox(label, key=key):
                done += 1
        progress = done / len(steps)
        st.progress(progress, text=f"Progress: {done}/{len(steps)} steps")

    with st.expander("📘 Functional Explanations", expanded=False):
        st.markdown(
            f"""
- **{t('data_management')}**: Discover symbols, watchlist curation, and refresh actions.
- **{t('data_showcase')}**: Multi-tab data view, charting, QC, and metadata adjustments.
- **{t('monitoring')}**: Alert rule lifecycle, quick tests, and acknowledgment workflow.
- **{t('strategies')}**: Run strategy simulations, inspect equity curve and trade lists.
- **Auto Strategy Lab**: Automated candidate generation, ranking, and historical run tracking.
            """
        )


pages = {
    "Start Here": [
        st.Page(render_home, title="Home", icon="🏠", default=True),
        st.Page("pages/0_GettingStarted.py", title="Getting Started", icon="🚀"),
    ],
    "Data Workspace": [
        st.Page("pages/1_DataManagement.py", title="Data Management", icon="📊"),
        st.Page("pages/2_DataShowcase.py", title="Data Showcase", icon="🔍"),
    ],
    "Monitoring": [
        st.Page("pages/3_MonitoringAlerts.py", title="Monitoring & Alerts", icon="🚨"),
        st.Page("pages/3_NotificationSetup.py", title="Notification Setup", icon="📧"),
        st.Page("pages/6_SchedulerNotifications.py", title="Scheduler & Notifications", icon="⏱️"),
        st.Page("pages/4_ConditionEditor.py", title="Condition Editor", icon="🧩"),
    ],
    "Research & Strategies": [
        st.Page("pages/4_Analytics.py", title="Analytics", icon="📈"),
        st.Page("pages/5_StrategiesBacktest.py", title="Strategies & Backtest", icon="🎯"),
        st.Page("pages/7_AutoStrategyLab.py", title="Auto Strategy Lab", icon="🤖"),
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()
