// Print package/sheets/*.svg (3 per floor) and schedules.html to PDF with Playwright's Chromium.
// Usage: node tools/print_pdfs.js   (needs the 'playwright' package; not committed)
const {chromium} = require('playwright');
const fs = require('fs'), path = require('path');
const root = path.resolve(__dirname, '..'), sh = path.join(root, 'package/sheets'), out = path.join(root, 'package/pdf');
fs.mkdirSync(out, {recursive: true});
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  for (const f of ['GF', 'F1-3', 'F4', 'TERRACE']) {
    const pages = ['A', 'E', 'P'].map(k => fs.readFileSync(path.join(sh, `${f}-${k}.svg`), 'utf8')
      .replace('<svg ', '<svg style="display:block;width:420mm;height:297mm" ')).join('<div style="page-break-after:always"></div>');
    await p.setContent(`<!doctype html><html><head><style>@page{size:A3 landscape;margin:0}body{margin:0}</style></head><body>${pages}</body></html>`);
    await p.pdf({path: path.join(out, `${f}.pdf`), width: '420mm', height: '297mm', printBackground: true, preferCSSPageSize: true});
  }
  await p.goto('file://' + path.join(sh, 'schedules.html'));
  await p.pdf({path: path.join(out, 'schedules.pdf'), format: 'A4', landscape: true, printBackground: true, margin: {top: '10mm', bottom: '10mm', left: '8mm', right: '8mm'}});
  await b.close(); console.log('pdfs written to', out);
})();
