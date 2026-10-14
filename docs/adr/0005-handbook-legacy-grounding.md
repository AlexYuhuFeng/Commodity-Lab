# ADR 0005 — Carry chapter identity into existing AI practice

2026-10-14. Additive engineering decision; editorial/provider qualification still pending.

Handbook links previously selected a legacy template but lost the written chapter context. Add optional chapter ID/version to existing generator/coaching contracts. Server resolves original passages from the chapter registry, validates version/template/commodity compatibility, and adds a trusted reference message. Requests without a chapter keep their previous behavior.

Both ordinary and streaming case generation store a minimal server-created reference in training_session. Existing saved case snapshots therefore retain the chapter. Advisor, tutor, drills and live assistant recover source passages from that reference; client-supplied chapter text is never trusted. Explicit references conflicting with a case are rejected. This is learning context, not proof of user identity or protected financial authority.

Frontend shows bilingual attached-context status in existing practice, lets learners clear it, clears pending context on unrelated template/commodity changes, and keeps case-derived context for follow-up variants and saved reviews. No new page/LLM provider/market engine. Legacy exploratory generation remains separate from the reviewed Risk Lab registry and its financial authority. Repeated competency/instructor evidence remains future work.
