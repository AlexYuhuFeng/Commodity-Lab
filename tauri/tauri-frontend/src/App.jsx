import React, { useEffect, useMemo, useRef, useState } from "react";
import { appWindow } from "@tauri-apps/api/window";
import { backendRequest } from "./api";
import { normalizeLocale, t } from "./i18n";

const currentVersion = "1.0.13";

const defaultProviderCatalog = {
  haineng: {
    label: "Haineng",
    default_model: "DeepSeek-V4-Flash",
    models: [
      {
        id: "DeepSeek-V4-Flash",
        label: "DeepSeek-V4-Flash",
        resolved_model: "DeepSeek-V4-Flash",
        base_url: "http://model.ai.cnooc/member1/deepseek-v4-flash-284b/v1"
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

const commodityTabs = [
  { id: "natural-gas", zh: "天然气", en: "Natural Gas", enabled: true },
  { id: "crude-oil", zh: "原油", en: "Crude Oil", enabled: false },
  { id: "refined", zh: "成品油", en: "Refined Products", enabled: false },
  { id: "power-carbon", zh: "电力与碳", en: "Power & Carbon", enabled: false },
  { id: "all", zh: "全部商品", en: "All Commodities", enabled: false }
];

const navItems = [
  { id: pageIds.home, icon: "home", zh: "首页", en: "Home" },
  { id: pageIds.caseLab, icon: "sparkles", zh: "案例实验室", en: "AI Case Lab" },
  { id: pageIds.workbench, icon: "workbench", zh: "训练工作台", en: "Training Workbench" },
  { id: pageIds.library, icon: "library", zh: "场景库", en: "Scenario Library" },
  { id: pageIds.review, icon: "chart", zh: "复盘反馈", en: "Review & Feedback" },
  { id: pageIds.knowledge, icon: "map", zh: "知识图谱", en: "Knowledge Map" },
  { id: pageIds.progress, icon: "progress", zh: "我的进度", en: "My Progress" },
  { id: pageIds.coach, icon: "coach", zh: "AI 教练", en: "AI Coach", badge: "NEW" }
];

const learningFlow = [
  { zh: "发现", en: "Discover", detailZh: "理解知识点与业务风险", detailEn: "Concepts and business risk" },
  { zh: "生成", en: "Generate", detailZh: "AI 构建案例与数据", detailEn: "AI case and data" },
  { zh: "练习", en: "Practice", detailZh: "组合实货与纸货动作", detailEn: "Build physical and paper legs" },
  { zh: "复盘", en: "Review", detailZh: "评分、错误和对照", detailEn: "Score and compare" },
  { zh: "强化", en: "Reinforce", detailZh: "按弱项生成变体", detailEn: "Drill weak points" }
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
    progress: 68,
    statusZh: "进行中",
    statusEn: "In progress",
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
    progress: 42,
    statusZh: "进行中",
    statusEn: "In progress",
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
    progress: 0,
    statusZh: "未开始",
    statusEn: "Not started",
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
    progress: 0,
    statusZh: "未开始",
    statusEn: "Not started",
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
    progress: 0,
    statusZh: "建设中",
    statusEn: "Constructing",
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

const progressDimensions = [
  ["exposure", "风险识别", "Exposure Identification", 78],
  ["instrument", "工具选择", "Hedge Instrument Selection", 66],
  ["basis", "基差逻辑", "Basis Logic", 58],
  ["fx", "汇率逻辑", "FX Logic", 44],
  ["capacity", "运力/物流", "Capacity & Logistics", 52],
  ["timing", "执行时机", "Execution Timing", 61],
  ["control", "风险控制", "Risk Control", 70],
  ["rationale", "说明质量", "Rationale Quality", 64]
];

function copy(locale, zh, en) {
  return normalizeLocale(locale) === "zh" ? zh : en;
}

const fallbackTemplates = {
  groups: [
    { id: "procurement", label: "采购端" },
    { id: "sales", label: "销售端" }
  ],
  knowledge_points: [
    { id: "basis_spread", label: "基差与枢纽价差", description: "TTF/NBP、地点差、单位与汇率归一化。" },
    { id: "physical_paper_matching", label: "实货与纸货匹配", description: "GSA、EFET、LNG、swap、future、FX、capacity 的组合动作。" }
  ],
  templates: [
    {
      id: "procurement_beach_to_germany",
      group: "procurement",
      business_type: "上游 Beach Delivery 资源（GSA）",
      title: "英国上游 Beach Delivery 卖德国",
      summary: "AI 生成 NBP/TTF、汇率、运输和实纸货匹配案例。",
      knowledge_points: ["basis_spread", "fx", "physical_paper_matching"],
      required_curves: ["TTF", "NBP", "EURGBP", "TTF_NBP_SPREAD"],
      suggested_leg_types: ["physical", "basis", "fx", "capacity"]
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
      title: zh ? "选择业务模板生成案例" : "Select a business template to generate a case",
      summary: zh
        ? "Commodity Lab 现在以 AI 生成训练数据为核心。先从左侧选择采购端或销售端业务模板。"
        : "Commodity Lab now uses AI-generated training data. Start from a procurement or sales business template.",
      business_type: zh ? "采购端 / 销售端" : "Procurement / Sales",
      knowledge_points: ["basis_spread", "physical_paper_matching"],
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

function normalizeProviderName(value, baseUrl = "") {
  const provider = compactKey(value);
  const url = String(baseUrl ?? "").toLowerCase();
  if (provider === "deepseek" || provider === "deep-seek" || provider === "ds" || url.includes("api.deepseek.com")) return "deepseek";
  return "haineng";
}

function firstConfigValue(payload, ...keys) {
  for (const key of keys) {
    const value = payload[compactKey(key)] ?? payload[String(key).toLowerCase()];
    if (value != null && String(value).trim()) return String(value).trim();
  }
  return "";
}

function parseAiKeyFile(text) {
  const raw = String(text ?? "").trim();
  if (!raw) throw new Error("AI key file is empty.");
  if (raw.startsWith("{")) {
    const parsed = JSON.parse(raw);
    return Object.fromEntries(Object.entries(parsed).map(([key, value]) => [compactKey(key), String(value ?? "").trim()]));
  }
  const payload = {};
  raw.split(/\r?\n/).forEach((line) => {
    const current = line.trim();
    if (!current || current.startsWith("#")) return;
    const index = current.includes("=") ? current.indexOf("=") : current.indexOf(":");
    if (index <= 0) return;
    payload[compactKey(current.slice(0, index))] = current.slice(index + 1).trim();
  });
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

function formFromAiKeyFile(text, catalog = defaultProviderCatalog) {
  const payload = parseAiKeyFile(text);
  const baseUrlHint = firstConfigValue(payload, "base_url", "url", "haineng_base_url", "deepseek_base_url");
  const provider = normalizeProviderName(firstConfigValue(payload, "provider", "ai_provider"), baseUrlHint);
  const config = providerConfig(catalog, provider);
  const providerPrefix = provider === "deepseek" ? "deepseek" : "haineng";
  const apiKey = firstConfigValue(payload, "api_key", "key", `${providerPrefix}_api_key`);
  if (!apiKey) throw new Error("AI key file is missing api_key.");
  const model = modelForProvider(provider, firstConfigValue(payload, "model", `${providerPrefix}_model`) || config.default_model, config);
  const selected = modelConfig(catalog, provider, model);
  return {
    api_key: apiKey,
    provider,
    model,
    base_url: firstConfigValue(payload, "base_url", "url", `${providerPrefix}_base_url`) || selected?.base_url || ""
  };
}

function formForProvider(provider, catalog = defaultProviderCatalog, apiKey = "") {
  const config = providerConfig(catalog, provider);
  const storedModel = savedValue(`commodity-lab-${provider}-model`, config.default_model);
  const model = config.models.some((option) => option.id === storedModel) ? storedModel : config.default_model;
  const selected = modelConfig(catalog, provider, model);
  const storedBaseUrl = savedValue(`commodity-lab-${provider}-base-url`, "");
  return {
    api_key: apiKey,
    provider,
    model,
    base_url: baseUrlMatchesProvider(provider, storedBaseUrl) ? storedBaseUrl : selected?.base_url ?? ""
  };
}

function orderFromStrategy(strategyLegs) {
  const leg = strategyLegs.find((item) => ["swap", "future", "basis", "paper"].includes(item.leg_type)) ?? strategyLegs[0];
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
  const hasPaper = legs.some((leg) => ["swap", "future", "basis", "paper"].includes(leg.leg_type));
  const targetTypes = new Set((caseData.target_actions ?? []).map((leg) => leg.leg_type));
  const matchedTypes = legs.filter((leg) => targetTypes.has(leg.leg_type)).length;
  const maxScore = rubric.reduce((sum, item) => sum + Number(item.points || 0), 0) || 100;
  let score = 0;
  if (hasPhysical) score += 25;
  if (hasPaper) score += 30;
  score += Math.min(25, matchedTypes * 8);
  if (/(basis|基差|spread|价差|fx|汇率|capacity|运力|limit|限额|liquidity|流动性)/i.test(text)) score += 20;
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
      paper_leg_count: legs.filter((leg) => ["swap", "future", "basis", "paper"].includes(leg.leg_type)).length,
      fx_leg_count: legs.filter((leg) => leg.leg_type === "fx").length,
      notional_usd: legs.reduce((sum, leg) => sum + (Number(leg.quantity) || 0) * (Number(leg.price) || 0), 0)
    }
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
    fullscreen: <path d="M8 4H4v4M16 4h4v4M20 16v4h-4M4 16v4h4" />,
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

function WindowControls({ locale }) {
  async function closeApp() {
    try {
      await appWindow.close();
    } catch {
      window.close();
    }
  }
  async function toggleFullscreen() {
    try {
      await appWindow.setFullscreen(!(await appWindow.isFullscreen()));
    } catch {
      // Browser preview fallback has no native window control.
    }
  }
  return (
    <div className="window-controls">
      <button title={t("toggleFullscreen", locale)} onClick={toggleFullscreen} type="button"><Icon name="fullscreen" /></button>
      <button title={t("close", locale)} onClick={closeApp} type="button"><Icon name="close" /></button>
    </div>
  );
}

function SettingsMenu({ aiReady, importing, locale, onCheckUpdate, onImportLocalSettings, onRestartGuide, onSaveSettings, providerStatus, saving, serviceMessage, setLocale, setTheme, theme, updateInfo }) {
  const catalog = providerCatalog(providerStatus);
  const fileInputRef = useRef(null);
  const [form, setForm] = useState(() => formForProvider(savedValue("commodity-lab-ai-provider", "haineng")));
  const [fileImportError, setFileImportError] = useState("");
  const provider = catalog[form.provider] ? form.provider : "haineng";
  const config = providerConfig(catalog, provider);
  const model = modelConfig(catalog, provider, form.model);

  function changeProvider(nextProvider) {
    setForm(formForProvider(nextProvider, catalog, form.api_key));
  }
  function changeModel(nextModel) {
    const next = modelConfig(catalog, provider, nextModel);
    setForm((current) => ({ ...current, model: nextModel, base_url: next?.base_url ?? current.base_url }));
  }
  async function importAiKeyFile(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    try {
      setFileImportError("");
      const text = await file.text();
      const importedForm = formFromAiKeyFile(text, catalog);
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
              <option value="dark">{t("darkMode", locale)}</option>
              <option value="light">{t("lightMode", locale)}</option>
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
            <label>
              {t("baseUrl", locale)}
              <input aria-label={t("baseUrl", locale)} value={form.base_url} placeholder={model?.base_url} onChange={(event) => setForm({ ...form, base_url: event.target.value })} />
            </label>
            <label>
              {t("model", locale)}
              <select aria-label={t("model", locale)} value={form.model} onChange={(event) => changeModel(event.target.value)}>
                {config.models.map((option) => <option key={option.id} value={option.id}>{option.label ?? option.id}</option>)}
              </select>
            </label>
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
            <label>{t("legType", locale)}<select value={leg.leg_type} onChange={(event) => updateLeg(index, { leg_type: event.target.value })}><option value="physical">{t("physicalLeg", locale)}</option><option value="swap">Swap</option><option value="future">Future</option><option value="basis">{t("basisLeg", locale)}</option><option value="fx">FX</option><option value="capacity">{t("capacityLeg", locale)}</option></select></label>
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

function LogoMark() {
  return (
    <span className="cl-logo-mark" aria-hidden="true">
      <Icon name="flame" />
    </span>
  );
}

function ProductTopbar({ activeCommodity, aiReady, locale, onCommodityChange, setLocale }) {
  return (
    <header className="cl-topbar">
      <div className="cl-brand">
        <LogoMark />
        <div>
          <strong>Commodity Lab</strong>
          <span>{copy(locale, "AI 驱动的大宗商品交易训练平台", "AI-powered commodity trading training lab")}</span>
        </div>
      </div>
      <nav className="cl-commodity-tabs" aria-label="Commodity">
        {commodityTabs.map((tab) => (
          <button
            className={tab.id === activeCommodity ? "active" : ""}
            key={tab.id}
            onClick={() => onCommodityChange(tab)}
            type="button"
          >
            <Icon name={tab.id === "natural-gas" ? "flame" : tab.id === "all" ? "grid" : "book"} />
            <span>{labelFor(locale, tab)}</span>
            {!tab.enabled ? <small>{copy(locale, "建设中", "Constructing")}</small> : null}
          </button>
        ))}
      </nav>
      <div className="cl-top-actions">
        <AiStatusBadge aiReady={aiReady} locale={locale} />
        <button className="cl-language-button" onClick={() => setLocale(locale === "zh" ? "en" : "zh")} type="button">
          <Icon name="globe" />
          <span>{locale === "zh" ? "中文" : "English"}</span>
        </button>
        <span className="cl-user-badge">AY</span>
        <WindowControls locale={locale} />
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
      <div className="cl-sidebar-spacer" />
      <section className="cl-data-notice">
        <Icon name="coach" />
        <strong>{copy(locale, "训练数据说明", "Training Data Notice")}</strong>
        <p>{copy(locale, "所有曲线、案例和评分规则均由 AI 生成，用于教学训练，不代表真实行情或交易建议。", "All curves, cases, and rubrics are AI-generated for training only. They are not live market data or trading advice.")}</p>
      </section>
      <button className={activePage === pageIds.settings ? "cl-settings-entry active" : "cl-settings-entry"} data-guide="settings-menu" onClick={() => onPageChange(pageIds.settings)} type="button">
        <Icon name="settings" />
        <span>{t("settings", locale)}</span>
      </button>
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

function HomePage({ activeTemplate, aiReady, caseData, evaluation, locale, onGenerate, onPageChange }) {
  const score = evaluation?.baseline_score ?? 72;
  return (
    <section className="cl-page cl-home-page">
      <PageTitle
        icon="home"
        locale={locale}
        titleZh="今天从哪里开始"
        titleEn="Where to start today"
        subtitleZh="按 AI 生成案例、训练进度和天然气业务知识点组织你的下一次练习。"
        subtitleEn="Your next session is organized by AI cases, progress, and natural gas hedging skills."
        action={<button className="cl-primary" onClick={() => onPageChange(pageIds.caseLab)} type="button"><Icon name="plus" />{copy(locale, "生成新案例", "Generate Case")}</button>}
      />
      <div className="cl-home-grid">
        <section className="cl-panel cl-hero-panel">
          <div>
            <span>{copy(locale, "推荐训练", "Recommended Training")}</span>
            <h3>{activeTemplate?.title ?? caseData.scenario?.title}</h3>
            <p>{caseData.scenario?.summary}</p>
          </div>
          <div className="cl-hero-actions">
            <button className="cl-primary" onClick={() => onGenerate(activeTemplate?.id ?? "procurement_beach_to_germany")} type="button"><Icon name="play" />{copy(locale, "继续训练", "Continue")}</button>
            <button className="cl-secondary" onClick={() => onPageChange(pageIds.knowledge)} type="button"><Icon name="map" />{copy(locale, "先看知识点", "Open Knowledge Map")}</button>
          </div>
        </section>
        <section className="cl-panel">
          <div className="cl-panel-heading"><span>{copy(locale, "能力快照", "Capability Snapshot")}</span><strong>{score}/100</strong></div>
          <div className="cl-progress-ring" style={{ "--score": `${score * 3.6}deg` }}>
            <strong>{score}</strong>
            <span>/100</span>
          </div>
          <p className="cl-muted">{copy(locale, "当前弱项：基差时机、汇率覆盖比例、运力弹性。", "Weak points: basis timing, FX hedge ratio, and capacity flexibility.")}</p>
        </section>
        <section className="cl-panel cl-quick-actions">
          <div className="cl-panel-heading"><span>{copy(locale, "AI 快捷入口", "AI Shortcuts")}</span><strong>{aiReady ? t("online", locale) : t("offline", locale)}</strong></div>
          {[
            [pageIds.caseLab, "sparkles", "按业务生成案例", "Generate by business scenario"],
            [pageIds.workbench, "workbench", "打开训练工作台", "Open training workbench"],
            [pageIds.coach, "coach", "询问 AI 教练", "Ask AI coach"],
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
            {(active?.knowledge_points ?? ["basis_spread", "physical_paper_matching"]).map((point) => <span key={point}>{point}</span>)}
          </div>
          <div className="cl-preview-facts">
            <span>{copy(locale, "将生成", "Will generate")}<strong>{copy(locale, "业务背景、曲线、事件、参考动作、评分规则", "Background, curves, events, target legs, rubric")}</strong></span>
            <span>{copy(locale, "数据性质", "Data type")}<strong>{t("aiGeneratedData", locale)}</strong></span>
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

function ScenarioLibraryPage({ activeTemplateId, locale, loadingTemplate, onGenerate, onPageChange }) {
  const [query, setQuery] = useState("");
  const filters = normalizeLocale(locale) === "zh"
    ? ["商品", "地区", "业务角色", "难度", "风险重点", "状态"]
    : ["Commodity", "Region", "Business Role", "Difficulty", "Risk Focus", "Status"];
  const visible = scenarioLibraryItems.filter((item) => {
    const text = `${item.titleZh} ${item.titleEn} ${item.summaryZh} ${item.summaryEn} ${item.tags.join(" ")}`.toLowerCase();
    return text.includes(query.trim().toLowerCase());
  });
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
            {visible.map((item) => (
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
                <span className="cl-progress-cell"><i style={{ "--pct": `${item.progress}%` }} /><b>{item.progress}%</b></span>
                <span className="cl-row-actions">
                  <button disabled={!item.enabled} onClick={() => onGenerate(activeTemplateId || item.id)} type="button">{item.progress ? copy(locale, "继续", "Continue") : copy(locale, "开始", "Start")}</button>
                  <button disabled={!item.enabled} onClick={() => onPageChange(pageIds.review)} type="button">{copy(locale, "复盘", "Review")}</button>
                </span>
              </article>
            ))}
          </div>
        </section>
        <aside className="cl-panel cl-library-side">
          <div className="cl-panel-heading"><span>{copy(locale, "我的集合与路径", "Collections & Paths")}</span><strong>{copy(locale, "查看全部", "View all")}</strong></div>
          {[
            ["我的收藏", "My Favorites", "12"],
            ["进阶交易路径", "Advanced Trading Path", "6"],
            ["风险管理专练", "Risk Management Drill", "8"],
            ["熊市模型专题", "Selloff Templates", "7"]
          ].map(([zh, en, count]) => <button key={en} type="button"><Icon name="star" /><span>{copy(locale, zh, en)}</span><small>{count}</small></button>)}
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
          <ul className="cl-mistake-list">
            {(evaluation?.mistake_tags?.length ? evaluation.mistake_tags : ["basis_timing", "capacity_optionality", "fx_hedge_ratio"]).map((tag) => <li key={tag}>{tag}</li>)}
          </ul>
        </section>
      </div>
    </section>
  );
}

function KnowledgeMapPage({ locale, onPageChange, runAiAction }) {
  const [selected, setSelected] = useState("basis");
  const node = knowledgeNodes.find((item) => item.id === selected) ?? knowledgeNodes[0];
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
        <div className="cl-path-row">{["Hub Pricing", "Basis & Spreads", "Capacity & Routing", "FX Hedge", "Integrated Hedge Design"].map((item, index) => <span key={item}><b>{index + 1}</b>{item}</span>)}</div>
      </section>
    </section>
  );
}

function ProgressPage({ evaluation, locale, onPageChange }) {
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
          <div className="cl-panel-heading"><span>{copy(locale, "能力画像", "Capability Profile")}</span><strong>{evaluation?.baseline_score ?? 72}/100</strong></div>
          <div className="cl-skill-bars">
            {progressDimensions.map(([id, zh, en, score]) => (
              <div key={id}>
                <span>{copy(locale, zh, en)}</span>
                <i><b style={{ width: `${score}%` }} /></i>
                <strong>{score}</strong>
              </div>
            ))}
          </div>
        </section>
        <section className="cl-panel">
          <div className="cl-panel-heading"><span>{copy(locale, "AI 推荐下一步", "AI Recommended Next Step")}</span><strong>{copy(locale, "基于弱项", "Based on weak points")}</strong></div>
          <h3>{copy(locale, "做一题英国上游 Beach Delivery 卖德国的下跌行情变体", "Practice a UK Beach Delivery to Germany selloff variant")}</h3>
          <p>{copy(locale, "重点训练基差方向、EUR/GBP 覆盖比例、运力弹性和执行窗口。", "Focus on basis direction, EUR/GBP hedge ratio, capacity flexibility, and execution window.")}</p>
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

function FloatingAssistant({ aiReady, applyAction, locale, messages, onSend, thinking }) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
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
          <header><div><span>{t("liveAssistant", locale)}</span><strong>{aiReady ? t("online", locale) : t("offline", locale)}</strong></div><button className="icon-button" onClick={() => setOpen(false)} type="button">×</button></header>
          <div className="assistant-messages">
            {messages.length ? messages.map((message, index) => (
              <article className={message.role} key={index}>
                <MarkdownText text={message.content} />
                {message.actions?.length ? <div className="assistant-actions">{message.actions.map((action, i) => <button key={i} onClick={() => applyAction(action)} type="button">{action.label ?? action.type}</button>)}</div> : null}
              </article>
            )) : <p className="empty-state">{t("assistantEmpty", locale)}</p>}
            {thinking ? <AiThinkingPanel locale={locale} titleKey="assistantWorking" /> : null}
          </div>
          <form onSubmit={submit}><textarea disabled={!aiReady || thinking} value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={t("assistantPlaceholder", locale)} /><button className="primary" disabled={!aiReady || thinking || !draft.trim()} type="submit">{thinking ? t("loading", locale) : t("send", locale)}</button></form>
        </section>
      ) : null}
      <button className="assistant-orb" onClick={() => setOpen((current) => !current)} type="button">AI</button>
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
  const [theme, setThemeState] = useState(() => savedValue("commodity-lab-theme", "dark"));
  const [backendReady, setBackendReady] = useState(false);
  const [startupStage, setStartupStage] = useState(startupStageKeys[0]);
  const [startupSlow, setStartupSlow] = useState(false);
  const [providerStatus, setProviderStatus] = useState(null);
  const [templates, setTemplates] = useState(fallbackTemplates);
  const [activeTemplateId, setActiveTemplateId] = useState(fallbackTemplates.templates[0].id);
  const [activePage, setActivePage] = useState(pageIds.home);
  const [activeCommodity, setActiveCommodity] = useState("natural-gas");
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
  const [guideIndex, setGuideIndex] = useState(() => savedValue("commodity-lab-guide-complete", "") ? -1 : 0);
  const aiReady = Boolean(providerStatus?.haineng?.ok);

  function setLocale(nextLocale) {
    localStorage.setItem("commodity-lab-locale", nextLocale);
    setLocaleState(nextLocale);
  }
  function setTheme(nextTheme) {
    localStorage.setItem("commodity-lab-theme", nextTheme);
    setThemeState(nextTheme);
  }
  function completeGuide() {
    localStorage.setItem("commodity-lab-guide-complete", "1");
    setGuideIndex(-1);
  }

  useEffect(() => {
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
    document.documentElement.dataset.theme = theme;
  }, [locale, theme]);

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
      .then(setProviderStatus)
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
      const payload = await backendRequest("POST", "/api/v1/provider-settings", form);
      localStorage.setItem("commodity-lab-ai-provider", form.provider);
      localStorage.setItem(`commodity-lab-${form.provider}-base-url`, form.base_url);
      localStorage.setItem(`commodity-lab-${form.provider}-model`, form.model);
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
      const payload = await backendRequest("POST", "/api/v1/provider-settings", form);
      const status = payload.haineng ?? {};
      if (status.provider) localStorage.setItem("commodity-lab-ai-provider", status.provider);
      if (status.base_url && status.provider) localStorage.setItem(`commodity-lab-${status.provider}-base-url`, status.base_url);
      if (status.model && status.provider) localStorage.setItem(`commodity-lab-${status.provider}-model`, status.model);
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
      const payload = await backendRequest("POST", "/api/v1/ai/training-case", { template_id: templateId, locale, user_request: userRequest });
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

  function handleCommodityChange(tab) {
    setActiveCommodity(tab.id);
    if (!tab.enabled) {
      setServiceMessage(copy(locale, `${labelFor(locale, tab)} 模块建设中，V1 先开放天然气训练。`, `${labelFor(locale, tab)} is under construction. V1 opens Natural Gas training first.`));
      setActiveCommodity("natural-gas");
    }
  }

  function buildAiPayload(capability) {
    return {
      capability,
      scenario_id: "europe_ttf_nbp_spread",
      locale,
      order: orderFromStrategy(strategyLegs),
      rationale,
      evaluation: evaluation ?? {},
      attempt_history: evaluation ? [evaluation] : [],
      market_context: { case: caseData, strategy_legs: strategyLegs },
      user_request: rationale,
      concept: "basis risk, physical-paper matching, FX hedge, EEX/OCM windows, LNG cargo risk",
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
      const payload = await backendRequest("POST", path, capability === "exam" ? { scenario_id: "europe_ttf_nbp_spread", locale, attempt_history: evaluation ? [evaluation] : [] } : buildAiPayload(capability));
      if (capability === "advisor_review") setAdvisorFeedback(payload.answer);
      else if (capability === "exam") setExam(payload.exam);
      else setAiOutput({ title: t(capability, locale), answer: payload.answer });
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
      const payload = await backendRequest("POST", "/api/v1/ai/live-assistant", {
        locale,
        message,
        workspace_state: { case: caseData, strategy_legs: strategyLegs, evaluation, active_template_id: activeTemplateId }
      });
      setAssistantMessages((current) => [...current, { role: "assistant", content: payload.answer, actions: payload.actions ?? [] }]);
    } catch (error) {
      setAssistantMessages((current) => [...current, { role: "assistant", content: formatErrorMessage(error, locale), actions: [] }]);
    } finally {
      setBusyAction("");
    }
  }

  function applyAssistantAction(action) {
    const payload = action.payload ?? {};
    if (action.type === "select_template" && payload.template_id) generateTrainingCase(payload.template_id);
    if (action.type === "set_chart_fields" && Array.isArray(payload.fields)) setFieldSelection(payload.fields.filter((field) => chartFields.includes(field)));
    if (action.type === "set_strategy_legs" && Array.isArray(payload.legs)) setStrategyLegs(payload.legs.map((leg, index) => ({ id: leg.id ?? `assistant-leg-${index}`, ...leg })));
    if (action.type === "fill_rationale" && payload.text) setRationale(payload.text);
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
      return <ScenarioLibraryPage activeTemplateId={activeTemplateId} locale={locale} loadingTemplate={loadingTemplate} onGenerate={generateTrainingCase} onPageChange={setActivePage} />;
    }
    if (activePage === pageIds.knowledge) {
      return <KnowledgeMapPage locale={locale} onPageChange={setActivePage} runAiAction={runAiAction} />;
    }
    if (activePage === pageIds.progress) {
      return <ProgressPage evaluation={evaluation} locale={locale} onPageChange={setActivePage} />;
    }
    if (activePage === pageIds.coach) {
      return <AiCoachPage aiReady={aiReady} applyAction={applyAssistantAction} locale={locale} messages={assistantMessages} onSend={sendAssistant} thinking={busyAction === "assistant"} />;
    }
    if (activePage === pageIds.settings) {
      return <SettingsPage locale={locale} settingsPanel={settingsPanel} />;
    }
    return <HomePage activeTemplate={activeTemplate} aiReady={aiReady} caseData={caseData} evaluation={evaluation} locale={locale} onGenerate={generateTrainingCase} onPageChange={setActivePage} />;
  }

  if (!backendReady) {
    return <StartupScreen locale={locale} slow={startupSlow} stageKey={startupStage} />;
  }

  return (
    <main className={aiReady ? "app-shell cl-app-shell ai-ready" : "app-shell cl-app-shell"}>
      <ProductTopbar activeCommodity={activeCommodity} aiReady={aiReady} locale={locale} onCommodityChange={handleCommodityChange} setLocale={setLocale} />

      <div className="cl-app-layout">
        <ProductSidebar activePage={activePage} locale={locale} onPageChange={setActivePage} />
        <section className="cl-content-shell">
          {generationStages.length && busyAction === "case_generation" ? <GenerationTimeline locale={locale} stages={generationStages} /> : null}
          {serviceMessage && activePage !== pageIds.settings ? <p className="cl-service-banner">{serviceMessage}</p> : null}
          {renderActivePage()}
        </section>
      </div>

      <FloatingAssistant aiReady={aiReady} applyAction={applyAssistantAction} locale={locale} messages={assistantMessages} onSend={sendAssistant} thinking={busyAction === "assistant"} />

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
