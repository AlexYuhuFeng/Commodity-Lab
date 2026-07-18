"""Entitled S&P Global Commodity Insights market-data adapter.

The adapter normalizes licensed forward assessments into Commodity Lab's
market-evidence contract. It never stores raw provider payloads and explicitly
separates entitled curve data from locally calibrated training history.
"""
from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PLATTS_DEFAULT_BASE_URL = "https://api.ci.spglobal.com"
PLATTS_CURRENT_SYMBOL_PATH = "/market-data/v3/value/current/symbol"
PLATTS_TOKEN_PATH = "/auth/api"


class PlattsError(RuntimeError):
    """Base class for provider errors safe to expose as fallback reasons."""

    code = "platts_error"

    def __init__(self, message: str, *, code: str | None = None, status: int | None = None) -> None:
        super().__init__(message)
        self.code = code or self.code
        self.status = status


class PlattsConfigurationError(PlattsError):
    code = "platts_configuration_error"


class PlattsRequestError(PlattsError):
    code = "platts_request_error"


Transport = Callable[..., dict[str, Any]]


def _config_root() -> Path:
    if os.name == "nt":
        root = os.getenv("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    else:
        root = os.getenv("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(root) / "Commodity Lab"


def _cache_root() -> Path:
    if os.name == "nt":
        root = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    else:
        root = os.getenv("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(root) / "Commodity Lab" / "market-cache"


def _env_int(name: str, default: int, minimum: int) -> int:
    try:
        return max(int(os.getenv(name, str(default)).strip()), minimum)
    except ValueError:
        return default


@dataclass(frozen=True)
class PlattsSettings:
    base_url: str = PLATTS_DEFAULT_BASE_URL
    auth_mode: str = "oauth_password"
    access_token: str = ""
    username: str = ""
    password: str = ""
    symbol_map_path: str = ""
    cache_dir: str = ""
    cache_ttl_seconds: int = 900
    max_stale_seconds: int = 86_400
    timeout_seconds: int = 20

    @property
    def has_credentials(self) -> bool:
        if self.access_token.strip():
            return True
        return bool(self.username.strip() and self.password.strip())

    @property
    def resolved_symbol_map_path(self) -> Path:
        value = self.symbol_map_path.strip()
        return Path(value) if value else _config_root() / "platts-symbol-map.json"

    @property
    def resolved_cache_dir(self) -> Path:
        value = self.cache_dir.strip()
        return Path(value) if value else _cache_root()


def settings_from_env() -> PlattsSettings:
    access_token = os.getenv("COMMODITY_LAB_PLATTS_ACCESS_TOKEN", "").strip()
    auth_mode = os.getenv("COMMODITY_LAB_PLATTS_AUTH_MODE", "").strip().lower()
    if not auth_mode:
        auth_mode = "bearer" if access_token else "oauth_password"
    return PlattsSettings(
        base_url=os.getenv("COMMODITY_LAB_PLATTS_BASE_URL", PLATTS_DEFAULT_BASE_URL).strip().rstrip("/")
        or PLATTS_DEFAULT_BASE_URL,
        auth_mode=auth_mode,
        access_token=access_token,
        username=os.getenv("COMMODITY_LAB_PLATTS_USERNAME", "").strip(),
        password=os.getenv("COMMODITY_LAB_PLATTS_PASSWORD", "").strip(),
        symbol_map_path=os.getenv("COMMODITY_LAB_PLATTS_SYMBOL_MAP", "").strip(),
        cache_dir=os.getenv("COMMODITY_LAB_PLATTS_CACHE_DIR", "").strip(),
        cache_ttl_seconds=_env_int("COMMODITY_LAB_PLATTS_CACHE_TTL_SECONDS", 900, 0),
        max_stale_seconds=_env_int("COMMODITY_LAB_PLATTS_MAX_STALE_SECONDS", 86_400, 0),
        timeout_seconds=_env_int("COMMODITY_LAB_PLATTS_TIMEOUT_SECONDS", 20, 1),
    )


def _default_transport(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    body: dict[str, str] | None = None,
    timeout: int = 20,
) -> dict[str, Any]:
    if params:
        url = f"{url}?{urlencode(params)}"
    request_headers = {"Accept": "application/json", **(headers or {})}
    data: bytes | None = None
    if body is not None:
        if request_headers.get("Content-Type") == "application/x-www-form-urlencoded":
            data = urlencode(body).encode("utf-8")
        else:
            request_headers.setdefault("Content-Type", "application/json")
            data = json.dumps(body).encode("utf-8")
    request = Request(url, data=data, headers=request_headers, method=method.upper())
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        suffix = f" Retry after {retry_after} seconds." if retry_after else ""
        code = "platts_rate_limited" if exc.code == 429 else "platts_http_error"
        raise PlattsRequestError(
            f"Platts request returned HTTP {exc.code}.{suffix}",
            code=code,
            status=exc.code,
        ) from exc
    except URLError as exc:
        raise PlattsRequestError("Platts request could not reach the provider.", code="platts_unreachable") from exc
    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise PlattsRequestError("Platts returned an invalid JSON response.", code="platts_invalid_response") from exc
    if not isinstance(parsed, dict):
        return {"results": parsed}
    return parsed


def _field(row: dict[str, Any], *names: str) -> Any:
    folded = {str(key).casefold(): value for key, value in row.items()}
    for name in names:
        if name.casefold() in folded:
            return folded[name.casefold()]
    return None


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        if payload and all(isinstance(item, dict) for item in payload):
            if any(_field(item, "symbol") is not None for item in payload):
                return payload
        for item in payload:
            found = _rows(item)
            if found:
                return found
    elif isinstance(payload, dict):
        for key in ("results", "data", "items", "values", "value"):
            if key in payload:
                found = _rows(payload[key])
                if found:
                    return found
        for value in payload.values():
            found = _rows(value)
            if found:
                return found
    return []


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iso_date(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date().isoformat()
    except ValueError:
        try:
            return date.fromisoformat(text[:10]).isoformat()
        except ValueError:
            return None


def _month_for_tenor(as_of: date, tenor: str, index: int) -> str:
    offset = index + 1
    normalized = str(tenor).upper().replace(" ", "")
    if normalized.startswith("M+"):
        try:
            offset = max(int(normalized[2:]), 1)
        except ValueError:
            pass
    month_index = as_of.year * 12 + as_of.month - 1 + offset
    return f"{month_index // 12:04d}-{month_index % 12 + 1:02d}"


def _mapping_for(settings: PlattsSettings, commodity: str) -> dict[str, Any]:
    path = settings.resolved_symbol_map_path
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PlattsConfigurationError(
            "Platts symbol mapping is not configured.", code="platts_symbol_map_missing"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise PlattsConfigurationError(
            "Platts symbol mapping cannot be read.", code="platts_symbol_map_invalid"
        ) from exc
    mapping = payload.get(commodity) if isinstance(payload, dict) else None
    points = mapping.get("forward_symbols") if isinstance(mapping, dict) else None
    if not isinstance(points, list) or len(points) < 2:
        raise PlattsConfigurationError(
            f"Platts symbol mapping needs at least two forward symbols for {commodity}.",
            code="platts_symbol_map_incomplete",
        )
    for point in points:
        if not isinstance(point, dict) or not str(point.get("symbol", "")).strip():
            raise PlattsConfigurationError(
                "Every Platts forward mapping must contain a symbol.", code="platts_symbol_map_invalid"
            )
    return mapping


def _cache_age_seconds(payload: dict[str, Any], now: datetime) -> float | None:
    text = str(payload.get("fetched_at", "")).replace("Z", "+00:00")
    try:
        fetched_at = datetime.fromisoformat(text)
    except ValueError:
        return None
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    return max((now - fetched_at.astimezone(timezone.utc)).total_seconds(), 0.0)


def _cached_context(context: dict[str, Any], age_seconds: float, *, stale: bool, locale: str) -> dict[str, Any]:
    copied = json.loads(json.dumps(context))
    copied["provenance"].update(
        {
            "mode": "live_stale_cache" if stale else "live_cached",
            "label": ("普氏授权数据（过期缓存）" if stale else "普氏授权数据（缓存）")
            if locale.lower().startswith("zh")
            else ("Platts entitled data (stale cache)" if stale else "Platts entitled data (cached)"),
            "is_live": False,
            "is_cached": True,
            "cache_age_seconds": round(age_seconds),
            "quality": "stale" if stale else "cached_current",
        }
    )
    return copied


class PlattsMarketClient:
    def __init__(self, settings: PlattsSettings | None = None, transport: Transport | None = None) -> None:
        self.settings = settings or settings_from_env()
        self.transport = transport or _default_transport

    def _auth_headers(self) -> dict[str, str]:
        if self.settings.access_token.strip():
            return {"Authorization": f"Bearer {self.settings.access_token.strip()}"}
        if not self.settings.has_credentials:
            raise PlattsConfigurationError("Platts credentials are not configured.", code="platts_credentials_missing")
        if self.settings.auth_mode == "basic":
            raw = f"{self.settings.username}:{self.settings.password}".encode("utf-8")
            return {"Authorization": f"Basic {b64encode(raw).decode('ascii')}"}
        token_payload = self.transport(
            "POST",
            f"{self.settings.base_url}{PLATTS_TOKEN_PATH}",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body={"username": self.settings.username, "password": self.settings.password},
            timeout=self.settings.timeout_seconds,
        )
        token = str(token_payload.get("access_token") or token_payload.get("token") or "").strip()
        if not token:
            raise PlattsRequestError("Platts authentication returned no access token.", code="platts_auth_failed")
        return {"Authorization": f"Bearer {token}"}

    def _cache_path(self, commodity: str) -> Path:
        return self.settings.resolved_cache_dir / f"platts-{commodity}.json"

    def _read_cache(self, commodity: str) -> dict[str, Any] | None:
        try:
            payload = json.loads(self._cache_path(commodity).read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) and isinstance(payload.get("context"), dict) else None

    def _write_cache(self, commodity: str, context: dict[str, Any], now: datetime) -> None:
        path = self._cache_path(commodity)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "fetched_at": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "context": context,
        }
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(temp, 0o600)
        except OSError:
            pass
        temp.replace(path)

    def _fetch_rows(self, symbols: list[str]) -> list[dict[str, Any]]:
        escaped = [symbol.replace('"', '\\"') for symbol in symbols]
        filter_value = "symbol IN (" + ",".join(f'\"{symbol}\"' for symbol in escaped) + ")"
        payload = self.transport(
            "GET",
            f"{self.settings.base_url}{PLATTS_CURRENT_SYMBOL_PATH}",
            headers=self._auth_headers(),
            params={"Filter": filter_value},
            timeout=self.settings.timeout_seconds,
        )
        rows = _rows(payload)
        if not rows:
            raise PlattsRequestError("Platts returned no entitled values for the mapped symbols.", code="platts_no_data")
        return rows

    def _normalize(
        self,
        *,
        commodity: str,
        mapping: dict[str, Any],
        rows: list[dict[str, Any]],
        locale: str,
        now: datetime,
    ) -> dict[str, Any]:
        from core.market_learning import build_simulated_market_context, classify_forward_curve

        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            symbol = str(_field(row, "symbol") or "").strip()
            if symbol:
                grouped.setdefault(symbol.casefold(), []).append(row)

        curve: list[dict[str, Any]] = []
        observed_dates: list[str] = []
        for index, point in enumerate(mapping["forward_symbols"]):
            symbol = str(point["symbol"]).strip()
            symbol_rows = grouped.get(symbol.casefold(), [])
            if not symbol_rows:
                raise PlattsRequestError(
                    f"Platts returned no value for mapped tenor {point.get('tenor', index + 1)}.",
                    code="platts_mapped_symbol_missing",
                )
            priced_rows = [(row, _number(_field(row, "value", "price", "assessmentValue"))) for row in symbol_rows]
            priced_rows = [(row, value) for row, value in priced_rows if value is not None]
            if not priced_rows:
                raise PlattsRequestError("A mapped Platts symbol has no numeric value.", code="platts_invalid_value")
            bate_values: dict[str, float] = {}
            for row, value in priced_rows:
                bate = str(_field(row, "bate", "valueType", "priceType") or "").strip().casefold()
                if bate:
                    bate_values[bate] = value
                row_date = _iso_date(_field(row, "assessDate", "assessmentDate", "modDate", "date"))
                if row_date:
                    observed_dates.append(row_date)
            preferred = next(
                (bate_values[key] for key in ("c", "close", "mid", "m", "settlement") if key in bate_values),
                priced_rows[0][1],
            )
            bid = next((bate_values[key] for key in ("b", "bid") if key in bate_values), None)
            ask = next((bate_values[key] for key in ("a", "ask", "o", "offer") if key in bate_values), None)
            synthetic_half_spread = max(preferred * 0.0015, 0.01)
            curve.append(
                {
                    "tenor": str(point.get("tenor") or f"M+{index + 1}"),
                    "delivery_month": str(point.get("delivery_month") or ""),
                    "price": round(preferred, 4),
                    "bid": round(bid if bid is not None else preferred - synthetic_half_spread, 4),
                    "ask": round(ask if ask is not None else preferred + synthetic_half_spread, 4),
                    "source_symbol": symbol,
                    "bid_ask_mode": "entitled" if bid is not None and ask is not None else "indicative_derived",
                }
            )

        as_of_text = max(observed_dates) if observed_dates else now.date().isoformat()
        as_of_date = date.fromisoformat(as_of_text)
        for index, point in enumerate(curve):
            if not point["delivery_month"]:
                point["delivery_month"] = _month_for_tenor(as_of_date, point["tenor"], index)
        metrics = classify_forward_curve(curve)
        history_regime = metrics["structure"] if metrics["structure"] in {"contango", "backwardation", "flat"} else "flat"
        seed_material = f"{commodity}|{as_of_text}|" + "|".join(f"{item['price']:.4f}" for item in curve)
        seed = int(sha256(seed_material.encode("utf-8")).hexdigest()[:8], 16)
        calibrated = build_simulated_market_context(
            commodity=commodity,
            regime=history_regime,
            seed=seed,
            as_of=as_of_text,
            locale=locale,
            base_price=curve[0]["price"],
        )
        benchmark = str(mapping.get("benchmark") or calibrated["benchmark"])
        unit = str(mapping.get("unit") or calibrated["unit"])
        zh = locale.lower().startswith("zh")
        return {
            "commodity": commodity,
            "benchmark": benchmark,
            "label": str(mapping.get("label_zh" if zh else "label_en") or benchmark),
            "unit": unit,
            "as_of": as_of_text,
            "forward_curve": curve,
            "history": calibrated["history"],
            "curve_metrics": metrics,
            "market_narrative": (
                f"{benchmark} 授权远期评估显示{metrics['structure']}；历史路径为锚定前月价格的本地校准训练数据。"
                if zh
                else f"Entitled {benchmark} forward assessments show {metrics['structure']}; history is a locally calibrated training path anchored to the front month."
            ),
            "provenance": {
                "mode": "live",
                "label": "普氏授权远期曲线" if zh else "Platts entitled forward curve",
                "source": "S&P Global Commodity Insights (Platts)",
                "source_tier": "entitled_subscription",
                "is_live": True,
                "is_cached": False,
                "quality": "entitled_current",
                "as_of": as_of_text,
                "requested_mode": "live",
                "requested_provider": "platts",
                "evidence_components": [
                    {
                        "id": "forward_curve",
                        "mode": "live",
                        "label": "授权评估价" if zh else "Entitled assessments",
                        "as_of": as_of_text,
                    },
                    {
                        "id": "history",
                        "mode": "calibrated_simulation",
                        "label": "本地校准历史路径" if zh else "Locally calibrated history path",
                        "as_of": as_of_text,
                    },
                ],
            },
        }

    def fetch_market_context(
        self,
        commodity: str,
        *,
        locale: str = "en",
        force_refresh: bool = False,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        if commodity not in {"natural_gas", "crude_oil"}:
            raise PlattsConfigurationError(f"Unsupported Platts commodity: {commodity}", code="platts_commodity_unsupported")
        current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        mapping = _mapping_for(self.settings, commodity)
        cached = self._read_cache(commodity)
        age = _cache_age_seconds(cached, current_time) if cached else None
        if not force_refresh and cached and age is not None and age <= self.settings.cache_ttl_seconds:
            return _cached_context(cached["context"], age, stale=False, locale=locale)
        symbols = [str(point["symbol"]).strip() for point in mapping["forward_symbols"]]
        try:
            rows = self._fetch_rows(symbols)
            context = self._normalize(
                commodity=commodity,
                mapping=mapping,
                rows=rows,
                locale=locale,
                now=current_time,
            )
            self._write_cache(commodity, context, current_time)
            return context
        except PlattsError:
            if cached and age is not None and age <= self.settings.max_stale_seconds:
                return _cached_context(cached["context"], age, stale=True, locale=locale)
            raise


def capability_status(settings: PlattsSettings | None = None) -> dict[str, Any]:
    resolved = settings or settings_from_env()
    has_mapping = resolved.resolved_symbol_map_path.is_file()
    if resolved.has_credentials and has_mapping:
        status = "ready"
    elif resolved.has_credentials:
        status = "credentials_present_missing_symbol_map"
    elif has_mapping:
        status = "symbol_map_present_missing_credentials"
    else:
        status = "not_configured"
    cache_entries: list[str] = []
    try:
        cache_entries = sorted(path.stem.removeprefix("platts-") for path in resolved.resolved_cache_dir.glob("platts-*.json"))
    except OSError:
        pass
    return {
        "status": status,
        "integration_state": "rest_adapter_ready",
        "auth_mode": resolved.auth_mode if resolved.has_credentials else None,
        "symbol_map_configured": has_mapping,
        "cached_commodities": cache_entries,
        "cache_ttl_seconds": resolved.cache_ttl_seconds,
        "requires_subscription": True,
    }
