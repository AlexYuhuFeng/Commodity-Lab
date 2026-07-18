from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

import pytest

from core.platts_market import (
    PlattsConfigurationError,
    PlattsMarketClient,
    PlattsRequestError,
    PlattsSettings,
    capability_status,
)


def _write_mapping(tmp_path) -> str:
    path = tmp_path / "platts-symbol-map.json"
    path.write_text(
        json.dumps(
            {
                "natural_gas": {
                    "benchmark": "TTF",
                    "unit": "EUR/MWh",
                    "label_en": "TTF forward assessments",
                    "label_zh": "TTF 远期评估",
                    "forward_symbols": [
                        {"tenor": "M+1", "symbol": "TEST_M1"},
                        {"tenor": "M+2", "symbol": "TEST_M2"},
                        {"tenor": "M+3", "symbol": "TEST_M3"},
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    return str(path)


def _rows() -> dict:
    return {
        "results": [
            {"symbol": "TEST_M1", "bate": "c", "value": 31.0, "assessDate": "2026-07-17"},
            {"symbol": "TEST_M1", "bate": "b", "value": 30.95, "assessDate": "2026-07-17"},
            {"symbol": "TEST_M1", "bate": "a", "value": 31.05, "assessDate": "2026-07-17"},
            {"symbol": "TEST_M2", "bate": "c", "value": 32.0, "assessDate": "2026-07-17"},
            {"symbol": "TEST_M3", "bate": "c", "value": 33.0, "assessDate": "2026-07-17"},
        ]
    }


def test_platts_oauth_fetch_normalizes_entitled_curve_and_calibrated_history(tmp_path) -> None:
    calls: list[tuple[str, str, dict]] = []

    def transport(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if url.endswith("/auth/api"):
            return {"access_token": "temporary-token"}
        return _rows()

    settings = PlattsSettings(
        username="licensed-user",
        password="licensed-password",
        symbol_map_path=_write_mapping(tmp_path),
        cache_dir=str(tmp_path / "cache"),
    )
    market = PlattsMarketClient(settings, transport).fetch_market_context(
        "natural_gas",
        locale="en",
        now=datetime(2026, 7, 18, tzinfo=timezone.utc),
    )

    assert [call[1].split("/")[-1] for call in calls] == ["api", "symbol"]
    assert calls[0][2]["body"] == {"username": "licensed-user", "password": "licensed-password"}
    assert calls[1][2]["headers"]["Authorization"] == "Bearer temporary-token"
    assert "TEST_M1" in calls[1][2]["params"]["Filter"]
    assert market["curve_metrics"]["structure"] == "contango"
    assert market["forward_curve"][0]["bid"] == 30.95
    assert market["forward_curve"][0]["ask"] == 31.05
    assert market["provenance"]["is_live"] is True
    assert market["provenance"]["evidence_components"][0]["mode"] == "live"
    assert market["provenance"]["evidence_components"][1]["mode"] == "calibrated_simulation"
    assert len(market["history"]) >= 30


def test_platts_uses_current_cache_without_another_provider_call(tmp_path) -> None:
    call_count = 0

    def transport(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        return {"access_token": "token"} if url.endswith("/auth/api") else _rows()

    settings = PlattsSettings(
        username="user",
        password="password",
        symbol_map_path=_write_mapping(tmp_path),
        cache_dir=str(tmp_path / "cache"),
        cache_ttl_seconds=900,
    )
    client = PlattsMarketClient(settings, transport)
    now = datetime(2026, 7, 18, tzinfo=timezone.utc)
    client.fetch_market_context("natural_gas", now=now)
    cached = client.fetch_market_context("natural_gas", now=now + timedelta(minutes=5))

    assert call_count == 2
    assert cached["provenance"]["mode"] == "live_cached"
    assert cached["provenance"]["quality"] == "cached_current"
    assert cached["provenance"]["is_live"] is False


def test_platts_falls_back_to_labelled_stale_cache_on_provider_failure(tmp_path) -> None:
    should_fail = False

    def transport(method, url, **kwargs):
        if should_fail:
            raise PlattsRequestError("rate limited", code="platts_rate_limited", status=429)
        return {"access_token": "token"} if url.endswith("/auth/api") else _rows()

    settings = PlattsSettings(
        access_token="token",
        symbol_map_path=_write_mapping(tmp_path),
        cache_dir=str(tmp_path / "cache"),
        cache_ttl_seconds=60,
        max_stale_seconds=3_600,
    )
    client = PlattsMarketClient(settings, transport)
    now = datetime(2026, 7, 18, tzinfo=timezone.utc)
    client.fetch_market_context("natural_gas", now=now)
    should_fail = True
    cached = client.fetch_market_context("natural_gas", now=now + timedelta(minutes=5))

    assert cached["provenance"]["mode"] == "live_stale_cache"
    assert cached["provenance"]["quality"] == "stale"
    assert cached["provenance"]["cache_age_seconds"] == 300


def test_platts_requires_customer_symbol_mapping(tmp_path) -> None:
    settings = PlattsSettings(access_token="token", symbol_map_path=str(tmp_path / "missing.json"))
    with pytest.raises(PlattsConfigurationError) as exc_info:
        PlattsMarketClient(settings).fetch_market_context("natural_gas")
    assert exc_info.value.code == "platts_symbol_map_missing"


def test_capability_status_requires_both_credentials_and_mapping(tmp_path) -> None:
    settings = PlattsSettings(access_token="token", symbol_map_path=_write_mapping(tmp_path))
    status = capability_status(settings)

    assert status["status"] == "ready"
    assert status["integration_state"] == "rest_adapter_ready"
    assert "token" not in str(status).lower()
