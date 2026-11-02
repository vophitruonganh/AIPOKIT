---
description: Quality gate and coverage table for an exported spec. Usage - /po-kit-spec:lint <markdown folder> [lang]
argument-hint: <markdown folder> [lang]
allowed-tools: Bash(python3:*)
---
Run `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/spec_lint.py <folder>` and then `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/spec_stats.py <folder> coverage.md [lang]` for: $ARGUMENTS
If an `inventory.md` exists next to the folder (or in it), also run `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/inventory_check.py <inventory.md> --md <folder>` and report coverage FAIL rows (elements seen on the app but missing in the spec).
Summarize FAIL rows by feature and cause in a short table. Offer to fix them with the `spec-writer` agent (one module per agent). Do not read the spec files themselves.
