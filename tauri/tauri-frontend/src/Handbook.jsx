import React, { useEffect, useRef, useState } from "react";
import { backendRequest } from "./api";
import "./risk-training.css";
import "./handbook.css";

const labels = {
  en: { title:"Interactive trading handbook", intro:"Understand the business. Explore the risks. Ask for a new challenge.", draft:"Editorial training draft • simulated examples • no trading authorization", chapters:"Business model", reference:"Reference chapter", conversation:"Learn through conversation", ask:"Ask about this business", placeholder:"Why is the hedge long? What would happen if the delivery volume changed?", send:"Send", explain:"Explain the economics", risk_map:"Map the risks", compare:"Compare mitigation", practice:"New checked practice", offline:"Offline reference mode — free-form questions are not answered", fallback:"AI unavailable or invalid — reference fallback", ai:"AI guidance • ungraded", cites:"Chapter references", question:"Checked numerical practice", givens:"Exercise inputs", answer:"Your answer", check:"Check answer", correct:"Correct within one cent", incorrect:"Review the calculation", expected:"Reference answer", provisional:"Practice evidence only; this does not establish mastery.", new:"New conversation", busy:"Working…", error:"Request failed. Retry, or start a new conversation if the saved record is unavailable. Reading remains available.", risk:"Exposure", financial:"Financial response", commercial:"Commercial / operational response", residual:"Residual risk", lab:"Open Risk Lab", legacy:"Open existing AI practice", scope:"Model boundaries", you:"You", coach:"Handbook coach", saved:"Conversation saved on this device", missing:"Saved conversation unavailable; start a new conversation.", empty:"Read a passage, ask a question or request checked practice. AI can assemble explanations, risk maps, comparisons and exercises around this business.", attach:"Current Risk Lab evidence attached", detach:"General chapter context; no market session attached" },
  zh: { title:"交互式交易手册", intro:"理解业务，探索风险，提出问题并请求新挑战。", draft:"编辑训练草稿 · 模拟示例 · 非交易授权", chapters:"业务模型", reference:"参考章节", conversation:"通过对话学习", ask:"询问这项业务", placeholder:"为什么需要多头套保？交付量发生变化会怎样？", send:"发送", explain:"解释业务经济模型", risk_map:"梳理风险", compare:"比较应对方式", practice:"新建数值验证练习", offline:"离线参考模式：不回答自由提问", fallback:"AI不可用或结构无效，使用参考内容", ai:"AI辅导 · 不计分", cites:"章节参考", question:"经过数值验证的练习", givens:"练习输入", answer:"你的答案", check:"检查答案", correct:"正确，误差在一分以内", incorrect:"请复习计算过程", expected:"参考答案", provisional:"仅作为练习证据，不代表已掌握专业能力。", new:"新建对话", busy:"处理中…", error:"请求失败，请重试。如本机记录不可用，可新建对话。仍可阅读章节。", risk:"敞口", financial:"金融应对", commercial:"商业 / 运营应对", residual:"剩余风险", lab:"打开风险实验室", legacy:"打开现有AI练习", scope:"模型边界", you:"你", coach:"手册教练", saved:"对话保存在本机", missing:"已保存对话不可用，请新建对话。", empty:"阅读章节、提问或请求数值验证练习。AI可围绕当前业务组合解释、风险图、比较及练习。", attach:"已关联当前风险实验室证据", detach:"通用章节背景，未关联市场情景" }
};
const inputNames = {
  quantity:["Purchased / delivered quantity","采购 / 交付量"], currency:["Currency","币种"], unit:["Unit","单位"], pricing_period:["Pricing window","定价窗口"], seed:["Reproducible seed","可复现种子"], hub_sales_price:["Hub sales price","枢纽售价"], beach_purchase_price:["Beach purchase price","上岸点采购价"], route_cost_per_unit:["Route cost per unit","单位线路成本"], sales_price:["Sales price","售价"], purchase_price:["Purchase price","采购价"], usable_energy_factor:["Usable-energy factor","可用能量系数"], terminal_fee_per_purchased_unit:["Terminal fee / purchased unit","接收站费 / 采购单位"], fixed_sales_price:["Fixed sales price","固定售价"], historical_purchase_price:["Historical purchase price","历史采购价"], benchmark_entry:["Swap entry benchmark","掉期入场基准"], benchmark_settlement:["Settlement benchmark","结算基准"], physical_basis:["Physical basis","实货基差"], freight_per_unit:["Freight per unit","单位运费"], signed_paper_quantity:["Signed paper quantity","有符号纸货数量"]
};

