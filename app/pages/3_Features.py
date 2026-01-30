import streamlit as st

st.set_page_config(page_title="Commodity Lab - Features", layout="wide")
st.title("Features - 特征工程（Step 3 预留）")

st.markdown("""
这一页用于把**标准化后的价格/价差数据**加工成可复用的“特征（Features）”，供策略、回测、监控共用。

### 目标
- 形成统一的特征库：rolling stats、分位数、相关性、regime 等
- 特征可配置、可复用、可追溯（由配置生成，而不是手工改代码）
- 输出既可用于**策略信号**，也可用于**市场状态解释**与**监控告警**

### 典型输入
- Clean prices（已完成单位/币种/日历对齐）
- Derived series（价差/比值/净回值等）

### 典型输出
- Features 表（按 date 对齐）
- Regime 标签（例如：高波动/相关崩塌/极端分位等）
""")

with st.sidebar:
    st.header("Feature 配置（占位）")
    st.selectbox("选择 Universe", ["global_gas (placeholder)"])
    st.multiselect("选择基础序列", ["HH", "TTF", "JKM", "TTF_HH", "JKM_TTF", "JKM_HH"])
    st.number_input("滚动窗口（天）", value=20, min_value=5, max_value=500, step=5)
    st.checkbox("计算 z-score", value=True)
    st.checkbox("计算 rolling volatility", value=True)
    st.checkbox("计算 rolling correlation", value=True)
    st.checkbox("计算 percentile bands", value=True)
    st.checkbox("生成 regime flags", value=True)
    st.button("生成 Features（占位）")

st.info("Step 3 完成后，这里将显示：特征表预览、特征分布图、regime 时间轴与解释。")
st.write("当前仅为页面占位。")
