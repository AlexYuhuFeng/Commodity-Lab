"""Versioned bilingual editorial drafts. No external/domain sign-off claimed."""
from types import MappingProxyType
from typing import Literal
from pydantic import Field, model_validator
from core.risk_training import Contract


class LocalizedText(Contract):
    en: str = Field(min_length=1,max_length=16000)
    zh: str = Field(min_length=1,max_length=16000)


class Section(Contract):
    id: str
    title: LocalizedText
    text: LocalizedText


class Risk(Contract):
    id: str
    name: LocalizedText
    exposure: LocalizedText
    financial: LocalizedText
    commercial: LocalizedText
    residual: LocalizedText


class Chapter(Contract):
    id: str
    version: Literal["handbook-v1"] = "handbook-v1"
    commodity: Literal["european_gas", "crude_oil"]
    role: Literal["trading_company"] = "trading_company"
    content_status: Literal["editorial_training_draft"] = "editorial_training_draft"
    title: LocalizedText
    summary: LocalizedText
    scope: LocalizedText
    sections: tuple[Section, ...] = Field(min_length=3)
    risks: tuple[Risk, ...] = Field(min_length=2)
    legacy_template: str
    scenario_id: str | None = None

    @model_validator(mode="after")
    def unique_anchors(self):
        if len({s.id for s in self.sections}) != len(self.sections):
            raise ValueError("duplicate_section")
        if len({r.id for r in self.risks}) != len(self.risks):
            raise ValueError("duplicate_risk")
        return self


def text(en, zh): return {"en": en, "zh": zh}
def section(id, en, zh, body_en, body_zh): return {"id":id,"title":text(en,zh),"text":text(body_en,body_zh)}
def risk(id, name, exposure, financial, commercial, residual):
    return {"id":id, **{k:text(*v) for k,v in zip(("name","exposure","financial","commercial","residual"),(name,exposure,financial,commercial,residual))}}

LIQUIDITY = risk("liquidity", ("Liquidity and credit", "流动性与信用"),
 ("Paper losses can demand cash before physical receipts arrive; a customer may pay late or default.","纸货亏损可能在实货回款前要求现金；客户也可能延迟付款或违约。"),
 ("Size hedges within a funded collateral reserve; financial hedging does not remove counterparty default.","在已落实的抵押资金储备内配置套保；金融套保不能消除对手方违约。"),
 ("Use credit limits, collateral terms and payment security; align payment dates and arrange funding.","设置信用限额、抵押条款及付款保障；匹配付款日期并安排资金。"),
 ("Funding cost, credit concentration and adverse margin calls remain.","融资成本、信用集中度及不利保证金追缴仍然存在。"))
BASIS = risk("basis", ("Basis and delivery", "基差与交付"),
 ("The physical price/location/quality or delivery window differs from the hedge reference.","实货价格、地点、品质或交付窗口与套保基准不同。"),
 ("Use a matching basis hedge only where the instrument, pricing period and liquidity are suitable.","仅在工具、定价期间与流动性适用时使用匹配的基差套保。"),
 ("Align purchase and sale formulas and delivery windows; contract capacity and manage specification tolerances.","匹配购销公式与交付窗口；落实容量并管理品质容差。"),
 ("A benchmark swap alone leaves basis, capacity and performance risk.","单独的基准掉期仍留下基差、容量与履约风险。"))

