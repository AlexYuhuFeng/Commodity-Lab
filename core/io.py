from __future__ import annotations

import pandas as pd
from core.schema import SeriesSpec

def read_series_csv(spec: SeriesSpec) -> pd.DataFrame:
    df = pd.read_csv(spec.path)

    if spec.date_col not in df.columns or spec.value_col not in df.columns:
        raise ValueError(
            f"[{spec.name}] CSV列名不匹配。需要 {spec.date_col}/{spec.value_col}，实际为 {list(df.columns)}"
        )

    out = df[[spec.date_col, spec.value_col]].rename(
        columns={spec.date_col: "date", spec.value_col: spec.name}
    )
    out["date"] = pd.to_datetime(out["date"])
    out[spec.name] = pd.to_numeric(out[spec.name], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date")
    return out

def merge_series_on_date(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    if not dfs:
        return pd.DataFrame(columns=["date"])
    merged = dfs[0]
    for d in dfs[1:]:
        merged = merged.merge(d, on="date", how="outer")
    return merged.sort_values("date").reset_index(drop=True)
