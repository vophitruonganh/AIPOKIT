# Preflight (Phase 0, v1.8): decide everything once, then run once
Most lost time is re-running a phase because a decision came late (write rights, test data, languages) or because the setup failed half way (device off, session expired). Do all of this before the first recon call; one message to the user, one approval.

## 1. Decisions (one message)
- Target(s), purpose, environment, roles, spec + document language, storage (as before).
- **Write level** for the environment. On dev, recommend level B. Production is always level A.
  - **A read-only**: open and close forms, never save (production default).
  - **B own TEST records**: create, edit and delete records the run created itself (prefix `TEST`), fictional but realistic Vietnamese content from the test-data pack; typed values are probed for validation messages; save is allowed on those records only. Each record is logged in `source/test-data.md` and removed at the end (note what cannot be removed).
  - **C named extras**: only the items the user names (sign, close a record, publish, activate a service, add staff...). Anything with an effect outside the app (SMS, email, push, payment, e-invoice, national systems, plan or permission changes of real accounts) stays forbidden at every level.
- Forbidden list = safety-rules.md defaults + the level above.

## 2. Test-data pack (write once, `source/testdata.md`, share with every agent)
Fictional, realistic, clearly fake: person `TEST Nguyễn Văn An` (never a real person; phone `0900000001..` pattern that cannot be a real subscriber; email `test.NN@example.com`), address in a real district list, diagnosis with ICD code, drug and supplier names, prices in VND, dates in the next 7 days. One row per entity type. Agents take the next unused row so records never collide.

## 3. Technical checks (script them, fail early)
- **Browser runner** (`browser-runner.md`): run `pokit-browser.mjs doctor --url <app>` on the machine that reaches the app; if it is not Ready, run `setup-browser.sh`, let the user sign in with `login`, run `calibrate` once. When it is Ready, recon and verify go through `run` with a plan; the Chrome checks below are only for the fallback.
- Device bridge connected; one `list_tabs` call works; the target host loads (not login page) in the user's Chrome.
- Session valid for each role; token expiry unknown: ask the user to keep the tab active.
- One Chrome **window** per agent when several agents work (background tabs are throttled: timers slow down, dialogs do not close).
- localStorage key per agent (`window.__AWKEY='pokit_aw_<letter>'`).
- Route list: from the previous SRS, sitemap or sidebar; give each agent its routes and its ID prefix up front.
- Plugin checks that bit before: `style_check.py` skips inventory labels in W12; `merge_parts.py` joins split modules; `walk_to_inventory.py` keeps routes out of labels.

## 4. One pass per screen
With level B or C, recon and verify are one pass: `AW.walk` (inventory), `AW.probe` (typed values, validation messages, no submit), then save the TEST record when allowed, read the result and the list row it creates, open its detail, edit, delete. The agent writes what it saw into the walk file; the open question is answered at the moment it is asked. A separate verify phase is only for what a pass could not reach.

## 5. Pipeline per module
One agent per module (or two for 10+ features) runs walk, probe, save, write, lint, in that order, so no phase waits for another. The orchestrator only merges (`merge_parts.py`, `inventory_check.py`, `spec_lint.py`) and exports.
