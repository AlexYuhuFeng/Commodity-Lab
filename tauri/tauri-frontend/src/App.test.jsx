import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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
    { id: "procurement", label: "Procurement" },
    { id: "sales", label: "Sales" }
  ],
  knowledge_points: [
    { id: "basis_spread", label: "Basis and hub spread", description: "Separate TTF/NBP, FX, and hub basis." },
    { id: "physical_paper_matching", label: "Physical-paper matching", description: "Match GSA, EFET, LNG, swaps, FX, and capacity." }
  ],
  templates: [
    {
      id: "procurement_beach_to_germany",
      group: "procurement",
      business_type: "Upstream beach delivery GSA",
      title: "UK beach delivery sold into Germany",
      summary: "Generate a NBP/TTF, FX, capacity, and physical-paper hedge case.",
      knowledge_points: ["basis_spread", "fx", "physical_paper_matching"],
      required_curves: ["TTF", "NBP", "EURGBP"],
      suggested_leg_types: ["physical", "basis", "fx", "capacity"]
    },
    {
      id: "sales_lng_regas",
      group: "sales",
      business_type: "LNG regas sale",
      title: "Regasified LNG sale during market selloff",
      summary: "Generate a LNG regas sale hedge case.",
      knowledge_points: ["outright_price", "volatility_event"],
      required_curves: ["TTF", "JKM"],
      suggested_leg_types: ["physical", "swap", "basis"]
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

function mockBackend({ aiReady = true, onCall } = {}) {
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
              { id: "DeepSeek-V4-Flash", label: "DeepSeek-V4-Flash", resolved_model: "DeepSeek-V4-Flash", base_url: "http://model.ai.cnooc/member1/deepseek-v4-flash-284b/v1" },
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
        current_version: "1.0.12",
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
    if (path === "/api/v1/ai/training-case") return { template: businessTemplates.templates[0], case: generatedCase };
    if (path === "/api/v1/ai/live-assistant") {
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
      return { current_version: "1.0.12", latest_version: "1.0.12", up_to_date: true, release_url: "https://github.com/AlexYuhuFeng/Commodity-Lab/releases/tag/v1.0.12", assets: [] };
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
    expect(screen.getByText("业务类型")).toBeInTheDocument();
    expect(screen.queryByText(/external market data source/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/涓|鈥|娴疯兘/)).not.toBeInTheDocument();
  });

  it("saves DeepSeek settings with a separate provider contract from Haineng", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: false, onCall: (call) => calls.push(call) });

    fireEvent.click((await screen.findAllByText("Settings"))[0]);
    fireEvent.change(await screen.findByLabelText("API key"), { target: { value: "local-secret" } });
    fireEvent.change(screen.getByLabelText("Provider"), { target: { value: "deepseek" } });
    fireEvent.change(screen.getByLabelText("Model"), { target: { value: "deepseek-v4-flash" } });
    fireEvent.click(screen.getByText("Save"));

    await waitFor(() => expect(calls.some((call) => call.path === "/api/v1/provider-settings")).toBe(true));
    const request = calls.find((call) => call.path === "/api/v1/provider-settings")?.body;
    expect(request.provider).toBe("deepseek");
    expect(request.base_url).toBe("https://api.deepseek.com");
    expect(request.model).toBe("deepseek-v4-flash");
  });

  it("binds Haineng model names to Haineng base URLs", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: false });

    fireEvent.click((await screen.findAllByText("Settings"))[0]);
    expect(screen.getByLabelText("Provider")).toHaveValue("haineng");
    expect(screen.getByLabelText("Model")).toHaveValue("DeepSeek-V4-Flash");
    expect(screen.getByLabelText("Base URL")).toHaveValue("http://model.ai.cnooc/member1/deepseek-v4-flash-284b/v1");

    fireEvent.change(screen.getByLabelText("Model"), { target: { value: "DeepSeek-V4" } });
    expect(screen.getByLabelText("Base URL")).toHaveValue("http://model.ai.cnooc/member1/deepseek-v4-pro-1-5t/v1");
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
    expect(request.model).toBe("DeepSeek-V4");
    expect(request.base_url).toBe("http://model.ai.cnooc/member1/deepseek-v4-pro-1-5t/v1");
  });

  it("generates an AI case from a business template and renders Markdown as formatted content", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    const templateTitle = (await screen.findAllByText("UK beach delivery sold into Germany")).find((node) => node.closest("button"));
    fireEvent.click(templateTitle.closest("button"));

    expect(await screen.findByText("UK Beach Delivery to German Citygate")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Decision task" })).toBeInTheDocument();
    expect(screen.queryByText(/###/)).not.toBeInTheDocument();
    expect(screen.getAllByText("TTF").length).toBeGreaterThan(0);
    expect(screen.getAllByText("NBP").length).toBeGreaterThan(0);
    expect(calls.some((call) => call.path === "/api/v1/ai/training-case" && call.body?.template_id === "procurement_beach_to_germany")).toBe(true);
  });

  it("scores a multi-leg strategy locally without waiting for AI scoring", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    const calls = [];
    renderShell({ aiReady: true, onCall: (call) => calls.push(call) });

    fireEvent.click(await screen.findByText("Submit strategy"));

    expect(await screen.findByText("91")).toBeInTheDocument();
    expect(calls.some((call) => call.path === "/api/v1/attempts/evaluate")).toBe(false);
  });

  it("uses the floating assistant for Markdown answers and safe workspace actions", async () => {
    localStorage.setItem("commodity-lab-locale", "en");
    renderShell({ aiReady: true });

    fireEvent.click(await screen.findByRole("button", { name: "AI" }));
    fireEvent.change(screen.getByPlaceholderText(/Generate a UK beach delivery/), { target: { value: "Show high low close and explain basis." } });
    fireEvent.click(screen.getByText("Send"));

    expect(await screen.findByRole("heading", { name: "Plan" })).toBeInTheDocument();
    expect(screen.queryByText(/###/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("Show high/low/close"));
    expect(screen.getByText("High")).toHaveClass("active");
    expect(screen.getByText("Low")).toHaveClass("active");
  });
});
