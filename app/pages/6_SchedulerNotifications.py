"""
定时告警检测管理页面 - P1阶段功能
整合调度器、通知配置、技术指标
"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Add workspace root
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from core.scheduler import (
    get_scheduler, init_scheduler_state, toggle_scheduler, 
    get_scheduler_status
)
from core.notifier import NotificationConfig, Notifier
from core.technical_indicators import TechnicalIndicators
from core.db import list_alert_rules, list_alert_events, get_db_connection
from app.i18n import t
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

st.set_page_config(page_title="任务调度", layout="wide")

# 初始化session state
if 'notification_config' not in st.session_state:
    st.session_state.notification_config = NotificationConfig()
if 'technical_indicators' not in st.session_state:
    st.session_state.technical_indicators = TechnicalIndicators()
    
init_scheduler_state()

st.title("⏱️ 任务调度与通知")

# 主选项卡
tab1, tab2, tab3, tab4 = st.tabs([
    "📅 调度器设置",
    "🔔 通知配置",
    "📊 技术指标",
    "📈 检测统计"
])

# ============ TAB 1: 调度器设置 ============
with tab1:
    st.header("自动告警检测调度")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        check_enabled = st.toggle(
            "启用自动检测",
            value=st.session_state.scheduler_running,
            help="启用后，系统每隔指定时间自动检测一次所有告警规则"
        )
        
    with col2:
        check_interval = st.slider(
            "检测间隔(秒)",
            min_value=60,
            max_value=3600,
            value=st.session_state.get('check_interval', 300),
            step=60,
            help="每隔多长时间检测一次规则"
        )
        
    with col3:
        manual_check = st.button("🔍 立即检测", width='stretch')
        
    # 更新调度器状态
    if check_enabled != st.session_state.scheduler_running:
        toggle_scheduler(check_enabled, check_interval)
        st.session_state.check_interval = check_interval
        st.rerun()
        
    # 手动检测
    if manual_check:
        scheduler = st.session_state.alert_scheduler
        with st.spinner("检测中..."):
            result = scheduler.check_all_rules()
        st.success(f"""
        ✅ 检测完成
        - 规则总数: {result['total_rules']}
        - 触发告警: {result['triggered']}
        - 错误数: {len(result['errors'])}
        - 时间: {result['timestamp']}
        """)
        
        if result['errors']:
            st.warning("⚠️ 部分规则评估出错:")
            for error in result['errors']:
                st.write(f"  - Rule {error['rule_id']}: {error['error']}")
        
    # 调度器状态
    st.divider()
    st.subheader("调度器状态")
    
    status = get_scheduler_status()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("运行状态", "✅ 运行中" if status['is_running'] else "⏹️ 已停止")
    with col2:
        st.metric("检测次数", status['check_count'])
    with col3:
        st.metric("错误次数", status['errors_count'])
    with col4:
        st.metric("检测间隔", f"{status['check_interval']}秒")
    with col5:
        last_check = status['last_check_time']
        if last_check:
            st.metric("最后检测", last_check[-8:])
        else:
            st.metric("最后检测", "未检测")
    
    # 最近触发的告警
    st.subheader("最近触发的告警")
    if status['latest_alerts']:
        alerts_df = pd.DataFrame(status['latest_alerts'])
        st.dataframe(
            alerts_df[['ticker', 'severity', 'message', 'created_at']],
            width='stretch',
            hide_index=True
        )
    else:
        st.info("暂无触发的告警")

# ============ TAB 2: 通知配置 ============
with tab2:
    st.header("多渠道通知配置")
    
    # Email配置
    with st.expander("📧 Email通知", expanded=False):
        st.write("配置Email告警通知")
        
        email_col1, email_col2 = st.columns(2)
        with email_col1:
            smtp_server = st.text_input(
                "SMTP服务器",
                value="smtp.gmail.com",
                placeholder="例: smtp.gmail.com"
            )
            sender_email = st.text_input(
                "发送者邮箱",
                placeholder="your-email@gmail.com"
            )
            
        with email_col2:
            smtp_port = st.number_input(
                "SMTP端口",
                value=587,
                min_value=1,
                max_value=65535
            )
            sender_password = st.text_input(
                "邮箱密码/应用密码",
                type="password",
                placeholder="应用专用密码"
            )
            
        if st.button("测试Email配置"):
            try:
                config = st.session_state.notification_config
                config.set_email(smtp_server, smtp_port, sender_email, sender_password)
                notifier = Notifier(config)
                notifier.send_email(
                    recipient=sender_email,
                    subject="Commodity Lab - Email配置测试",
                    body="这是一封测试邮件，说明Email通知配置成功！"
                )
                st.success("✅ Email配置测试成功！")
            except Exception as e:
                st.error(f"❌ Email配置失败: {e}")
    
    # Telegram配置
    with st.expander("✈️ Telegram通知", expanded=False):
        st.write("配置Telegram告警通知")
        st.info("""
        获取Telegram配置:
        1. 创建Telegram Bot: https://t.me/BotFather
        2. 获取Bot Token
        3. 与机器人聊天获取Chat ID: https://api.telegram.org/bot{TOKEN}/getUpdates
        """)
        
        tel_col1, tel_col2 = st.columns(2)
        with tel_col1:
            bot_token = st.text_input(
                "Bot Token",
                type="password",
                placeholder="例: 123456:ABC-DEF..."
            )
        with tel_col2:
            chat_id = st.text_input(
                "Chat ID",
                placeholder="例: -123456789"
            )
            
        if st.button("测试Telegram配置"):
            try:
                config = st.session_state.notification_config
                config.set_telegram(bot_token, chat_id)
                notifier = Notifier(config)
                notifier.send_telegram(
                    message="✅ Commodity Lab Telegram通知配置成功！"
                )
                st.success("✅ Telegram配置测试成功！")
            except Exception as e:
                st.error(f"❌ Telegram配置失败: {e}")
    
    # Slack配置
    with st.expander("🔗 Slack通知", expanded=False):
        st.write("配置Slack告警通知")
        st.info("""
        获取Slack Webhook:
        1. 访问 https://api.slack.com/apps
        2. 创建或选择应用
        3. 启用 Incoming Webhooks
        4. 复制Webhook URL
        """)
        
        webhook_url = st.text_input(
            "Webhook URL",
            type="password",
            placeholder="https://hooks.slack.com/services/..."
        )
        
        if st.button("测试Slack配置"):
            try:
                config = st.session_state.notification_config
                config.set_slack(webhook_url)
                notifier = Notifier(config)
                notifier.send_slack(
                    message="✅ Commodity Lab Slack通知配置成功！"
                )
                st.success("✅ Slack配置测试成功！")
            except Exception as e:
                st.error(f"❌ Slack配置失败: {e}")

# ============ TAB 3: 技术指标 ============
with tab3:
    st.header("技术指标计算与展示")
    
    # 选择商品
    rules = list_alert_rules()
    if rules:
        tickers = list(set([r['ticker'] for r in rules]))
    else:
        tickers = []
        
    if tickers:
        ticker = st.selectbox("选择商品", tickers)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            ma_period = st.slider("MA周期", min_value=5, max_value=200, value=20)
        with col2:
            bb_period = st.slider("布林带周期", min_value=5, max_value=200, value=20)
        with col3:
            rsi_period = st.slider("RSI周期", min_value=5, max_value=30, value=14)
        
        # 获取数据
        conn = get_db_connection()
        query = f"""
            SELECT date, close, volume FROM prices_daily 
            WHERE ticker = '{ticker}' 
            ORDER BY date DESC LIMIT 252
        """
        df = pd.read_sql(query, conn)
        conn.close()
        
        if not df.empty:
            df = df.sort_values('date')
            
            # 计算指标
            indicators = st.session_state.technical_indicators
            
            # SMA
            df['SMA'] = indicators.sma(df['close'].values, ma_period)
            
            # Bollinger Bands
            bb = indicators.bollinger_bands(df['close'].values, bb_period)
            df['BB_Upper'] = bb['upper']
            df['BB_Middle'] = bb['middle']
            df['BB_Lower'] = bb['lower']
            
            # RSI
            df['RSI'] = indicators.rsi(df['close'].values, rsi_period)
            
            # 绘制价格图表 + 指标
            fig = go.Figure()
            
            # K线
            fig.add_trace(go.Scatter(
                x=df['date'], y=df['close'],
                name='Close Price',
                line=dict(color='blue', width=2)
            ))
            
            # SMA
            fig.add_trace(go.Scatter(
                x=df['date'], y=df['SMA'],
                name=f'SMA({ma_period})',
                line=dict(color='orange', dash='dash')
            ))
            
            # 布林带
            fig.add_trace(go.Scatter(
                x=df['date'], y=df['BB_Upper'],
                name='BB Upper',
                line=dict(color='rgba(0,100,200,0.3)', width=1)
            ))
            fig.add_trace(go.Scatter(
                x=df['date'], y=df['BB_Lower'],
                name='BB Lower',
                line=dict(color='rgba(0,100,200,0.3)', width=1),
                fill='tonexty'
            ))
            
            fig.update_layout(
                title=f"{ticker} - 技术指标分析",
                yaxis_title="价格",
                xaxis_title="日期",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # RSI指标单独显示
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=df['date'], y=df['RSI'],
                name='RSI',
                line=dict(color='green')
            ))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超买(70)")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="blue", annotation_text="超卖(30)")
            
            fig_rsi.update_layout(
                title=f"{ticker} - RSI({rsi_period})",
                yaxis_title="RSI",
                xaxis_title="日期",
                height=300
            )
            
            st.plotly_chart(fig_rsi, width='stretch')
            
            # 显示计算结果
            st.subheader("最新指标值")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("现价", f"${df.iloc[-1]['close']:.2f}")
            with col2:
                st.metric("SMA", f"${df.iloc[-1]['SMA']:.2f}")
            with col3:
                st.metric("RSI", f"{df.iloc[-1]['RSI']:.1f}")
            with col4:
                st.metric("BB上界", f"${df.iloc[-1]['BB_Upper']:.2f}")
            with col5:
                st.metric("BB下界", f"${df.iloc[-1]['BB_Lower']:.2f}")
        else:
            st.warning(f"暂无 {ticker} 的数据")
    else:
        st.info("请先创建告警规则以选择商品")

# ============ TAB 4: 检测统计 ============
with tab4:
    st.header("告警检测统计")
    
    # 获取最近的告警事件
    events = list_alert_events(limit=100, acknowledged=None)
    
    if events:
        events_df = pd.DataFrame(events)
        events_df['triggered_at'] = pd.to_datetime(events_df['triggered_at'])
        
        # 时间序列图
        events_by_hour = events_df.groupby(
            pd.Grouper(key='triggered_at', freq='H')
        ).size()
        
        fig = px.bar(
            events_by_hour,
            title="告警触发频率 (按小时)",
            labels={'value': '告警数量', 'triggered_at': '时间'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 按严重级别分布
        col1, col2 = st.columns(2)
        
        with col1:
            severity_counts = events_df['severity'].value_counts()
            fig_severity = px.pie(
                values=severity_counts.values,
                names=severity_counts.index,
                title="按严重级别分布"
            )
            st.plotly_chart(fig_severity, use_container_width=True)
            
        with col2:
            # 未确认与已确认比例
            ack_counts = events_df['acknowledged'].value_counts()
            fig_ack = px.pie(
                values=ack_counts.values,
                names=['已确认' if x else '未确认' for x in ack_counts.index],
                title="事件确认状态"
            )
            st.plotly_chart(fig_ack, use_container_width=True)
        
        # 最近告警列表
        st.subheader("最近告警事件")
        display_cols = ['triggered_at', 'ticker', 'severity', 'message', 'acknowledged']
        st.dataframe(
            events_df[display_cols].head(20),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("暂无告警事件")
