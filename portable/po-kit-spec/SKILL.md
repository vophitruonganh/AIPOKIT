---
name: po-kit-spec
description: Build a verified product spec (features, rules, acceptance criteria, test cases) from any running website, web app or mobile app and export it as an SRS in the chosen language or template. Use when asked to document, spec or reverse-engineer an existing product.
---

## Tool mapping
- Browser control for inspecting the app: use your browser tool (e.g. Playwright MCP). Same safety rules apply.
- Spec storage: a markdown folder (one file per module). Skip any step that mentions a Claude Doc or `mcp__Claude_Docs__*`.
- Scripts: `python3 -I scripts/<name>.py` from this folder (needs `scripts/setup.sh` once for the SRS export).
- "Agent" sections below are roles: run them as separate sessions/sub-tasks if your tool supports it, otherwise one after another.

## Workflow

# Reverse-spec builder
Turn any running product (website, web app, mobile app) into a spec where every detail is labelled by how sure we are, then export it. Nothing here is specific to one product: work from visible labels, roles and routes, never from one site's framework or wording. Six phases (0-5) plus an optional extension, the PO loop (6), used only when it is worth it, one approval gate before touching the app, role checkpoints where the user signs in, and script gates that need no one. Scripts: `./scripts/`. References (read only the one you need): `references/`. Follow `references/token-rules.md` throughout.

## Standards and language
- Talk to the user in the user's own language, whatever the spec or document language.
- If `.po-kit/standards.md` exists, follow it over these defaults (it may add to the safety rules, never weaken them). If not, offer `workflow `setup-standards`` once; defaults work.
- Ask the user for two languages and store them in standards/config: **spec language** (the text of the spec) and **document language** (`lang` of the exported SRS: `en`, `vi`, or one added with `workflow `add-language``). Default both to the user's language. Headings and labels stay canonical English in the spec; the export localizes them.

## Phases
0. **Prep** (`references/session-rules.md`): access preflight and driver choice (`references/drivers.md`) run first, without asking. Then ONE message asks for what is missing: target(s), environment (default production), roles to cover (no credentials: the user signs in), forbidden-action list from `references/safety-rules.md`, spec and document language, storage. Write `brief.md`. GATE 0 (the only approval gate): the user approves the forbidden list; "ok" accepts the defaults.
1. **Recon** (`spec-recon`, one role at a time): walk EVERY feature down to sub-features per `references/coverage-rules.md` with the chosen driver, plus sitemap, API (web only), enums, roles, glossary. Output `inventory.md`. Role checkpoint between roles. Update run (a previous `inventory.md` exists): merge with `scripts/inventory_diff.py` so ids and feature numbers never change; only features it lists go to Phase 2. Script gate: `inventory_check.py` passes. Post the feature list to the user for information and continue; adjust later if they object.
2. **Write** (`spec-writer`, one per module, parallel): 16-block template (+ optional Formulas) (`references/feature-block-standard.md`), source labels, BR/AC/TC numbers. Every inventory row is described with its exact label. Script gate: `spec_lint.py` and `inventory_check.py --md` have no FAIL (unanswered questions are expected until Phase 4).
3. **Deepen** (only for features under the bar in `playbook.md`, counted from the md files with grep, not by reading): rewrite those features; optional `spec-reviewer` for modules flagged `money_or_legal`.
4. **Verify** (`spec-verifier`, one per module, grouped by role): answer every open question `Verified / Partly verified / Cannot verify`, retry `Needs data` / `Needs role` rows. Script gate: no unanswered question, `inventory_check.py --md` passes. Items left `Cannot verify` and `PO proposal` are not reviewed here: the exported document lists them as "To confirm", and the optional PO loop can close them.
4b. **Diagrams** (`spec-diagrammer`, one per module plus one for the overview, parallel; v1.5): `diagram_plan.py <md dir> config.json` scores the diagrams this content needs (`references/diagrams.md`); the agent writes only the blocks marked `agent MISSING`, from facts already in the spec. Script gate: `diagram_check.py` has no FAIL.
5. **Export**: `references/export.md`; customer template via `workflow `export-custom``.
6. **PO loop (optional extension)**: decide with `references/po-loop-decision.md` after Phase 5; ask the user once with a recommendation; skip unless they want it. When used (repeat until signed off): `workflow `po-sheet`` exports open questions and proposed rules to Excel; the PO decides Accept / Change / Reject / Check on app; `workflow `po-import`` loads it (snapshot, `PO decided <date>` label, version bump, change list), a `spec-writer` aligns feature text from `po-apply.md`, `po-verify.md` goes to Phase 4, then export again. Never reopen a decided point; ids (INV, N.M, TBD, BR, BUG) stay stable across versions.
Details and pitfalls: `references/playbook.md`.

## Commands (workflows to run when the user asks)

