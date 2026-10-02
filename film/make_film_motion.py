"""film_motion.html : la page du film V1, avec le moteur V2 et ses styles (fond animé,
fenêtres flottantes, masques de texte)."""
from pathlib import Path
ICI = Path(__file__).parent; RAC = ICI.parent
h = (RAC / "film.html").read_text()
css = """
#bgfx{position:absolute;inset:0;z-index:0;--x1:80%;--y1:-5%;--x2:8%;--y2:105%;--g:0;background:radial-gradient(1300px 900px at var(--x1) var(--y1),rgba(82,183,255,calc(.26 + var(--g))),rgba(82,183,255,0) 60%),radial-gradient(1200px 900px at var(--x2) var(--y2),rgba(27,10,176,.85),rgba(27,10,176,0) 62%),#0B0430}
.scene{z-index:1}
.stage.mst{background:transparent}
.win{position:absolute;left:0;top:0;width:1280px;height:720px;border-radius:14px;overflow:hidden;background:#F7F8FF;box-shadow:0 50px 120px -30px rgba(0,0,0,.7),0 0 0 1px rgba(255,255,255,.1);transform-origin:50% 50%}
.win .cam{position:absolute;inset:0}
.sheen{position:absolute;top:-30%;bottom:-30%;left:0;width:24%;pointer-events:none;background:linear-gradient(100deg,rgba(255,255,255,0),rgba(255,255,255,.65),rgba(255,255,255,0));mix-blend-mode:soft-light;z-index:6;opacity:0}
.wm{display:inline-block;overflow:hidden;vertical-align:top;padding:0 .03em .12em;margin-bottom:-.12em}
.ovl{font-size:33px;padding:15px 30px;background:rgba(18,0,80,.8);backdrop-filter:blur(14px) saturate(140%);border:1px solid rgba(255,255,255,.14);border-radius:16px}
.ovl em{color:#52B7FF;text-shadow:0 0 22px rgba(82,183,255,.5)}
.hud{background:rgba(18,0,80,.8);border:1px solid rgba(255,255,255,.12)}
"""
h = h.replace("</style></head>", css + "</style></head>", 1)
h = h.replace('<div id="film">', '<div id="film"><div id="bgfx"></div>', 1)
h = h.replace('<script src="film/engine.js"></script>', '<script src="film/engine_motion.js"></script>', 1)
assert "engine_motion.js" in h and 'id="bgfx"' in h
(RAC / "film_motion.html").write_text(h)
print("film_motion.html", len(h))
