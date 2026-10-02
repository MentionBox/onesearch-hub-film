"""Minutage du film, v2 : la voix est générée phrase par phrase, donc l'instant de chaque
phrase est connu exactement (plus de repérage dans les silences). Chaque phrase démarre sur
la grille au quart de temps (124 BPM) ; chaque scène dure un nombre entier de temps.
Écrit aussi, pour chaque scène, la réplique assemblée (vo_final/<clé>.wav) que lisent le
mixage et les lecteurs des planches."""
import json, math, wave
from pathlib import Path
import numpy as np
ICI = Path(__file__).parent; RAC = ICI.parent
BPM = 124; BEAT = 60 / BPM; Q = BEAT / 4
SR = 48000
SENT = json.loads((RAC / "vo_sent.json").read_text())
ORDER = list(json.loads((RAC / "vo_text.json").read_text()).keys())
N = {k: f"{i + 1:02d}" for i, k in enumerate(ORDER)}
STINGER = {"collect", "rank", "recommend", "coordinate", "launch", "evaluate"}
TITLE = {"one-box", "everywhere", "pieces", "intro", "six", "circle", "onehub", "cta"}
GAP = 0.02                                  # silence minimal entre deux phrases, avant calage
(RAC / "vo_final").mkdir(exist_ok=True)

def rd(p):
    w = wave.open(str(p)); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768; w.close(); return a

out, t = [], 0.0
for k in ORDER:
    start = t
    cur = start + BEAT / 2
    sents = []
    for i, s in enumerate(SENT[k]):
        at = math.ceil((cur - 1e-6) / Q) * Q          # calé au quart de temps
        sents.append({"text": s["text"], "at": round(at, 4), "dur": s["dur"]})
        cur = at + s["dur"] + GAP
    end_voice = sents[-1]["at"] + sents[-1]["dur"]
    beats = max(math.ceil((end_voice + 0.15 - start) / BEAT), 6 if k in TITLE else 7) + (3 if k == "cta" else 0)
    vo_at = sents[0]["at"]
    # réplique assemblée, la première phrase à 0
    buf = np.zeros(int((end_voice - vo_at + 0.1) * SR), np.float32)
    for i, s in enumerate(sents):
        a = rd(RAC / "vo_sent" / f"{k}_{i}.wav"); j = int((s["at"] - vo_at) * SR); buf[j:j + len(a)] += a[:len(buf) - j]
    with wave.open(str(RAC / "vo_final" / f"{k}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(buf, -1, 1) * 32767).astype(np.int16).tobytes())
    out.append({"key": k, "n": N[k], "start": round(start, 4), "beats": beats, "dur": round(beats * BEAT, 4),
                "vo_at": round(vo_at, 4), "vo_dur": round(end_voice - vo_at, 3), "stinger": k in STINGER, "sentences": sents, "how": "exact"})
    print(f"{N[k]} {k:<11} {beats:>3} temps = {beats * BEAT:5.2f} s · voix {end_voice - vo_at:5.2f} s · {len(sents)} phrases")
    t += beats * BEAT
(ICI / "timing.json").write_text(json.dumps({"bpm": BPM, "beat": BEAT, "total": round(t, 4), "scenes": out}, indent=1, ensure_ascii=False))
print(f"total {t:.2f} s = {int(t // 60)}:{int(t % 60):02d}")
