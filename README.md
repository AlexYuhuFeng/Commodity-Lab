# Commodity Lab

Commodity Lab is a private desktop learning platform for commodity trading skills. V1 focuses on natural gas hedging: learners inspect market and pipeline-capacity context, place simulated hedge orders, receive deterministic scoring, and get live coaching from a user-provided 海能-compatible LLM endpoint.

Commodity Lab 是一个私有桌面端商品交易学习平台。V1 聚焦天然气套期保值训练：学习者可以查看市场与管道运力环境、提交模拟套保订单、获得确定性评分，并通过用户自备的海能兼容 LLM 端点获得实时辅导。

![Status](https://img.shields.io/badge/status-V1%20active-1f6feb)
![Desktop](https://img.shields.io/badge/client-Windows-2563eb)
![Data](https://img.shields.io/badge/data-Platts%20%7C%20Yahoo%20Finance%20%7C%20Simulated-0f766e)

## Overview / 项目概览

Commodity Lab is designed as a modern, terminal-like training client rather than a static course. The app combines structured scenarios, market data, pipeline-capacity visuals, simulated order placement, and LLM-driven feedback.

Commodity Lab 的目标不是静态课程，而是现代化、交易终端风格的训练客户端。应用将结构化场景、市场数据、管道运力图示、模拟下单和 LLM 驱动反馈结合在一起。

V1 includes:

- Natural gas hedging scenarios only.
- Pipeline capacity and congestion context.
- Simulated hedge order tickets.
- Deterministic hedge metrics and scoring.
- 海能 advisor hints, action review, and exam generation.
- English and Mandarin UI.
- Data source labels: `Platts`, `Yahoo Finance`, `Simulated`.
- Future commodity modules visible as `Constructing`.

V1 包含：

- 仅天然气套保训练场景。
- 管道运力与拥堵环境。
- 模拟套保订单票据。
- 确定性套保指标与评分。
- 海能顾问提示、操作复盘与测验生成。
- 英文与中文界面。
- 数据来源标记：`Platts`、`Yahoo Finance`、`Simulated`。
- 其他商品模块保持可见，并显示为 `Constructing`。

## Architecture / 技术架构

```text
Commodity Lab
├── core/                         Python domain logic
│   ├── gas_scenarios.py          Natural gas scenarios and sample data
│   ├── learning_session.py       Attempt evaluation and scoring helpers
│   └── haineng_client.py         OpenAI-compatible 海能 client
├── tauri/backend/                FastAPI backend for the desktop client
├── tauri/tauri-frontend/         React + Vite frontend
├── tauri/src-tauri/              Tauri Rust shell and backend bridge
└── tests/                        Python and frontend regression tests
```

```text
Commodity Lab
├── core/                         Python 领域逻辑
│   ├── gas_scenarios.py          天然气场景与样例数据
│   ├── learning_session.py       训练尝试评估与评分辅助逻辑
│   └── haineng_client.py         OpenAI 兼容的海能客户端
├── tauri/backend/                桌面客户端使用的 FastAPI 后端
├── tauri/tauri-frontend/         React + Vite 前端
├── tauri/src-tauri/              Tauri Rust 外壳与后端桥接
└── tests/                        Python 与前端回归测试
```

## Requirements / 环境要求

- Python 3.12+
- Node.js 20+
- Rust stable
- Windows for desktop packaging
- User-provided 海能-compatible LLM API key and base URL
- Optional user-provided Platts credentials

环境要求：

- Python 3.12+
- Node.js 20+
- Rust stable
- Windows 桌面端打包环境
- 用户自备海能兼容 LLM API Key 与 Base URL
- 可选的用户自备 Platts 凭证

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

海能:

- `HAINENG_API_KEY`
- `HAINENG_BASE_URL`
- `HAINENG_MODEL` defaults to `V4-Flash`

Platts:

- `PLATTS_API_KEY`
- `PLATTS_KEY`
- `SPGLOBAL_API_KEY`
- `SP_GLOBAL_API_KEY`

If Platts is unavailable, Commodity Lab can use Yahoo Finance or simulated sample data where available.

如果 Platts 不可用，Commodity Lab 可在可用场景下使用 Yahoo Finance 或模拟样例数据。

## Windows Packaging / Windows 打包

Commodity Lab V1 generates Windows desktop client artifacts only.

Commodity Lab V1 仅生成 Windows 桌面客户端产物。

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

## Release / 发布

GitHub Actions workflow:

GitHub Actions 工作流：

```text
.github/workflows/tauri-build.yml
```

Create a release tag:

创建发布标签：

```powershell
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

Manual workflow runs produce downloadable Windows artifacts. Tag pushes also publish a GitHub Release.

手动运行工作流会生成可下载的 Windows 产物。推送版本标签时还会创建 GitHub Release。

## License / 许可

Private software. Internal use only.

私有软件，仅限内部使用。
