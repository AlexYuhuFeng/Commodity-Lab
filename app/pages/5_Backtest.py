import streamlit as st

st.set_page_config(page_title="Commodity Lab - Backtest", layout="wide")
st.title("Backtest - 回测与评估（Step 4/5 预留）")

st.markdown("""
这一页用于对策略进行**可复现回测**与**稳定性评估**，并输出核心指标与诊断。

### 目标
- 严格无前视（position 使用 t-1）
- 成本/滑点可控（先简化，后扩展）
- 支持 walk-forward / 样本外评估（防止过拟合）
- 输出“策略健康度”：Active / Watch / Retire

### 核心输出
- Equity curve（净值/累计 PnL）
- Drawdown curve（回撤）
- Trade list + attribution（为什么赚/亏）
- 指标：回撤、胜率、收益风险比、换手、成本敏感性、分阶段表现
""")

with st.sidebar:
    st.header("回测设置（占位）")
    st.selectbox("选择 Universe", ["global_gas (placeholder)"])
    st.selectbox("选择策略", ["strategy_v1 (placeholder)"])
    st.selectbox("回测频率", ["Daily"])
    st.checkbox("启用成本模型", value=True)
    st.checkbox("启用 walk-forward", value=False)
    st.number_input("训练窗口（天）", value=756, min_value=60, max_value=5000, step=20)
    st.number_input("测试窗口（天）", value=252, min_value=20, max_value=2000, step=20)
    st.button("运行回测（占位）")

st.info("Step 4/5 完成后，这里将显示：净值曲线、回撤曲线、指标表、分阶段评估、成本敏感性对比。")
st.write("当前仅为页面占位。")
