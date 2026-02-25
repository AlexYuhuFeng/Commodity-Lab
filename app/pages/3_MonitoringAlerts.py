# app/pages/3_MonitoringAlerts.py
"""
Monitoring & Alerts Page
Sophisticated alert system with multiple rule types and persistence
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta
import ast
import uuid
import pandas as pd
import streamlit as st
import numpy as np

# Add the workspace root to the Python path so core module can be imported
workspace_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace_root))

from core.db import (
    default_db_path,
    get_conn,
    init_db,
    list_instruments,
    list_alert_rules,
    upsert_alert_rule,
    delete_alert_rule,
    get_alert_rule,
    list_alert_events,
    create_alert_event,
    acknowledge_alert_event,
    query_prices_long,
)
from app.i18n import t, render_language_switcher, init_language

init_language()

st.set_page_config(page_title="Commodity Lab - Monitoring & Alerts", layout="wide")
render_language_switcher()

st.title(f"🚨 {t('monitoring')}")

with st.expander("🧭 Monitoring Guide / 监控说明", expanded=False):
    st.markdown(
        """
- 先创建规则，再逐条点击测试，确认阈值和提示语。
- 建议先启用价格阈值和数据陈旧规则，后续再加波动率/相关性规则。
- 对于自定义表达式，可使用变量 `value` 与 `threshold`（例如：`value > threshold * 1.05`）。
        """
    )

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = default_db_path(PROJECT_ROOT)

con = get_conn(DB_PATH)
init_db(con)


# ===== HELPER FUNCTIONS =====


def safe_eval_custom_expression(expr: str, value: float, threshold: float | None) -> bool:
    """Safely evaluate simple boolean expressions for custom rules."""
    if not expr:
        return False

    allowed_nodes = (
        ast.Expression,
        ast.BoolOp,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.And,
        ast.Or,
        ast.Not,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
    )

    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError("Expression contains unsupported syntax")
        if isinstance(node, ast.Name) and node.id not in {"value", "threshold"}:
            raise ValueError(f"Unsupported variable: {node.id}")

    return bool(
        eval(
            compile(tree, "<alert_expr>", "eval"),
            {"__builtins__": {}},
            {"value": float(value), "threshold": float(threshold) if threshold is not None else None},
        )
    )

def evaluate_alert_condition(ticker: str, con, rule: dict) -> dict | None:
    """
    Evaluate if alert condition is met
    Returns dict with value and triggered=True/False, or None if can't evaluate
    """
    rule_type = rule.get("rule_type", "").lower()
    threshold = rule.get("threshold")
    ticker = (ticker or "").strip()
    
    if not ticker:
        return None
    
    # Get latest price
    prices = query_prices_long(con, [ticker], field="close")
    if prices.empty:
        return None
    
    latest_price = prices.iloc[-1]["value"]
    if latest_price is None or np.isnan(latest_price):
        return None
    
    result = {
        "value": latest_price,
        "triggered": False,
        "message": "",
    }
    
    # Price Threshold rule
    if rule_type == "price_threshold":
        if threshold is not None:
            if latest_price > threshold:
                result["triggered"] = True
                result["message"] = f"{ticker} 价格 {latest_price:.4f} 超过 {threshold:.4f}"
    
    # Z-Score rule (deviation from moving average)
    elif rule_type == "zscore":
        if len(prices) >= 20 and threshold is not None:
            ma = prices["value"].tail(20).mean()
            std = prices["value"].tail(20).std()
            if std > 0:
                zscore = (latest_price - ma) / std
                if abs(zscore) > threshold:
                    result["triggered"] = True
                    result["message"] = f"{ticker} Z-score {zscore:.2f} 超过阈值 {threshold:.2f}"
    
    # Volatility rule
    elif rule_type == "volatility":
        if len(prices) >= 20 and threshold is not None:
            returns = prices["value"].pct_change().tail(20)
            volatility = returns.std() * np.sqrt(252)
            if volatility > threshold:
                result["triggered"] = True
                result["message"] = f"{ticker} 年化波动率 {volatility*100:.2f}% 超过 {threshold*100:.2f}%"
    
    # Data Staleness rule
    elif rule_type == "data_staleness":
        if threshold is not None:
            latest_date = prices.iloc[-1]["date"].date()
            staleness = (datetime.now().date() - latest_date).days
            if staleness > int(threshold):
                result["triggered"] = True
                result["message"] = f"{ticker} 数据已陈旧 {staleness} 天（阈值：{int(threshold)} 天）"
                result["value"] = staleness
    
    # Data Missing rule
    elif rule_type == "data_missing":
        if threshold is not None:
            total_rows = len(prices)
            missing = prices["value"].isna().sum()
            missing_pct = (missing / total_rows * 100) if total_rows > 0 else 0
            if missing_pct > threshold:
                result["triggered"] = True
                result["message"] = f"{ticker} 缺失值 {missing_pct:.2f}% 超过 {threshold:.2f}%"
                result["value"] = missing_pct
    
    # Correlation Break rule
    elif rule_type == "correlation_break":
        peer_ticker = (rule.get("condition_expr") or "").strip()
        if peer_ticker and threshold is not None and len(prices) >= 60:
            peer = query_prices_long(con, [peer_ticker], field="close")
            if not peer.empty:
                merged = pd.merge(
                    prices[["date", "value"]].rename(columns={"value": "v1"}),
                    peer[["date", "value"]].rename(columns={"value": "v2"}),
                    on="date",
                    how="inner",
                ).dropna()
                if len(merged) >= 60:
                    long_corr = merged["v1"].tail(60).corr(merged["v2"].tail(60))
                    short_corr = merged["v1"].tail(20).corr(merged["v2"].tail(20))
                    corr_diff = abs(float(short_corr) - float(long_corr))
                    if corr_diff > float(threshold):
                        result["triggered"] = True
                        result["value"] = corr_diff
                        result["message"] = (
                            f"{ticker} vs {peer_ticker} 相关性变化 {corr_diff:.3f} 超过阈值 {float(threshold):.3f}"
                        )

    # Custom Expression rule
    elif rule_type == "custom":
        expr = (rule.get("condition_expr") or "").strip()
        if expr:
            try:
                if safe_eval_custom_expression(expr, latest_price, threshold):
                    result["triggered"] = True
                    result["message"] = f"表达式触发: {expr} (value={latest_price:.4f})"
                else:
                    result["message"] = "表达式未触发"
            except Exception as exc:
                result["message"] = f"表达式错误: {exc}"
    
    return result


def test_alert_rule(rule: dict):
    """Test an alert rule and return result"""
    ticker = rule.get("ticker")
    if not ticker:
        return "请指定 ticker"
    
    result = evaluate_alert_condition(ticker, con, rule)
    if result is None:
        return "无法评估：数据不足或找不到 ticker"
    
    if result["triggered"]:
        return f"✅ 触发条件：{result['message']}"
    else:
        return f"⏸️ 未触发"


# ===== SIDEBAR: QUICK ACTIONS =====
with st.sidebar:
    st.header("⚙️ 快速操作")
    
    if st.button("🔄 检测所有规则", type="primary", use_container_width=True):
        st.session_state["check_all_rules"] = True
    
    st.divider()
    
    inst = list_instruments(con, only_watched=True)
    if not inst.empty:
        st.write(f"**已关注产品**: {len(inst)}")
        selected_ticker = st.selectbox("快速检测", inst["ticker"].tolist(), key="quick_check_ticker")
        
        if st.button("🔍 检测此产品的所有规则", use_container_width=True):
            st.session_state["quick_check_ticker"] = selected_ticker


# ===== MAIN TABS =====
tabs = st.tabs(["📋 告警规则", "🚨 活跃告警", "📊 告警历史"])


# ===== TAB 0: ALERT RULES =====
with tabs[0]:
    st.subheader("告警规则管理")
    
    rules = list_alert_rules(con, enabled_only=False)
    
    if not rules.empty:
        st.write(f"**总规则数**: {len(rules)}")
        
        # Display rules
        for idx, (_, rule) in enumerate(rules.iterrows()):
            with st.expander(f"📋 {rule['rule_name']} ({rule['rule_type']}) - {'✅ 启用' if rule['enabled'] else '⏸️ 禁用'}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**规则ID**: {rule['rule_id']}")
                    st.write(f"**类型**: {rule['rule_type']}")
                
                with col2:
                    st.write(f"**Ticker**: {rule.get('ticker', 'N/A')}")
                    st.write(f"**严重度**: {rule.get('severity', 'medium')}")
                
                with col3:
                    st.write(f"**阈值**: {rule.get('threshold', 'N/A')}")
                    st.write(f"**创建时间**: {rule.get('created_at', 'N/A')}")
                
                if rule.get("condition_expr"):
                    st.write(f"**条件**: {rule['condition_expr']}")
                
                if rule.get("notes"):
                    st.write(f"**备注**: {rule['notes']}")
                
                st.divider()
                
                # Test and Actions
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("✅ 测试规则", key=f"test_{rule['rule_id']}"):
                        result = test_alert_rule(rule)
                        st.info(result)
                
                with col2:
                    new_enabled = not rule["enabled"]
                    if st.button(
                        f"{'⏹️ 禁用' if rule['enabled'] else '▶️ 启用'}",
                        key=f"toggle_{rule['rule_id']}"
                    ):
                        upsert_alert_rule(con, {**rule.to_dict(), "enabled": new_enabled})
                        st.success(f"规则已{'启用' if new_enabled else '禁用'}")
                        st.rerun()
                
                with col3:
                    if st.button("✏️ 编辑", key=f"edit_{rule['rule_id']}"):
                        st.session_state[f"edit_{rule['rule_id']}"] = True
                
                with col4:
                    if st.button("🗑️ 删除", key=f"delete_{rule['rule_id']}"):
                        delete_alert_rule(con, rule["rule_id"])
                        st.success(f"规则已删除")
                        st.rerun()
    else:
        st.info("暂无告警规则，请创建一个")
    
    # Create new rule form
    st.divider()
    st.subheader("创建新告警规则")
    
    with st.form("create_alert_rule"):
        col1, col2 = st.columns(2)
        
        with col1:
            rule_name = st.text_input("规则名称", placeholder="e.g., Brent超过70")
            rule_id = st.text_input(
                "规则ID (自动生成)",
                value=f"rule_{str(uuid.uuid4())[:8]}",
                disabled=True
            )
        
        with col2:
            rule_type = st.selectbox(
                "规则类型",
                [
                    "price_threshold",
                    "zscore",
                    "volatility",
                    "data_staleness",
                    "data_missing",
                    "correlation_break",
                    "custom",
                ],
                format_func=lambda x: {
                    "price_threshold": "价格阈值",
                    "zscore": "Z分数异常",
                    "volatility": "波动率突增",
                    "data_staleness": "数据陈旧",
                    "data_missing": "数据缺失",
                    "correlation_break": "相关性断裂",
                    "custom": "自定义表达式",
                }.get(x, x)
            )
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            inst = list_instruments(con)
            ticker = st.selectbox(
                "产品 (可选)",
                [""] + inst["ticker"].tolist() if not inst.empty else [""],
            )
        
        with col2:
            threshold = st.number_input("阈值", value=0.0, step=0.1)
        
        with col3:
            severity = st.selectbox("严重度", ["low", "medium", "high", "critical"], index=1)
        
        with col4:
            enabled = st.checkbox("启用", value=True)
        
        condition_expr = st.text_area(
            "条件表达式 (自定义规则适用)",
            placeholder="e.g., price > 70 AND volatility < 0.2",
            height=80
        )
        
        notes = st.text_area("备注", height=60)
        
        submit_button = st.form_submit_button("➕ 创建规则", use_container_width=True)
        
        if submit_button:
            if not rule_name:
                st.error("请输入规则名称")
            elif not rule_type:
                st.error("请选择规则类型")
            else:
                try:
                    upsert_alert_rule(con, {
                        "rule_id": rule_id,
                        "rule_name": rule_name,
                        "rule_type": rule_type,
                        "ticker": ticker if ticker else None,
                        "threshold": threshold if threshold != 0 else None,
                        "severity": severity,
                        "enabled": enabled,
                        "condition_expr": condition_expr if condition_expr else None,
                        "notes": notes if notes else None,
                    })
                    st.success(f"✅ 规则已创建: {rule_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 创建失败: {str(e)}")


# ===== TAB 1: ACTIVE ALERTS =====
with tabs[1]:
    st.subheader("活跃告警")
    
    # Refresh active alerts if triggered
    if st.session_state.get("check_all_rules"):
        st.info("正在检查所有规则...")
        
        rules = list_alert_rules(con, enabled_only=True)
        alert_count = 0
        
        if not rules.empty:
            for _, rule in rules.iterrows():
                result = evaluate_alert_condition(rule.get("ticker"), con, rule)
                
                if result and result.get("triggered"):
                    event_id = create_alert_event(con, {
                        "event_id": f"event_{str(uuid.uuid4())[:8]}",
                        "rule_id": rule["rule_id"],
                        "ticker": rule.get("ticker"),
                        "severity": rule.get("severity", "medium"),
                        "message": result.get("message", ""),
                        "value": result.get("value"),
                    })
                    alert_count += 1
        
        st.success(f"✅ 检查完成，发现 {alert_count} 个新告警")
        st.session_state["check_all_rules"] = False
        st.rerun()
    
    # Get active alerts (not acknowledged)
    active_alerts = list_alert_events(con, limit=100, acknowledged=False)
    
    if active_alerts.empty:
        st.success("✅ 暂无活跃告警")
    else:
        st.warning(f"🚨 当前有 {len(active_alerts)} 个活跃告警")
        
        for idx, (_, alert) in enumerate(active_alerts.iterrows()):
            severity_emoji = {
                "low": "🟢",
                "medium": "🟡",
                "high": "🔴",
                "critical": "🆘",
            }.get(alert.get("severity", "medium"), "⚠️")
            
            with st.expander(
                f"{severity_emoji} {alert['message']} @ {alert['triggered_at'].strftime('%Y-%m-%d %H:%M')}"
            ):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**规则ID**: {alert.get('rule_id', 'N/A')}")
                    st.write(f"**Ticker**: {alert.get('ticker', 'N/A')}")
                
                with col2:
                    st.write(f"**严重度**: {alert.get('severity', 'N/A')}")
                    st.write(f"**值**: {alert.get('value', 'N/A')}")
                
                with col3:
                    st.write(f"**触发时间**: {alert['triggered_at']}")
                    st.write(f"**创建时间**: {alert['created_at']}")
                
                st.divider()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    ack_notes = st.text_input(
                        "确认备注",
                        key=f"ack_notes_{alert['event_id']}",
                        placeholder="记录你的处理方式"
                    )
                
                with col2:
                    if st.button("✅ 确认告警", key=f"ack_{alert['event_id']}", use_container_width=True):
                        acknowledge_alert_event(con, alert["event_id"], ack_notes)
                        st.success("告警已确认")
                        st.rerun()


# ===== TAB 2: ALERT HISTORY =====
with tabs[2]:
    st.subheader("告警历史")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_back = st.slider("显示最近N天的告警", 1, 90, 7)
    
    with col2:
        show_acknowledged = st.checkbox("包含已确认的告警", value=False)
    
    with col3:
        severity_filter = st.selectbox("按严重度筛选", ["all", "low", "medium", "high", "critical"])
    
    # Get history
    history = list_alert_events(con, limit=500, acknowledged=show_acknowledged if show_acknowledged else False)
    
    # Filter by date
    cutoff_date = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days_back)
    if "triggered_at" in history.columns:
        history["triggered_at"] = pd.to_datetime(history["triggered_at"], utc=True, errors="coerce")
        history = history[history["triggered_at"] >= cutoff_date]
    
    # Filter by severity
    if severity_filter != "all":
        history = history[history["severity"] == severity_filter]
    
    if history.empty:
        st.info("暂无告警历史")
    else:
        st.write(f"**总数**: {len(history)} 条告警")
        
        # Summary stats
        col1, col2, col3, col4, col5 = st.columns(5)
        
        severity_counts = history["severity"].value_counts()
        with col1:
            st.metric("Critical", severity_counts.get("critical", 0))
        with col2:
            st.metric("High", severity_counts.get("high", 0))
        with col3:
            st.metric("Medium", severity_counts.get("medium", 0))
        with col4:
            st.metric("Low", severity_counts.get("low", 0))
        with col5:
            st.metric("已确认", history["acknowledged"].sum())
        
        st.divider()
        
        # Display as table
        display_cols = ["triggered_at", "rule_id", "ticker", "severity", "message", "acknowledged"]
        available_cols = [c for c in display_cols if c in history.columns]
        
        df_display = history[available_cols].copy()
        df_display.columns = ["触发时间", "规则", "Ticker", "严重度", "信息", "已确认"]
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
        )
        
        # Download history
        st.divider()
        csv = history.to_csv(index=False)
        st.download_button(
            label="📥 下载告警历史 (CSV)",
            data=csv,
            file_name=f"alert_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