### add-language
Add a language pack so the SRS can be exported in it. Usage - workflow `add-language` <language code, e.g. fr, ja, es>

Create `./scripts/lang/<arguments>.json` (if the plugin folder is read-only, create it in `.po-kit/lang/` and tell the user it must be copied into the plugin to be picked up).
1. Copy `scripts/lang/en.json`. Set `code` and `name`.
2. Translate every string value (keys stay). Keep placeholders `%d`, `%s`, `<module>`, `<feature>`, `UC-`, `BR-`, `AC-`, `TC-` and codes exactly. `blocks`, `labels`, `answers`, `tc_types`, `overview`, `module_sections`, `field_hdr` are the headings of a spec written in that language; `srs` is the generated document text; `stats` is the coverage table text.
3. Set the wording heuristics for that language: `system_actor` (name of the system actor), `system_clause_regex` (regex for "..., then the system ..."), `claims_regex` (words meaning always/never/at most N), `proposal_prefix`, `lower_first` (true if module names are lowercased mid-sentence).
4. Check: `python3 -I scripts/langpack.py` loads without error; build `examples/expense-tracker` with `"lang": "<code>"`, convert to PDF and inspect two pages. Tell the user that sentence splitting for the main flow relies on capital letters, so scripts without case (e.g. Chinese, Thai) get coarser actor detection.

### build-spec
Build a verified product spec from any running website, web app or mobile app (phases 0-4). Usage - workflow `build-spec` <URL, app id or captures folder>

Run the `reverse-spec-builder` skill for: <arguments>

