#!/usr/bin/env node
// pokit-browser: run autowalk (walk / crud) in a headless browser on the user's own machine, many pages in parallel.
// The model writes a plan (JSON), this script runs it from start to end without a model turn per step, and writes one
// walk-format file per job. The login stays in a browser profile on this machine (~/.po-kit/profiles/<host>), like a
// normal browser profile; the user signs in themselves with `login`, and `forget` deletes it.
//
//   node pokit-browser.mjs doctor    [--url URL]                 check Node, Playwright, Chromium, login, calibration
//   node pokit-browser.mjs login     --url URL                    open a window; the user signs in; closes by itself
//   node pokit-browser.mjs calibrate --url URL [--route /path] [--max 12]   find how many parallel pages this machine takes
//   node pokit-browser.mjs run       plan.json [--workers N] [--out DIR] [--fresh] [--only TEXT] [--headed]
//   node pokit-browser.mjs forget    --url URL                    delete the saved login for that site
//   node pokit-browser.mjs status    [--watch]                    where the current or last command is (also ~/.po-kit/browser/status.json)
//
// Plan: {"base":"https://app.example.com", "loginPattern":"/login|/sign-?in|/auth",
//        "block":["extra-tracker.example"], "settleMs":600,
//        "jobs":[{"route":"/x","feature":"5.9","mode":"walk","walk":{"open":["Thêm mới"]}},
//                {"route":"/x","feature":"5.9","mode":"crud","crud":{"name":"TEST …", "open":"Thêm mới", ...}}]}
// Safety (on top of autowalk's own DANGER list and the TEST-name rule of crud):
//  - walk jobs: every PUT/PATCH/DELETE and every POST whose path looks like a change is aborted and logged;
//  - all jobs: requests whose path looks like send/notify/pay/sign/export/print are aborted and logged;
//  - crud jobs on the same route never run at the same time; analytics hosts are blocked.
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const HOME = process.env.POKIT_HOME || path.join(os.homedir(), '.po-kit');
const DEPS = path.join(HOME, 'browser');
const CAL = path.join(DEPS, 'calibration.json');
const AWJS = path.join(HERE, '..', 'autowalk.js');
const MIN_NODE = 18;
const TRACKERS = /google-analytics|analytics\.google|googletagmanager|doubleclick|amplitude\.com|facebook\.(com|net)|hotjar|clarity\.ms|segment\.(io|com)|mixpanel|sentry\.io|mpc2-prod/i;
const NEVER = /\b(send|sms|otp|notif\w*|zalo|e?mail|pay(ment)?|checkout|sign(ature)?|esign|e-?invoice|export|download|print|publish|logout|sign-?out)\b/i;
const WRITEY = /create|add|update|edit|save|delete|remove|approve|reject|cancel|confirm|submit|activate|close|import|upload/i;

const args = process.argv.slice(2);
const cmd = args[0];
const opt = (k, d) => { const i = args.indexOf('--' + k); return i < 0 ? d : (args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true); };
const die = (m, code = 1) => { console.error('ERROR: ' + m); process.exit(code); };
const log = m => console.log(m);
// Progress: every command keeps one status file up to date, so the user, a second terminal or the agent can see where it is:
//   node pokit-browser.mjs status [--watch]     (or: cat ~/.po-kit/browser/status.json)
const STATUS = path.join(DEPS, 'status.json');
function progress(o) {
  const st = { cmd, pid: process.pid, updated: new Date().toISOString(), ...o };
  if (o.done != null && o.total) { st.percent = Math.round(o.done * 100 / o.total); if (o.started && o.done) { const el = Date.now() - o.started; st.eta_s = Math.round(el / o.done * (o.total - o.done) / 1000); st.elapsed_s = Math.round(el / 1000); } delete st.started; }
  try { fs.mkdirSync(DEPS, { recursive: true }); fs.writeFileSync(STATUS, JSON.stringify(st, null, 1)); } catch (e) {}
}
const fmt = st => `${st.cmd} ${st.state || ''}${st.total ? ` ${st.done}/${st.total} (${st.percent}%)` : ''}${st.eta_s != null && st.state === 'running' ? `, about ${st.eta_s} s left` : ''}${st.step ? ' - ' + st.step : ''}`;

