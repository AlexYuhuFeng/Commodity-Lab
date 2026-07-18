import React, { useEffect, useMemo, useRef, useState } from "react";
import { backendRequest, backendStreamRequest } from "./api";
import { normalizeLocale, t } from "./i18n";

const currentVersion = "1.5.1";

const defaultProviderCatalog = {
  haineng: {
    label: "Haineng",
    default_model: "DeepSeek-V4-Flash",
    models: [
      {
        id: "DeepSeek-V4-Flash",
        label: "DeepSeek-V4-Flash",
        resolved_model: "DeepSeek-V4-Flash",
        base_url: "http://model.ai.cnooc/member1/deepseek-v4-flash-291b-1m/v1"
      },
      {
        id: "DeepSeek-V4",
        label: "DeepSeek-V4",
        resolved_model: "DeepSeek-V4",
        base_url: "http://model.ai.cnooc/member1/deepseek-v4-pro-1-5t/v1"
      }
    ]
  },
  deepseek: {
    label: "DeepSeek",
    default_model: "deepseek-v4-flash",
    models: [
      { id: "deepseek-v4-flash", label: "deepseek-v4-flash", resolved_model: "deepseek-v4-flash", base_url: "https://api.deepseek.com" },
      { id: "deepseek-v4-pro", label: "deepseek-v4-pro", resolved_model: "deepseek-v4-pro", base_url: "https://api.deepseek.com" }
    ]
  }
};

function fallbackMarketCapabilities(locale = "en") {
  return {
    modes: [
      {
        id: "ai_simulated",
        label: copy(locale, "AI 模拟市场", "AI-simulated market"),
        description: copy(locale, "本地数值引擎生成一致曲线，DeepSeek 负责业务情景与教学编排。", "A local numeric engine generates coherent curves while DeepSeek composes the business and lesson.")
      },
      {
        id: "historical_replay",
        label: copy(locale, "历史事件复盘", "Historical replay"),
        description: copy(locale, "只显示当时可知信息，提交决策后再揭示后续市场。", "Only information available at the time is shown; later outcomes are revealed after a decision.")
      },
      {
        id: "live",
        label: copy(locale, "实盘市场", "Live market"),
        description: copy(locale, "通过机构订阅接入真实评估价、曲线和市场元数据。", "Use entitled assessments, curves, and market metadata through an institutional subscription.")
      }
    ],
    providers: [
      {
        id: "platts",
        label: "S&P Global Commodity Insights (Platts)",
        status: "not_configured",
        integration_state: "rest_adapter_ready",
        requires_subscription: true
      }
    ],
    fallback_mode: "ai_simulated",
    replays: [
      {
        id: "hormuz_2026_disruption",
        commodity: "crude_oil",
        title: copy(locale, "2026 霍尔木兹海峡供应冲击复盘", "2026 Strait of Hormuz supply-shock replay"),
        summary: copy(locale, "从炼厂采购和原油贸易视角管理实货、Brent 纸货、月差、运费和可选性。", "Manage physical cargo, Brent paper, calendar spread, freight, and optionality as information is revealed."),
        checkpoint_count: 3
      },
      {
        id: "european_gas_crisis_2022",
        commodity: "natural_gas",
        title: copy(locale, "2022 欧洲天然气危机与 LNG 拥堵复盘", "2022 European gas crisis and LNG-congestion replay"),
        summary: copy(locale, "经历供应收紧、TTF 极端上涨和高库存/LNG 拥堵，连续调整实货与纸货。", "Move through supply tightening, the TTF spike, and high-storage/LNG congestion while adjusting physical and paper coverage."),
        checkpoint_count: 3
      },
      {
        id: "european_gas_refill_squeeze_2021",
        commodity: "natural_gas",
        title: copy(locale, "2021 欧洲储气补库与全球 LNG 竞争复盘", "2021 European storage-refill and global LNG competition replay"),
        summary: copy(locale, "经历低库存、补库竞争和高价入冬，管理 TTF、区域基差、LNG 与储气。", "Manage TTF, regional basis, LNG, and storage through low inventories, refill competition, and a high-price winter entry."),
        checkpoint_count: 3
      },
      {
        id: "wti_storage_squeeze_2020",
        commodity: "crude_oil",
        title: copy(locale, "2020 WTI 库容与交割挤压复盘", "2020 WTI storage and delivery squeeze replay"),
        summary: copy(locale, "经历需求骤降、Cushing 库容紧张和近月负价，管理实货、纸货、月差与交割。", "Manage physical flows, paper, calendar spreads, and delivery through demand collapse, tight Cushing storage, and negative prompt prices."),
        checkpoint_count: 3
      }
    ]
  };
}

const chartFields = ["close", "high", "low"];

const startupStageKeys = ["startupBackend", "startupAiRuntime", "startupWorkbench", "startupFinalizing"];
const themeModes = ["system", "light", "dark"];

const guideSteps = [
  ["settings-menu", "guideSettingsTitle", "guideSettingsBody"],
  ["case-lab", "guideBusinessTitle", "guideBusinessBody"],
  ["case-workspace", "guideCaseTitle", "guideCaseBody"],
  ["market-chart", "guideChartTitle", "guideChartBody"],
  ["strategy-builder", "guideStrategyTitle", "guideStrategyBody"],
  ["floating-assistant", "guideAssistantTitle", "guideAssistantBody"]
];

const pageIds = {
  home: "home",
  caseLab: "case-lab",
  workbench: "workbench",
  review: "review",
  library: "library",
  knowledge: "knowledge",
  progress: "progress",
  coach: "coach",
  settings: "settings"
};

function normalizeThemeMode(mode) {
  return themeModes.includes(mode) ? mode : "system";
}

