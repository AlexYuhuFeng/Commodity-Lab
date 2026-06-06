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
      { date: "2026-01-03", close: 3.14 }
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
  it("defaults to Mandarin and opens Base Mode without 海能", async () => {
    window.__COMMODITY_LAB_BACKEND__ = async (method, path) => {
      if (path === "/api/v1/provider-status") {
        return {
          haineng: { ok: false, configured: false },
          data_sources: [
            { id: "platts", label: "Platts", configured: false },
            { id: "yfinance", label: "Yahoo Finance", configured: true },
            { id: "simulated", label: "Simulated", configured: true }
          ]
        };
      }
      if (path.startsWith("/api/v1/scenarios?")) {
        return {
          categories: [{ id: "natural_gas", label: "天然气", status: "enabled" }],
          scenarios: [
            {
              ...scenarioPayload.scenarios[0],
              title: "欧洲路径运力约束",
              summary: "托运人在跨境运力趋紧时管理交付地点基差风险。",
              region_label: "欧洲"
            }
          ]
        };
      }
      if (path.startsWith("/api/v1/learning-journey?")) return journeyPayload;
      if (path.includes("/context")) return {
        ...contextPayload,
        scenario: {
          ...contextPayload.scenario,
          title: "欧洲路径运力约束",
          summary: "托运人在跨境运力趋紧时管理交付地点基差风险。",
          region_label: "欧洲"
        }
      };
      return {};
    };

    render(<App />);

    expect(await screen.findByText("基础模式")).toBeInTheDocument();
    expect(await screen.findByText("连接海能")).toBeInTheDocument();
    expect(screen.getAllByText("Platts").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Yahoo Finance").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Simulated").length).toBeGreaterThan(0);
  });

  it("renders constructing navigation for future categories", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    window.__COMMODITY_LAB_BACKEND__ = async (method, path) => {
      if (path === "/api/v1/provider-status") {
        return { haineng: { ok: true, configured: true }, data_sources: [] };
      }
      if (path.startsWith("/api/v1/scenarios?")) return scenarioPayload;
      if (path.startsWith("/api/v1/learning-journey?")) return journeyPayload;
      if (path.includes("/context")) return contextPayload;
      return { evaluation: { valid: true, baseline_score: 80, metrics: {} } };
    };

    render(<App />);

    expect(await screen.findByText("Oil Products")).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByText("Constructing").length).toBeGreaterThan(0));
    expect(screen.getAllByText("Europe Route Capacity Constraint").length).toBeGreaterThan(0);
  });

  it("submits an order for deterministic scoring and advisor review", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    window.__COMMODITY_LAB_BACKEND__ = async (method, path, body) => {
      calls.push({ method, path, body });
      if (path === "/api/v1/provider-status") {
        return { haineng: { ok: true, configured: true }, data_sources: [] };
      }
      if (path.startsWith("/api/v1/scenarios?")) return scenarioPayload;
      if (path.startsWith("/api/v1/learning-journey?")) return journeyPayload;
      if (path.includes("/context")) return contextPayload;
      if (path === "/api/v1/advisor/review") return { answer: "Good direction. Tighten hedge ratio." };
      return {
        evaluation: {
          valid: true,
          baseline_score: 88,
          metrics: { hedge_ratio: 0.6, notional_usd: 210000 },
          mistake_tags: ["under_hedged"],
          score_inputs: { direction_match: true, hedge_type_match: true }
        }
      };
    };

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
    window.__COMMODITY_LAB_BACKEND__ = async (method, path, body) => {
      calls.push({ method, path, body });
      if (path === "/api/v1/provider-status") {
        return { haineng: { ok: true, configured: true }, data_sources: [] };
      }
      if (path.startsWith("/api/v1/scenarios?")) return scenarioPayload;
      if (path.startsWith("/api/v1/learning-journey?")) return journeyPayload;
      if (path.includes("/context")) return contextPayload;
      if (path === "/api/v1/exam/generate") return { exam: "1. What is the exposure?" };
      return { evaluation: { valid: true, baseline_score: 80, metrics: {} } };
    };

    render(<App />);
    await screen.findByText("Zeebrugge Receipt");
    const button = await screen.findByText("AI exam");
    fireEvent.click(button);

    expect(await screen.findByText("1. What is the exposure?")).toBeInTheDocument();
    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/exam/generate")).toBe(true));
  });
});
