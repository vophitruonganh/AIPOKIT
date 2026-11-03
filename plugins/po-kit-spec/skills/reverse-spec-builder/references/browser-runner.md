# Browser runner (headless, parallel): `scripts/browser/pokit-browser.mjs`
Use it for recon and verify of a web target whenever it can run on a machine that reaches the app (usually the user's own computer, through Remote Control or the user's terminal). It runs autowalk in a headless Chromium, many pages at once, and needs no model turn per step: the model writes a plan, the script runs it, the model reads the result files. Measured on the test app: CRUD screen 15 s, read-only screen 1.5 to 3.5 s, 4 pages in parallel with no slow-down. Fall back to the Chrome driver (drivers.md) only where it cannot run (no Node, the app needs a hardware key, a screen needs judgment).

## Setup (once per machine, about 5 minutes)
1. `bash scripts/browser/setup-browser.sh` (macOS / Linux) or `powershell -File scripts/browser/setup-browser.ps1` (Windows). It installs Node with Homebrew or winget when missing, then Playwright and Chromium into `~/.po-kit/browser` (no sudo, nothing global), then runs the doctor.
2. `node scripts/browser/pokit-browser.mjs login --url <app url>`: a window opens and **the user signs in there themselves**. The window closes by itself once signed in. The login stays in `~/.po-kit/profiles/<host>` on that machine only (like a browser profile; never copy it, never print its contents). `forget --url` deletes it at the end of the project.
3. `node scripts/browser/pokit-browser.mjs calibrate --url <a read-only list page>`: finds how many pages this machine and this app take in parallel (stops when a page gets 60% slower or an error shows) and saves it. `run` uses it.
4. `node scripts/browser/pokit-browser.mjs doctor --url <app url>`: every line must be OK before a run. It prints the exact fix command for each missing item.

## Progress to the user (required)
The user cannot see a terminal the agent runs. Every step longer than about 20 seconds must show progress:
- Start `setup-browser.sh`, `login`, `calibrate` and `run` in the background, never as one silent blocking call.
- Every 20 to 30 seconds read the progress, and pass it to the user in one short line (or the progress checklist of the host) when it changed:
  - setup: `cat ~/.po-kit/browser/setup.status` (step n/5 and its name; the script also prints `[n/5] ... ok (N s)`, and `... N s` every 5 s during downloads);
  - login, calibrate, run: `node scripts/browser/pokit-browser.mjs status` (state, done/total, percent, seconds left, last route), or `status --watch` in a terminal the user can see.
- Before a step that needs the user (sign in), say so first, in one line, with what they will see ("a browser window opens, sign in there").
- At the end, give the result in one line (time, jobs, warnings) before the details.

## Plan (the model writes it, one per module or per run)
```json
{"base": "https://app.example.com", "loginPattern": "/login|/sign-?in|/auth",
 "apiHosts": ["api.example.com"], "block": ["tracker.example"], "settleMs": 600,
 "jobs": [
  {"route": "/pharmacy/settings/medicine/suppliers", "feature": "5.9", "mode": "walk", "walk": {"open": ["Thêm mới"]}},
  {"route": "/pharmacy/settings/medicine/suppliers", "feature": "5.9", "mode": "crud", "crud": {
    "name": "TEST Công ty Dược Hòa Bình Mẫu", "open": "Thêm mới", "save": "Lưu", "view": "Xem", "del": "Xóa", "confirm": "Xóa",
    "fill": {"Nhà cung cấp": "TEST Công ty Dược Hòa Bình Mẫu", "Mã số thuế": "0100000001", "Số điện thoại": "0900000001", "Email": "test.ncc01@example.com"},
    "edit": {"Người liên hệ": "TEST Liên hệ"},
    "checks": [{"Email": "abc@"}, {"Số điện thoại": "090123"}, {"Mã số thuế": "abc-12"}, {"Nhà cung cấp": "   "}]}}]}
```
- `walk` jobs are read-only: the runner aborts every PUT/PATCH/DELETE and every POST whose path looks like a change, and logs it (`note|blocked request ...`). Use them for all screens.
- `crud` jobs only with write level B or C (preflight.md), only names starting with `TEST`, only fictional data from the test-data pack. `checks` press Save with one bad value each and record the message; a value the app accepts creates a TEST row, which is deleted at once and reported as `accepted`. Jobs on the same route never run at the same time.
- On every job, requests whose path looks like send / notify / pay / sign / e-invoice / export / print are aborted. Analytics hosts are blocked (faster, and the run does not pollute the product's analytics).

## Run
`node scripts/browser/pokit-browser.mjs run plan.json --out source/browser-out` (`--workers N` to override, `--only <text>` for some routes, `--fresh` to redo finished jobs, `--headed` to watch). One file per job in the walk format (feed it to `walk_to_inventory.py`), plus `summary.json` (time per job, warnings). Finished jobs are skipped on the next run, so a stopped run continues where it stopped.
- Exit 3 / `LOGIN_NEEDED`: the login expired. Ask the user to run `login` again, then run the same command.
- `WARN ... TEST row left over`: clean that row by hand (or a crud job with only `del`) and log it in `source/test-data.md`.
- Screens where the result shows `note|error`, `not found` or a flow the plan could not express (wizard, conditional fields, file upload): finish them with the Chrome driver.

## Reading the output (token rule)
Read `summary.json` first, then only the files you need; `crud|check|...` and `crud|save.*` lines are the validation facts for the spec, `apishape|...` lines give the data model (keys and types, enum values only, never record values).
