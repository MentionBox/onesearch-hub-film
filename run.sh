#!/usr/bin/env bash
# Chaîne du film OneSearch Hub. Voir README.md.
#   ./run.sh all            tout refaire, des planches aux deux films (sans rappeler Gemini)
#   ./run.sh pages          planches + pages du film, après une modification d'écran ou de texte
#   ./run.sh audio          minutage, musique, mixage, après une modification de la voix
#   ./run.sh voice [clés]   régénère la voix avec Gemini (payant) : toutes les phrases, ou les scènes listées (ex. cta,score)
#   ./run.sh preview [v1|v2]  une image par scène → film/sheet*.png
#   ./run.sh render [v1|v2] [de] [à]   rend un film (ou un extrait en secondes) → dist/
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
film_of() { [ "${1:-v2}" = v1 ] && echo film.html || echo film_motion.html; }
pages() { $PY build.py; $PY film/make_film.py; $PY film/make_film_motion.py; }
audio() { $PY film/timing.py; $PY film/music.py; $PY film/mix.py; $PY storyboard_audio.py; }
render() {
  local v=${1:-v2} extra=()
  [ -n "${2:-}" ] && extra+=(--from "$2"); [ -n "${3:-}" ] && extra+=(--to "$3")
  node film/render.js --film "$(film_of "$v")" --out "film/out_$v" "${extra[@]}"
  $PY film/assemble.py "$v"
}
case "${1:-all}" in
  voice)   $PY build.py; $PY tts_sent.py ${2:-}; audio; pages ;;
  audio)   audio; pages ;;
  pages)   pages ;;
  preview) node film/preview.js --film "$(film_of "${2:-v2}")" ;;
  render)  render "${2:-v2}" "${3:-}" "${4:-}" ;;
  all)     audio; pages; render v1; render v2 ;;
  *) sed -n '2,9p' "$0"; exit 1 ;;
esac