function Practice({ question, conversationId, language, w, previous, onResult }) {
  const [answer, setAnswer] = useState(""); const [busy,setBusy]=useState(false); const [error,setError]=useState(false);
  async function submit(e) {
    e.preventDefault();setBusy(true);setError(false);
    try { const result=await backendRequest("POST",`/api/v1/handbook/conversations/${conversationId}/questions/${question.id}/answer`,{answer});onResult(question.id,result); }
    catch {setError(true);} finally {setBusy(false);}
  }
  return <section className="handbook-practice"><h4>{w.question}</h4><p>{question.prompt[language]}</p><details><summary>{w.givens} · {question.givens.currency}/{question.givens.unit}</summary><dl className="handbook-inputs">{Object.entries(question.givens).filter(([,v])=>v!==null).map(([key,value])=><div key={key}><dt>{inputNames[key]?.[language==="zh"?1:0]??key}</dt><dd>{key==="pricing_period"?(language==="zh"?"同一合成月份":"Same synthetic month"):String(value)}</dd></div>)}</dl></details>
    <form onSubmit={submit}><label htmlFor={`answer-${question.id}`}>{w.answer} ({question.answer_currency})</label><div className="handbook-answer"><input id={`answer-${question.id}`} type="number" step="0.01" min="-100000000000" max="100000000000" required value={answer} onChange={e=>setAnswer(e.target.value)}/><button disabled={busy}>{busy?w.busy:w.check}</button></div></form>
    {error&&<p role="alert">{w.error}</p>}{previous&&<div role="status" className={previous.correct?"risk-success":"risk-warning"}><strong>{previous.correct?w.correct:w.incorrect}</strong><p>{w.expected}: {previous.expected_answer} {question.answer_currency}</p><p>{previous.working[language]}</p><a href={`#handbook-${previous.remediation_section}`}>{w.cites}</a></div>}<p className="risk-muted">{w.provisional}</p>
  </section>;
}