HUB = Chapter(id="gas-hub-supply", commodity="european_gas", title=text("Hub supply and customer margin","枢纽供气与客户利润"),
 summary=text("Buy indexed gas and supply a fixed-price industrial customer. Discover how the margin becomes exposed.","按指数采购天然气，向工业客户固定价供气，理解利润如何产生敞口。"),
 scope=text("EUR/MWh introductory model; validated synthetic TTF Risk Lab available. Hub rules, credit terms and tariffs depend on the actual contract.","欧元/MWh入门模型；可进入经数值验证的合成TTF风险实验室。枢纽规则、信用条款与费率取决于实际合同。"),
 legacy_template="gas_local_market_procurement", scenario_id="gas-trading-company-v1",
 sections=(
 section("business","The business","业务结构","The trading company buys gas priced at a hub index plus a delivery differential and sells nominated gas to an industrial customer at a fixed price. The customer is not the learner's employer. Physical title, delivery location, nomination rights and payment terms must be explicit.","贸易公司按枢纽指数加交付价差采购天然气，并按固定价向工业客户出售提名量。客户不是学员的雇主。必须明确实货所有权、交付地点、提名权及付款条款。"),
 section("economics","Follow the margin","追踪利润","For matching delivered MWh, physical margin equals fixed sales revenue less indexed procurement, delivery and other costs. A price rise reduces margin. Long benchmark swaps can offset the benchmark component, but only for their matching quantity and pricing period. Keep derivative receipts separate from physical invoices.","对匹配的交付MWh，实货利润为固定销售收入减去指数采购、交付及其他成本。价格上涨压缩利润。基准多头掉期可抵消匹配数量与定价期间的基准价格部分。掉期收入与实货发票应分开。"),
 section("mitigation","Choose a response","选择应对方式","Compare partial or full benchmark hedging with indexed resale, back-to-back purchasing, smaller commitments or quantity clauses. Physical eligibility changes when customers renominate; reassess the total hedge, not just the next order. An illustrative 80% training limit is not company policy.","比较部分或全额基准套保、指数转售、背靠背采购、缩小承诺量及数量条款。客户重新提名会改变合格实货量；应重估总套保，而非仅考虑下一笔订单。80%训练限额只是示例，并非公司政策。"),
 section("operations","Delivery and cash timing","交付与现金时序","Track nominations, balancing, transport rights, invoices and collateral separately. A profitable physical deal can still need cash while swaps are marked adversely. One favorable outcome does not prove decision quality or mastery.","分别跟踪提名、平衡、运输权、发票与抵押资金。即使实货交易盈利，掉期出现不利盯市时仍可能需要现金。一次有利结果不能证明决策质量或专业掌握程度。")),
 risks=(risk("price",("Rising procurement cost","采购成本上涨"),("Fixed sales against floating purchases expose margin to a benchmark rise.","固定销售与浮动采购使利润面临基准上涨风险。"),("A matched long benchmark swap protects its covered volume.","匹配的基准多头掉期保护覆盖数量。"),("Index resale or align both pricing formulas; limit uncertain nominations.","采用指数转售或匹配双方定价公式；限制不确定提名。"),("Basis, volume changes and funding remain.","基差、数量变化及资金风险仍在。")),BASIS,LIQUIDITY))

