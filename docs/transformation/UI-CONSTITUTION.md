# UX constitution — before feature implementation

Use the existing desktop navigation and locale. The risk lab follows Brief → current market evidence → decision → review → settlement. Every statistic supports an action or an explanation.

- Typography: inherited system sans with Chinese fallbacks; body 14–16 px, headings 20–28 px, tabular financial figures.
- Spacing: 4/8/12/16/24/32 px; compact labelled 40 px controls, 8 px radii, maximum readable workspace width 1120 px.
- Color: inherit theme variables, high-contrast text; semantic status always includes text, never color alone.
- Layout: two columns for evidence and decision; single column below 760 px; no horizontal scroll at 390 px.
- Interaction: explicit units, bounded numeric input, visible progress, disabled pending submission, inline actionable error, persist session ID, restart available. No future-price preview.
- Accessibility: semantic headings, labels, native buttons/fields, fieldsets, focus outline, live error/loading announcements, keyboard operation, reduced-motion friendly.
- Chinese/English: all workflow labels, policy explanations, market facts, remediation and status translated; codes only in audit exports.
- Verification: component tests plus real browser workflow, bilingual screenshots, overflow checks, and reproducible screenshot comparison where available. Global redesign is deferred until all legacy pages have evidence.
