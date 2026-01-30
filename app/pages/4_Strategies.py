import streamlit as st

st.set_page_config(page_title="Commodity Lab - Strategies", layout="wide")
st.title("Strategies - 策略构建（Step 4 预留）")

st.markdown("""
这一页用于把特征转换成**可执行的交易策略**（信号 → 仓位），并形成“策略库”。

### 目标
- 策略模板化：均值回归、突破趋势、季节性、regime 切换等
- 参数可配置、可复现（配置文件/GUI 控件）
- 输出包括：signal、position、trade log、reason codes（为什么进出场）

### 策略对象（通用）
- Signal：根据 features 生成目标方向/强度
- Filter：根据 regime 或风控条件启用/禁用
- Sizer：仓位大小（固定/波动率目标/风险预算）
- Execution model：T+1 执行、滑点、成本等（初期简化）
""")

with st.sidebar:
    st.header("策略设置（占位）")
    st.selectbox("选择 Universe", ["global_gas (placeholder)"])
    st.selectbox("选择策略模板", [
        "Z-Score Mean Reversion（均值回归）",
        "Breakout / Momentum（突破趋势）",
        "Seasonality（季节性）",
        "Regime Switching（状态切换）",
    ])
    st.selectbox("信号标的（derived series）", ["JKM_TTF", "TTF_HH", "JKM_HH"])
    st.number_input("Lookback（天）", value=252, min_value=20, max_value=2000, step=10)
    st.number_input("入场阈值（z）", value=2.0, step=0.1)
    st.number_input("离场阈值（z）", value=0.5, step=0.1)
    st.checkbox("启用 regime filter", value=True)
    st.number_input("交易成本（$/单位）", value=0.02, step=0.01)
    st.button("生成信号与仓位（占位）")

st.info("Step 4 完成后，这里将显示：信号/仓位叠加图、交易列表、参数摘要、策略版本管理。")
st.write("当前仅为页面占位。")
