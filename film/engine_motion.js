/* Moteur du film OneSearch Hub — V2 « motion design » (fenêtres flottantes, transitions
   en profondeur, révélations par masque). Copie de la V1 ; la V1 reste inchangée.
   Moteur du film OneSearch Hub. render(t) est sans état : il recalcule toute l'image à
   l'instant t, ce qui permet de rendre n'importe quelle image dans n'importe quel ordre
   (et en parallèle). Les instants viennent de timing.json : coupes sur les temps (124 BPM),
   phrases de la voix repérées dans les silences de l'audio.
   Règle : jamais de `transform: scale` sur un ancêtre de texte SVG (Chrome garde la mise
   en page du texte à l'échelle d'origine) — les zooms passent par `zoom`, les mouvements
   par `translate`. */
(function () {
  "use strict";
  var T = window.TIMING, SC = T.scenes, BEAT = T.beat, RAMP = window.RAMP;
  var LETTERS = ["C", "I", "R", "C", "L", "E"], STAGES = ["Collect", "Identify", "Recommend", "Coordinate", "Launch", "Evaluate"];
  var STAGE_OF = { collect: 0, rank: 1, score: 1, overview: -1, recommend: 2, "ai-answer": 2, coordinate: 3, timeline: 3, launch: 4, formats: 4, evaluate: 5, traced: 5, report: 5 };

  /* ——— outils ——— */
  function cl(x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
  function E(x) { x = cl(x); return 1 - Math.pow(1 - x, 4); }
  function EB(x) { x = cl(x); var c = 1.70158; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); }  // léger rebond
  function P(t, at, d) { return d <= 0 ? (t >= at ? 1 : 0) : cl((t - at) / d); }
  function lerp(a, b, p) { return a + (b - a) * p; }
  function $$(root, sel) { return Array.prototype.slice.call(root.querySelectorAll(sel)); }
  function cue(s, i) { var a = s.sentences; if (!a.length) return s.vo_at; return a[Math.max(0, Math.min(i, a.length - 1))].at; }

  /* ——— coque de l'app (identique aux planches) ——— */
  var NAV = [["collect", "database", "Collect", "C", "12"], ["identify", "target", "Identify", "I", "38"], ["recommend", "sparkles", "Recommend", "R", "10"], ["coordinate", "users", "Coordinate", "C", "42"], ["launch", "rocket", "Launch", "L", "6"], ["evaluate", "trending-up", "Evaluate", "E", "+38%"]];
  $$(document, ".app").forEach(function (app) {
    var st = app.getAttribute("data-stage");
    var items = NAV.map(function (n) { return '<div class="it' + (n[0] === st ? " on" : "") + '"><span class="ico"><i data-lucide="' + n[1] + '"></i></span><span class="lt">' + n[3] + "</span>" + n[2] + '<span class="c">' + n[4] + "</span></div>"; }).join("");
    var sb = document.createElement("aside"); sb.className = "sb";
    sb.innerHTML = '<div class="back"><i data-lucide="arrow-left"></i>All brands</div><div class="lock"><svg class="mark" viewBox="0 0 40 40"><use href="#hub-light"/></svg><div><b>OneSearch Hub</b><small>by <svg viewBox="0 0 932 126"><use href="#mb-logo"/></svg></small></div></div><div class="brand"><b>Velox</b><code>velox.run</code></div>' +
      '<div class="it' + (st === "overview" ? " on" : "") + '"><span class="ico"><i data-lucide="layout-grid"></i></span>Overview</div><p class="sec">CIRCLE</p>' + items + '<div class="foot"><div class="it"><span class="ico"><i data-lucide="settings"></i></span>Settings</div><p class="ver">OneSearch Hub v1.0</p></div>';
    app.insertBefore(sb, app.firstChild);
    var hd = app.querySelector(".hd");
    if (hd) hd.innerHTML = '<span class="tg"><i data-lucide="panel-left"></i></span><span class="fav">V</span><code>velox.run</code><span class="ttl">' + hd.getAttribute("data-title") + '</span><span class="cnt">' + hd.getAttribute("data-count") + '</span><span class="r"><span class="btn btn-o"><i data-lucide="file-text"></i>Client report</span><span class="btn btn-o"><i data-lucide="languages"></i>EN</span><span class="btn btn-o btn-i"><i data-lucide="sun"></i></span></span>';
  });
  try { if (window.lucide) window.lucide.createIcons({ attrs: { "stroke-width": 1.5 } }); } catch (e) {}
  // caméra : .app dans un .cam
  $$(document, ".scene > .stage > .app").forEach(function (app) {
    var cam = document.createElement("div"); cam.className = "cam";
    app.parentNode.insertBefore(cam, app); cam.appendChild(app);
  });
  // V2 : la fenêtre flottante (.win) autour de la caméra, avec son éclat lumineux
  $$(document, ".scene > .stage > .cam").forEach(function (cam) {
    var win = document.createElement("div"); win.className = "win";
    cam.parentNode.insertBefore(win, cam); win.appendChild(cam);
    var sh = document.createElement("div"); sh.className = "sheen"; win.appendChild(sh);
    win.parentNode.classList.add("mst");
  });
  // vignettes de la boucle : clones à l'état final
  $$(document, "[data-thumb]").forEach(function (t) {
    var src = document.querySelector("#" + t.getAttribute("data-thumb") + " > .stage"); if (!src) return;
    var c = src.cloneNode(true); $$(c, ".ovl,.hud").forEach(function (n) { n.remove(); });
    c.style.zoom = parseFloat(t.getAttribute("data-w")) / 1280; t.appendChild(c);
  });

  /* ——— préparations génériques ——— */
  function base(el) { if (el._bt === undefined) el._bt = el.style.transform || ""; return el._bt; }
  function rev(el, t, at, d, dy, dx) {
    var p = E(P(t, at, d || 0.38)); base(el);
    el.style.opacity = p;
    el.style.transform = (el._bt + (p < 1 ? " translate(" + ((1 - p) * (dx || 0)) + "px," + ((1 - p) * (dy === undefined ? 16 : dy)) + "px)" : "")).trim();
  }
  function hide(el) { base(el); el.style.opacity = 0; }
  function words(el) {               // découpe un texte en mots animables, en gardant <em>, <br>
    if (el._w) return el._w;
    var out = [];
    (function walk(node) {
      $$(node, ":scope > *").length; // noop
      Array.prototype.slice.call(node.childNodes).forEach(function (ch) {
        if (ch.nodeType === 3) {
          var parts = ch.textContent.split(/(\s+)/), frag = document.createDocumentFragment();
          parts.forEach(function (p) {
            if (!p) return;
            if (/^\s+$/.test(p)) { frag.appendChild(document.createTextNode(p)); return; }
            var m = document.createElement("span"); m.className = "wm"; var sp = document.createElement("span"); sp.className = "w"; sp.textContent = p; m.appendChild(sp); frag.appendChild(m); out.push(sp);
          });
          node.replaceChild(frag, ch);
        } else if (ch.nodeType === 1 && ch.tagName !== "BR" && ch.tagName !== "svg" && ch.tagName !== "I") walk(ch);
        else if (ch.nodeType === 1 && (ch.tagName === "svg" || ch.tagName === "I")) out.push(ch);
      });
    })(el);
    el._w = out; return out;
  }
  function slam(el, t, at, gap, d) {  // mots qui claquent l'un après l'autre
    var ws = words(el); gap = gap === undefined ? 0.075 : gap;
    ws.forEach(function (w, i) {
      var p = P(t, at + i * gap, Math.max(d || 0.28, 0.42)), e = EB(p);
      var q = E(p); w.style.opacity = cl(p * 3);
      w.style.transform = p < 1 ? "translateY(" + ((1 - q) * 108) + "%) rotate(" + ((1 - q) * 5) + "deg)" : "";
    });
  }
  function wtimes(s, from, n, skip) {
    var out = [], k = from, sk = skip || 0;
    while (out.length < n && k < s.sentences.length) {
      var se = s.sentences[k], ws = se.text.split(/\s+/), tot = se.text.length, acc = 0, d = se.dur || 0.8;
      for (var j = 0; j < ws.length && out.length < n; j++) {
        if (sk > 0) { sk--; acc += ws[j].length + 1; continue; }
        out.push(se.at + d * 0.92 * acc / tot); acc += ws[j].length + 1;
      }
      k++;
    }
    while (out.length < n) out.push(out.length ? out[out.length - 1] + 0.15 : s.t0);
    return out;
  }
  function slamAt(el, t, times, d) {
    var ws = words(el);
    ws.forEach(function (w, i) {
      var at = times[Math.min(i, times.length - 1)], p = P(t, at, Math.max(d || 0.26, 0.42)), e = EB(p);
      var q = E(p); w.style.opacity = cl(p * 3);
      w.style.transform = p < 1 ? "translateY(" + ((1 - q) * 108) + "%) rotate(" + ((1 - q) * 5) + "deg)" : "";
    });
  }
  function counters(root) {
    return $$(root, ".kpi .n, .dsp.num, p.dsp.num").map(function (el) {
      var node = el; while (node.children.length === 1 && !node.childNodes[0].nodeValue) node = node.children[0];
      var txt = node.textContent, m = txt.match(/^([^\d]*?)(\d[\d,]*\.?\d*)([\s\S]*)$/);
      if (!m || node.children.length) return null;
      var raw = m[2], dec = raw.indexOf(".") >= 0 ? raw.split(".")[1].length : 0;
      return { node: node, pre: m[1], num: parseFloat(raw.replace(/,/g, "")), dec: dec, comma: raw.indexOf(",") >= 0, suf: m[3] };
    }).filter(Boolean);
  }
  function count(c, t, at, d) {
    var p = E(P(t, at, d || 1.0)), v = c.num * p, s = v.toFixed(c.dec);
    if (c.comma) s = Number(s).toLocaleString("en-US", { minimumFractionDigits: c.dec, maximumFractionDigits: c.dec });
    c.node.textContent = c.pre + s + c.suf;
  }
  function bars(root) {
    var out = [];
    $$(root, ".bar > i").forEach(function (el) { out.push({ el: el, kind: "w", w: el.style.width }); });
    $$(root, ".mix").forEach(function (el) { out.push({ el: el, kind: "sx" }); });
    return out;
  }
  function grow(b, t, at, d) {
    var p = E(P(t, at, d || 0.7));
    if (b.kind === "w") b.el.style.width = (parseFloat(b.w) * p) + "%";
    else { b.el.style.transformOrigin = "left center"; b.el.style.transform = "scaleX(" + p + ")"; }
  }
  function svgPrep(svg) {
    if (svg._p) return svg._p;
    var o = { rects: [], strokes: [], fades: [] };
    $$(svg, "rect, polyline, path, line, circle, polygon, text, ellipse").forEach(function (el) {
      var tag = el.tagName.toLowerCase();
      if (el.closest("defs") || el.closest("marker")) return;
      if (tag === "rect" && el.hasAttribute("rx") && parseFloat(el.getAttribute("width")) >= 8) { o.rects.push({ el: el, w: parseFloat(el.getAttribute("width")) }); return; }
      var dash = el.getAttribute("stroke-dasharray");
      if (tag === "circle" && dash && el.getAttribute("fill") === "none") {   // jauge
        var a = dash.split(/[ ,]+/).map(parseFloat); o.strokes.push({ el: el, gauge: a }); return;
      }
      if ((tag === "polyline" || tag === "path") && el.getAttribute("fill") === "none" && !dash) {
        var L = 0; try { L = el.getTotalLength(); } catch (e) {}
        o.strokes.push({ el: el, L: L }); return;
      }
      o.fades.push(el);
    });
    svg._p = o; return o;
  }
  function draw(svg, t, at, d, stagger) {
    var o = svgPrep(svg); d = d || 1.0;
    var st = stagger === undefined ? Math.min(0.06, (d * 0.5) / Math.max(1, o.rects.length)) : stagger;
    o.rects.forEach(function (r, i) { r.el.setAttribute("width", r.w * E(P(t, at + i * st, d * 0.55))); });
    o.strokes.forEach(function (s) {
      var p = E(P(t, at + d * 0.1, d * 0.85));
      if (s.gauge) s.el.setAttribute("stroke-dasharray", (s.gauge[0] * p) + " " + s.gauge[1]);
      else if (s.L) { s.el.style.strokeDasharray = (s.L * p) + " " + (s.L + 1); }
    });
    o.fades.forEach(function (f) { f.style.opacity = E(P(t, at, d * 0.45)); });
  }

  /* ——— scènes ——— */
  var FILM = document.getElementById("film"), FLASH = document.getElementById("flash"), STING = document.getElementById("sting");
  SC.forEach(function (s, i) {
    s.el = document.getElementById("p" + s.n);
    s.stage = s.el.querySelector(":scope > .stage");
    s.end = s.start + s.dur;
    s.app = s.el.querySelector(":scope > .stage > .win > .cam > .app");
    s.cam = s.app ? s.app.parentNode : null;
    s.ovl = s.el.querySelector(":scope > .stage > .ovl");
    s.hud = s.el.querySelector(":scope > .stage > .hud");
    // fin du carton d'étape : quand la voix a dit le nom de l'étape, calé au demi-temps
    s.t0 = s.start;
    if (s.stinger) {
      var raw = (s.sentences.length > 1 ? s.sentences[1].at : s.vo_at + 1) - s.start - 0.06;
      s.t0 = s.start + Math.max(3, Math.min(6, Math.round(raw / (BEAT / 2)))) * BEAT / 2;
    }
    s.units = [];
    if (s.app) {
      var ct = s.app.querySelector(".ct");
      Array.prototype.slice.call(ct.children).forEach(function (ch) {
        if (ch.classList.contains("card")) s.units.push(ch);
        else if (!ch.querySelector(".card")) s.units.push(ch);
        else $$(ch, ".card").forEach(function (c) { if (!c.parentElement.closest(".card")) s.units.push(c); });
      });
      s.units = s.units.map(function (el, k) {
        return { el: el, at: s.t0 + 0.12 + k * 0.07, cnt: counters(el), bars: bars(el), svgs: $$(el, "svg").filter(function (v) { return !v.classList.contains("lucide") && !v.closest(".lucide") && v.getAttribute("viewBox") !== "0 0 40 40"; }) };
      });
      s.unitOf = function (el) { for (var k = 0; k < s.units.length; k++) if (s.units[k].el === el) return s.units[k]; return null; };
    }
    s.ovlAt = s.sentences.length ? cue(s, s.sentences.length - 1) : s.t0 + 1;
    s.cams = null;
  });
  function S(key) { for (var i = 0; i < SC.length; i++) if (SC[i].key === key) return SC[i]; }
  function U(s, el) { return s.unitOf(el); }
  function setAt(s, el, at) { var u = U(s, el); if (u) u.at = at; return u; }

  /* réglages par scène, v4 : instants exacts des phrases (voix générée phrase par phrase).
     Un bloc apparaît 60 ms avant sa phrase ; le texte à l'écran reprend les mots de la voix,
     chaque mot à l'instant estimé de sa prononciation (proportion des caractères). */
  var LEAD = 0.06;
  (function () {
    var s;
    s = S("overview"); (function (s) {
      s.units.forEach(function (u, k) { u.at = s.t0 + 0.06 + k * 0.05; });
      var cards = s.units.filter(function (u) { return u.el.classList.contains("card"); });
      cards[4].at = cue(s, 0) - LEAD; cards[4].drawD = cue(s, 2) - cue(s, 0) + 0.5;
      cards[5].at = cue(s, 1) - LEAD; cards[6].at = cue(s, 2) - LEAD;
      s.ovlFrom = 3;
      s.cams = [[s.t0, 1, 640, 360], [cue(s, 0), 1.08, 520, 470], [cue(s, 1) + 0.1, 1.08, 560, 470], [cue(s, 2), 1, 640, 360], [s.end, 1.03, 640, 375]];
    })(s);
    s = S("collect"); (function (s) {
      var cards = s.units.filter(function (u) { return u.el.classList.contains("card"); });
      cards.slice(0, 4).forEach(function (u, k) { u.at = s.t0 + 0.04 + k * 0.06; });
      // ordre : GSC, MentionLab, AI Overviews, GA4, TikTok, YouTube, Instagram, Reddit, Amazon, Pulse, Members, crawl
      var at = [cue(s, 1), cue(s, 3), cue(s, 3) + 0.12, cue(s, 2), cue(s, 4), cue(s, 4) + 0.08, cue(s, 4) + 0.16, cue(s, 4) + 0.24,
                cue(s, 5), cue(s, 6), cue(s, 6) + 0.1, cue(s, 6) + 0.2];
      cards.slice(4, 16).forEach(function (u, k) { u.at = at[k] - LEAD; });
      cards[16].at = cue(s, 3) - LEAD; cards[16].drawD = 1.3;
      cards[17].at = cue(s, 7) - LEAD;
      s.ovlFrom = 6;
      s.cams = [[s.t0, 1, 640, 360], [cue(s, 1), 1.05, 600, 345], [cue(s, 6), 1.05, 640, 345], [s.end, 1.07, 640, 340]];
    })(s);
    s = S("rank"); (function (s) {
      s.units.forEach(function (u, k) { u.at = s.t0 + 0.04 + k * 0.06; });
      s.reorderAt = cue(s, 1) - LEAD; s.ovlFrom = 1;
      s.cams = [[s.t0, 1, 640, 360], [s.reorderAt, 1.1, 700, 470], [s.end, 1.15, 680, 480]];
      var table = s.units[s.units.length - 1].el, rows = Array.prototype.slice.call(table.children, 1);
      var names = rows.map(function (r) { return r.children[1].textContent; }), sorted = names.slice().sort();
      s.rows = rows.map(function (r, k) { return { el: r, off: (sorted.indexOf(names[k]) - k) * 36, mv: r.lastElementChild }; });
    })(s);
    s = S("score"); (function (s) {
      s.units.forEach(function (x, k) { x.at = s.t0 + 0.04 + k * 0.05; });
      var cards = s.units.filter(function (x) { return x.el.classList.contains("card"); });
      cards[0].drawAt = cue(s, 0); cards[0].drawD = 1.1;
      s.parts = $$(cards[0].el, ":scope > div").filter(function (d) { return d.querySelector(".bar"); });
      s.partsAt = [cue(s, 0) + 0.4, cue(s, 0) + 0.75, cue(s, 0) + 1.1];
      cards[1].at = cue(s, 0) + 0.3; cards[1].drawD = 1.3; cards[2].at = cue(s, 1) - LEAD;
      s.ovlFrom = 1;
      s.cams = [[s.t0, 1.15, 330, 340], [cue(s, 1) - 0.3, 1.15, 330, 420], [cue(s, 1) + 0.3, 1, 640, 360], [s.end, 1.03, 680, 370]];
    })(s);
    s = S("recommend"); (function (s) {
      var u = s.units; u[0].at = s.t0 + 0.04; u[1].at = cue(s, 0) + 0.25;
      for (var k = 0; k < 4; k++) u[2 + k].at = cue(s, 1 + k) - LEAD;     // Google, AI answers, TikTok, Amazon
      s.scanAt = cue(s, 0) + 0.2; s.ovlFrom = 5;
      s.cams = [[s.t0, 1, 640, 360], [cue(s, 1), 1.02, 640, 380], [s.end, 1.07, 640, 410]];
    })(s);
    s = S("ai-answer"); (function (s) {
      var u = s.units; u[0].at = s.t0; u[1].at = s.t0 + 0.03; u[2].at = cue(s, 0) + 0.35; u[2].drawD = 0.9; u[3].at = cue(s, 1) - LEAD;
      var left = u[1].el; s.q = left.children[1]; s.ans = left.children[2]; s.cites = left.children[3]; s.warn = left.children[4];
      s.typeEnd = cue(s, 1) - 0.1; s.citesAt = cue(s, 1) - 0.35; s.warnAt = cue(s, 1) - LEAD;
      s.ovlFrom = 0;
      s.cams = [[s.t0, 1.12, 420, 330], [cue(s, 1) - 0.3, 1.12, 420, 400], [cue(s, 1) + 0.3, 1.05, 880, 400], [s.end, 1.07, 880, 400]];
    })(s);
    s = S("coordinate"); (function (s) {
      s.units.forEach(function (x, k) { x.at = s.t0 + 0.04 + k * 0.06; });
      var grid = s.app.querySelector(".ct").children[2];
      s.cols = Array.prototype.slice.call(grid.children).filter(function (c) { return !c.classList.contains("card"); });
      s.colsAt = [0, 1, 2, 3, 4].map(function (k) { return cue(s, 1) - LEAD + k * 0.1; });    // le tableau arrive avec « Every action gets an owner. »
      setAt(s, grid.querySelector(":scope > .card"), cue(s, 1) + 0.75);                   // « …an owner. »
      s.avs = s.app.querySelector(".avs"); s.agAt = cue(s, 3);
      s.ovlFrom = 1;
      s.cams = [[s.t0, 1, 640, 360], [cue(s, 1), 1.03, 640, 350], [s.end, 1.06, 650, 340]];
    })(s);
    s = S("timeline"); (function (s) {
      var u = s.units; u[0].at = s.t0; u[1].at = s.t0 + 0.04; u[1].drawAt = s.t0 + 0.08; u[1].drawD = cue(s, 1) - s.t0 + 0.6;
      s.ovlFrom = 0;
      s.cams = [[s.t0, 1.02, 640, 355], [s.end, 1.07, 690, 338]];
    })(s);
    s = S("launch"); (function (s) {
      var u = s.units; u[0].at = s.t0; u[1].at = s.t0 + 0.03; u[2].at = cue(s, 1) - LEAD; u[3].at = cue(s, 2) - LEAD; u[4].at = cue(s, 3) - LEAD; u[5].at = cue(s, 4) - LEAD;
      s.steps = $$(u[1].el, ":scope > div > div"); s.stepsAt = [s.t0 + 0.04, cue(s, 1), cue(s, 2), cue(s, 3), cue(s, 4)];
      s.pills = $$(u[5].el, ".pl"); s.pillsAt = cue(s, 4) - LEAD;
      s.approve = u[4].el.querySelector(".btn-p"); s.approveAt = cue(s, 3) + 0.15;
      s.ovlFrom = 1;
      s.cams = [[s.t0, 1, 640, 360], [cue(s, 3), 1.03, 640, 375], [s.end, 1.05, 640, 385]];
    })(s);
    s = S("formats"); (function (s) {
      var u = s.units, w = wtimes(s, 0, 5);           // First drafts, for every platform.
      u[0].at = s.t0; u[1].at = w[0] - LEAD; u[2].at = w[2] - LEAD; u[3].at = w[3] - LEAD; u[4].at = w[4] + 0.2;
      s.ovlFrom = 0;
      s.cams = [[s.t0, 1, 640, 360], [s.end, 1.035, 640, 368]];
    })(s);
    s = S("evaluate"); (function (s) {
      var u = s.units; u[0].at = s.t0;
      var cards = u.filter(function (x) { return x.el.classList.contains("card"); });
      cards[0].at = cue(s, 1) - LEAD; cards[1].at = cue(s, 2) - LEAD; cards[2].at = cue(s, 3) - LEAD; cards[3].at = cue(s, 3) + 0.25;
      cards[4].at = s.t0 + 0.04; cards[4].drawD = 2.2; cards[5].at = cue(s, 3) + 0.3; cards[5].drawD = 1.0;
      s.ovlFrom = 1;                                   // Visibility ↑ Traffic ↑ Conversions ↑ = « Visibility, up. … »
      s.cams = [[s.t0, 1.08, 520, 470], [cue(s, 1), 1, 640, 360], [cue(s, 3), 1.04, 760, 420], [s.end, 1.04, 700, 400]];
    })(s);
    s = S("traced"); (function (s) {
      var u = s.units; u[0].at = s.t0; u[1].at = s.t0 + 0.03;
      var cards = u.filter(function (x) { return x.el.classList.contains("card"); });
      for (var k = 1; k <= 4; k++) cards[k].at = s.t0 + 0.2 + (k - 1) * 0.09;
      cards[5].at = s.t0 + 0.3; cards[5].drawD = 1.3; cards[6].at = s.t0 + 0.45;
      s.cited = $$(cards[6].el, ":scope > .rw"); s.citedAt = s.t0 + 0.6;
      s.ovlFrom = 0;
      s.cams = [[s.t0, 1, 640, 360], [s.end, 1.04, 630, 400]];
    })(s);
    s = S("report"); (function (s) {
      var st = s.stage; s.top = st.children[0]; s.cover = st.children[1]; s.nav = st.children[2]; s.pop = st.children[3];
      s.cnt = counters(s.cover); s.metrics = $$(s.cover, "div[style*='border-radius:16px']"); s.band = s.cover.querySelector("div[style*='border-left']");
      s.copied = s.pop.lastElementChild; s.popAt = cue(s, 0) - LEAD; s.copiedAt = cue(s, 1) + 0.25; s.ovlFrom = 0;
    })(s);
  })();

  /* ——— caméra ——— */
  function camera(s, t, ex) {
    if (!s.cam) return;
    s.app.style.zoom = 1; s.cam.style.transform = "";
    var w = s.cam.parentNode, dir = SC.indexOf(s) % 2 ? 1 : -1, p = cl((t - s.start) / s.dur);
    var e = p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
    var sc = lerp(0.862, 0.902, e), ry = lerp(-3.4 * dir, 2.8 * dir, e), rx = lerp(2.4, 0.5, e), dy = lerp(12, 0, e), dx = 0;
    ex = ex || {};
    sc *= (ex.sc || 1); dx += (ex.dx || 0); ry += (ex.ry || 0);
    w.style.transform = "translate(" + dx + "px," + dy + "px) perspective(2200px) rotateY(" + ry + "deg) rotateX(" + rx + "deg) scale(" + sc + ")";
    w.style.opacity = ex.op === undefined ? 1 : ex.op;
    w.style.filter = ex.blur > 0.2 ? "blur(" + ex.blur + "px)" : "";
    var sh = w.querySelector(".sheen"), ps = P(t, s.t0 + 0.2, 1.1);
    sh.style.opacity = ps > 0 && ps < 1 ? Math.sin(ps * Math.PI) : 0; sh.style.transform = "translateX(" + lerp(-60, 520, E(ps)) + "%) skewX(-18deg)";
  }

  /* ——— rendu d'une scène d'app ——— */
  function renderApp(s, t) {
    s.units.forEach(function (u) {
      rev(u.el, t, u.at, 0.45, 22);
      if (u.at > s.t0 + 0.3 && u.el.classList.contains("card")) {
        var pp = P(t, u.at + 0.1, 0.85), sp = pp > 0 && pp < 1 ? Math.sin(pp * Math.PI) : 0;
        if (!u._pos) u._pos = u.el.style.position || "relative";
        if (sp > 0.01) {
          u.el.style.transform += " scale(" + (1 + 0.035 * sp) + ")"; u.el.style.position = u._pos; u.el.style.zIndex = 4;
          u.el.style.boxShadow = "0 0 0 " + (2 * sp) + "px rgba(82,183,255," + (0.95 * sp) + "), 0 " + (22 * sp) + "px " + (48 * sp) + "px -12px rgba(27,10,176," + (0.38 * sp) + ")";
        } else { u.el.style.boxShadow = ""; u.el.style.zIndex = ""; }
      }
      u.cnt.forEach(function (c) { count(c, t, u.at + 0.05, 1.0); });
      u.bars.forEach(function (b, k) { grow(b, t, u.at + 0.15 + k * 0.03, 0.75); });
      u.svgs.forEach(function (v) { draw(v, t, u.drawAt || (u.at + 0.12), u.drawD || 1.1); });
    });
    var k = s.key;
    if (k === "rank") s.rows.forEach(function (r, i) {
      var p = E(P(t, s.reorderAt + i * 0.03, 1.1));
      r.el.style.transform = r.off ? "translateY(" + (r.off * (1 - p)) + "px)" : ""; r.el.style.position = "relative"; r.el.style.zIndex = r.off ? 2 : 1;
      r.mv.style.opacity = E(P(t, s.reorderAt + 0.8, 0.3));
    });
    if (k === "score") s.parts.forEach(function (d, i) {
      rev(d, t, s.partsAt[i] - 0.1, 0.35, 10);
      var b = d.querySelector(".bar > i"); if (!b._w) b._w = b.style.width; b.style.width = (parseFloat(b._w) * E(P(t, s.partsAt[i], 0.7))) + "%";
      var n = d.querySelector(".dsp.num"); if (n) { if (!n._c) n._c = counters(d)[0]; if (n._c) count(n._c, t, s.partsAt[i], 0.7); }
    });
    if (k === "recommend") {
      if (!s.scan) { s.scan = document.createElement("div"); s.scan.className = "scan"; s.stage.appendChild(s.scan); }
      var p = P(t, s.scanAt, 0.7); s.scan.style.opacity = p > 0 && p < 1 ? 1 : 0; s.scan.style.left = (200 + p * 1080 - 120) + "px";
      $$(s.app, ".ct > div:last-child > .card").forEach(function (col, ci) {
        var u = U(s, col); $$(col, ":scope > div[style*='border:1px']").forEach(function (it, j) { rev(it, t, u.at + 0.12 + j * 0.1, 0.35, 12); });
      });
    }
    if (k === "ai-answer") {
      rev(s.q, t, s.t0 + 0.1, 0.28, 10, 30);
      var p2 = P(t, s.t0 + 0.4, s.typeEnd - s.t0 - 0.4);
      s.ans.style.clipPath = "inset(0 0 " + ((1 - p2) * 100) + "% 0)"; s.ans.style.opacity = p2 > 0 ? 1 : 0;
      rev(s.cites, t, s.citesAt, 0.3, 8);
      rev(s.warn, t, s.warnAt, 0.35, 14);
    }
    if (k === "coordinate") {
      s.cols.forEach(function (c, i) {
        rev(c, t, s.colsAt[i], 0.35, 22);
        $$(c, ":scope > div:not(.rw)").forEach(function (cd, j) { rev(cd, t, s.colsAt[i] + 0.1 + j * 0.09, 0.32, 14); });
      });
      var avs = $$(s.avs, ".av"); var pa = P(t, s.agAt, 0.45);
      avs[avs.length - 1].style.transform = pa > 0 && pa < 1 ? "translateY(" + (-6 * Math.sin(pa * Math.PI)) + "px)" : "";
    }
    if (k === "launch") {
      s.steps.forEach(function (st, i) { st.style.opacity = 0.25 + 0.75 * E(P(t, s.stepsAt[i], 0.3)); });
      s.pills.forEach(function (pl, i) { rev(pl, t, s.pillsAt + 0.15 + i * 0.12, 0.3, 8); });
      var pa2 = P(t, s.approveAt, 0.5); s.approve.style.boxShadow = pa2 > 0 && pa2 < 1 ? "0 0 0 " + (8 * Math.sin(pa2 * Math.PI)) + "px rgba(12,155,56,.25)" : "";
    }
    if (k === "traced") s.cited.forEach(function (r, i) { rev(r, t, s.citedAt + i * 0.12, 0.3, 8); });
  }

  /* ——— scènes titres ——— */
  function renderTitle(s, t) {
    var st = s.stage, k = s.key;
    if (k === "one-box") {
      var c = st.querySelector(".c-center"), box = c.children[0], car = box.children[1] || box.lastElementChild;
      var p = E(P(t, s.start + 0.1, 0.6));
      box.style.opacity = p; c.style.transform = "scale(" + lerp(0.95, 1.06, (t - s.start) / s.dur) + ")";
      $$(box, "span").forEach(function (sp) { if (sp.style.height === "26px") sp.style.opacity = Math.floor((t - s.start) * 2.4) % 2 ? 0 : 1; });
      c.children[1].style.opacity = E(P(t, s.start + 0.9, 0.6)) * 1;
    }
    if (k === "everywhere") {
      var pills = $$(st, ".qpill"), hi = { 1: 1, 2: 2, 0: 3 }; // ChatGPT, TikTok, Amazon ← phrases 1,2,3
      pills.forEach(function (q, i) {
        if (!q._c) { q._c = [q.offsetLeft + q.offsetWidth / 2, q.offsetTop + q.offsetHeight / 2]; q._b = q.style.opacity || 1; }
        var at = s.start + 0.05 + i * 0.07, p = E(P(t, at, 0.5));
        var dx = (640 - q._c[0]) * (1 - p), dy = (360 - q._c[1]) * (1 - p), fl = (t - s.start);
        var bob = Math.sin(fl * 1.3 + i) * 5;
        var pulse = 0, idx = [1, 2, 3][["ChatGPT", "TikTok", "Amazon"].indexOf(q.querySelector("b").textContent.trim())];
        if (idx !== undefined) { var pp = P(t, cue(s, idx), 0.45); pulse = pp > 0 && pp < 1 ? Math.sin(pp * Math.PI) : 0; }
        var dep = 0.76 + ((i * 37) % 10) / 10 * 0.36;
        q.style.opacity = p * (q._b === "0.75" ? 0.75 : 1);
        q.style.filter = dep < 0.86 ? "blur(" + ((0.86 - dep) * 14) + "px)" : "";
        q.style.transform = "translate(" + (dx + Math.cos(fl * 0.5 + i) * 10 * dep) + "px," + (dy + bob * dep * 1.4) + "px) scale(" + ((lerp(0.4, 1, p) + 0.14 * pulse) * dep) + ")";
        q.style.borderColor = pulse > 0.05 ? "rgba(82,183,255," + (0.3 + 0.7 * pulse) + ")" : "";
        q.style.background = pulse > 0.05 ? "rgba(82,183,255," + (0.07 + 0.18 * pulse) + ")" : "";
      });
      var hu = st.querySelector(".huge"); slamAt(hu, t, (s._wh || (s._wh = wtimes(s, 0, words(hu).length))).map(function (x) { return x - 0.04; }), 0.26);
    }
    if (k === "pieces") {
      var fr = $$(st.children[0], ":scope > div"), fa = [cue(s, 0), cue(s, 0) + 0.12, cue(s, 1), cue(s, 1) + 0.12, cue(s, 1) + 0.24, cue(s, 1) + 0.36];
      fr.forEach(function (f, i) {
        base(f); var p = E(P(t, fa[i] - 0.1, 0.45)), fl = t - s.start;
        f.style.opacity = p * 0.95;
        f.style.transform = f._bt + " translate(" + (Math.sin(fl * 0.7 + i * 1.7) * 9 - (1 - p) * 60) + "px," + (Math.cos(fl * 0.6 + i) * 7) + "px)";
      });
      var qa = [cue(s, 2), cue(s, 3), cue(s, 4)]; $$(st.children[1], "p").forEach(function (q, i) { rev(q, t, qa[i] - 0.06, 0.3, 0, 46); });
    }
    if (k === "intro") {
      var pills2 = $$(st, ".qpill"), conv = E(P(t, s.start, cue(s, 0) - s.start + 0.3));
      pills2.forEach(function (q, i) {
        if (!q._c) { q._c = [parseFloat(q.style.left), parseFloat(q.style.top)]; q._o = parseFloat(q.style.opacity) || 1; }
        var dx = (q._c[0] - 640) * 0.9 * (1 - conv), dy = (q._c[1] - 360) * 0.9 * (1 - conv), pulse = 0;
        [1, 2, 3].forEach(function (bi, j) { var pp = P(t, cue(s, 0) + 0.6 + bi * BEAT + (i % 3 === j ? 0 : 0.05), 0.35); if (pp > 0 && pp < 1) pulse = Math.max(pulse, Math.sin(pp * Math.PI)); });
        q.style.opacity = q._o * E(P(t, s.start + i * 0.05, 0.5));
        q.style.transform = "translate(calc(-50% + " + dx + "px),calc(-50% + " + dy + "px)) scale(" + (1 + 0.12 * pulse) + ")";
      });
      var cc = st.querySelector(".c-center"), mark = cc.children[0], title = cc.children[1], by = cc.children[2];
      var pm = EB(P(t, s.start + 0.05, 0.5)), beat = 0;
      [1, 2, 3].forEach(function (bi) { var pp = P(t, cue(s, 0) + 0.6 + bi * BEAT, 0.3); if (pp > 0 && pp < 1) beat = Math.max(beat, Math.sin(pp * Math.PI)); });
      mark.style.filter = "drop-shadow(0 0 " + (10 + 40 * beat + 30 * Math.sin(Math.PI * P(t, cue(s, 0), 0.9))) + "px rgba(82,183,255,.85))";
      mark.style.opacity = cl(pm * 1.5); mark.style.transform = "rotate(" + ((1 - pm) * -120 + (t - s.start) * 6) + "deg) scale(" + (pm * (1 + 0.1 * beat)) + ")";
      slamAt(title, t, (s._wt2 || (s._wt2 = wtimes(s, 0, words(title).length, 1))).map(function (x) { return x - 0.04; }), 0.3);
      rev(by, t, cue(s, 0) + 0.45, 0.35, 10);
      st.querySelector("svg ellipse").parentNode.style.opacity = E(P(t, s.start, 1.2));
    }
    if (k === "six") {
      $$(st.querySelector(".c-center > div"), ":scope > div").forEach(function (d, i) {
        var at = s.start + 0.08 + i * BEAT / 2, p = EB(P(t, at, 0.28));
        d.children[0].style.opacity = cl(P(t, at, 0.12)); d.children[0].style.transform = "translateY(" + ((1 - p) * -90) + "px) scale(" + lerp(1.25, 1, E(P(t, at, 0.3))) + ")"; d.children[0].style.filter = "blur(" + ((1 - E(P(t, at, 0.3))) * 16) + "px)";
        d.children[1].style.opacity = E(P(t, at + 0.15, 0.3));
      });
      st.querySelector(".c-center > p").style.opacity = E(P(t, s.start, 0.4));
    }
    if (k === "circle") {
      var svg = st.querySelector(":scope > svg"); draw(svg, t, s.start + 0.05, 1.3, 0);
      if (!s.dot) { s.dot = document.createElementNS("http://www.w3.org/2000/svg", "circle"); s.dot.setAttribute("r", "9"); s.dot.setAttribute("fill", "#FFFFFF"); s.dot.style.filter = "drop-shadow(0 0 12px #52B7FF)"; svg.appendChild(s.dot); }
      var ang = (-120 + ((t - s.start) / (BEAT * 6)) * 360) * Math.PI / 180;
      s.dot.setAttribute("cx", 640 + 150 * Math.cos(ang)); s.dot.setAttribute("cy", 352 + 150 * Math.sin(ang)); s.dot.style.opacity = E(P(t, s.start + 0.7, 0.3));
      var th = $$(st, "[data-thumb]"), lb = $$(st, ":scope > p.dsp");
      var orb = (t - s.start) * 9 * Math.PI / 180;
      th.forEach(function (d, i) {
        var a0 = (-90 + 60 * i) * Math.PI / 180, ox = 410 * (Math.cos(a0 + orb) - Math.cos(a0)), oy = 245 * (Math.sin(a0 + orb) - Math.sin(a0));
        rev(d, t, s.start + 0.12 + i * 0.16, 0.4, 18); rev(lb[i], t, s.start + 0.2 + i * 0.16, 0.34, 8);
        d.style.transform += " translate(" + ox + "px," + oy + "px)"; lb[i].style.transform += " translate(" + ox + "px," + oy + "px)";
      });
      var ctr = st.querySelector(":scope > div:not([data-thumb])");
      rev(ctr.children[0], t, s.start + 0.9, 0.3, 12); rev(ctr.children[1], t, s.start + 1.15, 0.3, 8); slam(ctr.children[2], t, s.start + 1.75, 0.1, 0.28);
    }
    if (k === "onehub") {
      var c2 = st.querySelector(".c-center"), h = c2.children[0], lock = c2.children[1];
      if (!h._split) { h._split = true; h.innerHTML = '<span class="l1">One Search.</span><br><span class="l2"><em>One Hub.</em></span>'; }
      rev(lock, t, cue(s, 0) - 0.1, 0.4, 16);
      slamAt(h.querySelector(".l1"), t, wtimes(s, 1, 2).map(function (x) { return x - 0.04; }), 0.28); slamAt(h.querySelector(".l2"), t, wtimes(s, 2, 2).map(function (x) { return x - 0.04; }), 0.28);
    }
    if (k === "cta") {
      var left = st.children[0], right = st.children[1];
      rev(left.children[0], t, s.start + 0.1, 0.35, 10);
      slamAt(left.children[1], t, wtimes(s, 0, words(left.children[1]).length).map(function (x) { return x - 0.04; }), 0.26); slamAt(left.children[2], t, wtimes(s, 1, words(left.children[2]).length).map(function (x) { return x - 0.04; }), 0.28);
      rev(left.children[3], t, cue(s, 1) + 0.6, 0.35, 14);
      var pq = EB(P(t, cue(s, 1) + 0.75, 0.5)); right.style.opacity = cl(pq * 1.6); right.style.transform = "translateY(calc(-50% + " + ((1 - pq) * 30) + "px))";
      var fin = P(t, T.total - 2 * BEAT, 0.5), btn = left.children[3].children[0];
      btn.style.boxShadow = fin > 0 && fin < 1 ? "0 0 0 " + (14 * Math.sin(fin * Math.PI)) + "px rgba(82,183,255,.35)" : "";
    }
    if (k === "report") {
      rev(s.top, t, s.start, 0.3, -10); s.cover.style.opacity = E(P(t, s.start + 0.05, 0.4));
      s.metrics.forEach(function (m, i) { rev(m, t, s.start + 0.25 + i * 0.08, 0.35, 16); });
      s.cnt.forEach(function (c) { count(c, t, s.start + 0.3, 0.9); });
      rev(s.band, t, s.start + 0.7, 0.35, 0, -20); rev(s.nav, t, s.start + 0.5, 0.4, 10);
      var pp3 = EB(P(t, s.popAt, 0.4)); s.pop.style.opacity = cl(pp3 * 1.5); s.pop.style.transform = "translateY(" + ((1 - pp3) * -14) + "px)";
      s.copied.style.opacity = E(P(t, s.copiedAt, 0.25));
    }
  }

  /* ——— surcouches : texte à l'écran et repère CIRCLE ——— */
  function overlays(s, t) {
    if (s.ovl) {
      base(s.ovl);
      var n = words(s.ovl).length, times = s.ovlFrom !== undefined ? (s._wt || (s._wt = wtimes(s, s.ovlFrom, n))) : null;
      var at = times ? times[0] - 0.12 : s.ovlAt - 0.06, p = E(P(t, at, 0.22));
      s.ovl.style.opacity = p; s.ovl.style.transform = "translateX(-50%) translateY(" + ((1 - p) * 30) + "px)";
      if (times) slamAt(s.ovl, t, times.map(function (x) { return x - 0.04; }), 0.22); else slam(s.ovl, t, s.ovlAt, 0.085, 0.28);
    }
    if (s.hud) {
      s.hud.style.opacity = E(P(t, s.t0, 0.3));
      var b = s.hud.querySelector("b"), pb = P(t, s.t0 + 0.05, 0.5);
      if (b) b.style.textShadow = pb > 0 && pb < 1 ? "0 0 " + (14 * Math.sin(pb * Math.PI)) + "px #52B7FF" : "";
    }
  }

  /* ——— carton d'étape ——— */
  var lt_ = STING.querySelector(".lt"), nm_ = STING.querySelector(".nm"), st_ = STING.querySelector(".st"), br_ = STING.querySelector(".bar");
  function stinger(s, t) {
    if (!s.stinger || t >= s.t0 + IRIS) { STING.style.display = "none"; STING.style.clipPath = ""; return false; }
    var i = STAGE_OF[s.key], lt = t - s.start, d = s.t0 - s.start;
    var pin = easeIO(P(t, s.start, 0.36)); STING.style.clipPath = pin < 1 ? "circle(" + (pin * 1250) + "px at 50% 50%)" : "";
    STING.style.display = "block";
    lt_.textContent = LETTERS[i]; lt_.style.color = RAMP[i];
    nm_.textContent = STAGES[i]; st_.textContent = "Step " + (i + 1) + " of 6";
    var p = EB(P(lt, 0, 0.32)), q = E(P(lt, 0.08, 0.35));
    lt_.style.transform = "translateY(-54%) scale(" + lerp(1.6, 1, E(P(lt, 0, 0.42))) + ")"; lt_.style.opacity = cl(P(lt, 0, 0.12)); lt_.style.filter = "blur(" + ((1 - E(P(lt, 0, 0.36))) * 18) + "px)";
    var lw = lt_.offsetWidth; nm_.style.left = st_.style.left = br_.style.left = (150 + lw + 56) + "px";
    nm_.style.transform = "translate(" + ((1 - q) * 120) + "px,-36%)"; nm_.style.opacity = q;
    st_.style.transform = "translate(" + ((1 - q) * 80) + "px,-210%)"; st_.style.opacity = q;
    br_.style.top = "calc(50% + 92px)"; br_.style.width = (E(P(lt, 0.15, d - 0.2)) * 520) + "px";
    STING.style.transform = "";
    return true;
  }

  /* ——— V2 : transitions avec chevauchement ———
     glissé en profondeur entre deux écrans, fondu en profondeur entre carton et écran,
     ouverture en cercle à la sortie d'un carton d'étape (le cercle de CIRCLE). */
  var IRIS = 0.5, BG = document.getElementById("bgfx");
  var INK_BG = "radial-gradient(1300px 900px at 85% -10%, rgba(82,183,255,.30), rgba(82,183,255,0) 60%), radial-gradient(1200px 900px at 0% 110%, rgba(27,10,176,.85), rgba(27,10,176,0) 62%), #0B0430";
  function easeIO(p) { p = cl(p); return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; }
  function trType(a, b) { if (!a) return "none"; if (b.stinger) return "sting"; if (a.app && b.app) return "slide"; return "depth"; }
  var TRD = { slide: 0.62, depth: 0.55, sting: 0.36, none: 0 };
  function resetSec(s) { s.el.style.opacity = ""; s.el.style.transform = ""; s.el.style.filter = ""; s.el.style.clipPath = ""; s.el.style.zIndex = ""; s.el.style.background = ""; }
  function drawScene(s, t, ex) { if (s.app) { camera(s, t, ex); renderApp(s, t); } else renderTitle(s, t); overlays(s, t); }
  function fadeOv(s, a) { [s.ovl, s.hud].forEach(function (o) { if (o) o.style.opacity = parseFloat(o.style.opacity || 1) * a; }); }
  function background(t) {
    var a = t * 0.07, beatOn = t >= S("intro").start && t < S("circle").start && !(t >= S("six").start && t < S("collect").start);
    var ph = (t % BEAT) / BEAT, g = beatOn ? 0.16 * Math.exp(-ph * 5) : 0;
    BG.style.setProperty("--x1", (78 + 10 * Math.cos(a)) + "%"); BG.style.setProperty("--y1", (-6 + 10 * Math.sin(a * 1.3)) + "%");
    BG.style.setProperty("--x2", (8 + 10 * Math.sin(a * 0.9)) + "%"); BG.style.setProperty("--y2", (104 + 8 * Math.cos(a)) + "%");
    BG.style.setProperty("--g", g.toFixed(3));
  }
  window.render = function (t) {
    var ci = SC.length - 1;
    for (var i = 0; i < SC.length; i++) if (t >= SC[i].start && t < SC[i].end) { ci = i; break; }
    var cur = SC[ci], prev = ci > 0 ? SC[ci - 1] : null, type = trType(prev, cur), d = TRD[type];
    var inTr = !!prev && t < cur.start + d;
    SC.forEach(function (s) { if (s !== cur && !(inTr && s === prev)) s.el.classList.remove("on"); });
    resetSec(cur); if (prev) resetSec(prev);
    cur.el.classList.add("on"); cur.el.style.zIndex = 2;
    if (inTr) { prev.el.classList.add("on"); prev.el.style.zIndex = 1; }
    background(t);
    var p = inTr ? easeIO((t - cur.start) / d) : 1;
    if (inTr && type === "slide") {
      drawScene(prev, t, { dx: -1250 * p, sc: 1 - 0.12 * p, ry: 18 * p, op: 1 - 0.8 * p, blur: 9 * Math.sin(Math.PI * p) });
      fadeOv(prev, 1 - cl(p * 2.5));
      drawScene(cur, t, { dx: 1250 * (1 - p), sc: 0.88 + 0.12 * p, ry: -18 * (1 - p), op: 0.2 + 0.8 * p, blur: 9 * Math.sin(Math.PI * p) });
    } else if (inTr && type === "depth") {
      drawScene(prev, t); drawScene(cur, t, cur.app ? { sc: 0.78 + 0.22 * p } : null);
      prev.el.style.opacity = 1 - p; prev.el.style.transform = "scale(" + (1 + 0.12 * p) + ")"; prev.el.style.filter = "blur(" + (12 * p) + "px)";
      cur.el.style.opacity = p; if (!cur.app) cur.el.style.transform = "scale(" + (0.93 + 0.07 * p) + ")"; cur.el.style.filter = p < 1 ? "blur(" + (12 * (1 - p)) + "px)" : "";
    } else {
      if (inTr) drawScene(prev, t);
      drawScene(cur, t);
    }
    var stung = stinger(cur, t);
    if (cur.stinger) {
      if (t < cur.t0) cur.el.style.opacity = 0;
      else if (t < cur.t0 + IRIS) {
        var po = easeIO(P(t, cur.t0, IRIS)), cx = 150 + lt_.offsetWidth / 2;
        cur.el.style.opacity = 1; cur.el.style.zIndex = 55; cur.el.style.background = INK_BG;
        cur.el.style.clipPath = "circle(" + (po * 2300) + "px at " + cx + "px 540px)";
      }
    }
    var fl = 0;
    if (cur.key === "intro" || cur.key === "onehub") fl = 0.32 * (1 - P(t, cur.start, 0.28));
    FLASH.style.opacity = fl;
    return cur.key;
  };
  window.FILM_READY = true;
})();
