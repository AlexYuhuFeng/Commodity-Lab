"""
告警通知配置UI - 支持Email、Telegram、Slack配置和管理
"""
import streamlit as st
import sys
from pathlib import Path

workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import t, init_language
from core.notifier import NotificationConfig, AlertNotifier, NotificationHistory
from core.db import get_db

init_language()

st.set_page_config(page_title="告警通知", layout="wide")

st.title("📧 告警通知系统")
st.markdown("配置多渠道告警通知 - Email, Telegram, Slack")

# 初始化Session State
if 'notification_config' not in st.session_state:
    st.session_state.notification_config = NotificationConfig()
if 'notifier' not in st.session_state:
    st.session_state.notifier = None
if 'notification_history' not in st.session_state:
    st.session_state.notification_history = NotificationHistory()

# 侧边栏：通知渠道切换
st.sidebar.markdown("### 🔔 通知渠道管理")
selected_channel = st.sidebar.radio(
    "选择要配置的渠道",
    ["Email", "Telegram", "Slack", "历史记录", "测试发送"],
    key="selected_channel"
)

# 主区域
if selected_channel == "Email":
    st.subheader("📧 Email 通知配置")
    
    col1, col2 = st.columns(2)
    with col1:
        smtp_server = st.text_input(
            "SMTP服务器地址",
            value="smtp.gmail.com",
            help="例如: smtp.gmail.com, smtp.qq.com"
        )
        smtp_port = st.number_input(
            "SMTP服务器端口",
            value=587,
            min_value=1,
            max_value=65535,
            help="通常为: 587 (TLS) 或 465 (SSL)"
        )
        
    with col2:
        sender_email = st.text_input(
            "发件人邮箱",
            placeholder="your-email@gmail.com",
            help="用于发送告警的邮箱地址"
        )
        sender_password = st.text_input(
            "邮箱密码/授权码",
            type="password",
            placeholder="输入密码或授权码",
            help="Gmail需要使用应用专用密码"
        )
    
    # Email配置说明
    with st.expander("📚 Email配置指南"):
        st.markdown("""
        ### Gmail配置步骤:
        1. 启用两步验证: https://myaccount.google.com/security
        2. 生成应用专用密码: https://myaccount.google.com/apppasswords
        3. 使用专用密码而不是账户密码
        4. SMTP服务器: smtp.gmail.com
        5. 端口: 587 (TLS)
        
        ### QQ邮箱配置步骤:
        1. 进入 https://mail.qq.com
        2. 生成授权码: 邮箱设置 → 账户 → IMAP/SMTP服务
        3. SMTP服务器: smtp.qq.com
        4. 端口: 587 (TLS)
        """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ 保存Email配置", key="save_email"):
            if sender_email and sender_password and smtp_server:
                st.session_state.notification_config.set_email(
                    smtp_server, smtp_port, sender_email, sender_password
                )
                st.session_state.notifier = AlertNotifier(st.session_state.notification_config)
                st.success("✅ Email配置已保存")
            else:
                st.error("❌ 请填写所有必填项")
    
    with col2:
        if st.button("🧪 测试Email", key="test_email"):
            if st.session_state.notifier:
                test_alert = {
                    'rule_name': '测试规则',
                    'ticker': 'GOLD',
                    'severity': 'high',
                    'message': '这是一条测试通知',
                    'value': '1950.50',
                    'threshold': '1950.00'
                }
                result = st.session_state.notifier.notify(test_alert, channels=['email'])
                if result['results'].get('email', {}).get('success'):
                    st.success("✅ 测试邮件已发送")
                else:
                    st.error(f"❌ 发送失败: {result['results'].get('email', {}).get('error')}")
            else:
                st.error("❌ 请先保存Email配置")
    
    with col3:
        if st.button("🗑️  删除配置", key="delete_email"):
            st.session_state.notification_config.disable_channel('email')
            st.success("✅ Email配置已禁用")


elif selected_channel == "Telegram":
    st.subheader("📱 Telegram 通知配置")
    
    col1, col2 = st.columns(2)
    with col1:
        bot_token = st.text_input(
            "Bot Token",
            type="password",
            placeholder="输入你的Telegram Bot Token",
            help="从 BotFather 获取: https://t.me/botfather"
        )
    with col2:
        chat_id = st.text_input(
            "Chat ID",
            placeholder="输入接收通知的Chat ID",
            help="可以是个人用户ID或群组ID"
        )
    
    # Telegram配置说明
    with st.expander("📚 Telegram配置指南"):
        st.markdown("""
        ### 创建Telegram Bot步骤:
        1. 搜索 @BotFather (Telegram官方Bot管理工具)
        2. 发送 `/newbot` 创建新的Bot
        3. 按提示输入Bot名称和用户名
        4. 保存获得的Bot Token
        
        ### 获取Chat ID:
        1. 与你的Bot对话（发送任何消息）
        2. 访问: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
        3. 在JSON响应中找到 "chat": {"id": 123456789}
        4. 即可获得你的Chat ID
        
        ### 群组Chat ID:
        1. 将Bot添加到群组
        2. 在群组中发送一条消息
        3. 使用上面的getUpdates方法获取群组ID (通常是负数)
        """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ 保存Telegram配置", key="save_telegram"):
            if bot_token and chat_id:
                st.session_state.notification_config.set_telegram(bot_token, chat_id)
                st.session_state.notifier = AlertNotifier(st.session_state.notification_config)
                st.success("✅ Telegram配置已保存")
            else:
                st.error("❌ 请填写所有必填项")
    
    with col2:
        if st.button("🧪 测试Telegram", key="test_telegram"):
            if st.session_state.notifier:
                test_alert = {
                    'rule_name': '测试规则',
                    'ticker': 'GOLD',
                    'severity': 'high',
                    'message': '这是一条测试通知',
                    'value': '1950.50',
                    'threshold': '1950.00'
                }
                result = st.session_state.notifier.notify(test_alert, channels=['telegram'])
                if result['results'].get('telegram', {}).get('success'):
                    st.success("✅ Telegram消息已发送")
                else:
                    st.error(f"❌ 发送失败: {result['results'].get('telegram', {}).get('error')}")
            else:
                st.error("❌ 请先保存Telegram配置")
    
    with col3:
        if st.button("🗑️  删除配置", key="delete_telegram"):
            st.session_state.notification_config.disable_channel('telegram')
            st.success("✅ Telegram配置已禁用")


elif selected_channel == "Slack":
    st.subheader("💬 Slack 通知配置")
    
    webhook_url = st.text_input(
        "Webhook URL",
        type="password",
        placeholder="输入你的Slack Webhook URL",
        help="Slack通道集成的消息发送地址"
    )
    
    # Slack配置说明
    with st.expander("📚 Slack配置指南"):
        st.markdown("""
        ### 创建Slack Webhook步骤:
        1. 进入 https://api.slack.com/apps
        2. 创建新应用 (From scratch)
        3. 在 "Incoming Webhooks" 中启用
        4. 点击 "Add New Webhook to Workspace"
        5. 选择要接收通知的频道
        6. 复制生成的Webhook URL
        
        ### Webhook URL格式:
        ```
        https://hooks.slack.com/services/YOUR/WEBHOOK/URL
        ```
        
        ### 使用提示:
        - 每个频道需要一个独立的Webhook
        - Webhook URL包含验证信息，需要保密
        - 支持发送富文本和附件
        """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✅ 保存Slack配置", key="save_slack"):
            if webhook_url:
                st.session_state.notification_config.set_slack(webhook_url)
                st.session_state.notifier = AlertNotifier(st.session_state.notification_config)
                st.success("✅ Slack配置已保存")
            else:
                st.error("❌ 请输入Webhook URL")
    
    with col2:
        if st.button("🧪 测试Slack", key="test_slack"):
            if st.session_state.notifier:
                test_alert = {
                    'rule_name': '测试规则',
                    'ticker': 'GOLD',
                    'severity': 'high',
                    'message': '这是一条测试通知',
                    'value': '1950.50',
                    'threshold': '1950.00'
                }
                result = st.session_state.notifier.notify(test_alert, channels=['slack'])
                if result['results'].get('slack', {}).get('success'):
                    st.success("✅ Slack消息已发送")
                else:
                    st.error(f"❌ 发送失败: {result['results'].get('slack', {}).get('error')}")
            else:
                st.error("❌ 请先保存Slack配置")
    
    with col3:
        if st.button("🗑️  删除配置", key="delete_slack"):
            st.session_state.notification_config.disable_channel('slack')
            st.success("✅ Slack配置已禁用")


elif selected_channel == "历史记录":
    st.subheader("📋 通知历史记录")
    
    # 获取历史记录
    history = st.session_state.notification_history.get_history(limit=100)
    
    if history:
        col1, col2, col3 = st.columns(3)
        with col1:
            total = len(history)
            st.metric("总通知次数", total)
        with col2:
            successful = sum(1 for h in history if h['result'].get('success'))
            st.metric("成功次数", successful)
        with col3:
            failed = total - successful
            st.metric("失败次数", failed, delta=-failed if failed > 0 else 0)
        
        st.divider()
        
        # 失败通知列表
        failed_notifications = st.session_state.notification_history.get_failed_notifications()
        if failed_notifications:
            st.warning(f"⚠️  有 {len(failed_notifications)} 条失败的通知")
            
            with st.expander("📌 显示失败详情"):
                for record in failed_notifications[:10]:  # 显示最近10条
                    st.json(record)
            
            if st.button("🔄 重试失败通知"):
                if st.session_state.notifier:
                    retry_result = st.session_state.notification_history.retry_failed(
                        st.session_state.notifier
                    )
                    st.info(f"已提交 {len(retry_result)} 条通知重试")
        
        # 显示最近通知
        st.subheader("📅 最近通知")
        for i, record in enumerate(reversed(history[-20:])):
            with st.expander(
                f"{record['timestamp']} - "
                f"{'✅' if record['result'].get('success') else '❌'}"
            ):
                st.json(record['result'])
    else:
        st.info("暂无通知记录")


elif selected_channel == "测试发送":
    st.subheader("🧪 发送测试告警")
    
    col1, col2 = st.columns(2)
    with col1:
        rule_name = st.text_input("规则名称", value="测试规则")
        ticker = st.text_input("商品代码", value="GOLD")
    with col2:
        severity = st.selectbox("严重程度", ["low", "medium", "high"])
        message = st.text_area("告警信息", value="这是一条测试通知")
    
    col1, col2 = st.columns(2)
    with col1:
        value = st.number_input("当前值", value=1950.50)
    with col2:
        threshold = st.number_input("阈值", value=1950.00)
    
    # 选择通知渠道
    channels = []
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.checkbox("📧 Email"):
            channels.append('email')
    with col2:
        if st.checkbox("📱 Telegram"):
            channels.append('telegram')
    with col3:
        if st.checkbox("💬 Slack"):
            channels.append('slack')
    
    if st.button("🚀 发送测试通知", type="primary"):
        if not channels:
            st.error("❌ 请至少选择一个通知渠道")
        elif not st.session_state.notifier:
            st.error("❌ 请先配置至少一个通知渠道")
        else:
            test_alert = {
                'rule_name': rule_name,
                'ticker': ticker,
                'severity': severity,
                'message': message,
                'value': str(value),
                'threshold': str(threshold)
            }
            
            with st.spinner("正在发送通知..."):
                result = st.session_state.notifier.notify(test_alert, channels=channels)
                st.session_state.notification_history.add_record(result)
            
            # 显示结果
            st.divider()
            if result['success']:
                st.success("✅ 所有通知已成功发送")
            else:
                st.warning("⚠️  部分通知发送失败")
            
            # 显示详细结果
            col1, col2, col3 = st.columns(3)
            for i, (channel, res) in enumerate(result['results'].items()):
                with [col1, col2, col3][i % 3]:
                    if res.get('success'):
                        st.success(f"✅ {channel.upper()}: {res.get('message')}")
                    else:
                        st.error(f"❌ {channel.upper()}: {res.get('error')}")

# 顶部状态栏
st.sidebar.divider()
st.sidebar.markdown("### ✅ 已启用的渠道")
active_channels = st.session_state.notification_config.get_active_channels()
if active_channels:
    for channel in active_channels:
        st.sidebar.success(f"✓ {channel.upper()}")
else:
    st.sidebar.info("未配置任何通知渠道")

# 底部提示
st.sidebar.divider()
st.sidebar.info("""
💡 **提示:**
- 配置完成后，在告警规则页面可以选择通知渠道
- 支持多渠道同时发送
- 测试按钮可以验证配置是否正确
""")
