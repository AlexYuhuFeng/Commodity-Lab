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

const aiCapabilityKeys = [
  "aiCaseGeneration",
  "aiEventDrills",
  "aiScoringCoach",
  "aiConceptTutor",
  "aiTradePlaybook",
  "aiExaminer"
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

function AiActivationPanel({ aiReady, locale, onSaveSettings, saving, message }) {
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
    <section className={aiReady ? "ai-activation online" : "ai-activation"}>
      <div className="ai-activation-copy">
        <p className="eyebrow">{aiReady ? t("aiConnected", locale) : t("connectAi", locale)}</p>
        <h2>{aiReady ? t("aiTerminalUnlocked", locale) : t("aiTerminalLocked", locale)}</h2>
        <p>{aiReady ? t("aiUnlockedSubtitle", locale) : t("aiLockedSubtitle", locale)}</p>
      </div>
      <form className="setup-form compact" onSubmit={submit}>
        <label>
          {t("apiKey", locale)}
          <input
            aria-label={t("apiKey", locale)}
            autoComplete="off"
            onChange={(event) => setForm({ ...form, api_key: event.target.value })}
            placeholder={aiReady ? "••••••••" : t("enterKeyToUnlock", locale)}
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
          <input
            aria-label={t("model", locale)}
            onChange={(event) => setForm({ ...form, model: event.target.value })}
            value={form.model}
          />
        </label>
        <button className="primary" disabled={saving} type="submit">
          {saving ? t("loading", locale) : aiReady ? t("refreshAi", locale) : t("unlockAi", locale)}
        </button>
      </form>
      {message ? <div className={aiReady ? "status-line ok" : "status-line warn"}>{message}</div> : null}
    </section>
  );
}

