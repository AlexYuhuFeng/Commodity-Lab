"""
可视化条件编辑器UI - Streamlit实现
"""
import streamlit as st
import sys
from pathlib import Path

workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from app.i18n import init_language
from core.condition_builder import (
    ConditionBuilder, ConditionGroup, Condition, OperatorType,
    DataType, LogicalOperator, ConditionTemplate, ConditionValidator
)
import json

init_language()

st.set_page_config(page_title="条件编辑器", layout="wide")

st.title("🎨 自定义条件可视化编辑器")
st.markdown("直观的条件构建工具，无需手写代码")

# 初始化Session State
if 'condition_group' not in st.session_state:
    st.session_state.condition_group = ConditionBuilder.create_group('and')
if 'saved_templates' not in st.session_state:
    st.session_state.saved_templates = {}

# 侧边栏：模板和快速操作
with st.sidebar:
    st.markdown("### 📚 快速模板")
    
    template_col1, template_col2 = st.columns(2)
    
    with template_col1:
        if st.button("💰 价格监控", width='stretch'):
            st.session_state.current_template = "price_monitoring"
    
    with template_col2:
        if st.button("📊 波动率监控", width='stretch'):
            st.session_state.current_template = "volatility_monitoring"
    
    if st.button("⚠️  数据质量", width='stretch'):
        st.session_state.current_template = "data_quality"
    
    if st.button("🔗 相关性检测", width='stretch'):
        st.session_state.current_template = "correlation_detection"
    
    st.divider()
    
    # 加载预定义模板
    if st.session_state.get('current_template') == 'price_monitoring':
        st.success("✅ 已加载：价格监控模板")
        # 创建价格监控条件
        group = ConditionBuilder.create_group('or')
        group.add_condition(ConditionTemplate.price_above(1900))
        group.add_condition(ConditionTemplate.price_below(1850))
        st.session_state.condition_group = group
    
    elif st.session_state.get('current_template') == 'volatility_monitoring':
        st.success("✅ 已加载：波动率监控模板")
        group = ConditionBuilder.create_group('and')
        group.add_condition(ConditionTemplate.high_volatility(0.2))
        group.add_condition(ConditionTemplate.high_zscore(2.0))
        st.session_state.condition_group = group
    
    elif st.session_state.get('current_template') == 'data_quality':
        st.success("✅ 已加载：数据质量模板")
        group = ConditionBuilder.create_group('or')
        group.add_condition(ConditionTemplate.data_stale(7))
        group.add_condition(ConditionTemplate.data_missing(10))
        st.session_state.condition_group = group
    
    elif st.session_state.get('current_template') == 'correlation_detection':
        st.success("✅ 已加载：相关性检测模板")
        group = ConditionBuilder.create_group('and')
        group.add_condition(ConditionBuilder.create_comparison('correlation', '<', 0.7))
        st.session_state.condition_group = group

# 主区域
tab1, tab2, tab3, tab4 = st.tabs(["📐 可视化编辑", "💾 预存条件", "🧪 测试评估", "📝 代码导出"])

