---
description: Export the spec as a single-page web reader (contents, search, collapsible blocks, highlighted TBD). Usage - /po-kit-spec:export-reader <markdown folder> [config.json]
argument-hint: <markdown folder> [config.json]
---
Build the reader for the spec folder in $ARGUMENTS: `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/build_reader.py <md_dir> <config.json> <out.html>` (config defaults to the one next to the folder). Needs `pip install markdown`. Run `spec_lint.py` and `privacy_check.py` first; do not export a folder that fails. Then publish the HTML as the host allows (Claude Code: Artifact tool; otherwise give the file). The reader uses the same PO view as the SRS: statuses as a column, TBD ids, labels in the document language. Word/PDF stay the formal deliverables for sharing outside.
