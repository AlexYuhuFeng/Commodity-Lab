import sys
from pathlib import Path

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

render_language_switcher()

st.title("🌾 Commodity Lab")
st.subheader("Internal commodity analytics workspace")

st.markdown(
    """
> A practical platform for data ingestion, QC, monitoring, and strategy evaluation.
> Use the **Getting Started** page first if you are new to the product.
"""
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Data", "Management + Showcase")
k2.metric("Alerts", "Rules + Event History")
k3.metric("Backtest", "Strategy Simulation")
k4.metric("Languages", "EN / 中文")

st.divider()

left, right = st.columns([1.4, 1])
with left:
    st.subheader("Recommended workflow")
    st.markdown(
        f"""
1. **{t('data_management')}**: search + import watched instruments.
2. **{t('data_showcase')}**: verify QC, metadata, and derived series.
3. **{t('monitoring')}**: define alert rules and validate behavior.
4. **{t('strategies')}**: run parameterized backtests with realistic costs.
        """
    )

with right:
    with st.container(border=True):
        st.markdown("### ✨ Product guidance")
        st.markdown(
            """
- Check data freshness before decisions.
- Treat alerts as triage, not final verdict.
- Include costs/slippage in strategy tests.
- Export outputs for audit trails.
            """
        )

with st.expander("📘 Functional explanations / 功能说明", expanded=False):
    st.markdown(
        f"""
- **{t('data_management')}**: Discover symbols, watchlist curation, and refresh actions.
- **{t('data_showcase')}**: Multi-tab data view, charting, QC, and metadata adjustments.
- **{t('monitoring')}**: Alert rule lifecycle, quick tests, and acknowledgment workflow.
- **{t('strategies')}**: Run strategy simulations, inspect equity curve and trade lists.
        """
    )
