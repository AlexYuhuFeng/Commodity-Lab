# Handbook context across existing practice — HB2

2026-10-14. Additive branch `feature/handbook-practice-grounding`, based on PR #6 (`d2b8d51c`). See ADR 0005.

The first handbook milestone connected to existing tools by template selection only. This increment carries chapter ID/version into ordinary and streaming case generation and stores server-resolved identity in training_session. Existing saved case snapshots retain that reference. Generic tutor, exam prose, event drill, playbook, Socratic coach, advisor and floating live assistant recover the original chapter passages from the registry. No new provider or numerical engine.

Version, template and commodity mismatches are rejected before generation. Conflicting explicit/case references are rejected. Client-supplied chapter titles/passages never establish source authority: registered versioned text supplies prompts. Legacy calls without chapter context retain their existing builders. Handbook-linked coaching uses the actual current case instead of default gas scenarios/capacity, including for crude.

Learners see an attached-context notice in existing practice, can clear it for future generic generation, and context expires when selecting unrelated courses or products. Clearing pending context does not rewrite provenance of an already generated case. Saved reviews and matching variants can recover case-derived references.

## Verification

- **252 backend tests passed** (226 prior + 26 grounding regressions): ordinary/streamed generation for hub, beach, regas and inventory; source recovery; all seven coaching capabilities; current crude case and exclusion of unrelated gas-capacity defaults; live assistant; mismatch/stale version rejection; forged-source exclusion. Provider responses are mocked, not real qualification.
- **63 frontend tests passed**: prior 61 plus two complete App integration tests for handbook → existing generation → live assistant context, and explicit clearing before generic practice. Handbook component callback contract remains tested.
- Production Vite build passed.
- Seven real-backend browser workflows continue to pass; new handoff assertions verify visible chapter context and clearing. Existing 14 comparisons are preserved; a new context-banner screenshot was inspected, and all **15 final screenshot comparisons pass** without updating baselines.
- Linux PyInstaller build passed. Fresh packaged backend smoke passes the five handbook exercises and the source/version rejection gate; existing three gas/crude scenario smokes also pass.

## Limits and next work

This supplies learning context, not authenticated case provenance, a reviewed executable scenario, authoritative market content or expanded financial support. Existing AI-generated cases remain exploratory; reviewed Risk Lab calculations and policy scoring remain separate. No legacy numerical method/scoring/release behavior changed.

Real Haineng/DeepSeek calls, grounded response quality and latency, external editorial/domain review, full desktop bundles and repeated instructor-reviewed mastery remain unverified/pending. Next: review/import authored handbook content, qualify actual configured-provider behavior, then deepen validated beach/route and regas models. HB-09's repeated competency evidence criterion remains pending even though its grounding portion is delivered.

Real application [attached-context screenshot](../../tauri/tauri-frontend/e2e/handbook.spec.js-snapshots/handbook-practice-context-en-dark-linux.png). Durable test logs: `/workspace/scratch/commodity-ground-*.log`.

## Live follow-up

[DeepSeek live qualification](DEEPSEEK-LIVE.md) records real authentication, bilingual conversations, streaming generation and tutoring. Live testing led to the public Flash model mapping correction, concise-card guidance, unknown-unit protection and strict references for handbook-linked generic coaching. The final backend suite has 255 passing tests; live successes do not constitute broad model/domain certification.
