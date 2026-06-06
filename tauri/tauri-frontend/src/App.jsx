import React, { useEffect, useMemo, useState } from "react";
import { backendRequest } from "./api";
import { normalizeLocale, t } from "./i18n";

const defaultOrder = {
  side: "sell",
  quantity: 60000,
  hedge_type: "short_hedge",
  price: 3.5
};

const sourceOptions = [
  { id: "yfinance", labelKey: "yahooFinance" },
  { id: "sample", labelKey: "simulated" },
  { id: "platts", labelKey: "platts" }
];

const aiActionButtons = [
  { capability: "advisor_review", labelKey: "askHint", requiresEvaluation: true },
  { capability: "socratic_coach", labelKey: "socraticCoach" },
  { capability: "case_generation", labelKey: "generateCase" },
  { capability: "event_drill", labelKey: "eventDrill" },
  { capability: "concept_tutor", labelKey: "conceptTutor" },
  { capability: "trade_playbook", labelKey: "tradePlaybook" },
  { capability: "exam", labelKey: "generateExam" }
];

const aiModelOptions = [
  { value: "V4-Flash", labelKey: "v4Flash" },
  { value: "V4-Pro", labelKey: "v4Pro" }
];

const aiThinkingStepKeys = [
  "thinkingReadContext",
  "thinkingCheckMarket",
  "thinkingBuildPrompt",
  "thinkingWaitModel",
  "thinkingAssemble"
];

function savedValue(key, fallback = "") {
  if (typeof localStorage === "undefined") return fallback;
  return localStorage.getItem(key) ?? fallback;
}

function formatNumber(value, digits = 0) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits
  }).format(number);
}

function formatMoney(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
    style: "currency",
    currency: "USD"
  }).format(number);
}

function optionLabel(value, locale) {
  const labels = {
    buy: t("buy", locale),
    sell: t("sell", locale),
    short_hedge: t("shortHedge", locale),
    long_hedge: t("longHedge", locale),
    basis_hedge: t("basisHedge", locale),
    calendar_spread: t("calendarSpread", locale)
  };
  return labels[value] ?? value;
}

function capabilityLabel(capability, locale) {
  const titleKey = aiActionButtons.find((action) => action.capability === capability)?.labelKey ?? "aiCoach";
  return t(titleKey, locale);
}

function formatErrorMessage(error, locale) {
  const raw = typeof error === "string" ? error : error?.message ?? "";
  if (!raw) return t("serviceIssue", locale);

  try {
    const jsonStart = raw.indexOf("{");
    if (jsonStart >= 0) {
      const payload = JSON.parse(raw.slice(jsonStart));
      const detail = payload.detail ?? payload;
      if (detail.provider_message) return detail.provider_message;
      if (detail.message) return detail.message;
    }
  } catch {
    // Keep the raw provider/runtime message when backend errors are not JSON.
  }

  return raw.replace(/^backend status \d+:\s*/i, "");
}

