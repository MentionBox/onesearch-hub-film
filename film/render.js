// Rendu image par image d'un film (V1 : film.html, V2 : film_motion.html).
// render(t) est sans état : chaque page rend une tranche du film et l'envoie à son ffmpeg.
//   node film/render.js --film film_motion.html --out film/out_v2 [--workers 2] [--from 0] [--to 103.1] [--fps 30]
// ffmpeg : variable FFMPEG, sinon celui du paquet Python imageio-ffmpeg.
const { chromium } = require("playwright");
const { spawn, execSync } = require("child_process");
const fs = require("fs"), path = require("path");
const RAC = path.join(__dirname, "..");
const arg = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? process.argv[i + 1] : d; };
const FILM = arg("film", "film_motion.html"), OUT = path.resolve(RAC, arg("out", "film/out_v2"));
const NW = +arg("workers", 2), FPS = +arg("fps", 30);
const T = JSON.parse(fs.readFileSync(path.join(__dirname, "timing.json")));
const from = +arg("from", 0), to = +arg("to", T.total);
const FF = process.env.FFMPEG || execSync(`${process.env.PYTHON || "python3"} -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"`).toString().trim();
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  fs.readdirSync(OUT).filter(f => /^seg\d+\.mp4$/.test(f)).forEach(f => fs.unlinkSync(path.join(OUT, f)));
  const br = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
  const a0 = Math.round(from * FPS), N = Math.round(to * FPS), per = Math.ceil((N - a0) / NW), t0 = Date.now();
  await Promise.all([...Array(NW).keys()].map(async (w) => {
    const a = a0 + w * per, b = Math.min(N, a + per); if (a >= b) return;
    const p = await br.newPage({ viewport: { width: 1920, height: 1080 } });
    p.on("pageerror", e => console.error("erreur de page :", e.message));
    await p.goto("file://" + path.join(RAC, FILM), { waitUntil: "networkidle" });
    await p.evaluate(() => document.fonts.ready); await p.waitForFunction(() => window.FILM_READY);
    const ff = spawn(FF, ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
      "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", path.join(OUT, `seg${w}.mp4`)], { stdio: ["pipe", "inherit", "inherit"] });
    for (let i = a; i < b; i++) {
      await p.evaluate(t => window.render(t), i / FPS);
      const buf = await p.screenshot({ type: "jpeg", quality: 93 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
      if ((i - a) % 300 === 0) console.log(`tranche ${w} : ${i - a}/${b - a} images`);
    }
    ff.stdin.end(); await new Promise(r => ff.on("close", r));
  }));
  await br.close();
  fs.writeFileSync(path.join(OUT, "meta.json"), JSON.stringify({ from: a0 / FPS, to: N / FPS, fps: FPS }));
  console.log(`${N - a0} images en ${((Date.now() - t0) / 1000).toFixed(0)} s → ${path.relative(RAC, OUT)}/seg*.mp4`);
})();
