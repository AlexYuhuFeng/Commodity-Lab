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
  # Commodity Lab — Private (Internal Use Only)

  ![Private](https://img.shields.io/badge/Status-Private-red) ![Internal Use](https://img.shields.io/badge/Access-Selected%20Individuals-orange)

  > NOTICE: This repository is proprietary and intended for use by authorized personnel only. Do not distribute or publish.

  --

  <!-- Navigation (simple tab-like anchors) -->
  [Overview](#overview) • [Getting Started](#getting-started) • [Usage](#usage) • [Documentation](#documentation) • [Support & Access](#support--access)

  ---

  ## Overview

  Commodity Lab is an internal commodity data analytics platform for selected teams. It provides data ingestion, quality control, feature engineering, backtesting, and monitoring. All access is restricted; do not clone or share outside authorized groups.

  Key highlights:
  - Streamlit-based UI for quick inspection and management
  - DuckDB for local, lightweight analytics
  - Alerting system and backtest support

  ## Getting Started

  ### Requirements
  - Python 3.12+
  - Access to internal data feeds and credentials (not provided here)

  ### Quick install
  ```bash
  git clone <internal-repo-url>
  cd Commodity-Lab
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

  ### Run the app (local test)
  ```bash
  streamlit run app/main.py
  ```

  ## Usage

  Navigate the app using the sidebar. Primary pages:
  - Data Management — search & ingest
  - Data Showcase — product detail (multi-tab view)
  - Monitoring & Alerts — create and test rules
  - Analytics & Backtest — advanced features (internal)

  ## Documentation

  Use the links below to jump to detailed sections.

  - [Data Management](#data-management)
  - [Data Showcase (Tabs)](#data-showcase-tabs)
  - [Monitoring & Alerts](#monitoring--alerts)
  - [Developer Notes](#developer-notes)

  ### Data Management
  - Database: DuckDB at `data/commodity_lab.duckdb`
  - Tables: `instruments`, `prices_daily`, `derived_daily`, `alert_rules`, `alert_events`, etc.

  ### Data Showcase (Tabs)
  The product detail UI presents multiple tabs: Overview, Price Chart, QC, Attributes, Derived Series, Actions. These are accessible in the Streamlit UI and are not separate files.

  ### Monitoring & Alerts
  - Seven built-in rule types (price threshold, z-score, volatility, staleness, missing data, correlation break, custom expressions)
  - Rules can be tested and toggled in-app

  ### Developer Notes
  - Core modules live under `core/` (db, qc, transforms, refresh, yf_provider)
  - UI pages are under `app/pages/`
  - To add an alert type: update `app/pages/3_MonitoringAlerts.py` and i18n entries

  ## Support & Access

  If you need access or support, contact the internal dev team. Do not open public issues.

  - Primary contact: Commodity Lab Development Team (internal)
  - Docs: [UI_REDESIGN_GUIDE.md](UI_REDESIGN_GUIDE.md)

  ## License & Distribution

  Proprietary — Internal Use Only. Redistribution, public posting, or open-sourcing is prohibited.

  ## Changelog

  - v1.0 — Internal release; UI refactor and core features (2026-02-25)

  ---

  If you want the README to mimic VS Code extension pages even more closely (interactive tabs or marketplace-style layout), I can create an HTML/CSS-based tabbed layout inside this README or produce a separate `README.ext.md` optimized for internal docs hosting. Which would you prefer? 