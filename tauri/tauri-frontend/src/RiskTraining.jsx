import React, { useEffect, useState } from "react";
import { backendRequest } from "./api";
import "./risk-training.css";

const words = {
  en: {
    title: "European gas risk lab", subtitle: "Manage a commercial exposure. Defend your decisions.", synthetic: "Synthetic training • no live execution", setup: "Training environment", corporate: "Corporate Compliance Training", academy: "Professional Trading Academy", advanced: "Advanced Strategy Laboratory", disclaimer: "Illustrative policy, not company policy or trading authorization. Only validated training swaps are available in this case.", ratio: "Maximum paper / eligible physical ratio (%)", approval: "Approval required above (%)", limit: "Collateral limit (EUR)", backing: "Require eligible physical backing", start: "Start scenario", restart: "New scenario", checkpoint: "Decision checkpoint", settled: "Settlement review", brief: "Commercial brief", market: "Information available now", index: "TTF index / quote", basis: "Regional basis", physical: "Eligible November purchase", position: "Current paper position", settlementPosition: "Hedge carried into settlement", settlementCollateral: "Collateral estimate before settlement", collateral: "Estimated collateral", marginNote: "Simplified 10% initial margin plus adverse net mark-to-market; not clearing-house margin.", conventions: "EUR/MWh • November 2026 pricing and delivery • cash-settled training swaps", decision: "Your hedge decision", target: "Target total long swap position (MWh)", targetNote: "Enter the total position to hold after this decision, not an additional order. Negative values are short positions.", hold: "Hold current position", half: "50% coverage", max: "Policy maximum", signed: "Negative / short positions", approvalCheck: "Training approval obtained (self-declared)", rationale: "Commercial rationale", rationaleHelp: "Explain objective, sizing, basis risk and liquidity trade-offs (20+ characters). An instructor reviews reasoning.", exposureQ: "Which commercial risk are you managing?", exposureA: "Rising purchase cost", exposureB: "Falling sales revenue", basisQ: "What remains after a TTF hedge?", basisA: "Regional basis remains", basisB: "All price risk is removed", liquidityQ: "What must the risk manager plan for?", liquidityA: "Collateral may be needed", liquidityB: "Expected profit guarantees cash", choose: "Choose an answer", submit: "Submit decision and reveal next checkpoint", busy: "Working…", assessment: "Independent assessment", compliance: "Policy adherence", permitted: "Permitted in this simulation", blocked: "Proposal blocked — revise and resubmit", quality: "Diagnostic evidence", reasoning: "Rationale requires instructor review. One case does not establish mastery.", financial: "Financial outcome", salesCash: "Physical sales cash flow", salePrice: "Fixed customer sales price", commercialMargin: "Trading margin before other costs", physicalMargin: "Unhedged physical margin", physicalCash: "Physical purchase cash flow", derivativeCash: "Swap cash flow", net: "Net procurement cost", budget: "Volume-adjusted initial budget", variance: "Budget variance (positive = saving)", offset: "Realized cost-shock offset", offsetNote: "Swap receipts divided by purchase-cost increase against the initial price/basis budget. This is an ex-post measure, not statistical hedge effectiveness or decision quality.", peak: "Peak estimated collateral", basisCost: "Unhedged basis cost", noPnl: "Trading margin includes physical sales, purchases and swap cash flows. Freight, fees, tax and financing are excluded; this is not full accounting PnL.", coach: "Coaching & remediation", ask: "Ask the coach", offline: "Offline coaching", ai: "AI coaching • ungraded", timeline: "Revealed evidence timeline", history: "Decision audit", observedBreach: "Existing position breaches current policy. Resize or obtain the required training approval before proceeding.", error: "The request failed. Check the backend and retry; your saved session remains available.", missing: "The saved session is unavailable. Start a new scenario.", diagnosticHelp: "Answers are assessed as provisional evidence, separately from hedge cash flows.", exposure: "Exposure", liquidity: "Liquidity", remediation: "Review:", export: "Download decision record", empty: "No future observations are available until you submit a permitted decision.", policy: "Session policy", version: "Version", cap: "Paper limit", local: "Saved locally on this device", codes: {
      instrument_not_permitted: "Instrument is not permitted", physical_backing_required: "Position needs matching physical backing and direction", maximum_hedge_ratio_exceeded: "Paper exceeds the configured physical limit", approval_required: "Training approval is required", liquidity_limit_exceeded: "Estimated collateral exceeds the limit"
    }
  },
  zh: {
    title: "欧洲天然气风险实验室", subtitle: "管理商业敞口，解释决策依据。", synthetic: "合成训练数据 · 无实盘执行", setup: "训练环境", corporate: "企业合规培训", academy: "专业交易学院", advanced: "高级策略实验室", disclaimer: "示例政策，不代表公司政策或交易授权。本案例仅提供经过验证的训练掉期。", ratio: "纸货 / 合格实货最高比例（%）", approval: "超过此比例须审批（%）", limit: "抵押资金限额（欧元）", backing: "要求合格实货支持", start: "开始情景", restart: "新建情景", checkpoint: "决策时点", settled: "结算复盘", brief: "商业背景", market: "当前可知信息", index: "TTF指数 / 报价", basis: "区域基差", physical: "11月合格采购量", position: "当前纸货头寸", settlementPosition: "结算前持有的套保头寸", settlementCollateral: "结算前抵押资金估算", collateral: "估算抵押资金", marginNote: "简化估算：10%初始保证金加不利净盯市金额，并非清算所保证金。", conventions: "欧元/MWh · 2026年11月定价与交割 · 现金结算训练掉期", decision: "套保决策", target: "目标掉期多头总量（MWh）", targetNote: "输入决策后的总头寸，而非新增订单。负数代表空头。", hold: "维持现有头寸", half: "50%覆盖", max: "政策上限", signed: "负数 / 空头头寸", approvalCheck: "已获得训练审批（自行声明）", rationale: "商业理由", rationaleHelp: "解释目标、规模、基差及流动性取舍（至少20个字符）。理由由讲师审核。", exposureQ: "你在管理哪类商业风险？", exposureA: "采购成本上涨", exposureB: "销售收入下降", basisQ: "TTF套保后仍有哪些风险？", basisA: "区域基差仍然存在", basisB: "全部价格风险已消除", liquidityQ: "风险经理需要规划什么？", liquidityA: "可能需要抵押资金", liquidityB: "预期利润保证现金充足", choose: "请选择答案", submit: "提交决策并揭示下一时点", busy: "处理中…", assessment: "独立评估", compliance: "政策遵循", permitted: "本模拟允许", blocked: "提案被阻止，请修改后重新提交", quality: "诊断证据", reasoning: "商业理由需讲师审核，单个案例不代表已掌握专业能力。", financial: "财务结果", salesCash: "实货销售现金流", salePrice: "客户固定销售价格", commercialMargin: "其他费用前交易利润", physicalMargin: "未套保实货利润", physicalCash: "实货采购现金流", derivativeCash: "掉期现金流", net: "净采购成本", budget: "按最终数量调整的初始预算", variance: "预算差异（正数为节省）", offset: "已实现成本冲击抵消率", offsetNote: "掉期收入除以相对初始价格及基差预算的采购成本增量。这是事后指标，不等于统计套保有效性或决策质量。", peak: "峰值估算抵押资金", basisCost: "未套保基差成本", noPnl: "交易利润包含实货销售、采购与掉期现金流，不包含运费、费用、税项及融资成本，并非完整会计损益。", coach: "辅导与补救练习", ask: "请求教练辅导", offline: "离线辅导", ai: "AI辅导 · 不计分", timeline: "已揭示信息时间线", history: "决策记录", observedBreach: "现有头寸已违反当前政策。请调整规模或取得所需训练审批后再继续。", error: "请求失败，请检查后端并重试。已保存的情景仍可恢复。", missing: "已保存的情景不可用，请新建情景。", diagnosticHelp: "答案作为临时能力证据评估，与套保现金流分开。", exposure: "敞口", liquidity: "流动性", remediation: "需复习：", export: "下载决策记录", empty: "提交合规决策前无法查看未来信息。", policy: "情景政策", version: "版本", cap: "纸货限额", local: "记录保存在本机", codes: {
      instrument_not_permitted: "不允许该工具", physical_backing_required: "头寸需要匹配的实货支持及方向", maximum_hedge_ratio_exceeded: "纸货超过配置的实货比例限额", approval_required: "需要训练审批", liquidity_limit_exceeded: "估算抵押资金超过限额"
    }
  }
};

