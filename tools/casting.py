"""Casting : la même réplique par plusieurs voix graves, puis hauteur (F0 médiane) et débit."""
import json, base64, urllib.request, wave, struct, math, sys, time
from pathlib import Path
ICI = Path(__file__).parent
def _key():
    import os
    k = os.environ.get("GEMINI_API_KEY")
    if not k:
        env = Path(__file__).resolve().parent.parent / ".env"
        if env.exists():
            for l in env.read_text().splitlines():
                if l.startswith("GEMINI_API_KEY="): k = l.split("=", 1)[1].strip()
    if not k: raise SystemExit("GEMINI_API_KEY manquante : la mettre dans .env (voir .env.example)")
    return k
KEY = _key()
LINE = "Introducing OneSearch Hub. One place to run your entire Search strategy. Every platform. Every team. Every result."
STYLE = "deep, powerful keynote launch narrator for a high-energy product film, punchy and fast, confident, American English"
VOICES = sys.argv[1].split(",")

def f0_median(path):
    w = wave.open(str(path)); sr = w.getframerate(); n = w.getnframes()
    s = struct.unpack("<%dh" % n, w.readframes(n)); w.close()
    s = [sum(s[i:i + 3]) / 3 for i in range(0, len(s) - 2, 3)]; sr //= 3      # 8 kHz
    win, hop, f0s = 320, 160, []
    lo, hi = sr // 260, sr // 60
    for st in range(0, len(s) - win - hi, hop):
        fr = s[st:st + win + hi]
        e = sum(x * x for x in fr[:win]) / win
        if e < 2.5e5: continue
        best, bl = 0, 0
        for lag in range(lo, hi):
            c = sum(fr[i] * fr[i + lag] for i in range(0, win, 2))
            if c > best: best, bl = c, lag
        if best > 0.45 * sum(x * x for x in fr[:win:2]) and bl:
            f0s.append(sr / bl)
    f0s.sort()
    return f0s[len(f0s) // 2] if f0s else 0, len(f0s)

for v in VOICES:
    body = {"model": "gemini-3.8-flash-tts",
            "input": [{"type": "user_input", "content": [{"type": "text", "text": LINE,
                       "annotations": [{"type": "speech_metadata", "style": STYLE}]}]}],
            "response_format": {"type": "audio"}, "generation_config": {"speech_config": [{"voice": v}]}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/interactions", data=json.dumps(body).encode(),
                                 method="POST", headers={"x-goog-api-key": KEY, "Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=90).read())
    except Exception as e:
        print(v, "ÉCHEC", e); continue
    a = [c for st in r.get("steps", []) if st.get("type") == "model_output" for c in st.get("content", []) if c.get("type") == "audio"]
    out = ICI / "voix" / f"{v}.wav"; out.write_bytes(base64.b64decode(a[-1]["data"]))
    w = wave.open(str(out)); d = w.getnframes() / w.getframerate(); w.close()
    f0, nv = f0_median(out)
    print(f"{v:<20} F0 médiane {f0:6.1f} Hz ({nv} trames voisées) · {d:5.2f} s · {len(LINE.split()) / d * 60:5.0f} mots/min")