function LanguageToggle({ locale, setLocale }) {
  return (
    <div className="segmented" aria-label="Language">
      <button className={locale === "en" ? "active" : ""} onClick={() => setLocale("en")} type="button">
        EN
      </button>
      <button className={locale === "zh" ? "active" : ""} onClick={() => setLocale("zh")} type="button">
        中文
      </button>
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

function DataSourceStrip({ locale, sources = [], activeSource }) {
  const sourceRows = sources.length
    ? sources
    : [
        { id: "yfinance", label: "Yahoo Finance", configured: true },
        { id: "simulated", label: "Simulated", configured: true },
        { id: "platts", label: "Platts", configured: false }
      ];

  return (
    <div className="source-strip" aria-label={t("dataSources", locale)}>
      {sourceRows.map((source) => (
        <span
          className={
            source.id === activeSource || (source.id === "simulated" && activeSource === "sample")
              ? "source-pill active"
              : "source-pill"
          }
          key={source.id}
        >
          <strong>{source.label}</strong>
          <small>{source.configured ? t("configured", locale) : t("notConfigured", locale)}</small>
        </span>
      ))}
    </div>
  );
}

function AiActivationPanel({ aiReady, locale, onSaveSettings, providerStatus, saving, message }) {
  const [form, setForm] = useState({
    api_key: "",
    base_url: savedValue("commodity-lab-haineng-base-url", ""),
    model: savedValue("commodity-lab-haineng-model", "V4-Flash")
  });

  async function submit(event) {
    event.preventDefault();
    await onSaveSettings(form);
    setForm((current) => ({ ...current, api_key: "" }));
  }

  return (
    <details className={aiReady ? "ai-activation online" : "ai-activation"} open={!aiReady}>
      <summary>
        <div className="ai-activation-copy">
          <p>{aiReady ? t("aiConnected", locale) : t("connectAi", locale)}</p>
          <h2>{t("aiSettings", locale)}</h2>
          <span>{aiReady ? t("aiUnlockedCompact", locale) : t("aiLockedSubtitle", locale)}</span>
        </div>
        <div className="provider-summary">
          <span>
            {t("model", locale)}
            <strong>{providerStatus?.haineng?.resolved_model ?? form.model}</strong>
          </span>
          <span>
            {t("status", locale)}
            <strong>{aiReady ? t("online", locale) : t("offline", locale)}</strong>
          </span>
        </div>
        <span className="disclosure-label">{t("configure", locale)}</span>
      </summary>
      <form className="setup-form compact" onSubmit={submit}>
        <label>
          {t("apiKey", locale)}
          <input
            aria-label={t("apiKey", locale)}
            autoComplete="off"
            onChange={(event) => setForm({ ...form, api_key: event.target.value })}
            placeholder={aiReady ? "********" : t("enterKeyToUnlock", locale)}
            type="password"
            value={form.api_key}
          />
        </label>
        <label>
          {t("baseUrl", locale)}
          <input
            aria-label={t("baseUrl", locale)}
            onChange={(event) => setForm({ ...form, base_url: event.target.value })}
            placeholder="http://127.0.0.1:8001/v1"
            value={form.base_url}
          />
        </label>
        <label>
          {t("model", locale)}
          <select
            aria-label={t("model", locale)}
            onChange={(event) => setForm({ ...form, model: event.target.value })}
            value={form.model}
          >
            {aiModelOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {t(option.labelKey, locale)}
              </option>
            ))}
          </select>
        </label>
        <button className="primary" disabled={saving} type="submit">
          {saving ? t("loading", locale) : aiReady ? t("refreshAi", locale) : t("unlockAi", locale)}
        </button>
      </form>
      {message ? <div className={aiReady ? "status-line ok" : "status-line warn"}>{message}</div> : null}
    </details>
  );
}

function CategoryTabs({ categories, locale }) {
  return (
    <nav className="category-tabs" aria-label={t("futureModules", locale)}>
      {categories.map((category) => (
        <button
          className={category.status === "enabled" ? "category-tab active" : "category-tab"}
          disabled={category.status !== "enabled"}
          key={category.id}
          title={category.description}
          type="button"
        >
          <span>{category.label}</span>
          {category.status !== "enabled" ? <small>{t("constructing", locale)}</small> : null}
        </button>
      ))}
    </nav>
  );
}

function ScenarioDeck({ scenarios, selectedId, setSelectedId }) {
  return (
    <div className="scenario-list">
      {scenarios.map((scenario) => (
        <button
          className={scenario.id === selectedId ? "scenario-row active" : "scenario-row"}
          key={scenario.id}
          onClick={() => setSelectedId(scenario.id)}
          type="button"
        >
          <em>{scenario.region_label}</em>
          <strong>{scenario.title}</strong>
          <span>{scenario.summary}</span>
        </button>
      ))}
    </div>
  );
}

function SourceSelector({ locale, source, setSource, market }) {
  return (
    <label className="compact-label">
      {t("sourceSelect", locale)}
      <select aria-label={t("sourceSelect", locale)} onChange={(event) => setSource(event.target.value)} value={source}>
        {sourceOptions.map((option) => (
          <option key={option.id} value={option.id}>
            {t(option.labelKey, locale)}
          </option>
        ))}
      </select>
      {market ? (
        <span className="source-meta">
          {t("requestedSource", locale)}: {market.source_label} / {t("returnedSource", locale)}: {market.data_source_label}
        </span>
      ) : null}
    </label>
  );
}

