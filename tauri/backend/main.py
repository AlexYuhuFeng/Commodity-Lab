from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import pandas as pd

app = FastAPI()


class PingResp(BaseModel):
    message: str


class OrderSpec(BaseModel):
    order_id: str
    ticker: str
    side: str
    quantity: float
    open_date: str
    close_date: str
    open_price: float | None = None
    close_price: float | None = None
    hedge_type: str | None = "short_hedge"


@app.get("/api/ping", response_model=PingResp)
async def ping():
    return {"message": "pong from Tauri Python backend"}


@app.get("/api/instruments")
def list_instruments(limit: int = 100):
    # Use project root to find the DuckDB database
    project_root = Path(__file__).resolve().parents[3]
    from core.db import default_db_path, get_conn, init_db

    db_path = default_db_path(project_root)
    con = get_conn(db_path)
    init_db(con)
    df = con.execute(f"SELECT ticker, name, exchange, currency, unit, is_watched FROM instruments LIMIT {limit}").df()
    return df.to_dict(orient="records")


@app.post("/api/simulate")
def simulate_portfolio(orders: List[OrderSpec], source: str = "yfinance"):
    """Simulate a list of `OrderSpec`. For each order we fetch historical prices
    (from Yahoo Finance or Platts) and compute the simulation per order. Returns
    aggregated results and portfolio score."""
    from core.hedge import VirtualOrder, simulate_virtual_order, score_hedge_result
    from core.hedge import summarize_hedge_performance

    results = []
    for o in orders:
        tk = (o.ticker or "").strip()
        if not tk:
            raise HTTPException(status_code=400, detail="Ticker missing in order")

        # Fetch price series depending on source
        prices = None
        try:
            if source == "platts":
                from core.platts_connector import fetch_platts_history

                prices = fetch_platts_history(tk)
            else:
                from core.yf_prices import fetch_history_daily

                prices = fetch_history_daily(tk)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Price fetch failed for {tk}: {exc}")

        vo = VirtualOrder(
            order_id=o.order_id,
            ticker=tk,
            side=o.side,
            quantity=o.quantity,
            open_date=pd.to_datetime(o.open_date).date(),
            close_date=pd.to_datetime(o.close_date).date(),
            open_price=o.open_price,
            close_price=o.close_price,
            hedge_type=o.hedge_type or "short_hedge",
        )

        try:
            row = simulate_virtual_order(prices, vo)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        row["score"] = score_hedge_result(row)
        results.append(row)

    df = pd.DataFrame(results)
    perf = summarize_hedge_performance([], df)
    # overall score: average of individual scores
    overall = float(df["score"].mean()) if not df.empty else 0.0
    return {"results": df.to_dict(orient="records"), "summary": perf, "score": overall}


@app.post("/api/score_portfolio")
def score_portfolio_endpoint(rows: List[Dict]):
    from core.hedge import score_portfolio

    df = pd.DataFrame(rows)
    try:
        score = score_portfolio(df)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"score": score}


@app.post("/api/assistant")
def assistant_query(payload: Dict):
    question = payload.get("question", "")
    mode = payload.get("mode", "Performance review")
    context = payload.get("context")
    history = payload.get("history")
    try:
        from core.deepseek import ask_deepseek

        answer = ask_deepseek(question, context=context, mode=mode, history=history)
        return {"answer": answer}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
