// Browser side of tools/render3d.py: builds the three.js scene for one floor and draws it, then lays out the labels.
// Plan coordinates (x right, y towards the road, metres) map to three.js as (x, height, y).
import * as THREE from '__THREE__';
import { RoundedBoxGeometry } from '__RBOX__';
import { RoomEnvironment } from '__ENV__';

let scene;
const OPP = { E: 'W', W: 'E', N: 'S', S: 'N' };
let seed = 7;
const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
const cache = {};

function M(color, o = {}) {
  const k = color + JSON.stringify(o);
  if (!o.map && cache[k]) return cache[k];
  const m = new THREE.MeshStandardMaterial({ color, roughness: o.r ?? 0.8, metalness: o.m ?? 0 });
  if (o.map) m.map = o.map;
  if (o.e) { m.emissive = new THREE.Color(o.e); m.emissiveIntensity = o.ei ?? 1; }
  if (o.op) { m.transparent = true; m.opacity = o.op; m.depthWrite = false; }
  m.envMapIntensity = 0.5;
  if (!o.map) cache[k] = m;
  return m;
}
function add(geo, mat, x, y, h, o = {}) {
  const m = new THREE.Mesh(geo, mat);
  m.position.set(x, h, y);
  m.castShadow = o.cast ?? true;
  m.receiveShadow = true;
  scene.add(m);
  return m;
}
function box(r, h0, h1, mat, rad = 0, o = {}) {
  const w = r[2] - r[0], d = r[3] - r[1], hh = h1 - h0;
  if (w <= 1e-4 || d <= 1e-4 || hh <= 1e-4) return null;
  const rr = Math.min(rad, w / 2.01, d / 2.01, hh / 2.01);
  const g = rr > 0.001 ? new RoundedBoxGeometry(w, hh, d, 3, rr) : new THREE.BoxGeometry(w, hh, d);
  return add(g, mat, (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, (h0 + h1) / 2, o);
}
// local frame of an item: a runs from its back (or bed head) towards its front, c across it
function frame(r, back) {
  const [x0, y0, x1, y1] = r;
  if (back === 'W') return { L: x1 - x0, W: y1 - y0, R: (a0, a1, c0, c1) => [x0 + a0, y0 + c0, x0 + a1, y0 + c1] };
  if (back === 'E') return { L: x1 - x0, W: y1 - y0, R: (a0, a1, c0, c1) => [x1 - a1, y0 + c0, x1 - a0, y0 + c1] };
  if (back === 'N') return { L: y1 - y0, W: x1 - x0, R: (a0, a1, c0, c1) => [x0 + c0, y0 + a0, x0 + c1, y0 + a1] };
  return { L: y1 - y0, W: x1 - x0, R: (a0, a1, c0, c1) => [x0 + c0, y1 - a1, x0 + c1, y1 - a0] };
}
function hex2rgb(h) { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function shade(h, v) { return 'rgb(' + hex2rgb(h).map(c => Math.max(0, Math.min(255, Math.round(c + v)))).join(',') + ')'; }
function mix(h, t) { const c = hex2rgb(h).map(v => Math.round(v + (255 - v) * t)); return '#' + c.map(v => v.toString(16).padStart(2, '0')).join(''); }

// ---- canvas textures
function canvasTex(size, draw) {
  const c = document.createElement('canvas'); c.width = c.height = size;
  draw(c.getContext('2d'), size);
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}
const tiles = (base, grout, n, jit) => canvasTex(512, (g, s) => {
  const q = s / n;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    g.fillStyle = shade(base, (rnd() - 0.5) * jit); g.fillRect(i * q, j * q, q, q);
    for (let k = 0; k < 40; k++) { g.fillStyle = shade(base, (rnd() - 0.5) * jit * 1.6); g.globalAlpha = 0.25; g.fillRect(i * q + rnd() * q, j * q + rnd() * q, 2 + rnd() * 6, 1 + rnd() * 3); g.globalAlpha = 1; }
  }
  g.fillStyle = grout;
  for (let i = 0; i <= n; i++) { g.fillRect(i * q - 1.5, 0, 3, s); g.fillRect(0, i * q - 1.5, s, 3); }
});
const planks = (base) => canvasTex(512, (g, s) => {
  const n = 8, q = s / n;
  for (let i = 0; i < n; i++) {
    g.fillStyle = shade(base, (rnd() - 0.5) * 26); g.fillRect(0, i * q, s, q);
    for (let k = 0; k < 14; k++) { g.strokeStyle = shade(base, -25); g.globalAlpha = 0.25; g.beginPath(); const y = i * q + rnd() * q; g.moveTo(0, y); g.bezierCurveTo(s * 0.3, y + 3, s * 0.6, y - 3, s, y + 1); g.stroke(); g.globalAlpha = 1; }
    g.fillStyle = shade(base, -60); g.fillRect(0, i * q, s, 2.5);
    const cut = rnd() * s; g.fillRect(cut, i * q, 2.5, q);
  }
});
const rugTex = (base, edge) => canvasTex(256, (g, s) => {
  g.fillStyle = base; g.fillRect(0, 0, s, s);
  for (let k = 0; k < 1500; k++) { g.fillStyle = shade(base, (rnd() - 0.5) * 30); g.globalAlpha = 0.35; g.fillRect(rnd() * s, rnd() * s, 2, 2); }
  g.globalAlpha = 1; g.strokeStyle = edge; g.lineWidth = 6; g.strokeRect(14, 14, s - 28, s - 28);
  g.lineWidth = 2; g.strokeRect(26, 26, s - 52, s - 52);
  g.globalAlpha = 0.5; for (let i = 0; i < 6; i++) for (let j = 0; j < 6; j++) { g.beginPath(); g.arc(48 + i * 32, 48 + j * 32, 7, 0, 6.3); g.stroke(); }
});
const glowTex = canvasTex(128, (g, s) => {
  const gr = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  gr.addColorStop(0, 'rgba(255,214,150,0.85)'); gr.addColorStop(0.35, 'rgba(255,200,130,0.35)'); gr.addColorStop(1, 'rgba(255,190,120,0)');
  g.fillStyle = gr; g.fillRect(0, 0, s, s);
});

function floorPlane(r, tex, tile, h = 0.004) {
  const w = r[2] - r[0], d = r[3] - r[1];
  const t = tex.clone(); t.needsUpdate = true;
  t.repeat.set(w / tile, d / tile); t.offset.set(r[0] / tile, -r[3] / tile);
  const m = add(new THREE.PlaneGeometry(w, d), M('#ffffff', { map: t, r: 0.55 }), (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, h, { cast: false });
  m.rotation.x = -Math.PI / 2;
  return m;
}

// ---- furniture (real Wakefit sizes come in it.rect / it.h)
function bed(it) {
  const { L, W, R } = frame(it.rect, it.head);
  const queen = it.type === 'orion_queen_bed';
  const fm = M(queen ? '#7F858B' : '#ECE8E1', { r: queen ? 0.85 : 0.5 });
  box(R(0.07, L, 0, W), 0, 0.32, fm, 0.02);                                  // storage base
  box(R(0, 0.07, 0, W), 0, it.h, fm, 0.025);                                 // headboard
  if (queen) box(R(0.07, 0.11, 0.06, W - 0.06), 0.34, it.h - 0.08, M('#8D939A', { r: 0.95 }), 0.03);
  box(R(0.09, L - 0.02, 0.025, W - 0.025), 0.32, 0.52, M('#F6F4EF', { r: 0.9 }), 0.05);        // mattress
  const q0 = 0.09 + (L - 0.11) * 0.37;
  box(R(q0, L, -0.008, W + 0.008), 0.36, 0.545, M(it.quilt, { r: 0.95 }), 0.03);              // quilt
  box(R(q0, q0 + 0.16, -0.012, W + 0.012), 0.36, 0.565, M(mix(it.quilt, 0.35), { r: 0.95 }), 0.035);
  const pil = M('#FBFAF7', { r: 0.95 });
  const ps = W > 1.3 ? [[W / 2 - 0.72, W / 2 - 0.04], [W / 2 + 0.04, W / 2 + 0.72]] : [[W / 2 - 0.34, W / 2 + 0.34]];
  for (const [c0, c1] of ps) box(R(0.12, 0.5, c0, c1), 0.5, 0.64, pil, 0.06);
  const cc = W / 2;
  box(R(0.46, 0.6, cc - 0.2, cc + 0.2), 0.52, 0.64, M(it.quilt, { r: 0.95 }), 0.05);           // accent cushion
}
function lamp(x, y, h) {
  add(new THREE.CylinderGeometry(0.05, 0.065, 0.03, 20), M('#D9D2C6', { r: 0.4 }), x, y, h + 0.015);
  add(new THREE.CylinderGeometry(0.008, 0.008, 0.2, 8), M('#C2A878', { m: 0.7, r: 0.3 }), x, y, h + 0.13);
  add(new THREE.CylinderGeometry(0.075, 0.11, 0.15, 24), M('#FFF2DA', { e: '#FFD49A', ei: 0.55, r: 0.9 }), x, y, h + 0.28, { cast: false });
  const g = add(new THREE.PlaneGeometry(1.1, 1.1), new THREE.MeshBasicMaterial({ map: glowTex, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0.32 }), x, y, h + 0.42, { cast: false });
  g.rotation.x = -Math.PI / 2; g.receiveShadow = false;
}
function tinker(it) {
  const r = it.rect;
  box(r, 0, it.h, M('#8A6244', { r: 0.6 }), 0.012);
  box([r[0] + 0.02, r[1] + 0.02, r[2] - 0.02, r[3] - 0.02], it.h, it.h + 0.002, M('#9A7253', { r: 0.5 }));
  lamp((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, it.h);
}
function wardrobe(it) {
  const { L: D, W, R } = frame(it.rect, OPP[it.access[0]]);
  const g = it.type === 'gingham_wardrobe';
  box(R(0, D, 0, W), 0, it.h, M(g ? '#9B6B46' : '#D7B68C', { r: 0.6 }), 0.012);
  box(R(0.03, D - 0.03, 0.03, W - 0.03), it.h, it.h + 0.003, M(g ? '#A87852' : '#DDBE96', { r: 0.55 }));
  box(R(D - 0.004, D + 0.004, W / 2 - 0.004, W / 2 + 0.004), 0.06, it.h - 0.04, M('#4E3A2A'));
  for (const s of [-1, 1]) box(R(D, D + 0.03, W / 2 + s * 0.04 - 0.008, W / 2 + s * 0.04 + 0.008), it.h * 0.45, it.h * 0.62, M('#2F3033', { m: 0.7, r: 0.3 }), 0.004);
  if (g) box(R(D, D + 0.006, 0.06, W / 2 - 0.05), 0.3, it.h - 0.12, M('#DCE7EC', { m: 0.95, r: 0.06 }));
}
function chair(it) {
  const { L: D, W, R } = frame(it.rect, OPP[it.access[0]]);
  const a = D + 0.27, c = W / 2;
  const fab = M('#4A4F57', { r: 0.9 }), blk = M('#26282C', { r: 0.5, m: 0.3 });
  box(R(a - 0.23, a + 0.23, c - 0.24, c + 0.24), 0.43, 0.51, fab, 0.04);
  box(R(a + 0.19, a + 0.26, c - 0.22, c + 0.22), 0.58, 1.02, fab, 0.04);
  box(R(a + 0.2, a + 0.23, c - 0.03, c + 0.03), 0.43, 0.6, blk);
  const q = R(a - 0.001, a + 0.001, c - 0.001, c + 0.001), cx = (q[0] + q[2]) / 2, cy = (q[1] + q[3]) / 2;
  add(new THREE.CylinderGeometry(0.025, 0.025, 0.34, 10), blk, cx, cy, 0.26);
  for (let k = 0; k < 5; k++) {
    const t = k * 2 * Math.PI / 5 + 0.3;
    const m = add(new THREE.BoxGeometry(0.3, 0.03, 0.04), blk, cx + Math.cos(t) * 0.15, cy + Math.sin(t) * 0.15, 0.07);
    m.rotation.y = -t;
  }
}
function desk(it) {
  const { L: D, W, R } = frame(it.rect, OPP[it.access[0]]);
  const wood = M('#B4865B', { r: 0.55 }), h = it.h;
  box(R(0, D, 0, W), h - 0.03, h, wood, 0.008);
  box(R(0, D, 0, 0.025), 0, h - 0.03, wood); box(R(0, D, W - 0.025, W), 0, h - 0.03, wood);
  box(R(0, 0.02, 0.025, W - 0.025), 0.3, h - 0.03, wood);
  box(R(0.02, D * 0.55, 0.025, W - 0.025), 0.52, 0.54, wood);
  const c = W / 2, a0 = D * 0.3;
  box(R(a0, a0 + 0.23, c - 0.165, c + 0.165), h, h + 0.018, M('#3B3E44', { m: 0.5, r: 0.4 }), 0.006);
  box(R(a0 - 0.012, a0, c - 0.165, c + 0.165), h + 0.018, h + 0.23, M('#2A2D32', { m: 0.4, r: 0.3 }), 0.004);
  box(R(0.05, 0.13, W - 0.13, W - 0.05), h, h + 0.1, M('#E8E2D8', { r: 0.5 }), 0.01);   // pen stand
  if (it.chair) chair(it);
}
function sofa(it) {
  const { L: D, W, R } = frame(it.rect, OPP[it.access[0]]);
  const fab = M('#A2A5A8', { r: 0.95 }), seat = M('#ADB0B2', { r: 0.95 });
  box(R(0.02, D - 0.02, 0.02, W - 0.02), 0.06, 0.4, fab, 0.04);
  box(R(0, 0.22, 0, W), 0.06, 0.712, fab, 0.06);
  box(R(0, D, 0, 0.1), 0.06, 0.58, fab, 0.04); box(R(0, D, W - 0.1, W), 0.06, 0.58, fab, 0.04);
  box(R(0.22, D - 0.02, 0.1, W / 2 - 0.005), 0.4, 0.5, seat, 0.05);
  box(R(0.22, D - 0.02, W / 2 + 0.005, W - 0.1), 0.4, 0.5, seat, 0.05);
  box(R(0.2, 0.34, 0.14, 0.5), 0.48, 0.84, M('#8FA88A', { r: 0.95 }), 0.06);
  box(R(0.2, 0.34, W - 0.5, W - 0.14), 0.48, 0.8, M('#D6A08B', { r: 0.95 }), 0.06);
}
function tv(it) {
  const { W, R } = frame(it.rect, OPP[it.access[0]]);
  box(R(0, 0.03, W / 2 - 0.12, W / 2 + 0.12), 1.2, 1.4, M('#333438'));
  box(R(0.03, 0.07, 0, W), 1.1, 1.1 + it.h, M('#15161A', { r: 0.35, m: 0.4 }), 0.008);
  box(R(0.07, 0.073, 0.012, W - 0.012), 1.112, 1.1 + it.h - 0.012, M('#1E2B36', { r: 0.12, m: 0.3 }));
}
function plant(d) {
  const r = d.rect, cx = (r[0] + r[2]) / 2, cy = (r[1] + r[3]) / 2, rad = (r[2] - r[0]) / 2;
  add(new THREE.CylinderGeometry(rad * 0.8, rad * 0.62, 0.3, 24), M('#E9E4DC', { r: 0.5 }), cx, cy, 0.15);
  const greens = ['#5E8A4C', '#6F9C58', '#4E7A40', '#7BA662'];
  for (let k = 0; k < 9; k++) {
    const t = k * 2.4, rr = rad * (0.25 + 0.5 * rnd());
    const m = add(new THREE.IcosahedronGeometry(rad * (0.42 + 0.25 * rnd()), 1), M(greens[k % 4], { r: 0.8 }),
      cx + Math.cos(t) * rr, cy + Math.sin(t) * rr, 0.42 + 0.32 * rnd());
    m.scale.set(1, 0.8, 1);
  }
}
function planter(d) {
  const r = d.rect;
  box(r, 0, 0.42, M('#7E5D41', { r: 0.7 }), 0.02);
  box([r[0] + 0.03, r[1] + 0.03, r[2] - 0.03, r[3] - 0.03], 0.42, 0.425, M('#5A4433', { r: 1 }));
  const long = r[2] - r[0] > r[3] - r[1], len = long ? r[2] - r[0] : r[3] - r[1], n = Math.max(2, Math.round(len / 0.32));
  const greens = ['#5E8A4C', '#6F9C58', '#4E7A40', '#7BA662'];
  for (let i = 0; i < n; i++) {
    const u = (i + 0.5) / n, x = long ? r[0] + u * len : (r[0] + r[2]) / 2, y = long ? (r[1] + r[3]) / 2 : r[1] + u * len;
    const m = add(new THREE.IcosahedronGeometry(0.16 + 0.05 * rnd(), 1), M(greens[i % 4], { r: 0.8 }), x, y, 0.55 + 0.08 * rnd());
    m.scale.set(1, 0.85, 1);
    if (i % 3 === 1) add(new THREE.IcosahedronGeometry(0.05, 0), M('#E6A0A8', { r: 0.7 }), x + 0.05, y - 0.04, 0.74);
  }
}
function tchair(d) {
  const { L: D, W, R } = frame(d.rect, OPP[d.face]);
  const rat = M('#C49A6C', { r: 0.9 });
  box(R(0, D, 0, W), 0.08, 0.38, rat, 0.08);
  box(R(0, 0.12, 0, W), 0.08, 0.8, rat, 0.06);
  box(R(0, D, 0, 0.09), 0.08, 0.6, rat, 0.04); box(R(0, D, W - 0.09, W), 0.08, 0.6, rat, 0.04);
  box(R(0.12, D - 0.03, 0.09, W - 0.09), 0.38, 0.46, M('#EFE9DF', { r: 0.95 }), 0.05);
  box(R(0.12, 0.24, 0.16, W - 0.16), 0.46, 0.74, M('#D6A08B', { r: 0.95 }), 0.05);
}
function ttable(d) {
  const r = d.rect, cx = (r[0] + r[2]) / 2, cy = (r[1] + r[3]) / 2, rad = (r[2] - r[0]) / 2;
  add(new THREE.CylinderGeometry(rad, rad, 0.03, 40), M('#B98E60', { r: 0.7 }), cx, cy, 0.52);
  add(new THREE.CylinderGeometry(0.04, 0.12, 0.5, 16), M('#8C6A48', { r: 0.7 }), cx, cy, 0.25);
  add(new THREE.CylinderGeometry(0.04, 0.05, 0.12, 16), M('#F1EEE8', { r: 0.4 }), cx + 0.05, cy, 0.6);
  add(new THREE.IcosahedronGeometry(0.07, 1), M('#6F9C58'), cx + 0.05, cy, 0.7);
}
function rug(d) {
  const r = d.rect, w = r[2] - r[0], h = r[3] - r[1];
  const t = rugTex('#D9CBB3', '#B9A485'); t.repeat.set(1, 1);
  const m = add(new THREE.PlaneGeometry(w, h), M('#ffffff', { map: t, r: 1 }), (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, 0.012, { cast: false });
  m.rotation.x = -Math.PI / 2;
}
function wc(w) {
  const s = w.back === 'N' ? 1 : -1, y = w.y, x = w.x, white = M('#FAFAFA', { r: 0.25 });
  box([x - 0.18, Math.min(y, y + s * 0.17), x + 0.18, Math.max(y, y + s * 0.17)], 0.4, 0.78, white, 0.03);
  box([x - 0.19, Math.min(y + s * 0.12, y + s * 0.64), x + 0.19, Math.max(y + s * 0.12, y + s * 0.64)], 0, 0.4, white, 0.12);
  box([x - 0.17, Math.min(y + s * 0.2, y + s * 0.62), x + 0.17, Math.max(y + s * 0.2, y + s * 0.62)], 0.4, 0.42, M('#EDEDED', { r: 0.3 }), 0.1);
}

// ---- building
function door(d, wh) {
  const [hx, hy] = d.hinge, [qx, qy] = d.quadrant, th = 72 * Math.PI / 180;
  const c = d.leaf_axis === 'x' ? [qx, 0] : [0, qy], o = d.leaf_axis === 'x' ? [0, qy] : [qx, 0];
  const dir = [Math.cos(th) * c[0] + Math.sin(th) * o[0], Math.cos(th) * c[1] + Math.sin(th) * o[1]];
  const w = d.width - 0.03, hgt = Math.min(2.1, wh - 0.03);
  const m = add(new THREE.BoxGeometry(w, hgt, 0.04), M('#B98A5C', { r: 0.6 }), hx + dir[0] * w / 2, hy + dir[1] * w / 2, hgt / 2);
  m.rotation.y = Math.atan2(-dir[1], dir[0]);
}
function windowAt(wd, wh) {
  const r = wd.rect, glassFrom = Math.min(wd.sill, wh - 0.35);
  const wall = [M('#F2EDE6', { r: 0.9 }), M('#F2EDE6', { r: 0.9 }), M('#48494C', { r: 0.9 }), M('#F2EDE6'), M('#F2EDE6', { r: 0.9 }), M('#F2EDE6', { r: 0.9 })];
  const w = r[2] - r[0], d = r[3] - r[1];
  add(new THREE.BoxGeometry(w, glassFrom, d), wall, (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, glassFrom / 2);
  const cy = (r[1] + r[3]) / 2;
  box([r[0], cy - 0.025, r[2], cy + 0.025], glassFrom, wh, M('#BFDDEB', { r: 0.05, m: 0.1, op: 0.45 }), 0, { cast: false });
  const fr = M('#FAFAFA', { r: 0.4 });
  box([r[0], r[1] + 0.02, r[2], r[3] - 0.02], wh - 0.03, wh, fr);
  box([r[0], r[1] + 0.02, r[2], r[3] - 0.02], glassFrom, glassFrom + 0.03, fr);
  const n = Math.max(1, Math.round(w / 0.5));
  for (let i = 0; i <= n; i++) { const x = r[0] + i * w / n; box([x - 0.02, r[1] + 0.02, x + 0.02, r[3] - 0.02], glassFrom, wh, fr); }
}
function solid(r, h, top, side = '#F2EDE6') {
  const w = r[2] - r[0], d = r[3] - r[1];
  const s = M(side, { r: 0.9 }), t = M(top, { r: 0.85 });
  add(new THREE.BoxGeometry(w, h, d), [s, s, t, s, s, s], (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, h / 2);
}

export async function render(S) {
  const W = S.view.w, H = S.view.h, WH = S.wh;
  const canvas = document.getElementById('c');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(S.view.dpr); renderer.setSize(W, H);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  scene = new THREE.Scene();
  scene.background = new THREE.Color('#F3EEE7');
  const pm = new THREE.PMREMGenerator(renderer);
  scene.environment = pm.fromScene(new RoomEnvironment(renderer), 0.04).texture;

  const L = S.outline[3], SL = S.slab;
  // ground, slab and the base floor
  const gr = add(new THREE.PlaneGeometry(60, 60), M('#EEE8DF', { r: 1 }), 4, 6, -0.3, { cast: false }); gr.rotation.x = -Math.PI / 2;
  box([-0.04, -0.04, 8.04, SL + 0.04], -0.3, -0.002, M('#D6CCBF', { r: 0.9 }));
  box([0, 0, 8, SL], -0.002, 0.001, M('#E3D7C7', { r: 0.9 }), 0, { cast: false });
  if (S.road) {
    const z0 = SL + 0.5, z1 = SL + 1.75;
    box([-1.2, SL + 0.35, 9.2, z0], -0.3, -0.12, M('#C9C1B6', { r: 0.9 }));
    box([-1.2, z0, 9.2, z1], -0.3, -0.2, M('#6D7074', { r: 0.95 }));
    for (let x = -1.0; x < 9.0; x += 0.9) box([x, z1 - 0.42, x + 0.5, z1 - 0.36], -0.2, -0.195, M('#F4F2EE', { r: 0.6 }));
  }
  // floors
  const T = { room: tiles('#E8DAC7', '#D3C2AC', 4, 10), wet: tiles('#E2E5E8', '#C5CBD0', 8, 8), hall: tiles('#E5DDD2', '#CFC4B6', 4, 8), deck: planks('#B8885B') };
  for (const sp of S.spaces) {
    const n = sp.name, k = n.includes('TOILET') ? 'wet' : n.includes('TERRACE') ? 'deck' : n.startsWith('ROOM') ? 'room' : 'hall';
    for (const r of sp.rects) {
      if (n === 'LIFT') { box(r, 0, 0.006, M('#CFC9C0', { r: 0.6 }), 0, { cast: false }); continue; }
      floorPlane(r, T[k], k === 'deck' ? 1.2 : 2.4);
    }
  }
  // walls, parapets, rails, columns, windows, doors
  for (const r of S.walls) solid(r, WH, '#48494C');
  for (const r of S.parapets) solid(r, 1.0, '#48494C');
  for (const r of S.rails) { solid(r, 0.92, '#9A6B43', '#E6DED2'); }
  for (const c of S.cols) solid(c.rect, WH + 0.004, '#E8B829');
  for (const r of S.railings) {
    const long = r[2] - r[0] > r[3] - r[1];
    box(r, 0.98, 1.02, M('#55575B', { r: 0.4, m: 0.6 }));
    box(long ? [r[0], r[1] + 0.03, r[2], r[3] - 0.03] : [r[0] + 0.03, r[1], r[2] - 0.03, r[3]], 0.05, 0.98, M('#CFE3EC', { r: 0.05, op: 0.35 }), 0, { cast: false });
    const len = long ? r[2] - r[0] : r[3] - r[1], n = Math.max(1, Math.round(len / 1.0));
    for (let i = 0; i <= n; i++) {
      const u = i * len / n;
      box(long ? [r[0] + u - 0.025, r[1], r[0] + u + 0.025, r[3]] : [r[0], r[1] + u - 0.025, r[2], r[1] + u + 0.025], 0, 1.0, M('#55575B', { r: 0.4, m: 0.6 }));
    }
  }
  for (const wd of S.windows) windowAt(wd, WH);
  for (const d of S.doors) door(d, WH);
  for (const r of S.lift_doors) { const cy = (r[1] + r[3]) / 2; box([r[0], cy - 0.03, r[2], cy + 0.03], 0, WH - 0.02, M('#B9BEC3', { m: 0.7, r: 0.3 })); }
  // stair: left flight rises towards the rear, right flight returns towards the front (tread lines as drawn)
  const st = S.stair, mw = st.mid_wall, e = st.enclosure_clear, rs = 0.085, g = st.going;
  const stone = M('#DDD5C9', { r: 0.7 }), nose = M('#B8AC9C', { r: 0.7 });
  for (let k = 0; k < 7; k++) {
    const y1 = mw[3] - g * k, y0 = y1 - g;
    box([e[0], y0, mw[0], y1], 0, rs * (k + 1), stone); box([e[0], y0, mw[0], y0 + 0.025], rs * (k + 1) - 0.004, rs * (k + 1) + 0.002, nose);
  }
  box([e[0], e[1], e[2], mw[1]], 0, rs * 8, stone);
  for (let k = 0; k < 7; k++) {
    const y0 = mw[1] + g * k, y1 = y0 + g, hh = rs * (9 + k);
    box([mw[2], y0, e[2], y1], 0, hh, stone); box([mw[2], y1 - 0.025, e[2], y1], hh - 0.004, hh + 0.002, nose);
  }
  // furniture
  for (const it of S.items) {
    const t = it.type;
    if (t.endsWith('_bed')) bed(it);
    else if (t === 'tinker_side_table') tinker(it);
    else if (t.endsWith('wardrobe')) wardrobe(it);
    else if (t.endsWith('desk')) desk(it);
    else if (t.endsWith('sofa')) sofa(it);
    else if (t.startsWith('tv_')) tv(it);
  }
  for (const d of S.decor) ({ plant, planter_box: planter, terrace_chair: tchair, terrace_table: ttable, rug })[d.type](d);
  for (const w of S.wcs) wc(w);

  // lights
  scene.add(new THREE.HemisphereLight('#FFF8EF', '#CBC1B4', 0.7));
  const sun = new THREE.DirectionalLight('#FFF3E2', 2.1);
  const cx = 4.0, zmin = -1.0, zmax = S.road ? SL + 1.8 : SL + 0.35, cz = (zmin + zmax) / 2;
  sun.position.set(cx - 6, 24, cz + 7); sun.target.position.set(cx, 0, cz);
  sun.castShadow = true; sun.shadow.mapSize.set(4096, 4096);
  Object.assign(sun.shadow.camera, { left: -10, right: 10, top: 10, bottom: -10, near: 1, far: 70 });
  sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.02;
  scene.add(sun, sun.target);

  // camera: almost straight down, tipped a little towards the road like the family's pictures
  const fov = 20, aspect = W / H;
  const halfV = Math.max((zmax - zmin) / 2, 10.2 / 2 / aspect) * 1.02;
  const D = halfV / Math.tan(THREE.MathUtils.degToRad(fov / 2)), tilt = THREE.MathUtils.degToRad(9);
  const cam = new THREE.PerspectiveCamera(fov, aspect, 1, 200);
  cam.position.set(cx, D * Math.cos(tilt), cz + D * Math.sin(tilt)); cam.lookAt(cx, 0, cz);
  renderer.render(scene, cam);

  // labels, dimensions, title and legend
  const ov = document.getElementById('ov');
  const scr = (x, y, h = 0) => { const v = new THREE.Vector3(x, h, y).project(cam); return [(v.x + 1) / 2 * W, (1 - v.y) / 2 * H]; };
  const put = (cls, html, x, y, h) => { const [sx, sy] = scr(x, y, h); const d = document.createElement('div'); d.className = 'lab ' + cls; d.innerHTML = html; d.style.left = sx + 'px'; d.style.top = sy + 'px'; ov.appendChild(d); };
  for (const lb of S.labels) put(lb.kind, lb.lines.map((t, i) => i ? `<span>${t}</span>` : `<b>${t}</b>`).join(''), lb.at[0], lb.at[1], lb.h);
  for (const it of S.items) {
    if (!it.tag) continue;
    const r = it.rect;
    let x = (r[0] + r[2]) / 2, y = (r[1] + r[3]) / 2, h = it.h + 0.02;
    if (it.type.endsWith('_bed')) { const f = frame(r, it.head), q = f.R(f.L * 0.68, f.L * 0.7, f.W / 2, f.W / 2); x = q[0]; y = q[1]; h = 0.6; }
    if (it.type.startsWith('tv_')) h = 1.1 + it.h;
    put('tag', it.tag, x, y, h);
  }
  if (S.road) put('road', S.road_text, 4.0, SL + 0.85, -0.2);
  const svg = document.getElementById('dimsvg');
  for (const dm of S.dims) {
    const [ax, ay] = scr(dm.a[0], dm.a[1], WH), [bx, by] = scr(dm.b[0], dm.b[1], WH);
    svg.insertAdjacentHTML('beforeend', `<line x1="${ax}" y1="${ay}" x2="${bx}" y2="${by}" stroke="#2a2622" stroke-width="1.4" marker-start="url(#ar)" marker-end="url(#ar)"/>`);
    const vert = Math.abs(by - ay) > Math.abs(bx - ax), mx = (ax + bx) / 2, my = (ay + by) / 2;
    const d = document.createElement('div'); d.className = 'lab dim' + (dm.small ? ' dsm' : ''); d.textContent = dm.text;
    d.style.left = mx + 'px'; d.style.top = my + 'px'; if (vert) d.style.transform = 'translate(-50%,-50%) rotate(-90deg)';
    ov.appendChild(d);
  }
  const foot = document.getElementById('foot');
  foot.innerHTML = `<h1>${S.title}</h1><div class="rule"></div><div class="sub">${S.sub}</div><div class="leg">` +
    S.legend.map(l => `<div><span>${l.wakefit ? '<b>' + l.name + '</b>' : l.name} · ${l.size}</span><span>× ${l.n}</span></div>`).join('') +
    `</div><div class="note">${S.note}</div>`;
  return document.getElementById('page').getBoundingClientRect().height;
}
