# Coverage rules: walk every feature, miss nothing
A spec is only as accurate as the crawl behind it. Recon must reach **every** interactive element of the product the account can see, with whatever driver is used (`drivers.md`), down to the smallest sub-feature inside a big feature, and record it in one inventory. A feature that is not in the inventory does not exist for the spec, so a gap here becomes a gap in the SRS.

## What "every feature" means (walk in this order, depth first)
For each top-level navigation item (sidebar, top bar, bottom tab bar, drawer), then each sub-menu, then each screen:
1. **Navigation**: sidebar or bottom-bar groups and items, sub-menus, breadcrumbs, header elements (global search, notifications, user menu, language switch, help), footer links, links that open other routes.
2. **Tabs**: every tab, every sub-tab inside a tab, every left sub-menu inside a screen, every step of a wizard/stepper.
3. **View switches**: list/grid/calendar, day/week/month or any segmented control, collapse/expand, chart type toggles.
4. **Filters and search**: every input, select, date range, checkbox; open every dropdown and record **all options**; note defaults and whether the filter applies on change or on a button.
5. **Buttons and links**: every button and icon button (tooltips count as labels), including those inside cards, table headers, toolbars and empty states.
6. **Tables and lists**: every column, sortable columns, column chooser, row selection, bulk actions bar, pagination, page-size selector, total counter, expandable rows.
7. **Row actions**: hover icons, "..." menus, action column links; open each detail view read-only.
8. **Forms, modals, drawers, pop-overs**: open each create/edit form, modal and drawer, record every field, section, tab, radio/checkbox option, helper text and button, then close it with its close or cancel control, Esc or Back **without saving**. Opening is a read; saving is not.
9. **States**: empty, loading, error, disabled, read-only, permission-hidden, maintenance, very long text.
10. **Charts and widgets**: every widget, legend item, tooltip, drill-down.

Repeat the walk for **each role** you have an account for. Elements one role sees and another does not go in the inventory with the role column filled.

## Safety and coverage together
- `safety-rules.md` still wins. Coverage never justifies a forbidden action.
- Do not forbid *opening* forms in the brief by default: forbid *saving, submitting, deleting, exporting, toggling, sending*. A brief that forbids clicking create or edit buttons hides every field of those forms and turns the field tables into Unverified. If the brief does forbid opening, say in Phase 0 how much coverage that will cost.
- If a click might change data and you are not sure, do not click: mark the row `Safety-blocked: <rule>`.

## Element sweep (catch what the eye misses)
On each screen and after opening each tab, menu or modal, run the sweep of your driver (`drivers.md`: JS snippet for web, `android_sweep.py` for android, image reading for capture) and compare it with your inventory rows for that screen; every visible interactive element must map to a row.
Never put typed values, tokens or personal data from the sweep into files.

## The inventory (`inventory.md`, required output of Phase 1)
One markdown table, one row per element, next to the `md/` folder:

| ID | Screen | Path | Kind | Label | Role | Status | Feature |
| --- | --- | --- | --- | --- | --- | --- | --- |
| INV-001 | `/orders` | Orders > Filters | filter | Status | Manager | Explored | 2.1 |
| INV-002 | `/orders` | Orders > New order | modal | New order | Manager | Opened read-only | 2.2 |
| INV-003 | `/orders` | Orders > Export | button | Export | Manager | Safety-blocked: export | 2.1 |

- **Kind**: one of `menu, submenu, tab, subtab, view, filter, search, button, link, dropdown, option-list, column, row-action, bulk-action, pagination, modal, drawer, form-field, detail, widget, state, header, footer`.
- **Label**: the exact visible text (or tooltip/aria-label); the writer must reuse it word for word.
- **Screen**: route for web, activity + title for android, capture file name for capture (`drivers.md`).
- **Status**: `Explored` (seen and used) / `Opened read-only` (opened and closed without saving) / `Safety-blocked: <rule>` / `Needs data` / `Needs role: <role>` / `Broken: <what>` / `Removed: <version>` (update runs only, set by `inventory_diff.py`). `Not explored` is never allowed at the end of Phase 1.
- **Feature**: the `N.M` feature that must describe it, or `global` for shell elements (header, footer, sidebar) described in the overview.

## Update runs (the product changed)
Never renumber. Write the new walk to `inventory.new.md`, then `python3 -I <scripts>/inventory_diff.py inventory.md inventory.new.md inventory.md <version>`: matched rows keep their ID and Feature, new rows get the next ID, rows gone from the product become `Removed: <version>`. New features take the next free `N.M` of their module (new modules the next free N). Only the features the script lists go back to Phase 2; `spec_diff.py` then gives a meaningful change list.

## Gates (run `scripts/inventory_check.py`)
- Phase 1: `python3 -I <scripts>/inventory_check.py <spec dir>/inventory.md` passes: every row has a valid status and feature; no `Not explored`; no duplicate ID.
- Phase 2 and 4: `python3 -I <scripts>/inventory_check.py <spec dir>/inventory.md --md <spec dir>/md` passes: every `N.M` feature has inventory rows, every row points to an existing feature, and every row's Label appears in its feature section (FAIL), so nothing seen on the app is missing from the spec.
- `Needs data` and `Needs role` rows become Open questions in their feature with owner and reason, and are retried in Phase 4.
