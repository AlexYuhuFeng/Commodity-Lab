import streamlit as st

st.set_page_config(page_title="Commodity Lab - Monitor", layout="wide")
st.title("Monitor - 自动更新与告警（Step 5 预留）")

st.markdown("""
这一页用于将系统从“研究工具”升级为“**每日自动更新的监控台**”。

### 目标
- 每日自动拉取数据（API / 文件落地均可）
- 自动运行：QC → 标准化 → Features → 策略信号 → 影子组合表现
- 输出：机会雷达、策略健康度榜单、告警事件列表
- 通知：GUI 内告警 +（后续）邮件/IM/Telegram/Slack

### 告警类型（示例）
**数据告警**
- 数据未更新 / 延迟、缺失、重复、异常跳变、字段结构变化

**市场状态告警**
- spread 极端分位、波动率突变、相关性崩塌、regime 切换

**策略健康告警**
- 回撤超阈值、滚动表现退化（edge decay）、换手异常、逻辑失效提示
""")

with st.sidebar:
    st.header("监控设置（占位）")
    st.selectbox("选择 Universe", ["global_gas (placeholder)"])
    st.multiselect("监控策略池", ["mr_v1", "breakout_v1", "seasonal_v1"], default=["mr_v1"])
    st.checkbox("启用每日自动刷新", value=False)
    st.time_input("每日刷新时间（本地）", value=None)
    st.checkbox("启用告警", value=True)
    st.selectbox("告警输出", ["GUI", "Email（future）", "Telegram（future）", "Slack（future）"])
    st.button("手动运行一次监控流程（占位）")

st.info("Step 5 完成后，这里将显示：最新数据状态、今日信号、策略榜单、告警列表、推荐策略切换建议。")
st.write("当前仅为页面占位。")
