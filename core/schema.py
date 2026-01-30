from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SeriesSpec:
    """一条时间序列的规格定义（通用）"""
    name: str                 # e.g. "TTF", "HH", "JKM", "EURUSD"
    path: str                 # data/raw/xxx.csv
    date_col: str = "date"    # CSV里的日期列名
    value_col: str = "price"  # CSV里的价格列名
    unit: Optional[str] = None
    currency: Optional[str] = None
    tz: str = "UTC"
