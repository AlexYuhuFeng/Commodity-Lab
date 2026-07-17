import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { dictionaries, t } from "./i18n";

vi.mock("@tauri-apps/api/window", () => ({
  appWindow: {
    close: vi.fn(),
    isFullscreen: vi.fn(async () => false),
    setFullscreen: vi.fn()
  }
}));

const businessTemplates = {
  groups: [
    { id: "foundation", label: "Foundations" },
    { id: "crude", label: "Crude Oil Hedging" },
    { id: "procurement", label: "Procurement" },
    { id: "sales", label: "Sales" }
  ],
  knowledge_points: [
    { id: "exposure_objective", label: "Exposure and hedge objective", description: "Identify long, short, or spread exposure." },
    { id: "forward_curve_carry", label: "Forward structure and carry", description: "Read contango, backwardation, carry, and roll." },
    { id: "basis_spread", label: "Basis and hub spread", description: "Separate TTF/NBP, FX, and hub basis." },
    { id: "crude_benchmark_basis", label: "Crude benchmark basis", description: "Separate Brent, WTI, Dubai, grade, location, and loading-window basis." },
    { id: "inventory_freight_roll", label: "Inventory, freight, and roll risk", description: "Check inventory, freight, margin, credit, and futures roll risk." },
    { id: "physical_paper_matching", label: "Physical-paper matching", description: "Match GSA, EFET, LNG, swaps, FX, and capacity." },
    { id: "options_optionality", label: "Options and optionality", description: "Use caps, floors, collars, and LNG optionality." },
    { id: "hedge_ratio_cross_hedge", label: "Hedge ratio and cross-hedge quality", description: "Size imperfect hedges by sensitivity and correlation." }
  ],
  templates: [
    {
      id: "foundation_hedging_basics",
      group: "foundation",
      business_type: "General hedging foundations",
      title: "General hedging tools",
      summary: "Generate an inter-commodity exposure, forward structure, instrument, ratio, and control case.",
      coverage: ["exposure_objective", "forward_curve_carry", "outright_price", "physical_paper_matching", "basis_spread", "hedge_ratio_cross_hedge", "options_optionality", "fx", "risk_controls"],
      gas_models: ["simple_procurement"],
      knowledge_points: ["exposure_objective", "forward_curve_carry", "outright_price", "physical_paper_matching", "basis_spread", "hedge_ratio_cross_hedge", "options_optionality", "fx", "risk_controls"],
      required_curves: ["PRIMARY_BENCHMARK", "HEDGE_BENCHMARK"],
      suggested_leg_types: ["physical", "swap"]
    },
    {
      id: "procurement_beach_to_germany",
      group: "procurement",
      business_type: "Upstream beach delivery GSA",
      title: "UK beach delivery sold into Germany",
      summary: "Generate a NBP/TTF, FX, capacity, and physical-paper hedge case.",
      coverage: ["basis_spread", "fx", "capacity_storage_balancing", "physical_paper_matching", "risk_controls"],
      gas_models: ["gsa_procurement", "pipeline_capacity"],
      knowledge_points: ["basis_spread", "fx", "physical_paper_matching"],
      required_curves: ["TTF", "NBP", "EURGBP"],
      suggested_leg_types: ["physical", "basis", "fx", "capacity"]
    },
    {
      id: "crude_oil_hedging_basics",
      group: "crude",
      business_type: "Crude procurement / sales hedging",
      title: "How should Brent / WTI exposure be hedged?",
      summary: "Generate a crude cargo, futures/swaps, calendar/basis, inventory, and freight hedge case.",
      coverage: ["exposure_objective", "physical_paper_matching", "outright_price", "crude_benchmark_basis", "inventory_freight_roll", "risk_controls"],
      gas_models: ["crude_cargo_hedge", "crude_calendar_basis", "crude_inventory_hedge"],
      knowledge_points: ["exposure_objective", "crude_benchmark_basis", "inventory_freight_roll"],
      required_curves: ["BRENT", "WTI", "DUBAI"],
      suggested_leg_types: ["physical", "future", "swap", "basis"]
    },
    {
      id: "sales_lng_regas",
      group: "sales",
      business_type: "LNG regas sale",
      title: "Regasified LNG sale during market selloff",
      summary: "Generate a LNG regas sale hedge case.",
      coverage: ["outright_price", "basis_spread", "options_optionality", "capacity_storage_balancing"],
      gas_models: ["lng_regas_sale", "customer_indexed_sale"],
      knowledge_points: ["outright_price", "volatility_event", "options_optionality"],
      required_curves: ["TTF", "JKM"],
      suggested_leg_types: ["physical", "swap", "basis", "option"]
    }
  ]
};

