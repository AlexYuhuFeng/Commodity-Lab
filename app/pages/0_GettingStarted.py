"""Getting Started page for onboarding new users."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import init_language, render_language_switcher, t

init_language()
st.set_page_config(page_title="Commodity Lab - Getting Started", layout="wide")
render_language_switcher()

st.title("🚀 Getting Started / 新手指引")
st.caption("Learn the workflow in 5 minutes and avoid common mistakes.")

col1, col2 = st.columns(2)
with col1:
    st.subheader("1) Import data")
    st.markdown(
        """
- Open **Data Management** to search symbols.
- Add watchlist instruments and trigger refresh.
- Verify freshness from refresh logs.
        """
    )
with col2:
    st.subheader("2) Explore and validate")
    st.markdown(
        """
- Use **Data Showcase** tabs for chart/QC/attributes.
- Fix metadata (currency/unit/category) before analysis.
- Confirm no major QC issues before strategy testing.
        """
    )

st.divider()

col3, col4 = st.columns(2)
with col3:
    st.subheader("3) Configure monitoring")
    st.markdown(
        """
- Create alert rules (price/zscore/volatility/staleness etc.).
- Test each rule immediately in Monitoring page.
- Enable scheduler + notifications after test pass.
        """
    )
with col4:
    st.subheader("4) Run backtests")
    st.markdown(
        """
- Select ticker/date range/transaction costs.
- Compare strategy outputs and review trades.
- Treat backtests as decision support, not guaranteed outcome.
        """
    )

with st.expander("💡 Tips for better results / 使用建议", expanded=True):
    st.markdown(
        """
- Use a broad history window (>= 1 year) for more stable metrics.
- Always include realistic cost/slippage assumptions.
- Start with one ticker, then scale to a portfolio.
- Keep alert thresholds explicit and versioned.
        """
    )

with st.expander("📘 What each page does / 页面用途说明", expanded=False):
    st.markdown(
        f"""
- **{t('data_management')}**: symbol discovery, watchlist management, refresh operations.
- **{t('data_showcase')}**: profile, quality checks, derived series, export.
- **{t('monitoring')}**: rule-based alerts, active events, history and acknowledgement.
- **{t('strategies')}**: parameterized strategy simulation and trade inspection.
        """
    )
