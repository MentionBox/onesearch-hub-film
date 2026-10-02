"""Assemble les planches OneSearch Hub : remplit les marqueurs @@…@@ du gabarit avec des
SVG calculés (anneaux, graphes à l'échelle, QR factice) et des blocs répétitifs."""
import math, random, re, html, json
from pathlib import Path

ICI = Path(__file__).parent
TPL = (ICI / "template.html").read_text()
LOGO = (ICI / "logo_inner.svg").read_text()

INK, MUTED, GRID = "#120050", "#5B5878", "rgba(27,10,176,0.12)"
AXIS = "#6E6A94"
BLUE = "#328BFF"
GRAY = "#7A7F9E"
RAMP_DK = ["#328BFF", "#45A2FF", "#52B7FF", "#7CC8FF", "#A9DBFF", "#CCEAFF"]
RAMP_LT = ["#1B0AB0", "#1558AD", "#328BFF", "#52B7FF", "#7CC8FF", "#A9DBFF"]
STAGES = ["Collect", "Identify", "Recommend", "Coordinate", "Launch", "Evaluate"]
LETTERS = ["C", "I", "R", "C", "L", "E"]
TAGS = ["All your Search data. One place.", "Thousands of signals. One score.",
        "Every opportunity, turned into action.", "From recommendations to ownership.",
        "From brief to live.", "Impact you can prove."]
PLAT = {"Google": "#328BFF", "Amazon": "#B5722A", "TikTok": "#0D8F8F", "AI answers": "#6B4FE0",
        "YouTube": "#D94452", "Instagram": "#9B5FC7", "Reddit": GRAY}


