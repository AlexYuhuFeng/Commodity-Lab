# core/db.py
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import duckdb
import pandas as pd


ALLOWED_PRICE_FIELDS = {
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
}


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

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS alert_rules (
            rule_id         VARCHAR PRIMARY KEY,
            rule_name       VARCHAR NOT NULL,
            rule_type       VARCHAR NOT NULL,
            ticker          VARCHAR,
            condition_expr  VARCHAR,
            threshold       DOUBLE,
            severity        VARCHAR DEFAULT 'medium',
            enabled         BOOLEAN DEFAULT TRUE,
            notes           VARCHAR,
            created_at      TIMESTAMPTZ,
            updated_at      TIMESTAMPTZ
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS alert_events (
            event_id        VARCHAR PRIMARY KEY,
            rule_id         VARCHAR,
            ticker          VARCHAR,
            severity        VARCHAR,
            message         VARCHAR,
            value           DOUBLE,
            triggered_at    TIMESTAMPTZ,
            acknowledged    BOOLEAN DEFAULT FALSE,
            acknowledged_at TIMESTAMPTZ,
            notes           VARCHAR,
            created_at      TIMESTAMPTZ
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS notification_config (
            config_id       VARCHAR PRIMARY KEY,
            channel_type    VARCHAR NOT NULL,
            channel_name    VARCHAR,
            config_json     VARCHAR,
            is_enabled      BOOLEAN DEFAULT TRUE,
            test_status     VARCHAR,
            last_test_at    TIMESTAMPTZ,
            created_at      TIMESTAMPTZ,
            updated_at      TIMESTAMPTZ
        );
        """
    )



    con.execute(
        """
        CREATE TABLE IF NOT EXISTS strategy_runs (
            run_id          VARCHAR PRIMARY KEY,
            ticker          VARCHAR NOT NULL,
            strategy_name   VARCHAR NOT NULL,
            params_json     VARCHAR,
            score           DOUBLE,
            total_return_pct DOUBLE,
            max_drawdown_pct DOUBLE,
            sharpe_ratio    DOUBLE,
            win_rate        DOUBLE,
            created_at      TIMESTAMPTZ
        );
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS strategy_profiles (
            profile_id       VARCHAR PRIMARY KEY,
            profile_name     VARCHAR NOT NULL,
            strategy_name    VARCHAR NOT NULL,
            ticker           VARCHAR,
            params_json      VARCHAR,
            risk_policy      VARCHAR,
            risk_params_json VARCHAR,
            notes            VARCHAR,
            created_at       TIMESTAMPTZ,
            updated_at       TIMESTAMPTZ
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS scheduler_settings (
            setting_id      VARCHAR PRIMARY KEY,
            is_enabled      BOOLEAN DEFAULT FALSE,
            check_interval  INTEGER DEFAULT 300,
            last_check_at   TIMESTAMPTZ,
            check_count     INTEGER DEFAULT 0,
            error_count     INTEGER DEFAULT 0,
            created_at      TIMESTAMPTZ,
            updated_at      TIMESTAMPTZ
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
    tickers = [str(t).strip() for t in tickers if str(t).strip()]
    if not tickers:
        return

    if delete_prices:
        con.execute(
            "DELETE FROM prices_daily WHERE ticker IN (SELECT * FROM UNNEST(?))",
            [tickers],
        )

    # remove derived data and transform links to avoid ghost options
    con.execute(
        "DELETE FROM derived_daily WHERE derived_ticker IN (SELECT * FROM UNNEST(?))",
        [tickers],
    )
    con.execute(
        "DELETE FROM transforms WHERE derived_ticker IN (SELECT * FROM UNNEST(?)) OR base_ticker IN (SELECT * FROM UNNEST(?)) OR fx_ticker IN (SELECT * FROM UNNEST(?))",
        [tickers, tickers, tickers],
    )

    con.execute("DELETE FROM refresh_log WHERE ticker IN (SELECT * FROM UNNEST(?))", [tickers])
    con.execute("DELETE FROM strategy_profiles WHERE ticker IN (SELECT * FROM UNNEST(?))", [tickers])
    con.execute("DELETE FROM strategy_runs WHERE ticker IN (SELECT * FROM UNNEST(?))", [tickers])
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

    if field not in ALLOWED_PRICE_FIELDS:
        raise ValueError(
            f"Unsupported field '{field}'. Allowed values: {sorted(ALLOWED_PRICE_FIELDS)}"
        )

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


# ---------- Alert Rules ----------
def upsert_alert_rule(con: duckdb.DuckDBPyConnection, row: dict) -> None:
    """
    Insert or update an alert rule.
    
    Expected keys in row:
      rule_id, rule_name, rule_type, ticker(opt), condition_expr(opt), threshold(opt),
      severity(opt, default='medium'), enabled(opt, default=True), notes(opt)
    """
    now = utc_now()
    rule_id = (row.get("rule_id") or "").strip()
    if not rule_id:
        raise ValueError("rule_id is required")
    
    rule_name = (row.get("rule_name") or "").strip()
    if not rule_name:
        raise ValueError("rule_name is required")
    
    rule_type = (row.get("rule_type") or "").strip().lower()
    if not rule_type:
        raise ValueError("rule_type is required")
    
    ticker = (row.get("ticker") or "").strip() or None
    condition_expr = (row.get("condition_expr") or "").strip() or None
    threshold = row.get("threshold")
    if threshold is not None:
        try:
            threshold = float(threshold)
        except (ValueError, TypeError):
            threshold = None
    
    severity = (row.get("severity") or "medium").strip().lower()
    if severity not in ("low", "medium", "high", "critical"):
        severity = "medium"
    
    enabled = bool(row.get("enabled") if row.get("enabled") is not None else True)
    notes = (row.get("notes") or "").strip()
    
    con.execute(
        """
        INSERT INTO alert_rules
          (rule_id, rule_name, rule_type, ticker, condition_expr, threshold, severity, enabled, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (rule_id) DO UPDATE SET
          rule_name = excluded.rule_name,
          rule_type = excluded.rule_type,
          ticker = excluded.ticker,
          condition_expr = excluded.condition_expr,
          threshold = excluded.threshold,
          severity = excluded.severity,
          enabled = excluded.enabled,
          notes = excluded.notes,
          updated_at = excluded.updated_at
        """,
        [
            rule_id,
            rule_name,
            rule_type,
            ticker,
            condition_expr,
            threshold,
            severity,
            enabled,
            notes,
            now,
            now,
        ],
    )


def list_alert_rules(con: duckdb.DuckDBPyConnection, enabled_only: bool = False) -> pd.DataFrame:
    q = "SELECT * FROM alert_rules"
    if enabled_only:
        q += " WHERE enabled = TRUE"
    q += " ORDER BY updated_at DESC"
    return con.execute(q).df()


def get_alert_rule(con: duckdb.DuckDBPyConnection, rule_id: str) -> dict | None:
    row = con.execute(
        "SELECT * FROM alert_rules WHERE rule_id = ?",
        [rule_id],
    ).fetchone()
    if not row:
        return None
    cols = [d[0] for d in con.description]
    return dict(zip(cols, row))


def delete_alert_rule(con: duckdb.DuckDBPyConnection, rule_id: str) -> None:
    con.execute("DELETE FROM alert_rules WHERE rule_id = ?", [rule_id])


# ---------- Alert Events ----------
def create_alert_event(con: duckdb.DuckDBPyConnection, row: dict) -> str:
    """
    Create an alert event.
    
    Expected keys:
      event_id, rule_id, ticker, severity, message, value(opt), notes(opt)
    
    Returns event_id
    """
    now = utc_now()
    event_id = (row.get("event_id") or "").strip()
    if not event_id:
        # Generate event_id if not provided
        import uuid
        event_id = str(uuid.uuid4())
    
    rule_id = (row.get("rule_id") or "").strip()
    ticker = (row.get("ticker") or "").strip()
    severity = (row.get("severity") or "medium").strip().lower()
    if severity not in ("low", "medium", "high", "critical"):
        severity = "medium"
    
    message = (row.get("message") or "").strip()
    value = row.get("value")
    if value is not None:
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = None
    
    notes = (row.get("notes") or "").strip()
    
    con.execute(
        """
        INSERT INTO alert_events
          (event_id, rule_id, ticker, severity, message, value, triggered_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            event_id,
            rule_id if rule_id else None,
            ticker if ticker else None,
            severity,
            message,
            value,
            now,
            now,
        ],
    )
    
    return event_id


def list_alert_events(con: duckdb.DuckDBPyConnection, limit: int = 100, acknowledged: bool | None = None) -> pd.DataFrame:
    where = ""
    params = []
    if acknowledged is not None:
        where = "WHERE acknowledged = ?"
        params.append(acknowledged)
    
    sql = f"""
        SELECT * FROM alert_events
        {where}
        ORDER BY triggered_at DESC
        LIMIT ?
    """
    params.append(limit)
    
    df = con.execute(sql, params).df()
    if not df.empty:
        df["triggered_at"] = pd.to_datetime(df["triggered_at"])
        df["created_at"] = pd.to_datetime(df["created_at"])
        if "acknowledged_at" in df.columns:
            df["acknowledged_at"] = pd.to_datetime(df["acknowledged_at"])
    
    return df


def acknowledge_alert_event(con: duckdb.DuckDBPyConnection, event_id: str, notes: str = "") -> None:
    now = utc_now()
    con.execute(
        """
        UPDATE alert_events
        SET acknowledged = TRUE, acknowledged_at = ?, notes = ?
        WHERE event_id = ?
        """,
        [now, notes.strip(), event_id],
    )


# ---------- Strategy Runs ----------
def insert_strategy_run(con: duckdb.DuckDBPyConnection, row: dict) -> str:
    """Insert or update one strategy run record and return run_id."""
    import json
    import uuid

    now = utc_now()
    run_id = (row.get("run_id") or "").strip() or f"sr_{uuid.uuid4().hex[:12]}"
    ticker = (row.get("ticker") or "").strip()
    strategy_name = (row.get("strategy_name") or "").strip()

    params_json = row.get("params_json")
    if params_json is None and row.get("params") is not None:
        params_json = json.dumps(row.get("params"), ensure_ascii=False, sort_keys=True)

    con.execute(
        """
        INSERT INTO strategy_runs
          (run_id, ticker, strategy_name, params_json, score, total_return_pct,
           max_drawdown_pct, sharpe_ratio, win_rate, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (run_id) DO UPDATE SET
          ticker = excluded.ticker,
          strategy_name = excluded.strategy_name,
          params_json = excluded.params_json,
          score = excluded.score,
          total_return_pct = excluded.total_return_pct,
          max_drawdown_pct = excluded.max_drawdown_pct,
          sharpe_ratio = excluded.sharpe_ratio,
          win_rate = excluded.win_rate,
          created_at = excluded.created_at
        """,
        [
            run_id,
            ticker,
            strategy_name,
            params_json,
            row.get("score"),
            row.get("total_return_pct"),
            row.get("max_drawdown_pct"),
            row.get("sharpe_ratio"),
            row.get("win_rate"),
            row.get("created_at") or now,
        ],
    )
    return run_id


def list_strategy_runs(
    con: duckdb.DuckDBPyConnection,
    ticker: str | None = None,
    strategy_name: str | None = None,
    limit: int = 200,
) -> pd.DataFrame:
    """List strategy run history with optional filters."""
    where = []
    params: list = []

    if ticker:
        where.append("ticker = ?")
        params.append(ticker.strip())
    if strategy_name:
        where.append("strategy_name = ?")
        params.append(strategy_name.strip())

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    params.append(max(1, int(limit)))

    df = con.execute(
        f"""
        SELECT * FROM strategy_runs
        {where_sql}
        ORDER BY created_at DESC, run_id DESC
        LIMIT ?
        """,
        params,
    ).df()

    if not df.empty and "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])

    return df


# ---------- Notification Config ----------
def upsert_notification_config(con: duckdb.DuckDBPyConnection, channel_type: str, 
                               config_json: str, channel_name: str = "", is_enabled: bool = True) -> str:
    """添加或更新通知配置"""
    import uuid
    config_id = f"nc_{channel_type}_{uuid.uuid4().hex[:8]}"
    now = utc_now()
    
    con.execute(
        """
        INSERT INTO notification_config 
          (config_id, channel_type, channel_name, config_json, is_enabled, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (config_id) DO UPDATE SET 
          config_json = excluded.config_json,
          is_enabled = excluded.is_enabled,
          updated_at = excluded.updated_at
        """,
        [config_id, channel_type, channel_name, config_json, is_enabled, now, now]
    )
    return config_id


def list_notification_configs(con: duckdb.DuckDBPyConnection, enabled_only: bool = False) -> pd.DataFrame:
    """获取所有通知配置"""
    where = ""
    if enabled_only:
        where = "WHERE is_enabled = TRUE"
    
    df = con.execute(
        f"""
        SELECT * FROM notification_config {where}
        ORDER BY updated_at DESC
        """
    ).fetch_df()
    
    if not df.empty and "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["updated_at"] = pd.to_datetime(df["updated_at"])
        if "last_test_at" in df.columns:
            df["last_test_at"] = pd.to_datetime(df["last_test_at"])
    
    return df


def delete_notification_config(con: duckdb.DuckDBPyConnection, config_id: str) -> None:
    """删除通知配置"""
    con.execute("DELETE FROM notification_config WHERE config_id = ?", [config_id])


def update_notification_test_status(con: duckdb.DuckDBPyConnection, config_id: str, 
                                    status: str, timestamp: datetime | None = None) -> None:
    """更新通知配置的测试状态"""
    if timestamp is None:
        timestamp = utc_now()
    
    con.execute(
        """
        UPDATE notification_config
        SET test_status = ?, last_test_at = ?
        WHERE config_id = ?
        """,
        [status, timestamp, config_id]
    )


# ---------- Scheduler Settings ----------
def upsert_scheduler_settings(con: duckdb.DuckDBPyConnection, is_enabled: bool = False,
                             check_interval: int = 300) -> None:
    """更新或创建调度器设置"""
    now = utc_now()
    
    # 检查是否存在设置
    existing = con.execute("SELECT setting_id FROM scheduler_settings LIMIT 1").fetchall()
    
    if existing:
        con.execute(
            """
            UPDATE scheduler_settings
            SET is_enabled = ?, check_interval = ?, updated_at = ?
            WHERE setting_id = ?
            """,
            [is_enabled, check_interval, now, existing[0][0]]
        )
    else:
        con.execute(
            """
            INSERT INTO scheduler_settings 
              (setting_id, is_enabled, check_interval, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            ["scheduler_main", is_enabled, check_interval, now, now]
        )


def get_scheduler_settings(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """获取调度器设置"""
    df = con.execute("SELECT * FROM scheduler_settings LIMIT 1").fetch_df()
    
    if not df.empty:
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"])
        if "updated_at" in df.columns:
            df["updated_at"] = pd.to_datetime(df["updated_at"])
        if "last_check_at" in df.columns:
            df["last_check_at"] = pd.to_datetime(df["last_check_at"])
    
    return df


def update_scheduler_stats(con: duckdb.DuckDBPyConnection, check_count: int = None,
                          error_count: int = None, last_check_at: datetime | None = None) -> None:
    """更新调度器统计信息"""
    updates = []
    params = []
    
    if check_count is not None:
        updates.append("check_count = ?")
        params.append(check_count)
    if error_count is not None:
        updates.append("error_count = ?")
        params.append(error_count)
    if last_check_at is not None:
        updates.append("last_check_at = ?")
        params.append(last_check_at)
    
    if updates:
        updates.append("updated_at = ?")
        params.append(utc_now())
        
        query = f"UPDATE scheduler_settings SET {', '.join(updates)}"
        con.execute(query, params)


# Convenience helpers for other modules that expect simple helpers
def get_db_connection(db_path: Path | None = None) -> duckdb.DuckDBPyConnection:
    """Return a duckdb connection using the default project DB path when not provided."""
    if db_path is None:
        project_root = Path(__file__).resolve().parents[1]
        db_path = default_db_path(project_root)
    return get_conn(db_path)


def get_db(db_path: Path | None = None) -> duckdb.DuckDBPyConnection:
    """Alias for get_db_connection (keeps older import names working)."""
    return get_db_connection(db_path)


# ---------- Strategy Profiles ----------
def upsert_strategy_profile(con: duckdb.DuckDBPyConnection, row: dict) -> None:
    now = utc_now()
    pid = (row.get("profile_id") or "").strip()
    if not pid:
        raise ValueError("profile_id is required")
    pname = (row.get("profile_name") or "").strip()
    if not pname:
        raise ValueError("profile_name is required")
    sname = (row.get("strategy_name") or "").strip()
    if not sname:
        raise ValueError("strategy_name is required")

    con.execute(
        """
        INSERT INTO strategy_profiles
          (profile_id, profile_name, strategy_name, ticker, params_json, risk_policy, risk_params_json, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (profile_id) DO UPDATE SET
          profile_name = excluded.profile_name,
          strategy_name = excluded.strategy_name,
          ticker = excluded.ticker,
          params_json = excluded.params_json,
          risk_policy = excluded.risk_policy,
          risk_params_json = excluded.risk_params_json,
          notes = excluded.notes,
          updated_at = excluded.updated_at
        """,
        [
            pid,
            pname,
            sname,
            (row.get("ticker") or "").strip() or None,
            row.get("params_json"),
            row.get("risk_policy"),
            row.get("risk_params_json"),
            row.get("notes") or "",
            now,
            now,
        ],
    )


def list_strategy_profiles(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute("SELECT * FROM strategy_profiles ORDER BY updated_at DESC").df()


def delete_strategy_profile(con: duckdb.DuckDBPyConnection, profile_id: str) -> None:
    con.execute("DELETE FROM strategy_profiles WHERE profile_id = ?", [profile_id])
