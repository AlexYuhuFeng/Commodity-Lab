# Commodity Lab

一个全面的商品交易数据分析平台。提供数据导入、质量控制、特征工程、策略开发、回测和实时监控功能。

**语言 | Language**: 中文 / English (支持UI语言切换)

## ✨ 核心特性

### 📊 **数据管理** (Data Management)
- 搜索Yahoo Finance数据源（支持过滤和分页）
- 自动导入历史价格数据
- 本地数据库管理和元数据编辑
- 一键刷新所有已关注产品
- 刷新日志追踪

### 🔍 **数据展示** (Data Showcase)
- 仿券商股票详情页设计
- 6个标签页：概览、价格图表、质量检查、属性、派生序列、操作
- 交互式价格走势图表
- 自动QC检查（缺失值、异常值、数据陈旧度等）
- 派生序列创建与管理

### 🚨 **监控与告警** (Monitoring & Alerts)
- 7种告警规则类型：
  - 价格阈值告警
  - Z分数异常检测
  - 波动率突增告警
  - 数据质量告警（陈旧、缺失）
  - 相关性断裂检测
  - 自定义表达式告警
- 活跃告警实时显示
- 告警历史完整追踪
- 告警确认与备注管理
- 历史数据导出（CSV）

### 🎯 **分析与策略** (Advanced Features - 开发中)
- 特征工程库
- 关联性分析
- 策略回测
- 风险指标计算

### 🌐 **国际化** (Internationalization)
- 完整的中文和英文支持
- 一键语言切换
- 所有UI文本国际化

## 🚀 快速开始

### 前置条件
- Python 3.12+
- 已创建虚拟环境 (`venv`)

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动应用
```bash
# 方式1: 使用启动脚本
./run.sh

# 方式2: 直接使用streamlit
streamlit run app/main.py
```

应用将在 `http://localhost:8501` 启动

## 📖 使用指南

### 第一步：搜索和关注产品
1. 打开 **📊 数据管理** 页面
2. 在搜索框输入产品代码 (如: `Brent`, `Natural Gas`, `EURUSD`)
3. 点击 **➕ 添加关注**
4. 系统自动下载历史数据

### 第二步：查看产品详情
1. 打开 **🔍 数据展示** 页面
2. 从侧边栏选择产品
3. 浏览各个标签页：
   - **概览**: 关键指标和统计
   - **价格图表**: 交互式走势图
   - **质量检查**: 自动QC报告
   - **属性**: 产品元数据编辑
   - **派生序列**: 创建衍生指标
   - **操作**: 刷新、导出、关注管理

### 第三步：创建告警规则
1. 打开 **🚨 监控与告警** 页面
2. 在"告警规则"标签页创建新规则
3. 选择规则类型，设置条件
4. 点击"测试规则"验证效果
5. 规则自动生效

**示例：为Brent设置价格告警 (>70)**
- 规则名称: `Brent Over 70`
- 类型: `价格阈值`
- 产品: `BZ=F`
- 阈值: `70`
- 严重度: `High`

## 📁 项目结构

```
Commodity-Lab/
├── app/
│   ├── main.py                          # 主页面 + 语言切换
│   ├── i18n.py                          # 国际化框架
│   └── pages/
│       ├── 1_DataManagement.py          # 📊 数据管理
│       ├── 2_DataShowcase.py            # 🔍 数据展示 (6个Tab)
│       ├── 3_MonitoringAlerts.py        # 🚨 监控告警 (7种规则)
│       ├── 4_Analytics.py               # 📈 分析 (开发中)
│       └── 5_StrategiesBacktest.py      # 🎯 策略回测 (开发中)
├── core/
│   ├── db.py                            # 数据库操作 (DuckDB)
│   ├── qc.py                            # 质量检查
│   ├── transforms.py                    # 派生序列计算
│   ├── refresh.py                       # 数据刷新
│   ├── yf_provider.py                   # Yahoo Finance接口
│   ├── yf_prices.py                     # 价格获取
│   ├── yf_search.py                     # 搜索功能
│   └── ...                              # 其他模块
├── data/
│   └── commodity_lab.duckdb             # 数据库文件
├── run.sh                               # 启动脚本
├── requirements.txt                     # 依赖列表
├── pyproject.toml                       # 项目配置
└── README.md                            # 本文件
```

## 🗄️ 数据库

使用 **DuckDB** 作为数据库引擎，具有以下表：

- `instruments`: 产品信息（代码、名称、货币、单位等）
- `prices_daily`: 日线价格数据
- `derived_daily`: 派生序列数据
- `transforms`: 派生序列配置
- `refresh_log`: 数据刷新日志
- `alert_rules`: 告警规则定义
- `alert_events`: 告警事件历史

## 🔧 开发信息

### 技术栈
- **前端**: Streamlit
- **数据库**: DuckDB
- **数据处理**: Pandas, NumPy, Plotly
- **股票数据**: yfinance

