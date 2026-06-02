# Commodity Lab — 私有（仅限内部使用）

  ![Private](https://img.shields.io/badge/Status-Private-red) ![Internal Use](https://img.shields.io/badge/Access-Selected%20Individuals-orange)

  > 注意：该仓库为专有代码，仅限授权人员使用。请勿分发或公开发布。

  --

  <!-- 导航 -->
  [概述](#概述) • [快速开始](#快速开始) • [使用说明](#使用说明) • [文档](#文档) • [支持与访问](#支持与访问)

  ---

  ## 概述

Hedge Lab Terminal 是一个面向内部团队的商品对冲学习工作空间，提供合约发现、虚拟对冲模拟和 AI 反馈。应用可使用 Yahoo Finance 或 Platts 的真实行情数据。所有访问权限受限，未经授权请勿克隆或分享。

主要亮点：
- 基于 Streamlit 的 Windows 风格终端 UI，用于对冲训练
- 使用 DuckDB 存储本地观察合约和价格历史
- 虚拟订单模拟与盈亏回测
- 侧边栏持久 AI 助手，提供对冲指导、问题解答和提示建议

  ## 快速开始

  ### 要求
  - Python 3.12+
  - 访问内部数据源和凭证（本仓库中不提供）

  ### 快速安装
  ```bash
  git clone <internal-repo-url>
  cd Commodity-Lab
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

  ### 本地运行应用
  ```bash
  streamlit run app/main.py
  ```

  ### 桌面终端启动
  ```bash
  python app/desktop_launcher.py
  ```

  ### 使用 NSIS 构建 Windows 安装包
  ```bash
  bash build_nsis.sh
  ```

  ### 构建 Linux DEB 安装包
  ```bash
  bash build_deb.sh --clean
  ```

  ## 使用说明

  通过侧边栏导航应用。主要模块：
  - Welcome — 快速终端引导
  - Market Explorer — 从 Yahoo Finance 或 Platts 搜索并导入合约
  - Hedge Simulator — 下虚拟对冲单并查看模拟盈亏
  - AI Assistant — 持久侧边栏教练，用于对冲问题、指导和提示
  - Practice — 各类对冲场景练习题
  - Settings — 配置 Platts 和 DEEPSEEK 凭证

  ## 文档

  本仓库当前聚焦于虚拟对冲训练。

  - `data/commodity_lab.duckdb` 存储已关注合约和历史行情
  - `core/data_source.py` 将行情查询路由到 Yahoo Finance 或 Platts
  - `core/hedge.py` 包含虚拟订单模拟和盈亏计算
  - `core/deepseek.py` 集成 DEEPSEEK AI 反馈
  - UI 页面位于 `app/pages/`

  ### 开发人员说明
  - 核心模块位于 `core/`
  - UI 页面位于 `app/pages/`
  - 应用入口为 `app/main.py`，并使用终端风格 Streamlit 主题

  ## 支持与访问

  如果需要访问或支持，请联系内部开发团队。请勿创建公共 issue。

  - 主要联系人：Commodity Lab 开发团队（内部）
  - 文档： [UI_REDESIGN_GUIDE.md](UI_REDESIGN_GUIDE.md)

  ## 许可与分发

  专有软件——仅限内部使用。禁止重新分发、公开发布或开源。

  ## 更新日志

  - v1.0 — 内部发布；UI 重构与核心功能（2026-02-25）

## CI/CD 与发布

- CI 工作流（`.github/workflows/ci.yml`）在推送/PR 到 `main` 时运行测试。
- 构建与发布工作流（`.github/workflows/build-and-release.yml`）在 GitHub 上执行测试 → 构建 → 发布。
- 当前发布产物包括：
  - Windows：`Commodity-Lab.exe`、`Commodity-Lab-windows-x64.zip`
  - Linux：`commodity-lab_0.9.0-preview_amd64.deb`
  - macOS：`Commodity-Lab-macos.dmg`
- `main` 更新时会自动发布滚动预发布版本（`nightly-latest`）。
- 打标签发布时（`v*.*.*`），会自动创建版本发布。


## 自动策略操作

- `Auto Strategy Lab` 提供策略族参数搜索，并将每次运行结果存储在数据库表 `strategy_runs` 中。
- 包括候选排行榜和风险调整评分（收益、Sharpe、胜率、回撤惩罚）。
- 旨在为交易工作流提供持续的思路生成；部署前建议结合监控规则。
- 应用内可检测硬件加速就绪状态（Numba/CuPy），以支持重度计算场景。


## 项目结构

- `app/` — Streamlit UI 入口（`app/main.py`）和页面模块（`app/pages/`）
- `core/` — 数据访问、指标/策略逻辑、回测、调度/监控工具
- `tests/` — pytest 核心行为测试用例
- `.github/workflows/` — GitHub CI/CD 管道
- `scripts/` — 实用/示例脚本
- `reports/` — 生成的演示输出
