# Commodity Lab

![Status](https://img.shields.io/badge/status-V1%20active-1f6feb)
![Clients](https://img.shields.io/badge/clients-Windows%20%7C%20Linux-2563eb)
![Courses](https://img.shields.io/badge/courses-European%20gas%20%7C%20crude%20oil-0f766e)
![AI](https://img.shields.io/badge/AI-Haineng%20%2F%20DeepSeek-7c3aed)

Commodity Lab is an AI-driven desktop learning platform for commodity trading and hedging. It combines a shared financial-tool curriculum with product-specific workspaces, live-market integration contracts, point-in-time historical replays, generated multi-leg decisions, immediate local scoring, and adaptive AI coaching. European natural gas and crude oil are the current reviewed course tracks.

Commodity Lab 是一个 AI 驱动的大宗商品交易与金融工具学习平台。产品由跨品种金融工具通识和单品种工作区组成，结合实盘行情接入契约、分时点历史复盘、组合套保决策、本地即时评分和自适应 AI 教练。当前经审阅的正式课程为欧洲天然气和原油。

## Current Scope / 当前范围

Every learner starts from the same general hedging outcomes, then studies one product workspace. European natural gas covers physical supply, EFET/EEX/OCM, LNG, hubs, capacity, storage, FX, and integrated hedges. Crude oil covers cargoes, Brent/WTI/Dubai benchmarks, calendar/grade/location basis, inventory, and freight. North American Gas, Refined Products, Power, and Carbon are selectable scaffolds only: they contain no placeholder lessons or fake progress.

所有学习者先覆盖同一套套保通识，再进入一个单品种工作区。欧洲天然气课程覆盖实货资源、EFET/EEX/OCM、LNG、枢纽、运力、储气、汇率和组合套保；原油课程覆盖船货、Brent/WTI/Dubai 基准、月差/品级/地点基差、库存与运费。北美天然气、成品油、电力与碳目前仅提供可选择的产品架构，不展示占位课程或虚假进度。

Business workflows:

- Procurement: upstream beach delivery GSA, exchange or OCM execution window, LNG cargo, bilateral EFET with NBP or beach delivery.
- Sales: bilateral EFET, exchange window sales, LNG regas sale, and related hub/basis exposure.
- Knowledge points: outright hedge, basis and hub spread, FX hedge, physical-paper matching, capacity constraint, volatility response, execution and risk-control checks.

业务流程：

- 采购端：上游 beach delivery GSA、交易所或 OCM 窗口、LNG 船货、NBP 或 beach delivery 双边 EFET。
- 销售端：双边 EFET、窗口销售、LNG 船货气化销售，以及相关枢纽/基差敞口。
- 知识点：单边价格套保、基差与枢纽价差、汇率套保、实货与纸货匹配、运力约束、剧烈波动应对、执行与风控检查。

## Market Evidence / 市场依据

Every training session explicitly uses one market mode: entitled live data, point-in-time historical replay, or an AI-simulated market. The repository includes a Platts REST adapter for entitled current-symbol assessments, customer-owned symbol mapping, normalized local caching, stale-data handling, and explicit simulation fallback. The live forward curve and locally calibrated chart history remain separately labelled. Production use still requires the customer's subscription, entitlements, approved symbols, and licensing review.

每个训练会话都会明确使用一种市场模式：已授权实盘数据、分时点历史复盘或 AI 模拟市场。代码已实现 Platts REST 适配器、客户自有品种代码映射、标准化本地缓存、过期处理和明示模拟回退；授权远期曲线与本地校准历史路径会分开标记。生产使用仍需要客户订阅、数据权限、核准代码和许可审查。

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

- Windowed Windows and Linux desktop clients with a Codex-inspired native app shell.
- Bilingual UI: Mandarin by default, English available in settings.
- Settings menu for API provider, key-file import, language, light/dark/system theme, developer info, version info, and update checks.
- First-run guided overlay with visual highlights.
- Floating AI assistant with Markdown rendering and safe action cards.
- A shared inter-commodity hedging curriculum plus a compact product workspace switch. European Natural Gas and Crude Oil are active; North American Gas, Refined Products, Power, and Carbon are honest selectable scaffolds with no placeholder learning data.
- Real token streaming and progressive workspace updates: market evidence appears first, generated scenario text follows, and the complete task/rubric lands last.
- Structured AI actions update the case, curves, chart fields, strategy, and learning route directly instead of only replying in chat.
- Local deterministic scoring from generated target actions and rubrics.
- Professional multi-series chart for hub curves, high/low/close values, events, and strategy-leg overlays.

- Windows 与 Linux 桌面客户端，窗口化启动，采用参考 Codex 客户端的原生软件外壳体验。
- 双语界面：默认中文，可在设置切换英文。
- 设置菜单集中管理 API 供应方、密钥文件导入、语言、日间/夜间/跟随系统主题、开发者信息、版本信息和更新检查。
- 首次启动提供蒙版高亮式引导。
- 悬浮 AI 助手支持 Markdown 显示和安全动作卡。
- 课程体系由跨品种套保通识与单一产品工作区组成；欧洲天然气和原油已开放，北美天然气、成品油、电力与碳为可进入但不展示占位内容的建设中架构。
- 真实 token 流式传输与渐进式工作台更新：先显示市场依据，再补充场景文字，最后落位完整任务与评分规则。
- 结构化 AI 动作可直接修改案例、曲线、图表字段、策略和学习路径，而不是只在聊天框中回复。
- 根据生成的目标动作和评分规则进行本地确定性评分。
- 专业多曲线图表展示枢纽曲线、high/low/close、事件和策略腿叠加。

## Project Structure / 项目结构

```text
Commodity-Lab
├── core/
│   ├── training_templates.py      Gas business workflow templates
│   ├── gas_scenarios.py          AI-generated gas fixture catalog and offline training context
│   ├── market_learning.py        Market regimes, provenance, and historical replay packs
│   ├── platts_market.py          Entitled REST adapter, symbol mapping, and normalized cache
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

Formal cross-platform release (run from a clean `main` checkout):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\release_windows.ps1 -Version 1.5.0
```

The script qualifies and installs the Windows build locally, then pushes `v1.5.0`. GitHub Actions builds Windows x86_64, Linux x86_64, and Linux ARM64 natively and publishes one release with bilingual notes. Use `-SkipReleaseTag` for local Windows qualification without triggering a public release.

正式跨平台发布（必须在干净的 `main` 分支运行）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tauri\scripts\release_windows.ps1 -Version 1.5.0
```

该脚本先在本机完成 Windows 测试、审计、打包和安装验证，再推送 `v1.5.0` 标签。GitHub Actions 会分别原生构建 Windows x86_64、Linux x86_64 和 Linux ARM64，并统一发布带中英文说明的 Release。仅做本机 Windows 验证时使用 `-SkipReleaseTag`。

## Runtime Configuration / 运行配置

Environment variables are optional because the desktop settings screen can configure providers at runtime.

```powershell
$env:COMMODITY_LAB_AI_PROVIDER="haineng"   # or deepseek
$env:HAINENG_API_KEY="<local key>"
# HAINENG_BASE_URL and HAINENG_MODEL are optional legacy hints.
# Runtime provider endpoint and model are fixed by Commodity Lab.
```

For entitled Platts REST delivery, keep credentials and customer symbol mappings outside Git. Copy the example mapping to a controlled local path, replace only the placeholder symbols with codes included in the customer's entitlement, and set:

```powershell
$env:COMMODITY_LAB_PLATTS_AUTH_MODE="oauth_password"
$env:COMMODITY_LAB_PLATTS_USERNAME="<subscription username>"
$env:COMMODITY_LAB_PLATTS_PASSWORD="<subscription password>"
$env:COMMODITY_LAB_PLATTS_SYMBOL_MAP="C:\secure\platts-symbol-map.json"
```

`COMMODITY_LAB_PLATTS_ACCESS_TOKEN` can be used instead for a short-lived bearer token. The cache stores only Commodity Lab's normalized evidence snapshot, not the raw licensed response. See [`config/platts-symbol-map.example.json`](config/platts-symbol-map.example.json) and [S&P Global Energy API Getting Started](https://developer.spglobal.com/energy/delivery-solutions/api/getting-started).

可选环境变量：

```powershell
$env:COMMODITY_LAB_AI_PROVIDER="haineng"   # 或 deepseek
$env:HAINENG_API_KEY="<本地密钥>"
# HAINENG_BASE_URL 与 HAINENG_MODEL 仅作为兼容旧脚本的可选提示。
# 实际运行地址与模型由 Commodity Lab 固定匹配。
```

如需接入已授权 Platts REST 行情，请把凭证和客户代码映射保存在 Git 仓库之外。将示例映射复制到受控本地目录，只把占位代码替换成客户订阅权限内的代码，然后设置：

```powershell
$env:COMMODITY_LAB_PLATTS_AUTH_MODE="oauth_password"
$env:COMMODITY_LAB_PLATTS_USERNAME="<订阅用户名>"
$env:COMMODITY_LAB_PLATTS_PASSWORD="<订阅密码>"
$env:COMMODITY_LAB_PLATTS_SYMBOL_MAP="C:\secure\platts-symbol-map.json"
```

也可通过 `COMMODITY_LAB_PLATTS_ACCESS_TOKEN` 使用短期 bearer token。本地缓存只保存 Commodity Lab 标准化后的市场证据快照，不保存供应方原始授权响应。

## Developer Info / 开发者信息

- Organization: Natural Gas Center
- Project lead: Yang Min

- 组织：天然气中心
- 项目负责人：杨敏

## Security / 安全

- Do not commit API keys, local provider URLs that include credentials, certificates, or generated release artifacts.
- The app must redact provider credentials in health checks, logs, tests, release notes, and screenshots.
- AI-generated curves are training artifacts, not price advice or live market data.
- Raw licensed Platts payloads and customer symbol maps must remain outside the repository.

- 不要提交 API Key、带凭证的本地服务地址、证书或构建产物。
- 健康检查、日志、测试、release notes 和截图中必须隐藏供应方凭证。
- AI 生成曲线是训练材料，不构成价格建议或实时市场数据。
- Platts 原始授权响应和客户品种代码映射不得进入仓库。
