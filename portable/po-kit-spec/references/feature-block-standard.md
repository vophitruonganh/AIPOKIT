# Feature template: section `## N.M Feature name \`route\``
The template has 16 required blocks plus an optional Formulas block (rows below; row numbers are for reference). Use these headings exactly (bold line `**Heading**`); the scripts parse them. Headings of any shipped language pack are also accepted (legacy Vietnamese specs still lint and build). Content may be in any language.

| # | Heading | Content |
| --- | --- | --- |
| 1 | Problem & value | 2-3 sentences: who has what problem, how the feature solves it |
| 2 | User stories | 3-5 "As a <role>, I want <task> so that <benefit>" |
| 3 | Main flow | Numbered, 5-12 steps, each starts with the actor ("Manager...", "System..."). Short. No endpoint/parameter names |
| 4 | Alternate flows & exceptions | Lines "When <condition> → <system behaviour>" |
| 5 | Business rules | `BR-N.M.k`, continuous, one verifiable rule per line |
| 6 | UI & data | Field tables per screen block; buttons with shortcut, result, when enabled |
| 7 | Acceptance criteria | `AC-N.M.k` Given/When/Then, independently checkable |
| 8 | Field specification | Table: Field / Type / Required / Format / Default / Validation / Error message |
| 9 | State lifecycle | Table: From / To / Who / Action / Blocking condition / Effect; real enum values |
| 10 | Permissions by action | Table: Action / each role / Yes-No-Unknown |
| 11 | Formulas & calculations | Only if any: formula, order, numeric example |
| 12 | UI states | Empty, loading, load error, no permission, paging, default sort, filters, search fields |
| 13 | Edge cases & error handling | Table: Situation / Expected / Source. Cover duplicates, edit/delete in use, concurrency, lost connection, expired session, expiry, 0/negative/huge |
| 14 | Module links | Table: In/Out / Module / Data / When |
| 15 | Notifications, audit log & print/export | Who is notified, what is audit-logged, what print/export contains |
| 16 | Test cases | Table: `TC-N.M.k` / Precondition / Steps / Expected / Type (Main, Alternate, Edge, Permission). >=6 for a core feature, >=3 minor, at least one Edge and one Permission |
| 17 | Open questions & assumptions | Table: Question / Assumption / Owner / Priority / Answer. Every uncertainty goes here; owner "QA" if testable on the app. Phase 4 writes the result into the Answer column (add it if missing); lint treats a row as answered when it starts with an allowed prefix |
Blocks 8, 9, 11 may be absent when there are no fields, states or formulas; any other inapplicable block says `Not applicable: <reason>`.

Optional in any feature: one or more ` ```diagram <type>: <title>` blocks (sequence, flow, decision, timeline, state) written by `spec-diagrammer` after the Alternate flows block; syntax in `references/diagrams.md`. Writers do not need to add them.

## Source labels (every concrete detail)
| Label | Meaning | Use |
| --- | --- | --- |
| Observed <date> | Seen on the UI or by a real action | AC and test case directly |
| Inferred from API | From parameters, enums, responses; not seen on the UI | AC, QA confirms |
| PO proposal | Desired behaviour the app lacks or cannot show | Product decides before dev |
| PO decided <date> | Decided by the Product Owner (PO loop) | AC and test case directly; never set by an agent's guess |
| Unverified | No data | Never an AC |
Open-question answers start with `Verified <date>:`, `Partly verified <date>:` or `Cannot verify <date>:` (reason required).

## Writing rules
Product-owner voice, short sentences, glossary terms. No endpoint/parameter names in the body (Appendix A only). Never invent numbers, thresholds or statutes: label `PO proposal` or `[LEGAL REVIEW NEEDED]`. Error messages verbatim if observed, else `Proposal: "..."`. Fix contradictions at once or list them in the bugs table.
