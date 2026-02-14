# core/qc.py
from __future__ import annotations

from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np

from core.db import get_conn


def check_missing_data(df: pd.DataFrame, ticker: str) -> dict:
    """
    Check for missing values in a price dataframe.
    Returns a dict with missing value statistics.
    """
    if df.empty:
        return {"ticker": ticker, "all_missing": True, "missing_values": {}}
    
    missing = {}
    for col in ["open", "high", "low", "close", "adj_close", "volume"]:
        if col in df.columns:
            missing[col] = int(df[col].isna().sum())
    
    return {
        "ticker": ticker,
        "all_missing": df.empty,
        "missing_values": missing,
        "total_rows": len(df)
    }


def check_duplicates(df: pd.DataFrame, ticker: str) -> dict:
    """Check for duplicate entries (same date)."""
    if df.empty:
        return {"ticker": ticker, "duplicates": 0}
    
    duplicates = df.duplicated(subset=["date"], keep=False).sum()
    return {
        "ticker": ticker,
        "duplicates": int(duplicates),
        "duplicate_dates": df[df.duplicated(subset=["date"], keep=False)]["date"].unique().tolist() if duplicates > 0 else []
    }


def check_outliers(df: pd.DataFrame, ticker: str, zscore_threshold: float = 3.0) -> dict:
    """
    Check for outliers using z-score method on close prices.
    """
    if df.empty or "close" not in df.columns:
        return {"ticker": ticker, "outliers": 0, "outlier_dates": []}
    
    close_prices = df["close"].dropna()
    if len(close_prices) < 2:
        return {"ticker": ticker, "outliers": 0, "outlier_dates": []}
    
    mean = close_prices.mean()
    std = close_prices.std()
    
    if std == 0:
        return {"ticker": ticker, "outliers": 0, "outlier_dates": []}
    
    z_scores = np.abs((close_prices - mean) / std)
    outlier_mask = z_scores > zscore_threshold
    
    outlier_data = df[outlier_mask]
    
    return {
        "ticker": ticker,
        "outliers": int(outlier_mask.sum()),
        "outlier_dates": outlier_data["date"].astype(str).tolist() if len(outlier_data) > 0 else []
    }


def check_staleness(df: pd.DataFrame, ticker: str, as_of_date: date | None = None) -> dict:
    """
    Check how old the latest data is.
    """
    if df.empty or "date" not in df.columns:
        return {"ticker": ticker, "staleness_days": None, "last_date": None}
    
    if as_of_date is None:
        as_of_date = datetime.now().date()
    
    last_date = pd.to_datetime(df["date"]).dt.date.max()
    
    if last_date is None:
        return {"ticker": ticker, "staleness_days": None, "last_date": None}
    
    staleness = (as_of_date - last_date).days
    
    return {
        "ticker": ticker,
        "staleness_days": staleness,
        "last_date": last_date.isoformat() if last_date else None
    }


def check_business_day_gaps(df: pd.DataFrame, ticker: str) -> dict:
    """
    Check for unexpected gaps in business days.
    """
    if df.empty or "date" not in df.columns:
        return {"ticker": ticker, "missing_bdays": 0, "gap_info": []}
    
    dates = pd.to_datetime(df["date"]).sort_values()
    
    if len(dates) < 2:
        return {"ticker": ticker, "missing_bdays": 0, "gap_info": []}
    
    min_date = dates.min()
    max_date = dates.max()
    
    expected_bdays = pd.bdate_range(min_date.date(), max_date.date())
    actual_dates = set(dates.dt.date)
    expected_dates = set(expected_bdays.date)
    
    missing_dates = expected_dates - actual_dates
    
    return {
        "ticker": ticker,
        "missing_bdays": len(missing_dates),
        "gap_info": sorted([d.isoformat() for d in missing_dates])[:10]  # Show first 10
    }


def run_qc_report(df: pd.DataFrame, ticker: str) -> dict:
    """
    Run comprehensive QC checks on a price dataframe.
    Returns a dict with all QC results.
    """
    report = {
        "ticker": ticker,
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    report["checks"]["missing"] = check_missing_data(df, ticker)
    report["checks"]["duplicates"] = check_duplicates(df, ticker)
    report["checks"]["outliers"] = check_outliers(df, ticker)
    report["checks"]["staleness"] = check_staleness(df, ticker)
    report["checks"]["business_days"] = check_business_day_gaps(df, ticker)
    
    # Overall status
    has_issues = (
        report["checks"]["missing"]["all_missing"] or
        report["checks"]["duplicates"]["duplicates"] > 0 or
        report["checks"]["outliers"]["outliers"] > 0 or
        report["checks"]["business_days"]["missing_bdays"] > 10
    )
    
    report["status"] = "FAILED" if has_issues else "PASSED"
    
    return report


def summarize_qc_reports(reports: list[dict]) -> pd.DataFrame:
    """
    Convert QC reports to a summary dataframe.
    """
    rows = []
    for report in reports:
        ticker = report["ticker"]
        checks = report["checks"]
        
        row = {
            "ticker": ticker,
            "status": report["status"],
            "missing_values": sum(checks["missing"]["missing_values"].values()),
            "duplicates": checks["duplicates"]["duplicates"],
            "outliers": checks["outliers"]["outliers"],
            "staleness_days": checks["staleness"]["staleness_days"],
            "missing_bdays": checks["business_days"]["missing_bdays"]
        }
        rows.append(row)
    
    return pd.DataFrame(rows) if rows else pd.DataFrame()
