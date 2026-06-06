# Commodity Lab

**Commodity Lab** is an AI-powered desktop training terminal for energy trading practice. It combines market data, structured trading scenarios, deterministic scoring, and an optional Haineng-compatible LLM coach. Users can enter the terminal immediately in Base Mode with Yahoo Finance and simulated data; connecting Haineng unlocks Full Power Mode with AI case generation, event-driven drills, concept tutoring, scoring explanations, trade playbooks, and adaptive exams.

**Commodity Lab** 是一个 AI 驱动的能源交易训练终端。系统将市场数据、结构化业务场景、确定性评分和海能兼容 LLM 教练结合起来。用户无需先配置海能即可进入基础训练模式，使用 Yahoo Finance 和模拟数据完成训练；连接海能后进入 AI 全功能模式，解锁案例生成、事件演练、概念教学、评分解释、交易实务建议和自适应测验。

![Status](https://img.shields.io/badge/status-V1%20active-1f6feb)
![Desktop](https://img.shields.io/badge/client-Windows-2563eb)
![AI](https://img.shields.io/badge/AI-%E6%B5%B7%E8%83%BD%20compatible-0f766e)
![Data](https://img.shields.io/badge/data-Yahoo%20Finance%20%7C%20Simulated%20%7C%20Platts%20reserved-0e7490)

Suggested GitHub repository description:

```text
AI-powered desktop training terminal for energy trading, combining market data, structured scenarios, deterministic scoring, and Haineng LLM coaching.
```

## Product Goal / 产品目标

Commodity Lab is not intended to be a static course or a simple hedge calculator. The goal is to build a professional training terminal that teaches energy trading judgment through repeated practice:

- read the market context;
- understand the commercial exposure;
- choose an appropriate financial tool;
- submit a trade or hedge decision;
- receive deterministic scoring;
- use AI to generate cases, challenge reasoning, explain concepts, and produce exams.

Commodity Lab 不是静态课程，也不是简单套保计算器。项目目标是构建一个专业训练终端，通过反复训练提升能源交易判断能力：

- 阅读市场环境；
- 识别商业敞口；
- 选择合适金融工具；
- 提交交易或套保决策；
- 获得确定性评分；
- 使用 AI 生成案例、追问逻辑、解释概念并生成测验。

## Scope / 范围

V1 enables European natural gas training and shows the future energy scope as disabled modules.

V1 启用欧洲天然气训练，并将其他能源模块作为后续方向展示。

| Module | Status | Notes |
|---|---|---|
| Natural Gas / 天然气 | Enabled | Europe natural gas scenarios |
| Crude Oil / 原油 | Constructing | Future module |
| Oil Products / 成品油 | Constructing | Future module |
| Carbon / 碳 | Constructing | Future module |
| Power / 电力 | Constructing | Future module |

Natural gas V1 scenarios are organized around Europe:

- **Europe**: hub spread, storage spread, route/capacity logic, TTF/NBP-style thinking.
- **Future North America / LNG**: Henry Hub, regional basis, pipeline constraints, weather-driven load, and LNG optionality.

天然气 V1 场景围绕欧洲组织：

- **欧洲**：枢纽价差、储气月差、路径/运力逻辑、TTF/NBP 类思路。
- **后续北美 / LNG**：亨利港、区域基差、管道约束、天气负荷和 LNG 可选性。

## Experience Modes / 体验模式

### Base Mode

Base Mode is available immediately. No Haineng key is required at startup.

基础模式进入即用，启动时不要求提供海能 Key。

Base Mode includes:

- Yahoo Finance / simulated market data;
- scenario selection;
- exposure and route/capacity context;
- order decision ticket;
- deterministic scoring;
- bilingual UI.

### AI Full Power Mode

Connecting a user-provided Haineng-compatible endpoint unlocks the full AI training workflow.

连接用户自备的海能兼容端点后，系统进入 AI 全功能模式。

AI Full Power Mode is designed to support:

- **Business case generation**: generate realistic trading cases from commodity, region, exposure, and market setting.
- **Event-driven drills**: use international events, weather, supply disruption, sanctions, maintenance, storage, or shipping context to create scenario tests.
- **Concept tutoring**: explain futures, basis, spreads, storage optionality, route cost, nomination, and risk controls.
- **Scoring explanation**: translate deterministic scoring into a human-readable coaching review.
- **Trade playbook advice**: suggest what a trader should check before acting.
- **Adaptive exams**: generate targeted questions based on the learner's mistakes.

AI 全功能模式用于：

- **业务案例生成**：基于商品、区域、敞口和市场环境生成接近实务的训练案例。
- **事件驱动演练**：结合国际事件、天气、供应中断、制裁、检修、库存或航运信息生成测试题。
- **概念教学**：讲解期货、基差、价差、储气库可选性、路径成本、提名量和风控逻辑。
- **评分解释**：将确定性评分转换为可读的教练式复盘。
- **交易实务建议**：提示交易员在行动前应检查哪些信息。
- **自适应测验**：根据用户错误生成针对性测验。

## Architecture / 技术架构

```text
Commodity Lab
├── core/                         Python domain logic
│   ├── gas_scenarios.py          Energy scenario catalog, regions, market context
│   ├── learning_session.py       Deterministic scoring and attempt evaluation
│   ├── yf_prices.py              Yahoo Finance market data adapter
│   └── haineng_client.py         OpenAI-compatible Haineng client
├── tauri/backend/                FastAPI backend for the desktop client
├── tauri/tauri-frontend/         React + Vite terminal UI
├── tauri/src-tauri/              Tauri Rust shell and backend launcher
├── tauri/scripts/                Backend and desktop packaging scripts
└── tests/                        Python and frontend regression tests
```

```text
Commodity Lab
├── core/                         Python 领域逻辑
│   ├── gas_scenarios.py          能源场景目录、区域、市场环境
│   ├── learning_session.py       确定性评分与训练评估
│   ├── yf_prices.py              Yahoo Finance 市场数据适配器
│   └── haineng_client.py         OpenAI 兼容的海能客户端
├── tauri/backend/                桌面客户端使用的 FastAPI 后端
├── tauri/tauri-frontend/         React + Vite 终端界面
├── tauri/src-tauri/              Tauri Rust 外壳与后端启动器
├── tauri/scripts/                后端和桌面端打包脚本
└── tests/                        Python 与前端回归测试
```

## Requirements / 环境要求

- Python 3.12+
- Node.js 20+
- Rust stable
- Windows for desktop packaging
- Optional user-provided Haineng-compatible LLM API key and base URL
- Optional user-provided Platts credentials

环境要求：

- Python 3.12+
- Node.js 20+
- Rust stable
- Windows 桌面端打包环境
- 可选：用户自备海能兼容 LLM API Key 与 Base URL
- 可选：用户自备 Platts 凭证

## Quick Start / 快速开始

Install backend dependencies and start the FastAPI service:

安装后端依赖并启动 FastAPI 服务：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r tauri/backend/requirements.txt
python tauri/backend/main.py
```

Start the frontend:

启动前端：

```powershell
cd tauri\tauri-frontend
npm ci
npm run dev
```

Run the Tauri desktop shell:

运行 Tauri 桌面外壳：

```powershell
cd tauri
npm ci
npm run tauri:dev
```

## Configuration / 配置

Commodity Lab does not ship with provider credentials. Users configure providers at runtime.

Commodity Lab 不内置任何服务商凭证。用户在运行时自行配置。

海能 / AI:

- `HAINENG_API_KEY`
- `HAINENG_BASE_URL`
- `HAINENG_MODEL` defaults to `V4-Flash`

Backend runtime:

- `COMMODITY_LAB_BACKEND_HOST` defaults to `127.0.0.1`
- `COMMODITY_LAB_BACKEND_PORT` defaults to `8000`

Data providers:

- Yahoo Finance is used first when selected and available.
- Simulated data is always available as fallback.
- Platts is reserved for future integration or user-provided credentials.

数据来源：

- 选择 Yahoo Finance 时优先调用 Yahoo Finance。
- 模拟数据始终作为兜底。
- Platts 作为后续集成或用户凭证接入方向预留。

## Windows Packaging / Windows 打包

Commodity Lab V1 generates Windows desktop client artifacts.

Commodity Lab V1 生成 Windows 桌面客户端产物。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1
```

Dry run:

试运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1 -DryRun
```

Generated bundles are written under:

生成产物位于：

```text
tauri\src-tauri\target\release\bundle\
```

## Verification / 验证

Python tests:

Python 测试：

```powershell
pytest tests/test_gas_scenarios.py tests/test_learning_session.py tests/test_haineng_client.py tests/test_tauri_backend_v1.py tests/test_pages_smoke.py -q
```

Frontend tests and build:

前端测试与构建：

```powershell
cd tauri\tauri-frontend
npm ci
npm run test
npm run build
```

Tauri Rust check:

Tauri Rust 检查：

```powershell
cd tauri\src-tauri
cargo check
```

Full desktop package:

完整桌面端打包：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\package_tauri.ps1
```

## Release / 发布

GitHub Actions workflow:

GitHub Actions 工作流：

```text
.github/workflows/tauri-build.yml
```

Manual online build:

网页手动构建：

```text
Actions → Tauri Windows Build → Run workflow → main
```

Manual workflow runs upload the `commodity-lab-windows` artifact. Tag pushes also create a GitHub Release and upload the generated Windows bundle files.

手动运行工作流会上传 `commodity-lab-windows` 产物。推送版本标签时还会创建 GitHub Release 并上传 Windows 构建产物。

Create a release tag:

创建发布标签：

```powershell
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

## Security / 安全

- Do not commit 海能, Platts, Yahoo Finance, or other provider credentials.
- API keys are accepted only through environment variables or runtime setup.
- Backend responses redact configured secrets.
- LLM prompts must not include provider credentials.

安全要求：

- 不要提交海能、Platts、Yahoo Finance 或其他服务商凭证。
- API Key 仅通过环境变量或运行时设置输入。
- 后端响应会隐藏已配置的密钥。
- LLM 提示词不得包含服务商凭证。

## License / 许可

Private software. Internal use only.

私有软件，仅限内部使用。