const generatedCase = {
  scenario: {
    id: "ai-procurement-beach",
    title: "UK Beach Delivery to German Citygate",
    summary: "A procurement desk buys UK beach gas and sells German delivery, creating TTF/NBP, FX, and capacity risk.",
    business_type: "Upstream beach delivery GSA",
    knowledge_points: ["basis_spread", "fx", "physical_paper_matching"],
    exposure: { direction: "spread", volume_mmbtu: 60000, risk: "NBP/TTF spread, EUR/GBP FX, and route capacity." }
  },
  market: {
    unit: "EUR/MWh",
    as_of: "2026-07-17",
    benchmark: "TTF",
    curve_metrics: { structure: "contango", front_price: 31.5, back_price: 35.2, front_back_spread: 3.7, percentage_slope: 0.11746 },
    provenance: { mode: "ai_simulated", label: "AI-simulated market", source_tier: "synthetic", is_live: false, as_of: "2026-07-17" },
    forward_curve: [
      { tenor: "M+1", delivery_month: "2026-08", price: 31.5, bid: 31.45, ask: 31.55 },
      { tenor: "M+2", delivery_month: "2026-09", price: 32.1, bid: 32.05, ask: 32.15 },
      { tenor: "M+3", delivery_month: "2026-10", price: 33.0, bid: 32.95, ask: 33.05 },
      { tenor: "M+4", delivery_month: "2026-11", price: 35.2, bid: 35.15, ask: 35.25 }
    ],
    curves: [
      {
        id: "TTF",
        label: "TTF",
        color: "#38bdf8",
        points: [
          { date: "2026-01-05", open: 31, high: 32, low: 30, close: 31.5 },
          { date: "2026-01-06", open: 31.5, high: 33, low: 31, close: 32.6 }
        ]
      },
      {
        id: "NBP",
        label: "NBP",
        color: "#f59e0b",
        points: [
          { date: "2026-01-05", open: 74, high: 76, low: 73, close: 75 },
          { date: "2026-01-06", open: 75, high: 77, low: 74, close: 76.2 }
        ]
      }
    ],
    events: [{ date: "2026-01-06", label: "Capacity tightness" }]
  },
  target_actions: [
    { id: "physical-1", leg_type: "physical", market: "UK Beach GSA", side: "buy", quantity: 60000, price: 0, tenor: "M+1", rationale: "Source gas." },
    { id: "basis-1", leg_type: "basis", market: "TTF/NBP basis swap", side: "sell", quantity: 60000, price: 0, tenor: "M+1", rationale: "Lock spread." },
    { id: "fx-1", leg_type: "fx", market: "EURGBP forward", side: "buy", quantity: 60000, price: 0, tenor: "M+1", rationale: "Cover currency mismatch." }
  ],
  rubric: [
    { id: "physical", label: "Physical leg", points: 25, rule: "Include a real gas purchase or sale leg." },
    { id: "paper", label: "Paper hedge", points: 35, rule: "Include a swap, future, or basis hedge." },
    { id: "risk", label: "Risk explanation", points: 25, rule: "Explain basis, FX, capacity, and tenor logic." },
    { id: "controls", label: "Risk controls", points: 15, rule: "Mention liquidity, limits, credit, and execution windows." }
  ],
  prompt: "### **Decision task**\n\nBuild a multi-leg hedge for UK beach gas sold into Germany.\n\n- Include physical supply.\n- Include paper basis protection."
};

const crudeGeneratedCase = {
  scenario: {
    id: "ai-crude-cargo",
    title: "Brent Cargo Hedge for Refinery Procurement",
    summary: "A refinery buys Brent-linked crude and needs to hedge flat price, calendar spread, grade basis, inventory, and freight risk.",
    business_type: "Crude procurement / sales hedging",
    knowledge_points: ["crude_benchmark_basis", "inventory_freight_roll", "physical_paper_matching"],
    exposure: { direction: "long", volume_mmbtu: 100000, volume_unit: "bbl", risk: "Brent flat price, prompt-month roll, grade/location basis, inventory, and freight." }
  },
  market: {
    unit: "USD/bbl training index",
    curves: [
      {
        id: "BRENT",
        label: "Brent",
        color: "#38bdf8",
        points: [
          { date: "2026-01-05", open: 72, high: 74, low: 71, close: 73 },
          { date: "2026-01-06", open: 73, high: 75, low: 72, close: 74 }
        ]
      },
      {
        id: "WTI",
        label: "WTI",
        color: "#f59e0b",
        points: [
          { date: "2026-01-05", open: 68, high: 69, low: 67, close: 68.4 },
          { date: "2026-01-06", open: 68.4, high: 70, low: 67.8, close: 69.2 }
        ]
      }
    ],
    events: [{ date: "2026-01-06", label: "Freight tightness" }]
  },
  target_actions: [
    { id: "physical-crude", leg_type: "physical", market: "Brent cargo", side: "buy", quantity: 100000, price: 0, tenor: "M+1", rationale: "Source physical crude." },
    { id: "future-crude", leg_type: "future", market: "ICE Brent future", side: "sell", quantity: 100000, price: 0, tenor: "M+1", rationale: "Lock flat price." },
    { id: "basis-crude", leg_type: "basis", market: "Brent/WTI basis", side: "sell", quantity: 100000, price: 0, tenor: "M+1", rationale: "Manage basis mismatch." }
  ],
  rubric: [
    { id: "physical", label: "Physical leg", points: 25, rule: "Include a crude cargo or inventory leg." },
    { id: "paper", label: "Paper hedge", points: 35, rule: "Include futures, swap, or basis hedge." },
    { id: "risk", label: "Risk explanation", points: 25, rule: "Explain flat price, calendar, basis, inventory, and freight." },
    { id: "controls", label: "Risk controls", points: 15, rule: "Mention liquidity, margin, credit, roll, and execution window." }
  ],
  prompt: "### **Decision task**\n\nBuild a crude cargo hedge for Brent-linked procurement.\n\n- Include physical cargo.\n- Include paper flat-price and basis protection."
};

