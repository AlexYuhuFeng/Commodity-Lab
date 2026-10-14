import React from "react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import Handbook from "./Handbook";
import { backendRequest } from "./api";
vi.mock("./api",()=>({backendRequest:vi.fn()}));
const title={en:"Hub supply",zh:"枢纽供气"};
const chapter={id:"gas-hub-supply",version:"handbook-v1",title,summary:{en:"Trading-company physical supply",zh:"贸易公司实货供气"},scope:{en:"Synthetic EUR/MWh",zh:"合成欧元/MWh"},scenario_id:"gas-trading-company-v1",legacy_template:"gas_local_market_procurement",sections:[{id:"business",title:{en:"Business structure",zh:"业务结构"},text:{en:"Buy floating and sell fixed.",zh:"浮动采购与固定销售。"}},{id:"economics",title:{en:"Margin formation",zh:"利润形成"},text:{en:"Physical and derivative cash are separate.",zh:"实货与掉期现金流分开。"}}]};
const question={id:"q1",prompt:{en:"Calculate physical margin",zh:"计算实货利润"},givens:{quantity:"1000",currency:"EUR",unit:"MWh",pricing_period:"same synthetic month",seed:0},answer_currency:"EUR"};
const initial={id:"conversation1",chapter_id:chapter.id,version:chapter.version,revision:0,messages:[],risk_session_id:null};
const replied={...initial,revision:1,messages:[{role:"user",text:"New checked practice"},{role:"assistant",mode:"offline",text:"Offline mode cannot answer free-form questions.",citations:["economics"],cards:[{type:"practice",question}]}],attempts:{}};
beforeEach(()=>{localStorage.clear();vi.clearAllMocks();});afterEach(cleanup);
function catalog(){backendRequest.mockResolvedValueOnce({chapters:[{id:chapter.id,title}]}).mockResolvedValueOnce(chapter);}
it("reads chapter context and opens existing tools without calling AI",async()=>{
 catalog();const risk=vi.fn(),practice=vi.fn();render(<Handbook onOpenRisk={risk} onOpenPractice={practice}/>);
 await screen.findByText("Buy floating and sell fixed.");
 expect(screen.getByText(/Editorial training draft/)).toBeInTheDocument();
 expect(backendRequest).toHaveBeenCalledTimes(2);
 fireEvent.click(screen.getByRole("button",{name:"Open Risk Lab"}));expect(risk).toHaveBeenCalled();
 fireEvent.click(screen.getByRole("button",{name:"Open existing AI practice"}));expect(practice).toHaveBeenCalledWith("gas_local_market_procurement",expect.objectContaining({id:chapter.id,version:chapter.version}));
});
it("requests checked practice, withholds solution until grading and saves conversation",async()=>{
 catalog();backendRequest.mockResolvedValueOnce(initial).mockResolvedValueOnce(replied).mockResolvedValueOnce({correct:true,expected_answer:"20500.00",working:{en:"Sales minus procurement plus paper",zh:"销售减采购加纸货"},remediation_section:"economics"});
 render(<Handbook/>);await screen.findByText("Buy floating and sell fixed.");
 fireEvent.click(screen.getByRole("button",{name:"New checked practice"}));await screen.findByText("Calculate physical margin");
 expect(screen.queryByText(/20500/)).not.toBeInTheDocument();
 expect(localStorage.getItem("commodity-lab-handbook:european_gas:gas-hub-supply")).toBe("conversation1");
 fireEvent.change(screen.getByLabelText("Your answer (EUR)"),{target:{value:"20500"}});fireEvent.click(screen.getByRole("button",{name:"Check answer"}));
 await screen.findByText("Correct within one cent");
 expect(backendRequest).toHaveBeenLastCalledWith("POST","/api/v1/handbook/conversations/conversation1/questions/q1/answer",{answer:"20500"});
 expect(screen.getByText(/does not establish mastery/)).toBeInTheDocument();
});
it("resumes attempts in Chinese and shows grounded cards with valid source links",async()=>{
 localStorage.setItem("commodity-lab-handbook:european_gas:gas-hub-supply","conversation1");catalog();
 backendRequest.mockResolvedValueOnce({...replied,attempts:{q1:[{assessment:{correct:false,expected_answer:"20500.00",working:{en:"Calculation",zh:"计算过程"},remediation_section:"economics"}}]}});
 render(<Handbook locale="zh"/>);await screen.findByText("计算实货利润");
 expect(screen.getByText("请复习计算过程")).toBeInTheDocument();
 expect(screen.getByText("离线参考模式：不回答自由提问")).toBeInTheDocument();
 expect(screen.getAllByRole("link",{name:"利润形成"})[0]).toHaveAttribute("href","#handbook-economics");
});
it("recovers from missing saved record and retains input on failed reply",async()=>{
 localStorage.setItem("commodity-lab-handbook:european_gas:gas-hub-supply","gone");catalog();backendRequest.mockRejectedValueOnce(Error("404"));
 render(<Handbook/>);await screen.findByText(/Saved conversation unavailable/);
 expect(localStorage.getItem("commodity-lab-handbook:european_gas:gas-hub-supply")).toBeNull();
 backendRequest.mockResolvedValueOnce(initial).mockRejectedValueOnce(Error("503"));
 fireEvent.change(screen.getByLabelText("Ask about this business"),{target:{value:"Why is basis unhedged?"}});fireEvent.click(screen.getByRole("button",{name:"Send"}));
 await screen.findByRole("alert");expect(screen.getByLabelText("Ask about this business")).toHaveValue("Why is basis unhedged?");
});
it("does not attach an incompatible Risk Lab session",async()=>{
 localStorage.setItem("commodity-lab-risk-session-v1","other");catalog();backendRequest.mockResolvedValueOnce({scenario_version:"other-case"}).mockResolvedValueOnce(initial).mockResolvedValueOnce(replied);
 render(<Handbook/>);await screen.findByText("Buy floating and sell fixed.");fireEvent.click(screen.getByRole("button",{name:"New checked practice"}));await screen.findByText("Calculate physical margin");
 expect(backendRequest).toHaveBeenCalledWith("POST","/api/v1/handbook/conversations",{chapter_id:chapter.id,risk_session_id:null});
});
it("renders AI-selected comparison and simulation cards with escaped prose",async()=>{
 catalog();const risk=vi.fn();const r={id:"basis",name:{en:"Basis",zh:"基差"},financial:{en:"Matched basis hedge",zh:"匹配基差套保"},commercial:{en:"Align contracts",zh:"匹配合同"},residual:{en:"Delivery risk remains",zh:"交付风险仍在"}};
 backendRequest.mockResolvedValueOnce(initial).mockResolvedValueOnce({...initial,revision:1,messages:[{role:"assistant",mode:"ai",text:"<img src=x onerror=alert(1)>",citations:["economics"],cards:[{type:"comparison",risks:[r]},{type:"simulation",scenario_id:chapter.scenario_id}]}]});
 render(<Handbook onOpenRisk={risk}/>);await screen.findByText("Buy floating and sell fixed.");fireEvent.click(screen.getByRole("button",{name:"Compare mitigation"}));
 await screen.findByText("Matched basis hedge");expect(screen.getByText("Align contracts")).toBeInTheDocument();expect(screen.getByText("AI guidance • ungraded")).toBeInTheDocument();
 expect(document.querySelector("img")).toBeNull();expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeInTheDocument();
 fireEvent.click(screen.getAllByRole("button",{name:"Open Risk Lab"})[1]);expect(risk).toHaveBeenCalled();
});
it("refreshes a stale conversation before retrying while retaining the learner question",async()=>{
 catalog();backendRequest.mockResolvedValueOnce(initial).mockRejectedValueOnce(Error("stale_or_exhausted_conversation")).mockResolvedValueOnce({...initial,revision:1}).mockResolvedValueOnce({...initial,revision:2});
 render(<Handbook/>);await screen.findByText("Buy floating and sell fixed.");fireEvent.change(screen.getByLabelText("Ask about this business"),{target:{value:"Why does basis remain?"}});fireEvent.click(screen.getByRole("button",{name:"Send"}));
 await screen.findByRole("alert");expect(screen.getByLabelText("Ask about this business")).toHaveValue("Why does basis remain?");
 fireEvent.click(screen.getByRole("button",{name:"Send"}));await waitFor(()=>expect(backendRequest).toHaveBeenLastCalledWith("POST","/api/v1/handbook/conversations/conversation1/messages",expect.objectContaining({revision:1,message:"Why does basis remain?"})));
});
it("restores the selected business-model chapter rather than always returning to the first",async()=>{
 localStorage.setItem("commodity-lab-handbook-chapter:european_gas","gas-lng-regas");
 backendRequest.mockResolvedValueOnce({chapters:[{id:chapter.id,title},{id:"gas-lng-regas",title:{en:"Regas",zh:"气化"}}]}).mockResolvedValueOnce({...chapter,id:"gas-lng-regas",title:{en:"Regas",zh:"气化"}});
 render(<Handbook/>);await screen.findByRole("heading",{name:"Regas"});expect(backendRequest).toHaveBeenLastCalledWith("GET","/api/v1/handbook/chapters/gas-lng-regas");
});
