# Phase 5: export
1. Export each doc tab to markdown once (`mcp__Claude_Docs__export` then `scripts/decode_docs_export.py`), one tab at a time; work from the files afterwards.
2. `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/spec_lint.py <md_dir>` and `spec_stats.py <md_dir> coverage.md [lang]`. Read only their output.
3. `bash ${CLAUDE_PLUGIN_ROOT}/scripts/check_env.sh` (fix with `setup.sh`).
4. Two passes (set `lang` in config):
```
S=${CLAUDE_PLUGIN_ROOT}/scripts
python3 -I $S/build_srs.py <md_dir> out.docx pages.json config.json    # pass 1 (pages.json may not exist)
soffice --headless --convert-to pdf out.docx
python3 -I $S/pages.py out.pdf out.docx.meta.json pages.json
python3 -I $S/build_srs.py <md_dir> out.docx pages.json config.json    # pass 2
soffice --headless --convert-to pdf out.docx
```
5. Checks: TOC page numbers; `python3 -I $S/privacy_check.py out.docx <names> <test account names>` and the same on `out.pdf` and the md folder (exit 1 = fix before delivery; flags authors, emails, phone numbers and the terms given).
6. Deliver PDF, Word, coverage table, list of leftover test records.
Web reader: `/po-kit-spec:export-reader <md_dir>` (same PO view, one HTML page). How unknowns are shown: `references/po-view.md`.
Short classic SRS (no appendices, open questions or bug ids): add `"template": "classic"` to a copy of config.json and run the same two passes. Other templates: `/po-kit-spec:export-custom`. Other languages: `/po-kit-spec:add-language`.