First read `.po-kit/standards.md` if it exists (if not, mention once that `workflow `setup-standards`` records the team's own process and templates).
Phase 0, in this order:
1. Without asking: pick the driver and run the access preflight from `references/session-rules.md` and `references/drivers.md`. If the network blocks the target, switch to a driver on the user's machine and say so in one line; if nothing reaches it, stop and report the error.
2. ONE message for anything still missing: target(s), what the spec will be used for (as-is record, or basis for building/changing/testing), environment (production / staging / dev; default production), the roles to cover (never ask for passwords: the user signs in at each role checkpoint), the forbidden-actions list (show the defaults from `references/safety-rules.md`; forbid saving/submitting, not opening forms, and state the coverage cost of anything stricter, see `references/coverage-rules.md`), storage (Claude Doc with one tab per module, or a markdown folder), and the **spec language** and **document language** (default: the user's language).
3. After the user approves the forbidden list (the only gate), ask them to sign in as the first role, then work without asking. Stop only at role checkpoints (sign in as the next role) and when access is lost (session expired, device gone).

Model choice: do not hardcode models. Before each agent call, follow `references/model-routing.md` (`scripts/route_model.py`) to get a model tier and effort from the task's measured complexity, and pass them on that call.

### diff
Change list between two versions of a spec. Usage - workflow `diff` <old md folder> <new md folder> [lang]

Run `python3 -I ./scripts/spec_diff.py <old> <new> changes.md [lang]` for: <arguments>
Summarize the counts from the output in the user's language and give the path of `changes.md`. Do not read the spec files.

### export-custom
Export the spec into ANY template (Word, PDF, markdown outline, sheet) and language. Usage - workflow `export-custom` <template file> [markdown folder]

Produce a document from the spec using the template in: <arguments>
1. Read `.po-kit/standards.md` if present and the whole template. For Word/PDF/sheet templates load the matching document skill first. Ask once for the **document language** if not in standards.
2. **Mapping**: table `Template section | Source in spec | Transform | Gap`. Fill nothing yet. Work from exported markdown files, not the live doc.
3. **Gaps**: per unmapped section propose: write from existing content, leave `[TO BE COMPLETED BY PO]`, or drop. Ask in ONE message. Never invent content.
4. **Pilot**: build the first module only; user reviews layout, tone, mapping; fix.
5. **Full build** keeping the template's styles, numbering, headers/footers, cover. Keep source labels where there is room, else add a legend page. Translate headings and fixed text to the document language; keep the spec's own content as written unless the user asks to translate it.
6. **Checks**: sections vs template, privacy grep (names, test accounts, emails), no author in properties. Render the template and the output to images and compare them page type by page type (cover, table of contents, a section start, a use-case page, a table page): page size, fonts and sizes, heading numbering, table colours and column sets, captions. List every difference in a table and fix it before delivery; a layout the built-in builder cannot reach goes to the user as a named gap, never silently. If the template is close to the built-in classic layout, start from `"template": "classic"` in config.
7. Deliver the file, the mapping (appendix file), the placeholder list, leftover test records. Offer to save the mapping in `.po-kit/standards.md`.

### export-reader
Export the spec as a single-page web reader (contents, search, collapsible blocks, highlighted TBD). Usage - workflow `export-reader` <markdown folder> [config.json]

Build the reader for the spec folder in <arguments>: `python3 -I ./scripts/build_reader.py <md_dir> <config.json> <out.html>` (config defaults to the one next to the folder). Needs `pip install markdown`. Run `spec_lint.py` and `privacy_check.py` first; do not export a folder that fails. Then publish the HTML as the host allows (Claude Code: Artifact tool; otherwise give the file). The reader uses the same PO view as the SRS: statuses as a column, TBD ids, labels in the document language. Word/PDF stay the formal deliverables for sharing outside.

### export-srs
Export the spec as an IEEE-830 style SRS (Word + PDF) in the chosen language. Usage - workflow `export-srs` <markdown folder> [config.json]

Export for: <arguments>
1. `bash ./scripts/check_env.sh`; if anything is missing, stop and tell the user to run `bash ./scripts/setup.sh` (or offer to run it). Cloud sessions already have the tools.
2. No config yet: copy `scripts/config.example.json`, ask the user once for the fields in `references/config.md` (product, version, actors, **document language `lang`**, **spec language `spec_lang`**), save it.
3. Run lint first (`spec_lint.py`); stop on FAIL unless the user says to export anyway.
4. Run the two-pass build in `references/export.md`, then its checks (`privacy_check.py` on docx, pdf and markdown with the names/test accounts the user gives; TOC pages).
5. Deliver PDF, Word, coverage table (`spec_stats.py <dir> coverage.md <lang>`), list of leftover test records.
6. Optional PO loop: apply `references/po-loop-decision.md` (counts from `po_sheet_export.py <md folder> --count`). Recommend skip or use in one sentence with the counts and ask once in the same delivery message; no answer or "no" means skip, and do not ask again for this version.

### lint
Quality gate and coverage table for an exported spec. Usage - workflow `lint` <markdown folder> [lang]

Run `python3 -I ./scripts/spec_lint.py <folder>` and then `python3 -I ./scripts/spec_stats.py <folder> coverage.md [lang]` for: <arguments>
If an `inventory.md` exists next to the folder (or in it), also run `python3 -I ./scripts/inventory_check.py <inventory.md> --md <folder>` and report coverage FAIL rows (elements seen on the app but missing in the spec).
Summarize FAIL rows by feature and cause in a short table. Offer to fix them with the `spec-writer` agent (one module per agent). Do not read the spec files themselves.

### po-import
Optional PO loop, step 2. Load the Product Owner's answered sheet into the spec, bump the version, write the change list. Usage - workflow `po-import` <md folder> <answers.xlsx> [config]

1. Run `python3 -I ./scripts/po_sheet_import.py <md folder> <answers.xlsx> [config.json] --dry-run` for: <arguments>. Show the counts; if rows are "not found", list them and ask the user once whether to continue.
2. Run it again without `--dry-run`. It snapshots the old version under `versions/`, writes the answers and decided rules, bumps `version`, adds a `revisions` row, and writes `po-apply.md`, `po-verify.md` and `changes-v<old>-v<new>.md` next to the md folder.
3. If `po-apply.md` has rows: one `spec-writer` per module aligns the feature text (flows, rules, fields, AC, TC) with each decision, keeping the `PO decided <date>` label; never reopen a decided point.
4. If `po-verify.md` has rows: offer `workflow `verify`` for them (Phase 4).
5. Run lint and `inventory_check.py --md` (if an inventory exists), re-run `spec_diff.py <versions/v<old>/md> <md folder> changes-v<old>-v<new>.md` so the change list includes step 3, then offer `workflow `export-srs``. Report: decided, sent to QA, still open, file paths.

### po-sheet
Optional PO loop, step 1 (use only when po-loop-decision says it is worth it, or the user asks). Export the open questions and proposed rules as an Excel sheet for the Product Owner. Usage - workflow `po-sheet` <md folder> [config]

Run `python3 -I ./scripts/po_sheet_export.py <md folder> <spec dir>/po-sheet-v<version>.xlsx [config.json]` for: <arguments>
Report the counts per owner from the script output (do not open the sheet). Tell the user in their language: send the file to the PO; for each row the PO picks a Decision (Accept / Change / Reject / Check on app), writes the answer, name and date; leave Decision empty when not answered; send it back and run `workflow `po-import``.

### setup-standards
Record this team's own process, conventions, languages and templates so every later step follows them. Usage - workflow `setup-standards` [templates folder or files]

Create or update `.po-kit/standards.md` in the working folder (all commands and agents read it first). Input: <arguments>
1. If it exists, ask only what is missing. Copy any given templates/samples (spec, PRD, BRD, SRS, story format, test sheet) to `.po-kit/templates/` and infer conventions from them instead of asking.
2. Ask the rest in ONE message with defaults in brackets ("ok" accepts): spec language and document language [user's language]; output documents and templates [built-in SRS]; block set [default 16]; ID formats [BR-N.M.k, AC-N.M.k, TC-N.M.k]; source labels and what counts as verified [default]; quality bar [6 TC core, 3 minor]; approval gates [1: forbidden list; role checkpoints for sign-in]; roles and glossary [learned in Phase 1]; extra forbidden actions and test-data naming [defaults]; storage and reviewer.
3. Write one short section per topic marked `(default)` or `(custom)`, under two pages. Show it and save after a yes.
Limit to state plainly: lint, stats and the built-in SRS builder parse the default block names and ID formats. If the team changes them, mark `built-in lint/SRS: off` for those parts; use `workflow `export-custom`` and the `spec-reviewer` agent instead. The file may extend the safety rules, never weaken them.

### setup
Check and install the tools the Word/PDF export needs (graphviz, LibreOffice, Python modules in ~/.po-kit/venv). Usage - workflow `setup`

1. Run `bash ./scripts/check_env.sh`. If it prints "Environment OK", say so and stop.
2. Otherwise tell the user in one line what is missing and that `scripts/setup.sh` installs it (Homebrew on macOS, apt on Linux with sudo, Python modules in a private venv at `~/.po-kit/venv`, nothing system-wide for Python). Run it after the user says yes, then run `check_env.sh` again and report.

### start
Start here. Pick the website or the running app to document (an open browser tab, a URL, an Android app on a connected device, or a screenshots folder), then run the whole workflow. Usage - workflow `start` [URL | app | folder]

Entry point for a Product Owner. Input: <arguments>

1. **Target given** (a URL, an Android package or app name, or a folder of screenshots): use it and go to step 3.
2. **No target given**: build ONE numbered menu from what is running now, read-only, and ask the user to pick a number or paste a URL:
   - **Open browser tabs**: if a browser tool that lists tabs is available, list the user's open `http(s)` tabs as `title — host/path` (no query strings, at most 15, skip sign-in pages and browser-internal pages). Do not read their content.
   - **Android**: if `adb` is available, for each device in `adb devices` show the foreground app (`adb shell dumpsys activity activities | grep -m1 mResumedActivity`) as `Android: <app label or package> on <device model>`.
   - **Always add**: `Enter a URL`, `Use screenshots or screen recordings from a folder` (for iOS or any app that cannot be driven), and, if a `.po-kit/` spec folder already exists here, `Update the existing spec of <product>` (an update run).
   If nothing is detected, show only the always-added entries. Never open, reload or close any tab to build the menu.
3. **Confirm in one line**: "I will document <target> with the <web | android | capture> driver." A tab the user picked becomes the target URL (its origin and route); the agent works in its own new tab or window, never in the user's tab.
4. Run `workflow `build-spec` <target>` from Phase 0 (access preflight, one message of questions, forbidden list, sign-in per role). For an update run, follow the update rules in `references/coverage-rules.md`.
5. When Phase 4 is done, run `workflow `export-srs`` with the configured layout and follow its step on the optional PO loop.

### verify
Phase 4. Verify the spec's open questions on the real product with safe actions. Usage - workflow `verify` <module or tab>

Run Phase 4 for: <arguments>
Group the open questions by role, then by module. For each role: ask the user to sign in as that role (role checkpoint, `references/session-rules.md`), then run one `spec-verifier` per module, each in its own tab or session of that role, at most 4 in parallel. Brief each with: scope (module, feature ids, file path), driver, signed-in role, environment, the paths of `references/safety-rules.md`, `references/drivers.md`, `references/coverage-rules.md` and `inventory.md` (do not paste their text). When all roles are done, merge the bug lists into the bugs table, list leftover test records for engineering, and report counts of verified / partly / cannot verify. Do not ask the user to review Cannot verify items here: they go to the PO sheet (`workflow `po-sheet``).

## Roles

### spec-diagrammer
Writes the diagram blocks (process, sequence, wizard flow, ERD, decision table, timeline) that the diagram planner lists as missing, using only facts already in the spec. Never edits feature text. Full prompt: `prompts/spec-diagrammer.md`.

### spec-recon
Phase 1 recon. Maps every screen, API call, enum, role and glossary term of a running product (website, web app or mobile app) and records what cannot be seen. Does not write per-feature specs. Full prompt: `prompts/spec-recon.md`.

### spec-reviewer
Independent review of a module spec as a developer who must code from it and a QA who must test from it. Reports defects; never edits. Full prompt: `prompts/spec-reviewer.md`.

### spec-verifier
Phase 4. Verifies open questions and unverified labels of assigned features on the real app with safe actions and records exact results. Full prompt: `prompts/spec-verifier.md`.

### spec-writer
Phase 2/3. Writes or deepens assigned features to the fixed template with source labels and numbered BR/AC/TC. Full prompt: `prompts/spec-writer.md`.
