// Rend chaque plan à 1280 × 720, relève les débordements, puis assemble deux planches-contact.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const ICI = __dirname;
(async () => {
  const src = fs.readFileSync(path.join(ICI, "onesearch-storyboard.html"), "utf8");
  fs.mkdirSync(path.join(ICI, "shots"), { recursive: true });
  fs.writeFileSync(path.join(ICI, "test.html"), '<!doctype html><html><head><meta charset="utf-8"><style>.b-body{display:block!important}.frame{width:1280px!important;max-width:none!important;border-radius:0!important}.notes{display:none!important}</style></head><body>' + src + "</body></html>");
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 }, deviceScaleFactor: 1 });
  const errs = [];
  page.on("console", (m) => { if ((m.type() === "error" || m.type() === "warning") && !/Failed to load resource/.test(m.text())) errs.push(m.text()); });
  page.on("pageerror", (e) => errs.push("PAGEERROR " + e.message));
  await page.goto("file://" + path.join(ICI, "test.html"), { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.addStyleTag({ content: ".b-body{display:block!important}.frame{width:1280px!important;max-width:none!important;border-radius:0!important}.notes{display:none!important}" });
  await page.waitForTimeout(400);
  const report = await page.evaluate(() => {
    const out = [];
    document.querySelectorAll(".board").forEach((b) => {
      const st = b.querySelector(".frame > .stage");
      const r0 = st.getBoundingClientRect();
      const bad = [];
      st.querySelectorAll("*").forEach((el) => {
        if (el.closest("[data-thumb]")) return;
        const r = el.getBoundingClientRect();
        if (!r.width || !r.height) return;
        const cs = getComputedStyle(el);
        if (r.right > r0.right + 1 || r.bottom > r0.bottom + 1) bad.push("hors cadre " + el.tagName + "." + el.className + " " + Math.round(r.right - r0.left) + "×" + Math.round(r.bottom - r0.top));
        if ((cs.overflow === "hidden" || cs.textOverflow === "ellipsis") && el.scrollWidth > el.clientWidth + 1 && el.children.length === 0) bad.push("tronqué: " + el.textContent.slice(0, 50));
        if (el.children.length <= 2 && el.textContent.trim() && /hidden|clip/.test(cs.overflow + cs.overflowY) && el.scrollHeight > el.clientHeight + 2) bad.push("rogné en hauteur: " + el.textContent.trim().slice(0, 50) + " (" + el.clientHeight + "/" + el.scrollHeight + ")");
        if (el.textContent.trim() && el.tagName !== "svg" && !el.closest("svg") && cs.position !== "absolute") {
          let a = el.parentElement;
          while (a && a !== st) { const ac = getComputedStyle(a); if (ac.borderTopWidth !== "0px" || (ac.backgroundColor !== "rgba(0, 0, 0, 0)" && ac.backgroundColor !== "transparent")) break; a = a.parentElement; }
          if (a && a !== st) { const pr = a.getBoundingClientRect(); if (r.right > pr.right + 1.5 || r.left < pr.left - 1.5 || r.bottom > pr.bottom + 1.5) bad.push("déborde de son cadre: " + el.textContent.trim().slice(0, 40) + " (" + Math.round(Math.max(r.right - pr.right, pr.left - r.left, r.bottom - pr.bottom)) + " px)"); }
        }
        if (el.children.length === 0 && el.textContent.trim() && r.height > 0 && r.height < parseFloat(cs.fontSize) * 0.9) bad.push("écrasé: " + el.textContent.trim().slice(0, 50) + " (" + Math.round(r.height) + " px)");
      });
      const ct = st.querySelector(".ct");
      let fill = "";
      if (ct) { const kids = [...ct.children]; const last = kids[kids.length - 1].getBoundingClientRect(); fill = " bas du contenu à " + Math.round(last.bottom - r0.top) + " px"; }
      out.push(b.id + fill + (bad.length ? "\n   " + [...new Set(bad)].slice(0, 8).join("\n   ") : ""));
    });
    return out;
  });
  console.log(report.join("\n"));
  const ids = await page.$$eval(".board", (bs) => bs.map((b) => b.id));
  for (const id of ids) {
    await page.locator("#" + id + " .frame").screenshot({ path: path.join(ICI, "shots", id + ".png") });
  }
  const sheet = (list) => '<!doctype html><meta charset="utf-8"><body style="margin:0;background:#888;display:grid;grid-template-columns:repeat(2,960px);gap:6px;padding:6px;font:14px sans-serif">' +
    list.map((id) => `<div style="position:relative"><img src="shots/${id}.png" style="width:960px;display:block"><b style="position:absolute;left:6px;top:4px;background:#ff0;padding:0 4px">${id}</b></div>`).join("") + "</body>";
  fs.writeFileSync(path.join(ICI, "sheet1.html"), sheet(ids.slice(0, 8)));
  fs.writeFileSync(path.join(ICI, "sheet2.html"), sheet(ids.slice(8)));
  for (const n of [1, 2]) {
    const p2 = await browser.newPage({ viewport: { width: 1938, height: 800 } });
    await p2.goto("file://" + path.join(ICI, `sheet${n}.html`));
    await p2.screenshot({ path: path.join(ICI, `sheet${n}.png`), fullPage: true });
  }
  console.log("console:", errs.length ? errs.join("\n") : "rien");
  await browser.close();
})();
