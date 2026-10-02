# OneSearch Hub — le film de lancement

Le film de keynote « OneSearch Hub by MentionBox » : 1 min 43, 21 scènes, en anglais. Tout
y est du code : les écrans sont des pages HTML, l'animation une fonction JavaScript
`render(t)`, et la vidéo est capturée image par image par un Chromium piloté par
Playwright, puis assemblée par ffmpeg.

Deux montages partagent les mêmes écrans, la même voix et le même minutage :

| | Page | Moteur | Style |
|---|---|---|---|
| **V1 · sobre** | `film.html` | `film/engine.js` | écrans plein cadre, coupes sur les temps, caméra qui zoome dans l'interface |
| **V2 · motion** | `film_motion.html` | `film/engine_motion.js` | fenêtres flottantes sur fond animé, glissés en profondeur, ouvertures en cercle, mots révélés par masque |

Toutes les données sont fictives (marque « Velox », personnes, chiffres).

> **`onesearch-hub-film-code.zip`** : le même code en archive, figé au 2 octobre 2026. Le
> dépôt fait foi ; GitHub produit aussi une archive à jour par *Code › Download ZIP*.

## Installer

Il faut Node 20 ou plus et Python 3.10 ou plus.

```bash
npm install
npx playwright install chromium
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # seulement pour régénérer la voix
```

`imageio-ffmpeg` fournit un ffmpeg complet (x264, AAC) : rien d'autre à installer. Pour
utiliser un autre ffmpeg, définir `FFMPEG=/chemin/vers/ffmpeg` ; pour un autre Chromium,
`CHROMIUM_PATH=…`.

## Faire le film

```bash
./run.sh all                  # tout, des planches aux deux films → dist/
./run.sh render v2            # un seul montage
./run.sh render v2 40 55      # un extrait, de 40 s à 55 s, pour essayer vite
./run.sh preview v2           # une image par scène → film/sheet1.png, sheet2.png
```

Un rendu complet prend 3 à 5 minutes sur 8 cœurs (deux pages Chromium en parallèle). Il
sort dans `dist/` trois fichiers par montage : le 1080p complet (~40 Mo), un 1080p léger
(~15 Mo) et un 720p.

La voix est déjà générée (`vo_sent/`) : `./run.sh all` ne rappelle pas Gemini.

## La chaîne

```
template.html ─ build.py ─→ onesearch-storyboard.html   (planches : écrans, notes, voix par scène)
     │              └──────→ vo_text.json               (texte de la voix, scène par scène)
     │
vo_text.json ─ tts_sent.py (Gemini) ─→ vo_sent/<scène>_<n>.wav + vo_sent.json   (une phrase = un fichier)
     │
vo_sent ─ film/timing.py ─→ film/timing.json + vo_final/     (instant exact de chaque phrase, calé à 124 BPM)
timing ─ film/music.py ──→ film/music.wav                   (musique de travail, synthétisée)
timing ─ film/mix.py ────→ film/mix.wav                     (voix + musique baissée sous la voix, -14 LUFS)
storyboard + timing ─ film/make_film.py ─→ film.html  ·  film/make_film_motion.py ─→ film_motion.html
film*.html ─ film/render.js ─→ film/out_v*/seg*.mp4 ─ film/assemble.py ─→ dist/*.mp4
```

## Fichiers

| Fichier | Rôle |
|---|---|
| `template.html` | Les planches : HTML de chaque écran (`.stage`, 1280 × 720), voix (`.vo-t`), texte à l'écran (`.ovl`), notes de production. **Seule source du texte de la voix.** |
| `build.py` | Remplit les `@@MARQUEURS@@` du gabarit : graphes SVG calculés, tableaux, planning, code QR, numérotation et minutage. Sort `onesearch-storyboard.html` et `vo_text.json`. |
| `tts_sent.py` | Voix Gemini TTS phrase par phrase (`gemini-3.8-flash-tts`, voix `algieba`), silences coupés, débit +10 %. |
| `film/timing.py` | Pose chaque phrase sur la grille au quart de temps et fixe la durée de chaque scène en nombre entier de temps. |
| `film/music.py`, `film/mix.py` | Musique synthétisée (la mineur, 124 BPM) et mixage. |
| `film/engine.js`, `film/engine_motion.js` | Les moteurs d'animation V1 et V2. |
| `film/render.js`, `film/assemble.py` | Capture et assemblage. |
| `storyboard_audio.py` | Sons des lecteurs des planches (`audio/`). |
| `shoot.js` | Contrôle des planches : textes rognés, qui débordent de leur carte ou du cadre. |
| `tools/casting.py` | Fait dire la même phrase à plusieurs voix et mesure leur hauteur. |
| `fonts/` | Swiza et General Sans : **polices sous licence MentionBox, à ne pas publier.** |
| `lucide.js` | Icônes Lucide (licence ISC). |