const replayGeneratedCase = {
  ...crudeGeneratedCase,
  scenario: {
    ...crudeGeneratedCase.scenario,
    title: "2026 Strait of Hormuz supply-shock replay",
    summary: "Manage a refinery procurement hedge as point-in-time information is revealed."
  },
  market: {
    ...crudeGeneratedCase.market,
    unit: "USD/bbl",
    as_of: "2026-04-01",
    benchmark: "Brent",
    curve_metrics: { structure: "backwardation", front_price: 103, back_price: 96, front_back_spread: -7 },
    provenance: { mode: "historical_replay", label: "Historical replay (calibrated simulation)", source_tier: "historically_calibrated_simulation", is_live: false },
    forward_curve: [
      { tenor: "M+1", price: 103, bid: 102.95, ask: 103.05 },
      { tenor: "M+2", price: 100, bid: 99.95, ask: 100.05 },
      { tenor: "M+3", price: 96, bid: 95.95, ask: 96.05 }
    ],
    replay: {
      event: { id: "hormuz_2026_disruption", title: "2026 Strait of Hormuz supply-shock replay", summary: "Point-in-time refinery procurement replay.", skills: ["flat_price", "freight"], checkpoint_count: 3 },
      current_checkpoint: { index: 0, date: "2026-04-01", label: "Supply route disruption", facts: ["Hormuz traffic is constrained", "Prices and volatility rise"], decision_required: "Choose physical cover, Brent hedge ratio, and upside protection." },
      visible_timeline: [{ index: 0, date: "2026-04-01", label: "Supply route disruption", facts: ["Hormuz traffic is constrained"], decision_required: "Choose a hedge." }],
      next_checkpoint: 1,
      information_policy: "Only information available at this checkpoint is shown."
    }
  },
  target_actions: [],
  rubric: [
    { id: "decision_structure", label: "Decision structure", points: 55, rule: "Build coherent physical and paper legs." },
    { id: "risk_reasoning", label: "Risk reasoning", points: 25, rule: "Explain price, spreads, options, and freight." },
    { id: "controls", label: "Execution and controls", points: 20, rule: "Check margin, liquidity, and limits." }
  ],
  prompt: "### Supply route disruption\n\n- Hormuz traffic is constrained\n\n**Decision:** Choose a hedge."
};

