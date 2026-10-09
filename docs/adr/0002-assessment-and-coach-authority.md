# ADR 0002 — separate assessment authority from coaching

Accepted for M1, 2026-10-09.

Policy checks gate simulated trades; deterministic cash flows describe outcomes; structured diagnostics collect provisional evidence about exposure, basis and liquidity. No combined score blends these axes. Multiple hedge sizes, including a reasoned decision to hold no hedge, may be defensible. Rationale remains an instructor-review item rather than a keyword-derived professional judgment score.

The coach receives only the learner-visible, server-computed snapshot. It cannot write session state, choose settlement prices or override policy/grades. Provider prose is explicitly ungraded and never parsed into actions. Missing configuration or failed providers return labelled offline questions and a practice exercise. Real model availability is not a prerequisite for learning or settlement.

A fixed, validated synthetic pack is available in M1. AI-generated executable scenarios are not added here; expanding them requires a reviewed schema, chronological/financial consistency gate and author/reviewer lifecycle (backlog M2-02/M3-04). The legacy AI generation experience is preserved, not newly certified by this slice.
