---
description: Export the spec as an IEEE-830 style SRS (Word + PDF) in the chosen language. Usage - /po-kit-spec:export-srs <markdown folder> [config.json]
argument-hint: <markdown folder> [config.json]
allowed-tools: Bash
---
Export for: $ARGUMENTS
1. `bash ${CLAUDE_PLUGIN_ROOT}/scripts/check_env.sh`; if anything is missing, stop and tell the user to run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh` (or offer to run it). Cloud sessions already have the tools.
2. No config yet: copy `scripts/config.example.json`, ask the user once for the fields in `references/config.md` (product, version, actors, **document language `lang`**, **spec language `spec_lang`**), save it.
3. Run lint first (`spec_lint.py`), then `style_check.py <md> config.json`; fix every finding in the md and config, run again until FAIL 0 (stop on FAIL only if the user says to export anyway).
4. Run the build loop in `references/export.md`, then `style_check.py --srs` on the Word and PDF: fix the cause, rebuild, check again until FAIL 0 and no WARN left without a reason; then `privacy_check.py` on docx, pdf and markdown with the names/test accounts the user gives.
5. Deliver PDF, Word, coverage table (`spec_stats.py <dir> coverage.md <lang>`), list of leftover test records.
6. Optional PO loop: apply `references/po-loop-decision.md` (counts from `po_sheet_export.py <md folder> --count`). Recommend skip or use in one sentence with the counts and ask once in the same delivery message; no answer or "no" means skip, and do not ask again for this version.
