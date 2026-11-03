Read `.po-kit/standards.md` if present and `references/feature-block-standard.md` (path in your brief). Edit only the module/features you are given. Write the content in the spec language given in your brief; headings and labels stay exactly as in the template.

Open-questions tables have an Answer column (leave it empty for Phase 4).
Read only your slice of the inventory: `python3 -I <scripts>/inventory_check.py <spec dir>/inventory.md --slice <N>` (not the whole file). Every row whose Feature is in your scope must be described in that feature (UI & data, Field specification or UI states) using its exact Label; Safety-blocked / Needs data / Needs role rows also get an Open-questions row.
Per feature:
1. Keep correct existing detail; fix only wrong or contradictory parts. Add missing blocks; rewrite shallow ones (main flow <5 steps, <5 rules, no error flows).
2. Every concrete detail (length, limit, error message, sort order, page size) has a source label. No source means `PO proposal` or `Unverified` plus a row in Open questions (owner `QA` if testable on the app).
6. Write about the product only, never about the survey or the environment: no hosts, no "on dev" / "test account" / "read-only" / "during the survey", no dates of observation in the text (the source label carries them). The banned list and examples: `references/style-check.md` (W1-W3).
3. Continuous BR/AC/TC numbers, each TC typed; >=6 TC for a core feature (3 minor), including one Edge and one Permission.
4. Cover edge cases: duplicates, edit/delete in use, concurrency, lost connection, expired session, expiry, 0/negative/huge.
5. Never invent statutes, thresholds or limits; write `[LEGAL REVIEW NEEDED]`.

Doc writes: one feature per update, guarded (`ifHash` + `ifRev`); on `guard_mismatch` re-read and keep the other person's content.
Then run `python3 -I <scripts>/spec_lint.py <exported md dir>` `python3 -I <scripts>/inventory_check.py <spec dir>/inventory.md --md <exported md dir>` and `python3 -I <scripts>/style_check.py --fix <exported md dir> <config.json>` (scripts path in your brief); fix the FAIL rows in scope that `--fix` could not. Report (under 120 words): features done, TC added, contradictions fixed, new QA questions.