function loadPlaywright() {
  const tries = [path.join(DEPS, 'package.json'), process.env.POKIT_PLAYWRIGHT_DIR && path.join(process.env.POKIT_PLAYWRIGHT_DIR, 'package.json'), import.meta.url];
  try { tries.push(path.join(execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim(), 'package.json')); } catch (e) {}
  for (const t of tries.filter(Boolean)) { try { return createRequire(t)('playwright'); } catch (e) {} }
  return null;
}
const hostOf = u => { try { return new URL(u).host; } catch (e) { die('bad --url: ' + u); } };
const profileOf = u => path.join(HOME, 'profiles', hostOf(u).replace(/[^a-z0-9.-]/gi, '_'));
const readCal = () => { try { return JSON.parse(fs.readFileSync(CAL, 'utf8')); } catch (e) { return {}; } };
// Which browser: Playwright's Chromium when installed, else the Google Chrome or Edge already on the machine
// (a separate profile folder, never the user's own Chrome profile). Corporate networks often block the Chromium download.
function systemBrowser() {
  const c = [['chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'], ['chrome', '/usr/bin/google-chrome'], ['chrome', '/usr/bin/google-chrome-stable'],
    ['chrome', 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'], ['chrome', 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'],
    ['chrome', path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'Application', 'chrome.exe')],
    ['msedge', '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'], ['msedge', 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'], ['msedge', 'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe']];
  const f = c.find(([, p]) => fs.existsSync(p)); return f ? { channel: f[0], path: f[1] } : null;
}
function browserChoice(pw) {
  const want = process.env.POKIT_BROWSER;   // 'chromium' | 'chrome' | 'msedge'
  let exe = ''; try { exe = pw.chromium.executablePath(); } catch (e) {}
  if (want === 'chrome' || want === 'msedge') return { channel: want, label: want };
  if (exe && fs.existsSync(exe)) return { channel: undefined, label: 'Playwright Chromium' };
  const sys = systemBrowser(); return sys ? { channel: sys.channel, label: (sys.channel === 'chrome' ? 'Google Chrome' : 'Microsoft Edge') + ' (installed, separate profile)' } : null;
}
const median = a => { const s = [...a].sort((x, y) => x - y); return s.length ? s[Math.floor(s.length / 2)] : 0; };

async function openContext(pw, url, { headless = true } = {}) {
  const dir = profileOf(url); fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
  const b = browserChoice(pw); if (!b) die('no browser: run setup-browser.sh (or install Google Chrome).');
  try {
    return await pw.chromium.launchPersistentContext(dir, { headless, channel: b.channel, viewport: { width: 1440, height: 900 }, locale: 'vi-VN', timezoneId: 'Asia/Ho_Chi_Minh' });
  } catch (e) {
    if (/ProcessSingleton|SingletonLock|already in use/i.test(e.message)) die('the login profile is in use by another pokit-browser run. Wait for it to finish, or close its window.');
    if (/Executable doesn't exist|browserType.launch/i.test(e.message)) die('Chromium is not installed. Run the setup script again (setup-browser.sh).');
    throw e;
  }
}
async function prepare(ctx, plan) {
  const src = fs.readFileSync(AWJS, 'utf8');
  await ctx.addInitScript({ content: 'window.__AWNOSTORE=1;\n' + src });
  const extra = (plan.block || []).map(x => x.toLowerCase());
  await ctx.route('**/*', r => { const u = r.request().url(); if (TRACKERS.test(u) || extra.some(x => u.toLowerCase().includes(x))) return r.abort(); return r.fallback(); });
}
function guard(page, mode, base, blocked) {
  const hosts = [new URL(base).host, ...(guard.apiHosts || [])];
  return page.route('**/*', r => {
    const q = r.request(), m = q.method(); let u; try { u = new URL(q.url()); } catch (e) { return r.fallback(); }
    if (hosts.includes(u.host)) {
      if (m !== 'GET' && NEVER.test(u.pathname)) { blocked.push(m + ' ' + u.pathname); return r.abort(); }
      if (mode === 'walk' && (['PUT', 'PATCH', 'DELETE'].includes(m) || (m === 'POST' && WRITEY.test(u.pathname)))) { blocked.push(m + ' ' + u.pathname); return r.abort(); }
    }
    return r.fallback();
  });
}
async function load(page, base, route, plan) {
  const re = new RegExp(plan.loginPattern || '/login|/sign-?in|/auth\\b', 'i');
  await page.goto(new URL(route, base).href, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForFunction(() => {   // content stable for ~600 ms, then go (max 10 s)
    const t = (document.querySelector('main') || document.body)?.innerText || ''; const w = window.__AWSTB = window.__AWSTB || { t: '', n: 0 };
    if (t.length > 20 && t === w.t && !/đang tải|loading/i.test(t.slice(0, 400))) w.n++; else { w.t = t; w.n = 0; } return w.n >= 3;
  }, null, { polling: 200, timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(plan.settleMs ?? 300);
  const loginPage = re.test(new URL(page.url()).pathname) || await page.locator('input[type=password]').first().isVisible().catch(() => false);
  if (loginPage) { const e = new Error('LOGIN_NEEDED'); e.login = true; throw e; }
  const ok = await page.evaluate(() => !!window.AW).catch(() => false);
  if (!ok) throw new Error('autowalk did not load in the page (Content-Security-Policy?)');
}

async function doctor() {
  let bad = 0; const ok = (c, m, fix) => { log((c ? 'OK      ' : 'MISSING ') + m + (c || !fix ? '' : '  ->  ' + fix)); if (!c) bad = 1; };
  const v = +process.versions.node.split('.')[0];
  ok(v >= MIN_NODE, `Node ${process.versions.node} (need ${MIN_NODE}+)`, 'install Node.js LTS from https://nodejs.org');
  ok(fs.existsSync(AWJS), 'autowalk.js next to this script', 'reinstall the plugin');
  const pw = loadPlaywright();
  ok(!!pw, 'Playwright', 'run setup-browser.sh');
  if (pw) { const b = browserChoice(pw); ok(!!b, 'Browser: ' + (b ? b.label : 'none'), 'run setup-browser.sh, or install Google Chrome'); }
  const url = opt('url');
  if (url && pw && !bad) {
    const prof = profileOf(url);
    if (!fs.existsSync(prof)) ok(false, 'login for ' + hostOf(url), `node "${path.join(HERE, 'pokit-browser.mjs')}" login --url ${url}`);
    else {
      const ctx = await openContext(pw, url); const page = await ctx.newPage(); await prepare(ctx, {});
      try { await load(page, url, new URL(url).pathname || '/', {}); ok(true, 'signed in to ' + hostOf(url) + ' and autowalk loads'); }
      catch (e) { ok(false, e.login ? 'login for ' + hostOf(url) + ' (expired)' : 'open ' + url + ': ' + e.message.split('\n')[0], e.login ? `node "${path.join(HERE, 'pokit-browser.mjs')}" login --url ${url}` : 'check the URL / network (VPN?)'); }
      await ctx.close();
    }
    const c = readCal()[hostOf(url)]; log(c ? `INFO    calibrated workers: ${c.workers} (${c.date})` : 'INFO    not calibrated yet (run uses 4 workers); run: calibrate --url ' + url);
  }
  log(bad ? 'Not ready.' : 'Ready.'); process.exit(bad);
}

async function login() {
  const url = opt('url'); if (!url || url === true) die('login needs --url');
  const pw = loadPlaywright() || die('Playwright is missing. Run setup-browser.sh first.');
  const re = new RegExp(opt('login-pattern', '/login|/sign-?in|/auth\\b'), 'i');
  const ctx = await openContext(pw, url, { headless: false }); const page = ctx.pages()[0] || await ctx.newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded' }).catch(() => {});
  progress({ state: 'waiting for the user to sign in', step: 'browser window open on ' + hostOf(url) });
  log('A browser window is open. Sign in there yourself (the agent never types passwords or OTP codes).');
  log('It closes by itself about 5 seconds after you are signed in. You can also close the window when done.');
  let closed = false; ctx.on('close', () => { closed = true; });
  const t0 = Date.now(); let good = 0;
  while (!closed && Date.now() - t0 < 15 * 60 * 1000) {
    await new Promise(r => setTimeout(r, 1000));
    try {
      const p = ctx.pages().find(x => !x.isClosed()); if (!p) break;
      const onLogin = re.test(new URL(p.url()).pathname) || await p.locator('input[type=password]').first().isVisible().catch(() => false);
      good = onLogin || p.url().startsWith('about:') ? 0 : good + 1;
      const sec = Math.round((Date.now() - t0) / 1000); if (!good && sec % 15 === 0) log(`  waiting for sign-in... ${sec} s (page: ${new URL(p.url()).pathname})`);
      if (good === 1) log('  signed in, closing in 5 s');
      if (good >= 5) break;
    } catch (e) { if (closed) break; }
  }
  if (!closed) await ctx.close().catch(() => {});
  progress({ state: good >= 5 ? 'finished' : 'window closed', step: good >= 5 ? 'signed in' : 'not confirmed' });
  log(good >= 5 ? 'Signed in. The login is kept in ' + profileOf(url) : 'Window closed. Check with: doctor --url ' + url);
}

function forget() {
  const url = opt('url'); if (!url || url === true) die('forget needs --url');
  const dir = profileOf(url); if (!fs.existsSync(dir)) return log('No saved login for ' + hostOf(url));
  fs.rmSync(dir, { recursive: true, force: true }); log('Deleted the saved login for ' + hostOf(url));
}

// plain words for the live step a crud job reports (window.__AWSTEP = 'crud <key>')
function stepLabel(st) {
  const m = st.match(/^crud ([\w.]+)(?: (.*))?$/); if (!m) return st;
  const k = m[1], x = m[2] || '';
  const L = [[/^count\.start/, 'reading the list before changes'], [/^save\.empty/, 'pressing Save on an empty form'], [/^probe/, 'typing test values into each field'],
    [/^check\.delete/, 'removing a TEST row the app accepted'], [/^check$/, 'checking a bad value: ' + x], [/^(fill|save\.valid|dialog\.after\.save)/, 'creating the TEST record'],
    [/^(count\.after\.create|row$)/, 'reading the new row in the list'], [/^(save\.duplicate|count\.after\.duplicate)/, 'trying a duplicate'],
    [/^view/, 'opening the detail (view)'], [/^(edit|row\.after\.edit|dialog\.after\.edit)/, 'editing the TEST record'], [/^delete/, 'deleting the TEST record'],
    [/^(count\.end|count\.mismatch|left\.over)/, 'checking that nothing is left']];
  const f = L.find(([re]) => re.test(k)); return f ? f[1] : k;
}
async function runJob(ctx, plan, job, outDir, n) {
  const page = await ctx.newPage(); const blocked = []; const t0 = Date.now();
  try {
    await guard(page, job.mode, plan.base, blocked);
    await load(page, plan.base, job.route, plan);
    // live progress inside the job: the page writes its current step to window.__AWSTEP; print it when it changes,
    // and a 'still working' line every 10 s without change, so a long job never looks frozen
    let last = '', lastAt = Date.now();
    const tick = setInterval(async () => {
      const st = await page.evaluate(() => window.__AWSTEP).catch(() => null);
      if (st && stepLabel(st) !== last) { last = stepLabel(st); lastAt = Date.now(); log(`      job ${n} ${job.route}: ${last} (${Math.round((Date.now() - t0) / 1000)} s)`); progress.cur && progress({ ...progress.cur(), step: `job ${n} ${job.route}: ${last}` }); }
      else if (Date.now() - lastAt > 10000) { lastAt = Date.now(); log(`      job ${n}: still working (${Math.round((Date.now() - t0) / 1000)} s)`); }
    }, 1500);
    let body;
    try {
    if (job.mode === 'crud') {
      body = await page.evaluate(s => window.AW.crud(s), job.crud);
      await page.reload({ waitUntil: 'domcontentloaded' }).catch(() => {}); await load(page, plan.base, job.route, plan).catch(() => {});
      const still = await page.evaluate(n => [...document.querySelectorAll('tbody tr')].some(r => r.innerText.includes(n)), job.crud.name).catch(() => null);
      body += `\ncrud|left.over.after.reload|${still == null ? 'unknown' : still ? 'YES: clean up by hand' : 'none'}`;
    } else body = await page.evaluate(o => window.AW.walk(o), job.walk || {});
    } finally { clearInterval(tick); }
    body = (body || '').replace(/^## .*\n?/, '');
    const shapes = await page.evaluate(() => window.AW.api({ replay: false })).catch(() => '');
    const head = `## ${job.route} | ${job.feature || 'global'}`;
    const text = [head, body, shapes && shapes !== '(no api)' ? shapes : '', ...blocked.map(b => 'note|blocked request ' + b), `note|job ${Date.now() - t0} ms`].filter(Boolean).join('\n') + '\n';
    fs.writeFileSync(path.join(outDir, fileOf(job, n)), text);
    const left = /left\.over(\.after\.reload)?\|YES/.test(text);
    const broken = (text.match(/^crud\|(?:[\w.]+)\|.*(?:\(not found\)|FAILED|action not found|row not found|no row menu|not found:|refused).*$/m) || [])[0] || (/crud\|view\.fields\|0 fields/.test(text) ? 'view opened with 0 fields' : '');
    return { n, route: job.route, mode: job.mode || 'walk', ms: Date.now() - t0, ok: !/note\|error/.test(text) && !left && !broken, warn: left ? 'TEST row left over' : broken ? 'step failed: ' + broken.slice(0, 120) : (text.match(/note\|error ([^\n]*)/) || [])[1] };
  } finally { await page.close().catch(() => {}); }
}
const fileOf = (job, n) => `${String(n).padStart(3, '0')}-${(job.mode || 'walk')}-${job.route.replace(/^\/|\/$/g, '').replace(/[^a-z0-9]+/gi, '-').slice(0, 60) || 'root'}.txt`;

async function pool(items, workers, fn, onError) {
  const crudRoutes = new Set(items.filter(x => x.mode === 'crud').map(x => x.route));
  const locks = new Set(); const queue = items.map((it, i) => ({ it, i })); const res = []; let stop = false;
  async function worker() {
    while (!stop) {
      const k = queue.findIndex(q => !locks.has(q.it.route)); if (k < 0) { if (!queue.length) return; await new Promise(r => setTimeout(r, 200)); continue; }
      const { it, i } = queue.splice(k, 1)[0]; const lock = crudRoutes.has(it.route) ? it.route : null; if (lock) locks.add(lock);
      try { res[i] = await fn(it, i); } catch (e) { res[i] = { n: i + 1, route: it.route, mode: it.mode || 'walk', ok: false, warn: e.message.split('\n')[0] }; if (onError(e)) { stop = true; } }
      finally { if (lock) locks.delete(lock); }
    }
  }
  await Promise.all(Array.from({ length: Math.max(1, workers) }, worker));
  return { res, stopped: stop, left: queue.length };
}

async function run() {
  const file = args[1]; if (!file || file.startsWith('--')) die('run needs a plan file');
  const plan = JSON.parse(fs.readFileSync(file, 'utf8')); if (!plan.base || !Array.isArray(plan.jobs)) die('plan needs "base" and "jobs"');
  for (const j of plan.jobs) if (j.mode === 'crud' && !/^TEST/.test(j.crud?.name || '')) die(`crud job on ${j.route}: name must start with TEST`);
  const pw = loadPlaywright() || die('Playwright is missing. Run setup-browser.sh first.');
  if (!fs.existsSync(profileOf(plan.base))) die(`not signed in to ${hostOf(plan.base)}. Run: node "${path.join(HERE, 'pokit-browser.mjs')}" login --url ${plan.base}`, 3);
  const outDir = opt('out', path.join(path.dirname(path.resolve(file)), 'browser-out')); fs.mkdirSync(outDir, { recursive: true });
  const cal = readCal()[hostOf(plan.base)];
  const workers = +opt('workers', 0) || plan.workers || cal?.workers || 4;
  const only = opt('only'); const fresh = !!opt('fresh');
  const jobs = plan.jobs.map((j, i) => ({ ...j, n: i + 1 })).filter(j => (!only || j.route.includes(only)) && (fresh || !fs.existsSync(path.join(outDir, fileOf(j, j.n)))));
  const P = { started: Date.now(), done: 0, total: jobs.length, warn: 0 }; progress.cur = () => ({ state: 'running', ...P, warnings: P.warn }); progress({ state: 'starting browser', done: 0, total: jobs.length, step: plan.base });
  log(`${jobs.length} job(s), ${workers} worker(s)${cal ? ' (calibrated)' : ''}, output ${outDir}`);
  if (!jobs.length) return log('Nothing to do (all outputs exist; use --fresh to run again).');
  guard.apiHosts = plan.apiHosts || [];   // other hosts of the product API, guarded like the app host
  const ctx = await openContext(pw, plan.base, { headless: !opt('headed') }); await prepare(ctx, plan);
  const t0 = Date.now(); let loginLost = false;
  const r = await pool(jobs, workers, async j => { progress({ state: 'running', ...P, step: 'started ' + j.route }); const x = await runJob(ctx, plan, j, outDir, j.n); P.done++; if (!x.ok) P.warn++; progress({ state: 'running', ...P, step: `finished ${j.mode || 'walk'} ${j.route}`, warnings: P.warn }); log(`[${P.done}/${P.total}] ${x.ok ? 'done' : 'WARN'} ${String(x.n).padStart(3)} ${x.mode.padEnd(4)} ${x.route} ${x.ms} ms${x.warn ? '  ' + x.warn : ''}`); return x; },
    e => { if (e.login) { loginLost = true; return true; } log('FAIL ' + e.message.split('\n')[0]); return false; });
  await ctx.close();
  const done = r.res.filter(Boolean); const wall = Date.now() - t0;
  const sum = { base: plan.base, workers, wall_ms: wall, jobs: done.length, failed: done.filter(x => !x.ok).length, avg_job_ms: Math.round(done.filter(x => x.ms).reduce((a, x) => a + x.ms, 0) / Math.max(1, done.filter(x => x.ms).length)), results: done };
  fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(sum, null, 1));
  progress({ state: loginLost ? 'stopped: login needed' : 'finished', done: done.length, total: jobs.length, step: `${sum.failed} with warnings, ${(wall / 1000).toFixed(1)} s`, summary: path.join(outDir, 'summary.json') });
  log(`Finished ${done.length} job(s) in ${(wall / 1000).toFixed(1)} s, ${sum.failed} with warnings. Summary: ${path.join(outDir, 'summary.json')}`);
  if (loginLost) { log(`LOGIN_NEEDED: the login expired. Run login --url ${plan.base}, then run the same command again (finished jobs are kept).`); process.exit(3); }
}

async function calibrate() {
  const url = opt('url'); if (!url || url === true) die('calibrate needs --url');
  const route = opt('route', new URL(url).pathname || '/'); const pw = loadPlaywright() || die('Playwright is missing. Run setup-browser.sh first.');
  if (!fs.existsSync(profileOf(url))) die('not signed in. Run login first.', 3);
  const ceiling = Math.max(1, Math.min(+opt('max', 12), os.cpus().length * 2, Math.floor(os.totalmem() * 0.5 / (250 * 1024 * 1024))));
  log(`Ceiling from this machine: ${ceiling} (2 x ${os.cpus().length} CPU, RAM ${(os.totalmem() / 2 ** 30).toFixed(0)} GB). Read-only test on ${route}.`);
  const plan = { base: url }; const ctx = await openContext(pw, url); await prepare(ctx, plan);
  const levels = [1, 2, 4, 6, 8, 10, 12, 16].filter(x => x <= ceiling); let base = 0, best = 1; const rows = [];
  const C = { started: Date.now(), done: 0, total: levels.length };
  for (const n of levels) {
    progress({ state: 'running', ...C, step: `testing ${n} parallel page(s)` });
    const t0 = Date.now(); let err = 0; const ms = [];
    await Promise.all(Array.from({ length: n }, async () => { const p = await ctx.newPage(); const b = []; try { await guard(p, 'walk', url, b); const s = Date.now(); await load(p, url, route, plan); await p.evaluate(() => window.AW.walk({})); ms.push(Date.now() - s); } catch (e) { if (e.login) die('login expired. Run login again.', 3); err++; } finally { await p.close().catch(() => {}); } }));
    const m = median(ms); if (!base) base = m; const thr = (n * 1000 * 60) / Math.max(1, Date.now() - t0);
    rows.push({ workers: n, median_ms: m, errors: err, pages_per_min: +thr.toFixed(1) }); log(`workers ${String(n).padStart(2)}: median ${m} ms per page, ${thr.toFixed(1)} pages/min, errors ${err}`);
    C.done++; if (err) break; const top = Math.max(...rows.slice(0, -1).map(x => x.pages_per_min), 0); if (rows.at(-1).pages_per_min >= top) best = n; else if (rows.at(-1).pages_per_min < top * 0.9 || m > base * 1.6) break;
  }
  await ctx.close();
  const all = readCal(); all[hostOf(url)] = { workers: best, date: new Date().toISOString().slice(0, 10), levels: rows };
  fs.mkdirSync(DEPS, { recursive: true }); fs.writeFileSync(CAL, JSON.stringify(all, null, 1));
  progress({ state: 'finished', step: `use ${best} workers` });
  log(`Use ${best} workers for ${hostOf(url)} (saved in ${CAL}).`);
}

async function status() {
  const show = () => { try { const st = JSON.parse(fs.readFileSync(STATUS, 'utf8')); let alive = true; try { process.kill(st.pid, 0); } catch (e) { alive = false; } const end = /^(finished|stopped|window closed)/.test(st.state || ''); return [fmt(st) + (alive || end ? '' : ' (process no longer running)') + `  [${st.updated.slice(11, 19)}]`, end || !alive]; } catch (e) { return ['no run yet', true]; } };
  if (!opt('watch')) return log(show()[0]);
  let last = ''; for (;;) { const [t, end] = show(); if (t !== last) { log(t); last = t; } if (end) return; await new Promise(r => setTimeout(r, 2000)); }
}
const cmds = { doctor, login, run, calibrate, forget, status };
if (!cmds[cmd]) { log(fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n').slice(1, 12).map(l => l.replace(/^\/\/ ?/, '')).join('\n')); process.exit(cmd ? 1 : 0); }
Promise.resolve(cmds[cmd]()).catch(e => die(e.message.split('\n')[0]));