function getSystemThemePreference() {
  if (typeof window === "undefined" || !window.matchMedia) return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

const navItems = [
  { id: pageIds.home, icon: "home", zh: "课程", en: "Courses" },
  { id: pageIds.library, icon: "library", zh: "练习库", en: "Practice Library" },
  { id: pageIds.workbench, icon: "workbench", zh: "训练台", en: "Workbench" },
  { id: pageIds.progress, icon: "progress", zh: "进度", en: "Progress" }
];

const learningTracks = [
  {
    id: "foundation",
    templateId: "foundation_hedging_basics",
    zh: "通识金融工具",
    en: "General Hedging Tools",
    levelZh: "从这里开始",
    levelEn: "Start here",
    detailZh: "跨品种学习敞口、远期结构、期货/掉期、基差、期权、套保比率和风控。",
    detailEn: "Learn exposure, forward structure, futures/swaps, basis, options, hedge ratios, and controls across commodities.",
    requestZh: "生成一个跨品种通用的套保基础训练案例，聚焦敞口识别、远期结构、工具选择、套保比率、实货/纸货匹配和执行风控。",
    requestEn: "Generate an inter-commodity general hedging drill focused on exposure, forward structure, instrument choice, hedge ratio, physical-paper matching, and execution controls.",
    lessons: ["敞口与目标", "远期结构", "期货/掉期", "基差", "期权", "套保比率", "执行风控"],
    lessonsEn: ["Exposure", "Forward structure", "Futures/swaps", "Basis", "Options", "Hedge ratio", "Controls"]
  },
  {
    id: "crude",
    templateId: "crude_oil_hedging_basics",
    zh: "原油套保入门",
    en: "Crude Oil Hedging",
    levelZh: "新增",
    levelEn: "New",
    detailZh: "学习 Brent/WTI/Dubai、实货船货、期货/掉期、月差/基差、库存和运费风险。",
    detailEn: "Learn Brent/WTI/Dubai, physical cargoes, futures/swaps, calendar and quality basis, inventory, and freight risk.",
    requestZh: "生成一个原油套保入门训练案例：围绕 Brent、WTI 或 Dubai 采购/销售敞口，训练实货合同、期货或掉期、月差/基差、库存和运费风险匹配。",
    requestEn: "Generate a beginner crude oil hedging drill around Brent, WTI, or Dubai procurement/sales exposure, training physical contracts, futures or swaps, calendar/basis spread, inventory, and freight risk matching.",
    lessons: ["三大基准", "实货/纸货", "月差/基差", "库存/运费"],
    lessonsEn: ["Benchmarks", "Physical/paper", "Calendar/basis", "Inventory/freight"]
  },
  {
    id: "gas_local",
    templateId: "gas_local_market_procurement",
    zh: "本地市场价格风险",
    en: "Local-Market Price Risk",
    levelZh: "第二阶段",
    levelEn: "Stage 2",
    detailZh: "在同一市场、同一币种内掌握采购成本和销售收入的基础套保。",
    detailEn: "Hedge procurement cost and sales revenue within one market and one currency.",
    requestZh: "生成一个欧洲天然气本地市场套保案例，只包含单一枢纽、单一币种和清晰的采购或销售价格敞口。",
    requestEn: "Generate a European gas local-market hedge with one hub, one currency, and a clear procurement or sales price exposure.",
    lessons: ["采购成本", "销售收入", "数量与期限"],
    lessonsEn: ["Procurement cost", "Sales revenue", "Volume and tenor"]
  },
  {
    id: "gas_basis",
    templateId: "procurement_beach_to_germany",
    zh: "跨区域与基差风险",
    en: "Cross-Regional and Basis Risk",
    levelZh: "第三阶段",
    levelEn: "Stage 3",
    detailZh: "从单一价格风险扩展到枢纽、交割地点、跨期和运输路径错配。",
    detailEn: "Extend outright hedging to hub, delivery-location, calendar, and route mismatches.",
    requestZh: "生成一个欧洲天然气跨区域供销案例，重点训练枢纽基差、交割地点和运输路径。",
    requestEn: "Generate a European gas cross-regional supply-and-sale case focused on hub basis, delivery point, and transport route.",
    lessons: ["枢纽基差", "交割地点", "跨期与运力"],
    lessonsEn: ["Hub basis", "Delivery point", "Calendar and capacity"]
  },
  {
    id: "gas_fx",
    templateId: "gas_cross_currency_settlement",
    zh: "跨币种与结算风险",
    en: "Cross-Currency and Settlement Risk",
    levelZh: "第四阶段",
    levelEn: "Stage 4",
    detailZh: "在商品套保之外管理计价币种、结算币种、本位币和单位换算。",
    detailEn: "Manage pricing, settlement, functional-currency, and unit-conversion risk alongside the commodity hedge.",
    requestZh: "生成一个欧洲天然气跨币种供销案例，要求先完成商品套保，再匹配外汇金额、方向和期限。",
    requestEn: "Generate a European gas cross-currency supply-and-sale case that first hedges the commodity and then matches FX amount, direction, and tenor.",
    lessons: ["交易与结算币种", "FX 方向", "金额与期限"],
    lessonsEn: ["Trade and settlement currency", "FX direction", "Amount and tenor"]
  },
  {
    id: "gas_integrated",
    templateId: "integrated_gas_portfolio",
    zh: "运力、可选性与组合策略",
    en: "Capacity, Optionality, and Integrated Strategy",
    levelZh: "第五阶段",
    levelEn: "Stage 5",
    detailZh: "综合实货、纸货、基差、汇率、运力、期权、信用和执行约束。",
    detailEn: "Combine physical, paper, basis, FX, capacity, options, credit, and execution constraints.",
    requestZh: "生成综合天然气套保训练案例：必须包含实货腿、纸货腿、汇率或运力检查，并要求用户解释每条腿覆盖的风险。",
    requestEn: "Generate an integrated natural gas hedging drill with a physical leg, paper leg, FX or capacity check, and a requirement to explain the risk covered by each leg.",
    lessons: ["运输与交付", "LNG 可选性", "组合执行", "风控复盘"],
    lessonsEn: ["Transport and delivery", "LNG optionality", "Portfolio execution", "Risk review"]
  }
];

const productWorkspaces = [
  { id: "natural_gas", zh: "欧洲天然气", en: "European Natural Gas", icon: "flame", trackIds: ["foundation", "gas_local", "gas_basis", "gas_fx", "gas_integrated"], groups: ["foundation", "procurement", "sales", "integrated"], enabled: true, coursesReady: true },
  { id: "crude_oil", zh: "原油", en: "Crude Oil", icon: "chart", trackIds: ["foundation", "crude"], groups: ["foundation", "crude"], enabled: true, coursesReady: true },
  { id: "north_american_gas", zh: "北美天然气", en: "North American Gas", icon: "flame", trackIds: ["foundation"], groups: ["foundation"], enabled: true, coursesReady: false, scopeZh: "Henry Hub、区域基差、储气、管输和电力燃料需求", scopeEn: "Henry Hub, regional basis, storage, pipelines, and power-burn demand" },
  { id: "refined_products", zh: "成品油", en: "Refined Products", icon: "library", trackIds: ["foundation"], groups: ["foundation"], enabled: true, coursesReady: false, scopeZh: "裂解价差、库存、炼厂产率、船货和质量基差", scopeEn: "Crack spreads, inventory, refinery yields, cargoes, and quality basis" },
  { id: "power", zh: "电力", en: "Power", icon: "pulse", trackIds: ["foundation"], groups: ["foundation"], enabled: true, coursesReady: false, scopeZh: "负荷、节点电价、燃料成本、峰谷和可再生波动", scopeEn: "Load, nodal prices, fuel cost, peak/off-peak, and renewable intermittency" },
  { id: "carbon", zh: "碳", en: "Carbon", icon: "grid", trackIds: ["foundation"], groups: ["foundation"], enabled: true, coursesReady: false, scopeZh: "配额、履约周期、能源价差、政策与跨期风险", scopeEn: "Allowances, compliance cycles, energy spreads, policy, and calendar risk" }
];

const generalCoverageIds = new Set([
  "exposure_objective",
  "forward_curve_carry",
  "outright_price",
  "physical_paper_matching",
  "basis_spread",
  "hedge_ratio_cross_hedge",
  "options_optionality",
  "fx",
  "risk_controls"
]);

function productWorkspace(productScope) {
  return productWorkspaces.find((item) => item.id === productScope) ?? productWorkspaces[0];
}

function tracksForProduct(productScope) {
  const allowed = new Set(productWorkspace(productScope).trackIds);
  return learningTracks.filter((track) => allowed.has(track.id));
}

function templatesForProduct(templates, productScope) {
  const allowed = new Set(productWorkspace(productScope).groups);
  return templates.filter((template) => allowed.has(template.group));
}

function coverageForProduct(productScope) {
  const productIds = productScope === "crude_oil"
    ? new Set(["crude_benchmark_basis", "inventory_freight_roll"])
    : new Set(["capacity_storage_balancing"]);
  return hedgingKnowledgeCoverage.filter((item) => generalCoverageIds.has(item.id) || productIds.has(item.id));
}

function modelsForProduct(productScope) {
  return gasTradingModels.filter((item) => productScope === "crude_oil"
    ? ["foundation", "crude"].includes(item.group)
    : item.group !== "crude");
}

function scenarioCommodityForProduct(productScope) {
  if (productScope === "crude_oil") return "crude-oil";
  if (["natural_gas", "north_american_gas"].includes(productScope)) return "natural-gas";
  return productScope.replaceAll("_", "-");
}

function productScopeForTemplate(templateId) {
  if (templateId === "foundation_hedging_basics") return "general";
  return String(templateId ?? "").includes("crude") ? "crude_oil" : "natural_gas";
}

function exposureDirectionLabel(direction, locale) {
  const labels = {
    long: { zh: "采购成本上涨", en: "Procurement cost upside" },
    inventory_long: { zh: "库存价格下跌", en: "Inventory price downside" },
    short: { zh: "销售价格下跌", en: "Sales price downside" },
    buy: { zh: "采购成本上涨", en: "Procurement cost upside" },
    sell: { zh: "销售价格下跌", en: "Sales price downside" },
    spread: { zh: "价差波动", en: "Spread movement" }
  };
  const item = labels[String(direction ?? "").toLowerCase()];
  return item ? labelFor(locale, item) : direction || "--";
}

const courseSyllabus = [
  {
    trackId: "foundation",
    lessons: [
      {
        id: "foundation-exposure",
        titleZh: "敞口识别",
        titleEn: "Exposure Recognition",
        outcomeZh: "判断采购、销售或价差敞口的方向、数量和期限。",
        outcomeEn: "Identify exposure direction, volume, and tenor for procurement, sales, or spread risk."
      },
      {
        id: "foundation-forward-curve",
        titleZh: "远期结构与持有成本",
        titleEn: "Forward Structure and Carry",
        outcomeZh: "识别 Contango、Backwardation、展期和持有成本如何改变套保。",
        outcomeEn: "Explain how contango, backwardation, roll, and carry change a hedge."
      },
      {
        id: "foundation-instruments",
        titleZh: "期货、远期与掉期",
        titleEn: "Futures, Forwards, and Swaps",
        outcomeZh: "比较标准化期货、场外远期与掉期的现金流、流动性和信用差异。",
        outcomeEn: "Compare cash flows, liquidity, and credit across futures, forwards, and swaps."
      },
      {
        id: "foundation-match",
        titleZh: "实货 / 纸货匹配",
        titleEn: "Physical / Paper Matching",
        outcomeZh: "把实货义务和纸货工具匹配成一组可解释的套保动作。",
        outcomeEn: "Match physical obligations and paper instruments into one explainable hedge package."
      },
      {
        id: "foundation-basis-ratio",
        titleZh: "基差、相关性与套保比率",
        titleEn: "Basis, Correlation, and Hedge Ratio",
        outcomeZh: "识别不完全匹配并按敏感度、相关性、数量和期限确定套保比例。",
        outcomeEn: "Size imperfect hedges using sensitivity, correlation, volume, and tenor."
      },
      {
        id: "foundation-options",
        titleZh: "期权与非线性保护",
        titleEn: "Options and Nonlinear Protection",
        outcomeZh: "理解 cap、floor、collar 和运营可选性的非对称损益。",
        outcomeEn: "Understand asymmetric payoffs from caps, floors, collars, and operational optionality."
      },
      {
        id: "foundation-controls",
        titleZh: "执行、保证金与风控",
        titleEn: "Execution, Margin, and Controls",
        outcomeZh: "在交易前检查流动性、保证金、信用、限额、结算和执行窗口。",
        outcomeEn: "Check liquidity, margin, credit, limits, settlement, and execution windows before trading."
      }
    ]
  },
  {
    trackId: "crude",
    lessons: [
      {
        id: "crude-benchmarks",
        titleZh: "Brent / WTI / Dubai 基准",
        titleEn: "Brent / WTI / Dubai Benchmarks",
        outcomeZh: "识别采购或销售敞口引用哪个基准，以及 API、硫含量、地点和交割月造成的差异。",
        outcomeEn: "Identify which benchmark drives the exposure and how API, sulfur, location, and delivery month create basis."
      },
      {
        id: "crude-physical-paper",
        titleZh: "船货实货与纸货匹配",
        titleEn: "Cargo Physical / Paper Matching",
        outcomeZh: "把实货船货、管输、库存或销售合同与 futures、swap、basis leg 匹配。",
        outcomeEn: "Match cargo, pipeline, inventory, or sales contracts with futures, swaps, and basis legs."
      },
      {
        id: "crude-calendar-basis",
        titleZh: "月差、品级和地点基差",
        titleEn: "Calendar, Grade, and Location Basis",
        outcomeZh: "拆分 flat price、月差、Brent/WTI 或 Dubai 价差、品级贴水和运费影响。",
        outcomeEn: "Separate flat price, calendar spread, Brent/WTI or Dubai spread, grade differential, and freight effects."
      },
      {
        id: "crude-controls",
        titleZh: "库存、运费与风控",
        titleEn: "Inventory, Freight, and Controls",
        outcomeZh: "检查库存周期、租船窗口、保证金、信用、限额和展期风险。",
        outcomeEn: "Check inventory cycle, chartering window, margin, credit, limits, and roll risk."
      }
    ]
  },
  {
    trackId: "gas_local",
    lessons: [
      {
        id: "gas-local-procurement",
        titleZh: "本地采购成本套保",
        titleEn: "Local Procurement Cost Hedge",
        outcomeZh: "识别同一枢纽、同一币种下的采购价格上涨风险，并匹配纸货方向。",
        outcomeEn: "Identify procurement-price upside in one hub and currency, then match the paper-hedge direction."
      },
      {
        id: "gas-local-sale",
        titleZh: "本地销售收入套保",
        titleEn: "Local Sales Revenue Hedge",
        outcomeZh: "识别销售价格下跌风险，并区分固定价、浮动价和公式价敞口。",
        outcomeEn: "Identify sales-price downside and distinguish fixed, floating, and formula-priced exposure."
      },
      {
        id: "gas-local-volume-tenor",
        titleZh: "数量与期限匹配",
        titleEn: "Volume and Tenor Matching",
        outcomeZh: "把合同数量、交割期和套保工具期限逐项对齐。",
        outcomeEn: "Align contract volume, delivery period, and hedge-instrument tenor."
      }
    ]
  },
  {
    trackId: "gas_basis",
    lessons: [
      {
        id: "gas-basis-hub",
        titleZh: "枢纽基差",
        titleEn: "Hub Basis",
        outcomeZh: "区分 NBP、TTF、THE 等枢纽之间的价格风险与单边价格风险。",
        outcomeEn: "Separate NBP, TTF, THE, and other hub basis from outright price risk."
      },
      {
        id: "gas-basis-delivery",
        titleZh: "交割地点与合同基准",
        titleEn: "Delivery Point and Contract Benchmark",
        outcomeZh: "检查实货交割地、客户价格公式和纸货基准是否一致。",
        outcomeEn: "Check whether physical delivery, customer pricing, and paper benchmark align."
      },
      {
        id: "gas-basis-capacity",
        titleZh: "跨期、运力与路径",
        titleEn: "Calendar, Capacity, and Route",
        outcomeZh: "把期限错配和跨区域运输约束纳入基差套保。",
        outcomeEn: "Include tenor mismatch and cross-regional transport constraints in the basis hedge."
      }
    ]
  },
  {
    trackId: "gas_fx",
    lessons: [
      {
        id: "gas-fx-exposure",
        titleZh: "计价、结算与本位币",
        titleEn: "Pricing, Settlement, and Functional Currency",
        outcomeZh: "识别商品计价、合同结算和利润核算之间的汇率敞口。",
        outcomeEn: "Identify FX exposure across commodity pricing, contract settlement, and functional currency."
      },
      {
        id: "gas-fx-instrument",
        titleZh: "外汇工具与方向",
        titleEn: "FX Instrument and Direction",
        outcomeZh: "根据预期收付款选择外汇远期或掉期，并确定买卖方向。",
        outcomeEn: "Choose an FX forward or swap and determine direction from expected receipts and payments."
      },
      {
        id: "gas-fx-notional",
        titleZh: "金额、单位与期限",
        titleEn: "Notional, Units, and Tenor",
        outcomeZh: "统一 p/th、EUR/MWh、USD/MMBtu，并匹配外汇名义金额和期限。",
        outcomeEn: "Normalize p/th, EUR/MWh, and USD/MMBtu, then match FX notional and tenor."
      }
    ]
  },
  {
    trackId: "gas_integrated",
    lessons: [
      {
        id: "gas-integrated-delivery",
        titleZh: "运力、储气与平衡",
        titleEn: "Capacity, Storage, and Balancing",
        outcomeZh: "检查提名、管输、库存、偏差和交割窗口是否影响套保有效性。",
        outcomeEn: "Check whether nominations, transport, inventory, imbalance, and delivery windows affect hedge effectiveness."
      },
      {
        id: "gas-integrated-optionality",
        titleZh: "LNG 与运营可选性",
        titleEn: "LNG and Operational Optionality",
        outcomeZh: "用期权、领口和运营权利管理船货、气化和转港的非对称风险。",
        outcomeEn: "Use options, collars, and operating rights for asymmetric cargo, regas, and diversion risk."
      },
      {
        id: "gas-integrated-controls",
        titleZh: "组合执行与风控",
        titleEn: "Portfolio Execution and Controls",
        outcomeZh: "把多条实货与纸货腿、信用、保证金、限额和执行窗口合并检查。",
        outcomeEn: "Review multiple physical and paper legs together with credit, margin, limits, and execution windows."
      }
    ]
  }
];

const trackSkillFocus = {
  foundation: ["exposure", "instrument", "rationale"],
  crude: ["instrument", "basis", "timing", "control"],
  gas_local: ["exposure", "instrument", "timing"],
  gas_basis: ["basis", "capacity", "timing"],
  gas_fx: ["fx", "instrument", "timing"],
  gas_integrated: ["basis", "fx", "capacity", "control", "rationale"]
};

const hedgingKnowledgeCoverage = [
  {
    id: "exposure_objective",
    titleZh: "敞口与套保目标",
    titleEn: "Exposure and Objective",
    summaryZh: "先判断天然多头、空头或价差敞口，再确定锁价、锁利润、锁基差或保护下行的目标。",
    summaryEn: "Identify long, short, or spread exposure first, then define whether the goal is locking price, margin, basis, or downside.",
    conceptsZh: ["多头/空头套保", "敞口方向", "数量与期限", "剩余风险"],
    conceptsEn: ["Long/short hedge", "Exposure direction", "Volume and tenor", "Residual risk"],
    modelIds: ["simple_procurement", "customer_indexed_sale", "efet_bilateral_sale"]
  },
  {
    id: "physical_paper_matching",
    titleZh: "实货与纸货匹配",
    titleEn: "Physical-Paper Matching",
    summaryZh: "把商品实货义务与 futures、swap、basis、FX、option 组合成同一个风险闭环。",
    summaryEn: "Connect physical commodity obligations with futures, swaps, basis, FX, and options as one risk loop.",
    conceptsZh: ["实货腿", "纸货腿", "名义量", "履约义务"],
    conceptsEn: ["Physical leg", "Paper leg", "Notional", "Performance obligation"],
    modelIds: ["gsa_procurement", "efet_bilateral_sale", "lng_regas_sale"]
  },
  {
    id: "forward_curve_carry",
    titleZh: "远期结构与持有成本",
    titleEn: "Forward Structure and Carry",
    summaryZh: "理解 Contango、Backwardation、库存持有成本和展期如何改变套保损益与执行节奏。",
    summaryEn: "Understand how contango, backwardation, inventory carry, and roll change hedge P&L and execution timing.",
    conceptsZh: ["Contango", "Backwardation", "持有成本", "展期收益"],
    conceptsEn: ["Contango", "Backwardation", "Cost of carry", "Roll yield"],
    modelIds: ["simple_procurement", "crude_inventory_hedge"]
  },
  {
    id: "outright_price",
    titleZh: "单边价格套保",
    titleEn: "Outright Price Hedge",
    summaryZh: "用期货、远期或掉期管理商品基准价格的绝对涨跌。",
    summaryEn: "Use futures, forwards, or swaps to manage absolute moves in commodity benchmarks.",
    conceptsZh: ["期货", "远期", "固定/浮动掉期", "保证金"],
    conceptsEn: ["Futures", "Forwards", "Fixed-floating swaps", "Margin"],
    modelIds: ["eex_ocm_procurement", "customer_indexed_sale", "lng_cargo_procurement"]
  },
  {
    id: "basis_spread",
    titleZh: "基差、枢纽与跨期价差",
    titleEn: "Basis, Hub, and Calendar Spread",
    summaryZh: "拆分地点、枢纽、期限、单位和汇率带来的价差风险，避免只盯单一基准。",
    summaryEn: "Separate location, hub, tenor, unit, and FX basis from the benchmark price instead of watching one index.",
    conceptsZh: ["基准价差", "地点基差", "跨期价差", "单位归一"],
    conceptsEn: ["Benchmark spread", "Location basis", "Calendar spread", "Unit normalization"],
    modelIds: ["cross_border_sale", "pipeline_capacity", "lng_regas_sale"]
  },
  {
    id: "fx",
    titleZh: "汇率敞口与套保",
    titleEn: "FX Exposure and Hedge",
    summaryZh: "识别商品计价、结算与本位币之间的汇率敞口，并用远期或掉期匹配金额和期限。",
    summaryEn: "Identify FX exposure between commodity pricing, settlement, and functional currency, then match amount and tenor with forwards or swaps.",
    conceptsZh: ["交易币种", "本位币", "FX Forward", "交叉币种错配"],
    conceptsEn: ["Trade currency", "Functional currency", "FX forward", "Cross-currency mismatch"],
    modelIds: ["gsa_procurement", "lng_cargo_procurement", "crude_cargo_hedge"]
  },
  {
    id: "crude_benchmark_basis",
    titleZh: "原油基准、品级与地点基差",
    titleEn: "Crude Benchmarks, Grade, and Location Basis",
    summaryZh: "把 Brent、WTI、Dubai、品级贴水、交割地点和装船窗口拆开，避免把原油敞口误当成单一 flat price。",
    summaryEn: "Separate Brent, WTI, Dubai, grade differential, delivery location, and loading window instead of treating crude exposure as one flat price.",
    conceptsZh: ["Brent/WTI/Dubai", "品级贴水", "地点基差", "装船窗口"],
    conceptsEn: ["Brent/WTI/Dubai", "Grade differential", "Location basis", "Loading window"],
    modelIds: ["crude_cargo_hedge", "crude_calendar_basis"]
  },
  {
    id: "inventory_freight_roll",
    titleZh: "库存、运费与展期风险",
    titleEn: "Inventory, Freight, and Roll Risk",
    summaryZh: "原油套保需要同时检查库存持有期、租船或管输成本、保证金和期货展期风险。",
    summaryEn: "Crude hedging needs checks on inventory holding period, freight or pipeline cost, margin, and futures roll risk.",
    conceptsZh: ["库存周期", "租船/管输", "保证金", "展期"],
    conceptsEn: ["Inventory cycle", "Freight/pipeline", "Margin", "Roll"],
    modelIds: ["crude_cargo_hedge", "crude_inventory_hedge"]
  },
  {
    id: "options_optionality",
    titleZh: "期权与运营可选性",
    titleEn: "Options and Optionality",
    summaryZh: "用 cap、floor、collar、摆动权、船货转港和气化窗口处理非线性或不对称风险。",
    summaryEn: "Use caps, floors, collars, swing rights, diversion, and regas windows for nonlinear or asymmetric risk.",
    conceptsZh: ["Cap/Floor", "Collar", "Swing", "LNG 转港"],
    conceptsEn: ["Cap/Floor", "Collar", "Swing", "LNG diversion"],
    modelIds: ["lng_cargo_procurement", "lng_regas_sale", "customer_indexed_sale"]
  },
  {
    id: "hedge_ratio_cross_hedge",
    titleZh: "套保比率与交叉套保",
    titleEn: "Hedge Ratio and Cross-Hedge",
    summaryZh: "当工具与实货不完全一致时，按相关性、价格敏感度、期限和流动性确定套保比例。",
    summaryEn: "When the hedge instrument is imperfect, size it by correlation, price sensitivity, tenor, and liquidity.",
    conceptsZh: ["最小方差比率", "相关性", "错配风险", "流动性"],
    conceptsEn: ["Minimum variance ratio", "Correlation", "Mismatch risk", "Liquidity"],
    modelIds: ["eex_ocm_procurement", "cross_border_sale", "integrated_portfolio"]
  },
  {
    id: "capacity_storage_balancing",
    titleZh: "运力、储气与平衡",
    titleEn: "Capacity, Storage, and Balancing",
    summaryZh: "检查管输 capacity、提名、库存、偏差和跨境路径，否则价格套保不能覆盖交付风险。",
    summaryEn: "Check pipeline capacity, nominations, inventory, imbalance, and cross-border routes because price hedges do not cover delivery risk.",
    conceptsZh: ["管输 capacity", "提名", "库存", "日内平衡"],
    conceptsEn: ["Pipeline capacity", "Nominations", "Inventory", "Intraday balancing"],
    modelIds: ["pipeline_capacity", "gsa_procurement", "lng_regas_sale"]
  },
  {
    id: "risk_controls",
    titleZh: "执行与风控",
    titleEn: "Execution and Risk Controls",
    summaryZh: "把流动性、信用、限额、保证金、结算、移仓和窗口截点纳入交易前检查。",
    summaryEn: "Bring liquidity, credit, limits, margin, settlement, roll risk, and cut-off windows into the pre-trade check.",
    conceptsZh: ["信用", "限额", "保证金", "移仓"],
    conceptsEn: ["Credit", "Limits", "Margin", "Roll risk"],
    modelIds: ["efet_bilateral_sale", "eex_ocm_procurement", "integrated_portfolio"]
  }
];

const gasTradingModels = [
  {
    id: "simple_procurement",
    group: "foundation",
    titleZh: "基础固定价采购",
    titleEn: "Basic Fixed-Price Procurement",
    summaryZh: "从采购实货敞口出发，练习买卖方向、数量、期限和基准的一一匹配。",
    summaryEn: "Start from a physical procurement exposure and match side, quantity, tenor, and benchmark one by one.",
    risksZh: ["价格上涨", "数量错配", "期限错配", "基准错配"],
    risksEn: ["Price increase", "Quantity mismatch", "Tenor mismatch", "Benchmark mismatch"],
    instrumentsZh: ["实货采购", "固定价掉期", "期货"],
    instrumentsEn: ["Physical procurement", "Fixed-price swap", "Future"]
  },
  {
    id: "gsa_procurement",
    group: "procurement",
    titleZh: "上游 Beach / GSA 资源",
    titleEn: "Upstream Beach / GSA Supply",
    summaryZh: "处理上游交付资源、合同数量、提名、NBP/TTF 基差和跨境运输。",
    summaryEn: "Manage upstream delivery, contract quantity, nominations, NBP/TTF basis, and cross-border transport.",
    risksZh: ["资源锁定", "基差", "运力", "汇率"],
    risksEn: ["Supply lock-in", "Basis", "Capacity", "FX"],
    instrumentsZh: ["实货 GSA", "基差掉期", "EUR/GBP 远期", "管输 capacity"],
    instrumentsEn: ["Physical GSA", "Basis swap", "EUR/GBP forward", "Pipeline capacity"]
  },
  {
    id: "eex_ocm_procurement",
    group: "procurement",
    titleZh: "EEX / OCM 窗口采购",
    titleEn: "EEX / OCM Window Procurement",
    summaryZh: "围绕日内、日前或月度窗口比较现货采购、期货、掉期和执行成本。",
    summaryEn: "Compare spot procurement, futures, swaps, and execution cost around intraday, day-ahead, or monthly windows.",
    risksZh: ["日内波动", "期限错配", "流动性", "截点"],
    risksEn: ["Intraday volatility", "Tenor mismatch", "Liquidity", "Cut-off"],
    instrumentsZh: ["现货窗口", "TTF 期货", "固定/浮动掉期", "限价执行"],
    instrumentsEn: ["Spot window", "TTF future", "Fixed-floating swap", "Limit execution"]
  },
  {
    id: "lng_cargo_procurement",
    group: "procurement",
    titleZh: "LNG 船货采购",
    titleEn: "LNG Cargo Procurement",
    summaryZh: "处理 JKM/TTF 指数、船期、运费、转港可选性和气化前后的价格风险。",
    summaryEn: "Handle JKM/TTF indexing, cargo timing, freight, diversion optionality, and pre/post-regas price risk.",
    risksZh: ["JKM/TTF", "船期", "可选性", "汇率"],
    risksEn: ["JKM/TTF", "Cargo timing", "Optionality", "FX"],
    instrumentsZh: ["LNG 实货", "JKM/TTF 掉期", "期权领口", "FX"],
    instrumentsEn: ["Physical LNG", "JKM/TTF swap", "Option collar", "FX"]
  },
  {
    id: "efet_bilateral_sale",
    group: "sales",
    titleZh: "EFET 双边销售",
    titleEn: "Bilateral EFET Sale",
    summaryZh: "训练交割点、客户价格公式、信用限额、履约和结算风险的套保。",
    summaryEn: "Train delivery point, customer price formula, credit limit, performance, and settlement risk hedging.",
    risksZh: ["履约", "信用", "枢纽错配", "结算"],
    risksEn: ["Performance", "Credit", "Hub mismatch", "Settlement"],
    instrumentsZh: ["EFET 实货", "TTF/NBP 基差", "掉期", "信用检查"],
    instrumentsEn: ["Physical EFET", "TTF/NBP basis", "Swap", "Credit check"]
  },
  {
    id: "lng_regas_sale",
    group: "sales",
    titleZh: "LNG 气化销售",
    titleEn: "LNG Regas Sale",
    summaryZh: "把船货到港、气化窗口、下游销售和市场下跌保护连成一套组合动作。",
    summaryEn: "Connect cargo arrival, regas window, downstream sale, and downside protection into one strategy.",
    risksZh: ["气化窗口", "价格下跌", "基差", "履约"],
    risksEn: ["Regas window", "Selloff", "Basis", "Performance"],
    instrumentsZh: ["气化能力", "TTF 掉期", "期权", "基差腿"],
    instrumentsEn: ["Regas capacity", "TTF swap", "Option", "Basis leg"]
  },
  {
    id: "pipeline_capacity",
    group: "integrated",
    titleZh: "管输、库存与平衡",
    titleEn: "Pipeline, Storage, and Balancing",
    summaryZh: "训练 capacity、库存、提名偏差和路径拥堵如何改变实货和纸货策略。",
    summaryEn: "Train how capacity, inventory, nominations, and congestion change physical and paper strategy.",
    risksZh: ["拥堵", "提名", "库存", "偏差"],
    risksEn: ["Congestion", "Nominations", "Inventory", "Imbalance"],
    instrumentsZh: ["管输 capacity", "储气", "现货平衡", "基差"],
    instrumentsEn: ["Pipeline capacity", "Storage", "Spot balancing", "Basis"]
  },
  {
    id: "customer_indexed_sale",
    group: "sales",
    titleZh: "客户指数化销售",
    titleEn: "Customer Indexed Sale",
    summaryZh: "处理客户固定价、浮动价、上限价或公式价与采购端敞口的错配。",
    summaryEn: "Handle mismatch between fixed, floating, capped, or formula customer prices and procurement exposure.",
    risksZh: ["客户定价", "固定/浮动", "期权性", "利润率"],
    risksEn: ["Customer pricing", "Fixed/floating", "Optionality", "Margin"],
    instrumentsZh: ["销售合约", "swap", "cap/floor", "collar"],
    instrumentsEn: ["Sales contract", "Swap", "Cap/floor", "Collar"]
  },
  {
    id: "crude_cargo_hedge",
    group: "crude",
    titleZh: "原油船货采购/销售套保",
    titleEn: "Crude Cargo Procurement / Sale Hedge",
    summaryZh: "处理 Brent、WTI 或 Dubai 计价船货的 flat price、装船窗口、品级差和销售锁价。",
    summaryEn: "Handle flat price, loading window, grade differential, and sales lock-in for Brent, WTI, or Dubai indexed cargoes.",
    risksZh: ["Flat price", "装船窗口", "品级差", "销售锁价"],
    risksEn: ["Flat price", "Loading window", "Grade differential", "Sale lock-in"],
    instrumentsZh: ["原油实货", "期货", "固定/浮动掉期", "品级基差"],
    instrumentsEn: ["Physical crude", "Futures", "Fixed-floating swap", "Grade basis"]
  },
  {
    id: "crude_calendar_basis",
    group: "crude",
    titleZh: "原油月差与跨基准基差",
    titleEn: "Crude Calendar and Cross-Benchmark Basis",
    summaryZh: "拆分 prompt month、月差、Brent/WTI、Brent/Dubai、地点和运费带来的价差风险。",
    summaryEn: "Separate prompt month, calendar spreads, Brent/WTI, Brent/Dubai, location, and freight basis risk.",
    risksZh: ["月差", "跨基准", "地点", "运费"],
    risksEn: ["Calendar spread", "Cross-benchmark", "Location", "Freight"],
    instrumentsZh: ["Calendar spread", "Brent/WTI spread", "Brent/Dubai spread", "运费调整"],
    instrumentsEn: ["Calendar spread", "Brent/WTI spread", "Brent/Dubai spread", "Freight adjustment"]
  },
  {
    id: "crude_inventory_hedge",
    group: "crude",
    titleZh: "原油库存与展期套保",
    titleEn: "Crude Inventory and Roll Hedge",
    summaryZh: "围绕库存持有期、展期、保证金和信用限额设计 hedge ratio 与执行计划。",
    summaryEn: "Design hedge ratio and execution plan around inventory holding period, roll, margin, and credit limits.",
    risksZh: ["库存周期", "展期", "保证金", "信用限额"],
    risksEn: ["Inventory cycle", "Roll", "Margin", "Credit limits"],
    instrumentsZh: ["库存实货", "期货展期", "掉期", "风控检查"],
    instrumentsEn: ["Physical inventory", "Futures roll", "Swap", "Risk controls"]
  }
];

const scenarioLibraryItems = [
  {
    id: "gas_local_market_procurement",
    commodity: "natural-gas",
    stage: "foundation",
    role: "procurement",
    riskFocus: "outright",
    titleZh: "本地市场采购成本套保",
    titleEn: "Local-Market Procurement Cost Hedge",
    summaryZh: "同一枢纽、同一币种下，匹配采购合同与固定价掉期或期货，掌握方向、数量和期限。",
    summaryEn: "Match a same-hub, same-currency purchase contract with a fixed-price swap or future, focusing on direction, volume, and tenor.",
    tags: ["TTF", "Procurement", "Swap"],
    difficultyZh: "基础",
    difficultyEn: "Foundation",
    duration: "35",
    enabled: true
  },
  {
    id: "gas_local_market_sale",
    commodity: "natural-gas",
    stage: "foundation",
    role: "sales",
    riskFocus: "outright",
    titleZh: "本地市场销售收入套保",
    titleEn: "Local-Market Sales Revenue Hedge",
    summaryZh: "围绕固定价、浮动价或公式价销售合同，识别价格下跌风险并建立对应纸货保护。",
    summaryEn: "Identify downside in fixed, floating, or formula-priced sales and build the matching paper hedge.",
    tags: ["TTF", "Sales", "Fixed/Floating"],
    difficultyZh: "基础",
    difficultyEn: "Foundation",
    duration: "35",
    enabled: true
  },
  {
    id: "procurement_beach_to_germany",
    commodity: "natural-gas",
    stage: "basis",
    role: "integrated",
    riskFocus: "basis",
    titleZh: "跨枢纽供销基差套保",
    titleEn: "Cross-Hub Supply and Sales Basis Hedge",
    summaryZh: "上游或区域资源销往另一欧洲市场，训练 NBP、TTF、THE 等枢纽之间的基差和交割地点错配。",
    summaryEn: "Move upstream or regional supply into another European market and hedge basis across NBP, TTF, THE, or other delivery points.",
    tags: ["GSA/EFET", "Hub Basis", "Delivery Point"],
    difficultyZh: "进阶",
    difficultyEn: "Intermediate",
    duration: "55",
    enabled: true
  },
  {
    id: "gas_cross_currency_settlement",
    commodity: "natural-gas",
    stage: "currency",
    role: "integrated",
    riskFocus: "fx",
    titleZh: "跨币种天然气供销套保",
    titleEn: "Cross-Currency Gas Supply and Sales Hedge",
    summaryZh: "商品计价、合同结算与本位币不同，先完成商品套保，再匹配外汇金额、方向和期限。",
    summaryEn: "Hedge the commodity first, then align FX amount, direction, and tenor when pricing, settlement, and functional currencies differ.",
    tags: ["EUR/GBP", "FX Forward", "Unit Conversion"],
    difficultyZh: "进阶",
    difficultyEn: "Intermediate",
    duration: "60",
    enabled: true
  },
  {
    id: "gas_transport_capacity_hedge",
    commodity: "natural-gas",
    stage: "operations",
    role: "integrated",
    riskFocus: "capacity",
    titleZh: "跨区域运输与交付保障",
    titleEn: "Cross-Regional Transport and Delivery Coverage",
    summaryZh: "把管输运力、提名、路径拥堵和交割窗口纳入实货与纸货组合，识别价格套保无法覆盖的履约风险。",
    summaryEn: "Add capacity, nomination, congestion, and delivery windows to the physical-paper hedge and identify uncovered performance risk.",
    tags: ["Capacity", "Nomination", "Balancing"],
    difficultyZh: "进阶",
    difficultyEn: "Intermediate",
    duration: "65",
    enabled: true
  },
  {
    id: "procurement_eex_ocm_window",
    commodity: "natural-gas",
    stage: "operations",
    role: "procurement",
    riskFocus: "execution",
    titleZh: "EEX / OCM 窗口采购与纸货匹配",
    titleEn: "EEX / OCM window procurement hedge",
    summaryZh: "围绕窗口成交、期限错配和流动性风险，设计实货采购与掉期/期货组合。",
    summaryEn: "Design physical procurement plus swaps/futures around window execution, tenor mismatch, and liquidity.",
    tags: ["EEX", "OCM", "Swap", "Liquidity"],
    difficultyZh: "中等",
    difficultyEn: "Intermediate",
    duration: "60",
    enabled: true
  },
  {
    id: "sales_efet_bilateral",
    commodity: "natural-gas",
    stage: "basis",
    role: "sales",
    riskFocus: "basis",
    titleZh: "EFET 双边销售与交割基差",
    titleEn: "Bilateral EFET Sale and Delivery Basis",
    summaryZh: "围绕客户价格公式、交割点、信用限额和纸货基准，处理双边销售中的基差与履约风险。",
    summaryEn: "Manage customer pricing, delivery point, credit limit, paper benchmark, basis, and performance in a bilateral sale.",
    tags: ["EFET", "Credit", "Basis"],
    difficultyZh: "中等",
    difficultyEn: "Intermediate",
    duration: "55",
    enabled: true
  },
  {
    id: "sales_lng_regas",
    commodity: "natural-gas",
    stage: "portfolio",
    role: "sales",
    riskFocus: "optionality",
    titleZh: "LNG 气化与销售组合套保",
    titleEn: "LNG Regas and Sales Portfolio Hedge",
    summaryZh: "综合船货指数、气化窗口、下游销售、基差和运营可选性，管理非对称价格与履约风险。",
    summaryEn: "Combine cargo index, regas window, downstream sale, basis, and operating optionality to manage asymmetric price and performance risk.",
    tags: ["LNG", "Regas", "Optionality"],
    difficultyZh: "综合",
    difficultyEn: "Advanced",
    duration: "80",
    enabled: true
  },
  {
    id: "integrated_gas_portfolio",
    commodity: "natural-gas",
    stage: "portfolio",
    role: "integrated",
    riskFocus: "integrated",
    titleZh: "天然气组合风险管理",
    titleEn: "Integrated Gas Portfolio Risk Management",
    summaryZh: "同时管理实货、纸货、枢纽基差、汇率、运力、期权、信用和执行约束。",
    summaryEn: "Manage physical, paper, hub basis, FX, capacity, options, credit, and execution constraints as one portfolio.",
    tags: ["Multi-Leg", "Portfolio", "Controls"],
    difficultyZh: "综合",
    difficultyEn: "Advanced",
    duration: "90",
    enabled: true
  },
  {
    id: "crude_oil_hedging_basics",
    commodity: "crude-oil",
    stage: "foundation",
    role: "crude",
    riskFocus: "crude-basis-inventory",
    titleZh: "Brent / WTI 原油船货套保",
    titleEn: "Brent / WTI crude cargo hedge",
    summaryZh: "围绕原油采购或销售敞口，处理 flat price、月差、品级/地点基差、库存和运费风险。",
    summaryEn: "Hedge crude procurement or sales exposure across flat price, calendar spread, grade/location basis, inventory, and freight risk.",
    tags: ["Brent", "WTI", "Calendar", "Inventory"],
    difficultyZh: "入门",
    difficultyEn: "Beginner",
    duration: "70",
    enabled: true
  }
];

const scenarioFilterDefinitions = [
  { id: "commodity", labelZh: "商品", labelEn: "Commodity" },
  { id: "stage", labelZh: "学习阶段", labelEn: "Learning Stage" },
  { id: "role", labelZh: "业务角色", labelEn: "Business Role" },
  { id: "riskFocus", labelZh: "风险类型", labelEn: "Risk Type" }
];

const scenarioFilterLabels = {
  commodity: {
    "natural-gas": ["天然气", "Natural Gas"],
    "crude-oil": ["原油", "Crude Oil"]
  },
  stage: {
    foundation: ["1 基础价格风险", "1 Price Foundations"],
    basis: ["2 基差与跨区域", "2 Basis and Region"],
    currency: ["3 跨币种结算", "3 Cross-Currency"],
    operations: ["4 运输与执行", "4 Transport and Execution"],
    portfolio: ["5 综合组合", "5 Integrated Portfolio"]
  },
  role: {
    procurement: ["采购端", "Procurement"],
    sales: ["销售端", "Sales"],
    integrated: ["供销组合", "Integrated Supply and Sales"],
    crude: ["原油采购/销售", "Crude procurement/sales"],
    constructing: ["建设中", "Constructing"]
  },
  difficulty: {
    Beginner: ["入门", "Beginner"],
    Intermediate: ["中等", "Intermediate"],
    Advanced: ["困难", "Advanced"],
    Constructing: ["建设中", "Constructing"]
  },
  riskFocus: {
    outright: ["单边价格", "Outright Price"],
    basis: ["基差与交割点", "Basis and Delivery"],
    fx: ["汇率与结算", "FX and Settlement"],
    capacity: ["运力与平衡", "Capacity and Balancing"],
    execution: ["窗口与流动性", "Window and Liquidity"],
    optionality: ["LNG 与可选性", "LNG and Optionality"],
    integrated: ["组合风险", "Integrated Risk"],
    "crude-basis-inventory": ["原油基差 / 库存", "Crude Basis / Inventory"],
    constructing: ["建设中", "Constructing"]
  }
};

const knowledgeNodes = [
  { id: "hub", x: 50, y: 25, level: "intermediate", titleZh: "Hub Pricing", titleEn: "Hub Pricing", descZh: "TTF、NBP、THE、ZTP 等枢纽定价和交割逻辑。", descEn: "TTF, NBP, THE, ZTP hub pricing and delivery logic." },
  { id: "basis", x: 22, y: 38, level: "advanced", titleZh: "基差与价差", titleEn: "Basis & Spreads", descZh: "不同枢纽、时间和交割点之间的价差风险。", descEn: "Spread risk across hubs, tenors, and delivery points." },
  { id: "physical", x: 31, y: 18, level: "beginner", titleZh: "实货合同", titleEn: "Physical Contracts", descZh: "GSA、EFET、LNG 船货和气化销售的履约义务。", descEn: "GSA, EFET, LNG cargo, and regas sales obligations." },
  { id: "capacity", x: 20, y: 62, level: "intermediate", titleZh: "运力与路径", titleEn: "Capacity & Routing", descZh: "管输容量、跨境路径、拥堵和日内平衡风险。", descEn: "Pipeline capacity, cross-border routes, congestion, and balancing risk." },
  { id: "fx", x: 76, y: 44, level: "intermediate", titleZh: "汇率套保", titleEn: "FX Hedge", descZh: "EUR/GBP 和美元计价风险的前锋或掉期处理。", descEn: "Forwards or swaps for EUR/GBP and USD-denominated exposure." },
  { id: "lng", x: 76, y: 64, level: "beginner", titleZh: "LNG 与气化", titleEn: "LNG & Regas", descZh: "船期、气化窗口、JKM/TTF 转换和期权性。", descEn: "Cargo timing, regas windows, JKM/TTF conversion, and optionality." },
  { id: "crudeBench", x: 48, y: 54, level: "beginner", titleZh: "原油基准", titleEn: "Crude Benchmarks", descZh: "Brent、WTI、Dubai、品级、地点和装船窗口如何影响套保。", descEn: "How Brent, WTI, Dubai, grade, location, and loading windows shape hedges." },
  { id: "risk", x: 58, y: 82, level: "advanced", titleZh: "风险管理", titleEn: "Risk Management", descZh: "信用、限额、流动性、保证金和执行窗口。", descEn: "Credit, limits, liquidity, margin, and execution windows." },
  { id: "exchange", x: 78, y: 22, level: "intermediate", titleZh: "EFET / OCM / EEX", titleEn: "EFET / OCM / EEX", descZh: "双边、窗口和交易所工具的适用边界。", descEn: "Where bilateral, window, and exchange instruments fit." },
  { id: "storage", x: 36, y: 84, level: "beginner", titleZh: "储气与季节性", titleEn: "Storage & Seasonality", descZh: "注采节奏、库存和季节曲线对套保的影响。", descEn: "Injection/withdrawal, inventory, and seasonal curve impacts." }
];

const knowledgeFlowLevels = [
  {
    id: "foundation",
    titleZh: "基础认知",
    titleEn: "Foundation",
    descZh: "先建立实货、交付和价格基准的语言。",
    descEn: "Start with physical delivery and benchmark language.",
    nodes: ["physical", "hub", "lng", "crudeBench"]
  },
  {
    id: "exposure",
    titleZh: "敞口拆分",
    titleEn: "Exposure Breakdown",
    descZh: "再拆出地点、期限、运力和季节性错配。",
    descEn: "Then isolate location, tenor, capacity, and seasonality mismatches.",
    nodes: ["basis", "capacity", "storage"]
  },
  {
    id: "instruments",
    titleZh: "工具组合",
    titleEn: "Instrument Mix",
    descZh: "把交易所、双边、窗口和汇率工具组合成多腿策略。",
    descEn: "Combine exchange, bilateral, window, and FX tools into multi-leg hedges.",
    nodes: ["exchange", "fx"]
  },
  {
    id: "controls",
    titleZh: "执行复盘",
    titleEn: "Controls and Review",
    descZh: "最后用信用、限额、保证金和执行窗口检查策略质量。",
    descEn: "Finish with credit, limits, margin, and execution-window checks.",
    nodes: ["risk"]
  }
];

const learningRecordsKey = "commodity-lab-learning-records-v2";
const aiLessonPlanKey = "commodity-lab-ai-lesson-plan-v1";

const skillDimensions = [
  { id: "exposure", zh: "风险识别", en: "Exposure Identification" },
  { id: "instrument", zh: "工具选择", en: "Hedge Instrument Selection" },
  { id: "basis", zh: "基差逻辑", en: "Basis Logic" },
  { id: "fx", zh: "汇率逻辑", en: "FX Logic" },
  { id: "capacity", zh: "运力/物流", en: "Capacity & Logistics" },
  { id: "timing", zh: "执行时机", en: "Execution Timing" },
  { id: "control", zh: "风险控制", en: "Risk Control" },
  { id: "rationale", zh: "说明质量", en: "Rationale Quality" }
];

function copy(locale, zh, en) {
  return normalizeLocale(locale) === "zh" ? zh : en;
}

function levelLabel(locale, level) {
  const labels = {
    beginner: ["基础", "Foundation"],
    intermediate: ["进阶", "Intermediate"],
    advanced: ["综合", "Advanced"]
  };
  const [zh, en] = labels[level] ?? [level, level];
  return copy(locale, zh, en);
}

const mistakeLabels = {
  missing_physical_leg: ["缺少实货腿", "Missing physical leg"],
  missing_paper_leg: ["缺少纸货套保腿", "Missing paper hedge leg"],
  incomplete_target_legs: ["组合动作不完整", "Incomplete target legs"],
  wrong_direction: ["交易方向与目标敞口不一致", "Trade direction does not match the exposure"],
  quantity_mismatch: ["套保数量与目标敞口不匹配", "Hedge quantity does not match the target exposure"],
  tenor_mismatch: ["套保期限与交割期限不匹配", "Hedge tenor does not match delivery"],
  market_mismatch: ["工具基准或市场不匹配", "Instrument benchmark or market mismatch"],
  insufficient_rationale: ["策略说明过短，无法判断匹配逻辑", "Rationale is too short to explain the hedge"],
  missing_risk_explanation: ["未解释剩余价格、基差或可选性风险", "Residual price, basis, or optionality risk is not explained"],
  missing_execution_controls: ["未说明流动性、信用、限额或执行检查", "Liquidity, credit, limits, or execution checks are missing"]
};

function mistakeLabel(tag, locale) {
  const labels = mistakeLabels[tag];
  return labels ? labels[normalizeLocale(locale) === "zh" ? 0 : 1] : String(tag).replaceAll("_", " ");
}

const fallbackTemplates = {
  groups: [
    { id: "foundation", label: "通识金融工具" },
    { id: "crude", label: "原油套保" },
    { id: "procurement", label: "采购端" },
    { id: "sales", label: "销售端" },
    { id: "integrated", label: "组合策略" }
  ],
  knowledge_points: [
    { id: "exposure_objective", label: "敞口与套保目标", description: "判断多头、空头或价差敞口，再确定套保目的。" },
    { id: "physical_paper_matching", label: "实货与纸货匹配", description: "GSA、EFET、LNG、swap、future、basis、FX、option、capacity 的组合动作。" },
    { id: "outright_price", label: "单边价格套保", description: "使用期货、远期或掉期管理绝对价格风险。" },
    { id: "basis_spread", label: "基差、枢纽与跨期价差", description: "TTF/NBP、地点差、跨期、单位与汇率归一化。" },
    { id: "crude_benchmark_basis", label: "原油基准、品级与地点基差", description: "Brent、WTI、Dubai、品级、地点和装船窗口的差异。" },
    { id: "inventory_freight_roll", label: "库存、运费与展期风险", description: "库存周期、租船或管输成本、保证金和期货展期。" },
    { id: "options_optionality", label: "期权与运营可选性", description: "cap、floor、collar、LNG 转港和气化窗口等非线性风险。" },
    { id: "capacity_storage_balancing", label: "运力、储气与平衡", description: "管输 capacity、提名、库存、偏差和路径约束。" },
    { id: "risk_controls", label: "执行与风控", description: "流动性、信用、限额、保证金、结算和移仓风险。" }
  ],
  templates: [
    {
      id: "foundation_hedging_basics",
      group: "foundation",
      business_type: "跨品种套保通识",
      title: "金融工具与套保决策基础",
      summary: "通识案例：识别敞口，理解远期结构，并匹配工具、方向、数量、期限和风控。",
      coverage: ["exposure_objective", "forward_curve_carry", "outright_price", "physical_paper_matching", "basis_spread", "hedge_ratio_cross_hedge", "options_optionality", "fx", "risk_controls"],
      gas_models: ["simple_procurement"],
      knowledge_points: ["exposure_objective", "forward_curve_carry", "outright_price", "physical_paper_matching", "basis_spread", "hedge_ratio_cross_hedge", "options_optionality", "fx", "risk_controls"],
      required_curves: ["PRIMARY_BENCHMARK", "HEDGE_BENCHMARK"],
      suggested_leg_types: ["physical", "swap"]
    },
    {
      id: "gas_local_market_procurement",
      group: "procurement",
      business_type: "本地市场天然气采购",
      title: "本地市场采购成本套保",
      summary: "在同一枢纽、同一币种下管理采购成本上涨风险。",
      coverage: ["exposure_objective", "outright_price", "physical_paper_matching", "forward_curve_carry", "risk_controls"],
      gas_models: ["simple_procurement", "eex_ocm_procurement"],
      knowledge_points: ["exposure_objective", "outright_price", "physical_paper_matching", "risk_controls"],
      required_curves: ["TTF"],
      suggested_leg_types: ["physical", "swap"]
    },
    {
      id: "gas_local_market_sale",
      group: "sales",
      business_type: "本地市场天然气销售",
      title: "本地市场销售收入套保",
      summary: "在同一枢纽、同一币种下管理销售收入下跌风险。",
      coverage: ["exposure_objective", "outright_price", "physical_paper_matching", "risk_controls"],
      gas_models: ["customer_indexed_sale", "efet_bilateral_sale"],
      knowledge_points: ["exposure_objective", "outright_price", "physical_paper_matching", "risk_controls"],
      required_curves: ["TTF"],
      suggested_leg_types: ["physical", "swap"]
    },
    {
      id: "procurement_beach_to_germany",
      group: "procurement",
      business_type: "跨区域天然气供销",
      title: "跨枢纽供销基差套保",
      summary: "管理不同欧洲枢纽、交割地点和运输路径之间的基差风险。",
      coverage: ["basis_spread", "fx", "capacity_storage_balancing", "physical_paper_matching", "risk_controls"],
      gas_models: ["gsa_procurement", "pipeline_capacity"],
      knowledge_points: ["basis_spread", "fx", "capacity_storage_balancing", "physical_paper_matching"],
      required_curves: ["TTF", "NBP", "EURGBP", "TTF_NBP_SPREAD"],
      suggested_leg_types: ["physical", "basis", "fx", "capacity"]
    },
    {
      id: "gas_cross_currency_settlement",
      group: "integrated",
      business_type: "跨币种天然气供销",
      title: "跨币种天然气供销套保",
      summary: "在商品套保基础上匹配计价、结算和本位币敞口。",
      coverage: ["physical_paper_matching", "basis_spread", "fx", "risk_controls"],
      gas_models: ["cross_border_sale", "customer_indexed_sale"],
      knowledge_points: ["physical_paper_matching", "basis_spread", "fx", "risk_controls"],
      required_curves: ["TTF", "NBP", "EURGBP", "TTF_NBP_SPREAD"],
      suggested_leg_types: ["physical", "basis", "fx"]
    },
    {
      id: "gas_transport_capacity_hedge",
      group: "integrated",
      business_type: "跨区域运输与交付",
      title: "跨区域运输与交付保障",
      summary: "将运力、提名、拥堵和交割窗口纳入套保组合。",
      coverage: ["basis_spread", "capacity_storage_balancing", "physical_paper_matching", "risk_controls"],
      gas_models: ["pipeline_capacity", "cross_border_sale"],
      knowledge_points: ["basis_spread", "capacity_storage_balancing", "physical_paper_matching", "risk_controls"],
      required_curves: ["TTF", "NBP", "TTF_NBP_SPREAD"],
      suggested_leg_types: ["physical", "basis", "capacity"]
    },
    {
      id: "procurement_lng_cargo",
      group: "procurement",
      business_type: "LNG 船货采购",
      title: "带 JKM / TTF 可选性的 LNG 船货采购",
      summary: "AI 生成船货、JKM/TTF、汇率、转港可选性和气化敞口案例。",
      coverage: ["basis_spread", "fx", "options_optionality", "risk_controls"],
      gas_models: ["lng_cargo_procurement", "lng_regas_sale"],
      knowledge_points: ["basis_spread", "fx", "options_optionality", "risk_controls"],
      required_curves: ["TTF", "JKM", "EURUSD", "TTF_JKM_SPREAD"],
      suggested_leg_types: ["physical", "swap", "basis", "fx", "option"]
    },
    {
      id: "crude_oil_hedging_basics",
      group: "crude",
      business_type: "原油采购/销售套保",
      title: "Brent / WTI 敞口如何套保",
      summary: "AI 生成原油船货、期货/掉期、月差/基差、库存和运费风险匹配案例。",
      coverage: ["exposure_objective", "physical_paper_matching", "outright_price", "crude_benchmark_basis", "inventory_freight_roll", "risk_controls"],
      gas_models: ["crude_cargo_hedge", "crude_calendar_basis", "crude_inventory_hedge"],
      knowledge_points: ["exposure_objective", "crude_benchmark_basis", "physical_paper_matching", "inventory_freight_roll", "risk_controls"],
      required_curves: ["BRENT", "WTI", "DUBAI", "BRENT_WTI_SPREAD"],
      suggested_leg_types: ["physical", "future", "swap", "basis"]
    },
    {
      id: "sales_efet_bilateral",
      group: "sales",
      business_type: "EFET 双边销售",
      title: "EFET 双边销售与枢纽错配",
      summary: "AI 生成交割点、客户定价、信用和基差错配案例。",
      coverage: ["physical_paper_matching", "basis_spread", "risk_controls"],
      gas_models: ["efet_bilateral_sale"],
      knowledge_points: ["physical_paper_matching", "basis_spread", "risk_controls"],
      required_curves: ["TTF", "NBP", "TTF_NBP_SPREAD"],
      suggested_leg_types: ["physical", "basis", "swap"]
    },
    {
      id: "sales_lng_regas",
      group: "sales",
      business_type: "LNG 船货气化销售",
      title: "市场下跌中的 LNG 气化销售",
      summary: "AI 生成 LNG 气化销售、价格下跌、期权和履约保护案例。",
      coverage: ["outright_price", "basis_spread", "options_optionality", "capacity_storage_balancing", "risk_controls"],
      gas_models: ["lng_regas_sale", "customer_indexed_sale"],
      knowledge_points: ["outright_price", "basis_spread", "options_optionality", "capacity_storage_balancing"],
      required_curves: ["TTF", "JKM", "TTF_JKM_SPREAD", "REGAS_WINDOW"],
      suggested_leg_types: ["physical", "swap", "basis", "option", "capacity"]
    },
    {
      id: "integrated_gas_portfolio",
      group: "integrated",
      business_type: "天然气组合套保",
      title: "市场压力下的多腿天然气套保",
      summary: "AI 生成实货、纸货、基差、汇率、运力、期权和风控的综合案例。",
      coverage: ["exposure_objective", "physical_paper_matching", "basis_spread", "fx", "capacity_storage_balancing", "options_optionality", "risk_controls"],
      gas_models: ["gsa_procurement", "efet_bilateral_sale", "lng_regas_sale", "pipeline_capacity"],
      knowledge_points: ["physical_paper_matching", "basis_spread", "fx", "capacity_storage_balancing", "options_optionality", "risk_controls"],
      required_curves: ["TTF", "NBP", "JKM", "EURGBP", "TTF_NBP_SPREAD"],
      suggested_leg_types: ["physical", "swap", "basis", "fx", "capacity", "option"]
    }
  ]
};

function savedValue(key, fallback = "") {
  if (typeof localStorage === "undefined") return fallback;
  return localStorage.getItem(key) ?? fallback;
}

function formatNumber(value, digits = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(number);
}

function formatMoney(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(number);
}

function compactDate(value) {
  return String(value ?? "").slice(5) || "--";
}

function emptyCase(productScope = "natural_gas") {
  return {
    status: "empty",
    product_scope: productScope,
    scenario: null,
    market: null,
    target_actions: [],
    rubric: [],
    prompt: ""
  };
}

function defaultCase(locale) {
  const zh = normalizeLocale(locale) === "zh";
  return {
    scenario: {
      id: "starter_case",
      title: zh ? "第一课：套保对象与风险敞口" : "Lesson 1: Hedge Object and Risk Exposure",
      summary: zh
        ? "本课聚焦业务敞口、套保目标，以及实货与纸货的对应关系。"
        : "This lesson focuses on business exposure, hedge objectives, and physical-paper matching.",
      business_type: zh ? "天然气套保基础" : "Natural Gas Hedging Foundations",
      knowledge_points: ["outright_price", "physical_paper_matching"],
      exposure: {
        direction: "spread",
        volume_mmbtu: 60000,
        risk: zh ? "等待 AI 生成具体业务敞口、曲线、目标动作和评分规则。" : "Waiting for AI to generate exposure, curves, target actions, and scoring rubric."
      }
    },
    market: {
      unit: "EUR/MWh",
      as_of: "2026-01-09",
      benchmark: "TTF",
      curve_metrics: { structure: "contango", front_price: 31.8, back_price: 33.0, front_back_spread: 1.2, percentage_slope: 0.0377 },
      provenance: { mode: "ai_simulated", label: zh ? "AI 模拟市场" : "AI-simulated market", source_tier: "synthetic", is_live: false, as_of: "2026-01-09" },
      forward_curve: [
        { tenor: "M+1", delivery_month: "2026-02", price: 31.8, bid: 31.74, ask: 31.86 },
        { tenor: "M+2", delivery_month: "2026-03", price: 32.2, bid: 32.14, ask: 32.26 },
        { tenor: "M+3", delivery_month: "2026-04", price: 32.7, bid: 32.64, ask: 32.76 },
        { tenor: "M+4", delivery_month: "2026-05", price: 33.0, bid: 32.94, ask: 33.06 }
      ],
      curves: [
        {
          id: "TTF",
          label: "TTF",
          color: "#38bdf8",
          points: [
            { date: "2026-01-05", open: 31.2, high: 32.4, low: 30.9, close: 31.8 },
            { date: "2026-01-06", open: 31.8, high: 33.1, low: 31.1, close: 32.7 },
            { date: "2026-01-07", open: 32.8, high: 34.0, low: 32.2, close: 33.4 },
            { date: "2026-01-08", open: 33.4, high: 33.8, low: 31.8, close: 32.2 },
            { date: "2026-01-09", open: 32.2, high: 33.4, low: 31.6, close: 33.0 }
          ]
        },
        {
          id: "NBP",
          label: "NBP",
          color: "#f59e0b",
          points: [
            { date: "2026-01-05", open: 74.0, high: 75.2, low: 72.7, close: 74.8 },
            { date: "2026-01-06", open: 74.8, high: 76.3, low: 73.9, close: 75.7 },
            { date: "2026-01-07", open: 75.8, high: 77.4, low: 74.8, close: 76.6 },
            { date: "2026-01-08", open: 76.4, high: 76.8, low: 74.2, close: 75.1 },
            { date: "2026-01-09", open: 75.1, high: 76.6, low: 74.1, close: 76.0 }
          ]
        }
      ],
      events: [{ date: "2026-01-07", label: zh ? "运力紧张" : "Capacity tightness" }]
    },
    target_actions: [
      { id: "physical-1", leg_type: "physical", market: "UK Beach GSA", side: "buy", quantity: 60000, tenor: "M+1", hedge_type: "basis_hedge", rationale: "Source physical gas." },
      { id: "basis-1", leg_type: "basis", market: "TTF/NBP basis swap", side: "sell", quantity: 60000, tenor: "M+1", hedge_type: "basis_hedge", rationale: "Lock hub spread." }
    ],
    rubric: [
      { id: "physical", label: zh ? "实货腿" : "Physical leg", points: 25, rule: "Include a physical purchase/sale leg." },
      { id: "paper", label: zh ? "纸货腿" : "Paper leg", points: 35, rule: "Include swap/future/basis paper hedge leg." },
      { id: "risk", label: zh ? "风险解释" : "Risk explanation", points: 25, rule: "Explain price, basis, FX, capacity, and tenor logic." },
      { id: "controls", label: zh ? "风控检查" : "Risk controls", points: 15, rule: "Mention liquidity, limits, credit, and execution window." }
    ],
    prompt: zh
      ? "### 决策任务\n构建一个实货 + 纸货的组合套保。说明每条腿覆盖什么风险，以及需要检查哪些风控条件。"
      : "### Decision task\nBuild a physical + paper hedge strategy. Explain what each leg covers and which risk controls must be checked."
  };
}

function crudeDefaultCase(locale) {
  const zh = normalizeLocale(locale) === "zh";
  return {
    scenario: {
      id: "crude_starter_case",
      title: zh ? "第一课：原油船货与基准风险" : "Lesson 1: Crude Cargo and Benchmark Risk",
      summary: zh
        ? "本课聚焦 Brent/WTI/Dubai 基准、实货船货敞口、纸货工具、月差/基差、库存和运费风险。"
        : "This lesson focuses on Brent/WTI/Dubai benchmarks, physical cargo exposure, paper hedges, calendar/basis spread, inventory, and freight risk.",
      business_type: zh ? "原油采购/销售套保" : "Crude procurement / sales hedging",
      knowledge_points: ["crude_benchmark_basis", "physical_paper_matching", "inventory_freight_roll", "risk_controls"],
      exposure: {
        direction: "long",
        volume_mmbtu: 100000,
        volume_unit: "bbl",
        risk: zh ? "Brent flat price、Brent/WTI 基差、装船窗口、库存和运费风险。" : "Brent flat price, Brent/WTI basis, loading window, inventory, and freight risk."
      }
    },
    market: {
      unit: "USD/bbl",
      as_of: "2026-01-09",
      benchmark: "Brent",
      curve_metrics: { structure: "backwardation", front_price: 73.6, back_price: 71.9, front_back_spread: -1.7, percentage_slope: -0.0231 },
      provenance: { mode: "ai_simulated", label: zh ? "AI 模拟市场" : "AI-simulated market", source_tier: "synthetic", is_live: false, as_of: "2026-01-09" },
      forward_curve: [
        { tenor: "M+1", delivery_month: "2026-02", price: 73.6, bid: 73.56, ask: 73.64 },
        { tenor: "M+2", delivery_month: "2026-03", price: 73.0, bid: 72.96, ask: 73.04 },
        { tenor: "M+3", delivery_month: "2026-04", price: 72.5, bid: 72.46, ask: 72.54 },
        { tenor: "M+4", delivery_month: "2026-05", price: 71.9, bid: 71.86, ask: 71.94 }
      ],
      curves: [
        {
          id: "BRENT",
          label: "Brent",
          color: "#2563eb",
          points: [
            { date: "2026-01-05", open: 72.4, high: 73.6, low: 71.8, close: 72.9 },
            { date: "2026-01-06", open: 72.9, high: 74.2, low: 72.1, close: 73.8 },
            { date: "2026-01-07", open: 73.9, high: 75.3, low: 73.0, close: 74.7 },
            { date: "2026-01-08", open: 74.6, high: 75.0, low: 72.5, close: 73.1 },
            { date: "2026-01-09", open: 73.2, high: 74.0, low: 72.4, close: 73.6 }
          ]
        },
        {
          id: "WTI",
          label: "WTI",
          color: "#f59e0b",
          points: [
            { date: "2026-01-05", open: 68.0, high: 68.9, low: 67.2, close: 68.3 },
            { date: "2026-01-06", open: 68.3, high: 69.5, low: 67.8, close: 69.0 },
            { date: "2026-01-07", open: 69.1, high: 70.3, low: 68.4, close: 69.7 },
            { date: "2026-01-08", open: 69.6, high: 70.0, low: 67.9, close: 68.5 },
            { date: "2026-01-09", open: 68.5, high: 69.4, low: 67.8, close: 69.0 }
          ]
        }
      ],
      events: [{ date: "2026-01-07", label: zh ? "运费走强" : "Freight tightness" }]
    },
    target_actions: [
      { id: "crude-physical-1", leg_type: "physical", market: "Brent-linked cargo", side: "buy", quantity: 100000, tenor: "M+1", hedge_type: "physical_exposure", rationale: "Source physical crude cargo." },
      { id: "crude-future-1", leg_type: "future", market: "ICE Brent future", side: "sell", quantity: 100000, tenor: "M+1", hedge_type: "short_hedge", rationale: "Lock flat-price exposure." },
      { id: "crude-basis-1", leg_type: "basis", market: "Brent/WTI basis", side: "sell", quantity: 100000, tenor: "M+1", hedge_type: "basis_hedge", rationale: "Manage benchmark/location basis." }
    ],
    rubric: [
      { id: "physical", label: zh ? "原油实货腿" : "Crude physical leg", points: 25, rule: "Include a crude cargo or inventory leg." },
      { id: "paper", label: zh ? "纸货套保腿" : "Paper hedge leg", points: 35, rule: "Include Brent/WTI future, swap, or basis hedge." },
      { id: "risk", label: zh ? "基准与库存解释" : "Benchmark and inventory explanation", points: 25, rule: "Explain flat price, calendar, benchmark basis, inventory, and freight." },
      { id: "controls", label: zh ? "风控检查" : "Risk controls", points: 15, rule: "Mention liquidity, margin, credit, roll, and execution window." }
    ],
    prompt: zh
      ? "### 决策任务\n构建一个原油实货船货 + 纸货的组合套保。说明 Brent/WTI 基准、月差/基差、库存、运费和风控检查。"
      : "### Decision task\nBuild a physical crude cargo + paper hedge strategy. Explain Brent/WTI benchmark risk, calendar/basis spread, inventory, freight, and risk controls."
  };
}

function defaultCaseForTemplate(templateId, locale) {
  return templateId === "crude_oil_hedging_basics" ? crudeDefaultCase(locale) : defaultCase(locale);
}

function provisionalCaseForTemplate(templateId, locale) {
  const base = defaultCaseForTemplate(templateId, locale);
  return {
    ...base,
    status: "generating",
    scenario: {
      ...base.scenario,
      title: copy(locale, "AI 正在构建训练案例", "AI is building the training case"),
      summary: copy(locale, "业务背景和学习任务将随生成结果逐步填充。", "Business context and the decision task will fill in as generation progresses."),
      business_type: copy(locale, "正在匹配课程与业务", "Matching curriculum and business"),
      knowledge_points: [],
      exposure: { direction: "", volume_mmbtu: null, risk: "" }
    },
    market: {
      ...base.market,
      unit: "",
      as_of: "",
      benchmark: "",
      curve_metrics: null,
      provenance: null,
      forward_curve: [],
      curves: [],
      events: []
    },
    target_actions: [],
    rubric: [],
    prompt: ""
  };
}

function defaultLegs(locale = "zh") {
  return [{
    id: `draft-${Date.now()}`,
    leg_type: "",
    market: "",
    side: "",
    quantity: 0,
    price: 0,
    tenor: "",
    hedge_type: ""
  }];
}

function replayBundleFromSession(session) {
  return {
    event: session.event,
    current_checkpoint: session.current_checkpoint,
    visible_timeline: session.visible_timeline,
    next_checkpoint: session.next_checkpoint,
    decision_rubric: session.decision_rubric,
    information_policy: session.information_policy,
    source_notes: session.source_notes
  };
}

function provisionalTrainingSession({ marketMode = "ai_simulated", marketRegime = "contango", productScope, replayId = null, templateId, userRequest = "" }) {
  return {
    id: `pending-${Date.now()}`,
    schema_version: "1.0",
    created_at: new Date().toISOString(),
    product_scope: productScope,
    template_id: templateId,
    learning_objective: userRequest,
    market: {
      requested_mode: marketMode,
      effective_mode: marketMode,
      regime: marketRegime,
      fallback_applied: false
    },
    replay: replayId ? { event_id: replayId, checkpoint: 0 } : null,
    scoring: { mode: "local_deterministic", rubric_version: "case-rubric-v1" },
    ai: { case_generated: true, workspace_control_enabled: true }
  };
}

function marketOptionsFromCase(caseData) {
  const session = caseData?.training_session ?? {};
  const market = session.market ?? {};
  return {
    market_mode: market.requested_mode ?? market.effective_mode ?? caseData?.market?.provenance?.mode ?? "ai_simulated",
    market_regime: market.regime ?? caseData?.market?.curve_metrics?.structure ?? "contango",
    replay_id: session.replay?.event_id ?? caseData?.market?.replay?.event?.id ?? null
  };
}

function trainingSessionForReplayCheckpoint(trainingSession, session) {
  if (!trainingSession) return trainingSession;
  return {
    ...trainingSession,
    market: {
      ...(trainingSession.market ?? {}),
      effective_mode: "historical_replay",
      benchmark: session.market?.benchmark,
      as_of: session.market?.as_of,
      source_tier: session.market?.provenance?.source_tier
    },
    replay: {
      event_id: session.event?.id,
      checkpoint: session.current_checkpoint?.index ?? 0,
      checkpoint_count: session.event?.checkpoint_count
    }
  };
}

function replayPrompt(session, locale) {
  const checkpoint = session.current_checkpoint ?? {};
  const facts = (checkpoint.facts ?? []).map((fact) => `- ${fact}`).join("\n");
  return copy(
    locale,
    `### ${checkpoint.label ?? "复盘节点"}\n\n${facts}\n\n**决策：** ${checkpoint.decision_required ?? ""}`,
    `### ${checkpoint.label ?? "Replay checkpoint"}\n\n${facts}\n\n**Decision:** ${checkpoint.decision_required ?? ""}`
  );
}

function sampleMarketHistory(points, count = 8) {
  if (!Array.isArray(points) || points.length <= count) return points ?? [];
  const indexes = new Set(Array.from({ length: count }, (_, index) => Math.round(index * (points.length - 1) / (count - 1))));
  return [...indexes].map((index) => points[index]);
}

function applyStreamedMarketContext(current, context, locale) {
  const benchmark = context.benchmark ?? current.market?.benchmark ?? "MARKET";
  const history = sampleMarketHistory(context.history ?? [], 8);
  const replay = context.replay;
  const market = {
    ...(current.market ?? {}),
    unit: context.unit ?? current.market?.unit,
    as_of: context.as_of,
    benchmark,
    curve_metrics: context.curve_metrics,
    forward_curve: context.forward_curve ?? [],
    provenance: context.provenance,
    curves: history.length ? [{ id: benchmark, label: context.label ?? benchmark, color: "#0ea5e9", points: history }] : current.market?.curves ?? [],
    replay,
    events: replay?.visible_timeline?.map((item) => ({ date: item.date, label: item.label })) ?? current.market?.events ?? []
  };
  if (!replay?.event) return { ...current, market };
  const checkpoint = replay.current_checkpoint ?? {};
  return {
    ...current,
    scenario: {
      ...current.scenario,
      title: replay.event.title,
      summary: replay.event.summary,
      business_type: replay.event.commodity === "natural_gas"
        ? copy(locale, "天然气历史复盘", "Natural Gas Historical Replay")
        : copy(locale, "原油历史复盘", "Crude Oil Historical Replay"),
      knowledge_points: replay.event.skills,
      exposure: {
        ...(current.scenario?.exposure ?? {}),
        ...(replay.event.exposure ?? {}),
        risk: checkpoint.decision_required
      }
    },
    market,
    target_actions: [],
    rubric: replay.decision_rubric ?? current.rubric,
    prompt: replayPrompt({ current_checkpoint: checkpoint }, locale)
  };
}

function partialJsonString(buffer, key) {
  const source = String(buffer ?? "");
  const prefix = new RegExp(`"${key}"\\s*:\\s*"`).exec(source);
  if (!prefix) return "";
  let raw = "";
  let escaped = false;
  for (let index = prefix.index + prefix[0].length; index < source.length; index += 1) {
    const character = source[index];
    if (escaped) {
      raw += `\\${character}`;
      escaped = false;
      continue;
    }
    if (character === "\\") {
      escaped = true;
      continue;
    }
    if (character === '"') break;
    raw += character;
  }
  try {
    return JSON.parse(`"${raw}"`);
  } catch {
    return raw.replace(/\\n/g, "\n").replace(/\\"/g, '"').replace(/\\\\/g, "\\");
  }
}

function streamedCasePreview(buffer) {
  return {
    title: partialJsonString(buffer, "title"),
    summary: partialJsonString(buffer, "summary"),
    business_type: partialJsonString(buffer, "business_type")
  };
}

function generationStageLabel(id, locale, fallback = "") {
  const labels = {
    read_template: ["读取课程范围", "Reading lesson scope"],
    resolve_market: ["建立行情与证据", "Building market evidence"],
    generate_market: ["DeepSeek 编排业务场景", "DeepSeek composing the business scenario"],
    parse_case: ["写入题目与评分规则", "Applying task and scoring rubric"],
    stream_fallback: ["切换供应方兼容模式", "Switching provider compatibility mode"]
  };
  const label = labels[id];
  return label ? copy(locale, label[0], label[1]) : fallback;
}

const assistantAutoActionTypes = [
  "patch_case",
  "set_market_curves",
  "set_chart_fields",
  "set_strategy_legs",
  "fill_rationale",
  "set_exam",
  "submit_strategy",
  "set_learning_plan",
  "set_learning_goal",
  "navigate_page",
  "configure_market_session",
  "generate_case",
  "select_template",
  "run_ai_capability"
];

const assistantLocalActionTypes = [
  "patch_case",
  "set_market_curves",
  "set_chart_fields",
  "set_strategy_legs",
  "fill_rationale",
  "set_exam",
  "submit_strategy",
  "set_learning_plan",
  "set_learning_goal",
  "navigate_page"
];

function normalizeAssistantLegs(legs) {
  return (Array.isArray(legs) ? legs : []).map((leg, index) => ({ id: leg.id ?? `assistant-leg-${index}`, ...leg }));
}

function mergeCasePatch(currentCase, patch) {
  const next = { ...(currentCase ?? defaultCase("zh")) };
  if (patch.scenario && typeof patch.scenario === "object") {
    next.scenario = {
      ...(next.scenario ?? {}),
      ...patch.scenario,
      exposure: {
        ...(next.scenario?.exposure ?? {}),
        ...(patch.scenario.exposure ?? {})
      }
    };
  }
  if (patch.market && typeof patch.market === "object") {
    next.market = {
      ...(next.market ?? {}),
      ...patch.market,
      curves: Array.isArray(patch.market.curves) ? patch.market.curves : next.market?.curves,
      events: Array.isArray(patch.market.events) ? patch.market.events : next.market?.events
    };
  }
  if (Array.isArray(patch.target_actions)) next.target_actions = patch.target_actions;
  if (Array.isArray(patch.rubric)) next.rubric = patch.rubric;
  if (typeof patch.prompt === "string" && patch.prompt.trim()) next.prompt = patch.prompt;
  return next;
}

function providerCatalog(status) {
  return status?.ai_providers ?? defaultProviderCatalog;
}

function providerConfig(catalog, provider) {
  return catalog[provider] ?? catalog.haineng ?? defaultProviderCatalog.haineng;
}

function modelConfig(catalog, provider, model) {
  const config = providerConfig(catalog, provider);
  return config.models.find((option) => option.id === model) ?? config.models[0];
}

function modelFromBaseUrl(provider, baseUrl, catalog = defaultProviderCatalog) {
  const config = providerConfig(catalog, provider);
  const url = String(baseUrl ?? "").trim().toLowerCase();
  if (!url) return "";
  const match = config.models.find((option) => {
    const candidate = String(option.base_url ?? "").trim().toLowerCase();
    return candidate && (candidate === url || url.includes(candidate) || candidate.includes(url));
  });
  return match?.id ?? "";
}

function baseUrlMatchesProvider(provider, value) {
  const url = String(value ?? "").trim().toLowerCase();
  if (!url) return false;
  if (provider === "deepseek") return url.includes("api.deepseek.com");
  if (provider === "haineng") return url.includes("model.ai.cnooc") || url.includes("cnooc");
  return true;
}

function compactKey(value) {
  return String(value ?? "").trim().toLowerCase().replaceAll("_", "-").replaceAll(" ", "");
}

function configKeyCandidates(key) {
  const raw = String(key ?? "").trim().toLowerCase();
  const compact = compactKey(key);
  return [compact, compact.replaceAll("-", ""), raw, raw.replace(/[-_\s]/g, "")];
}

function cleanConfigValue(value) {
  let cleaned = String(value ?? "").trim();
  cleaned = cleaned.replace(/[,\)]$/g, "").trim();
  if ((cleaned.startsWith("\"") && cleaned.endsWith("\"")) || (cleaned.startsWith("'") && cleaned.endsWith("'")) || (cleaned.startsWith("`") && cleaned.endsWith("`"))) {
    cleaned = cleaned.slice(1, -1).trim();
  }
  return cleaned;
}

function normalizeProviderName(value, baseUrl = "") {
  const provider = compactKey(value);
  const url = String(baseUrl ?? "").toLowerCase();
  if (provider === "deepseek" || provider === "deep-seek" || provider === "ds" || url.includes("api.deepseek.com")) return "deepseek";
  return "haineng";
}

function firstConfigValue(payload, ...keys) {
  for (const key of keys) {
    const value = configKeyCandidates(key).map((candidate) => payload[candidate]).find((candidate) => candidate != null && String(candidate).trim());
    if (value != null && String(value).trim()) return String(value).trim();
  }
  return "";
}

function parseAiKeyFile(text) {
  const raw = String(text ?? "").trim();
  if (!raw) throw new Error("AI key file is empty.");
  if (raw.startsWith("{")) {
    const parsed = JSON.parse(raw);
    return Object.fromEntries(Object.entries(parsed).map(([key, value]) => [compactKey(key), cleanConfigValue(value)]));
  }
  const payload = {};
  const assignmentPattern = /\b(provider|ai_provider|api_key|apikey|key|base_url|baseurl|url|model|haineng_api_key|deepseek_api_key|haineng_base_url|deepseek_base_url|haineng_model|deepseek_model)\b(?:\s*:\s*[^=,\)\r\n#]+)?\s*=\s*("[^"]*"|'[^']*'|`[^`]*`|[^,\)\r\n#]+)/gi;
  raw.replace(assignmentPattern, (_, key, value) => {
    const payloadKey = compactKey(key);
    const cleaned = cleanConfigValue(value);
    if (payloadKey === compactKey(cleaned)) return "";
    payload[payloadKey] = cleaned;
    return "";
  });
  raw.split(/\r?\n/).forEach((line) => {
    const current = line.trim();
    if (!current || current.startsWith("#")) return;
    const index = current.includes("=") ? current.indexOf("=") : current.indexOf(":");
    if (index <= 0) return;
    payload[compactKey(current.slice(0, index))] = cleanConfigValue(current.slice(index + 1));
  });
  if (!Object.keys(payload).length && !/[\r\n=:]/.test(raw)) {
    payload["api-key"] = cleanConfigValue(raw);
  }
  return payload;
}

function modelForProvider(provider, model, config) {
  const normalized = compactKey(model);
  const aliases = {
    haineng: {
      "v4-flash": "DeepSeek-V4-Flash",
      v4flash: "DeepSeek-V4-Flash",
      "deepseek-v4-flash": "DeepSeek-V4-Flash",
      deepseekv4flash: "DeepSeek-V4-Flash",
      "v4-pro": "DeepSeek-V4",
      v4pro: "DeepSeek-V4",
      "deepseek-v4": "DeepSeek-V4",
      deepseekv4: "DeepSeek-V4",
      "deepseek-v4-pro": "DeepSeek-V4",
      deepseekv4pro: "DeepSeek-V4"
    },
    deepseek: {
      "v4-flash": "deepseek-v4-flash",
      v4flash: "deepseek-v4-flash",
      "deepseek-v4-flash": "deepseek-v4-flash",
      "v4-pro": "deepseek-v4-pro",
      v4pro: "deepseek-v4-pro",
      "deepseek-v4-pro": "deepseek-v4-pro"
    }
  };
  const mapped = aliases[provider]?.[normalized] ?? model;
  return config.models.some((option) => option.id === mapped) ? mapped : config.default_model;
}

function formFromAiKeyFile(text, catalog = defaultProviderCatalog, options = {}) {
  const payload = parseAiKeyFile(text);
  const baseUrlHint = firstConfigValue(payload, "base_url", "url", "haineng_base_url", "deepseek_base_url");
  const provider = normalizeProviderName(firstConfigValue(payload, "provider", "ai_provider") || options.currentProvider, baseUrlHint);
  const config = providerConfig(catalog, provider);
  const providerPrefix = provider === "deepseek" ? "deepseek" : "haineng";
  const apiKey = firstConfigValue(payload, "api_key", "apikey", "key", `${providerPrefix}_api_key`);
  if (!apiKey) throw new Error("AI key file is missing api_key.");
  const model = config.default_model;
  const selected = modelConfig(catalog, provider, model);
  return {
    api_key: apiKey,
    provider,
    model,
    base_url: selected?.base_url || ""
  };
}

function formForProvider(provider, catalog = defaultProviderCatalog, apiKey = "") {
  const config = providerConfig(catalog, provider);
  const model = config.default_model;
  const selected = modelConfig(catalog, provider, model);
  return {
    api_key: apiKey,
    provider,
    model,
    base_url: selected?.base_url ?? ""
  };
}

function orderFromStrategy(strategyLegs) {
  const leg = strategyLegs.find((item) => ["swap", "future", "basis", "paper", "option"].includes(item.leg_type)) ?? strategyLegs[0];
  return {
    side: leg?.side === "buy" ? "buy" : "sell",
    quantity: Number(leg?.quantity) || 0,
    hedge_type: leg?.hedge_type || "basis_hedge",
    price: Number(leg?.price) || 0
  };
}

function evaluateStrategy(caseData, legs, rationale) {
  const rubric = caseData.rubric ?? [];
  const normalizedRationale = String(rationale ?? "").trim();
  const rationaleText = normalizedRationale.toLowerCase();
  const hasPhysical = legs.some((leg) => ["physical", "gsa", "lng", "efet"].includes(leg.leg_type));
  const hasPaper = legs.some((leg) => ["swap", "future", "basis", "paper", "option"].includes(leg.leg_type));
  const targets = caseData.target_actions ?? [];
  const usedLegs = new Set();
  const mismatches = new Set();
  const normalized = (value) => String(value ?? "").trim().toLowerCase().replace(/\s+/g, " ");
  const marketMatch = (actual, expected) => {
    const left = normalized(actual);
    const right = normalized(expected);
    return !right || left === right || left.includes(right) || right.includes(left);
  };
  const quantityMatch = (actual, expected) => {
    const targetQuantity = Number(expected);
    if (!Number.isFinite(targetQuantity) || targetQuantity <= 0) return true;
    const ratio = Number(actual) / targetQuantity;
    return Number.isFinite(ratio) && ratio >= 0.9 && ratio <= 1.1;
  };
  let actionQuality = 0;
  for (const target of targets) {
    const candidateIndex = legs.findIndex((leg, index) => !usedLegs.has(index) && normalized(leg.leg_type) === normalized(target.leg_type));
    if (candidateIndex < 0) {
      mismatches.add("incomplete_target_legs");
      continue;
    }
    usedLegs.add(candidateIndex);
    const candidate = legs[candidateIndex];
    let quality = 0.4;
    if (!target.side || normalized(candidate.side) === normalized(target.side)) quality += 0.2;
    else mismatches.add("wrong_direction");
    if (marketMatch(candidate.market, target.market)) quality += 0.15;
    else mismatches.add("market_mismatch");
    if (quantityMatch(candidate.quantity, target.quantity)) quality += 0.15;
    else mismatches.add("quantity_mismatch");
    if (!target.tenor || normalized(candidate.tenor) === normalized(target.tenor)) quality += 0.1;
    else mismatches.add("tenor_mismatch");
    actionQuality += quality;
  }
  if (!targets.length) {
    actionQuality = (hasPhysical ? 0.5 : 0) + (hasPaper ? 0.5 : 0);
  } else {
    actionQuality /= targets.length;
  }

  const explainsRisk = /(risk|basis|spread|price|exposure|option|volatility|风险|基差|价差|价格|敞口|期权|波动)/i.test(rationaleText);
  const explainsControls = /(liquidity|credit|limit|margin|execution|settlement|counterparty|流动性|信用|限额|保证金|执行|结算|对手方)/i.test(rationaleText);
  const hasAdequateRationale = normalizedRationale.length >= 32;
  const rationaleScore = (hasAdequateRationale ? 10 : 0) + (explainsRisk ? 10 : 0) + (explainsControls ? 10 : 0);
  const baseline = Math.max(0, Math.min(100, Math.round(actionQuality * 70 + rationaleScore)));
  if (!hasAdequateRationale) mismatches.add("insufficient_rationale");
  if (!explainsRisk) mismatches.add("missing_risk_explanation");
  if (!explainsControls) mismatches.add("missing_execution_controls");
  return {
    valid: true,
    baseline_score: baseline,
    rubric,
    target_actions: caseData.target_actions ?? [],
    strategy_legs: legs,
    mistake_tags: [
      ...(!hasPhysical ? ["missing_physical_leg"] : []),
      ...(!hasPaper ? ["missing_paper_leg"] : []),
      ...mismatches
    ],
    metrics: {
      strategy_leg_count: legs.length,
      physical_leg_count: legs.filter((leg) => ["physical", "gsa", "lng", "efet"].includes(leg.leg_type)).length,
      paper_leg_count: legs.filter((leg) => ["swap", "future", "basis", "paper", "option"].includes(leg.leg_type)).length,
      fx_leg_count: legs.filter((leg) => leg.leg_type === "fx").length,
      notional_usd: legs.reduce((sum, leg) => sum + (Number(leg.quantity) || 0) * (Number(leg.price) || 0), 0)
    }
  };
}

const riskCoverageDefinitions = [
  {
    id: "physical",
    labelZh: "实货敞口",
    labelEn: "Physical exposure",
    legTypes: ["physical", "gsa", "lng", "efet"]
  },
  {
    id: "paper",
    labelZh: "纸货套保",
    labelEn: "Paper hedge",
    legTypes: ["swap", "future", "paper", "option"]
  },
  {
    id: "basis",
    labelZh: "基差/地点风险",
    labelEn: "Basis / location risk",
    legTypes: ["basis"]
  },
  {
    id: "fx",
    labelZh: "汇率风险",
    labelEn: "FX risk",
    legTypes: ["fx"]
  },
  {
    id: "capacity",
    labelZh: "运力/物流风险",
    labelEn: "Capacity / logistics risk",
    legTypes: ["capacity"]
  }
];

function legRiskId(leg) {
  const type = String(leg?.leg_type ?? "").toLowerCase();
  const contract = `${leg?.market ?? ""} ${leg?.hedge_type ?? ""}`.toLowerCase();
  if (type === "basis" || /\b(?:basis|spread)\b|ttf.*nbp|nbp.*ttf|brent.*wti|wti.*brent|brent.*dubai|dubai.*brent/.test(contract)) return "basis";
  return riskCoverageDefinitions.find((definition) => definition.legTypes.includes(type))?.id ?? "paper";
}

function describeLegForCoverage(leg, locale) {
  const market = leg?.market || copy(locale, "未命名工具", "unnamed instrument");
  return copy(locale, `由 ${market} 覆盖`, `Covered by ${market}`);
}

function buildRiskCoverageRows(caseData, strategyLegs, locale) {
  const rows = riskCoverageDefinitions.map((definition) => {
    const legs = strategyLegs.filter((leg) => legRiskId(leg) === definition.id);
    const targetCount = (caseData.target_actions ?? []).filter((leg) => legRiskId(leg) === definition.id).length;
    return {
      ...definition,
      label: copy(locale, definition.labelZh, definition.labelEn),
      legs,
      targetCount,
      covered: legs.length > 0
    };
  });
  const currentKeys = new Set(strategyLegs.map((leg) => `${String(leg.leg_type).toLowerCase()}::${String(leg.market).toLowerCase()}`));
  const missingTargets = (caseData.target_actions ?? []).filter((leg) => !currentKeys.has(`${String(leg.leg_type).toLowerCase()}::${String(leg.market).toLowerCase()}`));
  return { rows, missingTargets };
}

function clampScore(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return null;
  return Math.max(0, Math.min(100, Math.round(number)));
}

function averageScore(values) {
  const numbers = values.map((value) => Number(value)).filter(Number.isFinite);
  if (!numbers.length) return null;
  return clampScore(numbers.reduce((sum, value) => sum + value, 0) / numbers.length);
}

function loadLearningRecords() {
  if (typeof localStorage === "undefined") return [];
  const parsed = parseSafeJson(localStorage.getItem(learningRecordsKey));
  if (!Array.isArray(parsed)) return [];
  return parsed.filter((record) => Number.isFinite(Number(record?.evaluation?.baseline_score))).slice(-120);
}

function saveLearningRecords(records) {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(learningRecordsKey, JSON.stringify(records.slice(-120)));
}

function loadAiLessonPlan() {
  if (typeof localStorage === "undefined") return null;
  const parsed = parseSafeJson(localStorage.getItem(aiLessonPlanKey));
  if (!parsed || typeof parsed !== "object") return null;
  return parsed;
}

function saveAiLessonPlan(plan) {
  if (typeof localStorage === "undefined") return;
  if (!plan) {
    localStorage.removeItem(aiLessonPlanKey);
    return;
  }
  localStorage.setItem(aiLessonPlanKey, JSON.stringify(plan));
}

function reviewSnapshot(caseData) {
  const market = caseData?.market ?? {};
  return {
    scenario: caseData?.scenario ?? {},
    prompt: caseData?.prompt ?? "",
    target_actions: caseData?.target_actions ?? [],
    rubric: caseData?.rubric ?? [],
    market: {
      benchmark: market.benchmark ?? null,
      unit: market.unit ?? null,
      as_of: market.as_of ?? null,
      curve_metrics: market.curve_metrics ?? null,
      provenance: market.provenance ?? null,
      replay: market.replay ?? null
    },
    training_session: caseData?.training_session ?? null
  };
}

function recordLearningAttempt({ activeTemplateId, advisorFeedback = "", aiInterventions = [], caseData, evaluation, productScope, rationale, replayResult = null, strategyLegs }) {
  const trainingSession = caseData?.training_session ?? null;
  const market = trainingSession?.market ?? {};
  const replay = trainingSession?.replay ?? null;
  return {
    id: `attempt-${Date.now()}`,
    created_at: new Date().toISOString(),
    template_id: activeTemplateId,
    scenario_id: caseData?.scenario?.id ?? activeTemplateId,
    scenario_title: caseData?.scenario?.title ?? "",
    product_scope: productScopeForTemplate(activeTemplateId) === "general" ? "general" : productScope,
    session_id: trainingSession?.id ?? null,
    training_session: trainingSession,
    market_mode: market.requested_mode ?? market.effective_mode ?? caseData?.market?.provenance?.mode ?? "ai_simulated",
    evidence_snapshot: {
      benchmark: market.benchmark ?? caseData?.market?.benchmark ?? null,
      as_of: market.as_of ?? caseData?.market?.as_of ?? null,
      source_tier: market.source_tier ?? caseData?.market?.provenance?.source_tier ?? null,
      fallback_applied: Boolean(market.fallback_applied)
    },
    replay_checkpoint: replay ? { ...replay } : null,
    ai_actions: aiInterventions.slice(0, 8).map(({ kind, label, page }) => ({ kind, label, page })),
    case_snapshot: reviewSnapshot(caseData),
    advisor_feedback: advisorFeedback,
    replay_result: replayResult,
    evaluation,
    rationale,
    strategy_legs: strategyLegs
  };
}

function trackForId(trackId) {
  return learningTracks.find((track) => track.id === trackId) ?? learningTracks[0];
}

function syllabusForTrack(trackId) {
  return courseSyllabus.find((item) => item.trackId === trackId) ?? courseSyllabus[0];
}

function attemptsForTrack(learningProgress, track) {
  return learningProgress?.scenarioStats?.[track.templateId] ?? { attempts: 0, score: null };
}

function recommendedTrackId(learningProgress, productScope = "natural_gas") {
  const tracks = tracksForProduct(productScope);
  if (!learningProgress?.hasRecords) return tracks[0]?.id ?? "foundation";
  const unattempted = tracks.find((track) => !attemptsForTrack(learningProgress, track).attempts);
  if (unattempted) return unattempted.id;
  const weakestId = learningProgress.weakest?.[0]?.id;
  return tracks.find((track) => (trackSkillFocus[track.id] ?? []).includes(weakestId))?.id ?? tracks.at(-1)?.id ?? "foundation";
}

function selectedTrackForProduct(trackId, learningProgress, productScope) {
  const tracks = tracksForProduct(productScope);
  return tracks.find((track) => track.id === trackId)
    ?? tracks.find((track) => track.id === recommendedTrackId(learningProgress, productScope))
    ?? tracks[0];
}

function normalizeLearningPlan(payload, learningProgress, productScope = "natural_gas") {
  const allowedTracks = tracksForProduct(productScope);
  const requestedTrack = allowedTracks.find((item) => item.id === (payload.track_id ?? payload.trackId));
  const track = requestedTrack ?? trackForId(recommendedTrackId(learningProgress, productScope));
  const syllabus = syllabusForTrack(track.id);
  const fallbackSteps = syllabus.lessons.slice(0, 3).map((lesson) => lesson.titleZh);
  return {
    id: `plan-${Date.now()}`,
    track_id: track.id,
    product_scope: productScope,
    lesson_id: payload.lesson_id ?? payload.lessonId ?? syllabus.lessons[0]?.id,
    title: String(payload.title ?? payload.goal ?? track.zh ?? track.en),
    objective: String(payload.objective ?? payload.summary ?? track.detailZh ?? track.detailEn),
    steps: Array.isArray(payload.steps) && payload.steps.length ? payload.steps.map(String).slice(0, 5) : fallbackSteps,
    practice_prompt: String(payload.practice_prompt ?? payload.practicePrompt ?? track.requestZh ?? track.requestEn),
    created_at: new Date().toISOString()
  };
}

function recordText(record) {
  return `${record?.rationale ?? ""} ${(record?.strategy_legs ?? []).map((leg) => `${leg.leg_type} ${leg.market} ${leg.side} ${leg.hedge_type}`).join(" ")}`.toLowerCase();
}

function scoreDimension(record, dimensionId) {
  const evaluation = record?.evaluation ?? {};
  const baseline = clampScore(evaluation.baseline_score);
  if (baseline == null) return null;
  if (record?.assessment_type === "exam") {
    const skillScore = evaluation.skill_scores?.[dimensionId];
    return skillScore == null ? null : clampScore(skillScore);
  }
  const metrics = evaluation.metrics ?? {};
  const legs = record?.strategy_legs ?? evaluation.strategy_legs ?? [];
  const targetTypes = new Set((evaluation.target_actions ?? []).map((leg) => leg.leg_type));
  const legTypes = new Set(legs.map((leg) => leg.leg_type));
  const mistakes = new Set(evaluation.mistake_tags ?? []);
  const text = recordText(record);
  const hasPhysical = Number(metrics.physical_leg_count) > 0 || ["physical", "gsa", "lng", "efet"].some((type) => legTypes.has(type));
  const hasPaper = Number(metrics.paper_leg_count) > 0 || ["swap", "future", "basis", "paper", "option"].some((type) => legTypes.has(type));
  const matchedCount = legs.filter((leg) => targetTypes.has(leg.leg_type)).length;
  const targetCount = Math.max(1, targetTypes.size);
  const matchedRatio = Math.min(1, matchedCount / targetCount);
  const mentionsBasis = /(basis|spread|nbp|ttf|基差|价差)/i.test(text) || targetTypes.has("basis") || legTypes.has("basis");
  const mentionsFx = /(fx|foreign exchange|currency|eur|gbp|usd|汇率|外汇)/i.test(text) || targetTypes.has("fx") || legTypes.has("fx");
  const mentionsCapacity = /(capacity|pipeline|routing|transport|regas|运力|管输|气化|物流)/i.test(text) || targetTypes.has("capacity") || legTypes.has("capacity");
  const mentionsOption = /(option|cap|floor|collar|swing|期权|上限|下限|领口|摆动)/i.test(text) || targetTypes.has("option") || legTypes.has("option");
  const mentionsTiming = /(tenor|month|window|execution|timing|m\+|期限|窗口|执行|交割)/i.test(text);
  const mentionsControl = /(limit|liquidity|credit|margin|collateral|stop|VaR|风控|限额|流动性|信用|保证金)/i.test(text);
  const rationaleLength = String(record?.rationale ?? "").trim().length;

  if (dimensionId === "exposure") {
    return clampScore(baseline + (hasPhysical ? 6 : -18) + (mistakes.has("incomplete_target_legs") ? -10 : 0));
  }
  if (dimensionId === "instrument") {
    return clampScore(baseline + (hasPaper ? 6 : -16) + (mentionsOption ? 3 : 0) + matchedRatio * 12 - 6);
  }
  if (dimensionId === "basis") {
    if (!mentionsBasis) return null;
    return clampScore(baseline + (legTypes.has("basis") || /basis|spread|基差|价差/i.test(text) ? 8 : -18));
  }
  if (dimensionId === "fx") {
    if (!mentionsFx) return null;
    return clampScore(baseline + (legTypes.has("fx") || /fx|eur|gbp|usd|汇率|外汇/i.test(text) ? 8 : -20));
  }
  if (dimensionId === "capacity") {
    if (!mentionsCapacity) return null;
    return clampScore(baseline + (legTypes.has("capacity") || /capacity|pipeline|运力|管输|物流/i.test(text) ? 8 : -18));
  }
  if (dimensionId === "timing") {
    return clampScore(baseline + (mentionsTiming ? 8 : -14));
  }
  if (dimensionId === "control") {
    return clampScore(baseline + (mentionsControl ? 8 : -18));
  }
  if (dimensionId === "rationale") {
    return clampScore(baseline + (rationaleLength >= 120 ? 8 : rationaleLength >= 60 ? 0 : -18));
  }
  return null;
}

function summarizeLearningRecords(records) {
  const valid = records.filter((record) => Number.isFinite(Number(record?.evaluation?.baseline_score)));
  const latest = valid.at(-1) ?? null;
  const dimensions = skillDimensions.map((dimension) => {
    const scores = valid.map((record) => scoreDimension(record, dimension.id)).filter((score) => score != null);
    return { ...dimension, score: averageScore(scores), samples: scores.length };
  });
  const scenarioStats = valid.reduce((stats, record) => {
    const ids = [...new Set([record.template_id, record.scenario_id].filter(Boolean))];
    ids.forEach((id) => {
      const current = stats[id] ?? { attempts: 0, scores: [], latest: null };
      current.attempts += 1;
      current.scores.push(Number(record.evaluation.baseline_score));
      current.latest = record;
      stats[id] = current;
    });
    return stats;
  }, {});
  Object.keys(scenarioStats).forEach((key) => {
    const current = scenarioStats[key];
    const score = averageScore(current.scores);
    const lastAttemptAt = current.latest?.created_at ?? null;
    const intervalDays = score == null ? 1 : score < 70 ? 1 : score < 85 ? 3 : 7;
    const nextReviewAt = lastAttemptAt
      ? new Date(new Date(lastAttemptAt).getTime() + intervalDays * 24 * 60 * 60 * 1000).toISOString()
      : null;
    scenarioStats[key] = {
      attempts: current.attempts,
      score,
      latest: current.latest,
      lastAttemptAt,
      nextReviewAt,
      due: Boolean(nextReviewAt && new Date(nextReviewAt).getTime() <= Date.now())
    };
  });
  const weakest = dimensions.filter((dimension) => dimension.score != null).sort((a, b) => a.score - b.score).slice(0, 3);
  const sessionIds = new Set(valid.map((record) => record.session_id).filter(Boolean));
  const marketModes = valid.reduce((counts, record) => {
    const mode = record.market_mode ?? record.training_session?.market?.requested_mode ?? "ai_simulated";
    counts[mode] = (counts[mode] ?? 0) + 1;
    return counts;
  }, {});
  const reviewQueue = Object.entries(scenarioStats)
    .filter(([scenarioId, stat]) => stat.latest?.template_id === scenarioId)
    .map(([scenarioId, stat]) => ({ scenarioId, ...stat }))
    .filter((item) => item.nextReviewAt)
    .sort((a, b) => new Date(a.nextReviewAt).getTime() - new Date(b.nextReviewAt).getTime());
  return {
    hasRecords: valid.length > 0,
    attempts: valid.length,
    latest,
    latestScore: clampScore(latest?.evaluation?.baseline_score),
    averageScore: averageScore(valid.map((record) => record.evaluation.baseline_score)),
    sessions: sessionIds.size || valid.length,
    marketModes,
    replayCheckpoints: valid.filter((record) => record.replay_checkpoint).length,
    aiCustomizedAttempts: valid.filter((record) => record.ai_actions?.length).length,
    dimensions,
    scenarioStats,
    weakest,
    reviewQueue,
    dueReviews: reviewQueue.filter((item) => item.due).length,
    nextReview: reviewQueue[0] ?? null
  };
}

function parseSafeJson(value) {
  if (!value || typeof value !== "string") return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function MarkdownText({ text }) {
  const lines = String(text ?? "").split("\n");
  const inline = (value) =>
    String(value)
      .split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
      .filter(Boolean)
      .map((part, index) => {
        if (part.startsWith("**") && part.endsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
        if (part.startsWith("`") && part.endsWith("`")) return <code key={index}>{part.slice(1, -1)}</code>;
        return <React.Fragment key={index}>{part}</React.Fragment>;
      });

  const nodes = [];
  let paragraph = [];
  let list = [];
  let listType = null;

  function flushParagraph() {
    if (!paragraph.length) return;
    nodes.push({ type: "paragraph", text: paragraph.join(" ") });
    paragraph = [];
  }
  function flushList() {
    if (!list.length) return;
    nodes.push({ type: listType, items: list });
    list = [];
    listType = null;
  }

  lines.forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      flushParagraph();
      flushList();
      return;
    }
    const heading = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      flushList();
      nodes.push({ type: `h${Math.min(4, heading[1].length + 2)}`, text: heading[2] });
      return;
    }
    const bullet = trimmed.match(/^[-*]\s+(.+)$/);
    const ordered = trimmed.match(/^\d+\.\s+(.+)$/);
    if (bullet || ordered) {
      flushParagraph();
      const nextType = bullet ? "ul" : "ol";
      if (listType && listType !== nextType) flushList();
      listType = nextType;
      list.push((bullet || ordered)[1]);
      return;
    }
    flushList();
    paragraph.push(trimmed);
  });
  flushParagraph();
  flushList();

  return (
    <div className="markdown-output">
      {nodes.map((node, index) => {
        if (/^h[1-4]$/.test(node.type)) {
          const Tag = node.type;
          return <Tag key={index}>{inline(node.text)}</Tag>;
        }
        if (node.type === "ul") {
          return <ul key={index}>{node.items.map((item, itemIndex) => <li key={itemIndex}>{inline(item)}</li>)}</ul>;
        }
        if (node.type === "ol") {
          return <ol key={index}>{node.items.map((item, itemIndex) => <li key={itemIndex}>{inline(item)}</li>)}</ol>;
        }
        return <p key={index}>{inline(node.text)}</p>;
      })}
    </div>
  );
}

