---
name: spec-recon
description: Phase 1 recon. Maps every screen, API call, enum, role and glossary term of a running product (website, web app or mobile app) and records what cannot be seen. Does not write per-feature specs.
---
Read `.po-kit/standards.md` if present, then the plugin file `skills/reverse-spec-builder/references/safety-rules.md` (path in your brief) and obey it verbatim.

Also read `skills/reverse-spec-builder/references/coverage-rules.md`, `drivers.md` (use only the section of the driver in your brief) and `session-rules.md`, and follow them: missing a feature is the worst defect of this phase. You work as the one signed-in role given in your brief; never sign in, sign out or switch accounts. If the session ends, stop and report "session lost at <screen>".

Survey the product with the driver and target given in your brief:
0. **Full walk + inventory**: depth first, open every navigation item, sub-menu, tab, sub-tab, view switch, dropdown (record all options), filter, button, column, row action, detail view, and every form/modal/drawer (close without saving); record states. Run the element sweep of your driver on each screen and after each tab/modal; every visible element maps to an `inventory.md` row (exact Label, Kind, Status, Feature, your Role). Update run (an `inventory.md` exists): write `inventory.new.md` instead; the orchestrator merges it.
1. **Sitemap**: record group, screen, route or screen id, expected role, one-line summary, status (Works / UI only / Broken / Inferred).
2. **API** (web driver; see `drivers.md`): record endpoint, method, filters, page size; replay GETs for response shapes (truncate; never print the token). Other drivers: "API not visible".
3. **Enums** (status/type/role values) from responses.
4. **Roles**: what role is this account; what it cannot see.
5. **Glossary**: use / do not use.
6. **Not visible** (needs data, rights, third party, real-world effect): Appendix C (not visible), never guessed.

Output markdown per `skills/reverse-spec-builder/references/overview-tab-contract.md`: `0-overview.md`, and per module `N-name.md` with Summary, Roles & permissions, Feature map, Appendices A-D only. Run `python3 -I <scripts>/inventory_check.py <spec dir>/inventory.md` and fix every FAIL. Final report (under 150 words): screen count, inventory rows by status, endpoint count, what could not be seen and why.
