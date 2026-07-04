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
      business_type: "Natural gas hedging foundations",
      title: "What exposure are we hedging?",
      summary: "Generate a beginner exposure, hedge objective, and physical-paper matching case.",
      coverage: ["exposure_objective", "outright_price", "physical_paper_matching"],
      gas_models: ["simple_procurement", "customer_indexed_sale"],
      knowledge_points: ["exposure_objective", "outright_price", "physical_paper_matching"],
      required_curves: ["TTF", "TRAINING_HEDGE_INDEX"],
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
    unit: "training index",
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

function mockBackend({ aiReady = true, failTrainingCase = false, onCall } = {}) {
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
      const template = businessTemplates.templates.find((item) => item.id === body?.template_id) ?? businessTemplates.templates[0];
      return { template, case: body?.template_id === "crude_oil_hedging_basics" ? crudeGeneratedCase : generatedCase };
    }
    if (path === "/api/v1/ai/live-assistant") {
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
  it("defaults to Mandarin and no longer exposes external data source labels", async () => {
    renderShell({ aiReady: true });

    expect(await screen.findByText("AI 全功能")).toBeInTheDocument();
    expect(screen.getByText("Commodity Lab")).toBeInTheDocument();
    expect(screen.getAllByText("设置")[0]).toBeInTheDocument();
    expect(screen.getByText("商品套保学习路径")).toBeInTheDocument();
    expect(screen.getAllByText("生成练习").length).toBeGreaterThan(0);
    expect(screen.queryByText(/external market data source/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/涓|鈥|娴疯兘/)).not.toBeInTheDocument();
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
    expect(request.knowledge_coverage.map((item) => item.id)).toEqual(expect.arrayContaining(["basis_spread", "options_optionality", "hedge_ratio_cross_hedge"]));
    expect(request.gas_trading_models.map((item) => item.id)).toEqual(expect.arrayContaining(["gsa_procurement", "lng_regas_sale", "efet_bilateral_sale"]));
  });

  it("includes crude oil hedging as a real AI-generated course track", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    const crudeCard = (await screen.findByText("Crude Oil Hedging")).closest("article");
    expect(crudeCard).not.toBeNull();
    fireEvent.click(within(crudeCard).getByRole("button", { name: /Generate chapter drill/i }));

    expect(await screen.findByText("Brent Cargo Hedge for Refinery Procurement")).toBeInTheDocument();
    expect(screen.getAllByText("Crude procurement / sales hedging").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Brent").length).toBeGreaterThan(0);
    expect(calls.some((call) => call.path === "/api/v1/ai/training-case" && call.body?.template_id === "crude_oil_hedging_basics")).toBe(true);
  });

  it("keeps a crude-specific local case visible when AI generation fails", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true, failTrainingCase: true });

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

  it("shows textbook hedging coverage and gas trading models in the course map", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    fireEvent.click(await screen.findByText("Course Map"));

    expect(await screen.findByText("Textbook-Style Hedging Coverage")).toBeInTheDocument();
    expect(screen.getAllByText("Options and Optionality").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Hedge Ratio and Cross-Hedge").length).toBeGreaterThan(0);
    expect(screen.getByText("Commodity Trading Models")).toBeInTheDocument();
    expect(screen.getByText("Upstream Beach / GSA Supply")).toBeInTheDocument();
    expect(screen.getByText("Crude Cargo Procurement / Sale Hedge")).toBeInTheDocument();
    expect(screen.getByText("LNG Regas Sale")).toBeInTheDocument();
    expect(screen.getByText("Bilateral EFET Sale")).toBeInTheDocument();
  });

  it("scores a multi-leg strategy locally without waiting for AI scoring", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    fireEvent.click(await screen.findByText("Training Workbench"));
    const submitButtons = await screen.findAllByText("Submit strategy");
    fireEvent.click(submitButtons[0]);

    expect(await screen.findByText("91")).toBeInTheDocument();
    expect(calls.some((call) => call.path === "/api/v1/attempts/evaluate")).toBe(false);
  });

  it("maps strategy legs to visible risk coverage before submission", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    fireEvent.click(await screen.findByText("Training Workbench"));

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
    expect(screen.getAllByText("Hedge Instrument Selection").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Generate lesson with AI").length).toBeGreaterThan(0);
  });
});
