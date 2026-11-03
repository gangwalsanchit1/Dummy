// Runner for tools/render3d.py: draws a scene description with three.js in headless Chromium and saves the picture.
// Usage: THREE_DIR=<three@0.160.0 package folder> node tools/render3d.js <scene.json> <out.jpg|png>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const CSS = `
body{margin:0;background:#F3EEE7;font-family:Arial,Helvetica,sans-serif}
#page{width:1200px;background:#F3EEE7;position:relative}
#wrap{position:relative;width:1200px}
#c{display:block}
#ov,#dimsvg{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;overflow:visible}
.lab{position:absolute;transform:translate(-50%,-50%);text-align:center;white-space:nowrap}
.room{background:rgba(248,242,233,.9);border-radius:4px;padding:3px 9px;box-shadow:0 1px 3px rgba(0,0,0,.12)}
.room b{display:block;font-size:16px;color:#2a2622;letter-spacing:.03em}
.room span{display:block;font-size:12.5px;color:#3b3530}
.small{background:rgba(250,250,250,.85);border-radius:3px;padding:2px 6px}
.small b{display:block;font-size:11.5px;color:#25414b;letter-spacing:.03em}.small span{display:block;font-size:10.5px;color:#25414b}
.up b{font-size:14px;color:#2a2622;background:rgba(248,242,233,.85);padding:1px 6px;border-radius:3px}
.tag{background:rgba(32,32,36,.74);color:#fff;font-size:10.5px;font-weight:600;padding:1px 6px;border-radius:8px}
.road{color:#f4f2ee;font-size:15px;font-weight:700;letter-spacing:.12em}
.dim{font-size:13.5px;font-weight:700;color:#2a2622;background:#F3EEE7;padding:0 6px}
.dsm{font-size:11.5px}
#foot{padding:4px 46px 26px}
h1{font-size:28px;letter-spacing:.05em;margin:2px 0 4px;text-align:center;color:#2a2622}
.rule{height:2px;background:#2a2622;width:74%;margin:0 auto 8px}
.sub{text-align:center;font-size:13px;color:#4a443e;margin-bottom:12px}
.leg{display:grid;grid-template-columns:1fr 1fr;gap:2px 30px;font-size:12.5px;color:#2a2622}
.leg div{display:flex;justify-content:space-between;border-bottom:1px dotted #c9bfb2;padding:3px 0}
.note{font-size:11px;color:#5a534c;margin-top:10px;line-height:1.45}
`;

(async () => {
  const [scenePath, out] = process.argv.slice(2);
  const TD = process.env.THREE_DIR;
  const rd = (p) => fs.readFileSync(p, 'utf8');
  const src = {
    three: rd(path.join(TD, 'build/three.module.min.js')),
    rbox: rd(path.join(TD, 'examples/jsm/geometries/RoundedBoxGeometry.js')),
    env: rd(path.join(TD, 'examples/jsm/environments/RoomEnvironment.js')),
    app: rd(path.join(__dirname, 'render3d_scene.mjs')),
  };
  const S = JSON.parse(rd(scenePath));
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: S.view.w, height: S.view.h + 400 }, deviceScaleFactor: S.view.dpr });
  const errs = [];
  p.on('pageerror', (e) => errs.push(e.message));
  p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await p.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>${CSS}</style></head><body><div id="page"><div id="wrap">
<canvas id="c"></canvas><svg id="dimsvg"><defs><marker id="ar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#2a2622"/></marker></defs></svg>
<div id="ov"></div></div><div id="foot"></div></div></body></html>`);
  const height = await p.evaluate(async ({ src, S }) => {
    const url = (code) => URL.createObjectURL(new Blob([code], { type: 'text/javascript' }));
    const T = url(src.three);
    const fix = (c) => c.replace(/from\s*['"]three['"]/g, `from '${T}'`);
    const app = src.app.replace('__THREE__', T).replace('__RBOX__', url(fix(src.rbox))).replace('__ENV__', url(fix(src.env)));
    const m = await import(url(app));
    return await m.render(S);
  }, { src, S });
  await p.setViewportSize({ width: S.view.w, height: Math.ceil(height) });
  const el = await p.$('#page');
  const png = out.endsWith('.png');
  await el.screenshot({ path: out, type: png ? 'png' : 'jpeg', ...(png ? {} : { quality: 86 }) });
  await b.close();
  if (errs.length) { console.error('page errors:', errs.join(' | ')); process.exit(1); }
  console.log('wrote', out);
})();