def f(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def arc(cx, cy, r, a0, a1):
    x0, y0 = polar(cx, cy, r, a0)
    x1, y1 = polar(cx, cy, r, a1)
    large = 1 if (a1 - a0) > 180 else 0
    return f"M{f(x0)} {f(y0)} A{f(r)} {f(r)} 0 {large} 1 {f(x1)} {f(y1)}"


def segments(gap=6, arrow_gap=16):
    """Six arcs, Collect centré en haut. Entre Evaluate et Collect, une ouverture plus
    large où se loge la flèche du retour."""
    out = []
    for i in range(6):
        a0, a1 = -120 + 60 * i, -60 + 60 * i
        a0 += (arrow_gap * 0.35) if i == 0 else gap / 2
        a1 -= (arrow_gap * 0.65) if i == 5 else gap / 2
        out.append((a0, a1))
    return out


def ring(cx, cy, r, sw, colors, arrow=True, gap=6, arrow_gap=16):
    s = []
    segs = segments(gap, arrow_gap)
    for (a0, a1), c in zip(segs, colors):
        s.append(f'<path d="{arc(cx, cy, r, a0, a1)}" stroke="{c}" stroke-width="{sw}" fill="none"/>')
    if arrow:
        end = segs[5][1]
        tip = end + arrow_gap * 0.5
        b1, b2, t = polar(cx, cy, r - sw * 0.72, end), polar(cx, cy, r + sw * 0.72, end), polar(cx, cy, r, tip)
        s.append(f'<path d="M{f(b1[0])} {f(b1[1])} L{f(t[0])} {f(t[1])} L{f(b2[0])} {f(b2[1])} Z" fill="{colors[5]}"/>')
    return "".join(s)


# ——— logo MentionBox en symbole ———
logo = re.sub(r"<defs>.*?</defs>", "", LOGO, flags=re.S)
logo = logo.replace('fill="currentColor" class="logo_blue"', 'fill="url(#mbg)"')
logo = re.sub(r"^<svg[^>]*>", '<symbol id="mb-logo" viewBox="0 0 932 126">', logo)
logo = re.sub(r"</svg>\s*$", "</symbol>", logo)

hub = (f'<symbol id="hub-light" viewBox="0 0 40 40">{ring(20, 20, 14.5, 6, RAMP_LT, arrow=False, gap=14, arrow_gap=14)}</symbol>'
       f'<symbol id="hub-dark" viewBox="0 0 40 40">{ring(20, 20, 14.5, 6, RAMP_DK, arrow=False, gap=14, arrow_gap=14)}</symbol>')

# ——— grand anneau CIRCLE (section du document) ———
cx, cy, r = 490, 350, 205
big = [f'<svg viewBox="0 0 980 700" role="img" aria-label="Le cadre CIRCLE : Collect, Identify, Recommend, Coordinate, Launch, Evaluate, puis retour à Collect">']
big.append(ring(cx, cy, r, 40, RAMP_DK))
for i in range(6):
    mid = -90 + 60 * i
    nx, ny = polar(cx, cy, r, mid)
    big.append(f'<circle cx="{f(nx)}" cy="{f(ny)}" r="25" fill="#120050" stroke="{RAMP_DK[i]}" stroke-width="3"/>')
    big.append(f'<text x="{f(nx)}" y="{f(ny + 8)}" text-anchor="middle" fill="#FFFFFF" style="font:600 22px var(--f-display)">{LETTERS[i]}</text>')
    lx, ly = polar(cx, cy, r + 62, mid)
    c = math.cos(math.radians(mid))
    anchor = "middle" if abs(c) < 0.2 else ("start" if c > 0 else "end")
    if mid == -90:
        y1, y2 = ly - 26, ly - 6
    elif mid == 90:
        y1, y2 = ly + 14, ly + 34
    else:
        y1, y2 = ly - 2, ly + 18
    big.append(f'<text x="{f(lx)}" y="{f(y1)}" text-anchor="{anchor}" fill="#FFFFFF" style="font:500 21px var(--f-display);letter-spacing:-.02em">{STAGES[i]}</text>')
    big.append(f'<text x="{f(lx)}" y="{f(y2)}" text-anchor="{anchor}" fill="rgba(241,243,255,.7)" style="font:400 13.5px var(--f-text)">{TAGS[i]}</text>')
rx, ry = polar(cx, cy, r + 58, -128)
big.append(f'<text x="{f(rx)}" y="{f(ry)}" text-anchor="end" fill="#52B7FF" style="font:600 12px var(--f-text);letter-spacing:.14em">REPEAT ↻</text>')
big.append(f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" fill="#FFFFFF" style="font:500 50px var(--f-display);letter-spacing:-.04em">CIRCLE</text>')
big.append(f'<text x="{cx}" y="{cy + 34}" text-anchor="middle" fill="rgba(241,243,255,.7)" style="font:400 15px var(--f-text)">One Search, run end to end.</text>')
big.append("</svg>")

# ——— planche 05 : les six lettres ———
letters = "".join(
    f'<div style="width:150px;text-align:center"><p class="dsp" style="font-size:136px;line-height:1;color:{RAMP_DK[i]}">{LETTERS[i]}</p>'
    f'<p style="font-size:16px;color:rgba(241,243,255,.66);margin-top:14px">{STAGES[i]}</p></div>' for i in range(6))

# ——— planche 04 : l'orbite des plateformes ———
orb = ['<svg width="1280" height="720" style="position:absolute;inset:0"><ellipse cx="640" cy="360" rx="530" ry="282" fill="none" stroke="rgba(82,183,255,.22)" stroke-dasharray="3 7"/></svg>']
names = [("Google", PLAT["Google"]), ("ChatGPT", PLAT["AI answers"]), ("TikTok", PLAT["TikTok"]), ("Amazon", PLAT["Amazon"]),
         ("YouTube", PLAT["YouTube"]), ("Perplexity", PLAT["AI answers"]), ("Instagram", PLAT["Instagram"]),
         ("AI Overviews", PLAT["AI answers"]), ("Reddit", GRAY), ("Gemini", PLAT["AI answers"])]
for k, (n, c) in enumerate(names):
    a = -78 + k * 36
    x, y = polar(640, 360, 1, a)
    x, y = 640 + 530 * math.cos(math.radians(a)), 360 + 282 * math.sin(math.radians(a))
    op = 0.55 + 0.45 * ((k % 3) / 2)
    orb.append(f'<div class="qpill" style="left:{f(x)}px;top:{f(y)}px;transform:translate(-50%,-50%);opacity:{op:.2f};padding:7px 13px"><b><i style="--c:{c}"></i>{n}</b></div>')
orbit = "".join(orb)

# ——— planche 03 : les fragments ———
frags = [
    (0, 10, -4, "file-spreadsheet", "search-console-export.csv", "1,048,576 rows · cut off"),
    (210, 70, 3, "activity", "GA4 · Conversions", "Not linked to any search"),
    (30, 165, 2, "file-text", "Agency report_Q1.pdf", "38 pages · read by nobody"),
    (240, 230, -3, "sheet", "keywords_final_v7.xlsx", "Edited by 4 people"),
    (10, 330, -2, "message-square", "#search-team", "“Who’s doing the TikTok brief?”"),
    (220, 410, 4, "image", "chatgpt-answer.png", "Pasted into a slide"),
]
fr = []
for x, y, rot, ic, t, s in frags:
    fr.append(f'<div style="position:absolute;left:{x}px;top:{y}px;width:250px;transform:rotate({rot}deg);background:rgba(255,255,255,.07);border:1px solid rgba(241,243,255,.16);border-radius:12px;padding:12px 14px;display:flex;gap:10px;align-items:flex-start;color:#F1F3FF">'
              f'<i data-lucide="{ic}" style="font-size:18px;color:#52B7FF;margin-top:2px"></i><div><p style="font:500 14px var(--f-display);letter-spacing:-.01em">{t}</p>'
              f'<p style="font-size:12px;color:rgba(241,243,255,.6);margin-top:2px">{s}</p></div></div>')
fragments = "".join(fr)

# ——— planche 06 : sources et barres ———
sources = [
    ("Google Search Console", "Search", "1.1M signals", PLAT["Google"], "Live · 4 min ago"),
    ("MentionLab", "AI answers", "212k signals", PLAT["AI answers"], "Live · 12 min ago"),
    ("Google AI Overviews", "AI answers", "100k signals", PLAT["AI answers"], "Live · 4 min ago"),
    ("Google Analytics 4", "Web analytics", "84k conversions", GRAY, "Live · 9 min ago"),
    ("TikTok", "Social search", "288k signals", PLAT["TikTok"], "Live · 22 min ago"),
    ("YouTube", "Video search", "214k signals", PLAT["YouTube"], "Live · 22 min ago"),
    ("Instagram", "Social search", "86k signals", PLAT["Instagram"], "Live · 31 min ago"),
    ("Reddit", "Communities", "60k signals", PLAT["Reddit"], "Live · 40 min ago"),
    ("Amazon", "Marketplace", "336k signals", PLAT["Amazon"], "Live · 15 min ago"),
    ("Runner Pulse 2026", "Consumer research", "3,200 respondents", GRAY, "Uploaded 2 days ago"),
    ("Velox Members", "First-party CRM", "410k members", GRAY, "Live · 1 h ago"),
    ("velox.run", "Website crawl", "4,812 pages", GRAY, "Crawled today"),
]
src = []
for n, t, m, c, st in sources:
    src.append(f'<div class="card" style="padding:9px 11px;display:flex;flex-direction:column;gap:3px">'
               f'<p style="display:flex;align-items:center;gap:6px;font-weight:500;font-size:11.5px;line-height:1.5;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:none"><i style="width:7px;height:7px;border-radius:50%;background:{c};flex:none"></i>{n}</p>'
               f'<p style="font-size:10px;line-height:1.5;color:{MUTED};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex:none">{t}</p>'
               f'<p class="dsp num" style="font-size:15px;margin-top:2px;flex:none">{m}</p>'
               f'<p style="font-size:9.5px;color:#0a812f;display:flex;align-items:center;gap:4px"><i style="width:5px;height:5px;border-radius:50%;background:#0C9B38"></i>{st}</p></div>')
sources_html = "".join(src)

bars = [("Google", 1104), ("Amazon", 336), ("AI answers", 312), ("TikTok", 288), ("YouTube", 214), ("Instagram", 86), ("Reddit", 60)]
assert sum(v for _, v in bars) == 2400
W, rowh, lab, valw = 268, 30, 74, 46
bw = W - lab - valw
mx = max(v for _, v in bars)
cb = [f'<svg width="{W}" height="{rowh * len(bars) + 8}" style="display:block;margin-top:10px" role="img" aria-label="Signaux par plateforme">']
for i, (n, v) in enumerate(bars):
    y = 6 + i * rowh
    w = bw * v / mx
    cb.append(f'<text x="0" y="{y + 13}" fill="{INK}" style="font:400 11px var(--f-text)">{n}</text>')
    cb.append(f'<rect x="{lab}" y="{y + 4}" width="{f(bw)}" height="10" rx="3" fill="#EDEFFA"/>')
    cb.append(f'<rect x="{lab}" y="{y + 4}" width="{f(max(w, 8))}" height="10" rx="3" fill="{BLUE}"/>')
    lbl = f"{v / 1000:.1f}M" if v >= 1000 else f"{v}k"
    cb.append(f'<text x="{W}" y="{y + 13}" text-anchor="end" fill="{MUTED}" style="font:500 11px var(--f-text);font-variant-numeric:tabular-nums">{lbl}</text>')
cb.append("</svg>")
collect_bars = "".join(cb)

# ——— planche 07 : le tableau des opportunités ———
ORDER = ["Google", "AI answers", "TikTok", "YouTube", "Amazon"]
rows = [
    ("carbon plate running shoes", 182000, [38, 21, 19, 8, 14], 9, 94, "▲ 212"),
    ("marathon training plan", 246000, [44, 18, 16, 22, 0], 14, 91, "▲ 87"),
    ("running shoes for flat feet", 96000, [41, 20, 6, 10, 23], 6, 88, "▲ 340"),
    ("waterproof trail running shoes", 74000, [49, 4, 10, 10, 27], 18, 82, "▲ 45"),
    ("best running shoes for beginners", 210000, [40, 20, 14, 8, 18], 41, 71, "▼ 3"),
    ("how to choose running shoe size", 58000, [52, 26, 6, 8, 8], 33, 64, "▲ 12"),
    ("recovery shoes after a long run", 31000, [45, 6, 15, 4, 30], 22, 58, "▲ 9"),
    ("velox aero 3 review", 22000, [60, 12, 8, 10, 10], 72, 31, "▼ 6"),
]


def tier(s):
    if s >= 85: return "#093772", "High"
    if s >= 70: return "#1558AD", "Medium"
    if s >= 55: return "#2D76D4", "Medium"
    return "#8E8E8E", "Low"


cols = "26px minmax(0,1.6fr) 92px 196px 150px 96px 58px"
t = [f'<div style="display:grid;grid-template-columns:{cols};gap:12px;align-items:center;padding:8px 14px;background:#EDEFFA;font-size:10.5px;color:{MUTED}">'
     '<span>#</span><span>Search intent</span><span style="text-align:right">Demand / month</span><span>Where people search</span><span>Velox visibility</span><span>Opportunity Score</span><span style="text-align:right">Moved</span></div>']
for i, (q, d, mix, vis, sc, mv) in enumerate(rows):
    assert sum(mix) == 100, q
    seg = "".join(f'<i style="--c:{PLAT[ORDER[k]]};width:{m}%"></i>' for k, m in enumerate(mix) if m)
    bg, lab_ = tier(sc)
    up = mv.startswith("▲")
    hl = "background:rgba(50,139,255,.06);" if i == 0 else ""
    t.append(f'<div style="display:grid;grid-template-columns:{cols};gap:12px;align-items:center;padding:0 14px;height:36px;border-top:1px solid rgba(18,0,80,.08);{hl}">'
             f'<span class="num" style="color:{MUTED}">{i + 1}</span>'
             f'<span style="font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{q}</span>'
             f'<span class="num" style="text-align:right">{d:,}</span>'
             f'<div class="mix">{seg}</div>'
             f'<span style="display:flex;align-items:center;gap:8px"><span class="bar" style="flex:1;height:6px"><i style="width:{vis}%"></i></span><span class="num" style="width:28px;text-align:right">{vis}%</span></span>'
             f'<span style="display:inline-flex;align-items:center;gap:6px"><span class="num" style="background:{bg};color:#FFFFFF;font:600 12px var(--f-display);border-radius:6px;padding:2px 7px;min-width:32px;text-align:center">{sc}</span><span style="font-size:10.5px;color:{MUTED}">{lab_}</span></span>'
             f'<span class="num" style="text-align:right;font-weight:500;color:{"#0a812f" if up else "#e10000"}">{mv}</span></div>')
opp_table = "".join(t)

# ——— planche 08 : jauge, composantes, demande, visibilité ———
R, SW = 54, 12
circ = 2 * math.pi * R
gauge = (f'<svg width="132" height="132" viewBox="0 0 132 132" role="img" aria-label="Opportunity Score 94 sur 100">'
         f'<circle cx="66" cy="66" r="{R}" fill="none" stroke="#EDEFFA" stroke-width="{SW}"/>'
         f'<circle cx="66" cy="66" r="{R}" fill="none" stroke="{BLUE}" stroke-width="{SW}" stroke-linecap="round" stroke-dasharray="{f(circ * .94)} {f(circ)}" transform="rotate(-90 66 66)"/>'
         f'<text x="66" y="72" text-anchor="middle" fill="{INK}" style="font:500 38px var(--f-display);letter-spacing:-.04em">94</text>'
         f'<text x="66" y="90" text-anchor="middle" fill="{MUTED}" style="font:400 11px var(--f-text)">out of 100</text></svg>')
parts = [("Consumer demand", 96, "182,000 searches a month, +31% in a year"),
         ("Platform demand", 88, "62% of it happens outside Google: ChatGPT, TikTok, Amazon"),
         ("Visibility gap", 91, "Velox appears in 9% of results; stridelab.com in 47%")]
score_parts = "".join(
    f'<div><div class="rw"><span style="font-weight:500;font-size:12px">{n}</span><span class="sp dsp num" style="font-size:15px">{v}</span></div>'
    f'<div class="bar" style="margin-top:5px"><i style="width:{v}%"></i></div><p class="chs" style="margin-top:4px">{s}</p></div>' for n, v, s in parts)

dem = [139, 141, 144, 143, 149, 152, 157, 161, 166, 171, 176, 182]
assert round((dem[-1] / dem[0] - 1) * 100) == 31
DW, DH, L, Rr, T, B = 560, 150, 40, 30, 10, 22
pw, ph = DW - L - Rr, DH - T - B
X = lambda i: L + pw * i / (len(dem) - 1)
Y = lambda v: T + ph * (1 - v / 200)
d = [f'<svg width="{DW}" height="{DH}" style="display:block;margin-top:8px" role="img" aria-label="Demande mensuelle sur douze mois, de 139 000 à 182 000 recherches">']
for v in (0, 100, 200):
    d.append(f'<line x1="{L}" x2="{DW - Rr}" y1="{f(Y(v))}" y2="{f(Y(v))}" stroke="{GRID}" stroke-width="1"/>')
    d.append(f'<text x="{L - 8}" y="{f(Y(v) + 4)}" text-anchor="end" fill="{AXIS}" style="font:400 10px var(--f-text)">{v}k</text>')
pts = " ".join(f"{f(X(i))},{f(Y(v))}" for i, v in enumerate(dem))
d.append(f'<polygon points="{f(X(0))},{f(Y(0))} {pts} {f(X(len(dem) - 1))},{f(Y(0))}" fill="{BLUE}" fill-opacity="0.12"/>')
d.append(f'<polyline points="{pts}" fill="none" stroke="{BLUE}" stroke-width="2" stroke-linejoin="round"/>')
d.append(f'<circle cx="{f(X(11))}" cy="{f(Y(182))}" r="4.5" fill="{BLUE}" stroke="#FFFFFF" stroke-width="2"/>')
d.append(f'<text x="{f(X(11) - 8)}" y="{f(Y(182) - 9)}" text-anchor="end" fill="{INK}" style="font:500 11px var(--f-text)">182k</text>')
for i, m in [(0, "Apr"), (3, "Jul"), (6, "Oct"), (9, "Jan"), (11, "Mar")]:
    d.append(f'<text x="{f(X(i))}" y="{DH - 4}" text-anchor="middle" fill="{AXIS}" style="font:400 10px var(--f-text)">{m}</text>')
d.append("</svg>")
demand_chart = "".join(d)

vis = [("Google", 12, 47, "stridelab.com"), ("AI answers", 4, 38, "runnersguide.net"), ("TikTok", 7, 29, "@coach.jules"), ("Amazon", 15, 41, "stridelab.com")]
VW, lab, valw = 560, 78, 150
bw = VW - lab - valw
v_ = [f'<svg width="{VW}" height="{len(vis) * 32 + 4}" style="display:block;margin-top:8px" role="img" aria-label="Visibilité de Velox face au concurrent le plus visible, par plateforme">']
for i, (n, a, b, who) in enumerate(vis):
    y = 4 + i * 32
    v_.append(f'<text x="0" y="{y + 15}" fill="{INK}" style="font:400 11px var(--f-text)">{n}</text>')
    v_.append(f'<rect x="{lab}" y="{y + 3}" width="{f(max(bw * a / 50, 8))}" height="8" rx="3" fill="{BLUE}"/>')
    v_.append(f'<rect x="{lab}" y="{y + 14}" width="{f(bw * b / 50)}" height="8" rx="3" fill="{GRAY}"/>')
    v_.append(f'<text x="{f(lab + max(bw * a / 50, 8) + 6)}" y="{y + 11}" fill="{INK}" style="font:500 10.5px var(--f-text)">{a}%</text>')
    v_.append(f'<text x="{f(lab + bw * b / 50 + 6)}" y="{y + 22}" fill="{MUTED}" style="font:400 10.5px var(--f-text)">{b}% · {who}</text>')
v_.append("</svg>")
vis_bars = "".join(v_)

# ——— planche 09 : recommandations ———
reco = [
    ("Google Search", ["Google"], [
        ("t-opt", "Optimize", "/running/carbon-plate: add a fit and feel comparison", "+9,400 visits a month", "S", True),
        ("t-cre", "Create", "Guide: Is a carbon plate worth it for your first marathon?", "+6,100 visits a month", "M", True),
        ("t-tec", "Structured data", "Product and Review markup on 14 shoe pages", "Rich results on 14 pages", "S", True)]),
    ("AI answers", ["ChatGPT", "Gemini", "Perplexity"], [
        ("t-cit", "Get cited", "runnersguide.net is cited in 41% of AI answers. Pitch the Velox lab data.", "+AI citations", "M", True),
        ("t-cre", "Create", "Publish the energy-return lab test, numbers included", "+AI mentions", "M", True),
        ("t-opt", "Optimize", "Add a 6-question FAQ to the Aero 3 page", "+AI citations", "S", False)]),
    ("Social search", ["TikTok", "YouTube"], [
        ("t-cre", "Create", "3 TikToks: carbon vs foam, a 30-day test", "+210k views", "M", True),
        ("t-par", "Partner", "2 running creators already rank for this search", "1.2M reach", "M", False)]),
    ("Marketplaces", ["Amazon"], [
        ("t-opt", "Optimize", "Rewrite the Aero 3 title and bullets around carbon plate", "+12% click rate", "S", True),
        ("t-cre", "Create", "A+ comparison module: Aero 3 vs Aero 2", "+conversion rate", "S", False)]),
]
pc = {"Google": PLAT["Google"], "ChatGPT": PLAT["AI answers"], "Gemini": PLAT["AI answers"], "Perplexity": PLAT["AI answers"],
      "TikTok": PLAT["TikTok"], "YouTube": PLAT["YouTube"], "Amazon": PLAT["Amazon"]}
assert sum(len(c[2]) for c in reco) == 10
rc = []
for title, pills, items in reco:
    it = []
    for cls, typ, tt, imp, eff, on in items:
        box = (f'<span style="width:14px;height:14px;border-radius:4px;background:{BLUE};color:#FFFFFF;display:grid;place-items:center;font-size:10px"><i data-lucide="check"></i></span>'
               if on else '<span style="width:14px;height:14px;border-radius:4px;border:1.5px solid rgba(18,0,80,.25)"></span>')
        it.append(f'<div style="border:1px solid rgba(18,0,80,.10);border-radius:7px;padding:9px 10px;display:flex;flex-direction:column;gap:6px;background:#FFFFFF">'
                  f'<div class="rw"><span class="chip {cls}">{typ}</span><span class="sp">{box}</span></div>'
                  f'<p style="font-weight:500;font-size:11.5px;line-height:1.35">{tt}</p>'
                  f'<p style="font-size:10.5px;color:{MUTED};display:flex;gap:8px"><span class="up" style="font-weight:500">{imp}</span><span>Effort {eff}</span></p></div>')
    pl = "".join(f'<span class="pl" style="height:18px;font-size:10px"><i style="--c:{pc[p]}"></i>{p}</span>' for p in pills)
    rc.append(f'<div class="card" style="padding:12px;display:flex;flex-direction:column;gap:8px;background:#FBFBFF">'
              f'<p class="cht">{title}</p><div style="display:flex;gap:4px;flex-wrap:wrap">{pl}</div>{"".join(it)}</div>')
reco_cols = "".join(rc)

# ——— planche 10 : plan d'action ———
P = {"MC": ("Maya Chen", "#328BFF"), "TP": ("Tom Peeters", "#6B4FE0"), "ID": ("Inès Diallo", "#0D8F8F"),
     "KP": ("Kestrel PR", "#B5722A"), "LM": ("Lucas Martin", "#D94452"), "NH": ("Nora Haddad", "#9B5FC7")}
av = lambda k: f'<span class="av" style="background:{P[k][1]}">{k}</span>'
avatars = "".join(av(k) for k in ["MC", "TP", "ID", "NH", "LM", "KP"])
STS = {"todo": ("s-todo", "To do"), "prog": ("s-prog", "In progress"), "rev": ("s-rev", "In review"), "done": ("s-done", "Done")}
board = [
    ("SEO", "MC", 9, [("prog", "Product and Review markup · 14 pages", "MC", "2 May"), ("rev", "Optimize /running/carbon-plate", "MC", "4 May")]),
    ("Content", "TP", 11, [("prog", "Guide: Is a carbon plate worth it for your first marathon?", "TP", "6 May", True),
                           ("todo", "Publish the energy-return lab test", "NH", "7 May"), ("todo", "FAQ block · Aero 3 page", None, "10 May")]),
    ("Social", "ID", 8, [("prog", "3 TikToks: carbon vs foam", "ID", "5 May"), ("done", "Creator brief × 2", "ID", "24 Apr")]),
    ("PR", "KP", 6, [("rev", "Expert quotes for AI answers", "KP", "7 May"), ("todo", "Pitch the lab data to runnersguide.net", "KP", "12 May")]),
    ("E-commerce", "LM", 8, [("done", "Amazon title and bullets · Aero 3", "LM", "22 Apr"), ("prog", "A+ comparison module", "LM", "8 May")]),
]
assert sum(c[2] for c in board) == 42
bd = []
for name, lead, n, cards in board:
    cs = []
    for c in cards:
        st, tt, who, due = c[0], c[1], c[2], c[3]
        new = len(c) > 4
        cl, lb = STS[st]
        owner = (f'{av(who)}<span style="font-size:10.5px">{P[who][0]}</span>' if who else
                 '<span class="av" style="background:#FFFFFF;border:1.5px dashed rgba(18,0,80,.3);color:#5B5878">?</span><span style="font-size:10.5px;color:#7A4A00">Needs an owner</span>')
        ring_ = "box-shadow:0 0 0 2px #328BFF,0 10px 24px -12px rgba(27,10,176,.45);" if new else ""
        flag = '<span class="chip t-opt" style="height:16px;font-size:9.5px">New</span>' if new else ""
        cs.append(f'<div style="background:#FFFFFF;border:1px solid rgba(18,0,80,.10);border-radius:7px;padding:9px 10px;display:flex;flex-direction:column;gap:7px;{ring_}">'
                  f'<div class="rw"><span class="chip {cl}">{lb}</span>{flag}<span class="sp" style="font-size:10px;color:{MUTED}">{due}</span></div>'
                  f'<p style="font-weight:500;font-size:11.5px;line-height:1.35">{tt}</p>'
                  f'<div class="rw" style="gap:6px">{owner}<span class="sp" style="font-size:9.5px;color:{MUTED};display:flex;align-items:center;gap:3px"><i data-lucide="target"></i>94</span></div></div>')
    bd.append(f'<div style="background:#EDEFFA;border-radius:8px;padding:8px;display:flex;flex-direction:column;gap:7px;min-width:0">'
              f'<div class="rw" style="padding:2px 2px 4px"><span class="cht">{name}</span><span class="num" style="font-size:10.5px;color:{MUTED}">{n}</span><span class="sp">{av(lead)}</span></div>{"".join(cs)}</div>')
bd.append('<div class="card" style="position:absolute;left:330px;top:64px;width:196px;padding:8px;box-shadow:0 18px 40px -12px rgba(18,0,80,.35);z-index:3">'
          f'<p class="eb" style="padding:2px 4px 6px">Assign to</p>'
          f'<div class="rw" style="padding:5px 4px;border-radius:5px;background:rgba(50,139,255,.10)">{av("TP")}<span style="font-size:11px;font-weight:500">Tom Peeters</span><span class="sp" style="color:#1B0AB0;font-size:12px"><i data-lucide="check"></i></span></div>'
          f'<div class="rw" style="padding:5px 4px">{av("NH")}<span style="font-size:11px">Nora Haddad</span><span class="sp" style="font-size:9.5px;color:{MUTED}">Content</span></div>'
          f'<div class="rw" style="padding:5px 4px">{av("KP")}<span style="font-size:11px">Kestrel PR</span><span class="sp" style="font-size:9.5px;color:{MUTED}">Agency</span></div></div>')
board_html = "".join(bd)

# ——— planche 11 : production ———
steps = [("Recommendation", "Score 94", "done"), ("Brief", "Generated, edited by Tom", "done"), ("Draft", "1,640 words", "done"),
         ("Approval", "Maya Chen", "cur"), ("Live", "12 May, 09:00", "next")]
sp = []
for i, (n, s, k) in enumerate(steps):
    if k == "done":
        dot = f'<span style="width:22px;height:22px;border-radius:50%;background:{BLUE};color:#FFFFFF;display:grid;place-items:center;font-size:12px;flex:none"><i data-lucide="check"></i></span>'
    elif k == "cur":
        dot = '<span style="width:22px;height:22px;border-radius:50%;border:2px solid #1B0AB0;display:grid;place-items:center;flex:none"><span style="width:8px;height:8px;border-radius:50%;background:#1B0AB0"></span></span>'
    else:
        dot = '<span style="width:22px;height:22px;border-radius:50%;border:1.5px solid rgba(18,0,80,.25);flex:none"></span>'
    sp.append(f'<div style="display:flex;align-items:center;gap:9px;flex:none">{dot}<div><p style="font-weight:{600 if k == "cur" else 500};font-size:12px">{n}</p><p style="font-size:10px;color:{MUTED}">{s}</p></div></div>')
    if i < len(steps) - 1:
        sp.append(f'<span style="flex:1;height:2px;border-radius:2px;background:{BLUE if k == "done" else "rgba(18,0,80,.14)"};margin:0 12px"></span>')
stepper = f'<div style="display:flex;align-items:center">{"".join(sp)}</div>'

chk = lambda t_: f'<p style="display:flex;gap:6px;align-items:center;font-size:11px"><span style="color:#0a812f;font-size:12px"><i data-lucide="circle-check"></i></span>{t_}</p>'
lines = lambda n, w=100: "".join(f'<span style="display:block;height:6px;border-radius:3px;background:#EDEFFA;width:{w - (k * 7) % 23}%;margin-top:7px"></span>' for k in range(n))
launch_panels = (
    '<div class="card" style="display:flex;flex-direction:column;gap:9px">'
    f'<div class="rw"><p class="cht">Brief</p><span class="sp chip t-cre"><i data-lucide="sparkles"></i>Drafted by the Hub</span></div>'
    f'<div style="display:grid;grid-template-columns:62px 1fr;gap:5px 8px;font-size:11px"><span style="color:{MUTED}">Target</span><span style="font-weight:500">carbon plate running shoes · 94</span>'
    f'<span style="color:{MUTED}">Reader</span><span>First-time marathoners</span><span style="color:{MUTED}">Angle</span><span>An honest answer, with our lab numbers</span></div>'
    f'<div style="border-top:1px solid rgba(18,0,80,.10);padding-top:8px"><p class="eb">Outline</p>'
    '<ol style="margin:5px 0 0;padding-left:16px;font-size:11px;line-height:1.55"><li>What a carbon plate actually does</li><li>Who it helps, and who it doesn’t</li><li>Lab test: Aero 3 vs foam</li><li>How to choose your first pair</li></ol></div>'
    f'<div style="border-top:1px solid rgba(18,0,80,.10);padding-top:8px;display:flex;flex-direction:column;gap:4px"><p class="eb" style="margin-bottom:2px">To be cited by AI answers</p>'
    f'{chk("6-question FAQ block")}{chk("Product and Article schema")}{chk("3 stats, each with its source")}</div></div>'
    '<div class="card" style="padding:0;overflow:hidden;display:flex;flex-direction:column">'
    '<div style="height:28px;background:#EDEFFA;display:flex;align-items:center;gap:6px;padding:0 10px;border-bottom:1px solid rgba(18,0,80,.08)">'
    '<i style="width:7px;height:7px;border-radius:50%;background:#D5D3E6"></i><i style="width:7px;height:7px;border-radius:50%;background:#D5D3E6"></i><i style="width:7px;height:7px;border-radius:50%;background:#D5D3E6"></i>'
    f'<span style="margin-left:8px;font:10.5px var(--f-mono);color:{MUTED}">velox.run/journal/carbon-plate-first-marathon</span><span class="sp chip s-rev">Draft</span></div>'
    '<div style="padding:14px 22px;display:flex;flex-direction:column;gap:8px">'
    f'<p class="eb">Velox Journal · Training</p>'
    '<p class="dsp" style="font-size:21px;line-height:1.15">Is a carbon plate worth it for your first marathon?</p>'
    f'<p style="font-size:10.5px;color:{MUTED}">Tom Peeters · 7 min read</p>'
    '<div style="height:92px;border-radius:8px;background:linear-gradient(120deg,#120050 0%,#1B0AB0 45%,#52B7FF 100%);position:relative;overflow:hidden">'
    '<span style="position:absolute;left:18px;bottom:12px;font:500 20px var(--f-display);color:#FFFFFF;letter-spacing:-.02em">Aero 3</span>'
    '<span style="position:absolute;right:-20px;top:-30px;width:150px;height:150px;border-radius:50%;border:14px solid rgba(204,234,255,.35)"></span></div>'
    '<p style="font-size:11.5px;line-height:1.5">Short answer: yes, if you run your long runs at goal pace. A carbon plate stiffens the sole and returns energy late in the stride, which is when tired legs need it most.</p>'
    f'<div style="border-left:3px solid {BLUE};padding:4px 10px;background:rgba(50,139,255,.06);border-radius:0 6px 6px 0"><p class="dsp" style="font-size:16px">+4.1% running economy</p><p style="font-size:10px;color:{MUTED}">Velox lab test, 24 runners, Aero 3 vs a foam trainer</p></div>'
    f'<div>{lines(3)}</div></div></div>'
    '<div class="card" style="display:flex;flex-direction:column;gap:10px">'
    '<div class="rw"><p class="cht">Approval</p><span class="sp chip s-rev">Waiting</span></div>'
    f'<div class="rw" style="gap:8px">{av("MC")}<div><p style="font-size:11.5px;font-weight:500">Maya Chen</p><p style="font-size:10px;color:{MUTED}">SEO lead</p></div></div>'
    f'<p style="font-size:10.5px;color:{MUTED};display:flex;gap:5px;align-items:center"><i data-lucide="message-square"></i>2 comments, both resolved</p>'
    '<span class="btn btn-p" style="justify-content:center;background:#0C9B38"><i data-lucide="check"></i>Approve</span>'
    '<span class="btn btn-o" style="justify-content:center">Request changes</span>'
    f'<div style="border-top:1px solid rgba(18,0,80,.10);padding-top:10px;display:flex;flex-direction:column;gap:5px;font-size:11px">'
    f'<p class="eb">Publish</p><p style="display:flex;gap:6px;align-items:center"><i data-lucide="globe"></i>velox.run · Shopify</p>'
    f'<p style="display:flex;gap:6px;align-items:center"><i data-lucide="calendar"></i>12 May, 09:00</p>'
    f'<p style="display:flex;gap:6px;align-items:center;color:{MUTED}"><i data-lucide="send"></i>Ships with 3 TikToks and Amazon listing v2</p></div></div>'
)

# ——— planche 12 : impact ———
conv = [148, 152, 150, 147, 153, 151, 149, 155, 158, 162, 169, 174, 178,
        186, 191, 200, 207, 211, 215, 220, 223, 227, 230, 233, 236, 240]
prev, last = sum(conv[:13]), sum(conv[13:])
pct = round((last / prev - 1) * 100)
assert pct == 38, pct


def spark(vals, w=78, h=26):
    lo, hi = min(vals), max(vals)
    xs = [2 + (w - 6) * i / (len(vals) - 1) for i in range(len(vals))]
    ys = [h - 3 - (h - 7) * (v - lo) / (hi - lo) for v in vals]
    p_ = " ".join(f"{f(x)},{f(y)}" for x, y in zip(xs, ys))
    return (f'<svg width="{w}" height="{h}" style="display:block" aria-hidden="true"><polyline points="{p_}" fill="none" stroke="{BLUE}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle cx="{f(xs[-1])}" cy="{f(ys[-1])}" r="3" fill="{BLUE}"/></svg>')


monthly = [sum(conv[i:i + 4]) for i in range(0, 24, 4)]
kpis = [
    ("Visibility share", "27%", "from 10% in February, ×2.7", [10, 11, 13, 18, 23, 27]),
    ("Search traffic", "79.1k", '<span class="up">+64%</span> vs the previous 90 days', [48.2, 50, 57, 66, 73, 79.1]),
    ("Conversions from Search", f"{last:,}", f'<span class="up">+{pct}%</span> vs the previous 90 days ({prev:,})', monthly),
    ("AI answers citing Velox", "22%", "from 4% in February", [4, 5, 8, 14, 19, 22]),
]
eval_kpis = "".join(
    f'<div class="card kpi" style="display:flex;justify-content:space-between;align-items:flex-end;gap:8px"><div><p class="l">{l}</p><p class="n">{n}</p><p class="s">{s}</p></div>{spark(v)}</div>'
    for l, n, s, v in kpis)

CW, CH, L, Rr, T, B = 590, 262, 34, 12, 44, 22
pw, ph = CW - L - Rr, CH - T - B
X = lambda i: L + pw * i / (len(conv) - 1)
Y = lambda v: T + ph * (1 - v / 250)
c = [f'<svg width="{CW}" height="{CH}" style="display:block;margin-top:6px" role="img" aria-label="Conversions hebdomadaires venues de la recherche, de 148 à 236, avec quatre actions marquées">']
for v in (0, 50, 100, 150, 200, 250):
    c.append(f'<line x1="{L}" x2="{CW - Rr}" y1="{f(Y(v))}" y2="{f(Y(v))}" stroke="{GRID}"/>')
    c.append(f'<text x="{L - 7}" y="{f(Y(v) + 3.5)}" text-anchor="end" fill="{AXIS}" style="font:400 10px var(--f-text)">{v}</text>')
pts = " ".join(f"{f(X(i))},{f(Y(v))}" for i, v in enumerate(conv))
c.append(f'<polygon points="{f(X(0))},{f(Y(0))} {pts} {f(X(25))},{f(Y(0))}" fill="{BLUE}" fill-opacity="0.10"/>')
flags = [(7, "Amazon listing v2", "end", 0), (9, "3 TikToks live", "start", 1), (10, "Guide live", "start", 0), (14, "Cited in ChatGPT", "start", 0)]
for i, txt, anc, rowi in flags:
    x = X(i)
    ty = 12 + rowi * 16
    c.append(f'<line x1="{f(x)}" x2="{f(x)}" y1="{ty + 4}" y2="{f(Y(0))}" stroke="#1B0AB0" stroke-opacity="0.35" stroke-dasharray="3 3"/>')
    tx = x - 4 if anc == "end" else x + 4
    c.append(f'<text x="{f(tx)}" y="{ty + 3}" text-anchor="{anc}" fill="{INK}" style="font:500 10px var(--f-text)">{txt}</text>')
c.append(f'<polyline points="{pts}" fill="none" stroke="{BLUE}" stroke-width="2" stroke-linejoin="round"/>')
for i, *_ in flags:
    c.append(f'<circle cx="{f(X(i))}" cy="{f(Y(conv[i]))}" r="4" fill="#FFFFFF" stroke="#1B0AB0" stroke-width="2"/>')
c.append(f'<circle cx="{f(X(25))}" cy="{f(Y(conv[25]))}" r="4.5" fill="{BLUE}" stroke="#FFFFFF" stroke-width="2"/>')
c.append(f'<text x="{f(X(25) - 8)}" y="{f(Y(conv[25]) - 9)}" text-anchor="end" fill="{INK}" style="font:500 11px var(--f-text)">{conv[25]} a week</text>')
for i, m in [(0, "Mar"), (4, "Apr"), (9, "May"), (13, "Jun"), (17, "Jul"), (22, "Aug")]:
    c.append(f'<text x="{f(X(i))}" y="{CH - 5}" text-anchor="{"start" if i == 0 else "middle"}" fill="{AXIS}" style="font:400 10px var(--f-text)">{m}</text>')
c.append("</svg>")
conv_chart = "".join(c)

db = [("Google", 12, 31), ("AI answers", 4, 22), ("TikTok", 7, 19), ("Amazon", 15, 34), ("YouTube", 5, 14)]
weights = {"Google": .46, "Amazon": .14, "AI answers": .13, "TikTok": .12, "YouTube": .09}
before = sum(weights[n] * a for n, a, _ in db) / sum(weights.values())
after = sum(weights[n] * b for n, _, b in db) / sum(weights.values())
assert round(before) == 10 and round(after) == 27, (before, after)
DBW, L, Rr = 352, 76, 34
pw = DBW - L - Rr
Xd = lambda v: L + pw * v / 40
dd = [f'<svg width="{DBW}" height="{len(db) * 40 + 56}" style="display:block;margin-top:6px" role="img" aria-label="Visibilité par plateforme, février contre août">',
      f'<g style="font:400 10.5px var(--f-text)"><circle cx="{L}" cy="9" r="4" fill="{GRAY}"/><text x="{L + 8}" y="13" fill="{MUTED}">February</text>'
      f'<circle cx="{L + 76}" cy="9" r="4" fill="{BLUE}"/><text x="{L + 84}" y="13" fill="{MUTED}">August</text></g>']
for i, (n, a, b) in enumerate(db):
    y = 42 + i * 40
    dd.append(f'<text x="0" y="{y + 4}" fill="{INK}" style="font:400 11px var(--f-text)">{n}</text>')
    dd.append(f'<line x1="{f(Xd(a))}" x2="{f(Xd(b))}" y1="{y}" y2="{y}" stroke="{BLUE}" stroke-opacity="0.4" stroke-width="3"/>')
    dd.append(f'<circle cx="{f(Xd(a))}" cy="{y}" r="5" fill="{GRAY}" stroke="#FFFFFF" stroke-width="2"/>')
    dd.append(f'<circle cx="{f(Xd(b))}" cy="{y}" r="5.5" fill="{BLUE}" stroke="#FFFFFF" stroke-width="2"/>')
    dd.append(f'<text x="{f(Xd(b) + 10)}" y="{y + 4}" fill="{INK}" style="font:500 10.5px var(--f-text)">{b}%</text>')
yb = 42 + len(db) * 40 - 12
for v in (0, 10, 20, 30, 40):
    dd.append(f'<text x="{f(Xd(v))}" y="{yb + 12}" text-anchor="middle" fill="{AXIS}" style="font:400 10px var(--f-text)">{v}%</text>')
dd.append("</svg>")
dumbbell = "".join(dd)

# ——— planche 13 : la boucle ———
ccx, ccy = 640, 352
lp = ['<svg width="1280" height="720" style="position:absolute;inset:0" aria-hidden="true">', ring(ccx, ccy, 150, 18, RAMP_DK), "</svg>"]
thumbs = ["@@ID:collect@@", "@@ID:score@@", "@@ID:recommend@@", "@@ID:coordinate@@", "@@ID:launch@@", "@@ID:evaluate@@"]
TW, TH = 208, 117
for i, pid in enumerate(thumbs):
    a = -90 + 60 * i
    x = ccx + 410 * math.cos(math.radians(a))
    y = ccy + 245 * math.sin(math.radians(a))
    lp.append(f'<div data-thumb="{pid}" data-w="{TW}" style="position:absolute;left:{f(x - TW / 2)}px;top:{f(y - TH / 2)}px;width:{TW}px;height:{TH}px;border-radius:8px;overflow:hidden;border:1px solid rgba(241,243,255,.28);box-shadow:0 18px 40px -16px rgba(0,0,0,.6);background:#F7F8FF"></div>')
    lp.append(f'<p class="dsp" style="position:absolute;left:{f(x - 100)}px;width:200px;top:{f(y + TH / 2 + 8)}px;text-align:center;font-size:16px;color:{RAMP_DK[i]}">{LETTERS[i]} · {STAGES[i]}</p>')
lp.append(f'<div style="position:absolute;left:{ccx - 125}px;top:{ccy - 70}px;width:250px;text-align:center">'
          '<p class="dsp" style="font-size:40px;line-height:1;color:#FFFFFF">CIRCLE</p>'
          '<p style="font-size:12.5px;line-height:1.5;color:rgba(241,243,255,.72);margin-top:12px">Collect. Identify. Recommend.<br>Coordinate. Launch. Evaluate.</p>'
          '<p class="dsp" style="font-size:24px;color:#52B7FF;margin-top:8px">Repeat.</p></div>')
loop = "".join(lp)

# ——— planche 15 : QR factice ———
random.seed(7)
N, M = 29, 7
q = [[0] * N for _ in range(N)]
for i in range(N):
    for j in range(N):
        q[i][j] = 1 if random.random() < 0.48 else 0
def finder(r0, c0):
    for i in range(-1, 8):
        for j in range(-1, 8):
            ii, jj = r0 + i, c0 + j
            if 0 <= ii < N and 0 <= jj < N:
                edge = i in (0, 6) or j in (0, 6)
                core = 2 <= i <= 4 and 2 <= j <= 4
                q[ii][jj] = 1 if (0 <= i <= 6 and 0 <= j <= 6 and (edge or core)) else 0
for r0, c0 in [(0, 0), (0, N - 7), (N - 7, 0)]:
    finder(r0, c0)
qr = [f'<svg width="{N * M}" height="{N * M}" viewBox="0 0 {N * M} {N * M}" role="img" aria-label="Code QR factice, à remplacer"><rect width="100%" height="100%" fill="#FFFFFF"/>']
for i in range(N):
    for j in range(N):
        if q[i][j]:
            qr.append(f'<rect x="{j * M}" y="{i * M}" width="{M}" height="{M}" fill="#120050"/>')
qr.append("</svg>")
qr_html = "".join(qr)

# ——— planche « One screen » : visibilité par plateforme et cercle du trimestre ———
ov = [("Google", 12, 34, "stridelab.com"), ("Amazon", 15, 38, "stridelab.com"), ("AI answers", 4, 29, "runnersguide.net"),
      ("TikTok", 7, 22, "@coach.jules"), ("YouTube", 5, 18, "peakform.com"), ("Instagram", 9, 19, "peakform.com"), ("Reddit", 2, 11, "stridelab.com")]
OW, lab, rgt = 540, 78, 170
bw = OW - lab - rgt
Xo = lambda v: lab + bw * v / 40
o = [f'<svg width="{OW}" height="{len(ov) * 32 + 22}" style="display:block;margin-top:8px" role="img" aria-label="Visibilité de Velox par plateforme, face au leader de chaque plateforme">']
for v in (0, 10, 20, 30, 40):
    o.append(f'<line x1="{f(Xo(v))}" x2="{f(Xo(v))}" y1="2" y2="{len(ov) * 32 + 2}" stroke="{GRID}"/>')
    o.append(f'<text x="{f(Xo(v))}" y="{len(ov) * 32 + 17}" text-anchor="middle" fill="{AXIS}" style="font:400 10px var(--f-text)">{v}%</text>')
for i, (n, a, b, who) in enumerate(ov):
    y = 8 + i * 32
    o.append(f'<text x="0" y="{y + 9}" fill="{INK}" style="font:400 11px var(--f-text)">{n}</text>')
    o.append(f'<rect x="{lab}" y="{y}" width="{f(max(Xo(a) - lab, 8))}" height="12" rx="3" fill="{PLAT[n]}"/>')
    o.append(f'<text x="{f(Xo(a) + 6)}" y="{y + 10}" fill="{INK}" style="font:600 10.5px var(--f-text)">{a}%</text>')
    o.append(f'<rect x="{f(Xo(b) - 1.5)}" y="{y - 4}" width="3" height="20" rx="1.5" fill="{INK}"/>')
    o.append(f'<text x="{f(OW)}" y="{y + 10}" text-anchor="end" fill="{MUTED}" style="font:400 10.5px var(--f-text)">leader {b}% · {who}</text>')
o.append("</svg>")
overview_bars = "".join(o)

oc = [("C", "Collect", "12 sources live", "done"), ("I", "Identify", "38 opportunities", "done"), ("R", "Recommend", "10 actions ready", "cur"),
      ("C", "Coordinate", "Next", "next"), ("L", "Launch", "Not started", "next"), ("E", "Evaluate", "Baseline set", "next")]
tiles = []
for i, (l_, n, st, k) in enumerate(oc):
    bd_ = "border:1.5px solid #328BFF;background:rgba(50,139,255,.06)" if k == "cur" else "border:1px solid rgba(18,0,80,.10)"
    tick = '<span style="margin-left:auto;color:#0a812f;font-size:12px"><i data-lucide="circle-check"></i></span>' if k == "done" else ""
    tiles.append(f'<div style="{bd_};border-radius:7px;padding:7px 9px;display:flex;flex-direction:column;gap:2px">'
                 f'<p style="display:flex;align-items:center;gap:6px"><span style="width:18px;height:18px;border-radius:50%;background:{RAMP_LT[i]};color:#FFFFFF;display:grid;place-items:center;font:600 9.5px var(--f-display)">{l_}</span><b style="font-weight:500;font-size:11.5px">{n}</b>{tick}</p>'
                 f'<p style="font-size:10px;color:{MUTED}">{st}</p></div>')
overview_circle = f'<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin-top:8px">{"".join(tiles)}</div>'

# ——— planche « inside an AI answer » : sources citées ———
srcs = [("runnersguide.net", 41), ("stridelab.com", 33), ("reddit.com", 22), ("peakform.com", 18), ("youtube.com", 12), ("velox.run", 0)]
AW, lab, valw = 420, 112, 40
bw = AW - lab - valw
s_ = [f'<svg width="{AW}" height="{len(srcs) * 26 + 6}" style="display:block;margin-top:8px" role="img" aria-label="Part des réponses IA qui citent chaque source">']
for i, (n, v) in enumerate(srcs):
    y = 4 + i * 26
    me = n == "velox.run"
    s_.append(f'<text x="0" y="{y + 12}" fill="{INK}" style="font:{600 if me else 400} 11px var(--f-mono)">{n}</text>')
    s_.append(f'<rect x="{lab}" y="{y + 3}" width="{f(bw)}" height="10" rx="3" fill="#EDEFFA"/>')
    if v:
        s_.append(f'<rect x="{lab}" y="{y + 3}" width="{f(bw * v / 50)}" height="10" rx="3" fill="{PLAT["AI answers"]}"/>')
    s_.append(f'<text x="{AW}" y="{y + 12}" text-anchor="end" fill="{"#e10000" if me else INK}" style="font:{600 if me else 500} 11px var(--f-text)">{v}%</text>')
s_.append("</svg>")
ai_sources = "".join(s_)

# ——— planche « timeline » : le planning de la taskforce ———
import datetime as dt
D0 = dt.date(2026, 4, 20)
day = lambda s_: (dt.datetime.strptime(s_ + " 2026", "%b %d %Y").date() - D0).days
TEAMS = {"SEO": "#328BFF", "Content": "#6B4FE0", "Social": "#0D8F8F", "PR": "#B5722A", "E-commerce": "#D94452"}
gantt_rows = [
    ("SEO", "Product and Review markup · 14 pages", "MC", "Apr 22", "May 2", "prog"),
    ("SEO", "Optimize /running/carbon-plate", "MC", "Apr 24", "May 4", "rev"),
    ("Content", "Guide: carbon plate, first marathon", "TP", "Apr 27", "May 6", "prog"),
    ("Content", "Energy-return lab test", "NH", "May 2", "May 7", "todo"),
    ("Content", "FAQ block · Aero 3 page", None, "May 7", "May 10", "todo"),
    ("Social", "Creator brief × 2", "ID", "Apr 20", "Apr 24", "done"),
    ("Social", "3 TikToks: carbon vs foam", "ID", "Apr 28", "May 5", "prog"),
    ("PR", "Expert quotes for AI answers", "KP", "Apr 30", "May 7", "rev"),
    ("PR", "Pitch lab data to runnersguide.net", "KP", "May 7", "May 12", "todo"),
    ("E-commerce", "Amazon title and bullets · Aero 3", "LM", "Apr 20", "Apr 22", "done"),
    ("E-commerce", "A+ comparison module", "LM", "Apr 29", "May 8", "prog"),
]
GW, LX, PX0, PX1, HDR, RH, GH = 1040, 16, 300, 1022, 34, 27, 22
NDAYS = 27
pxd = (PX1 - PX0) / NDAYS
Xg = lambda d: PX0 + d * pxd
TODAY, LAUNCH = day("May 1"), day("May 12")
rows_y, y = [], HDR
prev_team = None
for r in gantt_rows:
    if r[0] != prev_team:
        rows_y.append(("team", r[0], y)); y += GH; prev_team = r[0]
    rows_y.append(("task", r, y)); y += RH
GHT = y + 8
g = [f'<svg width="{GW}" height="{GHT}" style="display:block" role="img" aria-label="Planning de la taskforce Carbon Season, du 20 avril au 16 mai">',
     '<defs><marker id="g-arr" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#120050"/></marker></defs>',
     f'<rect x="0" y="0" width="{GW}" height="{HDR}" fill="#EDEFFA"/>',
     f'<text x="{LX}" y="22" fill="{MUTED}" style="font:400 10.5px var(--f-text)">Task and owner</text>']
for k in range(0, NDAYS, 7):
    x = Xg(k)
    lbl = (D0 + dt.timedelta(days=k)).strftime("%b %-d")
    g.append(f'<line x1="{f(x)}" x2="{f(x)}" y1="{HDR}" y2="{GHT}" stroke="{GRID}"/>')
    g.append(f'<text x="{f(x + 5)}" y="22" fill="{MUTED}" style="font:400 10.5px var(--f-text)">{lbl}</text>')
for kind, r, yy in rows_y:
    if kind == "team":
        g.append(f'<rect x="0" y="{yy}" width="{GW}" height="{GH}" fill="#FBFBFF"/>')
        g.append(f'<rect x="{LX}" y="{yy + 7}" width="8" height="8" rx="2" fill="{TEAMS[r]}"/>')
        g.append(f'<text x="{LX + 14}" y="{yy + 15}" fill="{INK}" style="font:600 10px var(--f-text);letter-spacing:.06em">{r.upper()}</text>')
        continue
    team, task, who, a, b, stt = r
    c = TEAMS[team]
    cy = yy + RH / 2
    if who:
        g.append(f'<circle cx="{LX + 9}" cy="{f(cy)}" r="9" fill="{P[who][1]}"/>')
        g.append(f'<text x="{LX + 9}" y="{f(cy + 3)}" text-anchor="middle" fill="#FFFFFF" style="font:600 7.5px var(--f-text)">{who}</text>')
    else:
        g.append(f'<circle cx="{LX + 9}" cy="{f(cy)}" r="8.5" fill="#FFFFFF" stroke="rgba(18,0,80,.3)" stroke-dasharray="2 2"/>')
        g.append(f'<text x="{LX + 9}" y="{f(cy + 3.5)}" text-anchor="middle" fill="{MUTED}" style="font:600 9px var(--f-text)">?</text>')
    g.append(f'<text x="{LX + 26}" y="{f(cy + 4)}" fill="{INK}" style="font:400 11px var(--f-text)">{task}</text>')
    x0, x1 = Xg(day(a)), Xg(day(b) + 1)
    bh = 14
    by = cy - bh / 2
    if stt == "done":
        g.append(f'<rect x="{f(x0)}" y="{f(by)}" width="{f(x1 - x0)}" height="{bh}" rx="4" fill="{c}"/>')
        g.append(f'<text x="{f(x1 + 6)}" y="{f(cy + 3.5)}" fill="#0a812f" style="font:500 10px var(--f-text)">Done</text>')
    elif stt == "todo":
        g.append(f'<rect x="{f(x0)}" y="{f(by)}" width="{f(x1 - x0)}" height="{bh}" rx="4" fill="{c}" fill-opacity="0.14" stroke="{c}" stroke-opacity="0.6"/>')
    else:
        xt = min(max(Xg(TODAY + 1), x0), x1)
        g.append(f'<rect x="{f(x0)}" y="{f(by)}" width="{f(x1 - x0)}" height="{bh}" rx="4" fill="{c}" fill-opacity="0.3"/>')
        g.append(f'<rect x="{f(x0)}" y="{f(by)}" width="{f(xt - x0)}" height="{bh}" rx="4" fill="{c}"/>')
        if stt == "rev":
            g.append(f'<text x="{f(x1 - 6)}" y="{f(cy + 3.5)}" text-anchor="end" fill="#120050" style="font:600 9.5px var(--f-text)">In review</text>')
# dépendances : test de labo → pitch presse, guide → lancement
yo = {r[1]: yy + RH / 2 for kind, r, yy in rows_y if kind == "task"}
xa, ya = Xg(day("May 7") + 1), yo["Energy-return lab test"]
xb, yb_ = Xg(day("May 7")), yo["Pitch lab data to runnersguide.net"]
g.append(f'<path d="M{f(xa)} {f(ya)} h8 V{f(yb_ - 11)} H{f(xb + 6)} V{f(yb_ - 8)}" fill="none" stroke="#120050" stroke-width="1.3" marker-end="url(#g-arr)"/>')
xg_, yg_ = Xg(day("May 6") + 1), yo["Guide: carbon plate, first marathon"]
g.append(f'<path d="M{f(xg_)} {f(yg_)} H{f(Xg(LAUNCH) - 7)}" fill="none" stroke="#120050" stroke-width="1.3" stroke-dasharray="3 3" marker-end="url(#g-arr)"/>')
xt_ = Xg(TODAY + 0.5)
g.append(f'<line x1="{f(xt_)}" x2="{f(xt_)}" y1="{HDR - 2}" y2="{GHT}" stroke="#328BFF" stroke-width="2"/>')
g.append(f'<rect x="{f(xt_ - 22)}" y="{HDR - 14}" width="44" height="16" rx="8" fill="#328BFF"/><text x="{f(xt_)}" y="{HDR - 2.5}" text-anchor="middle" fill="#FFFFFF" style="font:600 9.5px var(--f-text)">Today</text>')
xl = Xg(LAUNCH)
g.append(f'<line x1="{f(xl)}" x2="{f(xl)}" y1="{HDR}" y2="{GHT}" stroke="#1B0AB0" stroke-width="1.5" stroke-dasharray="4 3"/>')
g.append(f'<path d="M{f(xl)} {f(yg_ - 9)} l9 9 l-9 9 l-9 -9 Z" fill="#1B0AB0"/>')
g.append(f'<text x="{f(xl + 14)}" y="{f(yg_ + 4)}" fill="#1B0AB0" style="font:600 11px var(--f-display)">Launch · 12 May</text>')
g.append("</svg>")
gantt = "".join(g)

# ——— planche « one action, traced » ———
pos = [18, 18, 17, 17, 16, 16, 15, 15, 14, 14, 14, 11, 8, 6, 5, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3]
assert len(pos) == 26 and pos[9] == 14 and pos[-1] == 3
PW, PH, L, Rr, T, B = 580, 196, 30, 16, 24, 22
pw, ph = PW - L - Rr, PH - T - B
Xp = lambda i: L + pw * i / (len(pos) - 1)
Yp = lambda v: T + ph * (v - 1) / 19
pc_ = [f'<svg width="{PW}" height="{PH}" style="display:block;margin-top:6px" role="img" aria-label="Position Google semaine par semaine, de 18 à 3, le guide publié le 12 mai">']
for v in (1, 5, 10, 15, 20):
    pc_.append(f'<line x1="{L}" x2="{PW - Rr}" y1="{f(Yp(v))}" y2="{f(Yp(v))}" stroke="{GRID}"/>')
    pc_.append(f'<text x="{L - 7}" y="{f(Yp(v) + 3.5)}" text-anchor="end" fill="{AXIS}" style="font:400 10px var(--f-text)">{v}</text>')
xf = Xp(10)
pc_.append(f'<line x1="{f(xf)}" x2="{f(xf)}" y1="10" y2="{f(Yp(20))}" stroke="#1B0AB0" stroke-opacity="0.4" stroke-dasharray="3 3"/>')
pc_.append(f'<text x="{f(xf + 5)}" y="13" fill="{INK}" style="font:500 10px var(--f-text)">Guide live · 12 May</text>')
pts = " ".join(f"{f(Xp(i))},{f(Yp(v))}" for i, v in enumerate(pos))
pc_.append(f'<polyline points="{pts}" fill="none" stroke="{BLUE}" stroke-width="2" stroke-linejoin="round"/>')
pc_.append(f'<circle cx="{f(Xp(10))}" cy="{f(Yp(14))}" r="4" fill="#FFFFFF" stroke="#1B0AB0" stroke-width="2"/>')
pc_.append(f'<circle cx="{f(Xp(25))}" cy="{f(Yp(3))}" r="4.5" fill="{BLUE}" stroke="#FFFFFF" stroke-width="2"/>')
pc_.append(f'<text x="{f(Xp(25) - 8)}" y="{f(Yp(3) - 9)}" text-anchor="end" fill="{INK}" style="font:500 11px var(--f-text)">Position 3</text>')
for i, m in [(0, "Mar"), (4, "Apr"), (9, "May"), (13, "Jun"), (17, "Jul"), (22, "Aug")]:
    pc_.append(f'<text x="{f(Xp(i))}" y="{PH - 5}" text-anchor="{"start" if i == 0 else "middle"}" fill="{AXIS}" style="font:400 10px var(--f-text)">{m}</text>')
pc_.append("</svg>")
pos_chart = "".join(pc_)

cited = [("ChatGPT", "9 June"), ("Gemini", "16 June"), ("Perplexity", "2 June"), ("AI Overviews", "23 June"), ("Copilot", None), ("Meta AI", None)]
cited_list = "".join(
    f'<div class="rw" style="padding:6px 0;border-top:1px solid rgba(18,0,80,.07)"><span class="pl" style="border:0;padding:0;height:auto"><i style="--c:{PLAT["AI answers"] if d else GRAY}"></i>{n}</span>'
    + (f'<span class="sp chip s-done"><i data-lucide="check"></i>Cited since {d}</span>' if d else '<span class="sp chip s-todo">Not yet</span>') + "</div>"
    for n, d in cited)

# ——— ligne de temps et script ———
BOARDS = [("one-box", "One box", 6, "#5D5A86", "#FFFFFF"), ("everywhere", "Everywhere", 9, "#5D5A86", "#FFFFFF"),
          ("pieces", "In pieces", 10, "#5D5A86", "#FFFFFF"), ("intro", "Introducing", 8, "#1B0AB0", "#FFFFFF"),
          ("overview", "One screen", 9, "#1B0AB0", "#FFFFFF"), ("six", "Six moves", 4, "#1B0AB0", "#FFFFFF"),
          ("collect", "Collect", 11, RAMP_DK[0], INK), ("rank", "Identify · ranking", 7, RAMP_DK[1], INK),
          ("score", "Identify · score", 11, RAMP_DK[1], INK), ("recommend", "Recommend", 12, RAMP_DK[2], INK),
          ("ai-answer", "Inside an AI answer", 9, RAMP_DK[2], INK), ("coordinate", "Coordinate", 11, RAMP_DK[3], INK),
          ("timeline", "Timeline", 8, RAMP_DK[3], INK), ("launch", "Launch", 11, RAMP_DK[4], INK),
          ("formats", "Every format", 9, RAMP_DK[4], INK), ("evaluate", "Evaluate", 12, RAMP_DK[5], INK),
          ("traced", "One action, traced", 8, RAMP_DK[5], INK), ("report", "The report", 7, RAMP_DK[5], INK),
          ("circle", "The circle", 9, "#120050", "#FFFFFF"), ("onehub", "One Hub", 5, "#120050", "#FFFFFF"),
          ("cta", "Be one of them", 7, "#120050", "#FFFFFF")]
_tim = ICI / "vo_timing.json"
if _tim.exists():
    _t = json.loads(_tim.read_text())
    BOARDS = [(k, n, _t[k]["slot"], bg, fg) for k, n, d, bg, fg in BOARDS]
_ft = ICI / "film" / "timing.json"
if _ft.exists():                      # le film fait foi : mêmes durées que le montage
    _F = {x["key"]: x for x in json.loads(_ft.read_text())["scenes"]}
    BOARDS = [(k, n, _F[k]["dur"], bg, fg) for k, n, d, bg, fg in BOARDS]
order = re.findall(r'id="@@ID:([a-z-]+)@@"', TPL)
assert order == [b[0] for b in BOARDS], (order, [b[0] for b in BOARDS])
TOTAL = sum(b[2] for b in BOARDS)
tc = lambda s: f"{int(round(s)) // 60}:{int(round(s)) % 60:02d}"
starts, t0 = {}, 0
for k, *_rest in BOARDS:
    starts[k] = t0
    t0 += _rest[1]
num = {k: f"{i + 1:02d}" for i, (k, *_r) in enumerate(BOARDS)}
timeline = "".join(
    f'<a href="#p{num[k]}" style="flex:{d} 1 0;background:{bg};color:{fg}" title="{num[k]} · {name} · {tc(starts[k])} → {tc(starts[k] + d)}"><b>{num[k]}</b><span>{name}</span></a>'
    for k, name, d, bg, fg in BOARDS)
ruler = "".join(f'<span style="left:{t_ / TOTAL * 100:.3f}%">{tc(t_)}</span>' for t_ in [*range(0, int(TOTAL) - 10, 30), TOTAL])

vos = re.findall(r'<p class="vo-t">(.*?)</p>', TPL)
assert len(vos) == len(BOARDS), len(vos)
words = sum(len(html.unescape(v).split()) for v in vos)
wpm = round(words / TOTAL * 60)
script_rows = "".join(f'<tr><td>{tc(starts[k])} → {tc(starts[k] + d)}</td><td>{num[k]} · {name}</td><td>{v}</td></tr>'
                      for (k, name, d, *_), v in zip(BOARDS, vos))

out = TPL
for k, v in {"LOGO_SYMBOL": logo, "HUB_MARKS": hub, "RING_BIG": "".join(big), "LETTERS": letters, "ORBIT": orbit,
             "FRAGMENTS": fragments, "SOURCES": sources_html, "COLLECT_BARS": collect_bars, "OPP_TABLE": opp_table,
             "GAUGE": gauge, "SCORE_PARTS": score_parts, "DEMAND_CHART": demand_chart, "VIS_BARS": vis_bars,
             "RECO_COLS": reco_cols, "AVATARS": avatars, "BOARD": board_html, "STEPPER": stepper,
             "LAUNCH_PANELS": launch_panels, "EVAL_KPIS": eval_kpis, "CONV_CHART": conv_chart, "DUMBBELL": dumbbell,
             "LOOP": loop, "QR": qr_html, "TIMELINE": timeline, "RULER": ruler, "SCRIPT_ROWS": script_rows,
             "WORDS": str(words), "WPM": str(wpm), "OVERVIEW_BARS": overview_bars, "OVERVIEW_CIRCLE": overview_circle,
             "AI_SOURCES": ai_sources, "GANTT": gantt, "POS_CHART": pos_chart, "CITED_LIST": cited_list,
             "AV_TP": av("TP"), "CONV_PAIR": f"{last:,} vs {prev:,}", "DUR": tc(TOTAL), "NB": str(len(BOARDS)),
             "DURTXT": f"{int(round(TOTAL)) // 60} min {int(round(TOTAL)) % 60:02d} s"}.items():
    out = out.replace(f"@@{k}@@", v)
for k in num:
    out = (out.replace(f"@@ID:{k}@@", f"p{num[k]}").replace(f"@@N:{k}@@", num[k])
              .replace(f"@@TC:{k}@@", f"{tc(starts[k])} → {tc(starts[k] + dict((b[0], b[2]) for b in BOARDS)[k])} · {dict((b[0], b[2]) for b in BOARDS)[k]:.1f} s".replace(".", ",")))
left = re.findall(r"@@[A-Za-z_:-]+@@", out)
assert not left, left
VO_JSON = [{"n": num[k], "key": k, "start": starts[k], "dur": d, "text": html.unescape(re.sub(r"<[^>]+>", "", v))}
           for (k, name, d, *_), v in zip(BOARDS, vos)]
import json
(ICI / "vo.json").write_text(json.dumps(VO_JSON, ensure_ascii=False, indent=1))
(ICI / "vo_text.json").write_text(json.dumps({x["key"]: x["text"] for x in VO_JSON}, ensure_ascii=False, indent=1))
(ICI / "onesearch-storyboard.html").write_text(out)
print(f"ok · {len(out):,} octets · {words} mots · {wpm} mots/min · conversions {prev} → {last} (+{pct} %) · visibilité {before:.1f} → {after:.1f}")