function Icon({ name }) {
  const icons = {
    arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
    book: <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5Z" />,
    chart: <path d="M4 19V5M4 19h16M8 15l3-4 3 2 4-7" />,
    coach: <path d="M12 3l7 4v5c0 4.5-2.8 7.4-7 9-4.2-1.6-7-4.5-7-9V7l7-4Z" />,
    close: <path d="M6 6l12 12M18 6L6 18" />,
    flame: <path d="M12 22c3.6 0 6.5-2.4 6.5-6.3 0-2.5-1.4-4.7-3.4-6.4-.7 1.7-1.8 2.8-3.1 3.4.4-3.6-1.3-6.2-4.3-8.7.2 3-1.3 4.8-2.3 6.3A8.4 8.4 0 0 0 4 15.7C4 19.6 8.4 22 12 22Z" />,
    folder: <path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H10l2 2h6.5A2.5 2.5 0 0 1 21 9.5V17a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 17Z" />,
    globe: <path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM3.6 9h16.8M3.6 15h16.8M12 3c2.2 2.5 3.2 5.5 3.2 9s-1 6.5-3.2 9c-2.2-2.5-3.2-5.5-3.2-9S9.8 5.5 12 3Z" />,
    grid: <path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z" />,
    home: <path d="M3 11l9-8 9 8M5 10v10h14V10M9 20v-6h6v6" />,
    history: <path d="M4 5v5h5M5.6 16.5A8 8 0 1 0 5 8M12 7v5l3 2" />,
    library: <path d="M4 19V5a2 2 0 0 1 2-2h12v18H6a2 2 0 0 1-2-2ZM8 7h7M8 11h7" />,
    map: <path d="M9 18l-6 3V6l6-3 6 3 6-3v15l-6 3-6-3ZM9 3v15M15 6v15" />,
    play: <path d="M8 5v14l11-7Z" />,
    plus: <path d="M12 5v14M5 12h14" />,
    progress: <path d="M4 19h16M7 16V9M12 16V5M17 16v-4" />,
    pulse: <path d="M3 12h4l2-6 4 12 2-6h6" />,
    refresh: <path d="M20 7v5h-5M4 17v-5h5M6.1 8.5A7 7 0 0 1 18.7 7M17.9 15.5A7 7 0 0 1 5.3 17" />,
    search: <path d="M10.5 18a7.5 7.5 0 1 1 5.3-2.2L21 21" />,
    settings: (
      <>
        <path d="M12 8.4A3.6 3.6 0 1 0 12 15.6A3.6 3.6 0 0 0 12 8.4Z" />
        <path d="M19.4 15a1.9 1.9 0 0 0 .38 2.1l.04.04a2.2 2.2 0 0 1-3.11 3.11l-.04-.04a1.9 1.9 0 0 0-2.1-.38 1.9 1.9 0 0 0-1.15 1.74V22a2.2 2.2 0 0 1-4.4 0v-.06a1.9 1.9 0 0 0-1.24-1.74 1.9 1.9 0 0 0-2.1.38l-.04.04a2.2 2.2 0 0 1-3.11-3.11l.04-.04a1.9 1.9 0 0 0 .38-2.1 1.9 1.9 0 0 0-1.74-1.15H2a2.2 2.2 0 0 1 0-4.4h.06A1.9 1.9 0 0 0 3.8 8.6a1.9 1.9 0 0 0-.38-2.1l-.04-.04a2.2 2.2 0 0 1 3.11-3.11l.04.04a1.9 1.9 0 0 0 2.1.38h.02A1.9 1.9 0 0 0 9.8 2.06V2a2.2 2.2 0 0 1 4.4 0v.06a1.9 1.9 0 0 0 1.15 1.74 1.9 1.9 0 0 0 2.1-.38l.04-.04a2.2 2.2 0 0 1 3.11 3.11l-.04.04a1.9 1.9 0 0 0-.38 2.1v.02A1.9 1.9 0 0 0 21.94 9.8H22a2.2 2.2 0 0 1 0 4.4h-.06A1.9 1.9 0 0 0 19.4 15Z" />
      </>
    ),
    sparkles: <path d="M12 3l1.6 5.2L19 10l-5.4 1.8L12 17l-1.6-5.2L5 10l5.4-1.8L12 3ZM19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15ZM5 3l.8 2.2L8 6l-2.2.8L5 9l-.8-2.2L2 6l2.2-.8L5 3Z" />,
    star: <path d="M12 3l2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3Z" />,
    workbench: <path d="M4 5h16v5H4zM4 14h7v5H4zM15 14h5v5h-5z" />
  };
  return (
    <svg aria-hidden="true" className="ui-icon" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" viewBox="0 0 24 24">
      {icons[name]}
    </svg>
  );
}

