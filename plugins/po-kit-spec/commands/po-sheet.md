---
description: Optional PO loop, step 1 (use only when po-loop-decision says it is worth it, or the user asks). Export the open questions and proposed rules as an Excel sheet for the Product Owner. Usage - /po-kit-spec:po-sheet <md folder> [config]
argument-hint: <md folder> [config.json]
allowed-tools: Bash(python3:*)
---
Run `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/po_sheet_export.py <md folder> <spec dir>/po-sheet-v<version>.xlsx [config.json]` for: $ARGUMENTS
Report the counts per owner from the script output (do not open the sheet). Tell the user in their language: send the file to the PO; for each row the PO picks a Decision (Accept / Change / Reject / Check on app), writes the answer, name and date; leave Decision empty when not answered; send it back and run `/po-kit-spec:po-import`.
