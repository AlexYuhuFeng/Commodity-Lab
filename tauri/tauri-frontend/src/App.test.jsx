import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import App from "./App";
import { dictionaries, t } from "./i18n";

const scenarioPayload = {
  categories: [
    { id: "natural_gas", label: "Natural Gas", status: "enabled" },
    { id: "oil_products", label: "Oil Products", status: "constructing" },
    { id: "power", label: "Power", status: "constructing" }
  ],
  scenarios: [
    {
      id: "europe_route_capacity_constraint",
      title: "Europe Route Capacity Constraint",
      summary: "Manage delivery-location basis when cross-border capacity tightens.",
      commodity: "natural_gas",
      region_label: "Europe",
      recommended_hedge_type: "basis_hedge",
      default_symbol: "NG=F"
    }
  ]
};

const contextPayload = {
  scenario: {
    id: "europe_route_capacity_constraint",
    title: "Europe Route Capacity Constraint",
    summary: "Manage delivery-location basis when cross-border capacity tightens.",
    region_label: "Europe",
    exposure: { direction: "short", volume_mmbtu: 60000, risk: "capacity and delivered basis risk" },
    recommended_side: "sell",
    recommended_hedge_type: "basis_hedge",
    default_symbol: "NG=F",
    guided_steps: [
      { id: "understand_exposure", label: "Understand exposure", description: "Identify the route exposure." },
      { id: "inspect_market", label: "Inspect market", description: "Check source and capacity." },
      { id: "place_hedge", label: "Place hedge", description: "Choose side and hedge type." }
    ]
  },
  market: {
    source: "sample",
    source_label: "Simulated",
    data_source: "simulated",
    data_source_label: "Simulated",
    symbol: "NG=F",
    unit: "USD/MMBtu",
    latest_price: 3.52,
    price_series: [
      { date: "2026-01-02", close: 3.08 },
      { date: "2026-01-03", close: 3.14 },
      { date: "2026-01-04", close: 3.31 },
      { date: "2026-01-05", close: 3.22 },
      { date: "2026-01-06", close: 3.52 }
    ],
    metadata: { requested_source_label: "Simulated", returned_source_label: "Simulated" }
  },
  capacity: {
    receipt_point: "Zeebrugge Receipt",
    delivery_point: "THE Delivery",
    pipeline_segment: "Northwest Europe Cross-Border Route",
    available_capacity_mmbtu: 75000,
    nominated_mmbtu: 69000,
    utilization_pct: 92,
    congestion_status: "constrained"
  }
};

const journeyPayload = {
  mode: "adaptive",
  profile: { attempt_count: 0 },
  recommendations: [
    {
      scenario_id: "europe_route_capacity_constraint",
      title: "Europe Route Capacity Constraint",
      region: "europe",
      skill_id: "capacity_route",
      ai_capability: "trade_playbook",
      reason: "Capacity and route skill is weak; use Europe gas route/capacity checks before trade execution.",
      priority: 1
    }
  ]
};

function mockBackend({ aiReady = true, onCall } = {}) {
  window.__COMMODITY_LAB_BACKEND__ = async (method, path, body) => {
    onCall?.({ method, path, body });
    if (path === "/api/v1/provider-status") {
      return {
        haineng: {
          ok: aiReady,
          configured: aiReady,
          model: "V4-Flash",
          resolved_model: "deepseek-v4-flash"
        },
        data_sources: [
          { id: "platts", label: "Platts", configured: false },
          { id: "yfinance", label: "Yahoo Finance", configured: true },
          { id: "simulated", label: "Simulated", configured: true }
        ]
      };
    }
    if (path.startsWith("/api/v1/scenarios?")) return scenarioPayload;
    if (path.startsWith("/api/v1/learning-journey?")) return journeyPayload;
    if (path.includes("/context")) return contextPayload;
    if (path === "/api/v1/provider-settings") {
      return {
        haineng: { ok: true, configured: true, model: body.model, resolved_model: "deepseek-v4-flash" },
        data_sources: []
      };
    }
    if (path === "/api/v1/advisor/review") return { answer: "Good direction. Tighten hedge ratio." };
    if (path === "/api/v1/exam/generate") return { exam: "1. What is the exposure?" };
    if (path === "/api/v1/ai/generate") return { answer: "Playbook: check capacity, basis, liquidity, and limits." };
    if (path === "/api/v1/attempts/evaluate") {
      return {
        evaluation: {
          valid: true,
          baseline_score: 88,
          metrics: { hedge_ratio: 0.6, notional_usd: 210000 },
          mistake_tags: ["under_hedged"],
          score_inputs: { direction_match: true, hedge_type_match: true }
        },
        journey: journeyPayload
      };
    }
    return {};
  };
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
    expect(t("missingRequired", "fr")).toBe("Missing required settings");
  });
});