export default function Handbook({ locale="en", productScope="natural_gas", onOpenRisk, onOpenPractice }) {
  const language=locale.startsWith("zh")?"zh":"en", w=labels[language];
  const commodity=productScope==="crude_oil"?"crude_oil":"european_gas";
  const [catalog,setCatalog]=useState([]),[chapterId,setChapterId]=useState(""),[chapter,setChapter]=useState(null),[conversation,setConversation]=useState(null),[attempts,setAttempts]=useState({}),[message,setMessage]=useState(""),[busy,setBusy]=useState(false),[error,setError]=useState("");
  const [learnerId]=useState(()=>localStorage.getItem("commodity-lab-handbook-learner-v1")||"local");
  const requestId=useRef(0);
  const key=id=>`commodity-lab-handbook:${commodity}:${id}${learnerId==="local"?"":`:${learnerId}`}`;
  useEffect(()=>{let alive=true;backendRequest("GET",`/api/v1/handbook/chapters?commodity=${commodity}`).then(data=>{if(alive){const saved=localStorage.getItem(`commodity-lab-handbook-chapter:${commodity}`);setCatalog(data.chapters);setChapterId(data.chapters.some(c=>c.id===saved)?saved:(data.chapters[0]?.id??""));}}).catch(()=>{if(alive)setError(w.error);});return()=>{alive=false;};},[commodity]);
  useEffect(()=>{
    if(!chapterId)return;const token=++requestId.current;let alive=true;setBusy(true);setError("");setChapter(null);setConversation(null);setAttempts({});setMessage("");
    (async()=>{try{const data=await backendRequest("GET",`/api/v1/handbook/chapters/${chapterId}`);if(!alive)return;setChapter(data);const saved=localStorage.getItem(key(chapterId));if(saved){try{const state=await backendRequest("GET",`/api/v1/handbook/conversations/${saved}`);if(state.chapter_id!==chapterId||state.version!==data.version||(state.learner_id??"local")!==learnerId)throw Error("mismatch");if(alive){setConversation(state);setAttempts(state.attempts??{});}}catch{if(alive){localStorage.removeItem(key(chapterId));setError(w.missing);}}}}catch{if(alive)setError(w.error);}finally{if(alive&&token===requestId.current)setBusy(false);}})();
    return()=>{alive=false;};
  },[chapterId,commodity]);
  useEffect(()=>{if(!chapter)return;const section=localStorage.getItem("commodity-lab-handbook-remediation");if(section){localStorage.removeItem("commodity-lab-handbook-remediation");document.getElementById(`handbook-${section}`)?.scrollIntoView({block:"start"});}},[chapter]);
  async function send(intent="ask") {
    if(busy||!chapter)return;const token=requestId.current;setBusy(true);setError("");
    let conversationId=conversation?.id;
    try {
      let state=conversation;
      if(!state){
        // Attach only an actual compatible session; a stale/mismatched local ID does not block chapter study.
        let riskId=null;const saved=localStorage.getItem(commodity==="crude_oil"?"commodity-lab-risk-session-v1:crude_oil":"commodity-lab-risk-session-v1");
        if(learnerId==="local"&&saved&&chapter.scenario_id){try{const view=await backendRequest("GET",`/api/v1/risk-training/sessions/${saved}`);if(view.scenario_version===chapter.scenario_id)riskId=saved;}catch{/* independent reading remains available */}}
        state=await backendRequest("POST","/api/v1/handbook/conversations",{chapter_id:chapter.id,risk_session_id:riskId,...(learnerId!=="local"?{learner_id:learnerId}:{})});
        if(token!==requestId.current)return;localStorage.setItem(key(chapterId),state.id);setConversation(state);conversationId=state.id;
      }
      const data=await backendRequest("POST",`/api/v1/handbook/conversations/${state.id}/messages`,{revision:state.revision,locale:language,message:intent==="ask"?message:w[intent],intent});
      if(token===requestId.current){setConversation(data);setAttempts(data.attempts??{});setMessage("");}
    }catch(error){
      if(token===requestId.current){
        if(conversationId && String(error.message).includes("stale_or_exhausted")){
          try{const latest=await backendRequest("GET",`/api/v1/handbook/conversations/${conversationId}`);if(token===requestId.current){setConversation(latest);setAttempts(latest.attempts??{});}}catch{/* keep the learner input for retry */}
        }
        setError(w.error);
      }
    }finally{if(token===requestId.current)setBusy(false);}
  }
  function restart(){localStorage.removeItem(key(chapterId));setConversation(null);setAttempts({});setError("");setMessage("");}
  function record(id,result){setAttempts(prev=>({...prev,[id]:[...(prev[id]??[]),{assessment:result}]}));}
  function card(card,index){
    if(card.type==="practice")return <Practice key={card.question.id} question={card.question} conversationId={conversation.id} language={language} w={w} previous={attempts[card.question.id]?.at(-1)?.assessment} onResult={record}/>;
    if(card.type==="explanation")return <div key={index}>{card.sections.map(s=><section key={s.id}><h4>{s.title[language]}</h4><p>{s.text[language]}</p></section>)}</div>;
    if(card.type==="reflection")return <p key={index} className="handbook-reflection">{card.question[language]}</p>;
    if(card.type==="simulation")return <button key={index} type="button" onClick={onOpenRisk}>{w.lab}</button>;
    return <div key={index} className="handbook-risk-map">{card.risks.map(r=><section key={r.id}><h4>{r.name[language]}</h4><dl>{(card.type==="comparison"?["financial","commercial","residual"]:["exposure","residual"]).map(k=><div key={k}><dt>{k==="exposure"?w.risk:w[k]}</dt><dd>{r[k][language]}</dd></div>)}</dl></section>)}</div>;
  }
  return <section className="risk-lab handbook" aria-labelledby="handbook-title"><header className="risk-header"><div><span className="risk-badge">{w.draft}</span><h1 id="handbook-title">{w.title}</h1><p>{w.intro}</p></div></header>
    <label>{w.chapters}<select value={chapterId} disabled={busy} onChange={e=>{localStorage.setItem(`commodity-lab-handbook-chapter:${commodity}`,e.target.value);setChapterId(e.target.value);}}>{catalog.map(c=><option value={c.id} key={c.id}>{c.title[language]}</option>)}</select></label>
    {error&&<p role="alert" className="risk-warning">{error}</p>}{busy&&<p role="status">{w.busy}</p>}
    {chapter&&<div className="handbook-grid"><article className="risk-card handbook-reading"><h2>{chapter.title[language]}</h2><p>{chapter.summary[language]}</p><p className="risk-muted">{w.reference} · {chapter.version}</p><div className="handbook-boundary"><h3>{w.scope}</h3><p>{chapter.scope[language]}</p></div><nav aria-label={w.cites}>{chapter.sections.map(s=><a key={s.id} href={`#handbook-${s.id}`}>{s.title[language]}</a>)}</nav>{chapter.sections.map(s=><section id={`handbook-${s.id}`} key={s.id} tabIndex="-1"><h3>{s.title[language]}</h3><p>{s.text[language]}</p></section>)}<div className="risk-actions">{chapter.scenario_id&&<button type="button" onClick={onOpenRisk}>{w.lab}</button>}<button type="button" onClick={()=>onOpenPractice(chapter.legacy_template, { id: chapter.id, version: chapter.version, title: chapter.title, template_id: chapter.legacy_template, commodity: chapter.commodity, content_status: chapter.content_status })}>{w.legacy}</button></div></article>
      <section className="risk-card handbook-dialogue" aria-labelledby="handbook-conversation"><div className="handbook-dialogue-header"><h2 id="handbook-conversation">{w.conversation}</h2>{conversation&&<button disabled={busy} onClick={restart} type="button">{w.new}</button>}</div><p className="risk-muted">{conversation?w.saved:w.empty}</p>{conversation&&<p className="risk-muted">{conversation.risk_session_id?w.attach:w.detach}</p>}
        <div className="handbook-messages" aria-live="polite">{conversation?.messages.map((m,i)=><article className={`handbook-message handbook-${m.role}`} key={i}><h3>{m.role==="user"?w.you:w.coach}</h3>{m.mode&&<span className="risk-badge">{w[m.mode]}</span>}<p className="handbook-prose">{m.text}</p>{m.citations&&<nav aria-label={w.cites}>{m.citations.map(id=><a href={`#handbook-${id}`} key={id}>{chapter.sections.find(s=>s.id===id)?.title[language]??id}</a>)}</nav>}{m.cards?.map(card)}</article>)}</div>
        <div className="risk-actions">{["explain","risk_map","compare","practice"].map(intent=><button type="button" disabled={busy} key={intent} onClick={()=>send(intent)}>{w[intent]}</button>)}</div><form onSubmit={e=>{e.preventDefault();send();}}><label htmlFor="handbook-question">{w.ask}</label><textarea id="handbook-question" rows="3" maxLength="4000" required placeholder={w.placeholder} value={message} onChange={e=>setMessage(e.target.value)}/><button className="risk-primary" disabled={busy||!message.trim()}>{w.send}</button></form>
      </section></div>}
  </section>;
}
