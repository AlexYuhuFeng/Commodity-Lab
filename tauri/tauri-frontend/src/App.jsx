import React, { useState } from "react";
import { invoke } from "@tauri-apps/api/tauri";

export default function App() {
  const [msg, setMsg] = useState("ready");

  async function ping() {
    try {
      const resp = await invoke("ping_backend");
      setMsg(JSON.stringify(resp));
    } catch (e) {
      setMsg("error: " + e);
    }
  }

  async function simulate() {
    try {
      const payload = {
        orders: [
          {
            order_id: "o1",
            ticker: "CL=F",
            side: "sell",
            quantity: 1.0,
            open_date: "2024-01-02",
            close_date: "2024-02-02",
            open_price: null,
            close_price: null,
            hedge_type: "short_hedge",
          },
        ],
        source: "yfinance",
      };
      const resp = await invoke("simulate_backend", payload);
      setMsg(JSON.stringify(resp));
    } catch (e) {
      setMsg("simulate error: " + e);
    }
  }

  async function askAssistant() {
    try {
      const resp = await invoke("simulate_backend", { orders: [] });
      // placeholder: call backend assistant endpoint via HTTP fallback
      setMsg("assistant placeholder: backend reachable");
    } catch (e) {
      setMsg("assistant error: " + e);
    }
  }

  return (
    <div style={{ padding: 24, fontFamily: "Inter, sans-serif" }}>
      <h1>Hedge Lab (Tauri)</h1>
      <p>Status: {msg}</p>
      <button onClick={ping}>Ping backend</button>
      <button onClick={simulate} style={{ marginLeft: 8 }}>Simulate demo order</button>
      <button onClick={askAssistant} style={{ marginLeft: 8 }}>Assistant (placeholder)</button>
    </div>
  );
}