with tab1:
    st.subheader("条件编辑器")
    
    # 显示当前条件组的信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("条件数量", len(st.session_state.condition_group.conditions))
    with col2:
        st.metric("子组数量", len(st.session_state.condition_group.sub_groups))
    with col3:
        logic_op = st.session_state.condition_group.logical_op.value.upper()
        st.metric("逻辑操作", logic_op)
    
    st.divider()
    
    # 逻辑操作符选择
    col1, col2, col3 = st.columns(3)
    with col1:
        logic_choice = st.radio(
            "主条件组的逻辑操作符",
            ["AND (全部满足)", "OR (任一满足)"],
            index=0,
            key="logic_op_choice"
        )
        if logic_choice == "AND (全部满足)":
            st.session_state.condition_group.logical_op = LogicalOperator.AND
        else:
            st.session_state.condition_group.logical_op = LogicalOperator.OR
    
    st.divider()
    
    # 添加新条件
    st.markdown("### ➕ 添加新条件")
    
    add_col1, add_col2, add_col3, add_col4 = st.columns(4)
    
    with add_col1:
        field = st.selectbox(
            "字段",
            list(ConditionTemplate.COMMODITY_FIELDS.keys()),
            key="new_field",
            label_visibility="collapsed"
        )
    
    with add_col2:
        # 根据数据类型显示合适的操作符
        if ConditionTemplate.COMMODITY_FIELDS.get(field) == DataType.NUMERIC:
            operators = [op.value for op in [
                OperatorType.EQUALS, OperatorType.GREATER_THAN, OperatorType.LESS_THAN,
                OperatorType.GREATER_EQUAL, OperatorType.LESS_EQUAL, OperatorType.IN_RANGE
            ]]
        else:
            operators = [op.value for op in [
                OperatorType.EQUALS, OperatorType.CONTAINS, OperatorType.NOT_CONTAINS,
                OperatorType.STARTS_WITH, OperatorType.ENDS_WITH
            ]]
        
        operator = st.selectbox(
            "操作符",
            operators,
            key="new_operator",
            label_visibility="collapsed"
        )
    
    with add_col3:
        if operator == "in_range":
            value = st.text_input(
                "范围 (min,max)",
                "0,100",
                key="new_value",
                label_visibility="collapsed"
            )
        else:
            value = st.text_input(
                "值",
                key="new_value",
                label_visibility="collapsed"
            )
    
    with add_col4:
        if st.button("✅ 添加", width='stretch'):
            try:
                # 解析操作符
                op = OperatorType(operator)
                
                # 解析值
                if operator == "in_range":
                    parts = value.split(',')
                    parsed_value = (float(parts[0].strip()), float(parts[1].strip()))
                else:
                    try:
                        parsed_value = float(value)
                    except:
                        parsed_value = value
                
                # 创建条件
                new_cond = Condition(
                    field=field,
                    operator=op,
                    value=parsed_value,
                    data_type=ConditionTemplate.COMMODITY_FIELDS.get(field, DataType.TEXT)
                )
                
                # 验证
                is_valid, msg = ConditionValidator.validate_condition(new_cond)
                if is_valid:
                    st.session_state.condition_group.add_condition(new_cond)
                    st.success(f"✅ 已添加条件：{field} {operator} {value}")
                else:
                    st.error(f"❌ 验证失败：{msg}")
            except Exception as e:
                st.error(f"❌ 错误：{str(e)}")
    
    st.divider()
    
    # 显示现有条件
    st.markdown("### 📋 当前条件列表")
    
    if st.session_state.condition_group.conditions:
        for i, cond in enumerate(st.session_state.condition_group.conditions):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.code(f"{cond.field} {cond.operator.value} {cond.value}")
            
            with col2:
                if st.button("✏️", key=f"edit_{i}"):
                    st.info("编辑功能开发中...")
            
            with col3:
                if st.button("🗑️", key=f"delete_{i}"):
                    st.session_state.condition_group.remove_condition(i)
                    st.success("✅ 已删除条件")
                    st.rerun()
    else:
        st.info("暂无条件，请添加第一个条件")
    
    st.divider()
    
    # 显示完整表达式
    st.markdown("### 📝 条件表达式")
    st.code(st.session_state.condition_group.to_expression(), language="text")


with tab2:
    st.subheader("预存条件库")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 保存当前条件")
        template_name = st.text_input("条件库名称", placeholder="输入一个易记的名称")
        template_desc = st.text_area("条件说明", placeholder="描述这个条件的用途")
        
        if st.button("💾 保存条件", type="primary"):
            if template_name:
                st.session_state.saved_templates[template_name] = {
                    'name': template_name,
                    'description': template_desc,
                    'data': st.session_state.condition_group.to_dict(),
                    'created_at': st.session_state.get(f'created_at_{template_name}', 'now')
                }
                st.success(f"✅ 已保存：{template_name}")
            else:
                st.error("❌ 请输入条件库名称")
    
    with col2:
        st.markdown("#### 加载已保存的条件")
        if st.session_state.saved_templates:
            selected_template = st.selectbox(
                "选择已保存的条件",
                list(st.session_state.saved_templates.keys())
            )
            
            if selected_template:
                template_info = st.session_state.saved_templates[selected_template]
                st.markdown(f"**说明：** {template_info.get('description', 'N/A')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📂 加载", type="primary"):
                        st.session_state.condition_group = ConditionGroup.from_dict(
                            template_info['data']
                        )
                        st.success(f"✅ 已加载：{selected_template}")
                        st.rerun()
                
                with col2:
                    if st.button("🗑️  删除"):
                        del st.session_state.saved_templates[selected_template]
                        st.success("✅ 已删除")
                        st.rerun()
        else:
            st.info("暂无已保存的条件")
    
    st.divider()
    
    # 显示所有已保存的条件
    st.markdown("#### 📚 条件库列表")
    if st.session_state.saved_templates:
        for name, template in st.session_state.saved_templates.items():
            with st.expander(f"📌 {name}"):
                st.markdown(f"**说明：** {template.get('description', 'N/A')}")
                st.json(template['data'])
    else:
        st.info("暂无已保存的条件")


