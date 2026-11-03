# Drivers: how to look at a product (web, Android, capture)
Recon and Verify do the same work on every driver: reach each screen, list every visible element, open things read-only, record states. Only the mechanics differ. Never rely on a CSS framework, class name or URL scheme of one product; use roles, labels and visible text.

## web
**First choice when it can run on a machine that reaches the app: the headless browser runner (`browser-runner.md`), many pages in parallel and no model turn per step.** The Chrome driver below is the fallback and the tool for screens that need judgment.

- **Session**: one tab or browser context per agent; note its id and pass it on every call; never touch tabs you did not open; close only your own. With a scripted browser (Playwright etc.) use a fresh context per run and close it.
- **Navigate**: click visible links and menus; for single-page apps you may set the URL path or hash inside your own tab. Never open sign-in or sign-out routes.
- **Screen id** (inventory Screen column): the route (path + hash without ids, e.g. `/orders/:id`), else the page title path.
- **Autowalk (default, v1.7)**: one call per screen instead of one per tab, dropdown and modal. Paste `scripts/autowalk.js` once per tab (it also keeps a copy in the page's localStorage: set `window.__AWKEY='pokit_aw_<your letter>'` before pasting, because localStorage is shared by every tab and agent of the origin; after a full reload run `eval(localStorage.pokit_aw_<letter>)`), move with `AW.go('/route')`, start `AW.walk({open: ['<button that opens a form>', ...]})` and read `AW.out()` in the next call (tools do not await promises; repeat while it says `running`). It sweeps the screen, opens every tab, dropdown and the first row menu to read their options, opens the named buttons, sweeps each dialog or page and closes it, and lists the product's API calls. It never clicks a label that matches `AW.DANGER` (save, delete, pay, send, sign, export, confirm...) or a switch. Save the output with `## <route> | <feature N.M>` headers, prefix a line with `-` to drop it, add `|<status>` to override, then run `python3 -I <scripts>/walk_to_inventory.py <walk files> --prefix <ID prefix> --role <role> --out <inventory file>`: rows, kinds and default statuses are generated, so never type inventory rows by hand. Where the write level allows typing (preflight.md level B/C), run `AW.probe()` inside an open form: it types a battery of values (empty, 300 chars, negative, spaces, markup, phone, bad email) into each text field without submitting and records the validation text. Open by hand only what the walk cannot (row detail pages, a second level of dialogs, drag and drop), with the element sweep below. Background tabs are throttled by Chrome (timers slow down, dialogs may not close): bring your tab to the front with switch_to_tab before a walk, or pass shorter waits. At the end remove your own key only (`localStorage.removeItem('pokit_aw_<letter>')`).
- **Element sweep**: run on each screen and after opening each tab, menu, modal or drawer:
```js
(() => { const sel = 'a[href],button,input,select,textarea,summary,[role=button],[role=link],[role=tab],[role=menuitem],[role=option],[role=switch],[role=checkbox],[role=radio],[role=combobox],[role=listbox],[role=slider],[role=treeitem],[aria-haspopup],[aria-expanded],[tabindex]:not([tabindex="-1"]),th,[role=columnheader]';
  const seen = new Set(); return [...document.querySelectorAll(sel)].filter(e => e.offsetParent !== null || e.getClientRects().length).map(e => {
    const t = (e.getAttribute('aria-label') || e.title || e.placeholder || e.innerText || e.value || '').trim().replace(/\s+/g, ' ').slice(0, 60);
    const k = e.tagName.toLowerCase() + (e.getAttribute('role') ? '[' + e.getAttribute('role') + ']' : '') + '|' + t;
    if (seen.has(k)) return null; seen.add(k); return k; }).filter(Boolean); })()
```
  Elements inside shadow DOM or iframes: repeat the sweep inside them if the tool allows, else read the screen text and mark what you could not list.
- **API**: before the walk run `performance.clearResourceTimings(); performance.setResourceTimingBufferSize(2000)`; after each screen read `performance.getEntriesByType('resource')` and keep calls of type fetch/xmlhttprequest to the product's own hosts; record method, path pattern, query parameters. Replay only GET calls, never print tokens, cookies or headers.
- **Tool errors**: a script call that returns nothing or "browser not running": retry up to 3 times, then read the page text instead and mark what could not be tried as `Cannot verify: tool error`.

## android
- **Session**: one device or emulator per role (or one Android user profile per role). Check with `adb devices`.
- **Screen id**: the current activity plus the screen title (`adb shell dumpsys activity activities | grep -m1 mResumedActivity`).
- **Element sweep**: `adb exec-out uiautomator dump /dev/tty` then `python3 -I <scripts>/android_sweep.py <dump.xml>` lists clickable, checkable, scrollable and text-input elements with their text, content description and bounds.
- **Navigate**: `adb shell input tap <x> <y>` on the bounds centre of a listed element; `adb shell input keyevent KEYCODE_BACK` to close; scroll with `input swipe`. Dropdowns and dialogs: dump again after opening.
- **API**: not visible without a proxy; Appendix A says "not visible (mobile app)". Do not install certificates or proxies on the user's device.
- Never type into sign-in screens, never clear app data, never uninstall.

## capture
- The user gives screenshots or screen recordings, one folder per role, file names that say the screen (`03-orders-filter-open.png`).
- **Screen id**: the file name without number. **Element sweep**: read each image; list every visible control with its exact text; a control whose options are not shown is `Needs data: options not captured`.
- Status `Explored` is not possible: use `Opened read-only` for what is visible on an image and `Needs data` for anything that needs an action. Source label: `Observed <date> (screenshot)`.
- Ask once, at the end of Recon, for missing captures as one list (screen and what to open); then continue with what you have.
