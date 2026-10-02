"""Voix phrase par phrase : un appel Gemini TTS par phrase, ce qui donne l'instant exact de
chaque phrase au montage. Silences coupés, débit +10 % sans changer la hauteur."""
import json, re, base64, urllib.request, subprocess, wave, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
ICI = Path(__file__).parent
def _key():
    import os
    k = os.environ.get("GEMINI_API_KEY")
    if not k:
        env = Path(__file__).resolve().parent / ".env"
        if env.exists():
            for l in env.read_text().splitlines():
                if l.startswith("GEMINI_API_KEY="): k = l.split("=", 1)[1].strip()
    if not k: raise SystemExit("GEMINI_API_KEY manquante : la mettre dans .env (voir .env.example)")
    return k
KEY = _key()
VOICE = "algieba"
BASE = "deep, low-register, powerful keynote narrator for a premium SaaS launch film, confident, American English, fast-paced and energetic, punchy"
STYLE = {"one-box": "calm and intimate", "pieces": "slightly tense, questioning", "intro": "a confident, proud reveal",
         "onehub": "warm, signature line", "cta": "bold, inspiring, a strong final push"}
TEXT = json.loads((ICI / "vo_text.json").read_text())
(ICI / "vo_sent").mkdir(exist_ok=True)
jobs = []
for k, txt in TEXT.items():
    for i, s in enumerate(re.split(r"(?<=[.?!])\s+", txt.strip())):
        jobs.append((k, i, s))
ONLY = set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None

def one(job):
    k, i, s = job
    if ONLY and k not in ONLY: return (k, i, s, None, "skip")
    style = BASE + ", " + STYLE.get(k, "energetic, rhythmic")
    body = {"model": "gemini-3.8-flash-tts", "input": [{"type": "user_input", "content": [{"type": "text", "text": s,
            "annotations": [{"type": "speech_metadata", "style": style}]}]}],
            "response_format": {"type": "audio"}, "generation_config": {"speech_config": [{"voice": VOICE}]}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/interactions", data=json.dumps(body).encode(),
                                 method="POST", headers={"x-goog-api-key": KEY, "Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=90).read())
    except Exception as e:
        return (k, i, s, None, f"ÉCHEC {e}")
    a = [c for st in r.get("steps", []) if st.get("type") == "model_output" for c in st.get("content", []) if c.get("type") == "audio"]
    if not a: return (k, i, s, None, "sans audio")
    raw = ICI / "vo_sent" / f"{k}_{i}.raw.wav"; raw.write_bytes(base64.b64decode(a[-1]["data"]))
    out = ICI / "vo_sent" / f"{k}_{i}.wav"
    af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,"
          "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04,areverse,atempo=1.10")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(raw), "-af", af, "-ar", "48000", "-ac", "1", str(out)], check=True)
    w = wave.open(str(out)); d = w.getnframes() / w.getframerate(); w.close()
    return (k, i, s, round(d, 3), "ok")

t0 = time.time()
with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(one, jobs))
man = {}
for k, i, s, d, st in res:
    if st == "skip": continue
    print(f"{k:<11} {i} {d if d else '-':>6} s  {st:<4} {s}")
    if d: man.setdefault(k, {})[i] = {"text": s, "dur": d}
prev = json.loads((ICI / "vo_sent.json").read_text()) if (ICI / "vo_sent.json").exists() and ONLY else {}
for k, v in man.items(): prev[k] = [v[i] for i in sorted(v)]
(ICI / "vo_sent.json").write_text(json.dumps(prev, ensure_ascii=False, indent=1))
print(f"{sum(1 for r in res if r[4] == 'ok')} phrases en {time.time() - t0:.0f} s")