function LanguageToggle({ locale, setLocale }) {
  return (
    <div className="segmented" aria-label={t("language", locale)}>
      <button className={locale === "zh" ? "active" : ""} onClick={() => setLocale("zh")} type="button">中文</button>
      <button className={locale === "en" ? "active" : ""} onClick={() => setLocale("en")} type="button">EN</button>
    </div>
  );
}

function AiStatusBadge({ aiReady, locale }) {
  return (
    <div className={aiReady ? "ai-status online" : "ai-status offline"}>
      <i />
      <span>{aiReady ? t("aiFullPower", locale) : t("baseMode", locale)}</span>
    </div>
  );
}

function CollapsiblePanel({ children, className = "", defaultOpen = false, meta, title }) {
  return (
    <details className={`collapsible-panel ${className}`.trim()} open={defaultOpen}>
      <summary>
        <span>{title}</span>
        {meta ? <strong>{meta}</strong> : null}
      </summary>
      <div className="collapsible-body">{children}</div>
    </details>
  );
}

function SettingsMenu({ aiReady, importing, locale, onCheckUpdate, onImportLocalSettings, onRestartGuide, onSaveSettings, providerStatus, saving, serviceMessage, setLocale, setTheme, theme, updateInfo }) {
  const catalog = providerCatalog(providerStatus);
  const fileInputRef = useRef(null);
  const [form, setForm] = useState(() => formForProvider(savedValue("commodity-lab-ai-provider", "haineng")));
  const [fileImportError, setFileImportError] = useState("");
  const provider = catalog[form.provider] ? form.provider : "haineng";
  const configuredProvider = ["haineng", "deepseek"].includes(providerStatus?.haineng?.provider)
    ? providerStatus.haineng.provider
    : "";

  useEffect(() => {
    if (!configuredProvider) return;
    localStorage.setItem("commodity-lab-ai-provider", configuredProvider);
    setForm((current) => (
      current.provider === configuredProvider
        ? current
        : formForProvider(configuredProvider, providerCatalog(providerStatus), current.api_key)
    ));
  }, [configuredProvider, providerStatus?.ai_providers]);

  function changeProvider(nextProvider) {
    setForm(formForProvider(nextProvider, catalog, form.api_key));
  }
  async function importAiKeyFile(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    try {
      setFileImportError("");
      const text = await file.text();
      const importedForm = formFromAiKeyFile(text, catalog, { currentProvider: provider });
      await onImportLocalSettings(importedForm, file.name);
      setForm({ ...importedForm, api_key: "" });
    } catch (error) {
      setFileImportError(error?.message ?? String(error));
    }
  }

  return (
      <div className="settings-panel">
        <section>
          <h3>{t("settings", locale)}</h3>
          <div className="settings-row">
            <span>{t("language", locale)}</span>
            <LanguageToggle locale={locale} setLocale={setLocale} />
          </div>
          <label>
            {t("theme", locale)}
            <select value={theme} onChange={(event) => setTheme(event.target.value)}>
              <option value="system">{t("systemMode", locale)}</option>
              <option value="light">{t("lightMode", locale)}</option>
              <option value="dark">{t("darkMode", locale)}</option>
            </select>
          </label>
        </section>

        <section>
          <h3>{t("apiSettings", locale)}</h3>
          <form className="setup-form" onSubmit={(event) => { event.preventDefault(); onSaveSettings(form); setForm((current) => ({ ...current, api_key: "" })); }}>
            <label>
              {t("provider", locale)}
              <select aria-label={t("provider", locale)} value={provider} onChange={(event) => changeProvider(event.target.value)}>
                <option value="haineng">{t("hainengProvider", locale)}</option>
                <option value="deepseek">{t("deepseekProvider", locale)}</option>
              </select>
            </label>
            <label>
              {t("apiKey", locale)}
              <input aria-label={t("apiKey", locale)} autoComplete="off" type="password" value={form.api_key} placeholder={aiReady ? "********" : t("enterKeyToUnlock", locale)} onChange={(event) => setForm({ ...form, api_key: event.target.value })} />
            </label>
            <p className="settings-note settings-auto-provider">{t("autoProviderRoute", locale)}</p>
            <button className="primary" disabled={saving || importing} type="submit">{saving ? t("loading", locale) : t("saveSettings", locale)}</button>
            <button className="secondary" disabled={saving || importing} onClick={() => fileInputRef.current?.click()} type="button">{importing ? t("loading", locale) : t("loadLocalAiKey", locale)}</button>
            <input className="visually-hidden" onChange={importAiKeyFile} ref={fileInputRef} type="file" />
          </form>
          <p className="settings-note">{t("localAiKeyHint", locale)}</p>
          {fileImportError ? <p className="service-error">{fileImportError}</p> : null}
          {serviceMessage ? <p className="settings-note">{serviceMessage}</p> : null}
        </section>

        <section>
          <h3>{t("developerInfo", locale)}</h3>
          <dl className="settings-facts">
            <div><dt>{t("organization", locale)}</dt><dd>{t("gasCenter", locale)}</dd></div>
            <div><dt>{t("projectLead", locale)}</dt><dd>{t("yangMin", locale)}</dd></div>
          </dl>
        </section>

        <section>
          <h3>{t("versionInfo", locale)}</h3>
          <dl className="settings-facts">
            <div><dt>{t("currentVersion", locale)}</dt><dd>{updateInfo.current_version ?? currentVersion}</dd></div>
            <div><dt>{t("latestVersion", locale)}</dt><dd>{updateInfo.latest_version ?? "--"}</dd></div>
          </dl>
          <div className="settings-actions">
            <button className="secondary" onClick={onCheckUpdate} type="button">{t("checkForUpdates", locale)}</button>
            <button className="secondary" onClick={onRestartGuide} type="button">{t("restartGuide", locale)}</button>
          </div>
          {updateInfo.message ? <p className="settings-note">{updateInfo.message}</p> : null}
          {updateInfo.release_url ? <a className="release-link" href={updateInfo.release_url} target="_blank" rel="noreferrer">{t("releasePage", locale)}</a> : null}
        </section>
      </div>
  );
}

function SettingsToggle({ locale, onClick, open }) {
  return (
    <button className={open ? "settings-toggle active" : "settings-toggle"} data-guide="settings-menu" onClick={onClick} type="button">
      <Icon name="settings" />
      <span>{t("settings", locale)}</span>
    </button>
  );
}

function BusinessNavigator({ activeTemplateId, businessTemplates, footer, generateTrainingCase, locale, loadingTemplate, settingsOpen, settingsPanel }) {
  const groups = businessTemplates.groups?.length ? businessTemplates.groups : fallbackTemplates.groups;
  const templates = businessTemplates.templates?.length ? businessTemplates.templates : fallbackTemplates.templates;
  const knowledge = businessTemplates.knowledge_points?.length ? businessTemplates.knowledge_points : fallbackTemplates.knowledge_points;
  return (
    <aside className="left-rail" data-guide="business-sidebar">
      <div className={settingsOpen ? "left-rail-main settings-mode" : "left-rail-main"}>
        {settingsOpen ? settingsPanel : (
        <>
        <CollapsiblePanel defaultOpen title={t("businessTypes", locale)} meta={t("aiGeneratedData", locale)}>
          <div className="business-navigator">
            {groups.map((group) => (
              <details className="business-group" key={group.id} open>
                <summary>{group.label}</summary>
                <div className="scenario-list">
                  {templates.filter((template) => template.group === group.id).map((template) => (
                    <button className={template.id === activeTemplateId ? "scenario-row active" : "scenario-row"} key={template.id} onClick={() => generateTrainingCase(template.id)} type="button">
                      <em>{template.business_type}</em>
                      <strong>{template.title}</strong>
                      <span>{template.summary}</span>
                      <small>{loadingTemplate === template.id ? t("aiGenerating", locale) : t("generateWithAi", locale)}</small>
                    </button>
                  ))}
                </div>
              </details>
            ))}
          </div>
        </CollapsiblePanel>
        <CollapsiblePanel title={t("knowledgePoints", locale)} meta={formatNumber(knowledge.length)}>
          <div className="knowledge-list">
            {knowledge.map((point) => (
              <article key={point.id}>
                <strong>{point.label}</strong>
                <p>{point.description}</p>
              </article>
            ))}
          </div>
        </CollapsiblePanel>
        </>
        )}
      </div>
      <div className="left-rail-footer">{footer}</div>
    </aside>
  );
}

function GenerationTimeline({ locale, stages, streamState }) {
  return (
    <div className="ai-generation-timeline">
      <div>
        {(stages.length ? stages : [{ id: "ready", label: t("aiCaseReady", locale) }]).map((stage, index) => (
          <span className={index === stages.length - 1 && stages.length ? "active" : ""} key={`${stage.id}-${index}`}>
            <i />
            {stage.label}
          </span>
        ))}
      </div>
      {streamState?.received ? (
        <small>
          <b>{copy(locale, "实时生成", "LIVE")}</b>
          {copy(locale, `已接收 ${formatNumber(streamState.received)} 个结构化字符`, `${formatNumber(streamState.received)} structured characters received`)}
        </small>
      ) : null}
    </div>
  );
}

function chartFieldLabel(field, locale) {
  const labels = {
    close: { zh: "收盘", en: "Close" },
    high: { zh: "最高", en: "High" },
    low: { zh: "最低", en: "Low" }
  };
  const label = labels[field];
  return label ? copy(locale, label.zh, label.en) : field;
}

function marketStructureLabel(structure, locale) {
  const normalized = String(structure ?? "flat").toLowerCase();
  if (normalized === "contango") return "Contango";
  if (normalized === "backwardation") return "Backwardation";
  if (normalized === "volatile") return copy(locale, "高波动", "Volatile");
  return copy(locale, "平坦", "Flat");
}

function marketQualityLabel(provenance, locale) {
  const quality = String(provenance?.quality ?? provenance?.mode ?? "ai_simulated").toLowerCase();
  if (quality === "entitled_current" || quality === "live") return copy(locale, "授权实盘", "Entitled live");
  if (quality === "cached_current" || quality === "live_cached") return copy(locale, "当前缓存", "Current cache");
  if (quality === "stale" || quality === "live_stale_cache") return copy(locale, "过期缓存", "Stale cache");
  if (quality === "historical_replay" || quality.includes("historically")) return copy(locale, "历史校准", "Historical calibration");
  if (quality === "explicit_simulation_fallback") return copy(locale, "模拟回退", "Simulated fallback");
  return copy(locale, "AI 模拟", "AI simulation");
}

function trainingMarketModeLabel(caseData, locale) {
  const sessionMarket = caseData?.training_session?.market ?? {};
  const requestedMode = sessionMarket.requested_mode ?? caseData?.market?.provenance?.mode ?? "ai_simulated";
  if (requestedMode === "historical_replay") return copy(locale, "历史复盘", "Historical replay");
  if (requestedMode === "live") {
    return sessionMarket.fallback_applied
      ? copy(locale, "实盘请求 · 模拟回退", "Live requested · simulated fallback")
      : copy(locale, "授权实盘", "Entitled live");
  }
  return copy(locale, "AI 模拟市场", "AI-simulated market");
}

function trainingSessionStatusLabel(caseData, locale) {
  const sessionReplay = caseData?.training_session?.replay;
  const marketReplay = caseData?.market?.replay;
  const replay = sessionReplay?.event_id ? sessionReplay : marketReplay?.event?.id ? {
    event_id: marketReplay.event.id,
    checkpoint: marketReplay.current_checkpoint?.index,
    checkpoint_count: marketReplay.event?.checkpoint_count
  } : null;
  if (replay?.event_id) {
    const current = Number(replay.checkpoint ?? 0) + 1;
    const total = replay.checkpoint_count ?? "--";
    return copy(locale, `复盘节点 ${current}/${total}`, `Replay checkpoint ${current}/${total}`);
  }
  return copy(locale, "本地即时评分", "Immediate local scoring");
}

function providerStatusCopy(status, locale) {
  const normalized = String(status ?? "not_configured");
  if (normalized === "ready" || normalized === "connected") {
    return {
      label: copy(locale, "已就绪", "Ready"),
      detail: copy(locale, "订阅凭证和品种映射已就绪；生成时读取授权远期评估。", "Subscription credentials and symbol mappings are ready for entitled forward assessments."),
      connected: true
    };
  }
  if (normalized === "credentials_present_missing_symbol_map") {
    return { label: copy(locale, "缺少映射", "Mapping required"), detail: copy(locale, "订阅凭证已识别，但还需配置各品种远期代码映射。", "Credentials are present; commodity forward-symbol mappings are still required."), connected: false };
  }
  if (normalized === "symbol_map_present_missing_credentials") {
    return { label: copy(locale, "缺少凭证", "Credentials required"), detail: copy(locale, "品种映射已识别，但还未配置订阅凭证。", "Symbol mappings are present; subscription credentials are still required."), connected: false };
  }
  return { label: copy(locale, "未配置", "Not configured"), detail: copy(locale, "未配置订阅；生成时会明确回退到 AI 模拟市场。", "No subscription is configured; generation will clearly fall back to AI simulation."), connected: false };
}

