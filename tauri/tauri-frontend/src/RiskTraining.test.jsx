import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import RiskTraining from "./RiskTraining";
import { backendRequest } from "./api";
vi.mock("./api", () => ({ backendRequest: vi.fn() }));
const policy = { profile: "corporate", maximum_hedge_ratio: "0.8", liquidity_limit_eur: "100000", version: "illustrative-v1" };
const fact = { en: "A trading company buys November gas at TTF plus basis for fixed-price customer sales.", zh: "公司按TTF加区域基差采购11月天然气。" };
function view(checkpoint = 0) {
  const current = { date: checkpoint ? "2026-10-15" : "2026-10-01", fact, physical_mwh: checkpoint ? "8000" : "10000", index_eur_mwh: "40", basis_eur_mwh: "2" };
  return { id: "session1", checkpoint, complete: false, policy, current, position_mwh: "0", collateral_estimate_eur: 0, current_compliance: { permitted: true }, visible_timeline: [current], decisions: [] };
}
function fillDecision() {
  fireEvent.click(screen.getByRole("button", { name: "50% coverage" }));
  fireEvent.change(screen.getByLabelText("Which commercial risk are you managing?"), { target: { value: "rising_purchase_cost" } });
  fireEvent.change(screen.getByLabelText("What remains after a TTF hedge?"), { target: { value: "basis_remains" } });
  fireEvent.change(screen.getByLabelText("What must the risk manager plan for?"), { target: { value: "collateral_needed" } });
  fireEvent.change(screen.getByLabelText("Commercial rationale"), { target: { value: "Hedge purchase costs while managing basis and collateral." } });
}
beforeEach(() => { localStorage.clear(); vi.clearAllMocks(); });
afterEach(cleanup);
describe("risk training learner workflow", () => {
  it("offers bilingual policy setup and separate educational profiles", () => {
    render(<RiskTraining locale="zh" />);
    expect(screen.getByRole("heading", { name: "欧洲天然气风险实验室" })).toBeInTheDocument();
    expect(screen.getByText(/不代表公司政策/)).toBeInTheDocument();
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "advanced" } });
    expect(screen.getByLabelText("纸货 / 合格实货最高比例（%）")).toHaveValue(150);
    expect(screen.getByLabelText("要求合格实货支持")).not.toBeChecked();
  });
  it("starts, submits a total target, reveals a checkpoint and preserves assessment", async () => {
    backendRequest.mockResolvedValueOnce(view()).mockResolvedValueOnce({ ...view(1), position_mwh: "5000", latest_assessment: { compliance: { permitted: true, reasons: [] }, decision_quality: { diagnostic_score: 100, remediation: [] } } });
    render(<RiskTraining />);
    fireEvent.click(screen.getByRole("button", { name: "Start scenario" }));
    await screen.findByText("Decision checkpoint 1 / 2");
    expect(screen.queryByText("2026-11-30")).not.toBeInTheDocument();
    fillDecision();
    fireEvent.click(screen.getByRole("button", { name: "Submit decision and reveal next checkpoint" }));
    await screen.findByText("Decision checkpoint 2 / 2");
    expect(backendRequest).toHaveBeenLastCalledWith("POST", "/api/v1/risk-training/sessions/session1/decisions", expect.objectContaining({ target_mwh: "5000", checkpoint: 0 }));
    expect(screen.getByText("Permitted in this simulation")).toBeInTheDocument();
    expect(localStorage.getItem("commodity-lab-risk-session-v1")).toBe("session1");
  });
  it("resumes a saved session, explains blocked proposals and offers offline coaching", async () => {
    localStorage.setItem("commodity-lab-risk-session-v1", "session1");
    const blocked = { ...view(), latest_assessment: { compliance: { permitted: false, reasons: ["maximum_hedge_ratio_exceeded"] }, decision_quality: { diagnostic_score: 67, remediation: ["basis"] } } };
    backendRequest.mockResolvedValueOnce(view()).mockResolvedValueOnce(blocked).mockResolvedValueOnce({ mode: "offline", answer: "Consider remaining basis.", graded: false });
    render(<RiskTraining />);
    await screen.findByText("Decision checkpoint 1 / 2"); fillDecision();
    fireEvent.click(screen.getByRole("button", { name: "Submit decision and reveal next checkpoint" }));
    await screen.findByText("Proposal blocked — revise and resubmit");
    expect(screen.getByText("Paper exceeds the configured physical limit")).toBeInTheDocument();
    expect(screen.getByLabelText("Commercial rationale")).toHaveValue("Hedge purchase costs while managing basis and collateral.");
    fireEvent.click(screen.getByRole("button", { name: "Ask the coach" }));
    await screen.findByText("Offline coaching"); expect(screen.getByText("Consider remaining basis.")).toBeInTheDocument();
  });
  it("shows an actionable error and can restart after missing saved session", async () => {
    localStorage.setItem("commodity-lab-risk-session-v1", "gone"); backendRequest.mockRejectedValueOnce(new Error("404"));
    render(<RiskTraining />);
    expect(await screen.findByRole("alert")).toHaveTextContent("saved session is unavailable");
    backendRequest.mockResolvedValueOnce(view()); fireEvent.click(screen.getByRole("button", { name: "Start scenario" }));
    await screen.findByText("Decision checkpoint 1 / 2");
    fireEvent.click(screen.getByRole("button", { name: "New scenario" }));
    expect(screen.getByRole("button", { name: "Start scenario" })).toBeInTheDocument();
  });
});

