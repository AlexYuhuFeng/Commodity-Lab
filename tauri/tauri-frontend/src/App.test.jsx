import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import App from "./App";
import { dictionaries, t } from "./i18n";

const scenarioPayload = {
  categories: [
    { id: "natural_gas", label: "Natural Gas", status: "enabled" },
    { id: "oil_products", label: "Oil Products", status: "constructing" }
  ],
  scenarios: [
    {
      id: "producer_short_hedge",
      title: "Producer Short Hedge",
      summary: "Protect production revenue.",
      commodity: "natural_gas",
      default_symbol: "NG=F"
    }
  ]
};

const contextPayload = {
  scenario: {
    id: "producer_short_hedge",
    title: "Producer Short Hedge",
    summary: "Protect production revenue.",
    exposure: { direction: "long_physical", volume_mmbtu: 100000, risk: "falling_price" },
    recommended_side: "sell",
    recommended_hedge_type: "short_hedge"
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
    receipt_point: "Permian Receipt",
    delivery_point: "Gulf Coast Delivery",
    pipeline_segment: "Permian-Gulf Mainline",
    available_capacity_mmbtu: 75000,
    nominated_mmbtu: 69000,
    utilization_pct: 92,
    congestion_status: "constrained"
  }
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
  it("renders the setup gate when 海能 is not healthy", async () => {
    window.__COMMODITY_LAB_BACKEND__ = async () => ({
      haineng: { ok: false, configured: false },
      data_sources: [
        { id: "platts", label: "Platts", configured: false },
        { id: "yfinance", label: "Yahoo Finance", configured: true },
        { id: "simulated", label: "Simulated", configured: true }
      ]
    });

    render(<App />);

    expect(await screen.findByText("海能 Setup")).toBeInTheDocument();
    expect(screen.getByText("Platts")).toBeInTheDocument();
    expect(screen.getByText("Yahoo Finance")).toBeInTheDocument();
    expect(screen.getByText("Simulated")).toBeInTheDocument();
  });

  it("renders constructing navigation for future categories", async () => {
    window.__COMMODITY_LAB_BACKEND__ = async (method, path) => {
      if (path === "/api/v1/provider-status") {
        return { haineng: { ok: true, configured: true }, data_sources: [] };
      }
      if (path.startsWith("/api/v1/scenarios?")) return scenarioPayload;
      if (path.includes("/context")) return contextPayload;
      return { evaluation: { valid: true, baseline_score: 80, metrics: {} } };
    };

    render(<App />);

    expect(await screen.findByText("Oil Products")).toBeInTheDocument();
    expect(await screen.findByText("Constructing")).toBeInTheDocument();
    expect(screen.getAllByText("Producer Short Hedge").length).toBeGreaterThan(0);
  });

  it("submits an order for deterministic scoring and advisor review", async () => {
    const calls = [];
    window.__COMMODITY_LAB_BACKEND__ = async (method, path, body) => {
      calls.push({ method, path, body });
      if (path === "/api/v1/provider-status") {
        return { haineng: { ok: true, configured: true }, data_sources: [] };
      }
      if (path.startsWith("/api/v1/scenarios?")) return scenarioPayload;
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
    await screen.findByText("Permian Receipt");
    fireEvent.click(await screen.findByText("Submit order"));

    await waitFor(() => expect(screen.getAllByText("88").length).toBeGreaterThan(0));
    expect(await screen.findByText("Good direction. Tighten hedge ratio.")).toBeInTheDocument();
    expect(calls.some((call) => call.path === "/api/v1/attempts/evaluate")).toBe(true);
    expect(calls.some((call) => call.path === "/api/v1/advisor/review")).toBe(true);
  });

  it("requests exam generation through backend helper", async () => {
    const calls = [];
    window.__COMMODITY_LAB_BACKEND__ = async (method, path, body) => {
      calls.push({ method, path, body });
      if (path === "/api/v1/provider-status") {
        return { haineng: { ok: true, configured: true }, data_sources: [] };
      }
      if (path.startsWith("/api/v1/scenarios?")) return scenarioPayload;
      if (path.includes("/context")) return contextPayload;
      if (path === "/api/v1/exam/generate") return { exam: "1. What is the exposure?" };
      return { evaluation: { valid: true, baseline_score: 80, metrics: {} } };
    };

    render(<App />);
    await screen.findByText("Permian Receipt");
    const button = await screen.findByText("Generate exam");
    fireEvent.click(button);

    expect(await screen.findByText("1. What is the exposure?")).toBeInTheDocument();
    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/exam/generate")).toBe(true));
  });
});
