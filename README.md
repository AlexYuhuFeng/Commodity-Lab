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
- Getting Started Guide — onboarding for new users

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

## CI/CD & Release

- CI executes tests on each push/PR to `main`.
- Build & Release workflow creates cross-platform executables for Linux/macOS/Windows.
- On `main` updates, a rolling prerelease (`nightly-latest`) is updated with latest artifacts and release notes.
- On version tags (`v*.*.*`), a versioned release is created automatically.
