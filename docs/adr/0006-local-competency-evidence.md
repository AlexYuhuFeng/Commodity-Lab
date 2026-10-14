# ADR 0006: Versioned local evidence without automatic mastery

Accepted for the HB3 engineering milestone. Builds on ADRs 0002, 0004 and 0005.

## Problem

Handbook answers were durable only inside individual conversations. A corrected answer, duplicate generated exercise or favorable profit could be mistaken for evidence of competence. There was no cross-conversation reasoning review or auditable learner ownership.

## Decision

Add `core.competency` and a FastAPI router to the existing modular application and SQLite store. Keep the original learning profile and device-wide legacy progress unchanged. Handbook conversations gain an explicit local learner ID; legacy records belong to `local`. UI conversation keys include nondefault learner IDs, and those learners never automatically attach shared legacy Risk Lab records. The API rejects those attachments until session ownership exists.

The five supported draft chapters map to existing skill IDs. Diagnostic prerequisite paths are hub supply → beach-to-hub → simplified regas, and refinery sourcing → owned inventory. They are versioned introductory learning paths, not a complete professional curriculum. Reading, AI conversation and practice remain open. Assessed reasoning submission requires three distinct first-pass numerical variants in each prerequisite chapter.

A variant fingerprint includes chapter ID/version, practice version and actual economic inputs, excluding the generation seed. The earliest graded exercise for each fingerprint owns its first-pass result; wrong attempts, retries and new IDs with identical economics cannot improve it. Three different correct first-pass variants establish numerical readiness only. They are **not independent commercial cases**.

Learners submit immutable four-part reasoning against a graded exercise: commercial exposure, hedge/no-hedge fit, residual mitigation, liquidity/credit/policy controls. A separate local profile records explicit 0–2 ratings and notes. No keyword/LLM grader scores this prose. The draft rubric permits multiple defensible choices. Review readiness requires at least 1 in every dimension, total at least 6, on two distinct first-pass variants. Combined numerical, prerequisite and review readiness yields `ready_for_guided_assessment`; **no endpoint awards mastery or certification**.

Review history is append-only within an atomically updated record, guarded by expected revision. New ratings supersede earlier ratings for readiness while retaining both. Export includes question and first-attempt snapshots, reflection, chapter/practice/evidence/rubric versions, synthetic-data and illustrative-policy labels, reviewer label, timestamps and complete review history. Ungraded exercises and private solutions are not exported. Chapter/practice/rubric drift cannot qualify current evidence.

## Boundaries and consequences

Local profile labels are not authenticated identities. Self-review under the same label is rejected, but labels cannot prove different people or instructor authority. This is an explicitly local reasoning-review workflow, not enterprise administration. Institutional mastery requires authenticated instructor authority, independent cases, calibrated rubrics and external domain approval in later milestones. We do not make prior draft chapters authoritative by adding review controls.

AI can use the current owner's derived chapter summary for remediation but cannot modify assessment or reviewer records. New local learners do not inherit the shared legacy profile. Deterministic financial engines, original learning workflows, Tauri architecture and release processes remain intact. No services or dependencies are added.