function crudeView(inventory = false) {
  const current = { date: "2026-10-01", fact, eligible_quantity: inventory ? "300000" : "600000", benchmark_price: "80", grade_basis: "1", freight_per_unit: "2" };
  return { id: "crude1", scenario_id: inventory ? "crude-merchant-inventory-v1" : "crude-refinery-procurement-v1", checkpoint: 0, complete: false, current, visible_timeline: [current], physical_contract: { fixed_price: inventory ? "77" : "94" }, conventions: { commodity: "crude_oil", unit: "bbl", currency: "USD", instrument: "brent_swap", pricing_period: "2026-11", delivery_period: "2026-11", pricing_window_start: "2026-11-05", pricing_window_end: "2026-11-25" }, position_quantity: "0", collateral_estimate: 0, hedge_sign: inventory ? -1 : 1, policy: { ...policy, currency: "USD", liquidity_limit: "10000000" }, current_compliance: { permitted: true }, decisions: [], visible_fixings: [] };
}
it("starts crude with a USD policy and keeps the saved gas session separate", async () => {
  localStorage.setItem("commodity-lab-risk-session-v1", "gas1");
  backendRequest.mockResolvedValueOnce(crudeView());
  render(<RiskTraining productScope="crude_oil" />);
  expect(backendRequest).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Start scenario" }));
  await screen.findByText("Decision checkpoint 1 / 2");
  expect(backendRequest).toHaveBeenCalledWith("POST", "/api/v1/risk-training/scenario-sessions", expect.objectContaining({ scenario_id: "crude-refinery-procurement-v1", policy: expect.objectContaining({ currency: "USD", liquidity_limit: "10000000" }) }));
  expect(localStorage.getItem("commodity-lab-risk-session-v1")).toBe("gas1");
  expect(localStorage.getItem("commodity-lab-risk-session-v1:crude_oil")).toBe("crude1");
});
it("submits a signed inventory hedge with explicit Brent conventions", async () => {
  backendRequest.mockResolvedValueOnce(crudeView(true)).mockResolvedValueOnce({ ...crudeView(true), checkpoint: 1, position_quantity: "-240000", latest_assessment: { compliance: { permitted: true, reasons: [] }, decision_quality: { diagnostic_score: 100, remediation: [] } } });
  render(<RiskTraining productScope="crude_oil" />);
  fireEvent.change(screen.getByLabelText("Trading-company mandate"), { target: { value: "crude-merchant-inventory-v1" } });
  fireEvent.click(screen.getByRole("button", { name: "Start scenario" }));
  await screen.findByText("Decision checkpoint 1 / 2");
  fireEvent.click(screen.getByRole("button", { name: "Policy maximum" }));
  expect(screen.getByLabelText("Target total short swap position (bbl)")).toHaveValue(-240000);
  fireEvent.change(screen.getByLabelText("Which commercial risk are you managing?"), { target: { value: "falling_sales_revenue" } });
  fireEvent.change(screen.getByLabelText("What remains after a Brent hedge?"), { target: { value: "basis_remains" } });
  fireEvent.change(screen.getByLabelText("What must the risk manager plan for?"), { target: { value: "collateral_needed" } });
  fireEvent.change(screen.getByLabelText("Commercial rationale"), { target: { value: "Protect owned inventory while retaining grade basis and funding collateral." } });
  fireEvent.click(screen.getByRole("button", { name: "Submit decision and reveal next checkpoint" }));
  await screen.findByText("Decision checkpoint 2 / 2");
  expect(backendRequest).toHaveBeenLastCalledWith("POST", "/api/v1/risk-training/sessions/crude1/decisions", expect.objectContaining({ target_quantity: "-240000", currency: "USD", unit: "bbl", instrument: "brent_swap", pricing_window_start: "2026-11-05", exposure_answer: "falling_sales_revenue" }));
});
it("resumes crude in Chinese with a blocked assessment and the inventory direction", async () => {
  localStorage.setItem("commodity-lab-risk-session-v1:crude_oil", "crude1");
  backendRequest.mockResolvedValueOnce({ ...crudeView(true), latest_assessment: { compliance: { permitted: false, reasons: ["physical_backing_required"] }, decision_quality: { diagnostic_score: 67, remediation: ["exposure"] } } });
  render(<RiskTraining productScope="crude_oil" locale="zh" />);
  await screen.findByText("提案被阻止，请修改后重新提交");
  expect(screen.getByLabelText("目标掉期空头总量（桶）")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "原油风险实验室" })).toBeInTheDocument();
});