function ForwardCurveStrip({ locale, market }) {
  const points = market.forward_curve ?? [];
  if (points.length < 2) return null;
  const visibleQuotes = points.slice(0, 6);
  const width = 680;
  const height = 118;
  const pad = { left: 42, right: 24, top: 16, bottom: 28 };
  const prices = points.map((point) => Number(point.price)).filter(Number.isFinite);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const range = Math.max(max - min, 0.01);
  const xFor = (index) => pad.left + (index / Math.max(points.length - 1, 1)) * (width - pad.left - pad.right);
  const yFor = (value) => pad.top + ((max - Number(value)) / range) * (height - pad.top - pad.bottom);
  const path = points.map((point, index) => `${index ? "L" : "M"} ${xFor(index).toFixed(1)} ${yFor(point.price).toFixed(1)}`).join(" ");
  return (
    <div className="forward-curve-strip">
      <div className="forward-curve-heading">
        <strong>{market.benchmark ?? "--"} {copy(locale, "远期", "FORWARD")}</strong>
        <small>{copy(locale, "曲线快照", "CURVE SNAPSHOT")} · {market.unit ?? "--"}</small>
      </div>
      <svg aria-label={copy(locale, "远期曲线", "Forward curve")} preserveAspectRatio="none" role="img" viewBox={`0 0 ${width} ${height}`}>
        {[0, 0.5, 1].map((ratio) => <line className="forward-grid" key={ratio} x1={pad.left} x2={width - pad.right} y1={pad.top + ratio * (height - pad.top - pad.bottom)} y2={pad.top + ratio * (height - pad.top - pad.bottom)} />)}
        <path className="forward-line" d={path} />
        {points.map((point, index) => (
          <g key={`${point.tenor}-${index}`}>
            <circle cx={xFor(index)} cy={yFor(point.price)} r="3.5" />
            <text className="forward-price" x={xFor(index)} y={Math.max(11, yFor(point.price) - 8)}>{formatNumber(point.price, 2)}</text>
            <text className="forward-tenor" x={xFor(index)} y={height - 7}>{point.tenor}</text>
          </g>
        ))}
      </svg>
      <div aria-label={copy(locale, "远期报价", "Forward quotes")} className="forward-quote-grid" role="table">
        {visibleQuotes.map((point) => (
          <div key={point.tenor} role="row">
            <strong role="cell">{point.tenor}</strong>
            <span role="cell"><small>BID</small><b>{formatNumber(point.bid, 2)}</b></span>
            <span role="cell"><small>ASK</small><b>{formatNumber(point.ask, 2)}</b></span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MarketChart({ caseData, fieldSelection, locale, setFieldSelection, strategyLegs }) {
  const market = caseData.market ?? {};
  const curves = market.curves ?? [];
  const [hoverIndex, setHoverIndex] = useState(null);
  const width = 860;
  const laneHeight = 112;
  const height = Math.max(300, 62 + Math.max(1, curves.length) * laneHeight);
  const pad = { left: 74, right: 116, top: 22, bottom: 34 };
  const plotW = width - pad.left - pad.right;
  const pointCount = Math.max(...curves.map((curve) => curve.points?.length ?? 0), 1);
  const xFor = (index) => pad.left + (pointCount <= 1 ? 0 : (index / (pointCount - 1)) * plotW);
  const hovered = hoverIndex == null ? null : curves.map((curve) => ({ curve, point: curve.points?.[hoverIndex] })).filter((row) => row.point);

  function curveStats(curve) {
    const values = (curve.points ?? []).flatMap((point) => fieldSelection.map((field) => Number(point[field])).filter(Number.isFinite));
    const min = values.length ? Math.min(...values) : 0;
    const max = values.length ? Math.max(...values) : 1;
    const padding = Math.max((max - min) * 0.08, 0.01);
    return { min: min - padding, max: max + padding, range: Math.max(max - min + padding * 2, 0.01) };
  }
  function laneTop(index) {
    return pad.top + index * laneHeight;
  }
  function yFor(curve, laneIndex, value) {
    const stats = curveStats(curve);
    const innerTop = laneTop(laneIndex) + 26;
    const innerH = laneHeight - 44;
    return innerTop + ((stats.max - Number(value)) / stats.range) * innerH;
  }
  function pathFor(curve, field, laneIndex) {
    return (curve.points ?? []).map((point, index) => {
      const value = Number(point[field]);
      if (!Number.isFinite(value)) return "";
      return `${index === 0 ? "M" : "L"} ${xFor(index).toFixed(1)} ${yFor(curve, laneIndex, value).toFixed(1)}`;
    }).filter(Boolean).join(" ");
  }
  function pointChange(curve) {
    const points = curve.points ?? [];
    const last = points.at(-1) ?? {};
    const prev = points.at(-2) ?? points[0] ?? {};
    const change = Number(last.close) - Number(prev.close);
    const pct = Number(prev.close) ? (change / Number(prev.close)) * 100 : 0;
    return { change, pct };
  }
  function toggleField(field) {
    setFieldSelection((current) => {
      if (current.includes(field) && current.length > 1) return current.filter((item) => item !== field);
      if (!current.includes(field)) return [...current, field];
      return current;
    });
  }
  function onMove(event) {
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
    setHoverIndex(Math.round(ratio * (pointCount - 1)));
  }

  return (
    <section className="panel market-panel" data-guide="market-chart">
      <div className="panel-title">
        <span>{t("marketContext", locale)}</span>
        <strong className={`market-quality quality-${market.provenance?.quality ?? market.provenance?.mode ?? "simulated"}`}>{marketQualityLabel(market.provenance, locale)}</strong>
      </div>
      <div className="market-evidence-strip">
        <span>{copy(locale, "数据证据", "Evidence quality")}<strong>{market.provenance?.label ?? t("aiGeneratedData", locale)}</strong></span>
        <span>{copy(locale, "远期结构", "Forward curve structure")}<strong>{marketStructureLabel(market.curve_metrics?.structure, locale)}</strong></span>
        <span>{copy(locale, "数据时点", "As of")}<strong>{copy(locale, `截至 ${market.as_of ?? market.provenance?.as_of ?? "--"}`, `As of ${market.as_of ?? market.provenance?.as_of ?? "--"}`)}</strong></span>
        <span>{copy(locale, "基准", "Benchmark")}<strong>{market.benchmark ?? curves[0]?.label ?? "--"}</strong></span>
      </div>
      {market.provenance?.evidence_components?.length ? (
        <div className="market-evidence-components" aria-label={copy(locale, "证据组成", "Evidence components")}>
          {market.provenance.evidence_components.map((component) => (
            <span className={`evidence-${component.mode}`} key={component.id}>
              <Icon name={component.id === "forward_curve" ? "pulse" : "history"} />
              <b>{component.id === "forward_curve" ? copy(locale, "远期曲线", "Forward curve") : copy(locale, "历史路径", "History path")}</b>
              <small>{component.label}</small>
            </span>
          ))}
        </div>
      ) : null}
      <ForwardCurveStrip locale={locale} market={market} />
      <div className="chart-toolbar">
        <div className="segmented compact">
          {chartFields.map((field) => (
            <button className={fieldSelection.includes(field) ? "active" : ""} key={field} onClick={() => toggleField(field)} type="button">{chartFieldLabel(field, locale)}</button>
          ))}
        </div>
        <span>{market.unit ?? "--"}</span>
      </div>
      <div className="price-chart-wrap" onMouseLeave={() => setHoverIndex(null)} onMouseMove={onMove}>
        <svg className="price-chart terminal-chart" role="img" aria-label={t("priceChart", locale)} preserveAspectRatio="none" viewBox={`0 0 ${width} ${height}`}>
          {curves.map((curve, laneIndex) => {
            const stats = curveStats(curve);
            const top = laneTop(laneIndex);
            const innerTop = top + 26;
            const innerH = laneHeight - 44;
            const last = curve.points?.at(-1) ?? {};
            return (
              <g className="chart-lane" key={curve.id}>
                <rect x={pad.left} y={top + 8} width={plotW} height={laneHeight - 14} rx="7" />
                {[0, 0.5, 1].map((ratio) => <line className="grid-line" key={ratio} x1={pad.left} x2={pad.left + plotW} y1={innerTop + innerH * ratio} y2={innerTop + innerH * ratio} />)}
                <text className="lane-title" x="12" y={top + 24}>{curve.label}</text>
                <text className="axis-label" x="12" y={innerTop + 5}>{formatNumber(stats.max, 2)}</text>
                <text className="axis-label" x="12" y={innerTop + innerH}>{formatNumber(stats.min, 2)}</text>
                <text className="lane-last" x={pad.left + plotW + 12} y={top + 32}>C {formatNumber(last.close, 2)}</text>
                <text className="lane-last muted" x={pad.left + plotW + 12} y={top + 52}>H {formatNumber(last.high, 2)}</text>
                <text className="lane-last muted" x={pad.left + plotW + 12} y={top + 70}>L {formatNumber(last.low, 2)}</text>
                {fieldSelection.map((field) => {
                  const path = pathFor(curve, field, laneIndex);
                  if (!path) return null;
                  const color = field === "close" ? curve.color : field === "high" ? "#7dd3a7" : "#f87171";
                  return <path className={`price-line field-${field}`} d={path} key={`${curve.id}-${field}`} style={{ stroke: color }} />;
                })}
              </g>
            );
          })}
          {market.events?.map((event) => {
            const index = Math.max(0, (curves[0]?.points ?? []).findIndex((point) => point.date === event.date));
            const x = xFor(index < 0 ? 0 : index);
            return <g className="event-marker" key={`${event.date}-${event.label}`}><line x1={x} x2={x} y1={pad.top} y2={height - pad.bottom} /><text x={x + 5} y={pad.top + 15}>{event.label}</text></g>;
          })}
          {hoverIndex != null ? <line className="hover-line" x1={xFor(hoverIndex)} x2={xFor(hoverIndex)} y1={pad.top} y2={height - pad.bottom} /> : null}
          {strategyLegs.map((leg, index) => {
            const x = pad.left + plotW * Math.min(0.92, 0.12 + index * 0.1);
            const laneIndex = index % Math.max(1, curves.length);
            const laneRound = Math.floor(index / Math.max(1, curves.length));
            const y = pad.top + 18 + laneIndex * laneHeight;
            const labelY = Math.min(y + 4 + laneRound * 15, pad.top + (laneIndex + 1) * laneHeight - 16);
            return <g className="trade-marker" key={leg.id ?? index}><circle cx={x} cy={y} r="5" /><text x={x + 8} y={labelY}>{leg.leg_type}:{leg.side}</text></g>;
          })}
          {curves[0]?.points?.[0]?.date ? <text className="date-label" x={pad.left} y={height - 12}>{compactDate(curves[0].points[0].date)}</text> : null}
          {curves[0]?.points?.at(-1)?.date ? <text className="date-label end" x={pad.left + plotW} y={height - 12}>{compactDate(curves[0].points.at(-1).date)}</text> : null}
        </svg>
        {hovered?.length ? (
          <div className="chart-tooltip">
            <strong>{hovered[0].point.date}</strong>
            {hovered.map(({ curve, point }) => (
              <span key={curve.id}>{curve.label}: C {formatNumber(point.close, 2)} / H {formatNumber(point.high, 2)} / L {formatNumber(point.low, 2)}</span>
            ))}
          </div>
        ) : null}
      </div>
      <div className="curve-table">
        {curves.map((curve) => {
          const point = curve.points?.at(-1) ?? {};
          const { change, pct } = pointChange(curve);
          return (
            <span key={curve.id}>
              <i style={{ background: curve.color }} />
              <strong>{curve.label}</strong>
              <small>{point.date ?? "--"} O {formatNumber(point.open, 2)} H {formatNumber(point.high, 2)} L {formatNumber(point.low, 2)} C {formatNumber(point.close, 2)} Δ {formatNumber(change, 2)} / {formatNumber(pct, 2)}%</small>
            </span>
          );
        })}
      </div>
    </section>
  );
}

function CaseWorkspace({ caseData, generationStages, locale }) {
  return (
    <section className="case-workspace" data-guide="case-workspace">
      <div className="scenario-header">
        <span>{caseData.scenario.business_type}</span>
        <h2>{caseData.scenario.title}</h2>
        <p>{caseData.scenario.summary}</p>
        <GenerationTimeline locale={locale} stages={generationStages} />
      </div>
      <section className="panel prompt-panel">
        <MarkdownText text={caseData.prompt} />
      </section>
    </section>
  );
}

function StrategyBuilder({ busy, locale, locked = false, onSubmit, rationale, setRationale, setStrategyLegs, strategyLegs }) {
  function updateLeg(index, patch) {
    setStrategyLegs((current) => current.map((leg, itemIndex) => itemIndex === index ? { ...leg, ...patch } : leg));
  }
  function addLeg() {
    setStrategyLegs((current) => [...current, { id: `leg-${Date.now()}`, leg_type: "", market: "", side: "", quantity: 0, price: 0, tenor: "", hedge_type: "" }]);
  }
  function removeLeg(index) {
    setStrategyLegs((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }
  return (
    <section className="panel order-ticket" data-guide="strategy-builder">
      <div className="panel-title"><span>{t("strategyBuilder", locale)}</span><strong>{t("decisionLab", locale)}</strong></div>
      <div className="strategy-leg-list">
        {strategyLegs.map((leg, index) => (
          <div className="strategy-leg" key={leg.id ?? index}>
            <label>{t("legType", locale)}<select disabled={locked} value={leg.leg_type} onChange={(event) => updateLeg(index, { leg_type: event.target.value })}><option value="">{copy(locale, "选择工具", "Select tool")}</option><option value="physical">{t("physicalLeg", locale)}</option><option value="swap">Swap</option><option value="future">Future</option><option value="basis">{t("basisLeg", locale)}</option><option value="fx">FX</option><option value="capacity">{t("capacityLeg", locale)}</option><option value="option">{copy(locale, "期权", "Option")}</option></select></label>
            <label>{t("market", locale)}<input disabled={locked} value={leg.market} onChange={(event) => updateLeg(index, { market: event.target.value })} /></label>
            <label>{t("side", locale)}<select disabled={locked} value={leg.side} onChange={(event) => updateLeg(index, { side: event.target.value })}><option value="">{copy(locale, "选择方向", "Select side")}</option><option value="sell">{t("sell", locale)}</option><option value="buy">{t("buy", locale)}</option><option value="pay">Pay</option><option value="receive">Receive</option></select></label>
            <label>{t("quantity", locale)}<input disabled={locked} min="0" type="number" value={leg.quantity} onChange={(event) => updateLeg(index, { quantity: Number(event.target.value) })} /></label>
            <label>{t("tenor", locale)}<input disabled={locked} value={leg.tenor} onChange={(event) => updateLeg(index, { tenor: event.target.value })} /></label>
            <button className="icon-button danger" disabled={locked || strategyLegs.length <= 1} onClick={() => removeLeg(index)} type="button">×</button>
          </div>
        ))}
      </div>
      <button className="secondary" disabled={locked} onClick={addLeg} type="button">{t("addLeg", locale)}</button>
      <label>{t("rationale", locale)}<textarea disabled={locked} value={rationale} onChange={(event) => setRationale(event.target.value)} placeholder={copy(locale, "说明实货、纸货、数量期限、剩余风险和执行检查。", "Explain the physical and paper legs, sizing, tenor, residual risks, and execution checks.")} /></label>
      <button className="primary" disabled={busy || locked} onClick={onSubmit} type="button">{locked ? copy(locale, "本节点已提交", "Checkpoint submitted") : busy ? t("loading", locale) : t("submitOrder", locale)}</button>
    </section>
  );
}

function ScorePanel({ evaluation, locale }) {
  const metrics = evaluation?.metrics ?? {};
  return (
    <section className="panel score-panel">
      <div className="panel-title"><span>{t("reviewScore", locale)}</span><strong>{t("localScoring", locale)}</strong></div>
      <div className="score-row">
        <div className="score-readout">{evaluation?.baseline_score ?? "--"}</div>
        <div className="metric-strip">
          <span>{t("strategyLegs", locale)}<strong>{formatNumber(metrics.strategy_leg_count)}</strong></span>
          <span>{t("paperLegs", locale)}<strong>{formatNumber(metrics.paper_leg_count)}</strong></span>
          <span>{t("notional", locale)}<strong>{metrics.notional_usd ? formatMoney(metrics.notional_usd) : "--"}</strong></span>
        </div>
      </div>
      {evaluation?.mistake_tags?.length ? <p className="service-error">{evaluation.mistake_tags.map((tag) => mistakeLabel(tag, locale)).join(" · ")}</p> : null}
    </section>
  );
}

function RiskCoverageMap({ caseData, locale, strategyLegs }) {
  const { rows, missingTargets } = buildRiskCoverageRows(caseData, strategyLegs, locale);
  return (
    <section className="panel risk-coverage-panel" data-guide="risk-coverage">
      <div className="panel-title">
        <span>{copy(locale, "风险覆盖图", "Risk Coverage Map")}</span>
        <strong>{copy(locale, "实货 + 纸货匹配", "Physical + paper match")}</strong>
      </div>
      <div className="risk-coverage-grid">
        {rows.map((row) => (
          <article className={row.covered ? "covered" : ""} key={row.id}>
            <div>
              <strong>{row.label}</strong>
              <small>{row.targetCount ? copy(locale, `目标 ${row.targetCount} 条`, `${row.targetCount} target action${row.targetCount > 1 ? "s" : ""}`) : copy(locale, "本题可选", "optional for this case")}</small>
            </div>
            {row.legs.length ? (
              row.legs.slice(0, 2).map((leg) => <span key={leg.id ?? `${leg.leg_type}-${leg.market}`}>{describeLegForCoverage(leg, locale)}</span>)
            ) : (
              <span>{copy(locale, "尚未覆盖", "Not covered yet")}</span>
            )}
          </article>
        ))}
      </div>
      <div className="risk-gap-strip">
        <strong>{copy(locale, "缺失目标动作", "Missing target actions")}</strong>
        {missingTargets.length ? (
          <span>{missingTargets.map((leg) => `${leg.leg_type} / ${leg.market}`).join(" · ")}</span>
        ) : (
          <span>{copy(locale, "当前策略已包含本题目标动作，请检查数量、方向和期限。", "Current strategy includes the target actions; verify quantity, side, and tenor.")}</span>
        )}
      </div>
    </section>
  );
}

function AiControlLog({ interventions, locale }) {
  const recent = (interventions ?? []).slice(0, 4);
  return (
    <section className="panel ai-control-log" aria-live="polite">
      <div className="panel-title">
        <span>{copy(locale, "AI 控制日志", "AI Control Log")}</span>
        <strong>{recent.length ? copy(locale, "AI 动作已应用", "AI action applied") : copy(locale, "等待指令", "Waiting for command")}</strong>
      </div>
      {recent.length ? (
        <ol>
          {recent.map((item) => (
            <li key={item.id}>
              <Icon name="sparkles" />
              <span>{item.label}</span>
              <small>{copy(locale, "已同步到界面", "Synced to workspace")}</small>
            </li>
          ))}
        </ol>
      ) : (
        <p>{copy(locale, "通过右下角 AI 助手要求生成题目、改曲线或填策略，动作会在这里留下记录。", "Ask the floating AI assistant to generate a drill, change curves, or fill strategy legs; applied actions appear here.")}</p>
      )}
    </section>
  );
}

function RubricPanel({ caseData, locale }) {
  return (
    <section className="panel rubric-panel">
      <div className="panel-title"><span>{t("rubric", locale)}</span><strong>{t("generatedWithCase", locale)}</strong></div>
      <div className="rubric-list">
        {(caseData.rubric ?? []).map((item) => <article key={item.id}><strong>{item.points} - {item.label}</strong><p>{item.rule}</p></article>)}
      </div>
    </section>
  );
}

function AiThinkingPanel({ activeStage = "", locale, titleKey = "aiThinkingTitle" }) {
  const stages = ["thinkingReadContext", "thinkingMatchKnowledge", "thinkingGenerateActions", "thinkingAssemble"];
  const stageIndexes = {
    read_workspace: 0,
    plan_workspace_actions: 1,
    stream_answer: 2,
    apply_workspace_actions: 3
  };
  const activeIndex = activeStage ? (stageIndexes[activeStage] ?? 0) : stages.length - 1;
  return (
    <section className="thinking-panel active" aria-live="polite">
      <div className="panel-title compact-title"><span>{t(titleKey, locale)}</span><strong>{t("working", locale)}</strong></div>
      <ol className="thinking-steps">
        {stages.map((key, index) => <li className={index < activeIndex ? "complete" : index === activeIndex ? "active" : ""} key={key}><i /><span>{t(key, locale)}</span></li>)}
      </ol>
    </section>
  );
}

function AdvisorRail({ aiOutput, aiReady, advisorFeedback, busyAction, error, evaluation, exam, locale, runAiAction }) {
  const hasAdvisorOutput = Boolean(error || advisorFeedback || exam || aiOutput?.answer);
  const structuredExam = normalizeExamPayload(exam);
  return (
    <aside className={aiReady ? "advisor-rail online" : "advisor-rail"}>
      <div className="advisor-head">
        <div>
          <span>{t("aiCoach", locale)}</span>
          <small>{aiReady ? t("online", locale) : t("offline", locale)}</small>
        </div>
        <strong>{aiReady ? t("enabled", locale) : t("connectToEnable", locale)}</strong>
      </div>
      <div className="advisor-scroll">
        {busyAction && !["evaluate", "provider"].includes(busyAction) ? <AiThinkingPanel locale={locale} /> : null}
        <details className="advisor-section" open>
          <summary><span>{t("aiTrainingActions", locale)}</span><strong>{aiReady ? t("enabled", locale) : t("connectToEnable", locale)}</strong></summary>
          <div className="ai-action-grid">
            {[
              ["advisor_review", "askHint", Boolean(evaluation)],
              ["exam", "generateExam", true],
              ["concept_tutor", "conceptTutor", true],
              ["trade_playbook", "tradePlaybook", true]
            ].map(([capability, labelKey, available]) => (
              <button disabled={Boolean(busyAction) || !aiReady || !available} key={capability} onClick={() => runAiAction(capability)} type="button">{busyAction === capability ? t("loading", locale) : t(labelKey, locale)}</button>
            ))}
          </div>
        </details>
        <details className="advisor-section" open>
          <summary><span>{t("aiTrainingOutput", locale)}</span><strong>{t("markdownEnabled", locale)}</strong></summary>
          <div className="advisor-output">
            {!aiReady ? <p className="service-error muted">{t("aiDisabledHint", locale)}</p> : null}
            {aiReady && !hasAdvisorOutput ? <p className="empty-state">{copy(locale, "选择一个 AI 动作，输出会显示在这里。", "Run an AI action or ask the assistant. Output appears here.")}</p> : null}
            {error ? <p className="service-error">{error}</p> : null}
            {advisorFeedback ? <section className="response-block"><h3>{t("advisorFeedback", locale)}</h3><MarkdownText text={advisorFeedback} /></section> : null}
            {structuredExam ? <section className="response-block"><h3>{t("examQuestions", locale)}</h3><p>{structuredExam.title} · {copy(locale, `${structuredExam.questions.length} 题`, `${structuredExam.questions.length} questions`)}</p></section> : null}
            {aiOutput?.answer ? <section className="response-block"><h3>{aiOutput.title}</h3><MarkdownText text={aiOutput.answer} /></section> : null}
          </div>
        </details>
      </div>
    </aside>
  );
}

function normalizeExamPayload(exam) {
  const parsed = typeof exam === "string" ? parseSafeJson(exam) : exam;
  if (!parsed || !Array.isArray(parsed.questions)) return null;
  const questions = parsed.questions
    .filter((question) => question && Array.isArray(question.options) && question.options.length >= 2)
    .map((question, index) => ({ id: question.id ?? `q${index + 1}`, ...question }));
  if (!questions.length) return null;
  return { id: parsed.id ?? `exam-${questions.length}`, title: parsed.title ?? "Course Checkpoint", questions };
}

function labelFor(locale, item, zhKey = "zh", enKey = "en") {
  return copy(locale, item[zhKey], item[enKey]);
}

function pageLabelFor(locale, activePage) {
  const navPage = navItems.find((item) => item.id === activePage);
  if (navPage) return labelFor(locale, navPage);
  const utilityPages = {
    [pageIds.review]: { zh: "\u590d\u76d8\u53cd\u9988", en: "Review" },
    [pageIds.coach]: { zh: "AI \u6559\u7ec3", en: "AI Coach" },
    [pageIds.settings]: { zh: "\u8bbe\u7f6e", en: "Settings" }
  };
  const page = utilityPages[activePage];
  return page ? labelFor(locale, page) : t("decisionLab", locale);
}

function curriculumReference(locale, productScope = "natural_gas") {
  const commodityModels = modelsForProduct(productScope).map((item) => ({
    id: item.id,
    group: item.group,
    title: labelFor(locale, item, "titleZh", "titleEn"),
    summary: copy(locale, item.summaryZh, item.summaryEn),
    risks: copy(locale, item.risksZh, item.risksEn),
    instruments: copy(locale, item.instrumentsZh, item.instrumentsEn)
  }));
  return {
    knowledge_coverage: coverageForProduct(productScope).map((item) => ({
      id: item.id,
      title: labelFor(locale, item, "titleZh", "titleEn"),
      summary: copy(locale, item.summaryZh, item.summaryEn),
      concepts: copy(locale, item.conceptsZh, item.conceptsEn)
    })),
    commodity_trading_models: commodityModels,
    gas_trading_models: commodityModels
  };
}

function trainingCurriculumReference(template, locale, productScope = "natural_gas") {
  const coverage = coverageForTemplate(template).map((item) => ({
    id: item.id,
    title: labelFor(locale, item, "titleZh", "titleEn"),
    summary: copy(locale, item.summaryZh, item.summaryEn),
    concepts: copy(locale, item.conceptsZh, item.conceptsEn)
  }));
  const allowedModelIds = new Set(modelsForProduct(productScope).map((item) => item.id));
  const models = modelsForTemplate(template).filter((item) => allowedModelIds.has(item.id)).map((item) => ({
    id: item.id,
    group: item.group,
    title: labelFor(locale, item, "titleZh", "titleEn"),
    risks: copy(locale, item.risksZh, item.risksEn),
    instruments: copy(locale, item.instrumentsZh, item.instrumentsEn)
  }));
  return { knowledge_coverage: coverage, commodity_trading_models: models, gas_trading_models: models };
}

function knowledgePointLabel(locale, pointId, businessTemplates) {
  const templatePoint = businessTemplates?.knowledge_points?.find((point) => point.id === pointId);
  if (templatePoint?.label) return templatePoint.label;
  const coverage = hedgingKnowledgeCoverage.find((point) => point.id === pointId);
  if (coverage) return labelFor(locale, coverage, "titleZh", "titleEn");
  return pointId;
}

function coverageForTemplate(template) {
  const ids = [...new Set([...(template?.coverage ?? []), ...(template?.knowledge_points ?? [])])];
  const coverage = hedgingKnowledgeCoverage.filter((item) => ids.includes(item.id));
  return coverage.length ? coverage : hedgingKnowledgeCoverage.slice(0, 3);
}

function modelsForTemplate(template) {
  const ids = template?.gas_models ?? [];
  const direct = gasTradingModels.filter((item) => ids.includes(item.id));
  const byGroup = gasTradingModels.filter((item) => item.group === template?.group).slice(0, 3);
  return direct.length ? direct : byGroup;
}

function CommodityLogo({ compact = false }) {
  return (
    <span className={compact ? "cl-logo-mark compact" : "cl-logo-mark"} aria-hidden="true">
      <svg viewBox="0 0 64 64" role="img">
        <defs>
          <linearGradient id="commodity-logo-bg" x1="12" x2="52" y1="8" y2="58" gradientUnits="userSpaceOnUse">
            <stop stopColor="#2f8cff" />
            <stop offset="0.58" stopColor="#0b6ff1" />
            <stop offset="1" stopColor="#0aa37f" />
          </linearGradient>
          <linearGradient id="commodity-logo-core" x1="22" x2="43" y1="14" y2="48" gradientUnits="userSpaceOnUse">
            <stop stopColor="#e8f4ff" />
            <stop offset="1" stopColor="#9ee6ff" />
          </linearGradient>
        </defs>
        <rect x="5" y="5" width="54" height="54" rx="14" fill="url(#commodity-logo-bg)" />
        <path d="M32 14c6.6 7.2 11.6 13 11.6 22.1C43.6 44 38.6 50 32 50s-11.6-6-11.6-13.9C20.4 27 25.4 21.2 32 14Z" fill="url(#commodity-logo-core)" opacity="0.94" />
        <path d="M33 23c2.8 3.3 5.1 6.7 5.1 11.2 0 4.9-2.8 8.2-6.8 8.2-3.5 0-6.4-2.6-6.4-6.6 0-2.8 1.7-5.3 4.2-7.5.1 3.3 1.5 5 3.9 5.7.9-3.4.7-6.7 0-11Z" fill="#0b6ff1" opacity="0.9" />
        <path d="M18 51h28" stroke="#ddf7ff" strokeWidth="3" strokeLinecap="round" opacity="0.84" />
      </svg>
    </span>
  );
}

function LogoMark() {
  return <CommodityLogo />;
}

function ProductTopbar({ activePage, aiReady, locale, onProductScopeChange, productScope }) {
  const currentPageLabel = pageLabelFor(locale, activePage);
  const workspace = productWorkspace(productScope);
  return (
    <header className="cl-topbar">
      <div className="cl-brand">
        <LogoMark />
        <div>
          <strong>Commodity Lab</strong>
        </div>
      </div>
      <div className="cl-top-actions">
        <label className="cl-product-switcher">
          <Icon name={workspace.icon} />
          <span>{copy(locale, "通识 +", "General +")}</span>
          <select aria-label={copy(locale, "课程产品", "Course product")} onChange={(event) => onProductScopeChange(event.target.value)} value={productScope}>
            {productWorkspaces.map((item) => (
              <option key={item.id} value={item.id}>
                {labelFor(locale, item)}{item.coursesReady ? "" : copy(locale, "（课程建设中）", " (course scaffold)")}
              </option>
            ))}
          </select>
        </label>
        <span className="cl-route-pill">{currentPageLabel}</span>
        <AiStatusBadge aiReady={aiReady} locale={locale} />
      </div>
    </header>
  );
}

function ProductSidebar({ activePage, collapsed, locale, onPageChange, onToggleCollapsed }) {
  return (
    <aside className={collapsed ? "cl-sidebar collapsed" : "cl-sidebar"}>
      <nav className="cl-main-nav">
        {navItems.map((item) => (
          <button aria-label={labelFor(locale, item)} className={activePage === item.id ? "active" : ""} key={item.id} onClick={() => onPageChange(item.id)} title={labelFor(locale, item)} type="button">
            <Icon name={item.icon} />
            <span>{labelFor(locale, item)}</span>
            {item.badge ? <small>{item.badge}</small> : null}
          </button>
        ))}
      </nav>
      <div className="cl-sidebar-footer">
        <button aria-label={t("settings", locale)} className={activePage === pageIds.settings ? "cl-settings-entry active" : "cl-settings-entry"} data-guide="settings-menu" onClick={() => onPageChange(pageIds.settings)} title={t("settings", locale)} type="button">
          <Icon name="settings" />
          <span>{t("settings", locale)}</span>
        </button>
        <button aria-label={collapsed ? copy(locale, "展开侧边栏", "Expand sidebar") : copy(locale, "收起侧边栏", "Collapse sidebar")} className="cl-sidebar-collapse" onClick={onToggleCollapsed} title={collapsed ? copy(locale, "展开侧边栏", "Expand sidebar") : copy(locale, "收起侧边栏", "Collapse sidebar")} type="button">
          <Icon name="arrow" />
        </button>
      </div>
    </aside>
  );
}

function aiActionKindLabel(locale, kind) {
  const labels = {
    generate_case: ["生成案例", "Generated case"],
    select_template: ["选择模板", "Selected template"],
    patch_case: ["改写题目", "Updated case"],
    set_market_curves: ["重绘曲线", "Redrew curves"],
    set_chart_fields: ["调整图表", "Adjusted chart"],
    set_strategy_legs: ["填入策略腿", "Filled strategy legs"],
    fill_rationale: ["起草说明", "Drafted rationale"],
    set_exam: ["生成测验", "Generated quiz"],
    submit_strategy: ["提交评分", "Scored strategy"],
    set_learning_plan: ["更新路径", "Updated path"],
    set_learning_goal: ["调整目标", "Updated goal"],
    navigate_page: ["切换页面", "Navigated"],
    run_ai_capability: ["运行能力", "Ran capability"]
  };
  const [zh, en] = labels[kind] ?? ["更新内容", "Updated content"];
  return copy(locale, zh, en);
}

function AiInterventionStrip({ interventions, locale, onNavigate }) {
  if (!interventions.length) return null;
  return (
    <div className="cl-ai-intervention-strip" role="status">
      <div className="cl-ai-intervention-summary">
        <span><Icon name="sparkles" />{copy(locale, "AI 已介入当前学习", "AI is shaping this lesson")}</span>
        <strong>{copy(locale, "已根据你的要求更新本课", "This lesson now reflects your request")}</strong>
      </div>
      <div className="cl-ai-action-pipeline" aria-label={copy(locale, "最近更新", "Recent updates")}>
        {interventions.slice(0, 3).map((item) => (
          <button key={item.id} onClick={() => item.page ? onNavigate(item.page) : null} type="button">
            <small>{aiActionKindLabel(locale, item.kind)}</small>
            <span>{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function PageTitle({ action, icon = "sparkles", locale, subtitleEn, subtitleZh, titleEn, titleZh }) {
  return (
    <div className="cl-page-title">
      <div>
        <span className="cl-title-icon"><Icon name={icon} /></span>
        <h2>{copy(locale, titleZh, titleEn)}</h2>
        <p>{copy(locale, subtitleZh, subtitleEn)}</p>
      </div>
      {action}
    </div>
  );
}

function lessonPracticePrompt(locale, track, lesson) {
  return copy(
    locale,
    `${copy(locale, track.requestZh, track.requestEn)}\n\n本节课重点：${copy(locale, lesson.titleZh, lesson.titleEn)}。学习产出：${copy(locale, lesson.outcomeZh, lesson.outcomeEn)}。请生成一个只围绕本节课目标的训练案例。`,
    `${copy(locale, track.requestZh, track.requestEn)}\n\nLesson focus: ${copy(locale, lesson.titleZh, lesson.titleEn)}. Learning outcome: ${copy(locale, lesson.outcomeZh, lesson.outcomeEn)}. Generate a training case focused only on this lesson objective.`
  );
}

function ProductScaffoldPage({ locale, workspace }) {
  return (
    <section className="cl-page cl-product-scaffold-page">
      <PageTitle
        icon={workspace.icon}
        locale={locale}
        titleZh={`${workspace.zh}工作区`}
        titleEn={`${workspace.en} Workspace`}
        subtitleZh="该品种的专项课程正在准备中。通识课程仍可正常学习。"
        subtitleEn="Product-specific lessons are in preparation. General hedging courses remain available."
      />
      <section className="cl-panel cl-product-scaffold">
        <div className="cl-scaffold-status">
          <span>{copy(locale, "课程状态", "Course status")}</span>
          <strong>{copy(locale, "筹备中", "In preparation")}</strong>
        </div>
        <div className="cl-scaffold-grid">
          <article>
            <Icon name="library" />
            <div>
              <strong>{copy(locale, "可先学习", "Available now")}</strong>
              <p>{copy(locale, "敞口识别、远期结构、期货与掉期、基差、期权、套保比率和风险控制。", "Exposure, forward structure, futures and swaps, basis, options, hedge ratios, and risk controls.")}</p>
            </div>
          </article>
          <article>
            <Icon name={workspace.icon} />
            <div>
              <strong>{copy(locale, "课程范围", "Planned coverage")}</strong>
              <p>{copy(locale, workspace.scopeZh, workspace.scopeEn)}</p>
            </div>
          </article>
        </div>
        <p className="cl-scaffold-note">{copy(locale, "欧洲天然气与原油专项课程现已开放。", "European natural gas and crude oil courses are available now.")}</p>
      </section>
    </section>
  );
}

function HomePage({ aiLessonPlan, aiReady, learningProgress, loadingTemplate, locale, onGenerate, onPageChange, productScope }) {
  const workspace = productWorkspace(productScope);
  const visibleTracks = tracksForProduct(productScope);
  const recommendedTrack = recommendedTrackId(learningProgress, productScope);
  const activePlan = !aiLessonPlan?.product_scope || aiLessonPlan.product_scope === productScope ? aiLessonPlan : null;
  const currentTrack = selectedTrackForProduct(activePlan?.track_id ?? recommendedTrack, learningProgress, productScope);
  const currentSyllabus = syllabusForTrack(currentTrack.id);
  const nextLesson = currentSyllabus.lessons[0];
  const nextPrompt = activePlan?.practice_prompt ?? lessonPracticePrompt(locale, currentTrack, nextLesson);
  const completedTracks = visibleTracks.filter((track) => attemptsForTrack(learningProgress, track).attempts > 0).length;
  const courseProgress = visibleTracks.length ? Math.round((completedTracks / visibleTracks.length) * 100) : 0;
  function startLesson(track, lesson = null) {
    const prompt = lesson
      ? lessonPracticePrompt(locale, track, lesson)
      : copy(locale, track.requestZh, track.requestEn);
    onGenerate(track.templateId, prompt);
  }
  return (
    <section className="cl-page cl-home-page">
      <PageTitle
        icon="home"
        locale={locale}
        titleZh={`${workspace.zh}套保课程`}
        titleEn={`${workspace.en} Hedging Course`}
        subtitleZh={productScope === "crude_oil"
          ? "先掌握通用金融工具，再进入基准、船货、月差、品级、库存和运费套保。"
          : "先掌握通用金融工具，再按风险复杂度完成本地市场、跨区域、跨币种和组合套保。"}
        subtitleEn={productScope === "crude_oil"
          ? "Master general instruments, then progress through benchmarks, cargoes, calendar spreads, grades, inventory, and freight hedging."
          : "Master general instruments, then progress through local-market, cross-regional, cross-currency, and portfolio hedging."}
      />
      <div className="cl-course-home">
        <section className="cl-panel cl-course-next">
          <div className="cl-course-next-copy">
            <span>{copy(locale, "下一课", "Next Lesson")}</span>
            <h3>{copy(locale, nextLesson.titleZh, nextLesson.titleEn)}</h3>
            <p>{activePlan?.objective ?? copy(locale, nextLesson.outcomeZh, nextLesson.outcomeEn)}</p>
            <div className="cl-course-next-meta">
              <span>{copy(locale, "所属阶段", "Stage")}<strong>{labelFor(locale, currentTrack)}</strong></span>
              <span>{copy(locale, "已完成阶段", "Completed stages")}<strong>{completedTracks}/{visibleTracks.length}</strong></span>
              <span>{copy(locale, "课程进度", "Course progress")}<strong>{courseProgress}%</strong></span>
            </div>
          </div>
          <button className="cl-primary" disabled={Boolean(loadingTemplate)} onClick={() => onGenerate(currentTrack.templateId, nextPrompt)} type="button"><Icon name="play" />{aiReady ? copy(locale, "开始本课", "Start Lesson") : copy(locale, "配置 AI", "Connect AI")}</button>
        </section>

        <section className="cl-panel cl-course-roadmap">
          <div className="cl-panel-heading"><span>{copy(locale, "课程顺序", "Course Sequence")}</span><strong>{copy(locale, "由基础到综合", "Foundation to Portfolio")}</strong></div>
          <ol className="cl-course-stage-list">
            {visibleTracks.map((track, index) => {
              const stats = attemptsForTrack(learningProgress, track);
              const syllabus = syllabusForTrack(track.id);
              const active = track.id === currentTrack.id;
              return (
                <li className={active ? "active" : stats.attempts ? "complete" : ""} key={track.id}>
                  <span className="cl-course-stage-number">{index + 1}</span>
                  <div className="cl-course-stage-copy">
                    <div><small>{copy(locale, track.levelZh, track.levelEn)}</small>{stats.score != null ? <b>{stats.score}/100</b> : null}</div>
                    <h3>{labelFor(locale, track)}</h3>
                    <p>{copy(locale, track.detailZh, track.detailEn)}</p>
                    <details>
                      <summary>{copy(locale, `查看 ${syllabus.lessons.length} 节课程`, `View ${syllabus.lessons.length} lessons`)}</summary>
                      <div className="cl-stage-lessons">
                        {syllabus.lessons.map((lesson, lessonIndex) => (
                          <button disabled={Boolean(loadingTemplate)} key={lesson.id} onClick={() => startLesson(track, lesson)} type="button">
                            <span>{lessonIndex + 1}</span>
                            <div><strong>{copy(locale, lesson.titleZh, lesson.titleEn)}</strong><small>{copy(locale, lesson.outcomeZh, lesson.outcomeEn)}</small></div>
                            <Icon name="arrow" />
                          </button>
                        ))}
                      </div>
                    </details>
                  </div>
                  <button className={active ? "cl-primary" : "cl-secondary"} disabled={Boolean(loadingTemplate)} onClick={() => startLesson(track)} type="button">
                    {stats.attempts ? copy(locale, "继续阶段", "Continue Stage") : copy(locale, "开始阶段", "Start Stage")}
                  </button>
                </li>
              );
            })}
          </ol>
          <div className="cl-course-library-link">
            <span>{copy(locale, "需要按业务类型或风险类型练习？", "Need practice by business or risk type?")}</span>
            <button className="cl-secondary" onClick={() => onPageChange(pageIds.library)} type="button"><Icon name="library" />{copy(locale, "打开练习库", "Open Practice Library")}</button>
          </div>
        </section>
      </div>
    </section>
  );
}

function AiCaseLabPage({ activeTemplateId, aiReady, businessTemplates, locale, loadingTemplate, onGenerate, productScope, setActiveTemplateId }) {
  const allTemplates = businessTemplates.templates?.length ? businessTemplates.templates : fallbackTemplates.templates;
  const templates = templatesForProduct(allTemplates, productScope);
  const [request, setRequest] = useState("");
  const [marketRegime, setMarketRegime] = useState("contango");
  const active = templates.find((template) => template.id === activeTemplateId) ?? templates[0];
  const activeCoverage = coverageForTemplate(active);
  const activeModels = modelsForTemplate(active);

  useEffect(() => {
    if (active?.id && active.id !== activeTemplateId) setActiveTemplateId(active.id);
  }, [active?.id, activeTemplateId, setActiveTemplateId]);

  function randomize() {
    const next = templates[Math.floor(Math.random() * templates.length)];
    setActiveTemplateId(next.id);
  }

  function marketGenerationOptions() {
    return {
      market_mode: "ai_simulated",
      market_regime: marketRegime,
      replay_id: null
    };
  }

  return (
    <section className="cl-page cl-case-lab-page" data-guide="case-lab">
      <PageTitle
        icon="sparkles"
        locale={locale}
        titleZh="自定义练习"
        titleEn="Custom Practice"
        subtitleZh="选择课程范围与市场条件，生成符合当前学习目标的练习。"
        subtitleEn="Choose a course scope and market conditions to create practice for your learning goal."
      />
      <div className="cl-case-studio">
        <section className="cl-panel cl-studio-composer">
          <label className="cl-studio-prompt">{copy(locale, "你想练什么？", "What do you want to practise?")}
            <textarea value={request} onChange={(event) => setRequest(event.target.value)} placeholder={productScope === "crude_oil"
              ? copy(locale, "例如：训练 Brent 计价船货在快速下跌中的采购套保。", "Example: practise a Brent-indexed cargo procurement hedge during a sharp selloff.")
              : copy(locale, "例如：训练跨枢纽供销中的价格、基差和汇率套保，市场快速下跌。", "Example: practise price, basis, and FX hedging for a cross-hub supply and sales position during a sharp selloff.")} />
          </label>
          <div className="cl-studio-setting-grid">
            <label>{copy(locale, "课程章节", "Course chapter")}<select value={active?.id ?? ""} onChange={(event) => setActiveTemplateId(event.target.value)}>{templates.map((template) => <option key={template.id} value={template.id}>{template.title}</option>)}</select></label>
            <label>{copy(locale, "远期曲线结构", "Forward curve structure")}
              <select value={marketRegime} onChange={(event) => setMarketRegime(event.target.value)}>
                <option value="contango">Contango</option>
                <option value="backwardation">Backwardation</option>
                <option value="flat">{copy(locale, "平坦", "Flat")}</option>
                <option value="volatile">{copy(locale, "高波动", "Volatile")}</option>
              </select>
            </label>
          </div>
          <div className="cl-studio-actions">
            <button className="cl-primary" disabled={!aiReady || loadingTemplate === active?.id} onClick={() => onGenerate(active?.id, request, marketGenerationOptions())} type="button"><Icon name="sparkles" />{loadingTemplate ? t("loading", locale) : copy(locale, "生成案例", "Generate Case")}</button>
            <button aria-label={copy(locale, "随机选择课程", "Randomize course")} className="cl-secondary" onClick={randomize} type="button"><Icon name="refresh" />{copy(locale, "换一个", "Randomize")}</button>
          </div>
          {!aiReady ? <p className="cl-studio-note">{copy(locale, "请先在设置中导入 AI 密钥。", "Import an AI key in Settings first.")}</p> : null}
        </section>
        <section className="cl-panel cl-ai-preview">
          <div className="cl-panel-heading"><span>{copy(locale, "本次训练", "This session")}</span><strong>{aiReady ? t("online", locale) : t("connectToEnable", locale)}</strong></div>
          <h3>{active?.title}</h3>
          <p>{active?.summary}</p>
          <div className="cl-chip-row">
            {(active?.knowledge_points ?? ["basis_spread", "physical_paper_matching"]).map((point) => <span key={point}>{knowledgePointLabel(locale, point, businessTemplates)}</span>)}
          </div>
          <div className="cl-preview-facts">
            <span>{copy(locale, "练习方式", "Practice mode")}<strong>{copy(locale, "分析行情并构建套保组合", "Analyse the market and build a hedge")}</strong></span>
            <span>{copy(locale, "市场环境", "Market setting")}<strong>{copy(locale, "AI 生成训练行情", "AI-generated training market")}</strong></span>
          </div>
          <div className="cl-preview-coverage">
            <h4>{copy(locale, "训练重点", "Learning Focus")}</h4>
            <div>
              {activeCoverage.slice(0, 4).map((item) => (
                <span key={item.id}>{labelFor(locale, item, "titleZh", "titleEn")}</span>
              ))}
            </div>
          </div>
          <p className="cl-preview-models">{copy(locale, "业务场景", "Business settings")}: {activeModels.slice(0, 3).map((item) => labelFor(locale, item, "titleZh", "titleEn")).join(" · ")}</p>
        </section>
      </div>
    </section>
  );
}

function ScenarioThumb({ scenarioId }) {
  const kind = scenarioId.includes("lng") ? "lng" : scenarioId.includes("eex") || scenarioId.includes("ocm") ? "window" : scenarioId.includes("efet") ? "contract" : scenarioId.includes("beach") || scenarioId.includes("pipeline") ? "pipeline" : "gas";
  return (
    <div className={`cl-thumb cl-thumb-${kind}`} aria-hidden="true">
      <svg viewBox="0 0 144 72" role="img">
        <rect width="144" height="72" rx="10" fill="rgba(255,255,255,.03)" />
        <path d="M0 55h144" stroke="rgba(255,255,255,.18)" strokeWidth="1" />
        {kind === "lng" ? (
          <>
            <path d="M21 47h71l-9 11H31Z" fill="rgba(230,244,255,.78)" />
            <path d="M33 37h34l8 10H27Z" fill="rgba(12,21,34,.72)" />
            <path d="M98 35h24v23H98zM102 30h16v5h-16z" fill="rgba(104,211,255,.52)" />
            <path d="M14 60c17-7 32 5 50 0s31-7 65 0" fill="none" stroke="#5fd1ff" strokeWidth="2" />
          </>
        ) : kind === "window" ? (
          <>
            <rect x="20" y="16" width="64" height="40" rx="6" fill="rgba(3,10,22,.58)" stroke="rgba(255,255,255,.24)" />
            <path d="M31 45V27M47 45V20M63 45V33M74 45V24" stroke="#52b7ff" strokeWidth="3" />
            <path d="M92 23h30M92 36h24M92 49h34" stroke="rgba(255,255,255,.52)" strokeWidth="2" />
          </>
        ) : kind === "contract" ? (
          <>
            <rect x="24" y="13" width="40" height="48" rx="5" fill="rgba(239,246,255,.82)" />
            <path d="M34 25h20M34 34h18M34 43h13" stroke="#0f3d70" strokeWidth="2" />
            <path d="M74 43c9-9 16-9 25 0M83 43l8 8 19-19" fill="none" stroke="#3ee6a0" strokeWidth="4" strokeLinecap="round" />
            <path d="M103 20h21v36h-21z" fill="rgba(54,118,193,.55)" />
          </>
        ) : kind === "pipeline" ? (
          <>
            <path d="M13 51h118" stroke="#8bd4ff" strokeWidth="8" strokeLinecap="round" />
            <path d="M33 51V29h20v22M88 51V23h24v28" fill="none" stroke="rgba(255,255,255,.72)" strokeWidth="4" />
            <path d="M18 36h24M67 36h55" stroke="rgba(255,255,255,.34)" strokeWidth="2" />
            <path d="M66 22l12 8-12 8" fill="none" stroke="#f8d36f" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          </>
        ) : (
          <>
            <path d="M30 55V28l18-10 18 10v27M78 55V24l18-8 18 8v31" fill="none" stroke="rgba(255,255,255,.72)" strokeWidth="4" />
            <path d="M21 55h103" stroke="#5fd1ff" strokeWidth="5" strokeLinecap="round" />
          </>
        )}
      </svg>
    </div>
  );
}

function scenarioFilterValue(item, filterId) {
  if (filterId === "difficulty") return item.difficultyEn;
  if (filterId === "status") return item.enabled ? "available" : "constructing";
  return item[filterId] ?? "";
}

function scenarioFilterLabel(locale, filterId, value) {
  const label = scenarioFilterLabels[filterId]?.[value];
  if (label) return copy(locale, label[0], label[1]);
  return value;
}

function scenarioFilterOptions(filterId, locale, items = scenarioLibraryItems) {
  const seen = new Set();
  return items
    .map((item) => scenarioFilterValue(item, filterId))
    .filter(Boolean)
    .filter((value) => {
      if (seen.has(value)) return false;
      seen.add(value);
      return true;
    })
    .map((value) => ({ value, label: scenarioFilterLabel(locale, filterId, value) }));
}

function ScenarioLibraryPage({ activeTemplateId, learningProgress, locale, loadingTemplate, onGenerate, onPageChange, onReview, productScope }) {
  const workspace = productWorkspace(productScope);
  const productItems = scenarioLibraryItems.filter((item) => item.commodity === scenarioCommodityForProduct(productScope));
  const filterDefinitions = scenarioFilterDefinitions.filter((item) => item.id !== "commodity");
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState(() => Object.fromEntries(filterDefinitions.map((item) => [item.id, "all"])));
  const visible = productItems.filter((item) => {
    const text = `${item.titleZh} ${item.titleEn} ${item.summaryZh} ${item.summaryEn} ${item.tags.join(" ")}`.toLowerCase();
    const matchesSearch = text.includes(query.trim().toLowerCase());
    const matchesFilters = filterDefinitions.every((filter) => filters[filter.id] === "all" || scenarioFilterValue(item, filter.id) === filters[filter.id]);
    return matchesSearch && matchesFilters;
  });
  const scenarioStat = (item) => learningProgress.scenarioStats[item.id] ?? null;
  const hasFilters = query.trim() || filterDefinitions.some((filter) => filters[filter.id] !== "all");
  function updateFilter(filterId, value) {
    setFilters((current) => ({ ...current, [filterId]: value }));
  }
  function clearFilters() {
    setQuery("");
    setFilters(Object.fromEntries(filterDefinitions.map((item) => [item.id, "all"])));
  }
  return (
    <section className="cl-page cl-library-page">
      <PageTitle
        icon="library"
        locale={locale}
        titleZh="练习库"
        titleEn="Practice Library"
        subtitleZh={`按风险复杂度学习${workspace.zh}套保，从单一价格敞口逐步进入跨区域与组合风险。`}
        subtitleEn={`Build ${workspace.en.toLowerCase()} hedging skills from single-price exposure to cross-regional and portfolio risk.`}
        action={<button className="cl-primary" onClick={() => onPageChange(pageIds.caseLab)} type="button"><Icon name="plus" />{copy(locale, "自定义练习", "Custom Practice")}</button>}
      />
      <div className="cl-library-grid cl-library-grid-single">
        <section className="cl-panel cl-library-main">
          <div className="cl-searchbar">
            <Icon name="search" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={copy(locale, "搜索场景标题、描述、标签或关键词...", "Search scenario titles, descriptions, tags, or keywords...")} />
          </div>
          <div className="cl-filter-row">
            {filterDefinitions.map((filter) => (
              <label key={filter.id}>
                <span>{copy(locale, filter.labelZh, filter.labelEn)}</span>
                <select value={filters[filter.id]} onChange={(event) => updateFilter(filter.id, event.target.value)}>
                  <option value="all">{copy(locale, `全部${filter.labelZh}`, `All ${filter.labelEn}`)}</option>
                  {scenarioFilterOptions(filter.id, locale, productItems).map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </select>
              </label>
            ))}
            {hasFilters ? <button className="cl-clear-filters" onClick={clearFilters} type="button">{copy(locale, "清除筛选", "Clear")}</button> : null}
          </div>
          <div className="cl-scenario-table">
            <div className="cl-scenario-head">
              <span>{copy(locale, "练习", "Practice")}</span><span>{copy(locale, "阶段 / 难度", "Stage / Level")}</span><span>{copy(locale, "预计时长", "Est.")}</span><span>{copy(locale, "进度", "Progress")}</span><span>{copy(locale, "操作", "Action")}</span>
            </div>
            {visible.map((item) => {
              const stat = scenarioStat(item);
              const progress = stat?.score ?? null;
              const reviewAvailable = Boolean(stat?.latest?.case_snapshot);
              return (
              <article className={!item.enabled ? "disabled" : ""} key={item.id}>
                <div className="cl-scenario-name">
                  <ScenarioThumb scenarioId={item.id} />
                  <div>
                    <strong>{copy(locale, item.titleZh, item.titleEn)}</strong>
                    <p>{copy(locale, item.summaryZh, item.summaryEn)}</p>
                    <div className="cl-chip-row">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
                  </div>
                </div>
                <span className="cl-scenario-level"><b>{scenarioFilterLabel(locale, "stage", item.stage)}</b><small>{copy(locale, item.difficultyZh, item.difficultyEn)}</small></span>
                <span>{item.duration}{item.duration === "--" ? "" : copy(locale, " 分钟", " min")}</span>
                <span className={progress == null ? "cl-progress-cell is-empty" : "cl-progress-cell"} style={{ "--pct": `${progress ?? 0}%` }}><b>{progress == null ? copy(locale, "未训练", "Not trained") : `${progress}%`}</b><i><em /></i></span>
                <span className="cl-row-actions">
                  <button disabled={!item.enabled} onClick={() => onGenerate(item.id || activeTemplateId)} type="button">{progress != null ? copy(locale, "继续", "Continue") : copy(locale, "开始", "Start")}</button>
                  <button disabled={!item.enabled || !reviewAvailable} onClick={() => onReview(stat.latest)} title={reviewAvailable ? "" : copy(locale, "完成一次正式提交后可复盘", "Review becomes available after a scored attempt")} type="button">{copy(locale, "复盘", "Review")}</button>
                </span>
              </article>
            );
            })}
            {!visible.length ? (
              <div className="cl-empty-table">
                <strong>{copy(locale, "没有匹配的场景", "No matching scenarios")}</strong>
                <button onClick={clearFilters} type="button">{copy(locale, "清除筛选", "Clear filters")}</button>
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </section>
  );
}

function DecisionTaskPanel({ caseData, locale }) {
  const volumeUnit = caseData.scenario?.exposure?.volume_unit ?? (/bbl|barrel/i.test(caseData.market?.unit ?? "") ? "bbl" : "MMBtu");
  return (
    <section className="cl-panel cl-decision-panel">
      <div className="cl-panel-heading"><span>1 {copy(locale, "决策任务", "Decision Task")}</span><strong>{caseData.scenario?.business_type}</strong></div>
      <MarkdownText text={caseData.prompt} />
      <div className="cl-exposure-strip">
        <span>{copy(locale, "方向", "Exposure")}<strong>{exposureDirectionLabel(caseData.scenario?.exposure?.direction, locale)}</strong></span>
        <span>{copy(locale, "数量", "Volume")}<strong>{formatNumber(caseData.scenario?.exposure?.volume_mmbtu)} {volumeUnit}</strong></span>
        <span>{copy(locale, "风险", "Risk")}<strong>{caseData.scenario?.exposure?.risk ?? "--"}</strong></span>
      </div>
    </section>
  );
}

function CaseHero({ activeTemplate, caseData, locale }) {
  return (
    <section className="cl-case-hero" data-guide="case-workspace">
      <div className="cl-case-image"><Icon name="flame" /></div>
      <div>
        <span>{activeTemplate?.business_type ?? caseData.scenario?.business_type}</span>
        <h2>{caseData.scenario?.title}</h2>
        <p>{caseData.scenario?.summary}</p>
        <div className="cl-chip-row">
          {(caseData.scenario?.knowledge_points ?? []).map((point) => <span key={point}>{point}</span>)}
        </div>
      </div>
      <dl>
        <div><dt>{copy(locale, "敞口方向", "Exposure Direction")}</dt><dd>{exposureDirectionLabel(caseData.scenario?.exposure?.direction, locale)}</dd></div>
        <div><dt>{copy(locale, "市场模式", "Market Mode")}</dt><dd>{trainingMarketModeLabel(caseData, locale)}</dd></div>
        <div><dt>{copy(locale, "会话状态", "Session Status")}</dt><dd>{trainingSessionStatusLabel(caseData, locale)}</dd></div>
      </dl>
    </section>
  );
}

function ReplayDecisionPanel({ advancing, caseData, decisionResult, locale, onAdvance }) {
  const replay = caseData.market?.replay;
  if (!replay?.event?.id) return null;
  const current = replay.current_checkpoint ?? {};
  const total = replay.event.checkpoint_count ?? Math.max((replay.visible_timeline ?? []).length, (current.index ?? 0) + 1);
  const visibleByIndex = Object.fromEntries((replay.visible_timeline ?? []).map((item) => [item.index, item]));
  const score = decisionResult?.evaluation?.baseline_score;
  return (
    <section className={advancing ? "cl-replay-console is-advancing" : "cl-replay-console"} aria-live="polite">
      <header>
        <div>
          <Icon name="history" />
          <span>{copy(locale, "事件复盘", "Event Replay")}</span>
          <strong>{replay.event.title}</strong>
        </div>
        <small>{copy(locale, `决策点 ${(current.index ?? 0) + 1} / ${total}`, `Checkpoint ${(current.index ?? 0) + 1} / ${total}`)}</small>
      </header>
      <div className="cl-replay-timeline" aria-label={copy(locale, "复盘进度", "Replay progress")}>
        {Array.from({ length: total }).map((_, index) => {
          const item = visibleByIndex[index];
          const status = index < (current.index ?? 0) ? "complete" : index === (current.index ?? 0) ? "active" : "locked";
          return (
            <div className={status} key={index}>
              <i>{index + 1}</i>
              <span>{item?.date ?? copy(locale, "待解锁", "Locked")}</span>
              <strong>{item?.label ?? copy(locale, "提交后揭示", "Reveal after decision")}</strong>
            </div>
          );
        })}
      </div>
      <div className="cl-replay-brief">
        <div>
          <small>{copy(locale, "当时已知信息", "Known at the time")}</small>
          <ul>{(current.facts ?? []).map((fact) => <li key={fact}>{fact}</li>)}</ul>
        </div>
        <div>
          <small>{copy(locale, "本节点决策", "Decision now")}</small>
          <p>{current.decision_required}</p>
          <em>{replay.information_policy}</em>
        </div>
      </div>
      {decisionResult ? (
        <div className="cl-replay-result">
          <div><small>{copy(locale, "节点得分", "Checkpoint score")}</small><strong>{score}/100</strong></div>
          <p><b>{decisionResult.feedback}</b><span>{decisionResult.outcome}</span></p>
          <button className="cl-primary" disabled={advancing} onClick={onAdvance} type="button">
            <Icon name={decisionResult.complete ? "chart" : "arrow"} />
            {advancing ? copy(locale, "正在推进市场...", "Advancing market...") : decisionResult.complete ? copy(locale, "完成复盘并查看总结", "Finish replay and review") : copy(locale, "揭示下一市场阶段", "Reveal next market phase")}
          </button>
          {decisionResult.alternative_strategies?.length ? (
            <details className="cl-replay-alternatives">
              <summary>{copy(locale, "比较可行替代方案", "Compare viable alternatives")}<span>{decisionResult.alternative_strategies.length}</span></summary>
              <div>
                {decisionResult.alternative_strategies.map((alternative) => (
                  <article key={alternative.id}>
                    <strong>{alternative.title}</strong>
                    <p>{alternative.rationale}</p>
                    <small>{copy(locale, "权衡：", "Trade-off: ")}{alternative.tradeoff}</small>
                    <ul>
                      {(alternative.legs ?? []).map((leg, index) => <li key={`${alternative.id}-${index}`}>{leg.leg_type} · {leg.market} · {leg.side} · {formatNumber(leg.quantity)} · {leg.tenor}</li>)}
                    </ul>
                  </article>
                ))}
              </div>
            </details>
          ) : null}
        </div>
      ) : (
        <div className="cl-replay-gate"><i /><span>{copy(locale, "先提交当前组合决策，后续市场信息才会解锁。", "Submit the current hedge decision before later market information is unlocked.")}</span></div>
      )}
    </section>
  );
}

function WorkbenchPage({ activeTemplate, advisorProps, aiInterventions, caseData, fieldSelection, locale, onAdvanceReplay, onCheckStrategy, onGenerateVariant, onPageChange, onSuggestTarget, replayAdvancing, replayDecision, strategyProps }) {
  if (caseData?.status === "empty") {
    return (
      <section className="cl-page cl-workbench-page">
        <PageTitle
          icon="workbench"
          locale={locale}
          titleZh="训练台"
          titleEn="Workbench"
          subtitleZh="在同一页面分析行情、构建套保组合并提交复盘。"
          subtitleEn="Analyse the market, build a hedge, and submit it for review on one screen."
        />
        <section className="cl-panel cl-workbench-empty">
          <div className="cl-workbench-empty-copy">
            <span className="cl-title-icon"><Icon name="sparkles" /></span>
            <div>
              <small>{copy(locale, "尚未选择练习", "No practice selected")}</small>
              <h3>{copy(locale, "从课程或练习库开始", "Start from a course or the practice library")}</h3>
              <p>{copy(locale, "选择一节课程，或按业务类型和风险类型查找练习。", "Choose a lesson, or find practice by business type and risk.")}</p>
            </div>
          </div>
          <div className="cl-workbench-empty-actions">
            <button className="cl-primary" onClick={() => onPageChange(pageIds.home)} type="button"><Icon name="home" />{copy(locale, "返回课程", "Open Courses")}</button>
            <button className="cl-secondary" onClick={() => onPageChange(pageIds.library)} type="button"><Icon name="library" />{copy(locale, "打开练习库", "Open Practice Library")}</button>
          </div>
        </section>
      </section>
    );
  }
  const isGenerating = caseData?.status === "generating";
  const isReplay = Boolean(caseData.market?.replay?.event?.id);
  return (
    <section className="cl-page cl-workbench-page">
      <CaseHero activeTemplate={activeTemplate} caseData={caseData} locale={locale} />
      <ReplayDecisionPanel advancing={replayAdvancing} caseData={caseData} decisionResult={replayDecision} locale={locale} onAdvance={onAdvanceReplay} />
      <div className="cl-workbench-grid">
        <div className="cl-workbench-left">
          {!isReplay ? <DecisionTaskPanel caseData={caseData} locale={locale} /> : null}
          <MarketChart caseData={caseData} fieldSelection={fieldSelection.value} locale={locale} setFieldSelection={fieldSelection.set} strategyLegs={strategyProps.strategyLegs} />
        </div>
        <div className="cl-workbench-center">
          <section className="cl-panel cl-strategy-tools">
            <div className="cl-panel-heading"><span>3 {copy(locale, "策略构建", "Build Strategy")}</span><strong>{copy(locale, "即时检查", "Instant check")}</strong></div>
            <div className="cl-action-grid">
              {!isReplay ? <button disabled={isGenerating} onClick={onSuggestTarget} type="button"><Icon name="sparkles" />{copy(locale, "AI 建议策略腿", "AI Suggest Legs")}</button> : null}
              {!isReplay ? <button disabled={isGenerating} onClick={onCheckStrategy} type="button"><Icon name="coach" />{copy(locale, "提交前检查", "Check Before Submit")}</button> : null}
              {!isReplay ? <button disabled={isGenerating} onClick={onGenerateVariant} type="button"><Icon name="plus" />{copy(locale, "生成变体", "Generate Variant")}</button> : null}
              <button className="cl-submit-inline" disabled={strategyProps.busy || strategyProps.locked} onClick={strategyProps.onSubmit} type="button"><Icon name="chart" />{strategyProps.locked ? copy(locale, "本节点已提交", "Checkpoint submitted") : strategyProps.busy ? t("loading", locale) : t("submitOrder", locale)}</button>
            </div>
          </section>
          <AiControlLog interventions={aiInterventions} locale={locale} />
          <StrategyBuilder {...strategyProps} />
          {!isReplay ? <RiskCoverageMap caseData={caseData} locale={locale} strategyLegs={strategyProps.strategyLegs} /> : null}
          <div className="cl-bottom-grid">
            {strategyProps.evaluation ? <ScorePanel evaluation={strategyProps.evaluation} locale={locale} /> : null}
            <RubricPanel caseData={caseData} locale={locale} />
          </div>
        </div>
        <AdvisorRail {...advisorProps} />
      </div>
    </section>
  );
}

function ReviewPage({ advisorFeedback, caseData, evaluation, exam, locale, onGenerateCounterfactual, onGenerateVariant, onPageChange, onSubmitExam, replayHistory = [], runAiAction, strategyLegs }) {
  const target = caseData.target_actions ?? [];
  const structuredExam = normalizeExamPayload(exam);
  const quizQuestions = structuredExam?.questions ?? [];
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizResult, setQuizResult] = useState(null);
  useEffect(() => {
    setQuizAnswers({});
    setQuizResult(null);
  }, [structuredExam?.id]);
  const quizOnly = quizQuestions.length > 0 && !evaluation;
  const isReplay = replayHistory.length > 0;
  const replayAverage = isReplay ? Math.round(replayHistory.reduce((sum, item) => sum + Number(item.evaluation?.baseline_score ?? 0), 0) / replayHistory.length) : null;
  function submitQuiz(event) {
    event.preventDefault();
    if (quizQuestions.some((question) => quizAnswers[question.id] == null)) return;
    const skillTotals = {};
    let correctCount = 0;
    quizQuestions.forEach((question) => {
      const correct = Number(quizAnswers[question.id]) === Number(question.correct_index);
      if (correct) correctCount += 1;
      (question.skills ?? ["instrument"]).forEach((skill) => {
        const current = skillTotals[skill] ?? { correct: 0, total: 0 };
        current.total += 1;
        if (correct) current.correct += 1;
        skillTotals[skill] = current;
      });
    });
    const result = {
      baseline_score: Math.round((correctCount / quizQuestions.length) * 100),
      correct_count: correctCount,
      total: quizQuestions.length,
      skill_scores: Object.fromEntries(Object.entries(skillTotals).map(([skill, value]) => [skill, Math.round((value.correct / value.total) * 100)])),
      mistake_tags: quizQuestions.filter((question) => Number(quizAnswers[question.id]) !== Number(question.correct_index)).flatMap((question) => question.skills ?? ["instrument"])
    };
    setQuizResult(result);
    onSubmitExam?.(result, structuredExam);
  }
  const quizPanel = quizQuestions.length ? (
    <section className="cl-panel cl-quiz-panel">
      <div className="cl-panel-heading"><span>{structuredExam?.title ?? copy(locale, "AI 测验模式", "AI Quiz Mode")}</span><strong>{quizResult ? `${quizResult.baseline_score}/100` : copy(locale, "即时评分", "Instant scoring")}</strong></div>
      <form className="cl-quiz-form" onSubmit={submitQuiz}>
        <div className="cl-quiz-list">
          {quizQuestions.map((question, index) => {
            const answered = quizAnswers[question.id] != null;
            const correct = answered && Number(quizAnswers[question.id]) === Number(question.correct_index);
            return (
              <article className={quizResult ? correct ? "is-correct" : "is-incorrect" : ""} key={question.id}>
                <small>{copy(locale, `问题 ${index + 1}`, `Question ${index + 1}`)}</small>
                <p>{question.prompt}</p>
                <div className="cl-quiz-options">
                  {question.options.map((option, optionIndex) => (
                    <label key={`${question.id}-${optionIndex}`}>
                      <input checked={Number(quizAnswers[question.id]) === optionIndex} disabled={Boolean(quizResult)} name={question.id} onChange={() => setQuizAnswers((current) => ({ ...current, [question.id]: optionIndex }))} type="radio" />
                      <span>{option}</span>
                    </label>
                  ))}
                </div>
                {quizResult ? <div className="cl-quiz-explanation"><strong>{correct ? copy(locale, "回答正确", "Correct") : copy(locale, "需要复习", "Review needed")}</strong><span>{question.explanation}</span></div> : null}
              </article>
            );
          })}
        </div>
        <div className="cl-quiz-submit">
          {quizResult ? <p>{copy(locale, `答对 ${quizResult.correct_count}/${quizResult.total} 题，结果已计入学习进度。`, `${quizResult.correct_count}/${quizResult.total} correct. This result is now part of your learning progress.`)}</p> : <p>{copy(locale, "完成全部题目后即可查看结果。", "Answer every question to view your result.")}</p>}
          <button className="cl-primary" disabled={Boolean(quizResult) || Object.keys(quizAnswers).length !== quizQuestions.length} type="submit"><Icon name="chart" />{copy(locale, "提交测验", "Submit quiz")}</button>
        </div>
      </form>
    </section>
  ) : null;
  return (
    <section className="cl-page cl-review-page">
      <PageTitle
        icon="chart"
        locale={locale}
        titleZh="复盘反馈"
        titleEn="Review & Feedback"
        subtitleZh="把你的组合动作和 AI 生成的目标动作逐项对照，再进入强化训练。"
        subtitleEn="Compare your multi-leg strategy with the AI-generated target before reinforcement drills."
        action={isReplay ? <button className="cl-primary" onClick={() => onPageChange(pageIds.home)} type="button"><Icon name="arrow" />{copy(locale, "返回学习路径", "Back to Learning Path")}</button> : quizOnly ? <button className="cl-primary" onClick={onGenerateVariant} type="button"><Icon name="sparkles" />{copy(locale, "生成类似练习", "Generate similar drill")}</button> : <button className="cl-primary" onClick={() => runAiAction("advisor_review")} disabled={!evaluation} type="button"><Icon name="coach" />{copy(locale, "AI 解释评分", "AI Explain Score")}</button>}
      />
      <div className="cl-review-grid">
        {quizOnly ? quizPanel : null}
        {!quizOnly ? (
          <>
        {isReplay ? (
          <section className="cl-panel cl-replay-review">
            <div className="cl-panel-heading"><span>{copy(locale, "事件决策轨迹", "Event Decision Trail")}</span><strong>{copy(locale, `平均 ${replayAverage}/100`, `Average ${replayAverage}/100`)}</strong></div>
            <div>
              {replayHistory.map((item) => (
                <article key={item.checkpoint?.index}>
                  <i>{(item.checkpoint?.index ?? 0) + 1}</i>
                  <div><small>{item.checkpoint?.date}</small><strong>{item.checkpoint?.label}</strong><p>{item.feedback}</p></div>
                  <b>{item.evaluation?.baseline_score}</b>
                </article>
              ))}
            </div>
          </section>
        ) : null}
        {advisorFeedback ? (
          <section className="cl-panel cl-review-advisor" aria-live="polite">
            <div className="cl-panel-heading"><span>{copy(locale, "AI 节点复盘", "AI Checkpoint Review")}</span><strong>{copy(locale, "基于当前案例", "Current case")}</strong></div>
            <MarkdownText text={advisorFeedback} />
          </section>
        ) : null}
        <section className="cl-panel cl-score-summary">
          <div className="cl-progress-ring large" style={{ "--score": `${((isReplay ? replayAverage : evaluation?.baseline_score) ?? 0) * 3.6}deg` }}><strong>{isReplay ? replayAverage : evaluation?.baseline_score ?? "--"}</strong><span>/100</span></div>
          <h3>{isReplay ? copy(locale, "历史复盘已完成", "Historical replay complete") : evaluation ? copy(locale, "策略评估已完成", "Strategy review complete") : copy(locale, "尚未提交策略", "No strategy submitted")}</h3>
          <p>{isReplay ? copy(locale, "每个节点均按当时信息独立评分；后续事实只在提交后揭示。", "Each checkpoint was scored on information available at the time; later facts were revealed only after submission.") : copy(locale, "查看得分、风险覆盖和改进建议，再进入下一项练习。", "Review the score, risk coverage, and improvement actions before the next drill.")}</p>
          <div className="cl-action-row">
            <button className="cl-secondary" onClick={() => onPageChange(pageIds.workbench)} type="button">{copy(locale, "回到工作台", "Back to Workbench")}</button>
            {isReplay ? <button className="cl-primary" onClick={onGenerateCounterfactual} type="button"><Icon name="sparkles" />{copy(locale, "生成反事实练习", "Generate counterfactual")}</button> : <button className="cl-primary" onClick={onGenerateVariant} type="button">{copy(locale, "训练弱项变体", "Drill Weak Variant")}</button>}
          </div>
        </section>
        {!isReplay ? (
          <>
            <section className="cl-panel cl-comparison-panel">
              <div className="cl-panel-heading"><span>{copy(locale, "用户策略 vs 目标动作", "User Strategy vs Target Actions")}</span><strong>{formatNumber(strategyLegs.length)} / {formatNumber(target.length)}</strong></div>
              <div className="cl-compare-table">
                <div><strong>{copy(locale, "你的动作", "Your Legs")}</strong><strong>{copy(locale, "目标动作", "Target Legs")}</strong></div>
                {Array.from({ length: Math.max(strategyLegs.length, target.length, 1) }).map((_, index) => (
                  <div key={index}>
                    <span>{strategyLegs[index] ? `${strategyLegs[index].leg_type} / ${strategyLegs[index].market} / ${strategyLegs[index].side}` : "--"}</span>
                    <span>{target[index] ? `${target[index].leg_type} / ${target[index].market} / ${target[index].side}` : "--"}</span>
                  </div>
                ))}
              </div>
            </section>
            <section className="cl-panel">
              <div className="cl-panel-heading"><span>{copy(locale, "常见错误", "Common Mistakes")}</span><strong>{copy(locale, "随案例生成", "Generated with case")}</strong></div>
              {evaluation?.mistake_tags?.length ? (
                <ul className="cl-mistake-list">
                  {evaluation.mistake_tags.map((tag) => <li key={tag}>{mistakeLabel(tag, locale)}</li>)}
                </ul>
              ) : <p className="empty-state">{copy(locale, "目标动作、数量、期限和风险说明均通过本地检查。", "Target legs, quantity, tenor, and rationale passed the local checks.")}</p>}
            </section>
          </>
        ) : null}
          </>
        ) : null}
      </div>
    </section>
  );
}

function KnowledgeMapPage({ locale, onPageChange, onRequestLearningPath, productScope, runAiAction }) {
  const workspace = productWorkspace(productScope);
  const productNodeIds = productScope === "crude_oil"
    ? new Set(["physical", "basis", "fx", "risk", "crudeBench"])
    : new Set(["physical", "basis", "fx", "risk", "hub", "lng", "capacity", "storage", "exchange"]);
  const productLevels = knowledgeFlowLevels
    .map((level) => ({ ...level, nodes: level.nodes.filter((nodeId) => productNodeIds.has(nodeId)) }))
    .filter((level) => level.nodes.length);
  const productCoverage = coverageForProduct(productScope);
  const generalCoverage = productCoverage.filter((item) => generalCoverageIds.has(item.id));
  const specificCoverage = productCoverage.filter((item) => !generalCoverageIds.has(item.id));
  const productModels = modelsForProduct(productScope);
  const [selected, setSelected] = useState(productScope === "crude_oil" ? "crudeBench" : "hub");
  const nodeById = useMemo(() => Object.fromEntries(knowledgeNodes.map((item) => [item.id, item])), []);
  const node = knowledgeNodes.find((item) => item.id === selected && productNodeIds.has(item.id)) ?? nodeById[productScope === "crude_oil" ? "crudeBench" : "hub"];
  const pathItems = productScope === "crude_oil" ? [
    ["通识：敞口与金融工具", "General: Exposure and Instruments"],
    ["Brent / WTI / Dubai 基准", "Brent / WTI / Dubai Benchmarks"],
    ["船货、品级与地点基差", "Cargo, Grade, and Location Basis"],
    ["月差、库存与运费", "Calendar, Inventory, and Freight"],
    ["组合执行与复盘", "Portfolio Execution and Review"]
  ] : [
    ["通识：敞口与金融工具", "General: Exposure and Instruments"],
    ["枢纽定价与实货合同", "Hub Pricing and Physical Contracts"],
    ["EFET / OCM / EEX 工具", "EFET / OCM / EEX Instruments"],
    ["LNG、运力、储气与平衡", "LNG, Capacity, Storage, and Balancing"],
    ["组合执行与复盘", "Portfolio Execution and Review"]
  ];

  useEffect(() => {
    setSelected(productScope === "crude_oil" ? "crudeBench" : "hub");
  }, [productScope]);
  return (
    <section className="cl-page cl-knowledge-page">
      <PageTitle
        icon="map"
        locale={locale}
        titleZh="知识图谱"
        titleEn="Knowledge Map"
        subtitleZh={`先学跨品种通识，再按顺序进入${workspace.zh}市场、业务场景和训练题。`}
        subtitleEn={`Learn inter-commodity fundamentals first, then progress through ${workspace.en.toLowerCase()} markets, business cases, and drills.`}
        action={<button className="cl-primary" onClick={() => onRequestLearningPath(node)} type="button"><Icon name="sparkles" />{copy(locale, "生成学习路径", "Generate Learning Path")}</button>}
      />
      <div className="cl-knowledge-grid">
        <section className="cl-panel cl-learning-map">
          <div className="cl-learning-map-head">
            <LogoMark />
            <div>
              <strong>{copy(locale, "商品套保学习顺序", "Commodity Hedging Learning Order")}</strong>
              <span>{copy(locale, "从业务语言到组合交易，再到执行复盘。", "From business language to multi-leg execution and review.")}</span>
            </div>
          </div>
          <div className="cl-learning-flow-map">
            {productLevels.map((level, levelIndex) => (
              <div className={`cl-learning-tier ${level.id}`} key={level.id}>
                <div className="cl-tier-label">
                  <b>{levelIndex + 1}</b>
                  <span>{copy(locale, level.titleZh, level.titleEn)}</span>
                  <small>{copy(locale, level.descZh, level.descEn)}</small>
                </div>
                <div className="cl-tier-nodes">
                  {level.nodes.map((nodeId) => {
                    const item = nodeById[nodeId];
                    if (!item) return null;
                    return (
                      <button className={selected === item.id ? `active ${item.level}` : item.level} key={item.id} onClick={() => setSelected(item.id)} type="button">
                        <span>{labelFor(locale, item, "titleZh", "titleEn")}</span>
                        <small>{levelLabel(locale, item.level)}</small>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </section>
        <aside className="cl-panel cl-topic-panel">
          <div className="cl-panel-heading"><span>{copy(locale, "选中主题", "Selected Topic")}</span><strong>{levelLabel(locale, node.level)}</strong></div>
          <h3>{labelFor(locale, node, "titleZh", "titleEn")}</h3>
          <p>{copy(locale, node.descZh, node.descEn)}</p>
          <h4>{copy(locale, "为什么重要", "Why it matters")}</h4>
          <p>{copy(locale, "它决定实货动作和纸货工具是否真正覆盖同一个风险，尤其影响基差、汇率、运力和履约。", "It decides whether physical and paper legs truly cover the same risk, especially basis, FX, capacity, and performance.")}</p>
          <div className="cl-action-grid">
            <button onClick={() => runAiAction("concept_tutor")} type="button">{copy(locale, "讲解概念", "Explain Concept")}</button>
            <button onClick={() => runAiAction("exam")} type="button">{copy(locale, "考我一下", "Quiz Me")}</button>
            <button onClick={() => onPageChange(pageIds.caseLab)} type="button">{copy(locale, "生成练习案例", "Generate Practice Case")}</button>
          </div>
        </aside>
      </div>
      <section className="cl-panel cl-path-panel">
        <div className="cl-panel-heading"><span>{copy(locale, "推荐路径", "Recommended Path")}</span><strong>{copy(locale, `通识 + ${workspace.zh}`, `General + ${workspace.en}`)}</strong></div>
        <div className="cl-path-row">{pathItems.map(([zh, en], index) => <span key={en}><b>{index + 1}</b>{copy(locale, zh, en)}</span>)}</div>
      </section>
      <section className="cl-panel cl-coverage-panel">
        <div className="cl-panel-heading"><span>{copy(locale, "通识金融工具", "General Hedging Tools")}</span><strong>{copy(locale, "跨品种共用", "Inter-commodity")}</strong></div>
        <div className="cl-coverage-grid">
          {generalCoverage.map((item) => (
            <article key={item.id}>
              <header>
                <b>{labelFor(locale, item, "titleZh", "titleEn")}</b>
                <small>{copy(locale, item.conceptsZh, item.conceptsEn).slice(0, 2).join(" / ")}</small>
              </header>
              <p>{copy(locale, item.summaryZh, item.summaryEn)}</p>
              <div className="cl-mini-chip-row">
                {copy(locale, item.conceptsZh, item.conceptsEn).slice(0, 4).map((concept) => <span key={concept}>{concept}</span>)}
              </div>
            </article>
          ))}
        </div>
        {specificCoverage.length ? <>
          <div className="cl-panel-heading cl-coverage-subheading"><span>{labelFor(locale, workspace)}</span><strong>{copy(locale, "产品专属知识", "Product-specific knowledge")}</strong></div>
          <div className="cl-coverage-grid">
            {specificCoverage.map((item) => (
              <article key={item.id}>
                <header><b>{labelFor(locale, item, "titleZh", "titleEn")}</b><small>{copy(locale, item.conceptsZh, item.conceptsEn).slice(0, 2).join(" / ")}</small></header>
                <p>{copy(locale, item.summaryZh, item.summaryEn)}</p>
                <div className="cl-mini-chip-row">{copy(locale, item.conceptsZh, item.conceptsEn).slice(0, 4).map((concept) => <span key={concept}>{concept}</span>)}</div>
              </article>
            ))}
          </div>
        </> : null}
      </section>
      <section className="cl-panel cl-model-panel">
        <div className="cl-panel-heading"><span>{copy(locale, "业务应用", "Business Applications")}</span><strong>{copy(locale, "场景实践", "Scenario Practice")}</strong></div>
        <div className="cl-gas-model-grid">
          {productModels.map((item) => (
            <article key={item.id}>
              <strong>{labelFor(locale, item, "titleZh", "titleEn")}</strong>
              <p>{copy(locale, item.summaryZh, item.summaryEn)}</p>
              <div className="cl-model-columns">
                <span>{copy(locale, "风险", "Risks")}<b>{copy(locale, item.risksZh, item.risksEn).join(" / ")}</b></span>
                <span>{copy(locale, "工具", "Tools")}<b>{copy(locale, item.instrumentsZh, item.instrumentsEn).join(" / ")}</b></span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}

function ProgressPage({ learningProgress, locale, onGenerateWeakPoint, onPageChange }) {
  const hasProgress = learningProgress.hasRecords;
  const weakSummary = learningProgress.weakest.length
    ? learningProgress.weakest.map((item) => labelFor(locale, item, "zh", "en")).join(" / ")
    : copy(locale, "完成一次评分后自动生成。", "Generated after your first scored attempt.");
  return (
    <section className="cl-page cl-progress-page">
      <PageTitle
        icon="progress"
        locale={locale}
        titleZh="我的进度"
        titleEn="My Progress"
        subtitleZh="按套保能力维度追踪弱项，而不是只看完成百分比。"
        subtitleEn="Track hedging skill dimensions instead of only completion percentage."
        action={hasProgress ? <button className="cl-primary" onClick={onGenerateWeakPoint} type="button"><Icon name="plus" />{copy(locale, "生成弱项训练", "Generate Weak-Point Drill")}</button> : null}
      />
      <div className={`cl-progress-layout${hasProgress ? "" : " is-empty"}`}>
        <section className="cl-panel">
          <div className="cl-panel-heading"><span>{copy(locale, "能力画像", "Capability Profile")}</span><strong>{hasProgress ? `${learningProgress.latestScore}/100` : copy(locale, "暂无记录", "No records")}</strong></div>
          {hasProgress ? (
            <>
              <div className="cl-progress-facts">
                <span>{copy(locale, "训练会话", "Training sessions")}<strong>{learningProgress.sessions}</strong></span>
                <span>{copy(locale, "正式提交", "Scored attempts")}<strong>{learningProgress.attempts}</strong></span>
                <span>{copy(locale, "最近得分", "Latest score")}<strong>{learningProgress.latestScore ?? "--"}</strong></span>
                <span>{copy(locale, "平均得分", "Average score")}<strong>{learningProgress.averageScore ?? "--"}</strong></span>
                {learningProgress.replayCheckpoints ? <span>{copy(locale, "复盘节点", "Replay checkpoints")}<strong>{learningProgress.replayCheckpoints}</strong></span> : null}
              </div>
              <div className="cl-skill-bars">
                {learningProgress.dimensions.map((item) => (
                  <div className={item.score == null ? "is-empty" : ""} key={item.id}>
                    <span>{labelFor(locale, item, "zh", "en")}</span>
                    <i><b style={{ width: `${item.score ?? 0}%` }} /></i>
                    <strong>{item.score == null ? "--" : item.score}</strong>
                    <small>{copy(locale, `样本 ${item.samples}`, `${item.samples} samples`)}</small>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="cl-empty-progress large">
              <strong>{copy(locale, "还没有可用于进度分析的训练记录", "No training records available for progress analysis")}</strong>
              <p>{copy(locale, "完成第一次练习后，这里将展示能力得分、薄弱项和复习计划。", "Complete your first practice to see skill scores, weak areas, and review plans here.")}</p>
              <button className="cl-primary" onClick={() => onPageChange(pageIds.home)} type="button">{copy(locale, "开始第一课", "Start first lesson")}</button>
            </div>
          )}
        </section>
        {hasProgress ? <section className="cl-panel">
          <div className="cl-panel-heading"><span>{copy(locale, "AI 推荐下一步", "AI Recommended Next Step")}</span><strong>{copy(locale, "基于弱项", "Based on weak points")}</strong></div>
          <h3>{copy(locale, "按当前弱项生成下一题", "Generate the next drill from current weak points")}</h3>
          <p>{copy(locale, "建议重点：", "Recommended focus: ") + weakSummary}</p>
          {learningProgress.nextReview ? <p className="cl-review-due"><strong>{copy(locale, "复习计划：", "Review plan: ")}</strong>{learningProgress.dueReviews
            ? copy(locale, `${learningProgress.dueReviews} 个场景到期`, `${learningProgress.dueReviews} scenario(s) due`)
            : copy(locale, `下次复习 ${new Date(learningProgress.nextReview.nextReviewAt).toLocaleDateString(locale === "zh" ? "zh-CN" : "en-US")}`, `Next review ${new Date(learningProgress.nextReview.nextReviewAt).toLocaleDateString("en-US")}`)}</p> : null}
          <button className="cl-primary" onClick={onGenerateWeakPoint} type="button">{copy(locale, "开始推荐训练", "Start Recommended Drill")}</button>
        </section> : null}
      </div>
    </section>
  );
}

function AiCoachPage({ aiReady, applyAction, locale, messages, onSend, thinking }) {
  const [draft, setDraft] = useState("");
  async function submit(event) {
    event.preventDefault();
    if (!draft.trim()) return;
    await onSend(draft.trim());
    setDraft("");
  }
  return (
    <section className="cl-page cl-coach-page">
      <PageTitle
        icon="coach"
        locale={locale}
        titleZh="AI 教练"
        titleEn="AI Coach"
        subtitleZh="让 AI 生成案例、解释概念、检查策略，并在安全范围内改动当前工作台。"
        subtitleEn="Ask AI to generate cases, explain concepts, check strategies, and safely customize the workspace."
      />
      <div className="cl-coach-grid">
        <section className="cl-panel cl-chat-panel">
          <div className="assistant-messages">
            {messages.length ? messages.map((message, index) => (
              <article className={message.role} key={index}>
                <MarkdownText text={message.content} />
                {message.actions?.length ? <div className="assistant-actions">{message.actions.map((action, i) => <button key={i} onClick={() => applyAction(action)} type="button">{action.label ?? action.type}</button>)}</div> : null}
              </article>
            )) : <p className="empty-state">{t("assistantEmpty", locale)}</p>}
            {thinking ? <AiThinkingPanel locale={locale} titleKey="assistantWorking" /> : null}
          </div>
          <form className="cl-chat-form" onSubmit={submit}>
            <textarea disabled={!aiReady || thinking} value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={t("assistantPlaceholder", locale)} />
            <button className="cl-primary" disabled={!aiReady || thinking || !draft.trim()} type="submit">{thinking ? t("loading", locale) : t("send", locale)}</button>
          </form>
        </section>
        <aside className="cl-panel cl-coach-actions">
          <div className="cl-panel-heading"><span>{copy(locale, "常用请求", "Common Requests")}</span><strong>{aiReady ? t("online", locale) : t("offline", locale)}</strong></div>
          {[
            copy(locale, "生成一个欧洲天然气跨枢纽供销套保训练题。", "Generate a European gas cross-hub supply and sales hedging drill."),
            copy(locale, "解释 TTF/NBP 基差风险和实货纸货如何匹配。", "Explain TTF/NBP basis risk and physical-paper matching."),
            copy(locale, "检查我的策略有没有漏掉汇率、运力或信用风险。", "Check whether my strategy misses FX, capacity, or credit risk."),
            copy(locale, "根据我上一次错误生成一个更难的变体。", "Generate a harder variant based on my last mistakes.")
          ].map((prompt) => <button key={prompt} onClick={() => onSend(prompt)} disabled={!aiReady || thinking} type="button">{prompt}</button>)}
        </aside>
      </div>
    </section>
  );
}

function SettingsPage({ locale, settingsPanel }) {
  return (
    <section className="cl-page cl-settings-page">
      <PageTitle
        icon="settings"
        locale={locale}
        titleZh="设置"
        titleEn="Settings"
        subtitleZh="管理语言、主题、AI 供应方、密钥文件导入、版本更新和开发者信息。"
        subtitleEn="Manage language, theme, AI provider, key-file import, version updates, and developer information."
      />
      <section className="cl-panel cl-settings-shell">{settingsPanel}</section>
    </section>
  );
}

function FloatingAssistant({ activePage, aiReady, applyAction, assistantStage, interventions, locale, messages, onOpen, onSend, thinking }) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const currentPage = navItems.find((item) => item.id === activePage);
  const quickPrompts = [
    copy(locale, "按当前课程生成下一道训练题。", "Generate the next drill for the current course."),
    copy(locale, "用三句话解释当前页面的核心知识点。", "Explain the current page concept in three sentences."),
    copy(locale, "检查当前策略还缺少哪些风险动作。", "Check which risk actions are missing from the current strategy.")
  ];
  const controlPrompts = [
    {
      label: copy(locale, "显示高低收", "Show high/low/close"),
      message: copy(locale, "把行情曲线切换为显示 High、Low、Close，并说明波动风险。", "Show high/low/close on the chart and explain volatility risk.")
    },
    {
      label: copy(locale, "填充策略腿", "Fill strategy legs"),
      message: copy(locale, "根据当前题目补全一个实货腿、纸货腿和必要的基差/汇率/运力腿。", "Fill the strategy with a physical leg, paper hedge, and any basis, FX, or capacity leg needed.")
    },
    {
      label: copy(locale, "下一道练习", "Next drill"),
      message: copy(locale, "基于当前课程生成下一道训练题，并切换到适合答题的界面。", "Generate the next drill from the current course and switch to the right workspace.")
    },
    {
      label: copy(locale, "生成测验", "Generate quiz"),
      message: copy(locale, "根据当前课程和最近练习生成一套简短测验，并直接打开复盘测验页。", "Generate a short quiz from the current course and recent practice, then open the review quiz page.")
    },
    {
      label: copy(locale, "提交策略", "Submit strategy"),
      message: copy(locale, "提交当前策略并打开复盘页。", "Submit the current strategy and open Review.")
    },
    {
      label: copy(locale, "检查缺口", "Check gaps"),
      message: copy(locale, "检查我当前策略还缺少哪些风险覆盖动作，回答要简短并给出可执行调整。", "Check the risk coverage gaps in my current strategy. Keep it concise and give actionable changes.")
    }
  ];
  async function submit(event) {
    event.preventDefault();
    if (!draft.trim()) return;
    await onSend(draft.trim());
    setDraft("");
  }
  return (
    <div className={open ? "floating-assistant open" : "floating-assistant"} data-guide="floating-assistant">
      {open ? (
        <section className={interventions?.length ? "assistant-panel has-interventions" : "assistant-panel"}>
          <header>
            <div>
              <span>{t("liveAssistant", locale)}</span>
              <strong>{aiReady ? t("online", locale) : t("offline", locale)} · {currentPage ? labelFor(locale, currentPage) : "Commodity Lab"}</strong>
            </div>
            <button className="icon-button" aria-label={t("close", locale)} onClick={() => setOpen(false)} type="button"><Icon name="close" /></button>
          </header>
          {interventions?.length ? (
            <div className="assistant-interventions">
              <span>{copy(locale, "AI 刚刚改动", "Recent AI changes")}</span>
              {interventions.slice(0, 3).map((item) => <button key={item.id} onClick={() => item.page ? applyAction({ type: "navigate_page", payload: { page: item.page } }) : null} type="button"><Icon name="sparkles" />{item.label}</button>)}
            </div>
          ) : null}
          <div className="assistant-command-bar" aria-label={copy(locale, "AI 控制面板", "AI controls")}>
            <span>{copy(locale, "AI 控制面板", "AI controls")}</span>
            <div>
              {controlPrompts.map((prompt) => (
                <button disabled={!aiReady || thinking} key={prompt.label} onClick={() => onSend(prompt.message)} type="button">{prompt.label}</button>
              ))}
            </div>
          </div>
          <div className="assistant-messages">
            {messages.length ? messages.map((message, index) => (
              <article className={message.role} key={index}>
                <MarkdownText text={message.content} />
                {message.actions?.length ? <div className="assistant-actions">{message.actions.map((action, i) => <button key={i} onClick={() => applyAction(action)} type="button">{action.label ?? action.type}</button>)}</div> : null}
              </article>
            )) : (
              <div className="assistant-empty">
                <strong>{copy(locale, "AI 学习助手", "AI learning assistant")}</strong>
                <p>{t("assistantEmpty", locale)}</p>
                <div className="assistant-quick-prompts">
                  {quickPrompts.map((prompt) => (
                    <button disabled={!aiReady || thinking} key={prompt} onClick={() => onSend(prompt)} type="button">{prompt}</button>
                  ))}
                </div>
              </div>
            )}
            {thinking ? <AiThinkingPanel activeStage={assistantStage} locale={locale} titleKey="assistantWorking" /> : null}
          </div>
          <form onSubmit={submit}><textarea disabled={!aiReady || thinking} value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={t("assistantPlaceholder", locale)} /><button className="primary" disabled={!aiReady || thinking || !draft.trim()} type="submit">{thinking ? t("loading", locale) : t("send", locale)}</button></form>
        </section>
      ) : null}
      <button className="assistant-orb" aria-expanded={open} aria-label={t("liveAssistant", locale)} onClick={() => setOpen((current) => {
        const next = !current;
        if (next) onOpen?.();
        return next;
      })} type="button">
        <span className={aiReady ? "assistant-status-dot online" : "assistant-status-dot"} />
        <strong>AI</strong>
        <small>{copy(locale, "助手", "Coach")}</small>
      </button>
    </div>
  );
}

function GuidedOverlay({ locale, onClose, onNext, stepIndex }) {
  const step = guideSteps[stepIndex];
  if (!step) return null;
  return (
    <div className="guided-overlay">
      <div className="guided-mask" />
      <div className={`guided-callout target-${step[0]}`}>
        <div className="guided-arrow" />
        <span>{stepIndex + 1} / {guideSteps.length}</span>
        <h3>{t(step[1], locale)}</h3>
        <p>{t(step[2], locale)}</p>
        <div className="guided-actions"><button className="secondary" onClick={onClose} type="button">{t("skipGuide", locale)}</button><button className="primary" onClick={onNext} type="button">{stepIndex === guideSteps.length - 1 ? t("finishGuide", locale) : t("next", locale)}</button></div>
      </div>
    </div>
  );
}

function StartupScreen({ locale, slow, stageKey }) {
  return (
    <main className="startup-screen" aria-live="polite">
      <section className="startup-card">
        <div className="startup-mark" aria-hidden="true">
          <span>CL</span>
          <i />
        </div>
        <div className="startup-copy">
          <p>{t("startupKicker", locale)}</p>
          <h1>Commodity Lab</h1>
          <span>{slow ? t("startupSlow", locale) : t(stageKey, locale)}</span>
        </div>
        <div className="startup-progress">
          <div />
        </div>
        <ol className="startup-steps">
          {startupStageKeys.map((key) => (
            <li className={key === stageKey ? "active" : ""} key={key}>
              <i />
              <span>{t(key, locale)}</span>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}

export default function App() {
  const initialLocale = normalizeLocale(savedValue("commodity-lab-locale", "zh"));
  const savedProductScope = savedValue("commodity-lab-product-scope", "natural_gas");
  const initialProductScope = productWorkspace(savedProductScope).enabled ? savedProductScope : "natural_gas";
  const [locale, setLocaleState] = useState(initialLocale);
  const [productScope, setProductScopeState] = useState(initialProductScope);
  const [theme, setThemeState] = useState(() => normalizeThemeMode(savedValue("commodity-lab-theme", "system")));
  const [resolvedTheme, setResolvedTheme] = useState(() => getSystemThemePreference());
  const [backendReady, setBackendReady] = useState(false);
  const [startupStage, setStartupStage] = useState(startupStageKeys[0]);
  const [startupSlow, setStartupSlow] = useState(false);
  const [providerStatus, setProviderStatus] = useState(null);
  const [marketCapabilities, setMarketCapabilities] = useState(() => fallbackMarketCapabilities(initialLocale));
  const [templates, setTemplates] = useState(fallbackTemplates);
  const [activeTemplateId, setActiveTemplateId] = useState(fallbackTemplates.templates[0].id);
  const [activePage, setActivePage] = useState(pageIds.home);
  const [caseData, setCaseData] = useState(() => emptyCase(initialProductScope));
  const [generationStages, setGenerationStages] = useState([]);
  const [generationStream, setGenerationStream] = useState(null);
  const [loadingTemplate, setLoadingTemplate] = useState("");
  const [fieldSelection, setFieldSelection] = useState(["close"]);
  const [strategyLegs, setStrategyLegs] = useState(() => defaultLegs(initialLocale));
  const [rationale, setRationale] = useState("");
  const [evaluation, setEvaluation] = useState(null);
  const [replayDecision, setReplayDecision] = useState(null);
  const [replayHistory, setReplayHistory] = useState([]);
  const [advisorFeedback, setAdvisorFeedback] = useState("");
  const [exam, setExam] = useState("");
  const [aiOutput, setAiOutput] = useState(null);
  const [busyAction, setBusyAction] = useState("");
  const [serviceMessage, setServiceMessage] = useState("");
  const [updateInfo, setUpdateInfo] = useState({ current_version: currentVersion });
  const [assistantMessages, setAssistantMessages] = useState([]);
  const [assistantStage, setAssistantStage] = useState("");
  const [learningRecords, setLearningRecords] = useState(() => loadLearningRecords());
  const [aiGuidanceAction, setAiGuidanceAction] = useState("");
  const [aiInterventions, setAiInterventions] = useState([]);
  const [aiLessonPlan, setAiLessonPlan] = useState(() => loadAiLessonPlan());
  const [guideIndex, setGuideIndex] = useState(() => savedValue("commodity-lab-guide-complete", "") ? -1 : 0);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => savedValue("commodity-lab-sidebar-collapsed", "") === "1");
  const generationRequestRef = useRef(0);
  const assistantRequestRef = useRef(0);
  const replayCoachRequestRef = useRef(0);
  const aiReady = Boolean(providerStatus?.haineng?.ok);
  const scopedLearningRecords = useMemo(() => learningRecords.filter((record) => {
    const recordScope = record.product_scope ?? productScopeForTemplate(record.template_id);
    return recordScope === "general" || recordScope === productScope;
  }), [learningRecords, productScope]);
  const learningProgress = useMemo(() => summarizeLearningRecords(scopedLearningRecords), [scopedLearningRecords]);

  function setLocale(nextLocale) {
    localStorage.setItem("commodity-lab-locale", nextLocale);
    setLocaleState(nextLocale);
  }
  function setTheme(nextTheme) {
    const normalized = normalizeThemeMode(nextTheme);
    localStorage.setItem("commodity-lab-theme", normalized);
    setThemeState(normalized);
  }
  function completeGuide() {
    localStorage.setItem("commodity-lab-guide-complete", "1");
    setGuideIndex(-1);
  }
  function appendLearningRecord(record) {
    setLearningRecords((current) => {
      const next = [...current, record].slice(-120);
      saveLearningRecords(next);
      return next;
    });
  }
  function updateLearningRecord(recordId, patch) {
    if (!recordId) return;
    setLearningRecords((current) => {
      const next = current.map((record) => record.id === recordId ? { ...record, ...patch } : record);
      saveLearningRecords(next);
      return next;
    });
  }
  function toggleSidebarCollapsed() {
    setSidebarCollapsed((current) => {
      const next = !current;
      localStorage.setItem("commodity-lab-sidebar-collapsed", next ? "1" : "0");
      return next;
    });
  }
  function showAiGuidance(message) {
    setAiGuidanceAction(message);
    window.clearTimeout(showAiGuidance.timer);
    showAiGuidance.timer = window.setTimeout(() => setAiGuidanceAction(""), 3600);
  }

  function recordAiIntervention(label, page = pageIds.workbench, kind = "software_action") {
    const item = { id: `${Date.now()}-${Math.random().toString(16).slice(2)}`, kind, label, page };
    setAiInterventions((current) => [item, ...current].slice(0, 5));
    return item;
  }
  function switchProductScope(nextScope) {
    const workspace = productWorkspace(nextScope);
    if (!workspace.enabled || nextScope === productScope) return;
    generationRequestRef.current += 1;
    assistantRequestRef.current += 1;
    replayCoachRequestRef.current += 1;
    localStorage.setItem("commodity-lab-product-scope", nextScope);
    setProductScopeState(nextScope);
    const availableTemplates = templatesForProduct(templates.templates ?? fallbackTemplates.templates, nextScope);
    const nextTemplate = availableTemplates.find((item) => item.group === "foundation") ?? availableTemplates[0];
    if (nextTemplate) setActiveTemplateId(nextTemplate.id);
    setCaseData(emptyCase(nextScope));
    setStrategyLegs(defaultLegs(locale));
    setEvaluation(null);
    setReplayDecision(null);
    setReplayHistory([]);
    setAdvisorFeedback("");
    setExam("");
    setAiOutput(null);
    setAssistantMessages([]);
    setAssistantStage("");
    setAiInterventions([]);
    setAiGuidanceAction("");
    setGenerationStages([]);
    setGenerationStream(null);
    setLoadingTemplate("");
    setBusyAction((current) => ["case_generation", "assistant"].includes(current) ? "" : current);
    setActivePage(pageIds.home);
  }

  useEffect(() => {
    if (aiInterventions.length && guideIndex >= 0) completeGuide();
  }, [aiInterventions.length, guideIndex]);

  useEffect(() => {
    const shortcutPages = [
      pageIds.home,
      pageIds.caseLab,
      pageIds.workbench,
      pageIds.library,
      pageIds.review,
      pageIds.knowledge,
      pageIds.progress,
      pageIds.coach,
      pageIds.settings
    ];
    function handleNavigationShortcut(event) {
      if (!event.ctrlKey || !event.altKey) return;
      const index = Number(event.key) - 1;
      if (!Number.isInteger(index) || !shortcutPages[index]) return;
      event.preventDefault();
      setActivePage(shortcutPages[index]);
    }
    window.addEventListener("keydown", handleNavigationShortcut);
    return () => window.removeEventListener("keydown", handleNavigationShortcut);
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.dataset.themeMode = theme;
  }, [locale, resolvedTheme, theme]);

  useEffect(() => {
    if (theme !== "system") {
      setResolvedTheme(theme);
      return undefined;
    }
    const media = window.matchMedia?.("(prefers-color-scheme: dark)");
    const updateResolvedTheme = () => setResolvedTheme(media?.matches ? "dark" : "light");
    updateResolvedTheme();
    media?.addEventListener?.("change", updateResolvedTheme);
    return () => media?.removeEventListener?.("change", updateResolvedTheme);
  }, [theme]);

  useEffect(() => {
    let cancelled = false;
    let timer;
    let attempts = 0;

    async function pollBackend() {
      if (cancelled) return;

      const stageIndex = Math.min(startupStageKeys.length - 1, Math.floor(attempts / 6));
      setStartupStage(startupStageKeys[stageIndex]);

      try {
        await backendRequest("GET", "/api/health");
        if (!cancelled) {
          setBackendReady(true);
        }
      } catch (error) {
        attempts += 1;
        if (attempts >= 48) {
          setStartupSlow(true);
          setServiceMessage(formatErrorMessage(error, initialLocale));
          setBackendReady(true);
          return;
        }
        timer = window.setTimeout(pollBackend, 350);
      }
    }

    pollBackend();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [initialLocale]);

  useEffect(() => {
    if (!backendReady) return;
    backendRequest("GET", "/api/v1/provider-status")
      .then((payload) => {
        setProviderStatus(payload);
        setServiceMessage((current) => (/failed to fetch/i.test(current) ? "" : current));
      })
      .catch((error) => {
        setProviderStatus({ haineng: { ok: false, configured: false }, ai_providers: defaultProviderCatalog });
        setServiceMessage(formatErrorMessage(error, locale));
      });
  }, [backendReady, locale]);

  useEffect(() => {
    if (!backendReady) return;
    backendRequest("GET", `/api/v1/business-templates?locale=${locale}`)
      .then((payload) => {
        setTemplates(payload);
        setActiveTemplateId((current) => current || payload.templates?.[0]?.id || "");
      })
      .catch(() => setTemplates(fallbackTemplates));
  }, [backendReady, locale]);

  useEffect(() => {
    const available = templatesForProduct(templates.templates ?? fallbackTemplates.templates, productScope);
    if (available.length && !available.some((item) => item.id === activeTemplateId)) {
      setActiveTemplateId(available[0].id);
    }
  }, [activeTemplateId, productScope, templates]);

  useEffect(() => {
    if (!backendReady) return;
    backendRequest("GET", `/api/v1/market/capabilities?locale=${locale}`)
      .then(setMarketCapabilities)
      .catch(() => setMarketCapabilities(fallbackMarketCapabilities(locale)));
  }, [backendReady, locale]);

  useEffect(() => {
    if (!backendReady) return;
    backendRequest("GET", "/api/v1/version").then(setUpdateInfo).catch(() => {});
  }, [backendReady]);

  async function saveProviderSettings(form) {
    setBusyAction("provider");
    setServiceMessage("");
    try {
      const fixedForm = formForProvider(form.provider, providerCatalog(providerStatus), form.api_key);
      const payload = await backendRequest("POST", "/api/v1/provider-settings", fixedForm);
      localStorage.setItem("commodity-lab-ai-provider", fixedForm.provider);
      setProviderStatus((current) => ({ ...(current ?? {}), ...payload }));
      setServiceMessage(t("providerSaved", locale));
    } catch (error) {
      setServiceMessage(formatErrorMessage(error, locale));
    } finally {
      setBusyAction("");
    }
  }

  async function importLocalProviderSettings(form, sourceName = "") {
    setBusyAction("provider-import");
    setServiceMessage("");
    try {
      const fixedForm = formForProvider(form.provider, providerCatalog(providerStatus), form.api_key);
      const payload = await backendRequest("POST", "/api/v1/provider-settings", fixedForm);
      const status = payload.haineng ?? {};
      if (status.provider) localStorage.setItem("commodity-lab-ai-provider", status.provider);
      setProviderStatus((current) => ({ ...(current ?? {}), ...payload }));
      setServiceMessage(`${t("localAiKeyLoaded", locale)}${sourceName ? `: ${sourceName}` : ""}`);
    } catch (error) {
      setServiceMessage(formatErrorMessage(error, locale));
    } finally {
      setBusyAction("");
    }
  }

  async function checkUpdate() {
    setUpdateInfo((current) => ({ ...current, message: t("checkingUpdates", locale) }));
    try {
      const payload = await backendRequest("GET", "/api/v1/update-check");
      setUpdateInfo({ ...payload, message: payload.up_to_date ? t("alreadyLatest", locale) : t("updateAvailable", locale) });
    } catch (error) {
      setUpdateInfo((current) => ({ ...current, message: formatErrorMessage(error, locale) }));
    }
  }

  async function generateTrainingCase(templateId, userRequest = "", marketOptions = {}) {
    const requestProductScope = productScope;
    const availableTemplates = templatesForProduct(templates.templates ?? fallbackTemplates.templates, requestProductScope);
    const selectedTemplate = availableTemplates.find((item) => item.id === templateId)
      ?? availableTemplates.find((item) => item.group !== "foundation")
      ?? availableTemplates[0];
    if (!selectedTemplate) {
      setServiceMessage(copy(locale, "当前产品没有可用课程。", "No course is available for the current product."));
      return;
    }
    const resolvedTemplateId = selectedTemplate.id;
    setActiveTemplateId(resolvedTemplateId);
    if (!aiReady) {
      setServiceMessage(t("aiRequiredForCase", locale));
      setActivePage(pageIds.settings);
      return;
    }
    const requestId = generationRequestRef.current + 1;
    generationRequestRef.current = requestId;
    const localTemplateCase = defaultCaseForTemplate(resolvedTemplateId, locale);
    const provisionalCase = provisionalCaseForTemplate(resolvedTemplateId, locale);
    const provisionalSession = provisionalTrainingSession({
      marketMode: marketOptions.market_mode ?? "ai_simulated",
      marketRegime: marketOptions.market_regime ?? "contango",
      productScope: requestProductScope,
      replayId: marketOptions.replay_id ?? null,
      templateId: resolvedTemplateId,
      userRequest
    });
    setLoadingTemplate(resolvedTemplateId);
    setBusyAction("case_generation");
    setActivePage(pageIds.workbench);
    setCaseData({ ...provisionalCase, training_session: provisionalSession });
    setStrategyLegs(defaultLegs(locale));
    setReplayDecision(null);
    setReplayHistory([]);
    setEvaluation(null);
    setAdvisorFeedback("");
    setExam("");
    setAiOutput(null);
    setServiceMessage("");
    setGenerationStages([{ id: "read_template", label: generationStageLabel("read_template", locale) }]);
    setGenerationStream({ active: true, received: 0, title: "", summary: "", business_type: "" });
    try {
      const curriculum = trainingCurriculumReference(selectedTemplate, locale, requestProductScope);
      let streamedCase = null;
      let modelBuffer = "";
      await backendStreamRequest("/api/v1/ai/training-case/stream", {
        template_id: resolvedTemplateId,
        product_scope: requestProductScope,
        locale,
        user_request: userRequest,
        market_mode: marketOptions.market_mode ?? "ai_simulated",
        market_regime: marketOptions.market_regime ?? "contango",
        replay_id: marketOptions.replay_id ?? null,
        ...curriculum
      }, (event, data) => {
        if (generationRequestRef.current !== requestId) return;
        if (event === "stage") {
          const stage = {
            id: data.id,
            label: generationStageLabel(data.id, locale, data.label)
          };
          setGenerationStages((current) => current.some((item) => item.id === stage.id) ? current : [...current, stage]);
          return;
        }
        if (event === "market") {
          setCaseData((current) => applyStreamedMarketContext(current, data, locale));
          return;
        }
        if (event === "session") {
          setCaseData((current) => ({ ...current, training_session: data }));
          return;
        }
        if (event === "model_delta") {
          modelBuffer += data.delta ?? "";
          const preview = streamedCasePreview(modelBuffer);
          setGenerationStream({
            active: true,
            received: data.received ?? modelBuffer.length,
            ...preview
          });
          if (preview.title || preview.summary || preview.business_type) {
            setCaseData((current) => ({
              ...current,
              scenario: {
                ...current.scenario,
                ...(preview.title ? { title: preview.title } : {}),
                ...(preview.summary ? { summary: preview.summary } : {}),
                ...(preview.business_type ? { business_type: preview.business_type } : {})
              }
            }));
          }
          return;
        }
        if (event === "case") {
          streamedCase = data.case ?? localTemplateCase;
          setCaseData((current) => ({
            ...streamedCase,
            training_session: streamedCase.training_session ?? data.training_session ?? current.training_session
          }));
        }
      });
      if (generationRequestRef.current !== requestId) return;
      if (!streamedCase) throw new Error(copy(locale, "AI 未返回完整训练案例。", "AI did not return a complete training case."));
      setStrategyLegs(defaultLegs(locale));
      setRationale("");
    } catch (error) {
      if (generationRequestRef.current === requestId) {
        setCaseData({ ...localTemplateCase, training_session: provisionalSession });
        setServiceMessage(formatErrorMessage(error, locale));
      }
    } finally {
      if (generationRequestRef.current === requestId) {
        setGenerationStream((current) => current ? { ...current, active: false } : null);
        setBusyAction("");
        setLoadingTemplate("");
      }
    }
  }

  async function submitStrategy(options = {}) {
    const recordedInterventions = options?.aiAction ? [options.aiAction, ...aiInterventions] : aiInterventions;
    setBusyAction("evaluate");
    const replay = caseData.market?.replay;
    if (replay?.event?.id) {
      try {
        const result = await backendRequest("POST", `/api/v1/replays/${replay.event.id}/decision`, {
          checkpoint: replay.current_checkpoint?.index ?? 0,
          locale,
          strategy_legs: strategyLegs,
          rationale
        });
        const nextEvaluation = result.evaluation;
        setEvaluation(nextEvaluation);
        setReplayDecision(result);
        setReplayHistory((current) => [
          ...current.filter((item) => item.checkpoint?.index !== result.checkpoint?.index),
          result
        ].sort((a, b) => (a.checkpoint?.index ?? 0) - (b.checkpoint?.index ?? 0)));
        const learningRecord = recordLearningAttempt({ activeTemplateId, aiInterventions: recordedInterventions, caseData, evaluation: nextEvaluation, productScope, rationale, replayResult: result, strategyLegs });
        appendLearningRecord(learningRecord);
        setAiOutput(null);
        showAiGuidance(copy(locale, "本节点已即时评分，下一阶段市场现在可以揭示。", "This checkpoint was scored instantly; the next market phase can now be revealed."));
        setBusyAction("");
        if (aiReady) void requestReplayCoach(result, learningRecord.id);
      } catch (error) {
        setServiceMessage(formatErrorMessage(error, locale));
        setBusyAction("");
      } finally {
        if (!aiReady) setBusyAction("");
      }
      return;
    }
    const nextEvaluation = evaluateStrategy(caseData, strategyLegs, rationale);
    setEvaluation(nextEvaluation);
    appendLearningRecord(recordLearningAttempt({ activeTemplateId, aiInterventions: recordedInterventions, caseData, evaluation: nextEvaluation, productScope, rationale, strategyLegs }));
    setAiOutput(null);
    setBusyAction("");
    setActivePage(pageIds.review);
  }

  async function requestReplayCoach(result, learningRecordId = null) {
    const requestId = replayCoachRequestRef.current + 1;
    replayCoachRequestRef.current = requestId;
    let answer = "";
    setAdvisorFeedback("");
    setBusyAction("advisor_review");
    try {
      await backendStreamRequest("/api/v1/ai/advisor-review/stream", {
        ...buildAiPayload("advisor_review"),
        evaluation: result.evaluation,
        market_context: {
          case: caseData,
          strategy_legs: strategyLegs,
          replay_decision: result
        }
      }, (event, data) => {
        if (replayCoachRequestRef.current !== requestId) return;
        if (event === "model_delta") {
          answer += data.delta ?? "";
          setAdvisorFeedback(answer);
        }
        if (event === "review" && data.answer) {
          answer = data.answer;
          setAdvisorFeedback(answer);
        }
      });
      if (replayCoachRequestRef.current === requestId) {
        if (answer && learningRecordId) updateLearningRecord(learningRecordId, { advisor_feedback: answer, replay_result: result });
        showAiGuidance(copy(locale, "AI 已结合本节点评分给出下一步观察重点。", "AI reviewed this checkpoint and highlighted what to watch next."));
      }
    } catch (error) {
      if (replayCoachRequestRef.current === requestId) setServiceMessage(formatErrorMessage(error, locale));
    } finally {
      if (replayCoachRequestRef.current === requestId) setBusyAction("");
    }
  }

  async function advanceReplay() {
    if (!replayDecision) return;
    if (replayDecision.next_checkpoint == null) {
      setActivePage(pageIds.review);
      return;
    }
    const replay = caseData.market?.replay;
    if (!replay?.event?.id) return;
    replayCoachRequestRef.current += 1;
    setBusyAction("replay_advance");
    setServiceMessage("");
    try {
      const session = await backendRequest("POST", `/api/v1/replays/${replay.event.id}/session`, {
        checkpoint: replayDecision.next_checkpoint,
        locale
      });
      const nextReplay = replayBundleFromSession(session);
      setCaseData((current) => ({
        ...current,
        training_session: trainingSessionForReplayCheckpoint(current.training_session, session),
        scenario: {
          ...current.scenario,
          title: session.event.title,
          summary: session.event.summary,
          knowledge_points: session.event.skills,
          exposure: {
            ...(current.scenario?.exposure ?? {}),
            risk: session.current_checkpoint?.decision_required
          }
        },
        market: {
          ...session.market,
          replay: nextReplay,
          events: (session.visible_timeline ?? []).map((item) => ({ date: item.date, label: item.label }))
        },
        target_actions: [],
        rubric: session.decision_rubric ?? current.rubric,
        prompt: replayPrompt(session, locale)
      }));
      setStrategyLegs(defaultLegs(locale));
      setRationale("");
      setEvaluation(null);
      setReplayDecision(null);
      setAiOutput(null);
      setGenerationStages((current) => [...current, { id: `replay_${session.current_checkpoint?.index}`, label: copy(locale, "市场阶段已揭示", "Market phase revealed") }]);
      showAiGuidance(copy(locale, "新的市场信息已进入终端，请重新评估组合。", "New market information is now in the terminal. Reassess the hedge."));
    } catch (error) {
      setServiceMessage(formatErrorMessage(error, locale));
    } finally {
      setBusyAction("");
    }
  }

  function suggestTargetStrategy() {
    setStrategyLegs((caseData.target_actions ?? defaultLegs(locale)).map((leg, index) => ({ id: leg.id ?? `target-leg-${index}`, ...leg })));
    setAiOutput({
      title: copy(locale, "AI 建议策略腿", "AI Suggested Strategy Legs"),
      answer: copy(
        locale,
        "### AI 已根据本案例目标动作填充策略腿\n\n请逐条检查实货、基差、汇率、运力和期限是否匹配，不要机械提交。",
        "### AI filled the strategy legs from the target action set\n\nReview physical, basis, FX, capacity, and tenor alignment before submitting."
      )
    });
  }

  function checkStrategyBeforeSubmit() {
    const preview = evaluateStrategy(caseData, strategyLegs, rationale);
    const missing = preview.mistake_tags?.length ? preview.mistake_tags.join(", ") : copy(locale, "未发现明显缺口", "No obvious gap detected");
    setEvaluation(preview);
    setAiOutput({
      title: copy(locale, "提交前检查", "Pre-submit Check"),
      answer: copy(
        locale,
        `### 本地即时检查\n\n- 预估得分：**${preview.baseline_score}/100**\n- 主要缺口：${missing}\n- 下一步：确认每条腿覆盖的实货、纸货、汇率、运力或信用风险，再提交策略。`,
        `### Immediate local check\n\n- Estimated score: **${preview.baseline_score}/100**\n- Main gaps: ${missing}\n- Next: confirm which physical, paper, FX, capacity, or credit exposure each leg covers before submitting.`
      )
    });
  }

  function generateVariant() {
    const weakTags = evaluation?.mistake_tags?.slice(0, 3) ?? [];
    const prompt = copy(
      locale,
      `基于当前案例生成一个更贴近真实业务的后续练习，重点训练${weakTags.length ? weakTags.join("、") : "市场剧烈波动、基差错配、汇率和运力约束"}。保留当前市场证据模式。`,
      `Generate a realistic follow-up drill focused on ${weakTags.length ? weakTags.join(", ") : "sharp market moves, basis mismatch, FX, and capacity constraints"}. Keep the current market-evidence mode.`
    );
    generateTrainingCase(activeTemplateId, prompt, marketOptionsFromCase(caseData));
  }

  function generateReplayCounterfactual() {
    const replayTitle = caseData.market?.replay?.event?.title ?? caseData.scenario?.title;
    const weakTags = evaluation?.mistake_tags?.slice(0, 3) ?? [];
    const prompt = copy(
      locale,
      `基于“${replayTitle}”生成一个反事实决策练习。只改变一个关键条件（套保时点、基差、期权结构、实货数量或运力约束），明确说明变化，不泄露原事件后续结果。重点补强：${weakTags.length ? weakTags.join("、") : "组合规模、可选性和执行风控"}。生成后直接进入工作台。`,
      `Generate a counterfactual decision drill from "${replayTitle}". Change exactly one key condition: hedge timing, basis, option structure, physical volume, or logistics constraint. State the change clearly and do not leak the original event's later outcome. Focus on: ${weakTags.length ? weakTags.join(", ") : "portfolio sizing, optionality, and execution controls"}. Open the result directly in the workbench.`
    );
    generateTrainingCase(activeTemplateId, prompt, { market_mode: "ai_simulated", market_regime: caseData.market?.curve_metrics?.structure ?? "volatile" });
  }

  function buildAiPayload(capability) {
    const curriculum = curriculumReference(locale, productScope);
    return {
      capability,
      scenario_id: "europe_ttf_nbp_spread",
      locale,
      order: orderFromStrategy(strategyLegs),
      rationale,
      evaluation: evaluation ?? {},
      attempt_history: scopedLearningRecords.map((record) => record.evaluation).filter(Boolean).slice(-12),
      learning_progress: learningProgress,
      market_context: { case: caseData, strategy_legs: strategyLegs },
      curriculum_context: curriculum,
      user_request: rationale,
      concept: curriculum.knowledge_coverage.map((item) => item.title).join(", "),
      commercial_goal: `Build a practical multi-leg hedge playbook for this generated ${productWorkspace(productScope).en.toLowerCase()} business case.`
    };
  }

  async function runAiAction(capability) {
    if (!aiReady) {
      setServiceMessage(t("aiRequiredForCase", locale));
      setActivePage(pageIds.settings);
      return;
    }
    if (capability === "advisor_review" && !evaluation) return;
    setBusyAction(capability);
    setServiceMessage("");
    try {
      const path = capability === "exam" ? "/api/v1/exam/generate" : "/api/v1/ai/generate";
      const payload = await backendRequest("POST", path, capability === "exam" ? {
        scenario_id: "europe_ttf_nbp_spread",
        locale,
        attempt_history: scopedLearningRecords.map((record) => record.evaluation).filter(Boolean).slice(-12),
        curriculum_context: curriculumReference(locale, productScope)
      } : buildAiPayload(capability));
      if (capability === "advisor_review") {
        setAdvisorFeedback(payload.answer);
        setActivePage(pageIds.review);
        showAiGuidance(copy(locale, "AI 已切到复盘页并生成简短反馈。", "AI opened Review with concise feedback."));
      } else if (capability === "exam") {
        setExam(payload.exam);
        setEvaluation(null);
        setReplayDecision(null);
        setReplayHistory([]);
        setAdvisorFeedback("");
        setActivePage(pageIds.review);
        showAiGuidance(copy(locale, "AI 已生成测验并切到复盘页。", "AI generated a quiz and opened Review."));
      } else {
        setAiOutput({ title: t(capability, locale), answer: payload.answer });
        showAiGuidance(copy(locale, "AI 已把结果放入当前工作区。", "AI placed the result in the workspace."));
      }
    } catch (error) {
      setServiceMessage(formatErrorMessage(error, locale));
    } finally {
      setBusyAction("");
    }
  }

  async function sendAssistant(message) {
    const requestId = assistantRequestRef.current + 1;
    assistantRequestRef.current = requestId;
    const userMessage = { role: "user", content: message };
    const workspace = productWorkspace(productScope);
    if (!workspace.coursesReady) {
      setAssistantMessages((current) => [...current, userMessage, {
        role: "assistant",
        content: copy(locale, "该产品工作区的框架已经建立，但专属课程尚未开放。当前可训练欧洲天然气或原油。", "This product workspace is scaffolded, but its product-specific courses are not open yet. European Natural Gas and Crude Oil are currently trainable."),
        actions: []
      }]);
      return;
    }
    setAssistantMessages((current) => [...current, userMessage, { role: "assistant", content: "", actions: [], streaming: true }]);
    setBusyAction("assistant");
    setAssistantStage("read_workspace");
    try {
      const activeTrack = learningTracks.find((track) => track.templateId === activeTemplateId)
        ?? tracksForProduct(productScope)[0];
      const market = caseData.market ?? {};
      const compactCurves = (market.curves ?? []).slice(0, 3).map((curve) => ({
        id: curve.id,
        label: curve.label,
        points: Array.isArray(curve.points) && curve.points.length ? [curve.points.at(-1)] : []
      }));
      let modelBuffer = "";
      let payload = null;
      await backendStreamRequest("/api/v1/ai/live-assistant/stream", {
        locale,
        message,
        workspace_state: {
          active_page: activePage,
          active_template_id: activeTemplateId,
          product_scope: productScope,
          curriculum_context: activeTrack ? {
            track_id: activeTrack.id,
            track_title: labelFor(locale, activeTrack),
            learning_objective: copy(locale, activeTrack.detailZh, activeTrack.detailEn)
          } : {},
          case: {
            scenario: caseData.scenario,
            prompt: caseData.prompt,
            rubric: caseData.rubric,
            training_session: caseData.training_session,
            market: {
              benchmark: market.benchmark,
              unit: market.unit,
              as_of: market.as_of,
              curve_metrics: market.curve_metrics,
              forward_curve: (market.forward_curve ?? []).slice(0, 6),
              curves: compactCurves,
              replay: market.replay
            }
          },
          ai_lesson_plan: aiLessonPlan,
          evaluation,
          learning_progress: learningProgress,
          recent_attempts: scopedLearningRecords.slice(-3),
          replay_catalog: (marketCapabilities?.replays ?? [])
            .filter((item) => item.commodity === productScope)
            .slice(0, 8)
            .map((item) => ({
              id: item.id,
              commodity: item.commodity,
              title: item.title,
              summary: item.summary,
              checkpoint_count: item.checkpoint_count
            })),
          strategy_legs: strategyLegs,
          rationale
        }
      }, (event, data) => {
        if (assistantRequestRef.current !== requestId) return;
        if (event === "stage") {
          setAssistantStage(data.id ?? "read_workspace");
          return;
        }
        if (event === "model_delta") {
          modelBuffer += data.delta ?? "";
          setAssistantStage("stream_answer");
          const preview = partialJsonString(modelBuffer, "answer");
          if (preview) {
            setAssistantMessages((current) => current.map((item, index) => index === current.length - 1
              ? { ...item, content: preview, streaming: true }
              : item));
          }
          return;
        }
        if (event === "result") {
          payload = data;
          setAssistantMessages((current) => current.map((item, index) => index === current.length - 1
            ? { role: "assistant", content: data.answer ?? "", actions: data.actions ?? [], streaming: false }
            : item));
        }
      });
      if (assistantRequestRef.current !== requestId) return;
      if (!payload) throw new Error(copy(locale, "AI 未返回可用结果。", "AI returned no usable result."));
      const actions = payload.actions ?? [];
      const actionable = actions
        .filter((action) => assistantAutoActionTypes.includes(action.type))
        .sort((a, b) => assistantAutoActionTypes.indexOf(a.type) - assistantAutoActionTypes.indexOf(b.type));
      const localActions = actionable.filter((action) => assistantLocalActionTypes.includes(action.type));
      const generationActions = actionable.filter((action) => !assistantLocalActionTypes.includes(action.type));
      const actionsToApply = [...generationActions.slice(0, 1), ...localActions].slice(0, 8);
      setAssistantStage("apply_workspace_actions");
      for (const action of actionsToApply) {
        applyAssistantAction(action);
        await new Promise((resolve) => window.setTimeout(resolve, 220));
      }
    } catch (error) {
      if (assistantRequestRef.current === requestId) {
        setAssistantMessages((current) => current.map((item, index) => index === current.length - 1
          ? { role: "assistant", content: formatErrorMessage(error, locale), actions: [], streaming: false }
          : item));
      }
    } finally {
      if (assistantRequestRef.current === requestId) {
        setAssistantStage("");
        setBusyAction("");
      }
    }
  }

  function replayIdForAssistantAction(action, payload) {
    const available = (marketCapabilities?.replays ?? []).filter((item) => item.commodity === productScope);
    if (!available.length) return null;
    const requestText = [payload.user_request, action.label]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const titleMatch = available.find((item) => {
      const title = String(item.title ?? "").toLowerCase();
      return requestText.includes(item.id.toLowerCase()) || (title && requestText.includes(title));
    });
    if (titleMatch) return titleMatch.id;

    const requestedYears = new Set(requestText.match(/\b20\d{2}\b/g) ?? []);
    const yearMatches = available.filter((item) => {
      const eventText = `${item.id} ${item.title ?? ""}`;
      return [...requestedYears].some((year) => eventText.includes(year));
    });
    if (yearMatches.length === 1) return yearMatches[0].id;

    const explicit = String(payload.replay_id ?? "").trim().toLowerCase();
    const explicitMatch = available.find((item) => item.id.toLowerCase() === explicit);
    return explicitMatch?.id ?? null;
  }

  function applyAssistantAction(action) {
    const payload = action.payload ?? {};
    const requestedReplayId = replayIdForAssistantAction(action, payload);
    if (action.type === "select_template" && payload.template_id) {
      generateTrainingCase(payload.template_id, payload.user_request ?? "", {
        market_mode: requestedReplayId ? "historical_replay" : payload.market_mode,
        market_regime: payload.market_regime,
        replay_id: requestedReplayId ?? payload.replay_id
      });
      recordAiIntervention(action.label ?? copy(locale, "生成课程练习", "Generated a course drill"), pageIds.workbench, action.type);
      showAiGuidance(copy(locale, "AI 正在按课程生成练习。", "AI is generating a course drill."));
    }
    if (action.type === "generate_case") {
      const availableTracks = tracksForProduct(productScope);
      const track = availableTracks.find((item) => item.id === payload.track_id)
        ?? availableTracks.find((item) => item.id !== "foundation")
        ?? availableTracks[0];
      generateTrainingCase(payload.template_id ?? track.templateId, payload.user_request ?? copy(locale, track.requestZh, track.requestEn), {
        market_mode: requestedReplayId ? "historical_replay" : payload.market_mode,
        market_regime: payload.market_regime,
        replay_id: requestedReplayId ?? payload.replay_id
      });
      recordAiIntervention(action.label ?? copy(locale, "生成新训练题", "Generated a new drill"), pageIds.workbench, action.type);
      showAiGuidance(copy(locale, "AI 正在生成新练习并打开工作台。", "AI is generating a new drill and opening the workbench."));
    }
    if (action.type === "configure_market_session") {
      const currentOptions = marketOptionsFromCase(caseData);
      const nextMode = requestedReplayId
        ? "historical_replay"
        : ["ai_simulated", "historical_replay", "live"].includes(payload.market_mode)
        ? payload.market_mode
        : currentOptions.market_mode;
      generateTrainingCase(activeTemplateId, payload.user_request ?? caseData.training_session?.learning_objective ?? "", {
        market_mode: nextMode,
        market_regime: payload.market_regime ?? currentOptions.market_regime,
        replay_id: nextMode === "historical_replay" ? (requestedReplayId ?? payload.replay_id ?? currentOptions.replay_id) : null
      });
      recordAiIntervention(action.label ?? copy(locale, "切换市场证据并重建练习", "Changed market evidence and rebuilt the drill"), pageIds.workbench, action.type);
      showAiGuidance(copy(locale, "AI 正在切换市场模式，并用新证据重建当前练习。", "AI is changing the market mode and rebuilding the current drill with new evidence."));
    }
    if (action.type === "patch_case") {
      setCaseData((current) => mergeCasePatch(current, payload));
      if (Array.isArray(payload.target_actions)) setStrategyLegs(normalizeAssistantLegs(payload.target_actions));
      if (typeof payload.rationale === "string" && payload.rationale.trim()) setRationale(payload.rationale);
      if (Array.isArray(payload.chart_fields)) {
        const fields = payload.chart_fields.filter((field) => chartFields.includes(field));
        if (fields.length) setFieldSelection(fields);
      }
      setEvaluation(null);
      setAdvisorFeedback("");
      setAiOutput(null);
      setActivePage(pageIds.workbench);
      recordAiIntervention(action.label ?? copy(locale, "改写当前题目和参考动作", "Updated the current case and target actions"), pageIds.workbench, action.type);
      showAiGuidance(copy(locale, "AI 已直接改写当前题目、曲线或评分规则。", "AI directly updated the current case, curve, or rubric."));
    }
    if (action.type === "set_market_curves" && Array.isArray(payload.curves)) {
      setCaseData((current) => ({
        ...current,
        market: {
          ...(current.market ?? {}),
          unit: payload.unit ?? current.market?.unit,
          curves: payload.curves,
          events: Array.isArray(payload.events) ? payload.events : current.market?.events
        }
      }));
      setActivePage(pageIds.workbench);
      recordAiIntervention(action.label ?? copy(locale, "重绘市场曲线", "Redrew market curves"), pageIds.workbench, action.type);
      showAiGuidance(copy(locale, "AI 已根据你的要求重绘训练行情。", "AI redrew the training market for your request."));
    }
    if (action.type === "set_learning_goal" && payload.goal) {
      setAiOutput({ title: copy(locale, "AI 学习目标", "AI Learning Goal"), answer: `### ${payload.goal}\n\n${Array.isArray(payload.focus) ? payload.focus.map((item) => `- ${item}`).join("\n") : ""}` });
      setActivePage(pageIds.home);
      recordAiIntervention(action.label ?? copy(locale, "调整学习目标", "Updated learning goal"), pageIds.home, action.type);
      showAiGuidance(copy(locale, "AI 已更新当前学习目标。", "AI updated the current learning goal."));
    }
    if (action.type === "navigate_page" && (pageIds[payload.page] || Object.values(pageIds).includes(payload.page))) {
      const page = pageIds[payload.page] ?? payload.page;
      setActivePage(page);
      recordAiIntervention(action.label ?? copy(locale, "切换页面", "Navigated page"), page, action.type);
      showAiGuidance(copy(locale, "AI 已切换到对应页面。", "AI navigated to the requested page."));
    }
    if (action.type === "set_chart_fields" && Array.isArray(payload.fields)) {
      const fields = payload.fields.filter((field) => chartFields.includes(field));
      setFieldSelection(fields.length ? fields : ["close"]);
      setActivePage(pageIds.workbench);
      recordAiIntervention(copy(locale, "调整图表字段", "Adjusted chart fields"), pageIds.workbench, action.type);
      showAiGuidance(copy(locale, "AI 已切到工作台并调整图表字段。", "AI opened the workbench and adjusted chart fields."));
    }
    if (action.type === "set_strategy_legs" && Array.isArray(payload.legs)) {
      setStrategyLegs(normalizeAssistantLegs(payload.legs));
      setActivePage(pageIds.workbench);
      recordAiIntervention(action.label ?? copy(locale, "填入组合套保动作", "Filled hedge legs"), pageIds.workbench, action.type);
      showAiGuidance(copy(locale, "AI 已把建议策略腿填入工作台，请你检查后再提交。", "AI filled suggested legs in the workbench. Review before submitting."));
    }
    if (action.type === "fill_rationale" && payload.text) {
      setRationale(payload.text);
      setActivePage(pageIds.workbench);
      recordAiIntervention(action.label ?? copy(locale, "起草策略说明", "Drafted rationale"), pageIds.workbench, action.type);
      showAiGuidance(copy(locale, "AI 已填入策略说明草稿。", "AI filled a rationale draft."));
    }
    if (action.type === "set_exam" && payload.exam) {
      setExam(payload.exam);
      setEvaluation(null);
      setReplayDecision(null);
      setReplayHistory([]);
      setAdvisorFeedback("");
      setActivePage(pageIds.review);
      recordAiIntervention(action.label ?? copy(locale, "生成测验并打开复盘", "Generated quiz"), pageIds.review, action.type);
      showAiGuidance(copy(locale, "AI 已创建测验并打开复盘页。", "AI created a quiz and opened Review."));
    }
    if (action.type === "submit_strategy") {
      const intervention = recordAiIntervention(action.label ?? copy(locale, "提交策略并复盘", "Submitted strategy"), pageIds.review, action.type);
      submitStrategy({ aiAction: intervention });
      showAiGuidance(copy(locale, "AI 已提交当前策略并打开复盘页。", "AI submitted the current strategy and opened Review."));
    }
    if (action.type === "set_learning_plan") {
      const nextPlan = normalizeLearningPlan(payload, learningProgress, productScope);
      setAiLessonPlan(nextPlan);
      saveAiLessonPlan(nextPlan);
      setActivePage(pageIds.home);
      recordAiIntervention(action.label ?? copy(locale, "更新 AI 教学计划", "Updated AI teaching plan"), pageIds.home, action.type);
      showAiGuidance(copy(locale, "AI 已重新安排当前学习路线。", "AI updated the current learning route."));
    }
    if (action.type === "run_ai_capability" && payload.capability) runAiAction(payload.capability);
  }

  const activeTemplate = useMemo(() => templates.templates?.find((item) => item.id === activeTemplateId), [templates, activeTemplateId]);
  const settingsPanel = (
    <SettingsMenu
      aiReady={aiReady}
      importing={busyAction === "provider-import"}
      locale={locale}
      onCheckUpdate={checkUpdate}
      onImportLocalSettings={importLocalProviderSettings}
      onRestartGuide={() => setGuideIndex(0)}
      onSaveSettings={saveProviderSettings}
      providerStatus={providerStatus}
      saving={busyAction === "provider"}
      serviceMessage={busyAction === "provider" ? "" : serviceMessage}
      setLocale={setLocale}
      setTheme={setTheme}
      theme={theme}
      updateInfo={updateInfo}
    />
  );

  const advisorProps = {
    aiOutput,
    aiReady,
    advisorFeedback,
    busyAction,
    error: serviceMessage && busyAction !== "provider" ? serviceMessage : "",
    evaluation,
    exam,
    locale,
    runAiAction
  };

  const strategyProps = {
    busy: ["evaluate", "case_generation"].includes(busyAction),
    evaluation,
    locked: Boolean(replayDecision),
    locale,
    onSubmit: submitStrategy,
    rationale,
    setRationale,
    setStrategyLegs,
    strategyLegs
  };

  function selectTemplateForPractice(templateId) {
    setActiveTemplateId(templateId);
  }

  function reviewLearningRecord(record) {
    const snapshot = record?.case_snapshot;
    if (!snapshot) return;
    const templateId = record.template_id || activeTemplateId;
    const fallback = defaultCaseForTemplate(templateId, locale);
    setActiveTemplateId(templateId);
    setCaseData({
      ...fallback,
      ...snapshot,
      scenario: { ...fallback.scenario, ...(snapshot.scenario ?? {}) },
      market: { ...fallback.market, ...(snapshot.market ?? {}) },
      training_session: snapshot.training_session ?? record.training_session ?? fallback.training_session
    });
    setStrategyLegs(record.strategy_legs ?? []);
    setRationale(record.rationale ?? "");
    setEvaluation(record.evaluation ?? null);
    const replayRecords = record.session_id
      ? learningRecords.filter((item) => item.session_id === record.session_id && item.replay_result)
      : record.replay_result ? [record] : [];
    const restoredReplayHistory = replayRecords
      .map((item) => item.replay_result)
      .sort((a, b) => (a?.checkpoint?.index ?? 0) - (b?.checkpoint?.index ?? 0));
    setReplayDecision(restoredReplayHistory.at(-1) ?? null);
    setReplayHistory(restoredReplayHistory);
    setAdvisorFeedback(record.advisor_feedback ?? replayRecords.at(-1)?.advisor_feedback ?? "");
    setExam("");
    setAiOutput(null);
    setActivePage(pageIds.review);
    showAiGuidance(copy(locale, "已打开这次正式提交的真实复盘记录。", "Opened the actual scored-attempt record."));
  }

  function submitExamResult(result, structuredExam) {
    const evaluationResult = {
      valid: true,
      baseline_score: result.baseline_score,
      mistake_tags: [...new Set(result.mistake_tags ?? [])],
      skill_scores: result.skill_scores ?? {},
      metrics: { correct_count: result.correct_count, question_count: result.total }
    };
    const record = {
      ...recordLearningAttempt({
        activeTemplateId,
        aiInterventions,
        caseData,
        evaluation: evaluationResult,
        productScope,
        rationale: `Exam: ${structuredExam?.title ?? "Course Checkpoint"}`,
        strategyLegs: []
      }),
      assessment_type: "exam",
      exam_id: structuredExam?.id ?? null
    };
    appendLearningRecord(record);
    showAiGuidance(copy(locale, "测验已即时评分并计入真实学习进度。", "The quiz was scored instantly and added to your real learning progress."));
  }

  function generateWeakPointDrill() {
    const track = selectedTrackForProduct(null, learningProgress, productScope);
    const weakSkills = learningProgress.weakest
      .map((item) => labelFor(locale, item, "zh", "en"))
      .slice(0, 3);
    const reviewScenario = learningProgress.dueReviews ? learningProgress.nextReview?.scenarioId : null;
    const prompt = copy(
      locale,
      `根据我的真实提交记录生成下一道补强训练。重点弱项：${weakSkills.length ? weakSkills.join("、") : "敞口识别、工具选择和风险控制"}。${reviewScenario ? `优先复习场景 ${reviewScenario}。` : "保持当前课程先修顺序。"}生成后直接进入工作台，不要只给文字建议。`,
      `Generate the next remediation drill from my actual scored attempts. Focus on: ${weakSkills.length ? weakSkills.join(", ") : "exposure identification, instrument selection, and risk controls"}. ${reviewScenario ? `Prioritize spaced review for scenario ${reviewScenario}.` : "Keep the current curriculum prerequisites."} Open the generated case in the workbench instead of returning only advice.`
    );
    generateTrainingCase(track.templateId, prompt);
  }

  function requestAiLearningPath(topic) {
    if (!aiReady) {
      setServiceMessage(t("aiRequiredForCase", locale));
      setActivePage(pageIds.settings);
      return;
    }
    const topicLabel = labelFor(locale, topic, "titleZh", "titleEn");
    setActivePage(pageIds.home);
    showAiGuidance(copy(locale, "AI 正在根据真实学习记录重排课程路径。", "AI is rebuilding the learning path from actual records."));
    void sendAssistant(copy(
      locale,
      `根据我的真实训练记录，为${productWorkspace(productScope).zh}生成一条简洁学习路径，重点围绕“${topicLabel}”。请使用 set_learning_plan 直接更新课程首页，并保留统一课程的必修知识点。`,
      `Build a concise ${productWorkspace(productScope).en} learning path from my actual training records, focused on "${topicLabel}". Use set_learning_plan to update the home curriculum directly and preserve required core outcomes.`
    ));
  }

  function renderActivePage() {
    const workspace = productWorkspace(productScope);
    if (!workspace.coursesReady && activePage !== pageIds.settings) {
      return <ProductScaffoldPage locale={locale} workspace={workspace} />;
    }
    if (activePage === pageIds.caseLab) {
      return (
        <AiCaseLabPage
          activeTemplateId={activeTemplateId}
          aiReady={aiReady}
          businessTemplates={templates}
          locale={locale}
          loadingTemplate={loadingTemplate}
          onGenerate={generateTrainingCase}
          productScope={productScope}
          setActiveTemplateId={selectTemplateForPractice}
        />
      );
    }
    if (activePage === pageIds.workbench) {
      return (
        <WorkbenchPage
          activeTemplate={activeTemplate}
          advisorProps={advisorProps}
          aiInterventions={aiInterventions}
          caseData={caseData}
          fieldSelection={{ value: fieldSelection, set: setFieldSelection }}
          locale={locale}
          onAdvanceReplay={advanceReplay}
          onCheckStrategy={checkStrategyBeforeSubmit}
          onGenerateVariant={generateVariant}
          onPageChange={setActivePage}
          onSuggestTarget={suggestTargetStrategy}
          replayAdvancing={busyAction === "replay_advance"}
          replayDecision={replayDecision}
          strategyProps={strategyProps}
        />
      );
    }
    if (activePage === pageIds.review) {
      return <ReviewPage advisorFeedback={advisorFeedback} caseData={caseData} evaluation={evaluation} exam={exam} locale={locale} onGenerateCounterfactual={generateReplayCounterfactual} onGenerateVariant={generateVariant} onPageChange={setActivePage} onSubmitExam={submitExamResult} replayHistory={replayHistory} runAiAction={runAiAction} strategyLegs={strategyLegs} />;
    }
    if (activePage === pageIds.library) {
      return <ScenarioLibraryPage activeTemplateId={activeTemplateId} learningProgress={learningProgress} locale={locale} loadingTemplate={loadingTemplate} onGenerate={generateTrainingCase} onPageChange={setActivePage} onReview={reviewLearningRecord} productScope={productScope} />;
    }
    if (activePage === pageIds.knowledge) {
      return <KnowledgeMapPage locale={locale} onPageChange={setActivePage} onRequestLearningPath={requestAiLearningPath} productScope={productScope} runAiAction={runAiAction} />;
    }
    if (activePage === pageIds.progress) {
      return <ProgressPage learningProgress={learningProgress} locale={locale} onGenerateWeakPoint={generateWeakPointDrill} onPageChange={setActivePage} />;
    }
    if (activePage === pageIds.coach) {
      return <AiCoachPage aiReady={aiReady} applyAction={applyAssistantAction} locale={locale} messages={assistantMessages} onSend={sendAssistant} thinking={busyAction === "assistant"} />;
    }
    if (activePage === pageIds.settings) {
      return <SettingsPage locale={locale} settingsPanel={settingsPanel} />;
    }
    return <HomePage aiLessonPlan={aiLessonPlan} aiReady={aiReady} learningProgress={learningProgress} loadingTemplate={loadingTemplate} locale={locale} onGenerate={generateTrainingCase} onPageChange={setActivePage} productScope={productScope} />;
  }
  const shellClassName = [
    "app-shell",
    "cl-app-shell",
    aiReady ? "ai-ready" : "",
    busyAction === "case_generation" ? "ai-streaming" : "",
    sidebarCollapsed ? "sidebar-collapsed" : ""
  ].filter(Boolean).join(" ");

  return (
    <main className={shellClassName}>
      <ProductTopbar activePage={activePage} aiReady={aiReady} locale={locale} onProductScopeChange={switchProductScope} productScope={productScope} />

      <div className="cl-app-layout">
        <ProductSidebar activePage={activePage} collapsed={sidebarCollapsed} locale={locale} onPageChange={setActivePage} onToggleCollapsed={toggleSidebarCollapsed} />
        <section className="cl-content-shell">
          {generationStages.length && busyAction === "case_generation" ? <GenerationTimeline locale={locale} stages={generationStages} streamState={generationStream} /> : null}
          {aiGuidanceAction ? <p className="cl-ai-guidance"><Icon name="sparkles" />{aiGuidanceAction}</p> : null}
          <AiInterventionStrip interventions={aiInterventions} locale={locale} onNavigate={setActivePage} />
          {serviceMessage && activePage !== pageIds.settings ? <p className="cl-service-banner">{serviceMessage}</p> : null}
          {renderActivePage()}
        </section>
      </div>

      <FloatingAssistant activePage={activePage} aiReady={aiReady} applyAction={applyAssistantAction} assistantStage={assistantStage} interventions={aiInterventions} locale={locale} messages={assistantMessages} onOpen={completeGuide} onSend={sendAssistant} thinking={busyAction === "assistant"} />

      {guideIndex >= 0 ? (
        <GuidedOverlay
          locale={locale}
          onClose={completeGuide}
          onNext={() => (guideIndex >= guideSteps.length - 1 ? completeGuide() : setGuideIndex((current) => current + 1))}
          stepIndex={guideIndex}
        />
      ) : null}
    </main>
  );
}

function formatErrorMessage(error, locale) {
  const raw = typeof error === "string" ? error : error?.message ?? "";
  if (!raw) return t("serviceIssue", locale);
  const jsonStart = raw.indexOf("{");
  const parsed = jsonStart >= 0 ? parseSafeJson(raw.slice(jsonStart)) : null;
  const code = parsed?.detail?.code ?? parsed?.code;
  if (code === "ai_response_parse_failed") {
    return copy(
      locale,
      "AI 返回的结构化内容不完整，已保留当前训练题。请再试一次。",
      "AI returned incomplete structured content. The current drill was kept; please try again."
    );
  }
  if (parsed?.detail?.provider_message) return parsed.detail.provider_message;
  if (parsed?.provider_message) return parsed.provider_message;
  return raw.replace(/^backend status \d+:\s*/i, "");
}
