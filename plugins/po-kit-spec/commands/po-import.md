---
description: Optional PO loop, step 2. Load the Product Owner's answered sheet into the spec, bump the version, write the change list. Usage - /po-kit-spec:po-import <md folder> <answers.xlsx> [config]
argument-hint: <md folder> <answers.xlsx> [config.json]
---
1. Run `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/po_sheet_import.py <md folder> <answers.xlsx> [config.json] --dry-run` for: $ARGUMENTS. Show the counts; if rows are "not found", list them and ask the user once whether to continue.
2. Run it again without `--dry-run`. It snapshots the old version under `versions/`, writes the answers and decided rules, bumps `version`, adds a `revisions` row, and writes `po-apply.md`, `po-verify.md` and `changes-v<old>-v<new>.md` next to the md folder.
3. If `po-apply.md` has rows: one `spec-writer` per module aligns the feature text (flows, rules, fields, AC, TC) with each decision, keeping the `PO decided <date>` label; never reopen a decided point.
4. If `po-verify.md` has rows: offer `/po-kit-spec:verify` for them (Phase 4).
5. Run lint and `inventory_check.py --md` (if an inventory exists), re-run `spec_diff.py <versions/v<old>/md> <md folder> changes-v<old>-v<new>.md` so the change list includes step 3, then offer `/po-kit-spec:export-srs`. Report: decided, sent to QA, still open, file paths.
