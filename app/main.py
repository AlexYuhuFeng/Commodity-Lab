import streamlit as st

st.set_page_config(page_title="Commodity Lab", layout="wide")
st.title("Commodity Lab（逐步构建中）")
st.info("fuck国际公司")
st.write("""
当前进度：
- ✅ Step 1：数据导入与展示（见左侧 Data 页面）
- ⏳ Step 2：单位/FX标准化 + QC
- ⏳ Step 3：特征工程
- ⏳ Step 4：策略与回测
- ⏳ Step 5：监控与告警
""")

st.info("请从左侧页面进入：Data → QC → Features → Strategies → Backtest → Monitor")
