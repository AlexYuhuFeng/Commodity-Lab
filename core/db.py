# core/db.py
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import duckdb
import pandas as pd


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _canon_currency(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    s = str(x).strip()
    return s.upper()


def _canon_unit(x) -> str:
    """
    Canonicalize common units so user can type 'Mwh' and we store 'MWh'.
    Extend this mapping anytime.
    """
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    s = str(x).strip()
    if not s:
        return ""

    key = s.casefold().replace(" ", "")
    mapping = {
        "mwh": "MWh",
        "mmbtu": "MMBtu",
        "usdpereur": "USDperEUR",
        "bbl": "bbl",
        "mt": "mt",
        "ton": "mt",        # optional alias
        "tons": "mt",       # optional alias
    }
    return mapping.get(key, s)  # unknown units kept as-is (but trimmed)


def default_db_path(project_root: Path) -> Path:
    return project_root / "data" / "commodity_lab.duckdb"


def get_conn(db_path: Path) -> duckdb.DuckDBPyConnection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def init_db(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS instruments (
            ticker      VARCHAR PRIMARY KEY,
            name        VARCHAR,
            quote_type  VARCHAR,
            exchange    VARCHAR,
            currency    VARCHAR,
            unit        VARCHAR,
            category    VARCHAR,
            is_watched  BOOLEAN DEFAULT FALSE,
            source      VARCHAR DEFAULT 'yfinance',
            created_at  TIMESTAMPTZ,
            updated_at  TIMESTAMPTZ
        );
        """
    )

    # Migration safety
    try:
        con.execute("ALTER TABLE instruments ADD COLUMN IF NOT EXISTS currency VARCHAR;")
    except Exception:
        pass
    try:
        con.execute("ALTER TABLE instruments ADD COLUMN IF NOT EXISTS unit VARCHAR;")
    except Exception:
        pass

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS prices_daily (
            ticker      VARCHAR,
            date        DATE,
            open        DOUBLE,
            high        DOUBLE,
            low         DOUBLE,
            close       DOUBLE,
            adj_close   DOUBLE,
            volume      BIGINT,
            updated_at  TIMESTAMPTZ,
            PRIMARY KEY (ticker, date)
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS refresh_log (
            ticker              VARCHAR PRIMARY KEY,
            last_attempt_at      TIMESTAMPTZ,
            last_success_date    DATE,
            status              VARCHAR,
            message             VARCHAR
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS transforms (
            transform_id     VARCHAR PRIMARY KEY,
            derived_ticker   VARCHAR,
            base_ticker      VARCHAR,
            fx_ticker        VARCHAR,
            fx_op            VARCHAR DEFAULT 'mul',
            target_currency  VARCHAR,
            target_unit      VARCHAR,
            multiplier       DOUBLE DEFAULT 1,
            divider          DOUBLE DEFAULT 1,
            enabled          BOOLEAN DEFAULT TRUE,
            notes            VARCHAR,
            created_at       TIMESTAMPTZ,
            updated_at       TIMESTAMPTZ
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS derived_daily (
            derived_ticker VARCHAR,
            date           DATE,
            value          DOUBLE,
            updated_at     TIMESTAMPTZ,
            PRIMARY KEY (derived_ticker, date)
        );
        """
    )


# ---------- Instruments ----------
def upsert_instruments(con: duckdb.DuckDBPyConnection, rows: pd.DataFrame) -> None:
    """
    rows expected columns:
      ticker, name, quote_type, exchange, currency(optional), unit(optional), category(optional), source(optional)
    """
    if rows is None or rows.empty:
        return

    rows = rows.copy()

    defaults = {
        "name": "",
        "quote_type": "",
        "exchange": "",
        "currency": "",
        "unit": "",
        "category": "",
        "source": "yfinance",
    }
    for col, default in defaults.items():
        if col not in rows.columns:
            rows[col] = default

    if "ticker" not in rows.columns:
        raise ValueError("rows must include 'ticker'")

    # ✅ normalize here
    rows["currency"] = rows["currency"].apply(_canon_currency)
    rows["unit"] = rows["unit"].apply(_canon_unit)

    now = utc_now()
    rows["updated_at"] = now

    con.register("rows_df", rows)

    con.execute(
        """
        INSERT INTO instruments
          (ticker, name, quote_type, exchange, currency, unit, category, source, created_at, updated_at)
        SELECT
          ticker,
          name,
          quote_type,
          exchange,
          currency,
          unit,
          category,
          source,
          ? AS created_at,
          updated_at
        FROM rows_df
        ON CONFLICT (ticker) DO UPDATE SET
          name = excluded.name,
          quote_type = excluded.quote_type,
          exchange = excluded.exchange,
          currency = CASE
            WHEN excluded.currency IS NOT NULL AND excluded.currency <> '' THEN excluded.currency
            ELSE instruments.currency
          END,
          unit = CASE
            WHEN excluded.unit IS NOT NULL AND excluded.unit <> '' THEN excluded.unit
            ELSE instruments.unit
          END,
          category = CASE
            WHEN excluded.category IS NOT NULL AND excluded.category <> '' THEN excluded.category
            ELSE instruments.category
          END,
          source = excluded.source,
          updated_at = excluded.updated_at
        """,
        [now],
    )

    con.unregister("rows_df")


def list_instruments(con: duckdb.DuckDBPyConnection, only_watched: bool = False) -> pd.DataFrame:
    q = "SELECT * FROM instruments"
    if only_watched:
        q += " WHERE is_watched = TRUE"
    q += " ORDER BY updated_at DESC"
    return con.execute(q).df()


def set_watch(con: duckdb.DuckDBPyConnection, tickers: Iterable[str], watched: bool) -> None:
    tickers = list(tickers)
    if not tickers:
        return
    now = utc_now()
    con.execute(
        """
        UPDATE instruments
        SET is_watched = ?, updated_at = ?
        WHERE ticker IN (SELECT * FROM UNNEST(?))
        """,
        [watched, now, tickers],
    )


def delete_instruments(con: duckdb.DuckDBPyConnection, tickers: Iterable[str], delete_prices: bool = False) -> None:
    tickers = list(tickers)
    if not tickers:
        return

    if delete_prices:
        con.execute(
            "DELETE FROM prices_daily WHERE ticker IN (SELECT * FROM UNNEST(?))",
            [tickers],
        )

    con.execute("DELETE FROM refresh_log WHERE ticker IN (SELECT * FROM UNNEST(?))", [tickers])
    con.execute("DELETE FROM instruments WHERE ticker IN (SELECT * FROM UNNEST(?))", [tickers])


def update_instrument_meta(con: duckdb.DuckDBPyConnection, meta: pd.DataFrame) -> None:
    """
    meta required: ticker
    optional: currency, unit, category
    """
    if meta is None or meta.empty:
        return

    now = utc_now()
    m = meta.copy()

    for col in ["currency", "unit", "category"]:
        if col not in m.columns:
            m[col] = None

    # ✅ normalize here (so UI can input Mwh / usd etc.)
    m["currency"] = m["currency"].apply(_canon_currency)
    m["unit"] = m["unit"].apply(_canon_unit)

    con.register("meta_df", m)
    con.execute(
        """
        UPDATE instruments AS i
        SET
          currency = COALESCE(NULLIF(meta_df.currency, ''), i.currency),
          unit     = COALESCE(NULLIF(meta_df.unit, ''), i.unit),
          category = COALESCE(NULLIF(meta_df.category, ''), i.category),
          updated_at = ?
        FROM meta_df
        WHERE i.ticker = meta_df.ticker
        """,
        [now],
    )
    con.unregister("meta_df")


def get_instrument_meta(con: duckdb.DuckDBPyConnection, tickers: list[str]) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame(columns=["ticker", "currency", "unit", "category"])
    return con.execute(
        """
        SELECT ticker, currency, unit, category
        FROM instruments
        WHERE ticker IN (SELECT * FROM UNNEST(?))
        """,
        [tickers],
    ).df()


# ---------- Prices ----------
def get_last_price_date(con: duckdb.DuckDBPyConnection, ticker: str):
    row = con.execute(
        "SELECT MAX(date) AS max_date FROM prices_daily WHERE ticker = ?",
        [ticker],
    ).fetchone()
    return row[0]


def get_min_price_date(con: duckdb.DuckDBPyConnection, ticker: str):
    row = con.execute(
        "SELECT MIN(date) AS min_date FROM prices_daily WHERE ticker = ?",
        [ticker],
    ).fetchone()
    return row[0]


def upsert_prices_daily(con: duckdb.DuckDBPyConnection, ticker: str, df_prices: pd.DataFrame) -> int:
    if df_prices is None or df_prices.empty:
        return 0

    now = utc_now()
    df = df_prices.copy()
    df["ticker"] = ticker
    df["updated_at"] = now

    for c in ["date", "open", "high", "low", "close", "adj_close", "volume"]:
        if c not in df.columns:
            df[c] = pd.NA

    df = df[["ticker", "date", "open", "high", "low", "close", "adj_close", "volume", "updated_at"]]

    con.register("px_df", df)
    con.execute(
        """
        INSERT INTO prices_daily
          (ticker, date, open, high, low, close, adj_close, volume, updated_at)
        SELECT
          ticker, date, open, high, low, close, adj_close, volume, updated_at
        FROM px_df
        ON CONFLICT (ticker, date) DO UPDATE SET
          open = excluded.open,
          high = excluded.high,
          low  = excluded.low,
          close = excluded.close,
          adj_close = excluded.adj_close,
          volume = excluded.volume,
          updated_at = excluded.updated_at
        """
    )
    con.unregister("px_df")
    return int(df.shape[0])


def query_prices_long(con: duckdb.DuckDBPyConnection, tickers: list[str], start=None, end=None, field: str = "close") -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame(columns=["date", "ticker", "value"])

    where = "WHERE ticker IN (SELECT * FROM UNNEST(?))"
    params = [tickers]
    if start is not None:
        where += " AND date >= ?"
        params.append(start)
    if end is not None:
        where += " AND date <= ?"
        params.append(end)

    sql = f"""
        SELECT date, ticker, {field} AS value
        FROM prices_daily
        {where}
        ORDER BY date ASC
    """
    df = con.execute(sql, params).df()
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


# ---------- Derived ----------
def get_last_derived_date(con: duckdb.DuckDBPyConnection, derived_ticker: str):
    row = con.execute(
        "SELECT MAX(date) AS max_date FROM derived_daily WHERE derived_ticker = ?",
        [derived_ticker],
    ).fetchone()
    return row[0]


def upsert_derived_daily(con: duckdb.DuckDBPyConnection, derived_ticker: str, df: pd.DataFrame) -> int:
    if df is None or df.empty:
        return 0
    now = utc_now()
    out = df.copy()
    out["derived_ticker"] = derived_ticker
    out["updated_at"] = now
    out = out[["derived_ticker", "date", "value", "updated_at"]]

    con.register("d_df", out)
    con.execute(
        """
        INSERT INTO derived_daily (derived_ticker, date, value, updated_at)
        SELECT derived_ticker, date, value, updated_at
        FROM d_df
        ON CONFLICT (derived_ticker, date) DO UPDATE SET
          value = excluded.value,
          updated_at = excluded.updated_at
        """
    )
    con.unregister("d_df")
    return int(out.shape[0])


def query_derived_long(con: duckdb.DuckDBPyConnection, derived_tickers: list[str], start=None, end=None) -> pd.DataFrame:
    if not derived_tickers:
        return pd.DataFrame(columns=["date", "ticker", "value"])

    where = "WHERE derived_ticker IN (SELECT * FROM UNNEST(?))"
    params = [derived_tickers]
    if start is not None:
        where += " AND date >= ?"
        params.append(start)
    if end is not None:
        where += " AND date <= ?"
        params.append(end)

    sql = f"""
        SELECT date, derived_ticker AS ticker, value
        FROM derived_daily
        {where}
        ORDER BY date ASC
    """
    df = con.execute(sql, params).df()
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


# ---------- Transforms ----------
def list_transforms(con: duckdb.DuckDBPyConnection, enabled_only: bool = False) -> pd.DataFrame:
    q = "SELECT * FROM transforms"
    if enabled_only:
        q += " WHERE enabled = TRUE"
    q += " ORDER BY updated_at DESC"
    return con.execute(q).df()


def upsert_transform(con: duckdb.DuckDBPyConnection, row: dict) -> None:
    now = utc_now()
    derived = (row.get("derived_ticker") or "").strip()
    if not derived:
        raise ValueError("derived_ticker is required")

    transform_id = (row.get("transform_id") or derived).strip()
    base = (row.get("base_ticker") or "").strip()
    if not base:
        raise ValueError("base_ticker is required")

    fx_ticker = (row.get("fx_ticker") or "").strip()
    fx_op = (row.get("fx_op") or "mul").strip().lower()
    if fx_op not in ("mul", "div"):
        fx_op = "mul"

    target_currency = _canon_currency(row.get("target_currency") or "")
    target_unit = _canon_unit(row.get("target_unit") or "")

    multiplier = float(row.get("multiplier") or 1.0)
    divider = float(row.get("divider") or 1.0)
    enabled = bool(row.get("enabled") if row.get("enabled") is not None else True)
    notes = (row.get("notes") or "").strip()

    con.execute(
        """
        INSERT INTO transforms
          (transform_id, derived_ticker, base_ticker, fx_ticker, fx_op, target_currency, target_unit,
           multiplier, divider, enabled, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (transform_id) DO UPDATE SET
          derived_ticker = excluded.derived_ticker,
          base_ticker = excluded.base_ticker,
          fx_ticker = excluded.fx_ticker,
          fx_op = excluded.fx_op,
          target_currency = excluded.target_currency,
          target_unit = excluded.target_unit,
          multiplier = excluded.multiplier,
          divider = excluded.divider,
          enabled = excluded.enabled,
          notes = excluded.notes,
          updated_at = excluded.updated_at
        """,
        [
            transform_id,
            derived,
            base,
            (fx_ticker if fx_ticker else None),
            fx_op,
            target_currency,
            target_unit,
            multiplier,
            divider,
            enabled,
            notes,
            now,
            now,
        ],
    )


def delete_transform(con: duckdb.DuckDBPyConnection, transform_id: str, delete_derived: bool = False) -> None:
    t = (transform_id or "").strip()
    if not t:
        return

    row = con.execute(
        "SELECT derived_ticker FROM transforms WHERE transform_id = ?",
        [t],
    ).fetchone()
    derived = row[0] if row else None

    con.execute("DELETE FROM transforms WHERE transform_id = ?", [t])

    if delete_derived and derived:
        con.execute("DELETE FROM derived_daily WHERE derived_ticker = ?", [derived])
        con.execute("DELETE FROM refresh_log WHERE ticker = ?", [derived])


# ---------- Refresh log ----------
def log_refresh(con: duckdb.DuckDBPyConnection, ticker: str, status: str, message: str = "", last_success_date=None) -> None:
    now = utc_now()
    con.execute(
        """
        INSERT INTO refresh_log (ticker, last_attempt_at, last_success_date, status, message)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (ticker) DO UPDATE SET
          last_attempt_at = excluded.last_attempt_at,
          last_success_date = excluded.last_success_date,
          status = excluded.status,
          message = excluded.message
        """,
        [ticker, now, last_success_date, status, message[:800]],
    )


def list_refresh_log(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute("SELECT * FROM refresh_log ORDER BY last_attempt_at DESC").df()