function mockBackend({ aiReady = true, assistantResponse = null, failTrainingCase = false, onCall, trainingCasePromise = null } = {}) {
  window.__COMMODITY_LAB_BACKEND__ = async (method, path, body) => {
    onCall?.({ method, path, body });
    if (path === "/api/health") {
      return { ok: true, service: "commodity-lab-backend" };
    }
    if (path === "/api/v1/provider-status") {
      return {
        haineng: {
          ok: aiReady,
          configured: aiReady,
          provider: "haineng",
          model: "DeepSeek-V4-Flash",
          resolved_model: "DeepSeek-V4-Flash"
        },
        ai_providers: {
          haineng: {
            label: "Haineng",
            default_model: "DeepSeek-V4-Flash",
            models: [
              { id: "DeepSeek-V4-Flash", label: "DeepSeek-V4-Flash", resolved_model: "DeepSeek-V4-Flash", base_url: "http://model.ai.cnooc/member1/deepseek-v4-flash-291b-1m/v1" },
              { id: "DeepSeek-V4", label: "DeepSeek-V4", resolved_model: "DeepSeek-V4", base_url: "http://model.ai.cnooc/member1/deepseek-v4-pro-1-5t/v1" }
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
        },
        training_data: { mode: "ai_generated", configured: aiReady }
      };
    }
    if (path.startsWith("/api/v1/business-templates?")) return businessTemplates;
    if (path.startsWith("/api/v1/market/capabilities?")) {
      return {
        modes: [
          { id: "live", label: "Live market", description: "Use entitled market data." },
          { id: "historical_replay", label: "Historical replay", description: "Reveal the market point by point." },
          { id: "ai_simulated", label: "AI-simulated market", description: "Use coherent deterministic curves." }
        ],
        providers: [
          { id: "platts", label: "S&P Global Commodity Insights (Platts)", status: "not_configured", integration_state: "adapter_contract_ready", requires_subscription: true }
        ],
        fallback_mode: "ai_simulated",
        replays: [
          {
            id: "hormuz_2026_disruption",
            commodity: "crude_oil",
            title: "2026 Strait of Hormuz supply-shock replay",
            summary: "Manage physical cargo, Brent paper, calendar spread, freight, and optionality as information is revealed.",
            checkpoint_count: 3
          }
        ]
      };
    }
    if (path === "/api/v1/version") {
      return {
        current_version: "1.2.1",
        organization: "天然气中心",
        project_lead: "杨敏",
        repository: "AlexYuhuFeng/Commodity-Lab"
      };
    }
    if (path === "/api/v1/provider-settings") {
      return {
        haineng: {
          ok: true,
          configured: true,
          provider: body.provider,
          base_url: body.base_url,
          model: body.model,
          resolved_model: body.provider === "deepseek" ? "deepseek-v4-flash" : "DeepSeek-V4-Flash"
        }
      };
    }
    if (path === "/api/v1/ai/training-case") {
      if (failTrainingCase) throw new Error("AI temporarily unavailable");
      if (trainingCasePromise) return trainingCasePromise;
      const template = businessTemplates.templates.find((item) => item.id === body?.template_id) ?? businessTemplates.templates[0];
      return { template, case: body?.market_mode === "historical_replay" ? replayGeneratedCase : body?.template_id === "crude_oil_hedging_basics" ? crudeGeneratedCase : generatedCase };
    }
    if (path === "/api/v1/replays/hormuz_2026_disruption/decision") {
      return {
        event_id: "hormuz_2026_disruption",
        checkpoint: replayGeneratedCase.market.replay.current_checkpoint,
        evaluation: { valid: true, baseline_score: 72, rubric: replayGeneratedCase.rubric, mistake_tags: ["thin_risk_reasoning"], dimensions: [], metrics: { strategy_leg_count: 1 } },
        feedback: "The direction is broadly sound, but execution controls need work.",
        outcome: "Prompt prices continued higher after the disruption.",
        model_strategy: [{ leg_type: "future", market: "ICE Brent", side: "buy", quantity: 70000, tenor: "M+2" }],
        next_checkpoint: 1,
        complete: false
      };
    }
    if (path === "/api/v1/replays/hormuz_2026_disruption/session") {
      return {
        event: replayGeneratedCase.market.replay.event,
        current_checkpoint: { index: body.checkpoint, date: "2026-04-29", label: "Uncertainty peaks", facts: ["Front-month Brent reaches the quarterly high"], decision_required: "Reassess hedge size and option protection." },
        visible_timeline: [replayGeneratedCase.market.replay.current_checkpoint, { index: 1, date: "2026-04-29", label: "Uncertainty peaks", facts: ["Brent reaches a high"], decision_required: "Reassess." }],
        next_checkpoint: 2,
        decision_rubric: replayGeneratedCase.rubric,
        market: { ...replayGeneratedCase.market, as_of: "2026-04-29", replay: undefined },
        source_notes: [],
        information_policy: "Only information available at this checkpoint is shown."
      };
    }
    if (path === "/api/v1/ai/live-assistant") {
      if (assistantResponse) return assistantResponse;
      if (/score|submit|evaluate/i.test(body?.message ?? "")) {
        return {
          answer: "I submitted the current strategy for local scoring.",
          actions: [
            {
              type: "submit_strategy",
              label: "Scored strategy",
              payload: {}
            }
          ]
        };
      }
      if (/quiz|exam|test/i.test(body?.message ?? "")) {
        return {
          answer: "I created a short quiz and opened Review.",
          actions: [
            {
              type: "set_exam",
              label: "Generated quiz",
              payload: {
                exam: "1. What basis risk remains?\n2. Which leg covers FX exposure?"
              }
            }
          ]
        };
      }
      if (/plan|next|course|学习|路线/i.test(body?.message ?? "")) {
        return {
          answer: "I set a short learning plan and opened the path.",
          actions: [
            {
              type: "set_learning_plan",
              label: "Set learning plan",
              payload: {
                track_id: "integrated",
                title: "Basis bridge plan",
                objective: "Connect physical delivery, basis, FX, and capacity into one hedge package.",
                steps: ["Review exposure", "Map hedge legs", "Generate an integrated drill"],
                practice_prompt: "Generate an integrated basis, FX, and capacity drill."
              }
            }
          ]
        };
      }
      return {
        answer: "### **Plan**\n\n- Use high/low/close to inspect volatility.\n- Add basis and FX legs.",
        actions: [
          { type: "set_chart_fields", label: "Show high/low/close", payload: { fields: ["high", "low", "close"] } }
        ]
      };
    }
    if (path === "/api/v1/ai/generate") return { answer: "### Playbook\nCheck capacity, basis, liquidity, FX, and risk limits." };
    if (path === "/api/v1/exam/generate") return { exam: "1. What basis risk remains?" };
    if (path === "/api/v1/update-check") {
      return { current_version: "1.2.1", latest_version: "1.2.1", up_to_date: true, release_url: "https://github.com/AlexYuhuFeng/Commodity-Lab/releases/tag/v1.2.1", assets: [] };
    }
    return {};
  };
}

function renderShell(options = {}) {
  localStorage.setItem("commodity-lab-guide-complete", "1");
  mockBackend(options);
  return render(<App />);
}

afterEach(() => {
  cleanup();
  localStorage.clear();
  delete window.__COMMODITY_LAB_BACKEND__;
  delete window.__COMMODITY_LAB_BACKEND_STREAM__;
});

describe("i18n catalog", () => {
  it("has matching English and Mandarin keys", () => {
    expect(Object.keys(dictionaries.zh).sort()).toEqual(Object.keys(dictionaries.en).sort());
  });

  it("falls back to English for unknown locale", () => {
    expect(t("appTitle", "fr")).toBe("Commodity Lab");
  });
});

describe("Commodity Lab shell", () => {
  it("defaults to Mandarin and presents the new market-aware learning model", async () => {
    renderShell({ aiReady: true });

    expect(await screen.findByText("AI 全功能")).toBeInTheDocument();
    expect(screen.getByText("Commodity Lab")).toBeInTheDocument();
    expect(screen.getAllByText("设置")[0]).toBeInTheDocument();
    expect(screen.getByText("通识 + 天然气 学习路径")).toBeInTheDocument();
    expect(screen.getByLabelText("课程产品")).toHaveValue("natural_gas");
    expect(screen.getAllByText("生成练习").length).toBeGreaterThan(0);
    expect(screen.queryByText(/涓|鈥|娴疯兘/)).not.toBeInTheDocument();
  });

  it("lets the learner choose a historical replay and sends the point-in-time mode to DeepSeek", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    fireEvent.change(await screen.findByLabelText("Course product"), { target: { value: "crude_oil" } });
    fireEvent.click(await screen.findByText("Practice Generator"));
    expect(await screen.findByText("Market evidence")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Historical replay" }));
    expect(screen.getByText("2026 Strait of Hormuz supply-shock replay")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Generate Case"));

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/ai/training-case")).toBe(true));
    const request = calls.find((call) => call.path === "/api/v1/ai/training-case")?.body;
    expect(request.market_mode).toBe("historical_replay");
    expect(request.replay_id).toBe("hormuz_2026_disruption");
    expect(request.product_scope).toBe("crude_oil");
  });

  it("gates future replay information until a local decision is submitted", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    fireEvent.change(await screen.findByLabelText("Course product"), { target: { value: "crude_oil" } });
    fireEvent.click(await screen.findByText("Practice Generator"));
    fireEvent.click(screen.getByRole("tab", { name: "Historical replay" }));
    fireEvent.click(screen.getByText("Generate Case"));

    expect(await screen.findByText("Event Replay")).toBeInTheDocument();
    expect(screen.getAllByText("Reveal after decision")).toHaveLength(2);
    expect(screen.queryByText("Uncertainty peaks")).not.toBeInTheDocument();

    fireEvent.click((await screen.findAllByText("Submit strategy"))[0]);
    expect(await screen.findByText("72/100")).toBeInTheDocument();
    expect(screen.getByText("Prompt prices continued higher after the disruption.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Reveal next market phase/i }));

    expect((await screen.findAllByText("Uncertainty peaks")).length).toBeGreaterThan(0);
    expect(calls.some((call) => call.path.endsWith("/decision"))).toBe(true);
    expect(calls.some((call) => call.path.endsWith("/session") && call.body?.checkpoint === 1)).toBe(true);
  });

  it("lets the learner request a backwardated simulated market and shows provenance in the workbench", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    fireEvent.click(await screen.findByText("Practice Generator"));
    fireEvent.change(await screen.findByLabelText("Forward curve structure"), { target: { value: "backwardation" } });
    fireEvent.click(screen.getByText("Generate Case"));

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/ai/training-case")).toBe(true));
    const request = calls.find((call) => call.path === "/api/v1/ai/training-case")?.body;
    expect(request.market_mode).toBe("ai_simulated");
    expect(request.market_regime).toBe("backwardation");
    expect(await screen.findByText("AI-simulated market")).toBeInTheDocument();
    expect(screen.getByText("Contango")).toBeInTheDocument();
    expect(screen.getByText("As of 2026-07-17")).toBeInTheDocument();
  });

  it("keeps the preview workbench aligned with a crude historical replay before generation", async () => {
    renderShell({ aiReady: false });

    fireEvent.change(await screen.findByLabelText("课程产品"), { target: { value: "crude_oil" } });
    fireEvent.click(await screen.findByText("生成练习"));
    fireEvent.click(screen.getByRole("tab", { name: "Historical replay" }));
    fireEvent.click(screen.getByRole("button", { name: "训练工作台" }));

    expect(await screen.findByText("第一课：原油船货与基准风险")).toBeInTheDocument();
    expect(screen.getByText("Backwardation")).toBeInTheDocument();
    expect(screen.queryByText("第一课：套保对象与风险敞口")).not.toBeInTheDocument();
  });

  it("saves DeepSeek settings with a separate provider contract from Haineng", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: false, onCall: (call) => calls.push(call) });

    fireEvent.click((await screen.findAllByText("Settings"))[0]);
    expect(screen.queryByLabelText("Model")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Base URL")).not.toBeInTheDocument();
    fireEvent.change(await screen.findByLabelText("API key"), { target: { value: "local-secret" } });
    fireEvent.change(screen.getByLabelText("Provider"), { target: { value: "deepseek" } });
    fireEvent.click(screen.getByText("Save"));

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/provider-settings")).toBe(true));
    const request = calls.find((call) => call.path === "/api/v1/provider-settings")?.body;
    expect(request.provider).toBe("deepseek");
    expect(request.base_url).toBe("https://api.deepseek.com");
    expect(request.model).toBe("deepseek-v4-flash");
  });

  it("uses fixed Haineng Flash routing without model or URL controls", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: false, onCall: (call) => calls.push(call) });

    fireEvent.click((await screen.findAllByText("Settings"))[0]);
    expect(screen.getByLabelText("Provider")).toHaveValue("haineng");
    expect(screen.queryByLabelText("Model")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Base URL")).not.toBeInTheDocument();
    fireEvent.change(await screen.findByLabelText("API key"), { target: { value: "local-secret" } });
    fireEvent.click(screen.getByText("Save"));

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/provider-settings")).toBe(true));
    const request = calls.find((call) => call.path === "/api/v1/provider-settings")?.body;
    expect(request.provider).toBe("haineng");
    expect(request.model).toBe("DeepSeek-V4-Flash");
    expect(request.base_url).toBe("http://model.ai.cnooc/member1/deepseek-v4-flash-291b-1m/v1");
  });

  it("imports an AI key file selected by the user from any location", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    const { container } = renderShell({ aiReady: false, onCall: (call) => calls.push(call) });

    fireEvent.click((await screen.findAllByText("Settings"))[0]);
    const file = new File(
      [JSON.stringify({ provider: "haineng", api_key: "file-secret-key", model: "V4-Pro" })],
      "AI密钥.json",
      { type: "application/json" }
    );
    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [file] } });

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/provider-settings" && call.body?.api_key === "file-secret-key")).toBe(true));
    const request = calls.find((call) => call.path === "/api/v1/provider-settings" && call.body?.api_key === "file-secret-key")?.body;
    expect(request.provider).toBe("haineng");
    expect(request.model).toBe("DeepSeek-V4-Flash");
    expect(request.base_url).toBe("http://model.ai.cnooc/member1/deepseek-v4-flash-291b-1m/v1");
  });

  it("imports Haineng Python SDK sample key files without keeping quotes in settings", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    const { container } = renderShell({ aiReady: false, onCall: (call) => calls.push(call) });

    fireEvent.click((await screen.findAllByText("Settings"))[0]);
    const file = new File(
      [
        [
          "from openai import OpenAI",
          "client = OpenAI(",
          "    api_key=\"python-secret-key\",",
          "    base_url=\"http://model.ai.cnooc/member1/deepseek-v4-pro-1-5t/v1\",",
          ")",
          "def chat_once(prompt: str, model: str = \"DeepSeek-V4\"):",
          "    return client.chat.completions.create(model=model, messages=[])"
        ].join("\n")
      ],
      "v4-flash-thinking.py",
      { type: "text/x-python" }
    );
    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [file] } });

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/provider-settings" && call.body?.api_key === "python-secret-key")).toBe(true));
    const request = calls.find((call) => call.path === "/api/v1/provider-settings" && call.body?.api_key === "python-secret-key")?.body;
    expect(request.provider).toBe("haineng");
    expect(request.model).toBe("DeepSeek-V4-Flash");
    expect(request.base_url).toBe("http://model.ai.cnooc/member1/deepseek-v4-flash-291b-1m/v1");
  });

  it("imports a single-line key using the currently selected provider", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    const { container } = renderShell({ aiReady: false, onCall: (call) => calls.push(call) });

    fireEvent.click((await screen.findAllByText("Settings"))[0]);
    fireEvent.change(screen.getByLabelText("Provider"), { target: { value: "deepseek" } });
    const file = new File(["raw-secret-key"], "AI密钥", { type: "text/plain" });
    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [file] } });

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/provider-settings" && call.body?.api_key === "raw-secret-key")).toBe(true));
    const request = calls.find((call) => call.path === "/api/v1/provider-settings" && call.body?.api_key === "raw-secret-key")?.body;
    expect(request.provider).toBe("deepseek");
    expect(request.model).toBe("deepseek-v4-flash");
    expect(request.base_url).toBe("https://api.deepseek.com");
  });

  it("generates an AI case from a business template and renders Markdown as formatted content", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    fireEvent.click(await screen.findByText("Practice Generator"));
    fireEvent.click(await screen.findByText("Generate Case"));

    expect(await screen.findByText("UK Beach Delivery to German Citygate")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Decision task" })).toBeInTheDocument();
    expect(screen.queryByText(/###/)).not.toBeInTheDocument();
    expect(screen.getAllByText("TTF").length).toBeGreaterThan(0);
    expect(screen.getAllByText("NBP").length).toBeGreaterThan(0);
    expect(calls.some((call) => call.path === "/api/v1/ai/training-case" && call.body?.template_id === "foundation_hedging_basics")).toBe(true);
    const request = calls.find((call) => call.path === "/api/v1/ai/training-case")?.body;
    expect(request.knowledge_coverage.map((item) => item.id)).toHaveLength(9);
    expect(request.knowledge_coverage.map((item) => item.id)).toEqual(expect.arrayContaining([
      "exposure_objective",
      "forward_curve_carry",
      "physical_paper_matching",
      "outright_price",
      "basis_spread",
      "fx",
      "options_optionality",
      "hedge_ratio_cross_hedge",
      "risk_controls"
    ]));
    expect(request.gas_trading_models.map((item) => item.id)).toEqual(["simple_procurement"]);
    expect(request.product_scope).toBe("natural_gas");
  });

  it("projects streamed AI market and scenario fields into the workbench before the final case", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });
    let releaseFinalCase;
    window.__COMMODITY_LAB_BACKEND_STREAM__ = async (_path, _body, onEvent) => {
      onEvent("stage", { id: "resolve_market", label: "Resolving market" });
      onEvent("market", {
        benchmark: "TTF",
        label: "TTF Front Month",
        unit: "EUR/MWh",
        as_of: "2026-07-17",
        curve_metrics: generatedCase.market.curve_metrics,
        forward_curve: generatedCase.market.forward_curve,
        history: generatedCase.market.curves[0].points,
        provenance: generatedCase.market.provenance
      });
      const partial = '{"scenario":{"title":"Streaming hedge case","summary":"Market data is already actionable","business_type":"Gas procurement"';
      onEvent("model_delta", { delta: partial, received: partial.length });
      await new Promise((resolve) => { releaseFinalCase = resolve; });
      onEvent("case", { case: generatedCase });
      onEvent("done", { ok: true });
    };

    fireEvent.click(await screen.findByText("Practice Generator"));
    fireEvent.click(await screen.findByText("Generate Case"));

    expect(await screen.findByText("Streaming hedge case")).toBeInTheDocument();
    expect(screen.getByText(/structured characters received/)).toBeInTheDocument();
    expect(screen.getAllByText("TTF").length).toBeGreaterThan(0);

    releaseFinalCase();
    expect(await screen.findByText("UK Beach Delivery to German Citygate")).toBeInTheDocument();
  });

  it("includes crude oil hedging as a real AI-generated course track", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    fireEvent.change(await screen.findByLabelText("Course product"), { target: { value: "crude_oil" } });
    const crudeCard = (await screen.findByText("Crude Oil Hedging")).closest("article");
    expect(crudeCard).not.toBeNull();
    fireEvent.click(within(crudeCard).getByRole("button", { name: /Generate chapter drill/i }));

    expect(await screen.findByText("Brent Cargo Hedge for Refinery Procurement")).toBeInTheDocument();
    expect(screen.getAllByText("Crude procurement / sales hedging").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Brent").length).toBeGreaterThan(0);
    expect(calls.some((call) => call.path === "/api/v1/ai/training-case" && call.body?.template_id === "crude_oil_hedging_basics")).toBe(true);
    expect(calls.find((call) => call.path === "/api/v1/ai/training-case")?.body.product_scope).toBe("crude_oil");
  });

  it("keeps a crude-specific local case visible when AI generation fails", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true, failTrainingCase: true });

    fireEvent.change(await screen.findByLabelText("Course product"), { target: { value: "crude_oil" } });
    const crudeCard = (await screen.findByText("Crude Oil Hedging")).closest("article");
    fireEvent.click(within(crudeCard).getByRole("button", { name: /Generate chapter drill/i }));

    expect(await screen.findByText("Lesson 1: Crude Cargo and Benchmark Risk")).toBeInTheDocument();
    expect(screen.getByText("100,000 bbl")).toBeInTheDocument();
    expect(screen.getAllByText("Brent").length).toBeGreaterThan(0);
    expect(screen.getAllByText("WTI").length).toBeGreaterThan(0);
    expect(screen.queryByText("60,000 MMBtu")).not.toBeInTheDocument();
  });

  it("does not show old pre-release learning scores on the home path", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    localStorage.setItem(
      "commodity-lab-learning-records-v1",
      JSON.stringify([{ evaluation: { baseline_score: 91 }, strategy_legs: [] }])
    );
    renderShell({ aiReady: true });

    expect(await screen.findByText("No scored training records yet")).toBeInTheDocument();
    expect(screen.queryByText("91/100")).not.toBeInTheDocument();
  });

  it("routes offline course actions to settings instead of appearing inert", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: false });

    fireEvent.click((await screen.findAllByText("Connect AI first"))[0]);

    expect(await screen.findByText("Manage language, theme, AI provider, key-file import, version updates, and developer information.")).toBeInTheDocument();
  });

  it("shows general knowledge plus only the selected product models in the course map", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    fireEvent.click(await screen.findByText("Course Map"));

    expect(await screen.findByText("General Hedging Tools")).toBeInTheDocument();
    expect(screen.getAllByText("Options and Optionality").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Hedge Ratio and Cross-Hedge").length).toBeGreaterThan(0);
    expect(screen.getByText("Commodity Trading Models")).toBeInTheDocument();
    expect(screen.getByText("Upstream Beach / GSA Supply")).toBeInTheDocument();
    expect(screen.queryByText("Crude Cargo Procurement / Sale Hedge")).not.toBeInTheDocument();
    expect(screen.getByText("LNG Regas Sale")).toBeInTheDocument();
    expect(screen.getByText("Bilateral EFET Sale")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Course product"), { target: { value: "crude_oil" } });
    fireEvent.click(await screen.findByText("Course Map"));
    expect(await screen.findByText("Crude Cargo Procurement / Sale Hedge")).toBeInTheDocument();
    expect(screen.queryByText("Upstream Beach / GSA Supply")).not.toBeInTheDocument();
  });

  it("scores a multi-leg strategy locally without waiting for AI scoring", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    fireEvent.click(await screen.findByText("Training Workbench"));
    fireEvent.click(await screen.findByText("AI Suggest Legs"));
    const submitButtons = await screen.findAllByText("Submit strategy");
    fireEvent.click(submitButtons[0]);

    expect(await screen.findByText("91")).toBeInTheDocument();
    expect(calls.some((call) => call.path === "/api/v1/attempts/evaluate")).toBe(false);
  });

  it("starts with an empty decision ticket instead of revealing target actions", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    fireEvent.click(await screen.findByText("Training Workbench"));

    expect(await screen.findByLabelText("Leg type")).toHaveValue("");
    expect(screen.getByLabelText("Market")).toHaveValue("");
    expect(screen.queryByText("Local scoring")).not.toBeInTheDocument();
  });

  it("maps strategy legs to visible risk coverage before submission", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    fireEvent.click(await screen.findByText("Training Workbench"));
    fireEvent.click(await screen.findByText("AI Suggest Legs"));

    expect(await screen.findByText("Risk Coverage Map")).toBeInTheDocument();
    expect(screen.getByText("Physical exposure")).toBeInTheDocument();
    expect(screen.getByText("Basis / location risk")).toBeInTheDocument();
    expect(screen.getByText("Covered by UK Beach GSA")).toBeInTheDocument();
    expect(screen.getByText("Covered by TTF/NBP basis swap")).toBeInTheDocument();
    expect(screen.getByText("Missing target actions")).toBeInTheDocument();
  });

  it("staggers chart trade-marker labels so strategy legs do not overlap", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const { container } = renderShell({ aiReady: true });

    fireEvent.click((await screen.findAllByText("Generate beginner drill"))[0]);
    expect(await screen.findByText("UK Beach Delivery to German Citygate")).toBeInTheDocument();
    fireEvent.click(await screen.findByText("AI Suggest Legs"));

    const markerLabels = Array.from(container.querySelectorAll(".trade-marker text"));
    expect(markerLabels.length).toBeGreaterThan(2);
    const yValues = markerLabels.map((label) => label.getAttribute("y"));
    expect(new Set(yValues).size).toBe(markerLabels.length);
  });

  it("uses the floating assistant for Markdown answers and safe workspace actions", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    fireEvent.click(await screen.findByText("Training Workbench"));
    fireEvent.click(await screen.findByRole("button", { name: "Live assistant" }));
    fireEvent.change(screen.getByPlaceholderText(/first hedging lesson/), { target: { value: "Show high low close and explain basis." } });
    fireEvent.click(screen.getByText("Send"));

    expect(await screen.findByRole("heading", { name: "Plan" })).toBeInTheDocument();
    expect(screen.queryByText(/###/)).not.toBeInTheDocument();
    expect(screen.getByText("AI is shaping this lesson")).toBeInTheDocument();
    fireEvent.click(screen.getAllByText("Show high/low/close").at(-1));
    expect(screen.getByText("High")).toHaveClass("active");
    expect(screen.getByText("Low")).toHaveClass("active");
    expect(screen.getByText("AI Control Log")).toBeInTheDocument();
    expect(screen.getAllByText("Adjusted chart fields").length).toBeGreaterThan(0);
    expect(screen.getByText("AI action applied")).toBeInTheDocument();
  });

  it("constrains AI template actions to the selected product workspace", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({
      aiReady: true,
      onCall: (call) => calls.push(call),
      assistantResponse: {
        answer: "I will build a matching product drill.",
        actions: [{
          type: "select_template",
          label: "Generate drill",
          payload: { template_id: "procurement_beach_to_germany", user_request: "Build a benchmark hedge." }
        }]
      }
    });

    fireEvent.change(await screen.findByLabelText("Course product"), { target: { value: "crude_oil" } });
    fireEvent.click(await screen.findByRole("button", { name: "Live assistant" }));
    fireEvent.change(screen.getByPlaceholderText(/first hedging lesson/), { target: { value: "Build a benchmark hedge." } });
    fireEvent.click(screen.getByText("Send"));

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/ai/training-case")).toBe(true));
    const request = calls.find((call) => call.path === "/api/v1/ai/training-case");
    expect(request.body.template_id).toBe("crude_oil_hedging_basics");
    expect(request.body.product_scope).toBe("crude_oil");
    expect(await screen.findByText("Brent Cargo Hedge for Refinery Procurement")).toBeInTheDocument();
  });

  it("ignores an in-flight case response after the product workspace changes", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    let resolveTrainingCase;
    const trainingCasePromise = new Promise((resolve) => {
      resolveTrainingCase = resolve;
    });
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call), trainingCasePromise });

    fireEvent.click((await screen.findAllByText("Generate beginner drill"))[0]);
    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/ai/training-case")).toBe(true));
    fireEvent.change(screen.getByLabelText("Course product"), { target: { value: "crude_oil" } });
    resolveTrainingCase({ template: businessTemplates.templates[1], case: generatedCase });

    expect(await screen.findByText("General + Crude Oil Learning Path")).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText("UK Beach Delivery to German Citygate")).not.toBeInTheDocument());
    expect(screen.getByLabelText("Course product")).toHaveValue("crude_oil");
  });

  it("keeps an AI control palette available before the user writes a prompt", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    fireEvent.click(await screen.findByText("Training Workbench"));
    fireEvent.click(await screen.findByRole("button", { name: "Live assistant" }));

    expect(screen.getByText("AI controls")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Show high/low/close" }));

    expect(await screen.findByRole("heading", { name: "Plan" })).toBeInTheDocument();
    expect(screen.getByText("High")).toHaveClass("active");
    expect(screen.getByText("Low")).toHaveClass("active");
    expect(screen.getByText("AI Control Log")).toBeInTheDocument();
    expect(screen.getAllByText("Adjusted chart fields").length).toBeGreaterThan(0);
  });

  it("lets the floating assistant visibly update the home learning plan", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    fireEvent.click(await screen.findByRole("button", { name: "Live assistant" }));
    fireEvent.change(screen.getByPlaceholderText(/first hedging lesson/), { target: { value: "Build my next course plan." } });
    fireEvent.click(screen.getByText("Send"));

    expect(await screen.findByText("AI Teaching Plan")).toBeInTheDocument();
    expect(screen.getByText("AI customized")).toBeInTheDocument();
    expect(screen.getByText("Basis bridge plan")).toBeInTheDocument();
    expect(screen.getAllByText("Generate this lesson").length).toBeGreaterThan(0);
    expect(screen.getByText("AI is shaping this lesson")).toBeInTheDocument();
    expect(screen.getByText("Conversation became app changes")).toBeInTheDocument();
    expect(screen.getByText("Updated path")).toBeInTheDocument();
  });

  it("turns the home page into a staged AI-guided course loop", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    expect(await screen.findByText("Learning Loop")).toBeInTheDocument();
    expect(screen.getAllByText("Discover").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Generate").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Practice").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Review").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Reinforce").length).toBeGreaterThan(0);

    fireEvent.click(await screen.findByRole("button", { name: "Live assistant" }));
    fireEvent.change(screen.getByPlaceholderText(/first hedging lesson/), { target: { value: "Build my next course plan." } });
    fireEvent.click(screen.getByText("Send"));

    expect(await screen.findByText("AI is guiding this step")).toBeInTheDocument();
    expect(screen.getByText("Current module")).toBeInTheDocument();
    expect(screen.getByText("Next classroom move")).toBeInTheDocument();
    expect(screen.getAllByText("Generate this lesson").length).toBeGreaterThan(0);
  });

  it("presents the home curriculum as ordered lessons with AI generation controls", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    expect((await screen.findAllByText("Lesson Sequence")).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Prerequisite/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Learning outcome").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Exposure Recognition").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Futures, Forwards, and Swaps").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Generate lesson with AI").length).toBeGreaterThan(0);
  });

  it("renders AI-generated quiz content on the review page after quiz generation", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    expect(await screen.findByText("AI Full Power")).toBeInTheDocument();
    fireEvent.click(await screen.findByText("Course Map"));
    fireEvent.click(screen.getByText("Quiz Me"));

    expect(await screen.findByText("AI Quiz Mode")).toBeInTheDocument();
    expect(screen.getByText("Question 1")).toBeInTheDocument();
    expect(screen.getByText("What basis risk remains?")).toBeInTheDocument();
    expect(screen.queryByText("No strategy submitted")).not.toBeInTheDocument();
  });

  it("lets the floating assistant generate a quiz and open the review workflow", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    expect(await screen.findByText("AI Full Power")).toBeInTheDocument();
    fireEvent.click(await screen.findByRole("button", { name: "Live assistant" }));
    fireEvent.click(screen.getByRole("button", { name: "Generate quiz" }));

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/ai/live-assistant")).toBe(true));
    expect(await screen.findByText("AI Quiz Mode")).toBeInTheDocument();
    expect(screen.getByText("Question 1")).toBeInTheDocument();
    expect(screen.getByText("What basis risk remains?")).toBeInTheDocument();
    expect(screen.getByText("Question 2")).toBeInTheDocument();
    expect(screen.getByText("Which leg covers FX exposure?")).toBeInTheDocument();
    expect(screen.getByText("Conversation became app changes")).toBeInTheDocument();
    expect(screen.getAllByText("Generated quiz").length).toBeGreaterThan(0);
    expect(screen.getByText("AI is shaping this lesson")).toBeInTheDocument();
  });

  it("lets the floating assistant submit and locally score the current strategy", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    expect(await screen.findByText("AI Full Power")).toBeInTheDocument();
    fireEvent.click(await screen.findByText("Training Workbench"));
    fireEvent.click(await screen.findByRole("button", { name: "Live assistant" }));
    fireEvent.click(screen.getByRole("button", { name: "Score strategy" }));

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/ai/live-assistant")).toBe(true));
    expect(await screen.findByText("Local scoring complete")).toBeInTheDocument();
    expect(screen.getByText("User Strategy vs Target Actions")).toBeInTheDocument();
    expect(screen.getByText("Conversation became app changes")).toBeInTheDocument();
    expect(screen.getAllByText("Scored strategy").length).toBeGreaterThan(0);
  });
});
