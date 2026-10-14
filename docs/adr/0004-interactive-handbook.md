# ADR 0004 — Add knowledge and context without replacing learning workflows

Date: 2026-10-14. Status: accepted engineering direction, editorial/domain review pending.

Commodity Lab becomes an interactive trading-company handbook. Commodity-neutral chapter contracts connect written commercial context to existing lessons, AI providers, practice templates and validated risk simulations. Initial collections: European gas (hub supply, beach-to-hub, LNG regas) and crude (refinery sourcing and merchant inventory).

Keep React/Tauri, FastAPI, profiles, learner records, courses, Workbench, practice generation, replay, Risk Lab, Haineng/DeepSeek and release workflows. Add modules rather than microservices. No autonomous migration or deletion of legacy data/workflows.

A chapter contains immutable versioned bilingual sections, contract/flow/economic explanations, risk/mitigation entries, explicit financial scope and links to registered practice/scenario identifiers. Content is an editorial training draft, not authoritative company policy or a verified legal/market handbook. General prose must qualify market-specific rules. No new commodity claimed supported.

Chapter conversations are durable local SQLite records with optimistic revision checks. The server supplies chapter content, available cards, actual learner profile and, optionally, only the current visible state of a compatible Risk Lab session. Conversation histories are chapter-bound; unknown versions, sections, links and incompatible sessions are rejected. AI cannot retrieve unrevealed market observations or private practice answers.

Generative UI uses a strict allowlist of explanation, risk-map, comparison, reflection, practice and simulation cards. The model returns prose, valid chapter references and card selections; the server assembles domain content/actions. No generated JSX, HTML, arbitrary URLs, financial numbers in authoritative cards, or LLM-computed settlement. Learner messages are untrusted. Prose is labeled ungraded AI guidance and references expose the actual reference passages, not a claim that every sentence is verified.

Numerical practice uses deterministic versioned templates with reproducible seeds, Decimal calculations, explicit units/currency, server-stored solutions and a grading endpoint. AI chooses presentation; engine creates/checks quantities and answers. Answers are withheld until submission. Records are provisional practice evidence, not mastery or an update to an established learner score. Existing richer AI/Workbench exercises remain available and separately labeled.

Without a provider, reference cards and practice remain usable. Offline mode explicitly says free-form questions are not answered; it never presents a canned response as an answer to the user's question. Provider failures/invalid structured output fall back visibly without leaking errors/credentials.

Trade-offs: one additive Handbook navigation item rather than replacing Courses; bounded whole-response cards rather than streaming arbitrary components; embedded Python content for packaging reliability rather than CMS/RAG services; authored draft content with anchors rather than fabricated sources. Later: instructor editing/review, content import, richer grounded retrieval, authoring permissions, repeated mastery evidence and streaming approved cards.
