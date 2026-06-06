from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd


AI_GENERATED_SOURCE = "ai_generated_training"


def search_market(query: str, source: str = AI_GENERATED_SOURCE, max_results: int = 25) -> list[dict[str, Any]]:
    """Return no external search results.

    Commodity Lab V1 is intentionally driven by AI-generated training cases and
    no longer connects to market-data providers. The function is retained for
    older internal callers so they fail closed instead of trying a network call.
    """
    _ = (query, source, max_results)
    return []


def fetch_price_history(
    ticker: str,
    source: str = AI_GENERATED_SOURCE,
    start: date | None = None,
    period_if_no_start: str = "max",
    end: date | None = None,
) -> pd.DataFrame:
    """Return an empty frame because V1 does not refresh external prices."""
    _ = (ticker, source, start, period_if_no_start, end)
    return pd.DataFrame(columns=["date", "open", "high", "low", "close"])


def available_sources() -> list[str]:
    return [AI_GENERATED_SOURCE]
