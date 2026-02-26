"""Automated strategy discovery and ranking utilities.

This module is designed for trader-style workflows where parameter search,
backtesting, and candidate ranking should be mostly automated.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any

import numpy as np
import pandas as pd

from core.backtest import SimpleBacktester
from core.strategy_examples import (
    bollinger_reversion_signals,
    breakout_signals,
    rsi_mean_reversion_signals,
    sma_crossover_signals,
)


@dataclass
class StrategyCandidate:
    strategy_name: str
    params: dict[str, Any]
    score: float
    metrics: dict[str, float]


def detect_hardware_acceleration() -> dict[str, bool]:
    """Best-effort runtime acceleration capability detection."""
    capabilities = {
        "numba": False,
        "cupy": False,
    }

    try:
        import numba  # noqa: F401

        capabilities["numba"] = True
    except Exception:
        pass

    try:
        import cupy  # noqa: F401

        capabilities["cupy"] = True
    except Exception:
        pass

    return capabilities


def _score_metrics(metrics: dict[str, float]) -> float:
    """Risk-adjusted objective for ranking candidates.

    Higher is better.
    """
    total_return = float(metrics.get("total_return_pct", 0.0))
    sharpe = float(metrics.get("sharpe_ratio", 0.0))
    max_drawdown = abs(float(metrics.get("max_drawdown_pct", 0.0)))
    win_rate = float(metrics.get("win_rate", 0.0))

    return (
        (0.45 * total_return)
        + (0.35 * sharpe * 10.0)
        + (0.20 * (win_rate / 100.0) * 10.0)
        - (0.25 * max_drawdown)
    )


def _sma_param_grid() -> list[dict[str, Any]]:
    shorts = [10, 20, 30]
    longs = [50, 100, 150]
    out = []
    for short, long in product(shorts, longs):
        if short < long:
            out.append({"short": short, "long": long})
    return out


def _rsi_param_grid() -> list[dict[str, Any]]:
    windows = [10, 14, 20]
    lowers = [25, 30, 35]
    uppers = [65, 70, 75]
    out = []
    for window, lower, upper in product(windows, lowers, uppers):
        if lower < upper:
            out.append({"window": window, "lower": lower, "upper": upper})
    return out




def _boll_param_grid() -> list[dict[str, Any]]:
    windows = [15, 20, 30]
    stds = [1.5, 2.0, 2.5]
    return [{"window": w, "num_std": s} for w, s in product(windows, stds)]


def _breakout_param_grid() -> list[dict[str, Any]]:
    return [{"window": w} for w in [10, 20, 40, 60]]
def _build_signals(strategy_name: str, prices: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    if strategy_name == "sma_crossover":
        return sma_crossover_signals(prices, short=int(params["short"]), long=int(params["long"]))
    if strategy_name == "rsi_mean_reversion":
        return rsi_mean_reversion_signals(
            prices,
            window=int(params["window"]),
            lower=int(params["lower"]),
            upper=int(params["upper"]),
        )
    if strategy_name == "bollinger_reversion":
        return bollinger_reversion_signals(prices, window=int(params["window"]), num_std=float(params["num_std"]))
    if strategy_name == "breakout":
        return breakout_signals(prices, window=int(params["window"]))
    raise ValueError(f"Unsupported strategy name: {strategy_name}")


def run_auto_strategy_search(
    prices: pd.DataFrame,
    strategy_names: list[str] | None = None,
    initial_capital: float = 100000.0,
    position_size_pct: float = 0.9,
    cost_per_trade: float = 0.001,
    slippage: float = 0.0,
    fixed_fee: float = 0.0,
    top_k: int = 10,
) -> pd.DataFrame:
    """Run parameter search across multiple strategy families and rank candidates."""
    if prices is None or prices.empty:
        return pd.DataFrame()

    strategy_names = strategy_names or ["sma_crossover", "rsi_mean_reversion", "bollinger_reversion", "breakout"]

    grids: dict[str, list[dict[str, Any]]] = {}
    if "sma_crossover" in strategy_names:
        grids["sma_crossover"] = _sma_param_grid()
    if "rsi_mean_reversion" in strategy_names:
        grids["rsi_mean_reversion"] = _rsi_param_grid()
    if "bollinger_reversion" in strategy_names:
        grids["bollinger_reversion"] = _boll_param_grid()
    if "breakout" in strategy_names:
        grids["breakout"] = _breakout_param_grid()

    candidates: list[StrategyCandidate] = []

    for strategy_name, params_list in grids.items():
        for params in params_list:
            signals = _build_signals(strategy_name, prices, params)
            bt = SimpleBacktester(prices_df=prices, signals_df=signals, capital=float(initial_capital))
            result = bt.run(
                position_size_pct=float(position_size_pct),
                cost_per_trade=float(cost_per_trade),
                slippage=float(slippage),
                fixed_fee=float(fixed_fee),
            )

            metrics = result.get("metrics") or {}
            score = _score_metrics(metrics)
            candidates.append(
                StrategyCandidate(
                    strategy_name=strategy_name,
                    params=params,
                    score=float(score),
                    metrics={k: float(v) for k, v in metrics.items()},
                )
            )

    if not candidates:
        return pd.DataFrame()

    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)[: max(1, int(top_k))]

    rows = []
    for i, c in enumerate(ranked, start=1):
        row = {
            "rank": i,
            "strategy_name": c.strategy_name,
            "params": c.params,
            "score": c.score,
        }
        row.update(c.metrics)
        rows.append(row)

    out = pd.DataFrame(rows)
    numeric_cols = [
        "score",
        "total_return_pct",
        "max_drawdown_pct",
        "num_trades",
        "win_rate",
        "avg_win",
        "avg_loss",
        "profit_factor",
        "sharpe_ratio",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    return out


def rolling_out_of_sample_score(scores: pd.Series, window: int = 20) -> float:
    """A simple stability score to prefer consistent strategies over lucky spikes."""
    if scores is None or scores.empty:
        return 0.0

    s = pd.Series(scores).dropna()
    if s.empty:
        return 0.0

    rolling_mean = s.rolling(window=min(window, len(s)), min_periods=1).mean()
    rolling_std = s.rolling(window=min(window, len(s)), min_periods=1).std().replace(0, np.nan)
    stability = (rolling_mean / rolling_std).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return float(stability.iloc[-1])