function MarketChart({ locale, market, source, setSource }) {
  const points = market?.price_series ?? [];
  const closes = points.map((point) => Number(point.close)).filter(Number.isFinite);
  const min = closes.length ? Math.min(...closes) : 0;
  const max = closes.length ? Math.max(...closes) : 1;
  const first = closes[0] ?? 0;
  const last = closes[closes.length - 1] ?? market?.latest_price ?? 0;
  const delta = last - first;
  const range = Math.max(max - min, 0.01);
  const chartWidth = 620;
  const chartHeight = 210;
  const padX = 28;
  const padTop = 20;
  const padBottom = 34;
  const plotWidth = chartWidth - padX * 2;
  const plotHeight = chartHeight - padTop - padBottom;
  const xFor = (index) => padX + (points.length <= 1 ? 0 : (index / (points.length - 1)) * plotWidth);
  const yFor = (close) => padTop + ((max - Number(close)) / range) * plotHeight;
  const linePath = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${xFor(index).toFixed(1)} ${yFor(point.close).toFixed(1)}`)
    .join(" ");
  const areaPath = linePath ? `${linePath} L ${padX + plotWidth} ${padTop + plotHeight} L ${padX} ${padTop + plotHeight} Z` : "";
  const latestX = points.length ? xFor(points.length - 1) : padX;
  const latestY = points.length ? yFor(points[points.length - 1].close) : padTop + plotHeight;

  return (
    <section className="panel market-panel">
      <div className="panel-title">
        <span>{t("marketContext", locale)}</span>
        <strong>{market?.symbol ?? "NG=F"}</strong>
      </div>
      <SourceSelector locale={locale} market={market} setSource={setSource} source={source} />
      <div className="price-chart-wrap">
        <svg className={delta >= 0 ? "price-chart up" : "price-chart down"} role="img" aria-label={t("priceChart", locale)} viewBox={`0 0 ${chartWidth} ${chartHeight}`}>
          <line className="grid-line" x1={padX} x2={padX + plotWidth} y1={padTop} y2={padTop} />
          <line className="grid-line" x1={padX} x2={padX + plotWidth} y1={padTop + plotHeight / 2} y2={padTop + plotHeight / 2} />
          <line className="grid-line baseline" x1={padX} x2={padX + plotWidth} y1={padTop + plotHeight} y2={padTop + plotHeight} />
          {areaPath ? <path className="price-area" d={areaPath} /> : null}
          {linePath ? <path className="price-line" d={linePath} /> : null}
          <circle className="latest-dot" cx={latestX} cy={latestY} r="5" />
          <text className="axis-label" x={padX} y={padTop + 12}>{formatNumber(max, 2)}</text>
          <text className="axis-label" x={padX} y={padTop + plotHeight - 6}>{formatNumber(min, 2)}</text>
          <text className="latest-label" x={Math.max(padX + 88, latestX - 82)} y={Math.max(28, latestY - 14)}>
            {formatNumber(last, 2)}
          </text>
          {points[0]?.date ? <text className="date-label" x={padX} y={chartHeight - 10}>{points[0].date}</text> : null}
          {points.at(-1)?.date ? <text className="date-label end" x={padX + plotWidth} y={chartHeight - 10}>{points.at(-1).date}</text> : null}
        </svg>
      </div>
      <div className="metric-strip compact-metrics">
        <span>
          {t("latestPrice", locale)}
          <strong>{formatNumber(market?.latest_price, 2)}</strong>
        </span>
        <span>
          {t("latestMove", locale)}
          <strong className={delta >= 0 ? "positive" : "negative"}>{delta >= 0 ? "+" : ""}{formatNumber(delta, 2)}</strong>
        </span>
        <span>
          {t("dataSource", locale)}
          <strong>{market?.data_source_label ?? t("simulated", locale)}</strong>
        </span>
      </div>
    </section>
  );
}

function CapacityDiagram({ locale, capacity }) {
  const utilization = Number(capacity?.utilization_pct ?? 0);
  const width = Math.min(100, Math.max(0, utilization));

  return (
    <section className="panel capacity-panel">
      <div className="panel-title">
        <span>{t("routeAndCapacity", locale)}</span>
        <strong>{capacity?.congestion_status ?? "--"}</strong>
      </div>
      <div className="flow-line">
        <span>
          <small>{t("receipt", locale)}</small>
          {capacity?.receipt_point ?? "--"}
        </span>
        <div className="pipe-track">
          <i style={{ width: `${width}%` }} />
        </div>
        <span>
          <small>{t("delivery", locale)}</small>
          {capacity?.delivery_point ?? "--"}
        </span>
      </div>
      <div className="metric-strip">
        <span>
          {t("availableCapacity", locale)}
          <strong>{formatNumber(capacity?.available_capacity_mmbtu)} MMBtu</strong>
        </span>
        <span>
          {t("nominations", locale)}
          <strong>{formatNumber(capacity?.nominated_mmbtu)} MMBtu</strong>
        </span>
        <span>
          {t("capacityUtilization", locale)}
          <strong>{formatNumber(utilization, 1)}%</strong>
        </span>
      </div>
    </section>
  );
}

function ExposurePanel({ locale, scenario }) {
  const exposure = scenario?.exposure ?? {};

  return (
    <section className="panel exposure-panel">
      <div className="panel-title">
        <span>{t("exposure", locale)}</span>
        <strong>{scenario?.region_label ?? "--"}</strong>
      </div>
      <div className="exposure-grid">
        <span>
          {t("direction", locale)}
          <strong>{exposure.direction ?? "--"}</strong>
        </span>
        <span>
          {t("quantity", locale)}
          <strong>{formatNumber(exposure.volume_mmbtu)} MMBtu</strong>
        </span>
        <span>
          {t("hedgePlan", locale)}
          <strong>{optionLabel(scenario?.recommended_hedge_type, locale)}</strong>
        </span>
        <span>
          {t("instrument", locale)}
          <strong>{scenario?.default_symbol ?? "--"}</strong>
        </span>
      </div>
      <p className="teaching-note">{exposure.risk}</p>
    </section>
  );
}

function TrainingGuide({ locale, scenario }) {
  const steps = scenario?.guided_steps ?? [];
  return (
    <section className="panel training-guide">
      <div className="panel-title">
        <span>{t("learningPath", locale)}</span>
        <strong>{t("guided", locale)}</strong>
      </div>
      <ol className="guide-list">
        {steps.map((step) => (
          <li key={step.id}>
            <strong>{step.label}</strong>
            <span>{step.description}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

function OrderTicket({ locale, order, setOrder, rationale, setRationale, onSubmit, busy }) {
  return (
    <section className="panel order-ticket">
      <div className="panel-title">
        <span>{t("orderTicket", locale)}</span>
        <strong>{t("decisionLab", locale)}</strong>
      </div>
      <div className="ticket-grid">
        <label>
          {t("side", locale)}
          <select value={order.side} onChange={(event) => setOrder({ ...order, side: event.target.value })}>
            <option value="sell">{t("sell", locale)}</option>
            <option value="buy">{t("buy", locale)}</option>
          </select>
        </label>
        <label>
          {t("quantity", locale)}
          <input min="0" onChange={(event) => setOrder({ ...order, quantity: Number(event.target.value) })} type="number" value={order.quantity} />
        </label>
        <label>
          {t("hedgeType", locale)}
          <select value={order.hedge_type} onChange={(event) => setOrder({ ...order, hedge_type: event.target.value })}>
            <option value="short_hedge">{t("shortHedge", locale)}</option>
            <option value="long_hedge">{t("longHedge", locale)}</option>
            <option value="basis_hedge">{t("basisHedge", locale)}</option>
            <option value="calendar_spread">{t("calendarSpread", locale)}</option>
          </select>
        </label>
        <label>
          {t("price", locale)}
          <input min="0" onChange={(event) => setOrder({ ...order, price: Number(event.target.value) })} step="0.01" type="number" value={order.price} />
        </label>
      </div>
      <label>
        {t("rationale", locale)}
        <textarea onChange={(event) => setRationale(event.target.value)} value={rationale} />
      </label>
      <button className="primary" disabled={busy} onClick={onSubmit} type="button">
        {busy ? t("loading", locale) : t("submitOrder", locale)}
      </button>
    </section>
  );
}

function ScorePanel({ locale, evaluation }) {
  const metrics = evaluation?.metrics ?? {};
  const mistakes = evaluation?.mistake_tags ?? [];

  return (
    <section className="panel score-panel">
      <div className="panel-title">
        <span>{t("reviewScore", locale)}</span>
        <strong>{t("deterministicCore", locale)}</strong>
      </div>
      <div className="score-readout">{evaluation?.baseline_score ?? "--"}</div>
      <div className="metric-strip">
        <span>
          {t("hedgeRatio", locale)}
          <strong>{formatNumber(metrics.hedge_ratio, 2)}</strong>
        </span>
        <span>
          {t("notional", locale)}
          <strong>{metrics.notional_usd ? formatMoney(metrics.notional_usd) : "--"}</strong>
        </span>
        <span>
          {t("mistakes", locale)}
          <strong>{mistakes.length ? mistakes.join(", ") : t("noMistakes", locale)}</strong>
        </span>
      </div>
    </section>
  );
}

function GuidedStepper({ locale, evaluation, aiReady }) {
  const steps = ["understandExposure", "inspectMarket", "placeHedge", "reviewScore", "exam"];
  const activeIndex = evaluation ? (aiReady ? 4 : 3) : 2;

  return (
    <ol className="stepper">
      {steps.map((step, index) => (
        <li className={index <= activeIndex ? "active" : ""} key={step}>
          {t(step, locale)}
        </li>
      ))}
    </ol>
  );
}

function LearningJourneyPanel({ journey, locale }) {
  const recommendations = journey?.recommendations ?? [];
  const attemptCount = journey?.profile?.attempt_count ?? 0;

  return (
    <div className="journey-panel">
      <div className="journey-summary">
        <span>
          {t("attemptCount", locale)}
          <strong>{formatNumber(attemptCount)}</strong>
        </span>
        <span>
          {t("skillFocus", locale)}
          <strong>{recommendations[0]?.skill_id ?? "--"}</strong>
        </span>
      </div>
      <div className="recommendation-list">
        {recommendations.length ? (
          recommendations.map((item) => (
            <article key={`${item.scenario_id}-${item.skill_id}`}>
              <span>{item.ai_capability}</span>
              <strong>{item.title}</strong>
              <p>{item.reason}</p>
            </article>
          ))
        ) : (
          <p className="empty-state">{t("noRecommendations", locale)}</p>
        )}
      </div>
    </div>
  );
}

function AiThinkingPanel({ aiThinking, busyAction, locale }) {
  const active = Boolean(aiThinking && busyAction && busyAction !== "provider" && busyAction !== "evaluate");
  const stepIndex = aiThinking?.stepIndex ?? 0;

  return (
    <section className={active ? "thinking-panel active" : "thinking-panel"} aria-live="polite">
      <div className="panel-title compact-title">
        <span>{active ? t("aiThinkingTitle", locale) : t("aiThinkingIdle", locale)}</span>
        <strong>{aiThinking?.capability ? capabilityLabel(aiThinking.capability, locale) : t("standby", locale)}</strong>
      </div>
      <ol className="thinking-steps">
        {aiThinkingStepKeys.map((key, index) => (
          <li className={active && index <= stepIndex ? "active" : ""} key={key}>
            <i />
            <span>{t(key, locale)}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

function AdvisorRail({ aiOutput, aiReady, advisorFeedback, aiThinking, busyAction, error, evaluation, exam, journey, locale, runAiAction }) {
  return (
    <aside className={aiReady ? "advisor-rail online" : "advisor-rail"}>
      <div className="advisor-head">
        <span>{t("aiCoach", locale)}</span>
        <strong>{aiReady ? t("online", locale) : t("offline", locale)}</strong>
      </div>
      <GuidedStepper aiReady={aiReady} evaluation={evaluation} locale={locale} />
      <AiThinkingPanel aiThinking={aiThinking} busyAction={busyAction} locale={locale} />
      <CollapsiblePanel defaultOpen title={t("aiTrainingActions", locale)} meta={aiReady ? t("enabled", locale) : t("connectToEnable", locale)}>
        <div className="ai-action-grid">
          {aiActionButtons.map((action) => (
            <button
              className={busyAction === action.capability ? "active" : ""}
              disabled={Boolean(busyAction) || !aiReady || (action.requiresEvaluation && !evaluation)}
              key={action.capability}
              onClick={() => runAiAction(action.capability)}
              type="button"
            >
              {busyAction === action.capability ? t("loading", locale) : t(action.labelKey, locale)}
            </button>
          ))}
        </div>
      </CollapsiblePanel>
      <CollapsiblePanel defaultOpen={Boolean(advisorFeedback || exam || aiOutput?.answer || error)} title={t("aiTrainingOutput", locale)} meta={t("outputReady", locale)}>
        {!aiReady ? <p className="service-error muted">{t("aiDisabledHint", locale)}</p> : null}
        {error ? <p className="service-error">{error}</p> : null}
        {advisorFeedback ? (
          <section className="response-block">
            <h3>{t("advisorFeedback", locale)}</h3>
            <p>{advisorFeedback}</p>
          </section>
        ) : null}
        {exam ? (
          <section className="response-block">
            <h3>{t("examQuestions", locale)}</h3>
            <p>{exam}</p>
          </section>
        ) : null}
        {aiOutput?.answer ? (
          <section className="response-block">
            <h3>{aiOutput.title}</h3>
            <p>{aiOutput.answer}</p>
          </section>
        ) : null}
      </CollapsiblePanel>
      <CollapsiblePanel title={t("learningRecommendations", locale)} meta={t("journeyReady", locale)}>
        <LearningJourneyPanel journey={journey} locale={locale} />
      </CollapsiblePanel>
    </aside>
  );
}

export default function App() {
  const [locale, setLocaleState] = useState(() => normalizeLocale(savedValue("commodity-lab-locale", "zh")));
  const [providerStatus, setProviderStatus] = useState(null);
  const [categories, setCategories] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [context, setContext] = useState(null);
  const [journey, setJourney] = useState(null);
  const [source, setSource] = useState("yfinance");
  const [order, setOrder] = useState(defaultOrder);
  const [rationale, setRationale] = useState("Manage the energy exposure with a hedge that matches the risk driver, timing, and volume.");
  const [evaluation, setEvaluation] = useState(null);
  const [advisorFeedback, setAdvisorFeedback] = useState("");
  const [exam, setExam] = useState("");
  const [aiOutput, setAiOutput] = useState(null);
  const [aiThinking, setAiThinking] = useState(null);
  const [busyAction, setBusyAction] = useState("");
  const [serviceMessage, setServiceMessage] = useState("");

  const aiReady = Boolean(providerStatus?.haineng?.ok);

  function setLocale(nextLocale) {
    localStorage.setItem("commodity-lab-locale", nextLocale);
    setLocaleState(nextLocale);
  }

  function startAiThinking(capability) {
    setAiThinking({ capability, stepIndex: 0 });
  }

  function finishAiThinking() {
    setAiThinking((current) => (current ? { ...current, stepIndex: aiThinkingStepKeys.length - 1 } : current));
  }

  useEffect(() => {
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
  }, [locale]);

  useEffect(() => {
    if (!aiThinking || !busyAction || busyAction === "provider" || busyAction === "evaluate") return undefined;
    const timer = window.setInterval(() => {
      setAiThinking((current) => {
        if (!current) return current;
        return { ...current, stepIndex: Math.min(current.stepIndex + 1, aiThinkingStepKeys.length - 1) };
      });
    }, 900);
    return () => window.clearInterval(timer);
  }, [aiThinking, busyAction]);

  useEffect(() => {
    let active = true;
    backendRequest("GET", "/api/v1/provider-status")
      .then((payload) => {
        if (active) setProviderStatus(payload);
      })
      .catch((error) => {
        if (!active) return;
        setProviderStatus({ haineng: { ok: false, configured: false }, data_sources: [] });
        setServiceMessage(formatErrorMessage(error, locale));
      });
    return () => {
      active = false;
    };
  }, [locale]);

  useEffect(() => {
    let active = true;
    backendRequest("GET", `/api/v1/scenarios?locale=${locale}`)
      .then((payload) => {
        if (!active) return;
        const nextScenarios = payload.scenarios ?? [];
        setCategories(payload.categories ?? []);
        setScenarios(nextScenarios);
        setSelectedId((current) => (nextScenarios.some((scenario) => scenario.id === current) ? current : nextScenarios[0]?.id ?? ""));
      })
      .catch((error) => setServiceMessage(formatErrorMessage(error, locale)));
    return () => {
      active = false;
    };
  }, [locale]);

  useEffect(() => {
    let active = true;
    backendRequest("GET", `/api/v1/learning-journey?locale=${locale}`)
      .then((payload) => {
        if (active) setJourney(payload);
      })
      .catch(() => {
        if (active) setJourney(null);
      });
    return () => {
      active = false;
    };
  }, [locale]);

  useEffect(() => {
    if (!selectedId) return undefined;
    let active = true;
    setContext(null);
    backendRequest("GET", `/api/v1/scenarios/${selectedId}/context?locale=${locale}&source=${source}`)
      .then((payload) => {
        if (!active) return;
        setContext(payload);
        setEvaluation(null);
        setAdvisorFeedback("");
        setExam("");
        setAiOutput(null);
      })
      .catch((error) => setServiceMessage(formatErrorMessage(error, locale)));
    return () => {
      active = false;
    };
  }, [selectedId, locale, source]);

  const selectedScenario = useMemo(() => context?.scenario ?? scenarios.find((scenario) => scenario.id === selectedId), [context?.scenario, scenarios, selectedId]);

  async function saveProviderSettings(form) {
    setBusyAction("provider");
    setServiceMessage("");
    try {
      const payload = await backendRequest("POST", "/api/v1/provider-settings", form);
      localStorage.setItem("commodity-lab-haineng-base-url", form.base_url);
      localStorage.setItem("commodity-lab-haineng-model", form.model);
      setProviderStatus((current) => ({ ...(current ?? {}), ...payload }));
      setServiceMessage(t("providerSaved", locale));
    } catch (error) {
      setServiceMessage(formatErrorMessage(error, locale) || t("providerSaveFailed", locale));
    } finally {
      setBusyAction("");
    }
  }

  async function requestAdvisorReview(nextEvaluation = evaluation) {
    if (!nextEvaluation || !selectedId || !aiReady) return;
    setBusyAction("advisor_review");
    startAiThinking("advisor_review");
    setServiceMessage("");
    try {
      const payload = await backendRequest("POST", "/api/v1/advisor/review", {
        scenario_id: selectedId,
        locale,
        order,
        rationale,
        evaluation: nextEvaluation
      });
      setAdvisorFeedback(payload.answer);
      setAiOutput(null);
      finishAiThinking();
    } catch (error) {
      setServiceMessage(formatErrorMessage(error, locale));
    } finally {
      setBusyAction("");
    }
  }

  async function submitOrder() {
    if (!selectedId) return;
    setBusyAction("evaluate");
    setServiceMessage("");
    try {
      const payload = await backendRequest("POST", "/api/v1/attempts/evaluate", {
        scenario_id: selectedId,
        locale,
        order,
        rationale
      });
      setEvaluation(payload.evaluation);
      setAiOutput(null);
      if (payload.journey) {
        setJourney(payload.journey);
      }
      if (payload.evaluation?.valid && aiReady) {
        await requestAdvisorReview(payload.evaluation);
      }
    } catch (error) {
      setServiceMessage(formatErrorMessage(error, locale));
    } finally {
      setBusyAction("");
    }
  }

  async function generateExam() {
    if (!selectedId || !aiReady) return;
    setBusyAction("exam");
    startAiThinking("exam");
    setServiceMessage("");
    try {
      const payload = await backendRequest("POST", "/api/v1/exam/generate", {
        scenario_id: selectedId,
        locale,
        attempt_history: evaluation ? [evaluation] : []
      });
      setExam(payload.exam);
      setAiOutput(null);
      finishAiThinking();
    } catch (error) {
      setServiceMessage(formatErrorMessage(error, locale));
    } finally {
      setBusyAction("");
    }
  }

  function buildAiPayload(capability) {
    const base = {
      capability,
      scenario_id: selectedId,
      locale,
      source,
      order,
      rationale,
      evaluation: evaluation ?? {},
      attempt_history: evaluation ? [evaluation] : [],
      market_context: context
    };

    if (capability === "case_generation") {
      return {
        ...base,
        learner_level: "intermediate",
        user_request: "Generate a Europe natural gas hedging case using the current scenario as the seed."
      };
    }
    if (capability === "event_drill") {
      return {
        ...base,
        event_context: "Pipeline capacity changes, storage surprises, weather demand swings, or TTF/NBP spread dislocations."
      };
    }
    if (capability === "concept_tutor") {
      return {
        ...base,
        concept: "basis risk, route capacity constraints, storage optionality, and calendar spread hedging"
      };
    }
    if (capability === "trade_playbook") {
      return {
        ...base,
        commercial_goal: "Prepare a practical pre-trade hedge playbook for the current Europe gas exposure."
      };
    }
    if (capability === "socratic_coach") {
      return {
        ...base,
        learner_message: rationale || "Ask me diagnostic questions before I place the hedge."
      };
    }
    return base;
  }

  async function runAiAction(capability) {
    if (capability === "advisor_review") {
      await requestAdvisorReview();
      return;
    }
    if (capability === "exam") {
      await generateExam();
      return;
    }
    if (!selectedId || !aiReady) return;

    setBusyAction(capability);
    startAiThinking(capability);
    setServiceMessage("");
    try {
      const payload = await backendRequest("POST", "/api/v1/ai/generate", buildAiPayload(capability));
      setAiOutput({ title: capabilityLabel(capability, locale), answer: payload.answer });
      finishAiThinking();
    } catch (error) {
      setServiceMessage(formatErrorMessage(error, locale));
    } finally {
      setBusyAction("");
    }
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
          <LanguageToggle locale={locale} setLocale={setLocale} />
        </div>
      </header>

      <AiActivationPanel
        aiReady={aiReady}
        locale={locale}
        message={busyAction === "provider" ? "" : serviceMessage}
        onSaveSettings={saveProviderSettings}
        providerStatus={providerStatus}
        saving={busyAction === "provider"}
      />

      <div className="workbench-layout">
        <aside className="left-rail">
          <CollapsiblePanel defaultOpen title={t("moduleNavigator", locale)} meta={t("naturalGasOnly", locale)}>
            <CategoryTabs categories={categories} locale={locale} />
          </CollapsiblePanel>
          <CollapsiblePanel defaultOpen title={t("scenarioDeck", locale)} meta={t("regionalGas", locale)}>
            <ScenarioDeck scenarios={scenarios} selectedId={selectedId} setSelectedId={setSelectedId} />
          </CollapsiblePanel>
          <CollapsiblePanel title={t("dataSources", locale)} meta={source === "sample" ? t("simulated", locale) : t(sourceOptions.find((option) => option.id === source)?.labelKey ?? "dataSource", locale)}>
            <DataSourceStrip activeSource={source === "sample" ? "simulated" : source} locale={locale} sources={providerStatus?.data_sources} />
          </CollapsiblePanel>
        </aside>

        <section className="workspace-main">
          <div className="scenario-header">
            <span>{selectedScenario?.region_label ?? t("scenario", locale)}</span>
            <h2>{selectedScenario?.title ?? t("loading", locale)}</h2>
            <p>{selectedScenario?.summary ?? ""}</p>
          </div>
          <div className="workspace-grid">
            <MarketChart locale={locale} market={context?.market} setSource={setSource} source={source} />
            <CapacityDiagram capacity={context?.capacity} locale={locale} />
            <ExposurePanel locale={locale} scenario={selectedScenario} />
            <OrderTicket
              busy={busyAction === "evaluate" || busyAction === "advisor_review"}
              locale={locale}
              onSubmit={submitOrder}
              order={order}
              rationale={rationale}
              setOrder={setOrder}
              setRationale={setRationale}
            />
            <ScorePanel evaluation={evaluation} locale={locale} />
            <TrainingGuide locale={locale} scenario={selectedScenario} />
          </div>
        </section>

        <AdvisorRail
          aiOutput={aiOutput}
          aiReady={aiReady}
          advisorFeedback={advisorFeedback}
          aiThinking={aiThinking}
          busyAction={busyAction}
          error={serviceMessage && busyAction !== "provider" ? serviceMessage : ""}
          evaluation={evaluation}
          exam={exam}
          journey={journey}
          locale={locale}
          runAiAction={runAiAction}
        />
      </div>
    </main>
  );
}
