# po-kit-spec (Claude Code plugin, part of AIPOKIT) v1.4.4
Reverse-engineer any running website, web app or mobile app into a verified, labelled product spec, then export it as an IEEE-830 style SRS (Word/PDF) in the language or template you choose. Nothing in the plugin is tied to one product: it works from visible labels, roles and routes.

## Install
```
/plugin marketplace add vophitruonganh/AIPOKIT
/plugin install po-kit-spec@aipokit
```
Easiest: `git clone https://github.com/vophitruonganh/AIPOKIT.git ~/AIPOKIT && bash ~/AIPOKIT/install.sh` (installs the plugin and the export tools, see the repository README). Manually, from a local copy, in a terminal (Claude Code does not let an agent install plugins into itself):
```
claude plugin marketplace add /path/to/po-kit
claude plugin install po-kit-spec@aipokit --scope user
```
Open a new session afterwards to see the `/po-kit-spec:*` commands.

## How a run goes
1. **Access check and driver** (automatic): `web` (a browser Claude controls), `android` (`adb`), or `capture` (your screenshots). If Claude's network cannot reach the target, it switches to a browser on your machine and tells you.
2. **One message of questions**: target, what the spec is for, environment (production / staging / dev), roles to cover, forbidden actions, languages, storage. You approve the forbidden list: the only approval gate.
3. **You sign in** for each role when asked (Claude never types passwords; a separate browser profile per role avoids signing out). Recon walks every feature into `inventory.md`.
4. Write, deepen (only weak features), verify: gated by scripts (`inventory_check.py`, `spec_lint.py`), no further questions.
5. **Export** the SRS (full PO view, or `"template": "classic"`), web reader, or your own template.
6. **Optional PO loop**: offered once, only when the spec is a basis for building or testing and High-priority decisions are pending.

## Commands
| Command | Does |
| --- | --- |
| `/po-kit-spec:start [URL or app]` | **start here**: pick an open browser tab, a URL, a running Android app or a screenshots folder; runs the whole workflow |
| `/po-kit-spec:setup` | check and install the export tools |
| `/po-kit-spec:setup-standards [templates]` | record your own process, templates, languages (optional) |
| `/po-kit-spec:build-spec <url, app or captures folder>` | phases 0-4 |
| `/po-kit-spec:verify <module>` | phase 4 only, grouped by role |
| `/po-kit-spec:lint <md folder> [lang]` | quality gate + coverage table |
| `/po-kit-spec:export-srs <md folder> [config]` | Word + PDF with the built-in SRS (full or classic) |
| `/po-kit-spec:export-reader <md folder> [config]` | one-page web reader |
| `/po-kit-spec:export-custom <template> [md folder]` | export into any template, with a page-by-page comparison |
| `/po-kit-spec:po-sheet` · `/po-kit-spec:po-import` | optional PO loop: Excel decisions in, new version and change list out |
| `/po-kit-spec:diff <old> <new>` | change list between two spec versions |
| `/po-kit-spec:add-language <code>` | add a document language (shipped: en, vi, fr; fr is machine-translated) |

## Safety
`skills/reverse-spec-builder/references/safety-rules.md` and `session-rules.md`: read-only by default; on production nothing is submitted; on staging/dev only invalid-data submissions and named `TEST` records within a budget; never payments, messages, settings, other people's records, exports, sign-in/sign-out, tokens or personal data in documents.

## Re-running on a new version
Recon writes `inventory.new.md`; `scripts/inventory_diff.py inventory.md inventory.new.md inventory.md <version>` keeps every id, marks vanished elements `Removed: <version>`, and lists the features to rewrite. Feature numbers never change, so `/po-kit-spec:diff` gives a real change list.

## Languages
Everything the model reads is English. The spec uses canonical English headings and labels, in any content language. The exported document language is `lang` in `config.json`; `spec_lang` is the language of the spec text.

## SRS export environment
Python 3 (python-docx, pymupdf, Pillow, openpyxl), Graphviz, LibreOffice, Liberation fonts. Check with `bash scripts/check_env.sh` (lists everything missing), install with `/po-kit-spec:setup` or `bash scripts/setup.sh` (apt on Linux, Homebrew on macOS; Python modules always go to a private venv `~/.po-kit/venv`, which the scripts switch to by themselves). Cloud sessions already have them.

## Folder map
`commands/` slash commands · `agents/` recon, writer, verifier, reviewer · `skills/reverse-spec-builder/` skill + `references/` (session-rules, drivers, coverage-rules, safety-rules, po-loop-decision, export, ... loaded on demand) · `scripts/` lint, stats, inventory check/diff, android sweep, SRS builder, PO sheet, language packs · `examples/` synthetic sample spec.

## Limits
Tested end to end on real web apps (Vietnamese) and one synthetic English spec. The `android` and `capture` drivers are documented but not yet run on a real app. Actor detection in the SRS builder is heuristic (sentence starts with the actor name); languages without capital letters get coarser results.
