---
description: Add a language pack so the SRS can be exported in it. Usage - /po-kit-spec:add-language <language code, e.g. fr, ja, es>
argument-hint: <language code>
---
Create `${CLAUDE_PLUGIN_ROOT}/scripts/lang/$ARGUMENTS.json` (if the plugin folder is read-only, create it in `.po-kit/lang/` and tell the user it must be copied into the plugin to be picked up).
1. Copy `scripts/lang/en.json`. Set `code` and `name`.
2. Translate every string value (keys stay). Keep placeholders `%d`, `%s`, `<module>`, `<feature>`, `UC-`, `BR-`, `AC-`, `TC-` and codes exactly. `blocks`, `labels`, `answers`, `tc_types`, `overview`, `module_sections`, `field_hdr` are the headings of a spec written in that language; `srs` is the generated document text; `stats` is the coverage table text.
3. Set the wording heuristics for that language: `system_actor` (name of the system actor), `system_clause_regex` (regex for "..., then the system ..."), `claims_regex` (words meaning always/never/at most N), `proposal_prefix`, `lower_first` (true if module names are lowercased mid-sentence).
4. Check: `python3 -I scripts/langpack.py` loads without error; build `examples/expense-tracker` with `"lang": "<code>"`, convert to PDF and inspect two pages. Tell the user that sentence splitting for the main flow relies on capital letters, so scripts without case (e.g. Chinese, Thai) get coarser actor detection.