## Modifier

**Un texte de la voix.** Le changer dans `template.html` (`<p class="vo-t">` de la scène).
Puis `./run.sh voice <clé>` régénère les phrases de cette scène (clés : `one-box`,
`everywhere`, `pieces`, `intro`, `overview`, `six`, `collect`, `rank`, `score`, `recommend`,
`ai-answer`, `coordinate`, `timeline`, `launch`, `formats`, `evaluate`, `traced`, `report`,
`circle`, `onehub`, `cta`). Le minutage, la musique, le mixage et les pages suivent, puis
`./run.sh render v2`. Une phrase est découpée sur `.`, `?` et `!` : chaque phrase est un
appel Gemini facturé, et un repère d'animation.

**Le texte à l'écran.** `<div class="ovl">` reprend **mot pour mot** une ou plusieurs phrases
de la voix : chaque mot s'affiche à l'instant où il est prononcé. Si le texte diffère de la
voix, l'œil et l'oreille se contredisent et le spectateur perçoit un décalage. La phrase de
départ se règle par `s.ovlFrom` dans le moteur.

**Un écran.** Le HTML est dans `template.html` ; les graphes, tableaux et le planning sont
calculés dans `build.py` (chercher le marqueur, par exemple `GANTT`, `CONV_CHART`). Ensuite
`./run.sh pages`, puis `./run.sh preview v2`, puis `node shoot.js` pour vérifier qu'aucun
texte n'est coupé.

**Le moment où un bloc apparaît.** Dans le moteur, section « réglages par scène » :
`cue(s, i)` est l'instant de la phrase `i` de la scène ; `u.at` l'instant d'apparition d'un
bloc ; `LEAD` (60 ms) l'avance de l'image sur la voix ; `s.cams` (V1) les mouvements de
caméra. En V2, la fenêtre et les transitions sont réglées dans `camera()` et
`window.render`.

**La musique.** `film/music.py` synthétise une piste de travail. Pour un titre sous licence :
le caler à 124 BPM (ou changer `BPM` dans `film/timing.py`, toutes les coupes suivent), le
convertir en `film/music.wav` (mono ou stéréo, même durée que le film), puis
`python film/mix.py`. La musique est baissée automatiquement sous la voix.

**La voix.** Voix et style dans `tts_sent.py` (`VOICE`, `BASE`, `STYLE`). Pour comparer des
voix : `python tools/casting.py algieba,charon,algenib`.

## À savoir

- `render(t)` est **sans état** : elle recalcule toute l'image à l'instant `t`. On peut donc
  rendre n'importe quelle image, dans n'importe quel ordre, en parallèle. Toute nouvelle
  animation doit rester une fonction du temps, jamais d'une image précédente.
- La V1 met l'interface à l'échelle avec `zoom` (une échelle initiale par défaut avait
  faussé le dessin des textes SVG dans Chrome) ; la V2 utilise `transform`, sans souci une
  fois les polices chargées. Les deux attendent `document.fonts.ready`.
- Geist Mono est chargée depuis Google Fonts : le rendu a besoin d'Internet, ou d'une copie
  locale de la police.
- La section « Le film » des planches lit des vidéos publiées à part (`filmweb/`) : en local,
  copier les fichiers de `dist/` dans `filmweb/` sous les noms attendus, ou ignorer ces lecteurs.
- Durée visée : 1 min 30 à 1 min 45. `film/timing.py` affiche la durée totale.
- La clé Gemini vit dans `.env`, jamais dans le code ni dans Git.
