"""Utilities to generate performance reports from backtest results."""
from __future__ import annotations

import pandas as pd
from typing import Dict, Any


def save_backtest_report(result: Dict[str, Any], out_prefix: str = "backtest_report") -> Dict[str, str]:
    """Save equity curve and trades to CSV files and return paths."""
    paths = {}
    if "equity_curve" in result:
        eq = result["equity_curve"]
        eq_path = f"{out_prefix}_equity.csv"
        eq.to_csv(eq_path, index=False)
        paths["equity_curve"] = eq_path
    if "trades" in result:
        trades = result["trades"]
        # convert dataclass Trade objects to dicts if needed
        try:
            trades_df = pd.DataFrame([t.__dict__ for t in trades])
        except Exception:
            trades_df = pd.DataFrame(trades)
        trades_path = f"{out_prefix}_trades.csv"
        trades_df.to_csv(trades_path, index=False)
        paths["trades"] = trades_path
    if "metrics" in result:
        metrics = result["metrics"]
        metrics_path = f"{out_prefix}_metrics.json"
        pd.Series(metrics).to_json(metrics_path)
        paths["metrics"] = metrics_path
    return paths


def summary_dataframe(metrics: Dict[str, Any]) -> pd.DataFrame:
    """Return a single-row DataFrame summarizing metrics."""
    return pd.DataFrame([metrics])