const crudeWords = {
  en: { title: "Crude oil risk lab", limit: "Collateral limit (USD)", index: "Brent strip quote / settlement average", basis: "Grade basis", physical: "Eligible cargo quantity", conventions: "USD/bbl • November 2026 pricing and delivery • synthetic cash-settled Brent swaps", basisQ: "What remains after a Brent hedge?", basisA: "Grade basis and freight remain", noPnl: "Trading margin includes physical sales, purchase cost, freight and swap cash flows. Fees, tax and financing are excluded; this is not full accounting PnL.", offsetNote: "Swap receipts divided by the adverse physical-margin change against initial prices and final quantity. This is an ex-post measure, not statistical hedge effectiveness or decision quality.", offset: "Realized adverse margin-shock offset", scenario: "Trading-company mandate", refinery: "Refinery supply procurement", inventory: "Owned merchant inventory", freight: "Freight per barrel", freightCash: "Freight cash flow", historic: "Historical inventory purchase price", short: "Target total short swap position (bbl)", long: "Target total long swap position (bbl)", cash: "Dated cash-flow ledger", settlementCash: "Settlement-date net cash flow", baseline: "Initial-price physical margin", variance: "Margin variance against initial prices", basisCost: "Grade-basis cash component", fixings: "Revealed synthetic pricing fixings", pricing: "Pricing window", rounding: "Three equally weighted synthetic fixings; prices rounded to six decimals and cash to cents. Not exchange settlement.", historyNote: "The inventory purchase was paid before this scenario. It contributes to lifecycle margin, but is excluded from settlement-date cash flow." },
  zh: { title: "原油风险实验室", limit: "抵押资金限额（美元）", index: "Brent期间报价 / 结算均价", basis: "品质基差", physical: "合格船货数量", conventions: "美元/桶 · 2026年11月定价与交割 · 合成现金结算Brent掉期", basisQ: "Brent套保后仍有哪些风险？", basisA: "品质基差及运费仍然存在", noPnl: "交易利润包含实货销售、采购成本、运费与掉期现金流，不包含费用、税项及融资，并非完整会计损益。", offsetNote: "掉期收入除以按初始价格和最终数量计算的实货利润不利变动。这是事后指标，不等于统计套保有效性或决策质量。", offset: "已实现不利利润冲击抵消率", scenario: "贸易公司业务委托", refinery: "炼厂供应采购", inventory: "自有贸易库存", freight: "每桶运费", freightCash: "运费现金流", historic: "历史库存采购价格", short: "目标掉期空头总量（桶）", long: "目标掉期多头总量（桶）", cash: "按日期记录的现金流", settlementCash: "结算日净现金流", baseline: "初始价格下实货利润", variance: "相对初始价格的利润差异", basisCost: "品质基差现金流影响", fixings: "已揭示的合成定价数据", pricing: "定价窗口", rounding: "三个等权重合成定价数据；价格四舍五入至六位小数，现金至分。并非交易所结算。", historyNote: "库存采购已在情景开始前支付。该成本计入全周期利润，但不计入结算日现金流。" }
};
function normalizeCrude(data) {
  const map = o => ({ ...o, index_eur_mwh: o.benchmark_price, basis_eur_mwh: o.grade_basis, physical_mwh: o.eligible_quantity, sale_price_eur_mwh: data.physical_contract.fixed_price });
  const f = data.financial;
  return { ...data, _record: data, current: map(data.current), position_mwh: data.position_quantity, collateral_estimate_eur: data.collateral_estimate,
    policy: { ...data.policy, liquidity_limit_eur: data.policy.liquidity_limit },
    financial: f && { ...f, physical_sales_cash_flow_eur:f.physical_sales_cash_flow, physical_cash_flow_eur:f.physical_purchase_cash_flow, derivative_cash_flow_eur:f.derivative_cash_flow, commercial_margin_before_costs_eur:f.commercial_margin_before_costs, unhedged_physical_margin_eur:f.unhedged_physical_margin, net_procurement_cost_eur:f.net_procurement_cost, volume_adjusted_budget_eur:f.volume_adjusted_baseline_physical_margin, budget_variance_eur:f.margin_variance, basis_cost_eur:f.grade_basis_cash_component, peak_collateral_estimate_eur:f.peak_collateral_estimate, cost_shock_offset_pct:f.adverse_margin_shock_offset_pct },
    decisions: data.decisions.map(r => ({ ...r, decision: { ...r.decision, target_mwh:r.decision.target_quantity } })) };
}

