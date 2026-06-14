import React, { useEffect, useMemo, useRef, useState } from "react";
import { backendRequest } from "./api";
import { normalizeLocale, t } from "./i18n";

const currentVersion = "1.1.3";

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
  { id: pageIds.home, icon: "home", zh: "学习路径", en: "Learning Path" },
  { id: pageIds.caseLab, icon: "sparkles", zh: "生成练习", en: "Practice Generator" },
  { id: pageIds.workbench, icon: "workbench", zh: "训练工作台", en: "Training Workbench" },
  { id: pageIds.library, icon: "library", zh: "场景库", en: "Scenario Library" },
  { id: pageIds.knowledge, icon: "map", zh: "课程地图", en: "Course Map" },
  { id: pageIds.progress, icon: "progress", zh: "我的进度", en: "My Progress" }
];

const learningFlow = [
  { zh: "发现", en: "Discover", detailZh: "理解知识点与业务风险", detailEn: "Concepts and business risk" },
  { zh: "生成", en: "Generate", detailZh: "AI 构建案例与数据", detailEn: "AI case and data" },
  { zh: "练习", en: "Practice", detailZh: "组合实货与纸货动作", detailEn: "Build physical and paper legs" },
  { zh: "复盘", en: "Review", detailZh: "评分、错误和对照", detailEn: "Score and compare" },
  { zh: "强化", en: "Reinforce", detailZh: "按弱项生成变体", detailEn: "Drill weak points" }
];

const learningTracks = [
  {
    id: "foundation",
    templateId: "foundation_hedging_basics",
    zh: "套保入门",
    en: "Hedging Foundations",
    levelZh: "从这里开始",
    levelEn: "Start here",
    detailZh: "先理解敞口、套保目标、实货与纸货为什么要匹配。",
    detailEn: "Start with exposure, hedge objective, and why physical and paper legs must match.",
    requestZh: "生成一个入门级天然气套保训练案例：只关注敞口识别、实货/纸货匹配、买卖方向、数量和期限，不要直接使用复杂跨境 Beach Delivery。",
    requestEn: "Generate a beginner natural gas hedging drill focused only on exposure identification, physical-paper matching, side, quantity, and tenor. Keep the case at foundation level instead of using a complex cross-border Beach Delivery scenario.",
    lessons: ["敞口识别", "套保工具", "实货/纸货匹配"],
    lessonsEn: ["Exposure", "Hedge tools", "Physical-paper matching"]
  },
  {
    id: "procurement",
    templateId: "procurement_beach_to_germany",
    zh: "采购端业务",
    en: "Procurement Desk",
    levelZh: "进阶",
    levelEn: "Intermediate",
    detailZh: "覆盖 GSA、EEX/OCM 窗口、LNG 船货、双边 EFET 的采购套保。",
    detailEn: "GSA, EEX/OCM windows, LNG cargo procurement, and bilateral EFET hedging.",
    requestZh: "生成采购端天然气套保案例，先说明业务背景，再训练 GSA、EEX/OCM、LNG 或 EFET 中一个具体场景。",
    requestEn: "Generate a procurement-side gas hedging case. Explain the business context first, then train one specific GSA, EEX/OCM, LNG, or EFET scenario.",
    lessons: ["GSA 资源", "EEX/OCM 窗口", "LNG 船货", "EFET 采购"],
    lessonsEn: ["GSA supply", "EEX/OCM window", "LNG cargo", "EFET procurement"]
  },
  {
    id: "sales",
    templateId: "sales_efet_bilateral",
    zh: "销售端业务",
    en: "Sales Desk",
    levelZh: "进阶",
    levelEn: "Intermediate",
    detailZh: "学习 EFET 双边、窗口销售、LNG 气化销售和客户价格风险。",
    detailEn: "EFET bilateral sales, window sales, LNG regas sales, and customer price risk.",
    requestZh: "生成销售端天然气套保案例，围绕 EFET 双边、窗口销售或 LNG 气化销售，强调客户定价和履约风险。",
    requestEn: "Generate a sales-side gas hedging case around EFET bilateral sales, window sales, or LNG regas sales, emphasizing customer pricing and performance risk.",
    lessons: ["双边销售", "窗口销售", "气化销售", "客户风险"],
    lessonsEn: ["Bilateral sale", "Window sale", "Regas sale", "Customer risk"]
  },
  {
    id: "integrated",
    templateId: "integrated_gas_portfolio",
    zh: "组合套保设计",
    en: "Integrated Hedge Design",
    levelZh: "综合",
    levelEn: "Advanced",
    detailZh: "把基差、汇率、运力、信用和执行窗口合成可交易的多腿策略。",
    detailEn: "Combine basis, FX, capacity, credit, and execution windows into a tradeable multi-leg strategy.",
    requestZh: "生成综合天然气套保训练案例：必须包含实货腿、纸货腿、汇率或运力检查，并要求用户解释每条腿覆盖的风险。",
    requestEn: "Generate an integrated natural gas hedging drill with a physical leg, paper leg, FX or capacity check, and a requirement to explain the risk covered by each leg.",
    lessons: ["基差", "汇率", "运力", "风控复盘"],
    lessonsEn: ["Basis", "FX", "Capacity", "Risk review"]
  }
];

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
    summaryZh: "把 GSA、EFET、LNG、运力与 futures、swap、basis、FX、option 组合成同一个风险闭环。",
    summaryEn: "Connect GSA, EFET, LNG, and capacity with futures, swaps, basis, FX, and options as one risk loop.",
    conceptsZh: ["实货腿", "纸货腿", "名义量", "履约义务"],
    conceptsEn: ["Physical leg", "Paper leg", "Notional", "Performance obligation"],
    modelIds: ["gsa_procurement", "efet_bilateral_sale", "lng_regas_sale"]
  },
  {
    id: "outright_price",
    titleZh: "单边价格套保",
    titleEn: "Outright Price Hedge",
    summaryZh: "用期货、远期或掉期管理 TTF、NBP、THE、JKM 等基准价格的绝对涨跌。",
    summaryEn: "Use futures, forwards, or swaps to manage absolute moves in TTF, NBP, THE, JKM, or similar benchmarks.",
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
    conceptsZh: ["TTF/NBP", "地点基差", "跨期价差", "单位归一"],
    conceptsEn: ["TTF/NBP", "Location basis", "Calendar spread", "Unit normalization"],
    modelIds: ["cross_border_sale", "pipeline_capacity", "lng_regas_sale"]
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
  }
];

const scenarioLibraryItems = [
  {
    id: "procurement_beach_to_germany",
    commodity: "natural-gas",
    titleZh: "英国上游 Beach Delivery 卖德国",
    titleEn: "UK Beach Delivery sold into Germany",
    summaryZh: "上游 beach 交付资源销售至德国，处理 NBP/TTF 基差、EUR/GBP、运力和 EFET/GSA 匹配。",
    summaryEn: "UK beach gas sold into Germany with NBP/TTF basis, EUR/GBP, capacity, and EFET/GSA matching.",
    tags: ["GSA", "TTF/NBP", "FX", "Capacity"],
    difficultyZh: "中等",
    difficultyEn: "Intermediate",
    duration: "90",
    enabled: true
  },
  {
    id: "sales_lng_regas",
    commodity: "natural-gas",
    titleZh: "LNG 船货气化销售下跌行情",
    titleEn: "LNG regas sale during selloff",
    summaryZh: "船货、气化窗口和下游销售之间的价格、基差、期权性和履约风险套保。",
    summaryEn: "Hedge cargo, regas window, downstream sale, basis, optionality, and performance risk.",
    tags: ["LNG", "Regas", "TTF", "Optionality"],
    difficultyZh: "困难",
    difficultyEn: "Advanced",
    duration: "75",
    enabled: true
  },
  {
    id: "procurement_eex_ocm_window",
    commodity: "natural-gas",
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
    titleZh: "EFET 双边销售与违约风险",
    titleEn: "Bilateral EFET sale and credit risk",
    summaryZh: "双边合约销售、信用限额、基差、履约和保证金占用的组合套保案例。",
    summaryEn: "Bilateral sale, credit limits, basis, performance, and margin usage in one hedge case.",
    tags: ["EFET", "Credit", "Basis"],
    difficultyZh: "中等",
    difficultyEn: "Intermediate",
    duration: "55",
    enabled: true
  },
  {
    id: "crude_placeholder",
    commodity: "crude-oil",
    titleZh: "原油船货套利冲击",
    titleEn: "Crude cargo arbitrage shock",
    summaryZh: "后续版本开放。",
    summaryEn: "Coming in a later version.",
    tags: ["Constructing"],
    difficultyZh: "建设中",
    difficultyEn: "Constructing",
    duration: "--",
    enabled: false
  }
];

