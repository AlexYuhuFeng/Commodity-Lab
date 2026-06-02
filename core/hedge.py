from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import date
from typing import Literal

import pandas as pd


HEDGE_TYPES = ["short_hedge", "long_hedge", "calendar_spread", "basis_hedge"]
ORDER_SIDES = ["buy", "sell"]


@dataclass
class VirtualOrder:
    order_id: str
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float
    open_date: date
    close_date: date
    open_price: float
    close_price: float | None = None
    hedge_type: str = "short_hedge"
    note: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _find_price_for_date(prices: pd.DataFrame, target_date: date) -> float | None:
    match = prices.loc[prices["date"] == pd.to_datetime(target_date)].copy()
    if match.empty:
        return None
    return float(match.iloc[0]["close"])


def simulate_virtual_order(prices: pd.DataFrame, order: VirtualOrder) -> dict[str, object]:
    open_price = order.open_price if order.open_price is not None else _find_price_for_date(prices, order.open_date)
    if open_price is None:
        raise ValueError(f"Open price unavailable for {order.ticker} on {order.open_date}")

    close_price = order.close_price if order.close_price is not None else _find_price_for_date(prices, order.close_date)
    if close_price is None:
        raise ValueError(f"Close price unavailable for {order.ticker} on {order.close_date}")

    if order.side == "buy":
        pnl = (close_price - open_price) * order.quantity
    else:
        pnl = (open_price - close_price) * order.quantity

    notional = open_price * order.quantity
    profit_pct = (pnl / notional * 100) if notional else 0.0
    duration_days = (order.close_date - order.open_date).days

    return {
        "order_id": order.order_id,
        "ticker": order.ticker,
        "hedge_type": order.hedge_type,
        "side": order.side,
        "quantity": order.quantity,
        "open_date": order.open_date,
        "close_date": order.close_date,
        "open_price": open_price,
        "close_price": close_price,
        "duration_days": duration_days,
        "notional": notional,
        "pnl": pnl,
        "profit_pct": profit_pct,
        "note": order.note,
    }


def score_hedge_result(result: dict[str, object]) -> float:
    """Score a single virtual hedge order using profit and risk sensitivity."""
    pnl = float(result.get("pnl", 0.0))
    profit_pct = float(result.get("profit_pct", 0.0))
    notional = float(result.get("notional", 0.0))
    risk_adjustment = min(max(abs(profit_pct) * 0.8, 0.0), 50.0)
    score = 50.0 + min(max(profit_pct, -50.0), 50.0) * 0.5 + min(max(pnl / max(notional, 1.0) * 100.0, -50.0), 50.0) * 0.3
    score -= risk_adjustment * 0.2
    return float(max(0.0, min(100.0, score)))


def score_portfolio(results: pd.DataFrame) -> float:
    """Aggregate score for a set of hedge orders in the current portfolio."""
    if results.empty:
        return 0.0

    individual = results.apply(score_hedge_result, axis=1)
    consistency = 100.0 - min(max(results["pnl"].std() / max(abs(results["pnl"].mean() or 1.0), 1.0) * 100.0, 0.0), 50.0)
    score = float(min(100.0, max(0.0, individual.mean() * 0.7 + consistency * 0.3)))
    return score


def simulate_portfolio(prices: pd.DataFrame, orders: list[VirtualOrder]) -> pd.DataFrame:
    rows = []
    for order in orders:
        rows.append(simulate_virtual_order(prices, order))
    df = pd.DataFrame(rows)
    if not df.empty:
        df["score"] = df.apply(score_hedge_result, axis=1)
    return df


def summarize_hedge_performance(orders: list[VirtualOrder], results: pd.DataFrame) -> dict[str, float]:
    if results.empty:
        return {
            "total_notional": 0.0,
            "total_pnl": 0.0,
            "average_profit_pct": 0.0,
            "order_count": 0,
        }

    return {
        "total_notional": float(results["notional"].sum()),
        "total_pnl": float(results["pnl"].sum()),
        "average_profit_pct": float(results["profit_pct"].mean()),
        "order_count": len(results),
    }