export default function RiskTraining({ locale = "en", productScope = "natural_gas" }) {
  const language = locale.startsWith("zh") ? "zh" : "en";
  const isCrude = productScope === "crude_oil";
  const key = isCrude ? "commodity-lab-risk-session-v1:crude_oil" : "commodity-lab-risk-session-v1";
  const [scenario, setScenario] = useState("crude-refinery-procurement-v1");
  const inventory = sessionInventory();
  function sessionInventory() { return isCrude && scenario === "crude-merchant-inventory-v1"; }
  const w = { ...words[language], ...(isCrude ? crudeWords[language] : {}) };
  if (isCrude) { w.budget = w.baseline; w.target = inventory ? w.short : w.long; if (inventory) w.salePrice = w.historic; }
  const unit = isCrude ? (language === "zh" ? "桶" : "bbl") : "MWh";
  const adapt = data => isCrude ? normalizeCrude(data) : data;
  const [session, setSession] = useState(null);
  const [profile, setProfile] = useState("corporate");
  const [ratio, setRatio] = useState(80);
  const [approvalRatio, setApprovalRatio] = useState(80);
  const [limit, setLimit] = useState(isCrude ? 10000000 : 100000);
  const [backing, setBacking] = useState(true);
  const [target, setTarget] = useState("0");
  const [rationale, setRationale] = useState("");
  const [answers, setAnswers] = useState({});
  const [approved, setApproved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [coaching, setCoaching] = useState(null);
  const [assessment, setAssessment] = useState(null);
  useEffect(() => {
    let active = true;
    const id = localStorage.getItem(key);
    if (id) {
      setBusy(true);
      backendRequest("GET", `/api/v1/risk-training/sessions/${id}`).then(data => {
        if (active) { setSession(adapt(data)); setTarget(isCrude ? data.position_quantity : data.position_mwh); if (isCrude) setScenario(data.scenario_id); }
      }).catch(() => { if (active) setError("missing"); }).finally(() => { if (active) setBusy(false); });
    }
    return () => { active = false; };
  }, []);
  const money = value => new Intl.NumberFormat(language === "zh" ? "zh-CN" : "en-IE", { style: "currency", currency: isCrude ? "USD" : "EUR", maximumFractionDigits: 2 }).format(value);
  const quantity = value => new Intl.NumberFormat(language === "zh" ? "zh-CN" : "en-IE").format(Number(value));
  async function run(action) {
    setBusy(true); setError("");
    try { await action(); } catch { setError("error"); } finally { setBusy(false); }
  }
  function changeProfile(value) {
    setProfile(value); setRatio(value === "corporate" ? 80 : value === "academy" ? 100 : 150);
    setApprovalRatio(value === "corporate" ? 80 : 200); setBacking(value === "corporate");
  }
  function start(event) {
    event.preventDefault();
    run(async () => {
      const policy = { profile, maximum_hedge_ratio: String(Number(ratio) / 100), approval_ratio: String(Number(approvalRatio) / 100), physical_backing_required: backing };
      const data = adapt(await backendRequest("POST", isCrude ? "/api/v1/risk-training/scenario-sessions" : "/api/v1/risk-training/sessions", isCrude ? { scenario_id: scenario, policy: { ...policy, currency: "USD", liquidity_limit: String(limit) } } : { ...policy, liquidity_limit_eur: String(limit) }));
      localStorage.setItem(key, data.id); setSession(data); setTarget("0"); setAssessment(null); setCoaching(null); setRationale(""); setAnswers({});
    });
  }
  function decide(event) {
    event.preventDefault();
    run(async () => {
      const { commodity, unit, currency, instrument, pricing_period, delivery_period, pricing_window_start, pricing_window_end } = session.conventions ?? {};
      const position = isCrude ? { target_quantity: target, commodity, unit, currency, instrument, pricing_period, delivery_period, pricing_window_start, pricing_window_end } : { target_mwh: target };
      const data = adapt(await backendRequest("POST", `/api/v1/risk-training/sessions/${session.id}/decisions`, { checkpoint: session.checkpoint, ...position, rationale, approval_obtained: approved, ...answers }));
      setAssessment(data.latest_assessment); setSession(data); setCoaching(null);
      if (data.latest_assessment.compliance.permitted) { setTarget(data.position_mwh); setRationale(""); setAnswers({}); setApproved(false); }
    });
  }
  function reset() { localStorage.removeItem(key); setSession(null); setAssessment(null); setCoaching(null); setError(""); }
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(session._record ?? session, null, 2)], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = `${isCrude ? "crude" : "gas"}-training-${session.id}.json`; a.click(); URL.revokeObjectURL(url);
  }
  const latest = assessment ?? session?.latest_assessment ?? session?.decisions?.at(-1)?.assessment;
  const diagnostics = [
    ["exposure_answer", w.exposureQ, [["rising_purchase_cost", w.exposureA], ["falling_sales_revenue", w.exposureB]]],
    ["basis_answer", w.basisQ, [["basis_remains", w.basisA], ["all_risk_removed", w.basisB]]],
    ["liquidity_answer", w.liquidityQ, [["collateral_needed", w.liquidityA], ["profit_guarantees_cash", w.liquidityB]]]
  ];
  return <section className={`risk-lab${isCrude ? " risk-crude" : ""}`} aria-labelledby="risk-title">
    <header className="risk-header"><div><span className="risk-badge">{w.synthetic}</span><h1 id="risk-title">{w.title}</h1><p>{w.subtitle}</p></div>{session && <button type="button" disabled={busy} onClick={reset}>{w.restart}</button>}</header>
    {error && <p role="alert" className="risk-warning">{w[error]}</p>}
    {busy && <p role="status">{w.busy}</p>}
    {!session ? <form onSubmit={start} className="risk-card risk-setup"><h2>{w.setup}</h2><p>{w.disclaimer}</p>
      {isCrude && <label>{w.scenario}<select value={scenario} onChange={e => setScenario(e.target.value)}><option value="crude-refinery-procurement-v1">{w.refinery}</option><option value="crude-merchant-inventory-v1">{w.inventory}</option></select></label>}
      <label>{w.setup}<select value={profile} onChange={e => changeProfile(e.target.value)}>{["corporate", "academy", "advanced"].map(p => <option key={p} value={p}>{w[p]}</option>)}</select></label>
      <div className="risk-fields"><label>{w.ratio}<input type="number" min="0" max="200" step="1" required value={ratio} onChange={e => setRatio(e.target.value)} /></label><label>{w.approval}<input type="number" min="0" max="200" required value={approvalRatio} onChange={e => setApprovalRatio(e.target.value)} /></label><label>{w.limit}<input type="number" min="1" max={isCrude ? "100000000" : "10000000"} required value={limit} onChange={e => setLimit(e.target.value)} /></label></div>
      <label className="risk-check"><input type="checkbox" checked={backing} onChange={e => setBacking(e.target.checked)} />{w.backing}</label>
      <button className="risk-primary" disabled={busy}>{w.start}</button>
    </form> : <>
      <div className="risk-progress"><strong>{session.complete ? w.settled : `${w.checkpoint} ${session.checkpoint + 1} / 2`}</strong><span>{w.local}</span></div>
      <div className="risk-grid"><div>
        <article className="risk-card"><h2>{w.brief}</h2><p>{session.current.fact[language]}</p><p className="risk-muted">{w.conventions}</p>
          <h3>{w.market} · {session.current.date}</h3><dl className="risk-metrics">
            {[[w.salePrice, `${money(session.current.sale_price_eur_mwh ?? 60)}/${unit}`], [w.index, `${money(session.current.index_eur_mwh)}/${unit}`], [w.basis, `${money(session.current.basis_eur_mwh)}/${unit}`], [w.physical, `${quantity(session.current.physical_mwh)} ${unit}`], [session.complete ? w.settlementPosition : w.position, `${quantity(session.position_mwh)} ${unit}`], [session.complete ? w.settlementCollateral : w.collateral, money(session.collateral_estimate_eur)]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
          </dl>{isCrude && <><p>{w.freight}: {money(session.current.freight_per_unit)}/{unit}</p><p className="risk-muted">{w.pricing}: {session.conventions.pricing_window_start} – {session.conventions.pricing_window_end}</p></>}<p className="risk-muted">{w.marginNote}</p>
          {!session.current_compliance.permitted && <p role="alert" className="risk-warning">{w.observedBreach}</p>}
        </article>
        <details className="risk-card"><summary>{w.policy}</summary><p>{w[session.policy.profile]} · {w.version}: {session.policy.version}</p><p>{w.cap}: {Number(session.policy.maximum_hedge_ratio) * 100}% · {w.limit}: {money(session.policy.liquidity_limit_eur)}</p><p>{w.disclaimer}</p></details>
        <details className="risk-card"><summary>{w.timeline}</summary><ol>{session.visible_timeline.map(cp => <li key={cp.date}><strong>{cp.date}</strong><p>{cp.fact[language]}</p></li>)}</ol>{!session.complete && <p>{w.empty}</p>}</details>
      </div><div>
        {!session.complete && <form className="risk-card" onSubmit={decide}><h2>{w.decision}</h2><label>{w.target}<input aria-describedby="target-help" type="number" min={isCrude ? "-1000000" : "-20000"} max={isCrude ? "1000000" : "20000"} step="0.01" value={target} onChange={e => setTarget(e.target.value)} required /></label><p id="target-help" className="risk-muted">{w.targetNote}</p>
          <div className="risk-actions">{[[w.hold, session.position_mwh], [w.half, Number(session.current.physical_mwh) * .5 * (session.hedge_sign ?? 1)], [w.max, Number(session.current.physical_mwh) * Number(session.policy.maximum_hedge_ratio) * (session.hedge_sign ?? 1)]].map(([label, value]) => <button key={label} type="button" onClick={() => setTarget(String(value))}>{label}</button>)}</div>
          <label className="risk-check"><input type="checkbox" checked={approved} onChange={e => setApproved(e.target.checked)} />{w.approvalCheck}</label>
          <fieldset><legend>{w.quality}</legend><p className="risk-muted">{w.diagnosticHelp}</p>{diagnostics.map(([name, label, options]) => <label key={name}>{label}<select required value={answers[name] ?? ""} onChange={e => setAnswers({ ...answers, [name]: e.target.value })}><option value="">{w.choose}</option>{options.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></label>)}</fieldset>
          <label>{w.rationale}<textarea minLength="20" maxLength="4000" required rows="4" value={rationale} onChange={e => setRationale(e.target.value)} /></label><p className="risk-muted">{w.rationaleHelp}</p><button className="risk-primary" disabled={busy}>{w.submit}</button>
        </form>}
        {latest && <article className="risk-card" aria-live="polite"><h2>{w.assessment}</h2><h3>{w.compliance}</h3><p className={latest.compliance.permitted ? "risk-success" : "risk-warning"}>{latest.compliance.permitted ? w.permitted : w.blocked}</p>{latest.compliance.reasons.map(code => <p key={code}>{w.codes[code]}</p>)}<h3>{w.quality}: {latest.decision_quality.diagnostic_score}/100</h3><p>{w.reasoning}</p>{latest.decision_quality.remediation.length > 0 && <p>{w.remediation} {latest.decision_quality.remediation.map(k => w[k]).join(" · ")}</p>}</article>}
        {session.financial && <article className="risk-card"><h2>{w.financial}</h2><dl className="risk-metrics">{[[w.salesCash, "physical_sales_cash_flow_eur"], [w.physicalCash, "physical_cash_flow_eur"], [w.derivativeCash, "derivative_cash_flow_eur"], [w.commercialMargin, "commercial_margin_before_costs_eur"], [w.physicalMargin, "unhedged_physical_margin_eur"], [w.net, "net_procurement_cost_eur"], [w.budget, "volume_adjusted_budget_eur"], [w.variance, "budget_variance_eur"], [w.basisCost, "basis_cost_eur"], [w.peak, "peak_collateral_estimate_eur"]].filter(([, name]) => session.financial[name] !== undefined).map(([label, name]) => <div key={name}><dt>{label}</dt><dd>{money(session.financial[name])}</dd></div>)}</dl><h3>{w.offset}: {session.financial.cost_shock_offset_pct ?? "—"}%</h3><p className="risk-muted">{w.offsetNote}</p><p>{w.noPnl}</p>{isCrude && <><h3>{w.cash}</h3>{inventory && <p>{w.historyNote}</p>}<dl className="risk-metrics">{session.financial.cash_flows.map(row => <div key={row.kind}><dt>{row.date} · {{ physical_sales:w.salesCash, physical_purchase:w.physicalCash, freight:w.freightCash, derivative:w.derivativeCash }[row.kind]}</dt><dd>{money(row.amount)}</dd></div>)}<div><dt>{w.settlementCash}</dt><dd>{money(session.financial.settlement_net_cash_flow)}</dd></div></dl><h3>{w.fixings}</h3><ol>{session.visible_fixings.map(f => <li key={f.date}>{f.date} · Brent {money(f.benchmark_price)}/{unit} · {w.basis}: {money(f.grade_basis)}/{unit}</li>)}</ol><p className="risk-muted">{w.rounding}</p></>}</article>}
        <article className="risk-card"><h2>{w.coach}</h2><button disabled={busy} onClick={() => run(async () => setCoaching(await backendRequest("POST", `/api/v1/risk-training/sessions/${session.id}/coach`, { locale: language })))} type="button">{w.ask}</button>{coaching && <><h3>{coaching.mode === "ai" ? w.ai : w.offline}</h3><p className="risk-coach-text">{coaching.answer}</p></>}</article>
      </div></div>
      {session.decisions.length > 0 && <details className="risk-card"><summary>{w.history} · {session.decisions.length}</summary>{session.decisions.map((record, i) => <article key={i}><h3>{record.information_snapshot.date} · {quantity(record.decision.target_mwh)} {unit}</h3><p>{record.decision.rationale}</p><p>{w.quality}: {record.assessment.decision_quality.diagnostic_score}/100</p></article>)}<button type="button" onClick={download}>{w.export}</button></details>}
    </>}
  </section>;
}