const knowledgeNodes = [
  { id: "hub", x: 50, y: 48, level: "intermediate", titleZh: "Hub Pricing", titleEn: "Hub Pricing", descZh: "TTF、NBP、THE、ZTP 等枢纽定价和交割逻辑。", descEn: "TTF, NBP, THE, ZTP hub pricing and delivery logic." },
  { id: "basis", x: 28, y: 38, level: "advanced", titleZh: "基差与价差", titleEn: "Basis & Spreads", descZh: "不同枢纽、时间和交割点之间的价差风险。", descEn: "Spread risk across hubs, tenors, and delivery points." },
  { id: "physical", x: 34, y: 24, level: "beginner", titleZh: "实货合同", titleEn: "Physical Contracts", descZh: "GSA、EFET、LNG 船货和气化销售的履约义务。", descEn: "GSA, EFET, LNG cargo, and regas sales obligations." },
  { id: "capacity", x: 24, y: 58, level: "intermediate", titleZh: "运力与路径", titleEn: "Capacity & Routing", descZh: "管输容量、跨境路径、拥堵和日内平衡风险。", descEn: "Pipeline capacity, cross-border routes, congestion, and balancing risk." },
  { id: "fx", x: 70, y: 44, level: "intermediate", titleZh: "汇率套保", titleEn: "FX Hedge", descZh: "EUR/GBP 和美元计价风险的前锋或掉期处理。", descEn: "Forwards or swaps for EUR/GBP and USD-denominated exposure." },
  { id: "lng", x: 68, y: 62, level: "beginner", titleZh: "LNG 与气化", titleEn: "LNG & Regas", descZh: "船期、气化窗口、JKM/TTF 转换和期权性。", descEn: "Cargo timing, regas windows, JKM/TTF conversion, and optionality." },
  { id: "risk", x: 48, y: 72, level: "advanced", titleZh: "风险管理", titleEn: "Risk Management", descZh: "信用、限额、流动性、保证金和执行窗口。", descEn: "Credit, limits, liquidity, margin, and execution windows." },
  { id: "exchange", x: 76, y: 30, level: "intermediate", titleZh: "EFET / OCM / EEX", titleEn: "EFET / OCM / EEX", descZh: "双边、窗口和交易所工具的适用边界。", descEn: "Where bilateral, window, and exchange instruments fit." },
  { id: "storage", x: 34, y: 72, level: "beginner", titleZh: "储气与季节性", titleEn: "Storage & Seasonality", descZh: "注采节奏、库存和季节曲线对套保的影响。", descEn: "Injection/withdrawal, inventory, and seasonal curve impacts." }
];

const learningRecordsKey = "commodity-lab-learning-records-v1";

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

