---
description: Record this team's own process, conventions, languages and templates so every later step follows them. Usage - /po-kit-spec:setup-standards [templates folder or files]
argument-hint: [templates folder or files]
---
Create or update `.po-kit/standards.md` in the working folder (all commands and agents read it first). Input: $ARGUMENTS
1. If it exists, ask only what is missing. Copy any given templates/samples (spec, PRD, BRD, SRS, story format, test sheet) to `.po-kit/templates/` and infer conventions from them instead of asking.
2. Ask the rest in ONE message with defaults in brackets ("ok" accepts): spec language and document language [user's language]; output documents and templates [built-in SRS]; block set [default 16]; ID formats [BR-N.M.k, AC-N.M.k, TC-N.M.k]; source labels and what counts as verified [default]; quality bar [6 TC core, 3 minor]; approval gates [1: forbidden list; role checkpoints for sign-in]; roles and glossary [learned in Phase 1]; extra forbidden actions and test-data naming [defaults]; storage and reviewer.
3. Write one short section per topic marked `(default)` or `(custom)`, under two pages. Show it and save after a yes.
Limit to state plainly: lint, stats and the built-in SRS builder parse the default block names and ID formats. If the team changes them, mark `built-in lint/SRS: off` for those parts; use `/po-kit-spec:export-custom` and the `spec-reviewer` agent instead. The file may extend the safety rules, never weaken them.
