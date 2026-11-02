---
description: Export the spec into ANY template (Word, PDF, markdown outline, sheet) and language. Usage - /po-kit-spec:export-custom <template file> [markdown folder]
argument-hint: <template file> [markdown folder]
---
Produce a document from the spec using the template in: $ARGUMENTS
1. Read `.po-kit/standards.md` if present and the whole template. For Word/PDF/sheet templates load the matching document skill first. Ask once for the **document language** if not in standards.
2. **Mapping**: table `Template section | Source in spec | Transform | Gap`. Fill nothing yet. Work from exported markdown files, not the live doc.
3. **Gaps**: per unmapped section propose: write from existing content, leave `[TO BE COMPLETED BY PO]`, or drop. Ask in ONE message. Never invent content.
4. **Pilot**: build the first module only; user reviews layout, tone, mapping; fix.
5. **Full build** keeping the template's styles, numbering, headers/footers, cover. Keep source labels where there is room, else add a legend page. Translate headings and fixed text to the document language; keep the spec's own content as written unless the user asks to translate it.
6. **Checks**: sections vs template, privacy grep (names, test accounts, emails), no author in properties. Render the template and the output to images and compare them page type by page type (cover, table of contents, a section start, a use-case page, a table page): page size, fonts and sizes, heading numbering, table colours and column sets, captions. List every difference in a table and fix it before delivery; a layout the built-in builder cannot reach goes to the user as a named gap, never silently. If the template is close to the built-in classic layout, start from `"template": "classic"` in config.
7. Deliver the file, the mapping (appendix file), the placeholder list, leftover test records. Offer to save the mapping in `.po-kit/standards.md`.