### 模块化架构
- **core.db**: 数据库层（CRUD操作）
- **core.qc**: 质量控制模块
- **core.transforms**: 数据转换模块
- **core.refresh**: 数据同步模块
- **app.i18n**: 国际化模块
- **app.pages**: UI页面

### 扩展功能

添加新的告警规则类型：
1. 在 `app/pages/3_MonitoringAlerts.py` 的 `evaluate_alert_condition()` 函数中添加条件逻辑
2. 在 i18n 配置中添加新规则的标签

创建新的派生序列：
1. 在**数据展示**页面的"派生序列"标签页中填写配置
2. 系统自动计算并存储结果

## 📊 告警规则详解

### 价格阈值 (Price Threshold)
当最新价格超过设定值时触发
```
条件: price > threshold
示例: BZ=F > 70
```

### Z分数异常 (Z-Score)
当价格偏离20日均值超过N个标准差时触发
```
条件: |z| > threshold
示例: |z| > 2.5 (超过2.5倍标准差)
```

### 波动率告警 (Volatility)
当年化波动率超过阈值时触发
```
条件: 年化波动率 > threshold
示例: volatility > 0.30 (30%)
```

### 数据陈旧告警 (Data Staleness)
当数据未更新超过N天时触发
```
条件: days_since_update > threshold
示例: staleness > 3 (超过3天)
```

### 数据缺失告警 (Missing Data)
当缺失值比例超过阈值时触发
```
条件: missing_pct > threshold
示例: missing > 5 (超过5%)
```

## 📈 路线图

### v1.1 (下一版本)
- [ ] 告警通知系统 (Email/Telegram/Slack)
- [ ] 自定义告警条件可视化编辑
- [ ] K线图表和技术指标
- [ ] 数据导出格式增强

### v1.2
- [ ] 特征工程库完整实现
- [ ] 关联性分析模块
- [ ] 策略回测引擎
- [ ] 风险指标计算

### v2.0
- [ ] Web部署 (Docker + 云平台)
- [ ] 多用户支持
- [ ] 权限管理
- [ ] 生产级监控

## 📝 更新日志

### v1.0 (2026-02-25) - UI重构完成
✅ 完成P0级别所有需求
- 国际化框架
- 数据管理页面整合
- 数据展示页面（Tab设计）
- 告警系统（7种规则类型）
- 功能模块化架构

## 💡 最佳实践

1. **定期刷新数据**: 设置每天自动刷新以保持数据最新
2. **创建分类告警**: 为不同的产品创建针对性的告警规则
3. **监控数据质量**: 定期检查QC报告，及时处理问题
4. **使用派生序列**: 创建有意义的衍生指标进行对比分析

## 🐛 故障排除

### 应用无法启动
```bash
# 检查虚拟环境是否激活
source venv/bin/activate

# 检查依赖是否安装
pip install -r requirements.txt

# 检查端口8501是否被占用
lsof -i :8501
```

### 数据导入失败
- 检查网络连接
- 确认产品代码正确 (使用搜索功能验证)
- 查看刷新日志了解错误详情

### 告警规则未触发
- 在告警规则管理中点击"测试规则"验证
- 确认规则已启用
- 检查产品数据是否存在

## 📞 支持

有任何问题或建议，请：
1. 查看 [UI_REDESIGN_GUIDE.md](UI_REDESIGN_GUIDE.md) 获取详细文档
2. 检查应用内的帮助信息
3. 提交Issue或联系开发团队

## 📄 许可证

MIT License

## 👨‍💻 作者

Commodity Lab Development Team


## Requirements

- Python 3.12+
- See `pyproject.toml` for detailed dependencies

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd Commodity-Lab
```

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:

**Option A (Common and Simple):**
```bash
pip install -r requirements.txt
```

**Option B (Development mode with editable install):**
```bash
pip install -e .
```

We recommend **Option A** for most users. Option B is useful if you're developing the `core` module and want changes reflected immediately without reinstalling.

## Usage

Run the Streamlit application:

```bash
streamlit run app/main.py
```

This will start a local web server (typically at `http://localhost:8501`) where you can access the application.

## Workflow

1. **Start with Data**: Go to the Data page to ingest commodity price data
2. **Quality Control**: Use the QC page to validate data integrity
3. **Transforms**: Apply unit and FX standardization as needed
4. **Features**: Engineer features for analysis
5. **Strategies**: Develop trading strategies
6. **Backtest**: Test strategy performance on historical data
7. **Monitor**: Set up real-time monitoring and alerts

## Technologies

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **DuckDB**: Lightweight SQL database for data storage
- **yfinance**: Financial data fetching
- **Plotly**: Interactive visualizations

## Development

To work with the project:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or for editable development mode
pip install -e .

# Run the app
streamlit run app/main.py

# Run specific pages for testing
streamlit run app/pages/0_Catalog.py
```

## Database

The project uses DuckDB for data storage. The database file is located at `data/commodity_lab.duckdb`.

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]