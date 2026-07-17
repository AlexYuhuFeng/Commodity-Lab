# Commodity Lab

![Status](https://img.shields.io/badge/status-V1%20active-1f6feb)
![Client](https://img.shields.io/badge/client-Windows-2563eb)
![Focus](https://img.shields.io/badge/focus-natural%20gas-0f766e)
![AI](https://img.shields.io/badge/AI-Haineng%20%2F%20DeepSeek-7c3aed)

Commodity Lab is an AI-driven desktop learning platform for commodity trading and hedging. It combines a stable curriculum with live-market integration contracts, point-in-time historical replays, deterministic simulated markets, generated multi-leg decisions, immediate local scoring, and adaptive AI coaching. Natural gas is the primary learning path; crude-oil hedging is now included as an active expansion track.

Commodity Lab 是一个 AI 驱动的大宗商品交易与金融工具学习平台。产品以稳定课程框架为基础，结合实盘行情接入契约、分时点历史复盘、可复现模拟市场、组合套保决策、本地即时评分和自适应 AI 教练。天然气是当前主学习路径，原油套保已作为扩展课程纳入。

## Current Scope / 当前范围

Natural gas remains the primary path. Crude oil adds cargo, Brent/WTI/Dubai benchmark, calendar/basis, inventory, and freight hedging. Other commodities remain roadmap items and do not occupy the primary interface.

天然气仍是主学习路径；原油课程覆盖船货、Brent/WTI/Dubai 基准、月差/基差、库存与运费套保。其他商品保留在路线图中，不占用主界面的核心空间。

Business workflows:

- Procurement: upstream beach delivery GSA, exchange or OCM execution window, LNG cargo, bilateral EFET with NBP or beach delivery.
- Sales: bilateral EFET, exchange window sales, LNG regas sale, and related hub/basis exposure.
- Knowledge points: outright hedge, basis and hub spread, FX hedge, physical-paper matching, capacity constraint, volatility response, execution and risk-control checks.

业务流程：

- 采购端：上游 beach delivery GSA、交易所或 OCM 窗口、LNG 船货、NBP 或 beach delivery 双边 EFET。
- 销售端：双边 EFET、窗口销售、LNG 船货气化销售，以及相关枢纽/基差敞口。
- 知识点：单边价格套保、基差与枢纽价差、汇率套保、实货与纸货匹配、运力约束、剧烈波动应对、执行与风控检查。

## Market Evidence / 市场依据

Every training session explicitly uses one market mode: entitled live data, point-in-time historical replay, or an AI-simulated market. The current repository contains the unified evidence contract, deterministic gas/crude simulation, replay support, and a Platts capability adapter contract. Production live Platts retrieval still requires the user's subscription, entitlements, credential flow, symbol mapping, and licensing review.

每个训练会话都会明确使用一种市场模式：已授权实盘数据、分时点历史复盘或 AI 模拟市场。当前代码已包含统一市场依据契约、天然气/原油可复现模拟、历史复盘支持和 Platts 接入能力契约；生产级 Platts 实盘拉取仍需要用户订阅、授权、凭证流程、代码映射和许可审查。

## AI Providers / AI 供应方

The desktop client supports two runtime provider profiles:

- Haineng: shown as `海能` in Chinese UI and `Haineng` in English UI.
- DeepSeek: available as a separate fallback/testing provider profile.

Users only choose the provider profile and provide an API key in the app settings. Commodity Lab fixes the endpoint and model internally: Haineng uses the current V4 Flash route, and DeepSeek uses its Flash route. Credentials are runtime-only and must not be committed to the repository.

For test distribution, provide users with a local `AI密钥` file instead of asking them to type keys manually. The Windows client can import this file from any folder through the lower-left Settings menu. See [docs/key-file-import.md](docs/key-file-import.md) for safe JSON and key-value templates.

桌面端支持两套运行时供应方配置：

- 海能：中文界面显示为 `海能`，英文界面显示为 `Haineng`。
- DeepSeek：作为独立的备用/测试供应方配置。

用户在软件设置里只需要选择供应方并填写 API Key；模型和地址由 Commodity Lab 在程序内固定匹配。凭证只用于本地运行，禁止提交到仓库。

测试分发时，可以给用户提供本机 `AI密钥` 文件，不需要用户手动输入密钥。Windows 客户端支持从左下角设置菜单导入任意位置的密钥文件。安全模板见 [docs/key-file-import.md](docs/key-file-import.md)。

## Product Loop / 产品流程

1. State the skill or business decision to practise.
2. Choose simulated, historical replay, or entitled live market evidence.
3. AI generates a concrete case, events, expected hedge legs, and rubric around that evidence.
4. Inspect spot history, forward structure, high/low/close values, and event markers.
5. Build a multi-leg strategy: physical, swap, future, basis, FX, capacity, freight, or options.
6. Submit for immediate local scoring and receive a concise AI review.

1. 用自然语言说明希望训练的技能或业务决策。
2. 选择模拟市场、历史复盘或已授权实盘市场依据。
3. AI 围绕该市场依据生成案例、事件、目标动作和评分规则。
4. 查看历史价格、远期结构、high/low/close 与事件标记。
5. 构建实货、掉期、期货、基差、汇率、运力、运费或期权组合。
6. 提交后立即本地评分，并获得简洁的 AI 复盘。

## Key Features / 核心功能

- Windowed Windows desktop client with a Codex-inspired native app shell.
- Bilingual UI: Mandarin by default, English available in settings.
- Settings menu for API provider, key-file import, language, light/dark/system theme, developer info, version info, and update checks.
- First-run guided overlay with visual highlights.
- Floating AI assistant with Markdown rendering and safe action cards.
- AI thinking and action progress states so long responses do not feel frozen.
- Local deterministic scoring from generated target actions and rubrics.
- Professional multi-series chart for hub curves, high/low/close values, events, and strategy-leg overlays.

- Windows 桌面客户端，窗口化启动，采用参考 Codex Windows 客户端的原生软件外壳体验。
- 双语界面：默认中文，可在设置切换英文。
- 设置菜单集中管理 API 供应方、密钥文件导入、语言、日间/夜间/跟随系统主题、开发者信息、版本信息和更新检查。
- 首次启动提供蒙版高亮式引导。
- 悬浮 AI 助手支持 Markdown 显示和安全动作卡。
- AI 思考与动作进度可视化，避免等待时卡顿无反馈。
- 根据生成的目标动作和评分规则进行本地确定性评分。
- 专业多曲线图表展示枢纽曲线、high/low/close、事件和策略腿叠加。

## Project Structure / 项目结构

```text
Commodity-Lab
├── core/
│   ├── training_templates.py      Gas business workflow templates
│   ├── gas_scenarios.py          AI-generated gas fixture catalog and offline training context
│   ├── market_learning.py        Market regimes, provenance, and historical replay packs
│   ├── learning_session.py       Deterministic scoring helpers
│   └── haineng_client.py         Haineng / DeepSeek compatible AI client and prompts
├── tauri/
│   ├── backend/                  FastAPI backend used by the desktop client
│   ├── tauri-frontend/           React + Vite frontend
│   ├── src-tauri/                Tauri Windows shell
│   └── scripts/                  Packaging scripts
├── tests/                        Python regression tests
└── docs/                         Architecture and roadmap notes
```

## Local Development / 本地开发

Python:

```powershell
python -m pip install -r requirements.txt
python -m pytest
```

Frontend:

```powershell
cd tauri\tauri-frontend
npm install
npm test
npm run build
```

Backend:

```powershell
uvicorn tauri.backend.main:app --host 127.0.0.1 --port 8000
```

Windows client:

```powershell
cd tauri
npm install
npm run tauri:build
```

Formal Windows release:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\release_windows.ps1 -Version 1.2.1
```

The release script runs frontend tests, backend tests, production build, npm audit, backend executable rebuild, Tauri Windows packaging, local installer execution, and GitHub release publishing with bilingual release notes.

正式 Windows 发布：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\release_windows.ps1 -Version 1.2.1
```

该脚本会依次执行前端测试、后端测试、生产构建、npm audit、后端可执行文件重建、Tauri Windows 打包、本机安装和带中英文说明的 GitHub release 发布。

## Runtime Configuration / 运行配置

Environment variables are optional because the desktop settings screen can configure providers at runtime.

```powershell
$env:COMMODITY_LAB_AI_PROVIDER="haineng"   # or deepseek
$env:HAINENG_API_KEY="<local key>"
# HAINENG_BASE_URL and HAINENG_MODEL are optional legacy hints.
# Runtime provider endpoint and model are fixed by Commodity Lab.
```

可选环境变量：

```powershell
$env:COMMODITY_LAB_AI_PROVIDER="haineng"   # 或 deepseek
$env:HAINENG_API_KEY="<本地密钥>"
# HAINENG_BASE_URL 与 HAINENG_MODEL 仅作为兼容旧脚本的可选提示。
# 实际运行地址与模型由 Commodity Lab 固定匹配。
```

## Developer Info / 开发者信息

- Organization: Natural Gas Center
- Project lead: Yang Min

- 组织：天然气中心
- 项目负责人：杨敏

## Security / 安全

- Do not commit API keys, local provider URLs that include credentials, certificates, or generated release artifacts.
- The app must redact provider credentials in health checks, logs, tests, release notes, and screenshots.
- AI-generated curves are training artifacts, not price advice or live market data.

- 不要提交 API Key、带凭证的本地服务地址、证书或构建产物。
- 健康检查、日志、测试、release notes 和截图中必须隐藏供应方凭证。
- AI 生成曲线是训练材料，不构成价格建议或实时市场数据。