BEACH = Chapter(id="gas-beach-hub", commodity="european_gas", title=text("Beach-to-hub trading","上岸点至枢纽交易"),
 summary=text("Acquire gas at a coastal entry point and monetize hub access. The spread must pay for a deliverable route.","在沿海上岸点采购天然气并利用枢纽通达性变现。价差必须覆盖可履行线路的成本。"),
 scope=text("Beach is a landing/entry-point concept, not a universal benchmark. Introductory matched EUR/MWh spread exercise only; real route tariffs, balancing and transport constraints require contract review.","上岸点指登陆或入口地点，并非统一基准。本章仅有欧元/MWh匹配价差入门练习；真实线路费率、平衡及运输约束需审查合同。"),
 legacy_template="procurement_beach_to_germany",
 sections=(
 section("business","Map the route","梳理线路","The trading company buys production-linked gas at a beach/entry point, secures entry and transport rights, then sells at a hub or downstream delivery point. Separate molecule ownership from capacity rights. A quoted spread is not necessarily executable.","贸易公司在上岸点或入口采购与生产相关的天然气，落实入网及运输权，再向枢纽或下游交付点销售。气体所有权与容量权须区分。报价价差不一定可执行。"),
 section("economics","What earns the spread?","价差收益来自何处？","With equal volumes, one currency and the same pricing window, margin is volume times hub sales price less beach purchase price and route costs. If both prices move equally, their common benchmark cancels; the differential and route cost still matter. Different windows, currencies or volumes break this simple cancellation.","在等量、同币种及同定价窗口下，利润为数量乘以枢纽售价减上岸点采购价及线路成本。两端价格等幅变动时，共同基准相抵，但差价及线路成本仍重要。窗口、币种或数量不同会破坏这一简化抵消。"),
 section("mitigation","Protect the commercial route","保护商业线路","A location-spread hedge can address a matched price differential where suitable instruments exist. It cannot create transport capacity or cure a production outage. Compare pricing alignment, firm capacity, fallback routes and volume flexibility before adding paper.","在存在适用工具时，地点价差套保可应对匹配的价格差异，但不能创造运输容量或解决生产中断。增加纸货前，应比较定价匹配、可靠容量、备用线路及数量灵活性。"),
 section("operations","What can interrupt delivery?","什么会中断交付？","Review upstream production, maintenance, entry rights, downstream nominations, balancing obligations and counterparties. Firm versus interruptible rights have different commercial risks; market-specific rules and penalties are not modeled in this introductory exercise.","审查上游生产、检修、入口权、下游提名、平衡义务及对手方。可靠与可中断权利的商业风险不同；本入门练习不模拟市场特定规则与罚则。")),risks=(BASIS,risk("delivery",("Production and transport availability","生产与运输可用性"),("An upstream outage or interrupted route can prevent hub delivery even when the spread is favorable.","即使价差有利，上游中断或线路受阻也可能妨碍枢纽交付。"),("Benchmark paper cannot replace missing molecules or transport rights.","基准纸货不能替代缺失气源或运输权。"),("Secure appropriate capacity, fallback supplies and nomination flexibility; review interruption terms.","落实适当容量、备用供应及提名灵活性，审查中断条款。"),("Availability, balancing and contractual performance obligations remain.","可用性、平衡及合同履约义务仍然存在。")),LIQUIDITY))

REGAS = Chapter(id="gas-lng-regas", commodity="european_gas", title=text("LNG cargo and regas send-out","LNG船货与气化外输"),
 summary=text("Connect cargo acquisition, terminal access and gas resale. Physical conversion and timing shape the margin.","连接船货采购、接收站通达及天然气转售。实物转化与时序决定利润。"),
 scope=text("Simplified pre-converted EUR/MWh exercise with an explicit usable-energy factor. Not a validated full LNG/JKM/FX or terminal simulator. Existing exploratory LNG practice remains available.","已预换算为欧元/MWh的简化练习，明确可用能量系数。并非已验证的完整LNG、JKM、汇率或接收站模拟器。可继续使用现有探索性LNG练习。"),
 legacy_template="procurement_lng_cargo",
 sections=(
 section("business","Connect cargo to gas sales","连接船货与天然气销售","A trading company acquires LNG, arranges shipping, unloading, terminal slots and regas access, then resells gas. Contract terms determine title, loss allocation, flexibility and responsibility for delay. Do not assume terminal ownership or utility operations.","贸易公司采购LNG，安排航运、卸货、接收窗口及气化通达，再转售天然气。合同条款决定所有权、损耗分摊、灵活性及延误责任。不要假定贸易公司拥有接收站或从事公用事业运营。"),
 section("economics","Energy in and energy sold","输入能量与销售能量","Purchased energy and saleable send-out may differ. In the introductory exercise, send-out equals purchased MWh times a stated usable-energy factor. Sales price applies to send-out; purchase and terminal fee apply to purchased energy. Full cargo economics also needs actual calorific conventions, freight, boil-off, FX, financing and terminal charges.","采购能量与可销售外输量可能不同。入门练习中，外输量等于采购MWh乘以给定可用能量系数；售价适用于外输量，采购价与接收站费适用于采购量。完整船货经济模型还需真实热值约定、运费、蒸发损耗、汇率、融资及接收站收费。"),
 section("mitigation","Align the hedge and delivery","匹配套保与交付","Hedge the actual pricing formula and expected saleable volume, not nominal cargo volume by default. Benchmark/basis and FX hedges require independently validated conventions. Contract timing flexibility, alternative slots, diversion rights and funding may manage risks that swaps do not.","应套保实际定价公式与预期可销售数量，而非默认按名义船货量套保。基准、基差及汇率套保需要独立验证的约定。合同时间灵活性、备用窗口、转运权及资金安排可管理掉期无法解决的风险。"),
 section("operations","Track the chain","跟踪链条","Arrival does not guarantee immediate send-out. Track vessel delays, terminal availability, inventory capacity, regas rate and downstream nominations. The simple exercise assumes all usable energy sells within the same window; it does not estimate a terminal schedule or delivery penalties.","到港不代表立即外输。应跟踪船舶延误、接收站可用性、库存容量、气化速率及下游提名。简化练习假定全部可用能量在同一窗口销售，不估计接收站排程或交付罚金。")),risks=(BASIS,risk("sendout",("Arrival, losses and send-out","到港、损耗与外输"),("Vessel delay, unavailable slots or lower usable energy changes the volume and timing of gas sales.","船舶延误、窗口不可用或可用能量下降，会改变销售数量与时间。"),("Match paper to expected saleable energy and pricing windows; a swap cannot provide a terminal slot.","将纸货匹配预期可销售能量与定价窗口；掉期不能提供接收窗口。"),("Arrange alternative slots or supply and contractual timing flexibility, subject to rights and consent.","在权利与许可允许时安排备用窗口、供应及合同时间灵活性。"),("Actual loss allocation, terminal performance and delivery penalties require contract-specific review.","实际损耗分摊、接收站履约及交付罚则需按具体合同审查。")),LIQUIDITY))

