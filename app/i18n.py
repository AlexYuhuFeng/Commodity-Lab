# app/i18n.py
"""
Internationalization (i18n) module for Commodity Lab
Supports English (en) and Simplified Chinese (zh)
"""

import streamlit as st
from typing import Dict, Any


TRANSLATIONS = {
    "en": {
        # Common
        "lang": "English",
        "switch_lang": "中文",
        "home": "Home",
        
        # Navigation & Pages
        "data_management": "Data Management",
        "data_showcase": "Data Showcase",
        "analytics": "Analytics",
        "monitoring": "Monitoring & Alerts",
        "strategies": "Strategies & Backtest",
        
        # Data Management Page
        "search": "Search",
        "keywords": "Keywords (e.g., Brent, Natural Gas, TTF, EURUSD)",
        "search_results": "Search Results",
        "add_to_watch": "Add to Watch",
        "already_watched": "Already Watched",
        "local_data": "Local Data",
        "no_local_data": "No local data yet",
        "refresh_settings": "Refresh Settings",
        "first_download_period": "First Download Period",
        "backfill_days": "Backfill Days",
        "backfill_derived": "Backfill Derived Days",
        "refresh_all": "Refresh All Watched",
        "auto_download": "Auto Download on Watch",
        "latest_price": "Latest Price",
        "last_update": "Last Update",
        "data_status": "Data Status",
        "rows": "Rows",
        "missing_bdays": "Missing Business Days",
        "staleness": "Staleness (Days)",
        "refresh_log": "Refresh Log",
        
        # Data Showcase Page
        "tabs": {
            "overview": "Overview",
            "price_chart": "Price Chart",
            "qc_report": "QC Report",
            "properties": "Properties",
            "derived": "Derived Series",
            "operations": "Operations",
        },
        "qc": {
            "title": "Quality Control",
            "missing_values": "Missing Values",
            "duplicates": "Duplicates",
            "outliers": "Outliers",
            "zscore_threshold": "Z-Score Threshold",
            "passed": "PASSED",
            "failed": "FAILED",
        },
        "derived": {
            "create": "Create Derived Series",
            "edit": "Edit",
            "delete": "Delete",
            "formula": "Formula",
            "base": "Base Ticker",
            "fx": "FX Ticker",
            "target_currency": "Target Currency",
            "target_unit": "Target Unit",
        },
        
        # Monitoring & Alerts
        "alerts": "Alerts",
        "alert_rules": "Alert Rules",
        "create_rule": "Create Alert Rule",
        "rule_name": "Rule Name",
        "rule_type": "Rule Type",
        "condition": "Condition",
        "alert_threshold": "Alert Threshold",
        "enabled": "Enabled",
        "active_alerts": "Active Alerts",
        "alert_history": "Alert History",
        "severity": "Severity",
        "triggered_at": "Triggered At",
        
        # Alert Types
        "alert_types": {
            "price_threshold": "Price Threshold",
            "zscore": "Z-Score",
            "volatility": "Volatility",
            "data_staleness": "Data Staleness",
            "data_missing": "Missing Data",
            "correlation_break": "Correlation Break",
            "custom": "Custom Expression",
        },
        
        # Strategies & Backtest
        "strategy": "Strategy",
        "backtest": "Backtest",
        "signal": "Signal",
        "position": "Position",
        
        # Common Actions
        "save": "Save",
        "cancel": "Cancel",
        "delete": "Delete",
        "edit": "Edit",
        "update": "Update",
        "download": "Download",
        "refresh": "Refresh",
        "close": "Close",
        "success": "Success",
        "error": "Error",
        "warning": "Warning",
        "info": "Info",
    },
    "zh": {
        # Common
        "lang": "中文",
        "switch_lang": "English",
        "home": "主页",
        
        # Navigation & Pages
        "data_management": "数据管理",
        "data_showcase": "数据展示",
        "analytics": "分析",
        "monitoring": "监控与告警",
        "strategies": "策略与回测",
        
        # Data Management Page
        "search": "搜索",
        "keywords": "关键词（例：Brent、Natural Gas、TTF、EURUSD）",
        "search_results": "搜索结果",
        "add_to_watch": "添加关注",
        "already_watched": "已关注",
        "local_data": "本地数据",
        "no_local_data": "暂无本地数据",
        "refresh_settings": "刷新设置",
        "first_download_period": "首次下载周期",
        "backfill_days": "回补天数",
        "backfill_derived": "派生序列回补天数",
        "refresh_all": "刷新全部已关注",
        "auto_download": "关注后自动下载",
        "latest_price": "最新价格",
        "last_update": "最后更新",
        "data_status": "数据状态",
        "rows": "行数",
        "missing_bdays": "缺失业务日",
        "staleness": "陈旧度（天）",
        "refresh_log": "刷新日志",
        
        # Data Showcase Page
        "tabs": {
            "overview": "概览",
            "price_chart": "价格图表",
            "qc_report": "质量检查",
            "properties": "属性",
            "derived": "派生序列",
            "operations": "操作",
        },
        "qc": {
            "title": "数据质量控制",
            "missing_values": "缺失值",
            "duplicates": "重复值",
            "outliers": "异常值",
            "zscore_threshold": "Z分数阈值",
            "passed": "通过",
            "failed": "失败",
        },
        "derived": {
            "create": "创建派生序列",
            "edit": "编辑",
            "delete": "删除",
            "formula": "公式",
            "base": "基础Ticker",
            "fx": "汇率Ticker",
            "target_currency": "目标货币",
            "target_unit": "目标单位",
        },
        
        # Monitoring & Alerts
        "alerts": "告警",
        "alert_rules": "告警规则",
        "create_rule": "创建告警规则",
        "rule_name": "规则名称",
        "rule_type": "规则类型",
        "condition": "条件",
        "alert_threshold": "告警阈值",
        "enabled": "启用",
        "active_alerts": "活跃告警",
        "alert_history": "告警历史",
        "severity": "严重程度",
        "triggered_at": "触发时间",
        
        # Alert Types
        "alert_types": {
            "price_threshold": "价格阈值",
            "zscore": "Z分数",
            "volatility": "波动率",
            "data_staleness": "数据陈旧",
            "data_missing": "数据缺失",
            "correlation_break": "相关性断裂",
            "custom": "自定义表达式",
        },
        
        # Strategies & Backtest
        "strategy": "策略",
        "backtest": "回测",
        "signal": "信号",
        "position": "仓位",
        
        # Common Actions
        "save": "保存",
        "cancel": "取消",
        "delete": "删除",
        "edit": "编辑",
        "update": "更新",
        "download": "下载",
        "refresh": "刷新",
        "close": "关闭",
        "success": "成功",
        "error": "错误",
        "warning": "警告",
        "info": "信息",
    }
}


