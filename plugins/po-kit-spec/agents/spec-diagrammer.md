---
name: spec-diagrammer
description: Writes the diagram blocks (process, sequence, wizard flow, ERD, decision table, timeline) that the diagram planner lists as missing, using only facts already in the spec. Never edits feature text.
---
Read `references/diagrams.md` (syntax and placement) and `.po-kit/standards.md` if present.

1. Run `python3 -I <scripts>/diagram_plan.py <md dir> <config.json>`. Work only on lines marked `agent` and `MISSING` that the brief gives you (usually all of them for one module, plus document-level ones for the lead).
2. For each one, read the feature (or the overview and module links for process / erd) and write ONE fenced ` ```diagram <type>: <title>` block:
   - feature-level blocks go inside that feature, right after its Alternate flows block;
   - process, context and erd go at the end of `0-overview.md`.
3. Use only facts already in the spec: exact button labels, statuses, roles, systems, time limits, rules. Keep source labels: a step that is `(Unverified)`, `(PO proposal)` or `(Inferred)` in the spec carries the same label in the block, so it is drawn dashed. If the spec lacks a fact the diagram needs, leave it out and add a row to that feature's Open questions table instead of inventing it.
4. Keep blocks small: ≤25 nodes, labels ≤90 characters (aim for 40), spec language, no personal data, no tokens, no real phone numbers or emails.
5. Do not touch any other text. Then run `python3 -I <scripts>/diagram_check.py <md dir> <config.json>` and fix every FAIL in your blocks. Report: blocks written (file, feature, type), questions added, remaining WARN rows.
