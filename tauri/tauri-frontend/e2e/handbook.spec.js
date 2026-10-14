import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
const fontCss=readFileSync("node_modules/@fontsource/noto-sans-sc/400.css","utf8").replaceAll("./files/","/node_modules/@fontsource/noto-sans-sc/files/");
async function open(page,locale="en",scope="natural_gas") {
 // Use the normal reproducible-seed contract for visual evidence, not mocked results.
 await page.route("**/api/v1/handbook/conversations/*/messages",route=>{const data=route.request().postDataJSON();route.continue({postData:JSON.stringify(data.intent==="practice"?{...data,practice_seed:0}:data)});});
 await page.addInitScript(({locale,scope})=>{localStorage.setItem("commodity-lab-locale",locale);localStorage.setItem("commodity-lab-theme",locale==="zh"?"light":"dark");localStorage.setItem("commodity-lab-product-scope",scope);localStorage.setItem("commodity-lab-guide-complete","1");},{locale,scope});
 await page.goto("/");await page.getByRole("button",{name:locale==="zh"?"交易手册":"Handbook",exact:true}).click();await expect(page.locator(".handbook-reading")).toBeVisible();
 await page.addStyleTag({content:fontCss+'\n.cl-app-shell, .cl-app-shell * { font-family:"Noto Sans SC",sans-serif !important; }'});await page.evaluate(async()=>{await document.fonts.ready;});
}
async function align(page,selector){await page.locator(selector).evaluate(el=>{const c=el.closest(".cl-content-shell");c.scrollTo({top:c.scrollTop+el.getBoundingClientRect().top-c.getBoundingClientRect().top-24,behavior:"instant"});});}
async function practice(page,zh=false){
 const response=page.waitForResponse(r=>r.url().includes("/messages")&&r.request().method()==="POST");await page.getByRole("button",{name:zh?"新建数值验证练习":"New checked practice",exact:true}).click();
 const data=await(await response).json();const q=data.messages.at(-1).cards.find(c=>c.type==="practice").question;expect(q).not.toHaveProperty("expected_answer");expect(q).not.toHaveProperty("answer");return q;
}
function margin(q){
 const g=q.givens,n=k=>Number(g[k]);
 if(q.chapter_id==="gas-beach-hub")return n("quantity")*(n("hub_sales_price")-n("beach_purchase_price")-n("route_cost_per_unit"));
 if(q.chapter_id==="gas-lng-regas")return n("quantity")*n("usable_energy_factor")*n("sales_price")-n("quantity")*(n("purchase_price")+n("terminal_fee_per_purchased_unit"));
 const inventory=q.chapter_id==="crude-inventory";
 const sales=n("quantity")*(inventory?n("benchmark_settlement")+n("physical_basis"):n("fixed_sales_price"));
 const cost=n("quantity")*(inventory?n("historical_purchase_price"):n("benchmark_settlement")+n("physical_basis"));
 return sales-cost-n("quantity")*n("freight_per_unit")+n("signed_paper_quantity")*(n("benchmark_settlement")-n("benchmark_entry"));
}
async function submit(page,q,zh=false){await page.getByLabel(`${zh?"你的答案":"Your answer"} (${q.answer_currency})`).fill(margin(q).toFixed(2));await page.getByRole("button",{name:zh?"检查答案":"Check answer",exact:true}).click();await expect(page.getByText(zh?"正确，误差在一分以内":"Correct within one cent",{exact:true})).toBeVisible();}
async function noOverflow(page){expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);}

test("gas handbook reading, checked practice, contextual questions, resume and existing tools",async({page})=>{
 await open(page);await expect(page.getByRole("heading",{name:"Hub supply and customer margin",exact:true})).toBeVisible();await expect(page).toHaveScreenshot("handbook-gas-reading-en-dark.png");
 const q=await practice(page);await expect(page.getByText("Offline reference mode — free-form questions are not answered",{exact:true})).toBeVisible();
 await page.getByLabel("Your answer (EUR)").fill("0");await page.getByRole("button",{name:"Check answer",exact:true}).click();await expect(page.getByText("Review the calculation",{exact:true})).toBeVisible();
 await submit(page,q);await align(page,".handbook-practice");await expect(page).toHaveScreenshot("handbook-gas-practice-en-dark.png");
 await page.getByLabel("Ask about this business").fill("Which risks remain after the benchmark hedge?");await page.getByRole("button",{name:"Send",exact:true}).click();await expect(page.locator(".handbook-reflection")).toBeVisible();
 await page.reload();await page.getByRole("button",{name:"Handbook",exact:true}).click();await expect(page.getByText("Correct within one cent",{exact:true})).toBeVisible();
 await page.getByRole("button",{name:"Open Risk Lab",exact:true}).click();await expect(page.getByRole("heading",{name:"European gas risk lab"})).toBeVisible();
 await page.getByRole("button",{name:"Handbook",exact:true}).click();await page.getByLabel("Business model").selectOption("gas-beach-hub");await expect(page.getByRole("heading",{name:"Beach-to-hub trading",exact:true})).toBeVisible();
 const beach=await practice(page);await submit(page,beach);await page.getByRole("button",{name:"Open existing AI practice",exact:true}).click();await expect(page.locator(".handbook")).not.toBeVisible();await expect(page.getByText(/Handbook context \(editorial draft\)/)).toBeVisible();await align(page,".cl-studio-composer");await expect(page).toHaveScreenshot("handbook-practice-context-en-dark.png");await page.getByRole("button",{name:"Clear handbook context"}).click();await expect(page.getByText(/Handbook context \(editorial draft\)/)).not.toBeVisible();await noOverflow(page);
});

test("Chinese mobile regas handbook, fresh practice and financial boundaries",async({page})=>{
 await page.setViewportSize({width:390,height:844});await open(page,"zh");await page.getByLabel("业务模型").selectOption("gas-lng-regas");await expect(page.getByRole("heading",{name:"LNG船货与气化外输",exact:true})).toBeVisible();await expect(page.locator(".handbook-reading")).toContainText("并非已验证的完整LNG");
 await align(page,".handbook-reading");await expect(page).toHaveScreenshot("handbook-regas-reading-zh-mobile-light.png");const q=await practice(page,true);await submit(page,q,true);await align(page,".handbook-practice");await noOverflow(page);await expect(page).toHaveScreenshot("handbook-regas-practice-zh-mobile-light.png");
});

test("crude handbook preserves historical inventory economics and independent practice",async({page})=>{
 await open(page,"en","crude_oil");const refinery=await practice(page);await submit(page,refinery);await page.getByLabel("Business model").selectOption("crude-inventory");await expect(page.getByRole("heading",{name:"Owned crude inventory and resale",exact:true})).toBeVisible();await expect(page.locator(".handbook-reading")).toContainText("Settlement-date cash excludes an acquisition paid earlier");const inventory=await practice(page);await submit(page,inventory);await noOverflow(page);
});