REFINERY = Chapter(id="crude-refinery-supply", commodity="crude_oil", title=text("Crude supply to a refinery","向炼厂供应原油"),
 summary=text("Source floating-price crude for fixed-price resale. Protect the trading company's supply margin.","以浮动价格采购原油并固定价转售，保护贸易公司的供应利润。"),
 scope=text("USD/bbl synthetic Brent-average model; validated training Risk Lab available. Not Dated Brent assessment or real exchange settlement.","美元/桶合成Brent均价模型；可进入数值验证的训练风险实验室。并非Dated Brent评估或真实交易所结算。"),
 legacy_template="crude_oil_hedging_basics", scenario_id="crude-refinery-procurement-v1",
 sections=(
 section("business","The refinery is your customer","炼厂是你的客户","The trading company contracts fixed-price delivery to a refinery, then buys crude at a benchmark plus grade differential. Define cargo specifications, nomination options, delivery terms and payment dates. The learner sources for the refinery; the learner does not operate it.","贸易公司签订向炼厂固定价交付的合同，再按基准加品质差价采购原油。明确船货规格、提名选择权、交付及付款条款。学员为炼厂采购，不是炼厂运营者。"),
 section("economics","Build the supply margin","构建供应利润","Physical margin equals fixed sales less indexed purchase cost and freight. A long matching benchmark swap offsets a rising benchmark on covered barrels. Grade differential, freight and quantity options remain separate. Pricing windows matter as much as the benchmark name.","实货利润等于固定销售减去指数采购成本及运费。匹配的基准多头掉期可抵消覆盖桶数的基准上涨。品质差价、运费及数量选择权仍需单独管理。定价窗口与基准名称同样重要。"),
 section("mitigation","Respond to a changed nomination","应对提名变化","When the customer reduces cargo quantity, reassess eligible physical backing and resize total paper. Compare financial protection with indexed resale, matched purchase terms and limits on customer quantity flexibility. There may be several defensible hedge ratios.","客户减少船货量时，应重估合格实货支持并调整纸货总量。比较金融保护、指数转售、匹配采购条款及限制客户数量灵活性。多种套保比例可能都有合理依据。"),
 section("operations","Separate cash-flow obligations","区分现金流义务","Review quality acceptance, vessel schedule, freight, counterparty credit and collateral. The training case separates sales, purchase, freight and swap cash flows; it excludes fees, tax and financing. A positive trading margin is not complete accounting PnL.","审查品质验收、船期、运费、对手方信用及抵押资金。训练案例分别列示销售、采购、运费与掉期现金流，不含其他费用、税项及融资。正交易利润不等于完整会计损益。")),risks=(HUB.risks[0],BASIS,LIQUIDITY))

