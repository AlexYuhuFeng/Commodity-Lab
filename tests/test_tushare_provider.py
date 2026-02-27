import pandas as pd
import requests

from core import tushare_provider as tp


def test_tushare_status_ok(monkeypatch):
    def fake_fetch(token, exchange):
        assert token == "tk"
        assert exchange == "SHFE"
        return pd.DataFrame([{"ts_code": "CU.SHF", "symbol": "CU", "name": "Copper"}])

    monkeypatch.setattr(tp, "_fetch_fut_basic_via_http", fake_fetch)
    assert tp.tushare_status("tk") == (True, "ok")


def test_tushare_status_missing_token():
    assert tp.tushare_status("") == (False, "missing_token")


def test_tushare_status_invalid_token(monkeypatch):
    def fake_fetch(*_args, **_kwargs):
        raise RuntimeError("tushare api error: Invalid token")

    monkeypatch.setattr(tp, "_fetch_fut_basic_via_http", fake_fetch)
    assert tp.tushare_status("bad") == (False, "invalid_token")


def test_fetch_retry_without_proxy(monkeypatch):
    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "code": 0,
                "data": {
                    "fields": ["ts_code", "symbol", "name"],
                    "items": [["CU.SHF", "CU", "Copper"]],
                },
            }

    def fake_post(*_args, **_kwargs):
        raise requests.exceptions.ProxyError("proxy blocked")

    class FakeDirectSession:
        def __init__(self):
            self.trust_env = True

        def post(self, *_args, **_kwargs):
            return FakeResp()

    monkeypatch.setattr(tp.requests, "post", fake_post)
    monkeypatch.setattr(tp, "Session", FakeDirectSession)

    out = tp._fetch_fut_basic_via_http("tk", "SHFE")
    assert not out.empty
    assert out.iloc[0]["ts_code"] == "CU.SHF"


def test_search_tushare_filters_rows(monkeypatch):
    def fake_fetch(_token, exchange):
        if exchange != "SHFE":
            return pd.DataFrame()
        return pd.DataFrame(
            [
                {"ts_code": "CU.SHF", "symbol": "CU", "name": "Copper"},
                {"ts_code": "AL.SHF", "symbol": "AL", "name": "Aluminum"},
            ]
        )

    monkeypatch.setattr(tp, "_fetch_fut_basic_via_http", fake_fetch)

    rows = tp.search_tushare("cu", max_results=5, token="tk")
    assert len(rows) == 1
    assert rows[0]["ticker"] == "CU.SHF"
    assert rows[0]["source"] == "tushare"
