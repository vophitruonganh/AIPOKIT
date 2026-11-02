# Drivers: how to look at a product (web, Android, capture)
Recon and Verify do the same work on every driver: reach each screen, list every visible element, open things read-only, record states. Only the mechanics differ. Never rely on a CSS framework, class name or URL scheme of one product; use roles, labels and visible text.

## web
- **Session**: one tab or browser context per agent; note its id and pass it on every call; never touch tabs you did not open; close only your own. With a scripted browser (Playwright etc.) use a fresh context per run and close it.
- **Navigate**: click visible links and menus; for single-page apps you may set the URL path or hash inside your own tab. Never open sign-in or sign-out routes.
- **Screen id** (inventory Screen column): the route (path + hash without ids, e.g. `/orders/:id`), else the page title path.
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
