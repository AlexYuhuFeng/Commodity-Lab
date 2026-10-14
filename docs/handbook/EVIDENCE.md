# HB3 — Handbook evidence portfolio

Open **Progress / 进度**. The handbook portfolio sits above the preserved device-wide practice progress. Select a local learner or add a named local profile. Continue a chapter, request checked numerical practice, submit an answer, and return to Progress. A refresh reads committed server records across conversations.

Numerical evidence, reasoning reviews and legacy progress remain separate. Three distinct first-pass variants qualify introductory numerical readiness; duplicate economic inputs and corrected retries do not. Required prerequisite diagnostics apply to reasoning submissions, while chapters and exploratory practice remain available. Remediation opens the economics or mitigation passage for the current gap.

Expand a graded exercise and explain exposure, hedge or defensible no-hedge choice, residual risks, and liquidity/credit/illustrative policy controls. A separate local profile can record ratings and specific feedback against the displayed rubric. Export audit JSON to retain the original inputs, first attempt, reasoning and all reviews with source versions. Local labels do not authenticate an instructor; readiness is never called mastery or live trading authorization.

## Contracts

- `GET/POST /api/v1/competency/learners`: local profile labels.
- `GET /api/v1/competency/rubric`: bilingual versioned draft rubric.
- `GET /api/v1/competency/learners/{id}/portfolio?commodity=european_gas|crude_oil`: cross-session evidence and derived readiness.
- `POST /api/v1/competency/learners/{id}/reasoning`: immutable reasoning tied to that learner's graded exercise.
- `POST /api/v1/competency/evidence/{id}/reviews`: separate reviewer, expected revision, explicit four-dimensional ratings, notes.
- `GET /api/v1/competency/learners/{id}/export`: evidence audit export, without hidden ungraded solutions.

Storage is additive to the existing training SQLite database. Legacy conversations migrate logically to `local` without rewriting their history. No numerical engine or AI provider contract was replaced. See [ADR 0006](../adr/0006-local-competency-evidence.md).

## Remaining qualification

This milestone provides repeatable arithmetic evidence and local reasoning review, not full professional competence. Authenticated instructor authority, independent commercial cases, externally calibrated rubric/domain sign-off, handbook import/review publishing and full desktop bundle qualification remain in the machine-readable backlog. Prior DeepSeek live evidence remains valid for the tested PR #7 head; no live calls were rerun in this environment, which has no configured provider secret.