INVENTORY = Chapter(id="crude-inventory", commodity="crude_oil", title=text("Owned crude inventory and resale","自有原油库存与转售"),
 summary=text("Manage barrels already purchased. Distinguish protecting resale value from paying for the cargo again.","管理已采购的桶数，区分保护转售价值与再次支付船货价款。"),
 scope=text("USD/bbl synthetic resale model; validated short-hedge Risk Lab available. Historical purchase cost and settlement-date cash are distinct.","美元/桶合成转售模型；可进入数值验证的空头套保风险实验室。历史采购成本与结算日现金不同。"),
 legacy_template="crude_oil_hedging_basics", scenario_id="crude-merchant-inventory-v1",
 sections=(
 section("business","The merchant book","贸易库存账簿","The trading company already owns and has paid for crude inventory. It will sell at a future benchmark plus grade differential, paying outbound freight. The open commercial exposure is resale value, with storage, quality and customer risks alongside price.","贸易公司已拥有并支付原油库存，未来按基准加品质差价销售并支付出港运费。未关闭的商业敞口是转售价值，同时伴随仓储、品质、客户及价格风险。"),
 section("economics","Margin is not today's cash","利润不等于今天的现金","Lifecycle margin includes historical acquisition cost, sales, freight and paper receipts. Settlement-date cash excludes an acquisition paid earlier. A short benchmark swap can protect against falling resale prices; it can require collateral when prices rise even as inventory becomes more valuable.","全周期利润包括历史采购成本、销售、运费与纸货收入。结算日现金不含已在之前支付的采购款。基准空头掉期可保护售价下跌；即使库存升值，价格上涨时仍可能要求抵押资金。"),
 section("mitigation","Protect value without confusing direction","保护价值并辨清方向","Distinguish an owned-inventory short hedge from a fixed-sales procurement long hedge. Compare partial protection, forward resale, smaller inventory and physical optionality. Paper should match the actual pricing period, volume and benchmark; no single hedge ratio is always best.","区分自有库存的空头套保与固定销售采购的多头套保。比较部分保护、远期转售、减少库存及实货灵活性。纸货应匹配实际定价期间、数量及基准；没有永远最好的单一套保比例。"),
 section("operations","Follow dates and residual risks","跟踪日期与剩余风险","Record the purchase date and cost basis before scenario decisions. Track sale receipts, freight and derivative settlement separately. Grade basis, funding, quality deterioration and storage availability remain outside a simple benchmark hedge.","在情景决策前记录采购日期与成本基础，分别跟踪销售回款、运费及掉期结算。品质基差、资金、品质劣化及仓储可用性仍在简单基准套保之外。")),
 risks=(risk("price",("Falling resale value","转售价值下跌"),("Owned barrels lose expected revenue when their benchmark falls.","基准下跌使自有桶数的预期收入减少。"),("A matching short benchmark swap protects covered barrels.","匹配的基准空头掉期保护覆盖桶数。"),("Forward resale or reduce stock, subject to commercial obligations.","在商业义务允许时，远期转售或减少库存。"),("Grade, freight and adverse short-position margin calls remain.","品质、运费及空头不利保证金追缴仍在。")),BASIS,LIQUIDITY))

CHAPTERS = MappingProxyType({c.id:c for c in (HUB,BEACH,REGAS,REFINERY,INVENTORY)})