with tab3:
    st.subheader("条件测试评估")
    
    st.markdown("### 输入测试数据")
    
    # 获取当前条件中的所有字段
    condition_fields = set()
    for cond in st.session_state.condition_group.conditions:
        condition_fields.add(cond.field)
    
    test_data = {}
    
    if condition_fields:
        col1, col2 = st.columns(2)
        
        for i, field in enumerate(sorted(condition_fields)):
            with [col1, col2][i % 2]:
                field_type = ConditionTemplate.COMMODITY_FIELDS.get(field, DataType.TEXT)
                
                if field_type == DataType.NUMERIC:
                    test_data[field] = st.number_input(
                        f"{field} (数值)",
                        value=0.0,
                        key=f"test_{field}"
                    )
                else:
                    test_data[field] = st.text_input(
                        f"{field} (文本)",
                        key=f"test_{field}"
                    )
        
        st.divider()
        
        # 评估
        if st.button("🧪 测试评估", type="primary", width='stretch'):
            result = st.session_state.condition_group.evaluate(test_data)
            
            st.markdown("### 📊 评估结果")
            
            if result:
                st.success("✅ 条件**满足** - 触发告警")
            else:
                st.info("❌ 条件**不满足** - 不触发告警")
            
            # 显示详细分析
            st.markdown("### 📈 详细分析")
            
            for i, cond in enumerate(st.session_state.condition_group.conditions):
                actual = test_data.get(cond.field, 'N/A')
                cond_result = cond.evaluate(actual)
                
                status = "✅" if cond_result else "❌"
                st.markdown(
                    f"{status} 条件 {i+1}: `{cond.field} {cond.operator.value} {cond.value}` "
                    f"(实际值: `{actual}`)"
                )
    else:
        st.warning("⚠️  请先添加至少一个条件")


with tab4:
    st.subheader("代码导出")
    
    st.markdown("### 🐍 Python代码")
    
    # 生成Python代码
    python_code = """
from core.condition_builder import ConditionBuilder, ConditionGroup

# 创建条件组
builder = ConditionBuilder()
group = builder.create_group('and')  # or 'or'

# 添加条件
group.add_condition(builder.create_comparison('price', '>', 100))
group.add_condition(builder.create_comparison('volatility', '>', 0.2))

# 评估
result = group.evaluate({
    'price': 150,
    'volatility': 0.3
})

print(f"条件满足: {result}")
    """
    
    # 替换为实际条件
    actual_group_dict = st.session_state.condition_group.to_dict()
    
    st.code(python_code, language="python")
    
    st.markdown("### 📋 JSON格式")
    
    json_str = json.dumps(actual_group_dict, indent=2, ensure_ascii=False)
    st.code(json_str, language="json")
    
    st.divider()
    
    # 导出选项
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 下载为JSON", width='stretch'):
            st.download_button(
                label="条件.json",
                data=json_str,
                file_name="condition.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📥 下载为Python", width='stretch'):
            st.download_button(
                label="条件.py",
                data=python_code,
                file_name="condition.py",
                mime="text/plain"
            )

# 底部帮助信息
st.sidebar.divider()
st.sidebar.markdown("""
### 💡 使用提示

1. **添加条件**: 选择字段、操作符、输入值
2. **测试**: 在"测试评估"标签页输入数据进行测试
3. **保存**: 保存常用的条件组以便后续使用
4. **导出**: 导出为JSON或Python代码供其他系统使用
""")
