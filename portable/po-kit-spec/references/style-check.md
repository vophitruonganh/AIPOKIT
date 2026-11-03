# Style check: wording, format, page layout

`scripts/style_check.py` runs twice in Phase 5:

- `style_check.py [--fix] <md_dir> config.json` checks the wording (W) after Phase 2, after Phase 4 and before the build. `--fix` first rewrites what has one right answer (curly quotes, old tone placement such as hóa → hoá, "trên dev", "QA (app dev)"), never inside quotes or code.
- `style_check.py --srs out.docx out.pdf <md_dir> config.json` checks the export (F, L) after the build.

FAIL blocks delivery. WARN is fixed too, unless the user accepts the reason it stays. The loop is always: check, fix the cause, rebuild, check again. Fix the md files or config.json (or the build script when the cause is layout), never the Word file by hand, because the next build overwrites it.

## Wording (md and config.json)

| Code | Level | What | How to fix |
| --- | --- | --- | --- |
| W1 | FAIL | How the survey was done: "khi khảo sát", "chưa khảo sát", "chỉ khảo sát desktop", "tài khoản test", "Quan sát ngày …, chỉ đọc", "theo brief", links to `source/…`, an "Environment" appendix, survey words on the cover or in revisions, references, assumptions; what the surveyor did or did not do ("chưa bấm", "không bấm", "chưa thử", "brief cấm"); test data used while surveying ("hồ sơ TEST", "ngân sách TEST") outside test cases and acceptance criteria | Delete the phrase or say the fact without the survey: "(chỉ khảo sát desktop)" → "Unverified"; "bị chặn khi khảo sát (gửi SMS thật)" → "mô tả từ mã client (Inferred from code)"; revision "Bản đầu, khảo sát trên dev…" → "Bản đầu." |
| W2 | FAIL | Document status or audience: "as-is", "bản để PO xác nhận", "chưa phải spec" | Delete |
| W3 | FAIL in features, WARN elsewhere | Environment hosts (dev, staging, IP, localhost), local paths (`/mnt/…`, `/Users/…`), environment words ("trên dev", "app dev", "môi trường dev") | Paths only (`/sign-up`), "app cùng môi trường", "site giới thiệu". A bug about a link that points to production says "trỏ app production" and names the production host |
| W4 | FAIL | A word from the glossary "Do not use" column | Use the standard term |
| W5 | WARN | A quoted label after "Bấm" / "chọn" that is not in the inventory | Copy the exact label from the inventory |
| W6 | FAIL | Endpoint names outside Appendix A | Move them to Appendix A |
| W7 | WARN | Sentence over 35 words (an enumeration after ":" counts as one item) | Split into two sentences |
| W8 | WARN | Role name written in lower case in a feature | Write it as in the role table |
| W9 | WARN | Mixed straight and curly quotes | Use one kind |
| W10 | FAIL | TODO, TBD, FIXME, ???, lorem ipsum | Fill in, or turn into an open question |
| W11 | WARN | Decree, law or circular without a source label | Add the label or `[LEGAL REVIEW NEEDED]` |
| W12 | WARN | Two tone placements of one word (hoá / hóa, thuỷ / thủy) | Use one (`--fix` does it) |
| W13 | WARN | Class names of a UI framework (`nz-select`, `mat-…`, `ant-…`) | Say what the control does: "ô chọn có tìm kiếm" |

## Format (Word and PDF)

| Code | Level | What |
| --- | --- | --- |
| F1 | FAIL | Heading numbers skip or repeat |
| F2 | FAIL | Figure / table numbers not continuous in a chapter |
| F3 | FAIL | Contents still shows "00", or a page number differs from the page |
| F4 | FAIL | A contents link opens the wrong page, or the contents has no links |
| F5 | FAIL | Image wider than the text area or taller than a page |
| F6 | WARN | Table row with an empty cell (nested flow tables count as text) |
| F7 | FAIL | Markdown left in the PDF: `**`, `##`, `](`, `<br>`, `\|` |
| F8 | FAIL | Environment words in the export ("trên dev", "môi trường dev", "staging") |
| F9 | FAIL | Body font differs from the document style |
| F10 | FAIL | Cover shows a source, environment, account, "as-is" |
| F11 | FAIL | A BR / AC / TC / UC code is mentioned but never defined |
| F12 | FAIL | A personal email address (role mailboxes such as cskh@, support@ are allowed) |
| F13 | WARN | English left in a Vietnamese document: column names, block headings, source tags (Inferred from code, Safety-blocked, Needs role, Works, Yes / No) |
| F14 | FAIL | Empty reference: "ma trận quyền chi tiết ở .", "use case ;", "()" (a config value or md text is missing) |

## Page layout (PDF)

| Code | Level | What | Fixed by the build |
| --- | --- | --- | --- |
| L1 | FAIL | Text or image outside the margins | — |
| L2 | FAIL | Heading space before not larger than space after | style values |
| L3 | FAIL | Body size outside 10.5–13 pt or line spacing outside 1.0–1.3 | style values |
| L6 | FAIL | Heading, block label or lead-in line ("Vai trò và quyền trong module:") alone at the bottom of a page | keep-with-next on headings and on the lead-in sentence of a figure; when the renderer still leaves one alone, `pages.py` records it in `heading_breaks` and the next build starts it on a new page |
| L7 | FAIL | Figure caption separated from its figure | keep-with-next; a table caption stays with its table |
| L9 | FAIL | Short table row that can break across pages; long table without a repeated header | cantSplit on short rows, repeated header on tables over 8 rows |
| L10 | WARN | Short table (≤ 10 rows, under a third of a page) split over two pages | `pages.py` records it in `table_breaks`, the next build starts it on a new page; a break that is no longer needed is dropped |
| L11 | WARN | Page more than 35 % empty at the bottom, when the next block could have fitted | Not reported when the next page opens with a figure, or a short table kept whole, taller than the gap |
| L12 | WARN | Page with only one or two lines | — |
| L13 | FAIL | Chapter not starting a page | page break before H1 |
| L14 | WARN | Use case table starting at the very bottom of a page | keep-with-next on its first rows |
| L15 | WARN | Column narrower than its longest word (words break mid-word) | column widths fit the longest word; empty columns are left out |
| L16 | WARN | Diagram text under 6 pt once the figure is fitted on the page | activity diagrams shorten step labels and draw fewer alternate branches until the text is at least 7 pt (the use case table keeps every step); other types: split the block or shorten labels |

## Project overrides

Optional lines in `.po-kit/standards.md` next to config.json:

```
style.banned: <phrase>     extra banned phrase (W1)
style.allow: <phrase>      never report this phrase
style.off: W7              switch a check off
style.fail: W5             raise a WARN check to FAIL
style.max_words: 35        sentence length limit (W7)
```
