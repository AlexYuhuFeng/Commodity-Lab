# app/i18n.py
"""
Internationalization (i18n) module for Commodity Lab.

Enhancements:
- Loads canonical translations from `app/locales/*.json`
- Falls back to legacy in-code keys for backward compatibility
- Supports dot notation (`nav.home`) and direct keys (`home`)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st


# Legacy translations retained for backwards compatibility with existing keys.
LEGACY_TRANSLATIONS = {
    "en": {
        "lang": "English",
        "switch_lang": "中文",
        "home": "Home",
        "data_management": "Data Management",
        "data_showcase": "Data Showcase",
        "analytics": "Analytics",
        "monitoring": "Monitoring & Alerts",
        "strategies": "Strategies & Backtest",
        "backtest_controls": "Backtest Controls",
        "backtest_info": "Configure strategy parameters and run backtest",
    },
    "zh": {
        "lang": "中文",
        "switch_lang": "English",
        "home": "主页",
        "data_management": "数据管理",
        "data_showcase": "数据展示",
        "analytics": "分析",
        "monitoring": "监控与告警",
        "strategies": "策略与回测",
        "backtest_controls": "回测控制",
        "backtest_info": "配置策略参数并运行回测",
    },
}

# Map legacy short keys to locale JSON paths.
KEY_ALIASES = {
    "home": "nav.home",
    "data_management": "nav.data_management",
    "data_showcase": "nav.data_showcase",
    "analytics": "nav.analytics",
    "monitoring": "nav.monitoring",
    "strategies": "nav.strategies",
    "lang": "language.name",
    "switch_lang": "language.switch",
}


@st.cache_data(show_spinner=False)
def _load_locale_files() -> dict[str, dict[str, Any]]:
    locales_dir = Path(__file__).parent / "locales"
    loaded: dict[str, dict[str, Any]] = {}

    for path in locales_dir.glob("*.json"):
        lang = path.stem
        try:
            loaded[lang] = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            loaded[lang] = {}

    # Ensure at least en/zh exist in memory
    loaded.setdefault("en", {})
    loaded.setdefault("zh", {})
    return loaded


def init_language() -> None:
    if "language" not in st.session_state:
        st.session_state.language = "en"


def get_language() -> str:
    init_language()
    return st.session_state.language


def set_language(lang: str) -> None:
    locales = _load_locale_files()
    if lang in locales:
        st.session_state.language = lang


def _resolve_path(data: dict[str, Any], key: str) -> str | None:
    result: Any = data
    for part in key.split("."):
        if isinstance(result, dict) and part in result:
            result = result[part]
        else:
            return None
    return str(result)


def t(key: str, lang: str | None = None) -> str:
    if lang is None:
        lang = get_language()

    locales = _load_locale_files()
    if lang not in locales:
        lang = "en"

    # 1) Try locale JSON directly.
    resolved = _resolve_path(locales.get(lang, {}), key)
    if resolved is not None:
        return resolved

    # 2) Try alias path in locale JSON.
    alias_key = KEY_ALIASES.get(key)
    if alias_key:
        resolved = _resolve_path(locales.get(lang, {}), alias_key)
        if resolved is not None:
            return resolved

    # 3) Try legacy in-code translations.
    legacy_lang = LEGACY_TRANSLATIONS.get(lang, {})
    if key in legacy_lang:
        return str(legacy_lang[key])

    # 4) Fallback to English locale path/alias.
    resolved = _resolve_path(locales.get("en", {}), key)
    if resolved is not None:
        return resolved
    if alias_key:
        resolved = _resolve_path(locales.get("en", {}), alias_key)
        if resolved is not None:
            return resolved

    # 5) Fallback to key itself.
    return key


def render_language_switcher() -> None:
    locales = _load_locale_files()
    options = sorted(locales.keys())
    current = get_language()
    if current not in options:
        current = "en"

    labels = {"en": "English", "zh": "中文"}
    c1, c2 = st.columns([6, 2])
    c2.markdown("### 🌐")
    selected = c2.selectbox(
        "Language / 语言",
        options=options,
        index=options.index(current),
        format_func=lambda x: labels.get(x, x),
        key="lang_selectbox",
        label_visibility="collapsed",
    )

    if selected != get_language():
        set_language(selected)
        st.rerun()
