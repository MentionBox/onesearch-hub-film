"""Assemble film.html : les plans des planches, plein cadre 1920 × 1080, plus le moteur
d'animation (engine.js) et le minutage (timing.json)."""
import json, re
from pathlib import Path
ICI = Path(__file__).parent; RAC = ICI.parent
html = (RAC / "onesearch-storyboard.html").read_text()
style = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
defs = re.search(r'(<svg width="0" height="0".*?</svg>)', html, re.S).group(1)
boards = re.findall(r'<article class="board" id="(p\d+)">.*?<div class="frame"[^>]*>(.*?)</div>\s*<div class="notes">', html, re.S)
T = json.loads((ICI / "timing.json").read_text())
assert len(boards) == len(T["scenes"]), (len(boards), len(T["scenes"]))
scenes = []
for (pid, stage), s in zip(boards, T["scenes"]):
    assert pid == f"p{s['n']}", (pid, s["n"])
    scenes.append(f'<section class="scene" id="{pid}" data-key="{s["key"]}">{stage}</section>')
RAMP = ["#328BFF", "#45A2FF", "#52B7FF", "#7CC8FF", "#A9DBFF", "#CCEAFF"]
film_css = """
html,body{margin:0;background:#000;overflow:hidden}
#film{position:relative;width:1920px;height:1080px;overflow:hidden;background:#120050}
.scene{position:absolute;inset:0;display:none;will-change:opacity}
.scene.on{display:block}
.scene>.stage{zoom:1.5}
.cam{position:absolute;inset:0;overflow:hidden}
.cam>.app{position:absolute;left:0;top:0;width:1280px}
#flash{position:absolute;inset:0;background:#FFFFFF;opacity:0;pointer-events:none;z-index:60}
#sting{position:absolute;inset:0;display:none;z-index:50;background:#120050;overflow:hidden;font-family:var(--f-display)}
#sting::before{content:"";position:absolute;inset:0;background:radial-gradient(1100px 760px at 85% -10%,rgba(82,183,255,.35),rgba(82,183,255,0) 62%),radial-gradient(1000px 760px at -5% 115%,rgba(27,10,176,.8),rgba(27,10,176,0) 62%)}
#sting .lt{position:absolute;left:150px;top:50%;font-weight:500;font-size:560px;line-height:1;letter-spacing:-.06em;transform-origin:left center}
#sting .nm{position:absolute;left:600px;top:50%;font-weight:500;font-size:150px;line-height:1;letter-spacing:-.045em;color:#FFFFFF}
#sting .st{position:absolute;left:606px;top:50%;font:600 26px var(--f-text);letter-spacing:.24em;text-transform:uppercase;color:#52B7FF}
#sting .bar{position:absolute;left:606px;height:6px;border-radius:3px;background:#52B7FF;top:50%}
.w{display:inline-block;white-space:pre}
.scan{position:absolute;top:0;bottom:0;width:240px;pointer-events:none;background:linear-gradient(90deg,rgba(50,139,255,0),rgba(50,139,255,.18),rgba(50,139,255,0));z-index:4}
"""
page = f"""<!doctype html><html><head><meta charset="utf-8"><title>OneSearch Hub · film</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500&display=swap">
<style>{style}{film_css}</style></head><body>
{defs}
<div id="film">{''.join(scenes)}
<div id="sting"><span class="lt"></span><span class="st"></span><span class="nm"></span><span class="bar"></span></div>
<div id="flash"></div></div>
<script>window.TIMING={json.dumps(T)};window.RAMP={json.dumps(RAMP)};</script>
<script src="lucide.js"></script>
<script src="film/engine.js"></script>
</body></html>"""
(RAC / "film.html").write_text(page)
print("film.html", len(page), "octets,", len(scenes), "scènes")