def init_language():
    """Initialize language setting in session state"""
    if "language" not in st.session_state:
        st.session_state.language = "en"


def get_language() -> str:
    """Get current language setting"""
    init_language()
    return st.session_state.language


def set_language(lang: str):
    """Set language"""
    if lang in TRANSLATIONS:
        st.session_state.language = lang


def t(key: str, lang: str = None) -> str:
    """
    Translate a key to current language
    
    Args:
        key: Translation key (supports dot notation for nested keys)
        lang: Optional language override
    
    Returns:
        Translated string or key if not found
    """
    if lang is None:
        lang = get_language()
    
    if lang not in TRANSLATIONS:
        lang = "en"
    
    translations = TRANSLATIONS[lang]
    
    # Handle nested keys (e.g., "alert_types.price_threshold")
    keys = key.split(".")
    result = translations
    
    for k in keys:
        if isinstance(result, dict) and k in result:
            result = result[k]
        else:
            return key  # Return key if translation not found
    
    return str(result)


def render_language_switcher():
    """Render language switcher in sidebar"""
    with st.sidebar:
        current_lang = get_language()
        other_lang = "zh" if current_lang == "en" else "en"
        
        if st.button(f"🌐 {t('switch_lang')}", key="lang_switcher"):
            set_language(other_lang)
            st.rerun()
