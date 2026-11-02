// Rasterise SVG files with the Chromium bundled with Playwright. Reads JSON lines {"svg": path, "png": path, "scale": n}; prints "ok" or "err <msg>" per line.
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) { console.log('noplaywright'); process.exit(0); }
const fs = require('fs'); const rl = require('readline').createInterface({ input: process.stdin });
(async () => {
  let b;
  try { b = await chromium.launch(); } catch (e) { try { b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }); } catch (e2) { console.log('nobrowser'); process.exit(0); } }
  const pages = {};
  console.log('ready');
  for await (const line of rl) {
    try {
      const j = JSON.parse(line); const sc = j.scale || 2;
      if (!pages[sc]) pages[sc] = await b.newPage({ deviceScaleFactor: sc });
      const svg = fs.readFileSync(j.svg, 'utf8');
      await pages[sc].setContent('<html><body style="margin:0;background:white">' + svg.slice(svg.indexOf('<svg')) + '</body></html>');
      await pages[sc].locator('svg').screenshot({ path: j.png });
      console.log('ok');
    } catch (e) { console.log('err ' + String(e).slice(0, 200)); }
  }
  await b.close();
})();
