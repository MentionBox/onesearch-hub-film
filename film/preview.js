// Images de contrôle : une par scène (à 72 % de la scène), ou les instants donnés.
//   node film/preview.js --film film_motion.html [--times 12.5,40.2]
// Écrit film/prev/*.jpg et film/sheet1.png, sheet2.png (planches-contact de 12 images).
const { chromium } = require("playwright");
const fs = require("fs"), path = require("path");
const RAC = path.join(__dirname, "..");
const arg = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? process.argv[i + 1] : d; };
(async () => {
  const T = JSON.parse(fs.readFileSync(path.join(__dirname, "timing.json")));
  const times = arg("times", "") ? arg("times").split(",").map(Number) : T.scenes.map(s => s.start + 0.72 * s.dur);
  const b = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  const errs = []; p.on("pageerror", e => errs.push(e.message));
  await p.goto("file://" + path.join(RAC, arg("film", "film_motion.html")), { waitUntil: "networkidle" });
  await p.evaluate(() => document.fonts.ready); await p.waitForFunction(() => window.FILM_READY);
  const dir = path.join(__dirname, "prev"); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir);
  const shots = [];
  for (const t of times) {
    const k = await p.evaluate(t => window.render(t), t);
    const f = `prev/${t.toFixed(2)}.jpg`; shots.push([f, k, t]);
    await p.screenshot({ path: path.join(__dirname, f), type: "jpeg", quality: 82 });
  }
  for (let g = 0; g < shots.length; g += 12) {
    fs.writeFileSync(path.join(__dirname, "sheet.html"), `<!doctype html><meta charset="utf-8"><body style="margin:0;background:#777;display:grid;grid-template-columns:repeat(3,640px);gap:4px;padding:4px">` +
      shots.slice(g, g + 12).map(([f, k, t]) => `<div style="position:relative"><img src="${f}" style="width:640px;display:block"><b style="position:absolute;left:4px;top:4px;background:#ff0;font:12px sans-serif;padding:0 3px">${k} @${t.toFixed(2)}</b></div>`).join("") + "</body>");
    const q = await b.newPage({ viewport: { width: 1936, height: 400 } });
    await q.goto("file://" + path.join(__dirname, "sheet.html"));
    await q.screenshot({ path: path.join(__dirname, `sheet${g / 12 + 1}.png`), fullPage: true });
  }
  console.log(errs.length ? "erreurs : " + errs.join(" | ") : `${shots.length} images, aucune erreur de page`);
  await b.close();
})();
