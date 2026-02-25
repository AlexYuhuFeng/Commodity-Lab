# app/pages/4_Analytics.py
"""Analytics workspace for feature and relationship analysis."""

import sys
from pathlib import Path

import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import init_language, render_language_switcher, t

init_language()

st.set_page_config(page_title="Commodity Lab - Analytics", layout="wide")
render_language_switcher()

st.title(f"📊 {t('analytics')}")
st.caption("Feature engineering, regime detection, and correlation diagnostics.")

c1, c2, c3 = st.columns(3)
c1.metric("Feature Library", "Rolling / Zscore")
c2.metric("Correlation", "Pair + Matrix")
c3.metric("Market State", "Volatility Regime")

st.divider()

st.markdown("### Planned modules")
st.markdown(
    """
1. **Feature Studio**: rolling stats, percentile bands, signal transforms.
2. **Relationship Lab**: spread z-score, rolling correlation, lead-lag checks.
3. **Regime Monitor**: volatility buckets, anomaly markers, trend state.
"""
)

with st.expander("🧭 How to use this page / 使用建议", expanded=True):
    st.markdown(
        """
- Step 1: Validate instrument data quality in Data Showcase.
- Step 2: Build derived series before running relationship analysis.
- Step 3: Save validated features and feed them to backtesting.
        """
    )

st.info("Analytics modules are being completed in iterative milestones.")
