// Print the final floor 1 drawing set: docs/final/floor1-final.html -> floor1-final.pdf (A3) and floor1-final-plan.png
// Usage: node tools/print_final.js   (needs Playwright with Chromium)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const root = path.resolve(__dirname, '..');
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1100, height: 1550 }, deviceScaleFactor: 1.5 });
  await p.goto('file://' + path.join(root, 'docs/final/floor1-final.html'));
  await p.pdf({ path: path.join(root, 'docs/final/floor1-final.pdf'), format: 'A3', printBackground: true, margin: { top: '10mm', bottom: '10mm', left: '10mm', right: '10mm' } });
  const svg = fs.readFileSync(path.join(root, 'docs/final/floor1-final-plan.svg'), 'utf8');
  await p.setContent('<html><body style="margin:0;background:#fff">' + svg + '</body></html>');
  const el = await p.$('svg');
  await el.screenshot({ path: path.join(root, 'docs/final/floor1-final-plan.png') });
  await b.close();
  console.log('wrote docs/final/floor1-final.pdf and floor1-final-plan.png');
})();