describe("Commodity Lab shell", () => {
  it("defaults to readable Mandarin and keeps AI setup collapsed when connected", async () => {
    mockBackend({ aiReady: true });

    render(<App />);

    expect(await screen.findByText("AI 全功能")).toBeInTheDocument();
    expect(await screen.findByText("AI 设置")).toBeInTheDocument();
    expect(screen.getByText("中文")).toBeInTheDocument();
    expect(screen.queryByText(/涓|鈥|娴疯兘/)).not.toBeInTheDocument();
    expect(screen.getAllByText("Platts").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Yahoo Finance").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Simulated").length).toBeGreaterThan(0);
  });

  it("renders constructing navigation for future categories", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    mockBackend({ aiReady: true });

    render(<App />);

    expect(await screen.findByText("Oil Products")).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText("Constructing").length).toBeGreaterThan(0));
    expect(screen.getAllByText("Europe Route Capacity Constraint").length).toBeGreaterThan(0);
  });

  it("saves provider settings with a Flash model dropdown", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    mockBackend({ aiReady: false, onCall: (call) => calls.push(call) });

    render(<App />);
    fireEvent.change(await screen.findByLabelText("API key"), { target: { value: "local-secret" } });
    fireEvent.change(screen.getByLabelText("Base URL"), { target: { value: "https://api.deepseek.com" } });
    fireEvent.change(screen.getByLabelText("Model"), { target: { value: "V4-Flash" } });
    fireEvent.click(screen.getByText("Unlock"));

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/provider-settings")).toBe(true));
    expect(calls.find((call) => call.path === "/api/v1/provider-settings")?.body.model).toBe("V4-Flash");
  });

  it("submits an order for deterministic scoring and advisor review", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    mockBackend({ aiReady: true, onCall: (call) => calls.push(call) });

    render(<App />);
    await screen.findByText("Zeebrugge Receipt");
    fireEvent.click(await screen.findByText("Submit decision"));

    await waitFor(() => expect(screen.getAllByText("88").length).toBeGreaterThan(0));
    expect(await screen.findByText("Good direction. Tighten hedge ratio.")).toBeInTheDocument();
    expect(calls.some((call) => call.path === "/api/v1/attempts/evaluate")).toBe(true);
    expect(calls.some((call) => call.path === "/api/v1/advisor/review")).toBe(true);
  });

  it("requests exam generation through backend helper", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    mockBackend({ aiReady: true, onCall: (call) => calls.push(call) });

    render(<App />);
    await screen.findByText("Zeebrugge Receipt");
    const button = await screen.findByText("AI exam");
    fireEvent.click(button);

    expect(await screen.findByText("1. What is the exposure?")).toBeInTheDocument();
    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/exam/generate")).toBe(true));
  });

  it("shows AI thinking progress immediately while running a training action", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    mockBackend({
      aiReady: true,
      onCall: (call) => calls.push(call)
    });

    render(<App />);
    await screen.findByText("Zeebrugge Receipt");
    fireEvent.click(await screen.findByText("Trade playbook"));

    expect(await screen.findByText("Haineng is thinking")).toBeInTheDocument();
    expect(screen.getByText("Reading scenario and exposure")).toBeInTheDocument();
    expect(await screen.findByText("Playbook: check capacity, basis, liquidity, and limits.")).toBeInTheDocument();
    await waitFor(() =>
      expect(calls.some((call) => call.path === "/api/v1/ai/generate" && call.body?.capability === "trade_playbook")).toBe(true)
    );
  });
});
