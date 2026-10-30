// Rend les blocs de texte de la carte en PNG transparents via Chromium (façonnage arabe exact).
// usage : node render_text.js <spec.json> <dossier_sortie>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const spec = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const out = path.resolve(process.argv[3]);
  const css = Object.entries(spec.fonts).map(([fam, file]) =>
    `@font-face{font-family:'${fam}';src:url('file://${file}');}`).join('\n');
  const blocks = spec.blocks.map(b =>
    `<div id="${b.id}" dir="${b.dir || 'ltr'}" lang="${b.lang || 'fr'}" style="display:inline-block;width:${b.width}px;` +
    `text-align:center;font-family:'${b.font}';font-size:${b.size}px;line-height:${b.lh};color:${b.color};` +
    `font-weight:${b.weight || 400};font-style:${b.style || 'normal'};letter-spacing:${b.ls || 0}px;` +
    `text-shadow:${b.shadow || 'none'};padding:30px 10px;margin:0 0 120px 0;">${b.text}</div><br>`).join('\n');
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>${css}
    html,body{margin:0;background:transparent;} body{padding:20px;}</style></head><body>${blocks}</body></html>`;
  const f = path.join(out, '_text.html'); fs.writeFileSync(f, html);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1200, height: 1600 }, deviceScaleFactor: 1 });
  await p.goto('file://' + f); await p.evaluate(() => document.fonts.ready);
  for (const bl of spec.blocks) {
    await p.locator('#' + bl.id).screenshot({ path: path.join(out, bl.id + '.png'), omitBackground: true });
  }
  await b.close();
})();
