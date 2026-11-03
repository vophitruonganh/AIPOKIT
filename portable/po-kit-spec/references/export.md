# Phase 5: export
1. Export each doc tab to markdown once (`mcp__Claude_Docs__export` then `scripts/decode_docs_export.py`), one tab at a time; work from the files afterwards.
2. `python3 -I ./scripts/spec_lint.py <md_dir>` and `spec_stats.py <md_dir> coverage.md [lang]`. Read only their output.
3. `bash ./scripts/check_env.sh` (fix with `setup.sh`).
4. Wording gate, then fix, then check again (until FAIL 0 and WARN 0, or each WARN left has a reason the user accepts):
```
S=./scripts
python3 -I $S/style_check.py --fix <md_dir> config.json   # fixes quotes, tone marks, "trên dev" itself, then W1-W12: survey talk, document status, dev hosts, env words, long sentences...
```
   What is left needs judgment (route it as task `reword`, `references/model-routing.md`). Fix every finding in the md files and config.json (cover, revisions, references, assumptions), not in the Word file. Rules and examples: `references/style-check.md`.
5. Build loop (set `lang` in config). Layout needs more than one pass: page numbers, and short tables the renderer split and headings left alone at a page bottom, which the next build moves to a new page (`pages.json` → `table_breaks`, `heading_breaks`):
```
python3 -I $S/diagram_check.py <md_dir> config.json                    # gate: no FAIL (v1.5 diagrams)
python3 -I $S/build_srs.py <md_dir> out.docx pages.json config.json    # pass 1 (pages.json may not exist)
soffice --headless --convert-to pdf out.docx
# repeat until pages.py reports "(+0)" for table and heading breaks and "moved 0", usually 2-4 rounds (stop at 5):
python3 -I $S/pages.py out.pdf out.docx.meta.json pages.json
python3 -I $S/build_srs.py <md_dir> out.docx pages.json config.json
soffice --headless --convert-to pdf out.docx
```
6. Export gate: `python3 -I $S/style_check.py --srs out.docx out.pdf <md_dir> config.json` (F1-F14 format, L1-L15 page layout, `--csv` for the full list). A FAIL blocks delivery. Fix the cause (md, config, or the build), rebuild, run again; do not hand-edit the Word file. Then `privacy_check.py out.docx <names> <test account names>`, the same on `out.pdf` and the md folder (exit 1 = fix before delivery).
7. Deliver PDF, Word, coverage table, list of leftover test records.
Web reader: `workflow `export-reader` <md_dir>` (same PO view, one HTML page). How unknowns are shown: `references/po-view.md`.
Short classic SRS (no appendices, open questions or bug ids): add `"template": "classic"` to a copy of config.json and run the same two passes. Other templates: `workflow `export-custom``. Other languages: `workflow `add-language``.


## Diagrams (v1.5)
The figures are chosen from the content by `diagram_plan.py` (see `references/diagrams.md`). Pick the set with `config.json` → `"diagrams": {"profile": "full" | "classic" | "po" | "dev", "include": [], "exclude": []}`; default `full` (`classic` for the classic template). Each figure is saved as PNG (Word) and SVG next to it in `srs_img/`.
