// po-kit autowalk: one call per screen instead of one per tab / dropdown / modal.
// Install once per page load (paste this file), then call AW.walk({...}) and read AW.out() in the next call
// (browser tools do not await promises). SPA navigation by AW.go('/path') keeps AW installed.
// Never clicks anything whose label matches AW.DANGER, never toggles switches or checkboxes, never submits.
// Output is the walk format read by walk_to_inventory.py: '## <screen>' then 'kind|label' lines,
// '### <path>' for what opened inside the screen (tab, popup, dialog), '!status' suffix for read-only opens.
window.__AWSRC = (function AWFACTORY() {
  const DANGER = /lưu|xoá|xóa|thu tiền|đã thu|gửi|ký số|^ký|xuất|tải về|tải xuống|^in\b|in phiếu|đăng xuất|nâng cấp|thanh toán|hoàn tất|xác nhận|kích hoạt|phê duyệt|duyệt|từ chối|^bán|gọi|nhận thông báo|đồng ý|áp dụng|cập nhật|phát hành|huỷ|hủy lịch|bắt đầu|kết thúc|delete|save|submit|logout|sign out|confirm|pay|send|export|download|print|approve|reject|upgrade|apply/i;
  const CLOSE = /^(hủy|huỷ|đóng|quay lại|trở lại|bỏ qua|cancel|close|back)$/i;
  // Timers from a Web Worker are not throttled in background tabs (setTimeout in a hidden tab can slow to 1/s or 1/min).
  let WK = null, WN = 0; const WQ = {};
  try { WK = new Worker(URL.createObjectURL(new Blob(['onmessage=e=>setTimeout(()=>postMessage(e.data[0]),e.data[1])'], { type: 'text/javascript' }))); WK.onmessage = e => { const f = WQ[e.data]; delete WQ[e.data]; f && f(); }; } catch (e) { WK = null; }
  const wait = ms => new Promise(r => { if (WK) { const id = ++WN; WQ[id] = r; WK.postMessage([id, ms]); } else setTimeout(r, ms); });
  const vis = e => e && (e.offsetParent !== null || e.getClientRects().length > 0);
  const txt = e => (e.getAttribute('aria-label') || e.innerText || e.value || e.title || '').trim().replace(/\s+/g, ' ').slice(0, 70);
  const labelOf = e => {
    let l = e.id && document.querySelector(`label[for="${CSS.escape(e.id)}"]`);
    if (!l) l = e.closest('label') || e.closest('[class*=item],[class*=field],div')?.querySelector('label');
    return ((l && l.innerText) || e.getAttribute('aria-label') || e.placeholder || e.name || '').trim().replace(/\s+/g, ' ').slice(0, 60);
  };
  const SEL = 'h1,h2,h3,h4,a[href],button,input,select,textarea,[role=button],[role=tab],[role=switch],[role=checkbox],[role=radio],[role=combobox],[aria-haspopup],th,[role=columnheader]';
  function sweep(root) {
    const out = [], seen = new Set();
    for (const e of (root || document).querySelectorAll(SEL)) {
      if (!vis(e) || e.closest('[data-aw-skip]') || (e.closest('th,[role=columnheader]') && e !== e.closest('th,[role=columnheader]'))) continue;
      const tag = e.tagName.toLowerCase(), role = e.getAttribute('role'); let kind, label;
      if (/^h\d$/.test(tag)) { kind = 'heading'; label = txt(e); }
      else if (tag === 'th' || role === 'columnheader') { kind = 'column'; label = txt(e); }
      else if (tag === 'select') { kind = 'dropdown'; label = labelOf(e) + ' = ' + [...e.options].map(o => o.text.trim()).join(' / '); }
      else if (tag === 'input' || tag === 'textarea') {
        const t = (e.type || 'text').toLowerCase(); if (t === 'hidden') continue;
        kind = t === 'checkbox' ? 'checkbox' : t === 'radio' ? 'radio' : t === 'file' ? 'upload' : tag === 'textarea' ? 'textarea' : 'input';
        label = labelOf(e) + (e.placeholder && labelOf(e) !== e.placeholder ? ` [${e.placeholder}]` : '') + (e.required || e.getAttribute('aria-required') === 'true' ? ' *' : '') + (t !== 'text' && kind === 'input' ? ` (${t})` : '') + (e.disabled ? ' (disabled)' : '');
      }
      else if (role === 'tab') { kind = 'tab'; label = txt(e); }
      else if (role === 'switch') { kind = 'toggle'; label = labelOf(e) || txt(e); }
      else if (role === 'checkbox' || role === 'radio') { kind = role; label = labelOf(e) || txt(e); }
      else if (role === 'combobox' || e.getAttribute('aria-haspopup')) { kind = 'dropdown'; label = labelOf(e) || txt(e); }
      else if (tag === 'a') { kind = 'link'; label = txt(e) + ' -> ' + (e.getAttribute('href') || ''); }
      else { kind = 'button'; label = txt(e) || (e.querySelector('svg') ? '(icon ' + (e.className.baseVal || e.className || '').toString().split(' ').find(c => /icon|lucide/.test(c)) + ')' : ''); }
      if (!label) continue;
      const k = kind + '|' + label; if (seen.has(k)) continue; seen.add(k); out.push(k);
    }
    return out;
  }
  // Radix/shadcn menus open on pointerdown, not on click: send the full pointer sequence.
  const press = e => { const o = { bubbles: true, cancelable: true, button: 0, pointerType: 'mouse', isPrimary: true }; e.dispatchEvent(new PointerEvent('pointerdown', o)); e.dispatchEvent(new MouseEvent('mousedown', o)); e.dispatchEvent(new PointerEvent('pointerup', o)); e.dispatchEvent(new MouseEvent('mouseup', o)); e.click(); };
  const dialogs = () => [...document.querySelectorAll('[role=dialog],[role=alertdialog],[data-state=open][role=menu],[role=listbox]')].filter(vis);
  async function closeAll() {
    for (let i = 0; i < 3 && dialogs().length; i++) {
      document.activeElement && document.activeElement.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); await wait(250);
      const d = dialogs()[0]; if (!d) break;
      const c = [...d.querySelectorAll('button')].find(b => CLOSE.test(txt(b)) || /close|đóng/i.test(b.getAttribute('aria-label') || ''));
      if (c) { c.click(); await wait(300); }
    }
  }
  async function options(trigger) {
    if (DANGER.test(txt(trigger))) return null;
    press(trigger); await wait(350);
    const box = dialogs().pop(); let opts = [];
    if (box) opts = [...box.querySelectorAll('[role=option],[role=menuitem],[role=menuitemradio],[role=menuitemcheckbox],li,button')].filter(vis).map(txt).filter(Boolean);
    await closeAll();
    opts = [...new Set(opts)];
    if (opts.length > 5 && opts.every((x, i) => /^\d+$/.test(x) && (i === 0 || +x === +opts[i - 1] + 1))) return [opts[0] + '..' + opts[opts.length - 1]];
    return opts.slice(0, 60);
  }
  async function popups(root, lines, depth) {
    const trig = [...root.querySelectorAll('[aria-haspopup],[role=combobox]')].filter(e => vis(e) && !e.closest('th,[role=columnheader]'));
    const done = new Set();
    for (const t of trig) {
      const inRow = t.closest('tbody tr'); const key = (inRow ? 'row:' : '') + (labelOf(t) || txt(t));
      if (done.has(key) || (inRow && [...done].some(k => k.startsWith('row:')) && key.startsWith('row:'))) continue;
      done.add(key);
      const o = await options(t); if (!o || !o.length) continue;
      lines.push(`### ${inRow ? 'Row menu' : 'Dropdown'}: ${key.replace(/^row:/, '')}`, ...o.map(x => 'option|' + x));
    }
  }
  async function walk(opt = {}) {
    window.__AWR = null; const t0 = Date.now(); const lines = [`## ${location.pathname}`];
    try {
      performance.setResourceTimingBufferSize(3000);
      const main = document.querySelector('main') || document.body;
      lines.push(...sweep(main));
      await popups(main, lines);
      window.__AWSTEP = 'walk: screen elements and dropdowns';
      for (const tab of [...main.querySelectorAll('[role=tab]')].filter(vis)) {
        window.__AWSTEP = 'walk: tab ' + txt(tab);
        if (tab.getAttribute('aria-selected') === 'true' || DANGER.test(txt(tab))) continue;
        const before = new Set(sweep(main)); tab.click(); await wait(opt.tabWait || 600);
        const add = sweep(main).filter(x => !before.has(x)); lines.push(`### Tab: ${txt(tab)}`, ...add);
        await popups(main, lines);
      }
      for (const name of opt.open || []) {
        window.__AWSTEP = 'walk: open ' + name;
        const b = [...document.querySelectorAll('button,a,[role=button],[role=menuitem]')].filter(vis).find(e => txt(e) === name || txt(e).startsWith(name));
        if (!b) { lines.push(`### Open: ${name}`, 'note|not found'); continue; }
        if (DANGER.test(name)) { lines.push(`### Open: ${name}`, 'note|blocked by AW.DANGER'); continue; }
        const url = location.href; b.click(); await wait(opt.openWait || 800);
        const d = dialogs().pop();
        if (d) { lines.push(`### Dialog: ${name} !Opened read-only`, ...sweep(d)); await popups(d, lines); await closeAll(); }
        else if (location.href !== url) { lines.push(`### Page: ${name} -> ${location.pathname} !Opened read-only`, ...sweep(document.querySelector('main') || document.body)); history.back(); await wait(800); }
        else lines.push(`### Open: ${name}`, 'note|nothing opened');
      }
      const hosts = opt.hosts || [location.host];
      const api = [...new Set(performance.getEntriesByType('resource').filter(r => /fetch|xmlhttprequest/.test(r.initiatorType) && r.startTime >= (window.__AWT || 0) && hosts.some(h => r.name.includes(h)) && !/[?&]_rsc=|cdn-cgi|collect|analytics/.test(r.name)).map(r => { const u = new URL(r.name); return u.host + u.pathname.replace(/[0-9a-f]{24}|\b\d{3,}\b/g, ':id') + (u.search ? '?' + [...u.searchParams.keys()].join('&') : ''); }))];
      lines.push('### API', ...api.map(a => 'api|' + a));
    } catch (e) { lines.push('note|error ' + e.message); }
    lines.push(`note|walk ${Date.now() - t0} ms`);
    return (window.__AWR = lines.join('\n'));
  }

  // AW.probe({root: <selector of the open dialog/form, default last dialog or main>, values: {...}}) : types a battery of values into each text field
  // (native setter + input/change/blur, never submits) and records the validation text that appears. Read the result with AW.out().
  const BATTERY = [['empty', ''], ['long', 'A'.repeat(300)], ['negative', '-5'], ['space', '   '], ['special', '<b>x</b> & "q" \'s\''], ['number', '0912345678'], ['email', 'abc@']];
  function setv(el, v) { const p = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype; Object.getOwnPropertyDescriptor(p, 'value').set.call(el, v); el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); el.dispatchEvent(new Event('blur', { bubbles: true })); el.dispatchEvent(new FocusEvent('focusout', { bubbles: true })); }
  const msgs = root => [...root.querySelectorAll('[role=alert],[class*=error],[class*=invalid],[class*=destructive],[class*=helper],[aria-invalid=true] ~ *,p[id$=message]')].filter(vis).map(e => e.innerText.trim().replace(/\s+/g, ' ')).filter(x => x && x.length < 160);
  async function probe(opt = {}) {
    window.__AWR = null; const lines = ['### Probe']; const root = opt.root ? document.querySelector(opt.root) : (dialogs().pop() || document.querySelector('main') || document.body);
    try {
      const fields = [...root.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=file]):not([type=password]),textarea')].filter(e => vis(e) && !e.disabled && !e.readOnly);
      for (const f of fields) {
        const lab = labelOf(f) || f.name || f.placeholder || '(no label)'; const seen = new Set();
        for (const [name, v] of BATTERY) {
          if (name === 'number' && (f.type === 'text' && !/phone|điện thoại|số/i.test(lab))) continue;
          if (name === 'email' && !/email|mail/i.test(lab)) continue;
          const before = f.value; setv(f, v); await wait(opt.wait || 120);
          const m = [...new Set(msgs(root))].join(' / '); const shown = f.value.length > 40 ? f.value.length + ' chars' : f.value;
          const key = name + '|' + m; if (seen.has(key)) continue; seen.add(key);
          if (!m && f.value === v && !opt.all) { setv(f, before); continue; }   // accepted as typed, no message: nothing to report
          lines.push(`probe|${lab}|${name}=${JSON.stringify(v.length > 12 ? v.length + ' chars' : v)}|kept=${JSON.stringify(shown)}|msg=${m || '(none)'}`);
          setv(f, before);
        }
      }
    } catch (e) { lines.push('note|error ' + e.message); }
    return (window.__AWR = lines.join('\n'));
  }

  // AW.api(): structure of the product's own API responses seen since install (keys and types, enum-like values only).
  // Values are never kept, except short values of keys named like status/type/state/kind/role/method/unit (enums). Tokens and headers are never read.
  const SHAPES = window.__AWSHAPES = window.__AWSHAPES || {};
  const ENUMK = /status|type|state|kind|role|method|unit|gender|level|mode|category|scope/i;
  function shape(v, d, enums, k) {
    if (Array.isArray(v)) return v.length ? '[' + shape(v[0], d, enums, k) + ']' : '[]';
    if (v && typeof v === 'object') { if (d > 2) return '{…}'; return '{' + Object.keys(v).slice(0, 40).map(x => x + ':' + shape(v[x], d + 1, enums, x)).join(',') + '}'; }
    if (typeof v === 'string' && k && ENUMK.test(k) && v.length <= 30) (enums[k] = enums[k] || new Set()).add(v);
    return v === null ? 'null' : typeof v;
  }
  function record(method, url, status, body) {
    try {
      const u = new URL(url, location.href); if (u.host !== location.host && !(window.__AWHOSTS || []).some(h => u.host.includes(h))) return;
      if (/[?&]_rsc=|websocket|token|auth\/(login|refresh)/i.test(u.href)) return;
      const key = method + ' ' + u.pathname.replace(/\/([0-9a-f]{24}|\d+)(?=\/|$)/g, '/:id'); const e = SHAPES[key] = SHAPES[key] || { status: new Set(), enums: {}, shape: '' };
      e.status.add(status); const j = JSON.parse(body); const en = {}; e.shape = shape(j, 0, en);
      // list total for crud counts: only from the list API of this screen (path ends with the last route segment, has a records array)
      const seg = location.pathname.split('/').filter(Boolean).pop() || '';
      if (method === 'GET' && j && j.result && typeof j.result.total === 'number' && seg && u.pathname.endsWith('/' + seg) && Object.values(j.result).some(Array.isArray)) window.__AWTOTAL = j.result.total;
      for (const k in en) { e.enums[k] = e.enums[k] || []; for (const x of en[k]) if (!e.enums[k].includes(x) && e.enums[k].length < 12) e.enums[k].push(x); }
    } catch (e) {}
  }
  if (!window.__AWNET) {
    window.__AWNET = 1; const of = window.fetch;
    window.fetch = async function (i, o) { const r = await of.apply(this, arguments); try { const c = r.clone(); c.text().then(t => record((o && o.method) || (i && i.method) || 'GET', typeof i === 'string' ? i : i.url, r.status, t)); } catch (e) {} return r; };
    const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function (m, u) { this.__aw = [m, u]; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.send = function () { this.addEventListener('load', () => { try { record(this.__aw[0], this.__aw[1], this.status, this.responseText); } catch (e) {} }); return os.apply(this, arguments); };
  }
  // Many apps keep their own reference to fetch from before the hook, so the hook misses their calls.
  // A PerformanceObserver still sees every request URL; api() then replays the GET ones once to read the shape.
  const URLS = window.__AWURLS = window.__AWURLS || new Set();
  const NOREPLAY = /send|sms|otp|notif|pay|export|download|print|sign|logout|delete|remove|create|update|approve|cancel|confirm|zalo|mail/i;
  if (!window.__AWPO) { window.__AWPO = 1; try { performance.setResourceTimingBufferSize(5000); new PerformanceObserver(l => { for (const r of l.getEntries()) if (/fetch|xmlhttprequest/.test(r.initiatorType)) { try { const u = new URL(r.name); if (u.host === location.host && /\/api\//.test(u.pathname)) URLS.add(u.pathname + u.search); } catch (e) {} } }).observe({ type: 'resource', buffered: true }); } catch (e) {} }
  async function api(opt = {}) {
    window.__AWR = null;
    try {
      const done = new Set(Object.keys(SHAPES).map(k => k.split(' ')[1]));
      for (const u of URLS) {
        const pat = u.split('?')[0].replace(/[0-9a-f]{24}|\b\d{3,}\b/g, ':id');
        if (done.has(pat) || NOREPLAY.test(pat) || opt.replay === false) continue; done.add(pat);
        try { const r = await fetch(u, { credentials: 'include' }); record('GET', u, r.status, await r.text()); } catch (e) {}
      }
    } catch (e) {}
    window.__AWR = Object.entries(SHAPES).map(([k, e]) => `apishape|${k}|${[...e.status].join(',')}|${e.shape.slice(0, 600)}` + (Object.keys(e.enums).length ? '|enums ' + JSON.stringify(e.enums) : '')).join('\n') || '(no api)';
    return window.__AWR;
  }

  // AW.crud(spec): one call for the whole create / validate / edit / delete scenario of a list screen (write level B only).
  // spec = { name: 'TEST ...', open: 'Thêm mới', fill: {label: value}, save: 'Lưu', rowMenu: true, view: 'Xem', edit: {label: value},
  //          del: 'Xóa', confirm: 'Xóa', empty: true, dup: true, probe: true }
  // Guard: refuses unless spec.name starts with TEST; edits and deletes only the table row whose text contains spec.name.
  const toasts = [];
  const tobs = new MutationObserver(ms => { for (const m of ms) for (const n of m.addedNodes) { if (n.nodeType !== 1) continue; const t = (n.innerText || '').trim().replace(/\s+/g, ' '); if (t && t.length < 200 && (n.matches('[data-sonner-toast],[role=status],[role=alert],li[data-type]') || n.querySelector?.('[data-sonner-toast],[role=status]'))) toasts.push(t); } });
  const obs = () => tobs.observe(document.body || document.documentElement, { childList: true, subtree: true });
  if (document.body) obs(); else document.addEventListener('DOMContentLoaded', obs);
  const EMPTY = /không có dữ liệu|chưa có dữ liệu|no data|no results|no records|empty/i;
  const dataRows = () => [...document.querySelectorAll('tbody tr')].filter(r => vis(r) && !(r.cells.length <= 1 || EMPTY.test(r.innerText)));
  const count = () => { const m = (document.body.innerText.match(/Tổng\s+([\d.]+)\s+kết quả|Total\s+([\d,]+)/i) || []); const ui = m[1] || m[2]; return (ui != null ? 'footer ' + ui : 'rows ' + dataRows().length) + (window.__AWTOTAL != null ? ', api ' + window.__AWTOTAL : ''); };
  const btnIn = (root, name) => [...root.querySelectorAll('button,[role=button],[role=menuitem],a')].filter(vis).find(b => txt(b) === name || txt(b).startsWith(name));
  const lastDialog = () => dialogs().filter(d => d.matches('[role=dialog],[role=alertdialog]')).pop();
  // wait until something happens (toast, field message, dialog closed) instead of a fixed sleep; a short extra wait catches late toasts
  async function settle(d, max = 4000) { const t = Date.now(); while (Date.now() - t < max) { await wait(120); if (toasts.length || (d && (!d.isConnected || !vis(d) || msgs(d).length))) break; } await wait(250); }
  const takeToasts = () => { const t = [...new Set(toasts)].join(' / '); toasts.length = 0; return t || '(none)'; };
  function fill(root, map) {
    const done = [];
    for (const [lab, v] of Object.entries(map || {})) {
      const f = [...root.querySelectorAll('input,textarea')].filter(e => vis(e) && !e.disabled).find(e => labelOf(e).replace(/\s*\*$/, '').trim().startsWith(lab));
      if (f) { setv(f, v); done.push(lab); } else done.push(lab + ' (not found)');
    }
    return done.join(', ');
  }
  async function until(f, max = 2500) { const t = Date.now(); let v; while (!(v = f()) && Date.now() - t < max) await wait(60); return v; }
  async function openForm(name) { const b = btnIn(document, name); if (!b) return null; const n = dialogs().length; b.click(); await until(() => dialogs().length > n); await wait(150); return lastDialog() || document.querySelector('main'); }
  async function closeForm() { const d = lastDialog(); if (!d) return; const c = [...d.querySelectorAll('button')].find(b => CLOSE.test(txt(b)) || /close|đóng/i.test(b.getAttribute('aria-label') || '')); if (c) c.click(); else document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); await until(() => !d.isConnected || !vis(d), 1500); await wait(100); }
  const rowOf = name => [...document.querySelectorAll('tbody tr')].find(r => vis(r) && r.innerText.includes(name));
  async function rowAction(name, action) {
    const r = rowOf(name); if (!r) return 'row not found';
    const t = r.querySelector('[aria-haspopup],button'); if (!t) return 'no row menu';
    press(t); const it = await until(() => btnIn(document, action), 1500); if (!it) { await closeAll(); return 'action not found'; }
    const n = dialogs().filter(d => d.matches('[role=dialog],[role=alertdialog]')).length; it.click(); await until(() => dialogs().filter(d => d.matches('[role=dialog],[role=alertdialog]')).length > n, 2000); await wait(150); return 'ok';
  }
  // AW.crud(spec): create / duplicate / view+edit / delete one TEST record, with field checks that press Save.
  // spec: {name:'TEST …', open:'Thêm mới', fill:{label:value}, save:'Lưu', view:'Xem', edit:{label:value}, del:'Xóa', confirm:'Xóa',
  //        checks:[{label:badValue}, …], empty, probe, dup (false to skip)}. Refuses unless name starts with TEST.
  // A check that the app accepts creates a TEST row; it is deleted at once and reported as 'accepted'.
  async function crud(s) {
    window.__AWR = null; const L = ['### CRUD ' + s.name]; const t0 = Date.now();
    const step = (k, v) => { L.push(`crud|${k}|${v}`); window.__AWSTEP = 'crud ' + k.replace(/\|.*/, '') + (k.startsWith('check|') ? ' ' + k.split('|')[1] : ''); };   // __AWSTEP: live progress for the runner
    const cells = r => [...r.cells].map(c => c.innerText.trim().replace(/\s+/g, ' ')).join(' | ');
    const fmsg = d => [...new Set(msgs(d))].join(' / ') || '(none)';
    async function save(d) { const b = btnIn(d, s.save); if (!b) return false; toasts.length = 0; b.click(); await settle(d); return true; }
    async function delAll(tag) {
      for (let i = 0; i < 3 && rowOf(s.name); i++) {
        step(tag, await rowAction(s.name, s.del)); const c = lastDialog();
        if (c) { step(tag + '.confirm.text', (c.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 160)); const cb = btnIn(c, s.confirm || s.del) || [...c.querySelectorAll('button')].filter(vis).pop(); toasts.length = 0; cb.click(); await until(() => !rowOf(s.name), 4000); await until(() => toasts.length, 2000); await wait(200); step(tag + '.toast', takeToasts()); }
        else await until(() => !rowOf(s.name), 4000);
      }
    }
    try {
      if (!/^TEST/.test(s.name || '')) { step('refused', 'name must start with TEST'); throw new Error('refused'); }
      if (rowOf(s.name)) { step('refused', 'a row with this TEST name already exists: clean it first'); throw new Error('refused'); }
      step('count.start', count()); takeToasts();
      let d;
      if (s.empty !== false && (d = await openForm(s.open))) { await save(d); step('save.empty', fmsg(d)); step('save.empty.toast', takeToasts()); await closeForm(); }
      if (s.probe !== false && (d = await openForm(s.open))) { await probe({ root: null }); L.push(...(window.__AWR || '').split('\n').slice(1)); window.__AWR = null; await closeForm(); }
      for (const c of s.checks || []) {
        if (!(d = await openForm(s.open))) break;
        fill(d, s.fill); fill(d, c); await save(d);
        const k = Object.entries(c).map(([l, v]) => l + '=' + JSON.stringify(v.length > 20 ? v.length + ' chars' : v)).join(', ');
        step('check|' + k, fmsg(d) + ' | toast ' + takeToasts());
        if (lastDialog()) await closeForm();
        await wait(200); if (rowOf(s.name)) { step('check|' + k + '|accepted', 'saved; deleting'); await delAll('check.delete'); }
      }
      if (!(d = await openForm(s.open))) { step('open', 'not found: ' + s.open); throw new Error('form did not open'); }
      step('fill', fill(d, s.fill)); await save(d);
      step('save.valid.msgs', fmsg(d)); step('save.valid.toast', takeToasts()); if (lastDialog()) { step('dialog.after.save', 'still open'); await closeForm(); }
      await wait(300); let r = rowOf(s.name); step('count.after.create', count()); step('row', r ? cells(r) : 'not found');
      if (s.dup !== false && r && (d = await openForm(s.open))) { fill(d, s.fill); await save(d); step('save.duplicate.msgs', fmsg(d)); step('save.duplicate.toast', takeToasts()); await closeForm(); step('count.after.duplicate', count()); }
      if (s.view && r) {
        step('view', await rowAction(s.name, s.view));
        // the detail form loads its data after the dialog opens (and some apps swap the dialog element): wait for filled fields
        await until(() => { const d = lastDialog(); return d && [...d.querySelectorAll('input,textarea')].some(e => e.value); }, 5000); await wait(200); const v = lastDialog();
        if (v) { const ins = [...v.querySelectorAll('input,textarea')].filter(vis); step('view.fields', ins.length + ' fields, ' + ins.filter(e => !e.disabled && !e.readOnly).length + ' editable; title ' + (v.querySelector('h1,h2,h3,[role=heading]')?.innerText || '').trim());
          if (s.edit) { step('edit.fill', fill(v, s.edit)); if (await save(v)) step('edit.toast', takeToasts()); if (lastDialog()) { step('dialog.after.edit', 'still open'); await closeForm(); } await wait(300); const r2 = rowOf(s.name); const after = r2 ? cells(r2) : 'not found'; step('row.after.edit', after); const want = Object.values(s.edit); step('edit.result', want.every(x => after.includes(x)) ? 'changed' : 'FAILED: row does not show the edited value'); }
          else await closeForm(); }
      }
      if (s.del) await delAll('delete');
      await until(() => { const m = document.body.innerText.match(/Tổng\s+([\d.]+)\s+kết quả/i); return !m || window.__AWTOTAL == null || +m[1] === window.__AWTOTAL; }, 3000);
      step('count.end', count());
      { const m = document.body.innerText.match(/Tổng\s+([\d.]+)\s+kết quả/i); if (m && window.__AWTOTAL != null && +m[1] !== window.__AWTOTAL) step('count.mismatch', `footer shows ${m[1]} but the list API says ${window.__AWTOTAL} (app does not refresh its footer?)`); } step('left.over', rowOf(s.name) ? 'YES: clean up by hand' : 'none');
    } catch (e) { L.push('note|error ' + e.message); }
    finally { L.push(`note|crud ${Date.now() - t0} ms`); window.__AWR = L.join('\n'); }
    return window.__AWR;   // also reached after an early 'return' inside try (finally runs first)
  }
  function go(path) { window.__AWT = performance.now(); const a = document.querySelector(`a[href="${path}"]`); if (a) a.click(); else history.pushState({}, '', path), dispatchEvent(new PopStateEvent('popstate')); return path; }
  return { DANGER, sweep, walk, probe, crud, api, go, out: () => window.__AWR || 'running' };
}).toString();
// Set window.__AWKEY = 'pokit_aw_<agent>' BEFORE pasting when several agents share the origin (the key is per origin, not per tab).
// install: window.AW now, and a copy in localStorage so a reloaded page re-installs with: eval(localStorage.pokit_aw)
window.AW = eval('(' + window.__AWSRC + ')')(); if (!window.__AWNOSTORE) try { localStorage.setItem(window.__AWKEY || 'pokit_aw', 'window.AW=(' + window.__AWSRC + ')();"AW ready"'); } catch (e) {} 'AW ready'