const fallbackTemplates = {
  groups: [
    { id: "foundation", label: "套保基础" },
    { id: "procurement", label: "采购端" },
    { id: "sales", label: "销售端" },
    { id: "integrated", label: "组合策略" }
  ],
  knowledge_points: [
    { id: "exposure_objective", label: "敞口与套保目标", description: "判断多头、空头或价差敞口，再确定套保目的。" },
    { id: "physical_paper_matching", label: "实货与纸货匹配", description: "GSA、EFET、LNG、swap、future、basis、FX、option、capacity 的组合动作。" },
    { id: "outright_price", label: "单边价格套保", description: "使用期货、远期或掉期管理绝对价格风险。" },
    { id: "basis_spread", label: "基差、枢纽与跨期价差", description: "TTF/NBP、地点差、跨期、单位与汇率归一化。" },
    { id: "options_optionality", label: "期权与运营可选性", description: "cap、floor、collar、LNG 转港和气化窗口等非线性风险。" },
    { id: "capacity_storage_balancing", label: "运力、储气与平衡", description: "管输 capacity、提名、库存、偏差和路径约束。" },
    { id: "risk_controls", label: "执行与风控", description: "流动性、信用、限额、保证金、结算和移仓风险。" }
  ],
  templates: [
    {
      id: "foundation_hedging_basics",
      group: "foundation",
      business_type: "天然气套保基础",
      title: "套保对象与风险敞口识别",
      summary: "入门案例：识别业务敞口，并匹配实货、纸货、方向、数量和期限。",
      coverage: ["exposure_objective", "physical_paper_matching", "outright_price"],
      gas_models: ["simple_procurement", "customer_indexed_sale"],
      knowledge_points: ["exposure_objective", "outright_price", "physical_paper_matching"],
      required_curves: ["TTF", "TRAINING_HEDGE_INDEX"],
      suggested_leg_types: ["physical", "swap"]
    },
    {
      id: "procurement_beach_to_germany",
      group: "procurement",
      business_type: "上游 Beach Delivery 资源（GSA）",
      title: "英国上游 Beach Delivery 卖德国",
      summary: "AI 生成 NBP/TTF、汇率、运输和实纸货匹配案例。",
      coverage: ["basis_spread", "fx", "capacity_storage_balancing", "physical_paper_matching", "risk_controls"],
      gas_models: ["gsa_procurement", "pipeline_capacity"],
      knowledge_points: ["basis_spread", "fx", "capacity_storage_balancing", "physical_paper_matching"],
      required_curves: ["TTF", "NBP", "EURGBP", "TTF_NBP_SPREAD"],
      suggested_leg_types: ["physical", "basis", "fx", "capacity"]
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
      unit: "training index",
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

function defaultLegs(locale = "zh") {
  return defaultCase(locale).target_actions.map((leg) => ({ ...leg }));
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
  const text = `${rationale} ${legs.map((leg) => `${leg.leg_type} ${leg.market} ${leg.side}`).join(" ")}`.toLowerCase();
  const hasPhysical = legs.some((leg) => ["physical", "gsa", "lng", "efet"].includes(leg.leg_type));
  const hasPaper = legs.some((leg) => ["swap", "future", "basis", "paper", "option"].includes(leg.leg_type));
  const targetTypes = new Set((caseData.target_actions ?? []).map((leg) => leg.leg_type));
  const matchedTypes = legs.filter((leg) => targetTypes.has(leg.leg_type)).length;
  const maxScore = rubric.reduce((sum, item) => sum + Number(item.points || 0), 0) || 100;
  let score = 0;
  if (hasPhysical) score += 25;
  if (hasPaper) score += 30;
  score += Math.min(25, matchedTypes * 8);
  if (/(basis|基差|spread|价差|fx|汇率|capacity|运力|option|cap|floor|collar|期权|limit|限额|liquidity|流动性)/i.test(text)) score += 20;
  const baseline = Math.max(0, Math.min(100, Math.round((score / Math.max(100, maxScore)) * 100)));
  return {
    valid: true,
    baseline_score: baseline,
    rubric,
    target_actions: caseData.target_actions ?? [],
    strategy_legs: legs,
    mistake_tags: [
      ...(!hasPhysical ? ["missing_physical_leg"] : []),
      ...(!hasPaper ? ["missing_paper_leg"] : []),
      ...(matchedTypes < Math.min(2, targetTypes.size) ? ["incomplete_target_legs"] : [])
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

function recordLearningAttempt({ activeTemplateId, caseData, evaluation, rationale, strategyLegs }) {
  return {
    id: `attempt-${Date.now()}`,
    created_at: new Date().toISOString(),
    template_id: activeTemplateId,
    scenario_id: caseData?.scenario?.id ?? activeTemplateId,
    scenario_title: caseData?.scenario?.title ?? "",
    evaluation,
    rationale,
    strategy_legs: strategyLegs
  };
}

function recordText(record) {
  return `${record?.rationale ?? ""} ${(record?.strategy_legs ?? []).map((leg) => `${leg.leg_type} ${leg.market} ${leg.side} ${leg.hedge_type}`).join(" ")}`.toLowerCase();
}

function scoreDimension(record, dimensionId) {
  const evaluation = record?.evaluation ?? {};
  const baseline = clampScore(evaluation.baseline_score);
  if (baseline == null) return null;
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
    const ids = [record.template_id, record.scenario_id].filter(Boolean);
    ids.forEach((id) => {
      const current = stats[id] ?? { attempts: 0, scores: [] };
      current.attempts += 1;
      current.scores.push(Number(record.evaluation.baseline_score));
      stats[id] = current;
    });
    return stats;
  }, {});
  Object.keys(scenarioStats).forEach((key) => {
    scenarioStats[key] = {
      attempts: scenarioStats[key].attempts,
      score: averageScore(scenarioStats[key].scores)
    };
  });
  const weakest = dimensions.filter((dimension) => dimension.score != null).sort((a, b) => a.score - b.score).slice(0, 3);
  return {
    hasRecords: valid.length > 0,
    attempts: valid.length,
    latest,
    latestScore: clampScore(latest?.evaluation?.baseline_score),
    averageScore: averageScore(valid.map((record) => record.evaluation.baseline_score)),
    dimensions,
    scenarioStats,
    weakest
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
    library: <path d="M4 19V5a2 2 0 0 1 2-2h12v18H6a2 2 0 0 1-2-2ZM8 7h7M8 11h7" />,
    map: <path d="M9 18l-6 3V6l6-3 6 3 6-3v15l-6 3-6-3ZM9 3v15M15 6v15" />,
    play: <path d="M8 5v14l11-7Z" />,
    plus: <path d="M12 5v14M5 12h14" />,
    progress: <path d="M4 19h16M7 16V9M12 16V5M17 16v-4" />,
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

function GenerationTimeline({ locale, stages }) {
  return (
    <div className="ai-generation-timeline">
      {(stages.length ? stages : [{ id: "ready", label: t("aiCaseReady", locale) }]).map((stage, index) => (
        <span className={index === stages.length - 1 && stages.length ? "active" : ""} key={`${stage.id}-${index}`}>
          <i />
          {stage.label}
        </span>
      ))}
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
        <strong>{t("aiGeneratedData", locale)}</strong>
      </div>
      <div className="chart-toolbar">
        <div className="segmented compact">
          {chartFields.map((field) => (
            <button className={fieldSelection.includes(field) ? "active" : ""} key={field} onClick={() => toggleField(field)} type="button">{t(field, locale)}</button>
          ))}
        </div>
        <span>{market.unit ?? "--"}</span>
      </div>
      <div className="price-chart-wrap" onMouseLeave={() => setHoverIndex(null)} onMouseMove={onMove}>
        <svg className="price-chart terminal-chart" role="img" aria-label={t("priceChart", locale)} viewBox={`0 0 ${width} ${height}`}>
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
            const y = pad.top + 18 + (index % Math.max(1, curves.length)) * laneHeight;
            return <g className="trade-marker" key={leg.id ?? index}><circle cx={x} cy={y} r="5" /><text x={x + 8} y={y + 4}>{leg.leg_type}:{leg.side}</text></g>;
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

function StrategyBuilder({ busy, locale, onSubmit, rationale, setRationale, setStrategyLegs, strategyLegs }) {
  function updateLeg(index, patch) {
    setStrategyLegs((current) => current.map((leg, itemIndex) => itemIndex === index ? { ...leg, ...patch } : leg));
  }
  function addLeg() {
    setStrategyLegs((current) => [...current, { id: `leg-${Date.now()}`, leg_type: "swap", market: "TTF", side: "sell", quantity: 0, price: 0, tenor: "M+1", hedge_type: "short_hedge" }]);
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
            <label>{t("legType", locale)}<select value={leg.leg_type} onChange={(event) => updateLeg(index, { leg_type: event.target.value })}><option value="physical">{t("physicalLeg", locale)}</option><option value="swap">Swap</option><option value="future">Future</option><option value="basis">{t("basisLeg", locale)}</option><option value="fx">FX</option><option value="capacity">{t("capacityLeg", locale)}</option><option value="option">{copy(locale, "期权", "Option")}</option></select></label>
            <label>{t("market", locale)}<input value={leg.market} onChange={(event) => updateLeg(index, { market: event.target.value })} /></label>
            <label>{t("side", locale)}<select value={leg.side} onChange={(event) => updateLeg(index, { side: event.target.value })}><option value="sell">{t("sell", locale)}</option><option value="buy">{t("buy", locale)}</option><option value="pay">Pay</option><option value="receive">Receive</option></select></label>
            <label>{t("quantity", locale)}<input min="0" type="number" value={leg.quantity} onChange={(event) => updateLeg(index, { quantity: Number(event.target.value) })} /></label>
            <label>{t("tenor", locale)}<input value={leg.tenor} onChange={(event) => updateLeg(index, { tenor: event.target.value })} /></label>
            <button className="icon-button danger" disabled={strategyLegs.length <= 1} onClick={() => removeLeg(index)} type="button">×</button>
          </div>
        ))}
      </div>
      <button className="secondary" onClick={addLeg} type="button">{t("addLeg", locale)}</button>
      <label>{t("rationale", locale)}<textarea value={rationale} onChange={(event) => setRationale(event.target.value)} /></label>
      <button className="primary" disabled={busy} onClick={onSubmit} type="button">{busy ? t("loading", locale) : t("submitOrder", locale)}</button>
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
      {evaluation?.mistake_tags?.length ? <p className="service-error">{evaluation.mistake_tags.join(", ")}</p> : null}
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

function AiThinkingPanel({ locale, titleKey = "aiThinkingTitle" }) {
  return (
    <section className="thinking-panel active" aria-live="polite">
      <div className="panel-title compact-title"><span>{t(titleKey, locale)}</span><strong>{t("working", locale)}</strong></div>
      <ol className="thinking-steps">
        {["thinkingReadContext", "thinkingMatchKnowledge", "thinkingGenerateActions", "thinkingAssemble"].map((key) => <li className="active" key={key}><i /><span>{t(key, locale)}</span></li>)}
      </ol>
    </section>
  );
}

function AdvisorRail({ aiOutput, aiReady, advisorFeedback, busyAction, error, evaluation, exam, locale, runAiAction }) {
  const hasAdvisorOutput = Boolean(error || advisorFeedback || exam || aiOutput?.answer);
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
            {exam ? <section className="response-block"><h3>{t("examQuestions", locale)}</h3><MarkdownText text={exam} /></section> : null}
            {aiOutput?.answer ? <section className="response-block"><h3>{aiOutput.title}</h3><MarkdownText text={aiOutput.answer} /></section> : null}
          </div>
        </details>
      </div>
    </aside>
  );
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

function curriculumReference(locale) {
  return {
    knowledge_coverage: hedgingKnowledgeCoverage.map((item) => ({
      id: item.id,
      title: labelFor(locale, item, "titleZh", "titleEn"),
      summary: copy(locale, item.summaryZh, item.summaryEn),
      concepts: copy(locale, item.conceptsZh, item.conceptsEn)
    })),
    gas_trading_models: gasTradingModels.map((item) => ({
      id: item.id,
      group: item.group,
      title: labelFor(locale, item, "titleZh", "titleEn"),
      summary: copy(locale, item.summaryZh, item.summaryEn),
      risks: copy(locale, item.risksZh, item.risksEn),
      instruments: copy(locale, item.instrumentsZh, item.instrumentsEn)
    }))
  };
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

function LogoMark() {
  return (
    <span className="cl-logo-mark" aria-hidden="true">
      <Icon name="flame" />
    </span>
  );
}

function ProductTopbar({ activePage, aiReady, locale }) {
  const currentPageLabel = pageLabelFor(locale, activePage);
  return (
    <header className="cl-topbar">
      <div className="cl-brand">
        <LogoMark />
        <div>
          <strong>Commodity Lab</strong>
          <span>{copy(locale, "AI 驱动的大宗商品交易训练平台", "AI-powered commodity trading training lab")}</span>
        </div>
      </div>
      <div className="cl-top-actions">
        <span className="cl-mode-pill"><Icon name="sparkles" />{copy(locale, "训练模式", "Training Mode")}</span>
        <span className="cl-route-pill">{currentPageLabel}</span>
        <AiStatusBadge aiReady={aiReady} locale={locale} />
      </div>
    </header>
  );
}

function ProductSidebar({ activePage, locale, onPageChange }) {
  return (
    <aside className="cl-sidebar">
      <nav className="cl-main-nav">
        {navItems.map((item) => (
          <button className={activePage === item.id ? "active" : ""} key={item.id} onClick={() => onPageChange(item.id)} type="button">
            <Icon name={item.icon} />
            <span>{labelFor(locale, item)}</span>
            {item.badge ? <small>{item.badge}</small> : null}
          </button>
        ))}
      </nav>
      <div className="cl-sidebar-footer">
        <button className={activePage === pageIds.settings ? "cl-settings-entry active" : "cl-settings-entry"} data-guide="settings-menu" onClick={() => onPageChange(pageIds.settings)} type="button">
          <Icon name="settings" />
          <span>{t("settings", locale)}</span>
        </button>
      </div>
    </aside>
  );
}

function LearningStepper({ active = 2, locale }) {
  return (
    <ol className="cl-learning-stepper">
      {learningFlow.map((step, index) => (
        <li className={index === active ? "active" : index < active ? "done" : ""} key={step.en}>
          <span>{index + 1}</span>
          <strong>{labelFor(locale, step)}</strong>
          <small>{copy(locale, step.detailZh, step.detailEn)}</small>
        </li>
      ))}
    </ol>
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

function HomePage({ aiReady, learningProgress, locale, onGenerate, onPageChange }) {
  const score = learningProgress.latestScore;
  const hasProgress = learningProgress.hasRecords && score != null;
  const weakSummary = learningProgress.weakest.length
    ? learningProgress.weakest.map((item) => labelFor(locale, item, "zh", "en")).join(" / ")
    : copy(locale, "提交一次策略后自动生成能力画像。", "Submit a strategy once to build your capability profile.");
  const startTrack = learningTracks[0];
  function startTrackDrill(track) {
    onGenerate(track.templateId, copy(locale, track.requestZh, track.requestEn));
  }
  return (
    <section className="cl-page cl-home-page">
      <PageTitle
        icon="home"
        locale={locale}
        titleZh="天然气套保学习路径"
        titleEn="Natural Gas Hedging Learning Path"
        subtitleZh="先按业务和知识点建立框架，再进入 AI 生成案例、组合操作和复盘。"
        subtitleEn="Build the business and concept framework first, then move into AI-generated cases, multi-leg decisions, and review."
        action={<button className="cl-primary" onClick={() => startTrackDrill(startTrack)} disabled={!aiReady} type="button"><Icon name="play" />{copy(locale, "开始第一课", "Start Lesson 1")}</button>}
      />
      <div className="cl-home-grid">
        <section className="cl-panel cl-hero-panel cl-course-hero">
          <div>
            <span>{copy(locale, "建议从基础课开始", "Recommended starting point")}</span>
            <h3>{copy(locale, "从基础敞口识别开始，逐步掌握套保目标、工具选择与实货/纸货匹配。", "Start with exposure identification, then build hedge objectives, tool selection, and physical-paper matching.")}</h3>
            <p>{copy(locale, "Commodity Lab 的训练顺序是：识别业务敞口 -> 选择实货/纸货工具 -> 做组合腿 -> 本地评分 -> AI 针对弱项生成下一题。", "Commodity Lab trains in this order: identify exposure -> choose physical/paper tools -> build multi-leg strategy -> score locally -> let AI generate the next weak-point drill.")}</p>
          </div>
          <div className="cl-hero-actions">
            <button className="cl-primary" onClick={() => startTrackDrill(startTrack)} disabled={!aiReady} type="button"><Icon name="play" />{copy(locale, "入门练习", "Beginner drill")}</button>
            <button className="cl-secondary" onClick={() => onPageChange(pageIds.knowledge)} type="button"><Icon name="map" />{copy(locale, "看课程地图", "Open course map")}</button>
          </div>
        </section>
        <section className="cl-panel cl-learning-route-panel cl-course-panel">
          <div className="cl-panel-heading"><span>{copy(locale, "业务课程路径", "Business Course Path")}</span><strong>{copy(locale, "Coursera + Roadmap 模式", "Course + Roadmap mode")}</strong></div>
          <div className="cl-course-grid">
            {learningTracks.map((track, index) => (
              <article key={track.id}>
                <div>
                  <b>{index + 1}</b>
                  <span>{copy(locale, track.levelZh, track.levelEn)}</span>
                </div>
                <h3>{labelFor(locale, track)}</h3>
                <p>{copy(locale, track.detailZh, track.detailEn)}</p>
                <div className="cl-chip-row">
                  {(locale === "zh" ? track.lessons : track.lessonsEn).map((lesson) => <span key={lesson}>{lesson}</span>)}
                </div>
                <button className={index === 0 ? "cl-primary" : "cl-secondary"} disabled={!aiReady} onClick={() => startTrackDrill(track)} type="button">
                  <Icon name={index === 0 ? "play" : "sparkles"} />
                  {index === 0 ? copy(locale, "开始", "Start") : copy(locale, "生成本章练习", "Generate drill")}
                </button>
              </article>
            ))}
          </div>
        </section>
        <section className="cl-panel">
          <div className="cl-panel-heading"><span>{copy(locale, "能力快照", "Capability Snapshot")}</span><strong>{hasProgress ? `${score}/100` : copy(locale, "本机记录", "Local records")}</strong></div>
          {hasProgress ? (
            <>
              <div className="cl-progress-ring" style={{ "--score": `${score * 3.6}deg` }}>
                <strong>{score}</strong>
                <span>/100</span>
              </div>
              <p className="cl-muted">{copy(locale, "当前弱项：", "Current weak points: ")}{weakSummary}</p>
              <div className="cl-mini-skill-grid">
                {learningProgress.dimensions.filter((item) => item.score != null).slice(0, 4).map((item) => (
                  <span key={item.id}>
                    <small>{labelFor(locale, item, "zh", "en")}</small>
                    <i><b style={{ width: `${item.score}%` }} /></i>
                    <strong>{item.score}</strong>
                  </span>
                ))}
              </div>
            </>
          ) : (
            <div className="cl-empty-progress">
              <strong>{copy(locale, "暂无正式训练记录", "No scored training records yet")}</strong>
              <p>{copy(locale, "生成案例并提交一次组合策略后，这里才会显示真实能力分、弱项和学习建议。", "Generate a case and submit a strategy to see real scores, weak points, and learning guidance.")}</p>
              <button className="cl-secondary" onClick={() => onPageChange(pageIds.caseLab)} type="button">{copy(locale, "开始第一次训练", "Start first drill")}</button>
            </div>
          )}
        </section>
        <section className="cl-panel cl-quick-actions">
          <div className="cl-panel-heading"><span>{copy(locale, "下一步", "Next Actions")}</span><strong>{aiReady ? t("online", locale) : t("offline", locale)}</strong></div>
          {[
            [pageIds.knowledge, "map", "先看知识结构", "Understand the map"],
            [pageIds.caseLab, "sparkles", "生成章节练习", "Generate chapter drill"],
            [pageIds.workbench, "workbench", "打开训练工作台", "Open training workbench"],
            [pageIds.progress, "progress", "查看训练画像", "View progress profile"]
          ].map(([page, icon, zh, en]) => (
            <button key={page} onClick={() => onPageChange(page)} type="button"><Icon name={icon} /><span>{copy(locale, zh, en)}</span><Icon name="arrow" /></button>
          ))}
        </section>
      </div>
    </section>
  );
}

function AiCaseLabPage({ activeTemplateId, aiReady, businessTemplates, locale, loadingTemplate, onGenerate, setActiveTemplateId }) {
  const templates = businessTemplates.templates?.length ? businessTemplates.templates : fallbackTemplates.templates;
  const [request, setRequest] = useState("");
  const active = templates.find((template) => template.id === activeTemplateId) ?? templates[0];
  const gasTemplates = templates.filter((template) => template.group === active?.group || template.id === active?.id);
  const activeCoverage = coverageForTemplate(active);
  const activeModels = modelsForTemplate(active);

  function randomize() {
    const next = templates[Math.floor(Math.random() * templates.length)];
    setActiveTemplateId(next.id);
  }

  return (
    <section className="cl-page cl-case-lab-page" data-guide="case-lab">
      <PageTitle
        icon="sparkles"
        locale={locale}
        titleZh="构建 AI 训练案例"
        titleEn="Build an AI Training Case"
        subtitleZh="选择业务参数，或者直接用自然语言描述你想训练的天然气套保问题。"
        subtitleEn="Configure parameters or describe the natural gas hedging case you want to practice."
        action={<button className="cl-secondary" type="button">{copy(locale, "操作说明", "How it works")}</button>}
      />
      <section className="cl-panel cl-course-picker">
        <div className="cl-panel-heading"><span>{copy(locale, "先选课程章节", "Choose a course chapter first")}</span><strong>{copy(locale, "AI 按章节生成练习", "AI generates by chapter")}</strong></div>
        <div className="cl-course-grid compact">
          {learningTracks.map((track, index) => (
            <article key={track.id}>
              <div><b>{index + 1}</b><span>{copy(locale, track.levelZh, track.levelEn)}</span></div>
              <h3>{labelFor(locale, track)}</h3>
              <p>{copy(locale, track.detailZh, track.detailEn)}</p>
              <div className="cl-mini-chip-row">
                {copy(locale, track.lessons, track.lessonsEn).slice(0, 3).map((lesson) => <span key={lesson}>{lesson}</span>)}
              </div>
              <button className={index === 0 ? "cl-primary" : "cl-secondary"} disabled={!aiReady || Boolean(loadingTemplate)} onClick={() => onGenerate(track.templateId, copy(locale, track.requestZh, track.requestEn))} type="button">
                <Icon name="sparkles" />{copy(locale, "生成练习", "Generate drill")}
              </button>
            </article>
          ))}
        </div>
      </section>
      <div className="cl-case-lab-grid">
        <section className="cl-panel cl-config-panel">
          <div className="cl-panel-heading"><span>1 {copy(locale, "配置场景", "Configure Scenario")}</span><button className="cl-secondary" onClick={randomize} type="button">{copy(locale, "随机", "Randomize")}</button></div>
          <div className="cl-form-grid">
            <label>{copy(locale, "商品", "Commodity")}<select value="natural-gas" disabled><option value="natural-gas">{copy(locale, "天然气", "Natural Gas")}</option></select></label>
            <label>{copy(locale, "业务角色", "Business Role")}<select defaultValue={active?.group ?? "procurement"}><option value="procurement">{copy(locale, "采购端", "Procurement")}</option><option value="sales">{copy(locale, "销售端", "Sales")}</option></select></label>
            <label>{copy(locale, "业务模板", "Scenario Family")}<select value={active?.id ?? ""} onChange={(event) => setActiveTemplateId(event.target.value)}>{templates.map((template) => <option key={template.id} value={template.id}>{template.title}</option>)}</select></label>
            <label>{copy(locale, "地区", "Region")}<select defaultValue="europe"><option value="europe">{copy(locale, "欧洲", "Europe")}</option><option value="uk">{copy(locale, "英国", "United Kingdom")}</option></select></label>
            <label>{copy(locale, "难度", "Difficulty")}<select defaultValue="intermediate"><option>{copy(locale, "中等", "Intermediate")}</option><option>{copy(locale, "困难", "Advanced")}</option></select></label>
            <label>{copy(locale, "风险重点", "Risk Focus")}<select defaultValue="basis"><option>{copy(locale, "价格、基差、汇率", "Price, Basis, FX")}</option><option>{copy(locale, "运力、信用、履约", "Capacity, Credit, Performance")}</option></select></label>
          </div>
          <label>{copy(locale, "自然语言需求", "Free-form request")}
            <textarea value={request} onChange={(event) => setRequest(event.target.value)} placeholder={copy(locale, "例如：英国上游 beach delivery 卖德国，市场快速下跌，训练实货、基差、汇率和运力组合套保。", "Example: UK beach delivery sold into Germany during a sharp selloff; train physical, basis, FX, and capacity hedge design.")} />
          </label>
          <div className="cl-action-row">
            <button className="cl-primary" disabled={!aiReady || loadingTemplate === active?.id} onClick={() => onGenerate(active?.id, request)} type="button"><Icon name="sparkles" />{loadingTemplate ? t("loading", locale) : copy(locale, "生成案例", "Generate Case")}</button>
            <button className="cl-secondary" onClick={() => setRequest("")} type="button">{copy(locale, "清空", "Clear")}</button>
          </div>
        </section>
        <section className="cl-panel cl-ai-preview">
          <div className="cl-panel-heading"><span>{copy(locale, "AI 预览", "AI Preview")}</span><strong>{aiReady ? t("online", locale) : t("connectToEnable", locale)}</strong></div>
          <h3>{active?.title}</h3>
          <p>{active?.summary}</p>
          <div className="cl-chip-row">
            {(active?.knowledge_points ?? ["basis_spread", "physical_paper_matching"]).map((point) => <span key={point}>{knowledgePointLabel(locale, point, businessTemplates)}</span>)}
          </div>
          <div className="cl-preview-facts">
            <span>{copy(locale, "将生成", "Will generate")}<strong>{copy(locale, "业务背景、曲线、事件、参考动作、评分规则", "Background, curves, events, target legs, rubric")}</strong></span>
            <span>{copy(locale, "数据性质", "Data type")}<strong>{t("aiGeneratedData", locale)}</strong></span>
          </div>
          <div className="cl-preview-coverage">
            <h4>{copy(locale, "知识覆盖", "Knowledge Coverage")}</h4>
            <div>
              {activeCoverage.slice(0, 4).map((item) => (
                <span key={item.id}>{labelFor(locale, item, "titleZh", "titleEn")}</span>
              ))}
            </div>
          </div>
          <div className="cl-preview-coverage">
            <h4>{copy(locale, "业务模型", "Gas Trading Models")}</h4>
            <div>
              {activeModels.slice(0, 4).map((item) => (
                <span key={item.id}>{labelFor(locale, item, "titleZh", "titleEn")}</span>
              ))}
            </div>
          </div>
        </section>
        <aside className="cl-panel cl-template-families">
          <div className="cl-panel-heading"><span>{copy(locale, "模板族", "Template Families")}</span><strong>{formatNumber(templates.length)}</strong></div>
          {gasTemplates.map((template) => (
            <button className={template.id === active?.id ? "active" : ""} key={template.id} onClick={() => setActiveTemplateId(template.id)} type="button">
              <Icon name="library" />
              <span>{template.title}</span>
              <small>{template.business_type}</small>
            </button>
          ))}
        </aside>
      </div>
    </section>
  );
}

function ScenarioLibraryPage({ activeTemplateId, learningProgress, locale, loadingTemplate, onGenerate, onPageChange }) {
  const [query, setQuery] = useState("");
  const filters = normalizeLocale(locale) === "zh"
    ? ["商品", "地区", "业务角色", "难度", "风险重点", "状态"]
    : ["Commodity", "Region", "Business Role", "Difficulty", "Risk Focus", "Status"];
  const visible = scenarioLibraryItems.filter((item) => {
    const text = `${item.titleZh} ${item.titleEn} ${item.summaryZh} ${item.summaryEn} ${item.tags.join(" ")}`.toLowerCase();
    return text.includes(query.trim().toLowerCase());
  });
  const scenarioStat = (item) => learningProgress.scenarioStats[item.id] ?? null;
  const trainedScenarios = Object.values(learningProgress.scenarioStats).filter((stat) => stat.attempts > 0).length;
  return (
    <section className="cl-page cl-library-page">
      <PageTitle
        icon="library"
        locale={locale}
        titleZh="场景库"
        titleEn="Scenario Library"
        subtitleZh="浏览、搜索并管理 AI 生成的训练案例，天然气场景优先开放。"
        subtitleEn="Browse, search, and manage AI-generated training cases. Natural gas scenarios are live first."
        action={<button className="cl-primary" onClick={() => onPageChange(pageIds.caseLab)} type="button"><Icon name="plus" />{copy(locale, "新建案例", "New Case")}</button>}
      />
      <div className="cl-library-grid">
        <section className="cl-panel cl-library-main">
          <div className="cl-searchbar">
            <Icon name="search" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={copy(locale, "搜索场景标题、描述、标签或关键词...", "Search scenario titles, descriptions, tags, or keywords...")} />
          </div>
          <div className="cl-filter-row">
            {filters.map((label) => <select key={label}><option>{copy(locale, `全部${label}`, `All ${label}`)}</option></select>)}
          </div>
          <div className="cl-scenario-table">
            <div className="cl-scenario-head">
              <span>{copy(locale, "场景", "Scenario")}</span><span>{copy(locale, "商品", "Commodity")}</span><span>{copy(locale, "难度", "Difficulty")}</span><span>{copy(locale, "预计时长", "Est.")}</span><span>{copy(locale, "进度", "Progress")}</span><span>{copy(locale, "操作", "Action")}</span>
            </div>
            {visible.map((item) => {
              const stat = scenarioStat(item);
              const progress = stat?.score ?? null;
              return (
              <article className={!item.enabled ? "disabled" : ""} key={item.id}>
                <div className="cl-scenario-name">
                  <div className="cl-thumb" />
                  <div>
                    <strong>{copy(locale, item.titleZh, item.titleEn)}</strong>
                    <p>{copy(locale, item.summaryZh, item.summaryEn)}</p>
                    <div className="cl-chip-row">{item.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
                  </div>
                </div>
                <span>{item.commodity === "natural-gas" ? copy(locale, "天然气", "Natural Gas") : copy(locale, "建设中", "Constructing")}</span>
                <span>{copy(locale, item.difficultyZh, item.difficultyEn)}</span>
                <span>{item.duration}{item.duration === "--" ? "" : copy(locale, " 分钟", " min")}</span>
                <span className={progress == null ? "cl-progress-cell is-empty" : "cl-progress-cell"}><i style={{ "--pct": `${progress ?? 0}%` }} /><b>{progress == null ? copy(locale, "未训练", "Not trained") : `${progress}%`}</b></span>
                <span className="cl-row-actions">
                  <button disabled={!item.enabled} onClick={() => onGenerate(item.id || activeTemplateId)} type="button">{progress != null ? copy(locale, "继续", "Continue") : copy(locale, "开始", "Start")}</button>
                  <button disabled={!item.enabled} onClick={() => onPageChange(pageIds.review)} type="button">{copy(locale, "复盘", "Review")}</button>
                </span>
              </article>
            );
            })}
          </div>
        </section>
        <aside className="cl-panel cl-library-side">
          <div className="cl-panel-heading"><span>{copy(locale, "我的本机记录", "My Local Records")}</span><strong>{copy(locale, "真实训练", "Actual training")}</strong></div>
          {[
            [copy(locale, "正式提交", "Scored attempts"), learningProgress.attempts],
            [copy(locale, "已训练场景", "Trained scenarios"), trainedScenarios],
            [copy(locale, "平均得分", "Average score"), learningProgress.averageScore ?? "--"],
            [copy(locale, "最近得分", "Latest score"), learningProgress.latestScore ?? "--"]
          ].map(([label, value]) => <button key={label} type="button"><Icon name="progress" /><span>{label}</span><small>{value}</small></button>)}
          <div className="cl-divider" />
          <div className="cl-panel-heading"><span>{copy(locale, "为你推荐", "Recommended")}</span><strong>{copy(locale, "换一换", "Refresh")}</strong></div>
          {scenarioLibraryItems.filter((item) => item.enabled).slice(0, 3).map((item) => <button key={item.id} onClick={() => onGenerate(item.id)} type="button"><span>{copy(locale, item.titleZh, item.titleEn)}</span><small>{item.duration} min</small></button>)}
        </aside>
      </div>
    </section>
  );
}

function DecisionTaskPanel({ caseData, locale }) {
  return (
    <section className="cl-panel cl-decision-panel">
      <div className="cl-panel-heading"><span>1 {copy(locale, "决策任务", "Decision Task")}</span><strong>{caseData.scenario?.business_type}</strong></div>
      <MarkdownText text={caseData.prompt} />
      <div className="cl-exposure-strip">
        <span>{copy(locale, "方向", "Exposure")}<strong>{caseData.scenario?.exposure?.direction ?? "--"}</strong></span>
        <span>{copy(locale, "数量", "Volume")}<strong>{formatNumber(caseData.scenario?.exposure?.volume_mmbtu)} MMBtu</strong></span>
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
          <span>{t("aiGeneratedData", locale)}</span>
        </div>
      </div>
      <dl>
        <div><dt>{copy(locale, "敞口方向", "Exposure Direction")}</dt><dd>{copy(locale, "卖出 / Short", "Short / Sell")}</dd></div>
        <div><dt>{copy(locale, "期限", "Tenor")}</dt><dd>1-3M</dd></div>
        <div><dt>{copy(locale, "来源 / 交付", "Origin / Delivery")}</dt><dd>UK Beach &gt; Germany</dd></div>
      </dl>
    </section>
  );
}

function WorkbenchPage({ activeTemplate, advisorProps, caseData, fieldSelection, locale, onCheckStrategy, onGenerateVariant, onSuggestTarget, strategyProps }) {
  return (
    <section className="cl-page cl-workbench-page">
      <LearningStepper active={2} locale={locale} />
      <CaseHero activeTemplate={activeTemplate} caseData={caseData} locale={locale} />
      <div className="cl-workbench-grid">
        <div className="cl-workbench-left">
          <DecisionTaskPanel caseData={caseData} locale={locale} />
          <MarketChart caseData={caseData} fieldSelection={fieldSelection.value} locale={locale} setFieldSelection={fieldSelection.set} strategyLegs={strategyProps.strategyLegs} />
        </div>
        <div className="cl-workbench-center">
          <section className="cl-panel cl-strategy-tools">
            <div className="cl-panel-heading"><span>3 {copy(locale, "策略构建辅助", "Strategy Assistance")}</span><strong>{copy(locale, "本地即时反馈", "Immediate local feedback")}</strong></div>
            <div className="cl-action-grid">
              <button onClick={onSuggestTarget} type="button"><Icon name="sparkles" />{copy(locale, "AI 建议策略腿", "AI Suggest Legs")}</button>
              <button onClick={onCheckStrategy} type="button"><Icon name="coach" />{copy(locale, "提交前检查", "Check Before Submit")}</button>
              <button onClick={onGenerateVariant} type="button"><Icon name="plus" />{copy(locale, "生成变体", "Generate Variant")}</button>
              <button className="cl-submit-inline" disabled={strategyProps.busy} onClick={strategyProps.onSubmit} type="button"><Icon name="chart" />{strategyProps.busy ? t("loading", locale) : t("submitOrder", locale)}</button>
            </div>
          </section>
          <StrategyBuilder {...strategyProps} />
          <div className="cl-bottom-grid">
            <ScorePanel evaluation={strategyProps.evaluation} locale={locale} />
            <RubricPanel caseData={caseData} locale={locale} />
          </div>
        </div>
        <AdvisorRail {...advisorProps} />
      </div>
    </section>
  );
}

function ReviewPage({ caseData, evaluation, locale, onGenerateVariant, onPageChange, runAiAction, strategyLegs }) {
  const target = caseData.target_actions ?? [];
  return (
    <section className="cl-page cl-review-page">
      <LearningStepper active={3} locale={locale} />
      <PageTitle
        icon="chart"
        locale={locale}
        titleZh="复盘反馈"
        titleEn="Review & Feedback"
        subtitleZh="把你的组合动作和 AI 生成的目标动作逐项对照，再进入强化训练。"
        subtitleEn="Compare your multi-leg strategy with the AI-generated target before reinforcement drills."
        action={<button className="cl-primary" onClick={() => runAiAction("advisor_review")} disabled={!evaluation} type="button"><Icon name="coach" />{copy(locale, "AI 解释评分", "AI Explain Score")}</button>}
      />
      <div className="cl-review-grid">
        <section className="cl-panel cl-score-summary">
          <div className="cl-progress-ring large" style={{ "--score": `${(evaluation?.baseline_score ?? 0) * 3.6}deg` }}><strong>{evaluation?.baseline_score ?? "--"}</strong><span>/100</span></div>
          <h3>{evaluation ? copy(locale, "本地评分已完成", "Local scoring complete") : copy(locale, "尚未提交策略", "No strategy submitted")}</h3>
          <p>{copy(locale, "评分不等待 AI；AI 用于解释、追问和生成后续训练。", "Scoring does not wait for AI. AI explains, challenges, and generates follow-up drills.")}</p>
          <div className="cl-action-row">
            <button className="cl-secondary" onClick={() => onPageChange(pageIds.workbench)} type="button">{copy(locale, "回到工作台", "Back to Workbench")}</button>
            <button className="cl-primary" onClick={onGenerateVariant} type="button">{copy(locale, "训练弱项变体", "Drill Weak Variant")}</button>
          </div>
        </section>
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
              {evaluation.mistake_tags.map((tag) => <li key={tag}>{tag}</li>)}
            </ul>
          ) : <p className="empty-state">{copy(locale, "提交策略后显示真实错误标签。", "Submit a strategy to show real mistake tags.")}</p>}
        </section>
      </div>
    </section>
  );
}

function KnowledgeMapPage({ locale, onPageChange, runAiAction }) {
  const [selected, setSelected] = useState("basis");
  const node = knowledgeNodes.find((item) => item.id === selected) ?? knowledgeNodes[0];
  const pathItems = [
    ["敞口与目标", "Exposure and Objective"],
    ["实货/纸货匹配", "Physical-Paper Matching"],
    ["单边价格套保", "Outright Price Hedge"],
    ["基差与价差", "Basis and Spreads"],
    ["期权与可选性", "Options and Optionality"],
    ["执行与风控", "Execution and Controls"]
  ];
  return (
    <section className="cl-page cl-knowledge-page">
      <PageTitle
        icon="map"
        locale={locale}
        titleZh="知识图谱"
        titleEn="Knowledge Map"
        subtitleZh="围绕天然气交易，把概念、业务场景和训练题连接起来。"
        subtitleEn="Connect natural gas concepts, business scenarios, and practice cases."
        action={<button className="cl-primary" onClick={() => onPageChange(pageIds.caseLab)} type="button"><Icon name="sparkles" />{copy(locale, "生成学习路径", "Generate Learning Path")}</button>}
      />
      <div className="cl-knowledge-grid">
        <section className="cl-panel cl-map-canvas">
          <div className="cl-map-center"><LogoMark /><strong>{copy(locale, "天然气交易", "Natural Gas Trading")}</strong></div>
          {knowledgeNodes.map((item) => (
            <button className={selected === item.id ? `active ${item.level}` : item.level} key={item.id} onClick={() => setSelected(item.id)} style={{ left: `${item.x}%`, top: `${item.y}%` }} type="button">
              <span>{labelFor(locale, item, "titleZh", "titleEn")}</span>
              <small>{item.level}</small>
            </button>
          ))}
        </section>
        <aside className="cl-panel cl-topic-panel">
          <div className="cl-panel-heading"><span>{copy(locale, "选中主题", "Selected Topic")}</span><strong>{node.level}</strong></div>
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
        <div className="cl-panel-heading"><span>{copy(locale, "推荐路径", "Recommended Path")}</span><strong>Natural Gas</strong></div>
        <div className="cl-path-row">{pathItems.map(([zh, en], index) => <span key={en}><b>{index + 1}</b>{copy(locale, zh, en)}</span>)}</div>
      </section>
      <section className="cl-panel cl-coverage-panel">
        <div className="cl-panel-heading"><span>{copy(locale, "教材式套保知识覆盖", "Textbook-Style Hedging Coverage")}</span><strong>{copy(locale, "天然气化", "Gas-specific")}</strong></div>
        <div className="cl-coverage-grid">
          {hedgingKnowledgeCoverage.map((item) => (
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
      </section>
      <section className="cl-panel cl-model-panel">
        <div className="cl-panel-heading"><span>{copy(locale, "天然气交易模型", "Gas Trading Models")}</span><strong>{copy(locale, "用于 AI 出题", "Used by AI")}</strong></div>
        <div className="cl-gas-model-grid">
          {gasTradingModels.map((item) => (
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

function ProgressPage({ learningProgress, locale, onPageChange }) {
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
        action={<button className="cl-primary" onClick={() => onPageChange(pageIds.caseLab)} type="button"><Icon name="plus" />{copy(locale, "生成弱项训练", "Generate Weak-Point Drill")}</button>}
      />
      <div className="cl-progress-layout">
        <section className="cl-panel">
          <div className="cl-panel-heading"><span>{copy(locale, "能力画像", "Capability Profile")}</span><strong>{hasProgress ? `${learningProgress.latestScore}/100` : copy(locale, "暂无记录", "No records")}</strong></div>
          {hasProgress ? (
            <>
              <div className="cl-progress-facts">
                <span>{copy(locale, "正式提交", "Scored attempts")}<strong>{learningProgress.attempts}</strong></span>
                <span>{copy(locale, "最近得分", "Latest score")}<strong>{learningProgress.latestScore ?? "--"}</strong></span>
                <span>{copy(locale, "平均得分", "Average score")}<strong>{learningProgress.averageScore ?? "--"}</strong></span>
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
              <p>{copy(locale, "只有点击“提交策略”完成本地评分后，Commodity Lab 才会记录能力分、弱项和场景进度。", "Commodity Lab records capability scores, weak points, and scenario progress only after you submit a strategy for local scoring.")}</p>
              <button className="cl-primary" onClick={() => onPageChange(pageIds.caseLab)} type="button">{copy(locale, "生成第一个案例", "Generate first case")}</button>
            </div>
          )}
        </section>
        <section className="cl-panel">
          <div className="cl-panel-heading"><span>{copy(locale, "AI 推荐下一步", "AI Recommended Next Step")}</span><strong>{copy(locale, "基于弱项", "Based on weak points")}</strong></div>
          <h3>{hasProgress ? copy(locale, "按当前弱项生成下一题", "Generate the next drill from current weak points") : copy(locale, "先完成一次正式训练", "Complete one scored drill first")}</h3>
          <p>{hasProgress ? copy(locale, "建议重点：", "Recommended focus: ") + weakSummary : copy(locale, "进度页不会使用演示数据；第一条学习建议会在你提交策略后出现。", "This page does not use demo data; your first recommendation appears after you submit a strategy.")}</p>
          <button className="cl-primary" onClick={() => onPageChange(pageIds.caseLab)} type="button">{copy(locale, "开始推荐训练", "Start Recommended Drill")}</button>
        </section>
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
            copy(locale, "生成一个英国上游 beach delivery 卖德国的套保训练题。", "Generate a UK beach delivery sale into Germany hedging drill."),
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

function FloatingAssistant({ activePage, aiReady, applyAction, locale, messages, onSend, thinking }) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const currentPage = navItems.find((item) => item.id === activePage);
  const quickPrompts = [
    copy(locale, "按当前课程生成下一道训练题。", "Generate the next drill for the current course."),
    copy(locale, "用三句话解释当前页面的核心知识点。", "Explain the current page concept in three sentences."),
    copy(locale, "检查当前策略还缺少哪些风险动作。", "Check which risk actions are missing from the current strategy.")
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
        <section className="assistant-panel">
          <header>
            <div>
              <span>{t("liveAssistant", locale)}</span>
              <strong>{aiReady ? t("online", locale) : t("offline", locale)} · {currentPage ? labelFor(locale, currentPage) : "Commodity Lab"}</strong>
            </div>
            <button className="icon-button" aria-label={t("close", locale)} onClick={() => setOpen(false)} type="button"><Icon name="close" /></button>
          </header>
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
            {thinking ? <AiThinkingPanel locale={locale} titleKey="assistantWorking" /> : null}
          </div>
          <form onSubmit={submit}><textarea disabled={!aiReady || thinking} value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={t("assistantPlaceholder", locale)} /><button className="primary" disabled={!aiReady || thinking || !draft.trim()} type="submit">{thinking ? t("loading", locale) : t("send", locale)}</button></form>
        </section>
      ) : null}
      <button className="assistant-orb" aria-expanded={open} aria-label={t("liveAssistant", locale)} onClick={() => setOpen((current) => !current)} type="button">
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
  const [locale, setLocaleState] = useState(initialLocale);
  const [theme, setThemeState] = useState(() => normalizeThemeMode(savedValue("commodity-lab-theme", "system")));
  const [resolvedTheme, setResolvedTheme] = useState(() => getSystemThemePreference());
  const [backendReady, setBackendReady] = useState(false);
  const [startupStage, setStartupStage] = useState(startupStageKeys[0]);
  const [startupSlow, setStartupSlow] = useState(false);
  const [providerStatus, setProviderStatus] = useState(null);
  const [templates, setTemplates] = useState(fallbackTemplates);
  const [activeTemplateId, setActiveTemplateId] = useState(fallbackTemplates.templates[0].id);
  const [activePage, setActivePage] = useState(pageIds.home);
  const [caseData, setCaseData] = useState(() => defaultCase(initialLocale));
  const [generationStages, setGenerationStages] = useState([]);
  const [loadingTemplate, setLoadingTemplate] = useState("");
  const [fieldSelection, setFieldSelection] = useState(["close"]);
  const [strategyLegs, setStrategyLegs] = useState(() => defaultLegs(initialLocale));
  const [rationale, setRationale] = useState(() =>
    initialLocale === "zh"
      ? "说明实货、纸货、基差/汇率/运力的匹配逻辑。"
      : "Explain how the physical, paper, basis, FX, and capacity legs match the exposure."
  );
  const [evaluation, setEvaluation] = useState(null);
  const [advisorFeedback, setAdvisorFeedback] = useState("");
  const [exam, setExam] = useState("");
  const [aiOutput, setAiOutput] = useState(null);
  const [busyAction, setBusyAction] = useState("");
  const [serviceMessage, setServiceMessage] = useState("");
  const [updateInfo, setUpdateInfo] = useState({ current_version: currentVersion });
  const [assistantMessages, setAssistantMessages] = useState([]);
  const [learningRecords, setLearningRecords] = useState(() => loadLearningRecords());
  const [aiGuidanceAction, setAiGuidanceAction] = useState("");
  const [guideIndex, setGuideIndex] = useState(() => savedValue("commodity-lab-guide-complete", "") ? -1 : 0);
  const aiReady = Boolean(providerStatus?.haineng?.ok);
  const learningProgress = useMemo(() => summarizeLearningRecords(learningRecords), [learningRecords]);

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
  function showAiGuidance(message) {
    setAiGuidanceAction(message);
    window.clearTimeout(showAiGuidance.timer);
    showAiGuidance.timer = window.setTimeout(() => setAiGuidanceAction(""), 2600);
  }

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

  async function generateTrainingCase(templateId, userRequest = "") {
    setActiveTemplateId(templateId);
    if (!aiReady) {
      setServiceMessage(t("aiRequiredForCase", locale));
      setActivePage(pageIds.settings);
      return;
    }
    setLoadingTemplate(templateId);
    setBusyAction("case_generation");
    setActivePage(pageIds.workbench);
    setGenerationStages([{ id: "read_template", label: t("stageReadTemplate", locale) }]);
    try {
      setGenerationStages((current) => [...current, { id: "generate_market", label: t("stageGenerateMarket", locale) }]);
      const curriculum = curriculumReference(locale);
      const payload = await backendRequest("POST", "/api/v1/ai/training-case", {
        template_id: templateId,
        locale,
        user_request: userRequest,
        ...curriculum
      });
      const nextCase = payload.case ?? defaultCase(locale);
      setGenerationStages((current) => [...current, { id: "build_case", label: t("stageBuildCase", locale) }]);
      setCaseData(nextCase);
      setStrategyLegs((nextCase.target_actions ?? defaultLegs()).map((leg, index) => ({ id: leg.id ?? `ai-leg-${index}`, ...leg })));
      setRationale(locale === "zh" ? "写下你的组合套保逻辑、风险覆盖和执行检查。" : "Write your hedge logic, covered risks, and execution checks.");
      setEvaluation(null);
      setAdvisorFeedback("");
      setExam("");
      setAiOutput(null);
    } catch (error) {
      setServiceMessage(formatErrorMessage(error, locale));
    } finally {
      setBusyAction("");
      setLoadingTemplate("");
    }
  }

  function submitStrategy() {
    setBusyAction("evaluate");
    const nextEvaluation = evaluateStrategy(caseData, strategyLegs, rationale);
    setEvaluation(nextEvaluation);
    appendLearningRecord(recordLearningAttempt({ activeTemplateId, caseData, evaluation: nextEvaluation, rationale, strategyLegs }));
    setAiOutput(null);
    setBusyAction("");
    setActivePage(pageIds.review);
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
    const prompt = copy(
      locale,
      "基于当前案例生成一个更贴近真实业务的变体，重点放在市场剧烈波动、基差错配、汇率和运力约束。",
      "Generate a realistic variant of the current case focused on sharp market moves, basis mismatch, FX, and capacity constraints."
    );
    generateTrainingCase(activeTemplateId, prompt);
  }

  function buildAiPayload(capability) {
    const curriculum = curriculumReference(locale);
    return {
      capability,
      scenario_id: "europe_ttf_nbp_spread",
      locale,
      order: orderFromStrategy(strategyLegs),
      rationale,
      evaluation: evaluation ?? {},
      attempt_history: learningRecords.map((record) => record.evaluation).filter(Boolean).slice(-12),
      learning_progress: learningProgress,
      market_context: { case: caseData, strategy_legs: strategyLegs },
      curriculum_context: curriculum,
      user_request: rationale,
      concept: curriculum.knowledge_coverage.map((item) => item.title).join(", "),
      commercial_goal: "Build a practical multi-leg hedge playbook for this generated gas business case."
    };
  }

  async function runAiAction(capability) {
    if (!aiReady) return;
    if (capability === "advisor_review" && !evaluation) return;
    setBusyAction(capability);
    setServiceMessage("");
    try {
      const path = capability === "exam" ? "/api/v1/exam/generate" : "/api/v1/ai/generate";
      const payload = await backendRequest("POST", path, capability === "exam" ? {
        scenario_id: "europe_ttf_nbp_spread",
        locale,
        attempt_history: learningRecords.map((record) => record.evaluation).filter(Boolean).slice(-12),
        curriculum_context: curriculumReference(locale)
      } : buildAiPayload(capability));
      if (capability === "advisor_review") {
        setAdvisorFeedback(payload.answer);
        setActivePage(pageIds.review);
        showAiGuidance(copy(locale, "AI 已切到复盘页并生成简短反馈。", "AI opened Review with concise feedback."));
      } else if (capability === "exam") {
        setExam(payload.exam);
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
    const userMessage = { role: "user", content: message };
    setAssistantMessages((current) => [...current, userMessage]);
    setBusyAction("assistant");
    try {
      const curriculum = curriculumReference(locale);
      const payload = await backendRequest("POST", "/api/v1/ai/live-assistant", {
        locale,
        message,
        workspace_state: {
          active_page: activePage,
          active_template_id: activeTemplateId,
          curriculum_context: curriculum,
          case: caseData,
          evaluation,
          learning_progress: learningProgress,
          recent_attempts: learningRecords.slice(-8),
          strategy_legs: strategyLegs
        }
      });
      const actions = payload.actions ?? [];
      setAssistantMessages((current) => [...current, { role: "assistant", content: payload.answer, actions }]);
      actions.filter((action) => ["navigate_page", "set_chart_fields", "set_exam", "generate_case", "select_template", "run_ai_capability"].includes(action.type)).slice(0, 1).forEach(applyAssistantAction);
    } catch (error) {
      setAssistantMessages((current) => [...current, { role: "assistant", content: formatErrorMessage(error, locale), actions: [] }]);
    } finally {
      setBusyAction("");
    }
  }

  function applyAssistantAction(action) {
    const payload = action.payload ?? {};
    if (action.type === "select_template" && payload.template_id) {
      generateTrainingCase(payload.template_id, payload.user_request ?? "");
      showAiGuidance(copy(locale, "AI 正在按课程生成练习。", "AI is generating a course drill."));
    }
    if (action.type === "generate_case") {
      const track = learningTracks.find((item) => item.id === payload.track_id) ?? learningTracks[0];
      generateTrainingCase(payload.template_id ?? track.templateId, payload.user_request ?? copy(locale, track.requestZh, track.requestEn));
      showAiGuidance(copy(locale, "AI 正在生成新练习并打开工作台。", "AI is generating a new drill and opening the workbench."));
    }
    if (action.type === "navigate_page" && (pageIds[payload.page] || Object.values(pageIds).includes(payload.page))) {
      const page = pageIds[payload.page] ?? payload.page;
      setActivePage(page);
      showAiGuidance(copy(locale, "AI 已切换到对应页面。", "AI navigated to the requested page."));
    }
    if (action.type === "set_chart_fields" && Array.isArray(payload.fields)) {
      const fields = payload.fields.filter((field) => chartFields.includes(field));
      setFieldSelection(fields.length ? fields : ["close"]);
      setActivePage(pageIds.workbench);
      showAiGuidance(copy(locale, "AI 已切到工作台并调整图表字段。", "AI opened the workbench and adjusted chart fields."));
    }
    if (action.type === "set_strategy_legs" && Array.isArray(payload.legs)) {
      setStrategyLegs(payload.legs.map((leg, index) => ({ id: leg.id ?? `assistant-leg-${index}`, ...leg })));
      setActivePage(pageIds.workbench);
      showAiGuidance(copy(locale, "AI 已把建议策略腿填入工作台，请你检查后再提交。", "AI filled suggested legs in the workbench. Review before submitting."));
    }
    if (action.type === "fill_rationale" && payload.text) {
      setRationale(payload.text);
      setActivePage(pageIds.workbench);
      showAiGuidance(copy(locale, "AI 已填入策略说明草稿。", "AI filled a rationale draft."));
    }
    if (action.type === "set_exam" && payload.exam) {
      setExam(payload.exam);
      setActivePage(pageIds.review);
      showAiGuidance(copy(locale, "AI 已创建测验并打开复盘页。", "AI created a quiz and opened Review."));
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
    busy: busyAction === "evaluate",
    evaluation,
    locale,
    onSubmit: submitStrategy,
    rationale,
    setRationale,
    setStrategyLegs,
    strategyLegs
  };

  function renderActivePage() {
    if (activePage === pageIds.caseLab) {
      return (
        <AiCaseLabPage
          activeTemplateId={activeTemplateId}
          aiReady={aiReady}
          businessTemplates={templates}
          locale={locale}
          loadingTemplate={loadingTemplate}
          onGenerate={generateTrainingCase}
          setActiveTemplateId={setActiveTemplateId}
        />
      );
    }
    if (activePage === pageIds.workbench) {
      return (
        <WorkbenchPage
          activeTemplate={activeTemplate}
          advisorProps={advisorProps}
          caseData={caseData}
          fieldSelection={{ value: fieldSelection, set: setFieldSelection }}
          locale={locale}
          onCheckStrategy={checkStrategyBeforeSubmit}
          onGenerateVariant={generateVariant}
          onSuggestTarget={suggestTargetStrategy}
          strategyProps={strategyProps}
        />
      );
    }
    if (activePage === pageIds.review) {
      return <ReviewPage caseData={caseData} evaluation={evaluation} locale={locale} onGenerateVariant={generateVariant} onPageChange={setActivePage} runAiAction={runAiAction} strategyLegs={strategyLegs} />;
    }
    if (activePage === pageIds.library) {
      return <ScenarioLibraryPage activeTemplateId={activeTemplateId} learningProgress={learningProgress} locale={locale} loadingTemplate={loadingTemplate} onGenerate={generateTrainingCase} onPageChange={setActivePage} />;
    }
    if (activePage === pageIds.knowledge) {
      return <KnowledgeMapPage locale={locale} onPageChange={setActivePage} runAiAction={runAiAction} />;
    }
    if (activePage === pageIds.progress) {
      return <ProgressPage learningProgress={learningProgress} locale={locale} onPageChange={setActivePage} />;
    }
    if (activePage === pageIds.coach) {
      return <AiCoachPage aiReady={aiReady} applyAction={applyAssistantAction} locale={locale} messages={assistantMessages} onSend={sendAssistant} thinking={busyAction === "assistant"} />;
    }
    if (activePage === pageIds.settings) {
      return <SettingsPage locale={locale} settingsPanel={settingsPanel} />;
    }
    return <HomePage aiReady={aiReady} learningProgress={learningProgress} locale={locale} onGenerate={generateTrainingCase} onPageChange={setActivePage} />;
  }

  return (
    <main className={aiReady ? "app-shell cl-app-shell ai-ready" : "app-shell cl-app-shell"}>
      <ProductTopbar activePage={activePage} aiReady={aiReady} locale={locale} />

      <div className="cl-app-layout">
        <ProductSidebar activePage={activePage} locale={locale} onPageChange={setActivePage} />
        <section className="cl-content-shell">
          {generationStages.length && busyAction === "case_generation" ? <GenerationTimeline locale={locale} stages={generationStages} /> : null}
          {aiGuidanceAction ? <p className="cl-ai-guidance"><Icon name="sparkles" />{aiGuidanceAction}</p> : null}
          {serviceMessage && activePage !== pageIds.settings ? <p className="cl-service-banner">{serviceMessage}</p> : null}
          {renderActivePage()}
        </section>
      </div>

      <FloatingAssistant activePage={activePage} aiReady={aiReady} applyAction={applyAssistantAction} locale={locale} messages={assistantMessages} onSend={sendAssistant} thinking={busyAction === "assistant"} />

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
  if (parsed?.detail?.provider_message) return parsed.detail.provider_message;
  if (parsed?.provider_message) return parsed.provider_message;
  return raw.replace(/^backend status \d+:\s*/i, "");
}
