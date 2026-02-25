import sys
from pathlib import Path

# Add the workspace root to the Python path so core module can be imported
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

import streamlit as st
from app.i18n import t, render_language_switcher, init_language

init_language()

st.set_page_config(
    page_title="Commodity Lab",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Render language switcher at the top of sidebar
render_language_switcher()

st.title("🌾 Commodity Lab")
st.subheader(t("home"))

st.info(t("info") if False else "Commodity Lab - A comprehensive data analytics platform for commodity trading and analysis")

st.markdown(f"""
### {t("home")} 
当前进度：
- ✅ {t("data_management")}：搜索、导入、管理商品数据
- ✅ {t("data_showcase")}：完整的数据展示、QC、派生序列管理
- ⏳ {t("analytics")}：特征工程、关联性分析
- ⏳ {t("monitoring")}：自定义告警、监控仪表板
- ⏳ {t("strategies")}：策略构建、回测引擎

### 快速导航
从左侧菜单选择页面：

1. **{t("data_management")}** → 搜索和导入商品数据
2. **{t("data_showcase")}** → 查看数据、QC、属性、派生序列
3. **{t("analytics")}** → 特征工程、关联性分析、市场状态
4. **{t("monitoring")}** → 自定义告警规则、告警历史
5. **{t("strategies")}** → 策略构建、回测

### 如何使用
1. 首先在"{t("data_management")}"页面搜索并关注您感兴趣的商品
2. 系统会自动下载历史数据
3. 在"{t("data_showcase")}"页面查看详细数据和质量报告
4. 在"{t("monitoring")}"页面设置自定义告警规则
5. 根据数据和分析制定交易策略
""")