function AiCapabilityMatrix({ aiReady, locale }) {
  return (
    <section className={aiReady ? "ai-matrix online" : "ai-matrix"}>
      {aiCapabilityKeys.map((key, index) => (
        <div className="ai-card" key={key} style={{ animationDelay: `${index * 80}ms` }}>
          <span>{`0${index + 1}`}</span>
          <strong>{t(key, locale)}</strong>
          <small>{aiReady ? t("enabled", locale) : t("connectToEnable", locale)}</small>
        </div>
      ))}
    </section>
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

function ScenarioDeck({ locale, scenarios, selectedId, setSelectedId }) {
  return (
    <aside className="panel scenario-deck">
      <div className="panel-title">
        <span>{t("scenarioDeck", locale)}</span>
        <strong>{t("regionalGas", locale)}</strong>
      </div>
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
    </aside>
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
          {t("requestedSource", locale)}: {market.source_label} · {t("returnedSource", locale)}: {market.data_source_label}
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
  const range = Math.max(max - min, 0.01);

  return (
    <section className="panel market-panel">
      <div className="panel-title">
        <span>{t("marketContext", locale)}</span>
        <strong>{market?.symbol ?? "NG=F"}</strong>
      </div>
      <SourceSelector locale={locale} market={market} setSource={setSource} source={source} />
      <div className="bar-chart" role="img" aria-label={t("marketContext", locale)}>
        {points.map((point) => {
          const height = 24 + ((Number(point.close) - min) / range) * 76;
          return <span key={point.date} style={{ height: `${height}%` }} title={`${point.date}: ${point.close}`} />;
        })}
      </div>
      <div className="metric-strip">
        <span>
          {t("latestPrice", locale)}
          <strong>{formatNumber(market?.latest_price, 2)}</strong>
        </span>
        <span>
          {t("unit", locale)}
          <strong>{market?.unit ?? "USD/MMBtu"}</strong>
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

function AdvisorRail({ aiReady, advisorFeedback, busy, error, evaluation, exam, generateExam, locale, requestAdvisorReview }) {
  return (
    <aside className={aiReady ? "panel advisor-rail online" : "panel advisor-rail"}>
      <div className="panel-title">
        <span>{t("aiCoach", locale)}</span>
        <strong>{aiReady ? t("online", locale) : t("offline", locale)}</strong>
      </div>
      <GuidedStepper aiReady={aiReady} evaluation={evaluation} locale={locale} />
      <div className="advisor-actions">
        <button disabled={busy || !evaluation || !aiReady} onClick={() => requestAdvisorReview()} type="button">
          {t("askHint", locale)}
        </button>
        <button disabled={busy || !aiReady} onClick={generateExam} type="button">
          {t("generateExam", locale)}
        </button>
      </div>
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
    </aside>
  );
}

export default function App() {
  const [locale, setLocaleState] = useState(() => normalizeLocale(savedValue("commodity-lab-locale", "en")));
  const [providerStatus, setProviderStatus] = useState(null);
  const [categories, setCategories] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [context, setContext] = useState(null);
  const [source, setSource] = useState("yfinance");
  const [order, setOrder] = useState(defaultOrder);
  const [rationale, setRationale] = useState("Manage the energy exposure with a hedge that matches the risk driver, timing, and volume.");
  const [evaluation, setEvaluation] = useState(null);
  const [advisorFeedback, setAdvisorFeedback] = useState("");
  const [exam, setExam] = useState("");
  const [busyAction, setBusyAction] = useState("");
  const [serviceMessage, setServiceMessage] = useState("");

  const aiReady = Boolean(providerStatus?.haineng?.ok);

  function setLocale(nextLocale) {
    localStorage.setItem("commodity-lab-locale", nextLocale);
    setLocaleState(nextLocale);
  }

  useEffect(() => {
    let active = true;
    backendRequest("GET", "/api/v1/provider-status")
      .then((payload) => {
        if (active) setProviderStatus(payload);
      })
      .catch((error) => {
        if (!active) return;
        setProviderStatus({ haineng: { ok: false, configured: false }, data_sources: [] });
        setServiceMessage(error.message);
      });
    return () => {
      active = false;
    };
  }, []);

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
      .catch((error) => setServiceMessage(error.message));
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
      })
      .catch((error) => setServiceMessage(error.message));
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
      setServiceMessage(error.message || t("providerSaveFailed", locale));
    } finally {
      setBusyAction("");
    }
  }

  async function requestAdvisorReview(nextEvaluation = evaluation) {
    if (!nextEvaluation || !selectedId || !aiReady) return;
    setBusyAction("advisor");
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
    } catch (error) {
      setServiceMessage(error.message);
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
      if (payload.evaluation?.valid && aiReady) {
        await requestAdvisorReview(payload.evaluation);
      }
    } catch (error) {
      setServiceMessage(error.message);
    } finally {
      setBusyAction("");
    }
  }

  async function generateExam() {
    if (!selectedId || !aiReady) return;
    setBusyAction("exam");
    setServiceMessage("");
    try {
      const payload = await backendRequest("POST", "/api/v1/exam/generate", {
        scenario_id: selectedId,
        locale,
        attempt_history: evaluation ? [evaluation] : []
      });
      setExam(payload.exam);
    } catch (error) {
      setServiceMessage(error.message);
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
        message={serviceMessage}
        onSaveSettings={saveProviderSettings}
        saving={busyAction === "provider"}
      />
      <AiCapabilityMatrix aiReady={aiReady} locale={locale} />

      <div className="workspace-shell">
        <CategoryTabs categories={categories} locale={locale} />
        <div className="terminal-grid">
          <ScenarioDeck locale={locale} scenarios={scenarios} selectedId={selectedId} setSelectedId={setSelectedId} />
          <section className="workspace-main">
            <div className="scenario-header">
              <span>{selectedScenario?.region_label ?? t("scenario", locale)}</span>
              <h2>{selectedScenario?.title ?? t("loading", locale)}</h2>
              <p>{selectedScenario?.summary ?? ""}</p>
            </div>
            <DataSourceStrip activeSource={source === "sample" ? "simulated" : source} locale={locale} sources={providerStatus?.data_sources} />
            <div className="workspace-grid">
              <MarketChart locale={locale} market={context?.market} setSource={setSource} source={source} />
              <CapacityDiagram capacity={context?.capacity} locale={locale} />
              <ExposurePanel locale={locale} scenario={selectedScenario} />
              <TrainingGuide locale={locale} scenario={selectedScenario} />
              <OrderTicket
                busy={busyAction === "evaluate" || busyAction === "advisor"}
                locale={locale}
                onSubmit={submitOrder}
                order={order}
                rationale={rationale}
                setOrder={setOrder}
                setRationale={setRationale}
              />
              <ScorePanel evaluation={evaluation} locale={locale} />
            </div>
          </section>
          <AdvisorRail
            aiReady={aiReady}
            advisorFeedback={advisorFeedback}
            busy={Boolean(busyAction)}
            error={serviceMessage && busyAction !== "provider" ? serviceMessage : ""}
            evaluation={evaluation}
            exam={exam}
            generateExam={generateExam}
            locale={locale}
            requestAdvisorReview={requestAdvisorReview}
          />
        </div>
      </div>
    </main>
  );
}
