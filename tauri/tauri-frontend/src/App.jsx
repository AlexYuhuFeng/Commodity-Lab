import React, { useEffect, useMemo, useRef, useState } from "react";
import { appWindow } from "@tauri-apps/api/window";
import { backendRequest } from "./api";
import { normalizeLocale, t } from "./i18n";

const currentVersion = "1.0.10";

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
  ["business-sidebar", "guideBusinessTitle", "guideBusinessBody"],
  ["case-workspace", "guideCaseTitle", "guideCaseBody"],
  ["market-chart", "guideChartTitle", "guideChartBody"],
  ["strategy-builder", "guideStrategyTitle", "guideStrategyBody"],
  ["floating-assistant", "guideAssistantTitle", "guideAssistantBody"]
];

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
    close: <path d="M6 6l12 12M18 6L6 18" />,
    fullscreen: <path d="M8 4H4v4M16 4h4v4M20 16v4h-4M4 16v4h4" />,
    settings: (
      <>
        <path d="M12 8.4A3.6 3.6 0 1 0 12 15.6A3.6 3.6 0 0 0 12 8.4Z" />
        <path d="M19.4 15a1.9 1.9 0 0 0 .38 2.1l.04.04a2.2 2.2 0 0 1-3.11 3.11l-.04-.04a1.9 1.9 0 0 0-2.1-.38 1.9 1.9 0 0 0-1.15 1.74V22a2.2 2.2 0 0 1-4.4 0v-.06a1.9 1.9 0 0 0-1.24-1.74 1.9 1.9 0 0 0-2.1.38l-.04.04a2.2 2.2 0 0 1-3.11-3.11l.04-.04a1.9 1.9 0 0 0 .38-2.1 1.9 1.9 0 0 0-1.74-1.15H2a2.2 2.2 0 0 1 0-4.4h.06A1.9 1.9 0 0 0 3.8 8.6a1.9 1.9 0 0 0-.38-2.1l-.04-.04a2.2 2.2 0 0 1 3.11-3.11l.04.04a1.9 1.9 0 0 0 2.1.38h.02A1.9 1.9 0 0 0 9.8 2.06V2a2.2 2.2 0 0 1 4.4 0v.06a1.9 1.9 0 0 0 1.15 1.74 1.9 1.9 0 0 0 2.1-.38l.04-.04a2.2 2.2 0 0 1 3.11 3.11l-.04.04a1.9 1.9 0 0 0-.38 2.1v.02A1.9 1.9 0 0 0 21.94 9.8H22a2.2 2.2 0 0 1 0 4.4h-.06A1.9 1.9 0 0 0 19.4 15Z" />
      </>
    )
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
  const [settingsOpen, setSettingsOpen] = useState(false);
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
      return;
    }
    setLoadingTemplate(templateId);
    setBusyAction("case_generation");
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

  if (!backendReady) {
    return <StartupScreen locale={locale} slow={startupSlow} stageKey={startupStage} />;
  }

  return (
    <main className={aiReady ? "app-shell ai-ready" : "app-shell"}>
      <header className="topbar">
        <div>
          <p>{t("appKicker", locale)}</p>
          <h1>{t("appTitle", locale)}</h1>
        </div>
        <div className="topbar-actions">
          <AiStatusBadge aiReady={aiReady} locale={locale} />
          <span className="active-template">{activeTemplate?.title ?? t("noCase", locale)}</span>
          <WindowControls locale={locale} />
        </div>
      </header>

      <div className="workbench-layout">
        <BusinessNavigator
          activeTemplateId={activeTemplateId}
          businessTemplates={templates}
          settingsOpen={settingsOpen}
          settingsPanel={(
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
          )}
          footer={<SettingsToggle locale={locale} onClick={() => setSettingsOpen((current) => !current)} open={settingsOpen} />}
          generateTrainingCase={generateTrainingCase}
          loadingTemplate={loadingTemplate}
          locale={locale}
        />

        <section className="workspace-main">
          <CaseWorkspace caseData={caseData} generationStages={generationStages} locale={locale} />
          <div className="workspace-grid">
            <MarketChart caseData={caseData} fieldSelection={fieldSelection} locale={locale} setFieldSelection={setFieldSelection} strategyLegs={strategyLegs} />
            <StrategyBuilder busy={busyAction === "evaluate"} locale={locale} onSubmit={submitStrategy} rationale={rationale} setRationale={setRationale} setStrategyLegs={setStrategyLegs} strategyLegs={strategyLegs} />
            <ScorePanel evaluation={evaluation} locale={locale} />
            <RubricPanel caseData={caseData} locale={locale} />
          </div>
        </section>

        <AdvisorRail aiOutput={aiOutput} aiReady={aiReady} advisorFeedback={advisorFeedback} busyAction={busyAction} error={serviceMessage && busyAction !== "provider" ? serviceMessage : ""} evaluation={evaluation} exam={exam} locale={locale} runAiAction={runAiAction} />
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
