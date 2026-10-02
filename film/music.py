"""Musique de travail, synthétisée : 124 BPM, la mineur, la–fa–do–sol. Provisoire —
à remplacer par un titre sous licence. Suit la structure du film lue dans timing.json."""
import json, wave
from pathlib import Path
import numpy as np
ICI = Path(__file__).parent
T = json.loads((ICI / "timing.json").read_text())
SR, BEAT = 44100, T["beat"]
TOT = T["total"] + 3.0
N = int(TOT * SR)
S = {s["key"]: s["start"] for s in T["scenes"]}
END = T["total"]
rng = np.random.default_rng(3)
tr = {k: np.zeros(N, np.float32) for k in ["kick", "clap", "hat", "bass", "pad", "stab", "arp", "fx"]}

def put(track, t, x, g=1.0):
    i = int(t * SR)
    if i >= N: return
    x = x[:N - i]; tr[track][i:i + len(x)] += g * x

def lp(x, fc):           # passe-bas par FFT
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / fc) ** 4); return np.fft.irfft(X, len(x)).astype(np.float32)

def hp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (fc / np.maximum(f, 1)) ** 4); return np.fft.irfft(X, len(x)).astype(np.float32)

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def saw(f, n, harm=12):
    t = np.arange(n) / SR; x = np.zeros(n, np.float32)
    for k in range(1, harm + 1):
        if k * f > 9000: break
        x += np.sin(2 * np.pi * k * f * t) / k
    return x

kick_s = (lambda t: (np.sin(2 * np.pi * np.cumsum(46 + 110 * np.exp(-t * 32)) / SR) * np.exp(-t * 6.5)
                     + 0.4 * rng.standard_normal(len(t)) * np.exp(-t * 300)).astype(np.float32))(np.arange(int(0.42 * SR)) / SR)
clap_s = hp(lp(rng.standard_normal(int(0.25 * SR)).astype(np.float32), 3500), 900) * env(int(0.25 * SR), 0.001, 0.07)
hat_s = hp(rng.standard_normal(int(0.07 * SR)).astype(np.float32), 7000) * env(int(0.07 * SR), 0.0005, 0.018)
ohat_s = hp(rng.standard_normal(int(0.3 * SR)).astype(np.float32), 6500) * env(int(0.3 * SR), 0.001, 0.12)
boom_s = (np.sin(2 * np.pi * np.cumsum(38 + 50 * np.exp(-np.arange(int(2.2 * SR)) / SR * 3)) / SR) * env(int(2.2 * SR), 0.002, 0.7)).astype(np.float32)
crash_s = hp(rng.standard_normal(int(2.0 * SR)).astype(np.float32), 3000) * env(int(2.0 * SR), 0.001, 0.55)

def impact(t, g=1.0):
    put("fx", t, boom_s, 0.9 * g); put("fx", t, crash_s, 0.35 * g); put("kick", t, kick_s, 1.0 * g)

def riser(t0, t1, g=0.5):
    n = int((t1 - t0) * SR); x = rng.standard_normal(n).astype(np.float32)
    ramp = np.linspace(0, 1, n) ** 2.2
    x = hp(x, 1500) * ramp
    tt = np.arange(n) / SR; f = 200 + 1400 * (tt / tt[-1]) ** 2
    x += 0.25 * np.sin(2 * np.pi * np.cumsum(f) / SR).astype(np.float32) * ramp
    put("fx", t0, x, g)

def snare_roll(t0, beats, g=0.6):
    k = int(beats * 4)
    for i in range(k):
        put("clap", t0 + i * BEAT / 4, clap_s, g * (0.35 + 0.65 * i / k))

# progression : 2 mesures par accord
CH = [("A", [220.0, 261.63, 329.63, 392.0], 55.0), ("F", [174.61, 220.0, 261.63, 329.63], 43.65),
      ("C", [196.0, 261.63, 329.63, 392.0], 65.41), ("G", [196.0, 246.94, 293.66, 392.0], 49.0)]
def chord_at(t):
    return CH[int(t // (8 * BEAT)) % 4]

def section(t):
    if t < S["everywhere"]: return "intro0"
    if t < S["intro"]: return "tension"
    if t < S["six"]: return "full"
    if t < S["collect"]: return "drop"
    if t < S["circle"]: return "full+" if t >= S["recommend"] else "full"
    if t < S["onehub"]: return "break"
    if t < S["cta"]: return "hold"
    return "outro" if t < END - BEAT * 2 else "end"

nb = int(END / BEAT)
for b in range(nb):
    t = b * BEAT; sec = section(t); beat_in_bar = b % 4
    name, notes, root = chord_at(t)
    if sec in ("full", "full+", "outro"):
        put("kick", t, kick_s, 0.95 if sec != "outro" else 0.75)
        if beat_in_bar in (1, 3): put("clap", t, clap_s, 0.55)
        put("hat", t + BEAT / 2, hat_s, 0.32)
        if sec == "full+": put("hat", t + BEAT / 4, hat_s, 0.14); put("hat", t + 3 * BEAT / 4, hat_s, 0.14)
        if beat_in_bar == 3 and (b // 4) % 2 == 1: put("hat", t + BEAT / 2, ohat_s, 0.22)
        # basse « pushy » : croches, octave sur le contretemps
        for j, (mul, g) in enumerate([(1, 0.9), (2, 0.6)]):
            n = int(BEAT / 2 * SR * 0.9)
            put("bass", t + j * BEAT / 2, saw(root * mul, n, 10) * env(n, 0.004, 0.16), g)
        if beat_in_bar in (1, 3) or sec == "full+":
            n = int(0.22 * SR)
            st = sum(saw(f * 2, n, 6) for f in notes[1:]) * env(n, 0.002, 0.06)
            put("stab", t + BEAT / 2, st, 0.10)
    elif sec == "tension":
        if beat_in_bar == 0: put("kick", t, kick_s, 0.55)
        put("hat", t + BEAT / 2, hat_s, 0.18)
        if beat_in_bar == 2: put("clap", t, clap_s, 0.18)
    if sec in ("full+", "break"):
        for j in range(4):
            n = int(BEAT / 4 * SR * 0.8)
            f = notes[(b * 4 + j) % 4] * 2
            put("arp", t + j * BEAT / 4, saw(f, n, 5) * env(n, 0.002, 0.07), 0.07 if sec == "full+" else 0.09)

# nappe : une note tenue par accord, partout sauf le silence final
t = 0.0
while t < END - BEAT:
    name, notes, root = chord_at(t); n = int(8 * BEAT * SR)
    x = sum(saw(f * d, n, 8) for f in notes[:3] for d in (0.996, 1.004))
    a = np.minimum(1, np.arange(n) / (0.6 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.4 * SR))
    put("pad", t, (x * a).astype(np.float32), 0.05)
    t += 8 * BEAT

# moments
riser(S["intro"] - 4 * BEAT * 2, S["intro"], 0.55); snare_roll(S["intro"] - 4 * BEAT, 4, 0.55); impact(S["intro"], 1.0)
riser(S["six"], S["collect"], 0.45); snare_roll(S["collect"] - 2 * BEAT, 2, 0.5)
for k in ["collect", "rank", "recommend", "coordinate", "launch", "evaluate"]:
    impact(S[k], 0.55 if k != "collect" else 0.85)
    if k != "collect": snare_roll(S[k] - BEAT, 1, 0.35)
riser(S["circle"] + 2 * BEAT, S["onehub"], 0.5); impact(S["onehub"], 1.0); impact(S["cta"], 0.6)
impact(END - 2 * BEAT, 0.9)

# traitements : passe-bas sur basse et nappe, réverbe par convolution, sidechain du kick
tr["bass"] = lp(tr["bass"], 420); tr["pad"] = lp(tr["pad"], 1400); tr["stab"] = lp(tr["stab"], 3200)
for k in ["tension_lp"]: pass
mask = np.zeros(N, np.float32)
for b in range(nb):
    t = b * BEAT
    if section(t) in ("full", "full+", "outro"):
        i = int(t * SR); n = int(0.3 * SR); mask[i:i + n] = np.maximum(mask[i:i + n], np.exp(-np.arange(min(n, N - i)) / SR / 0.11))
duck = 1 - 0.65 * mask
for k in ["bass", "pad", "stab", "arp"]: tr[k] *= duck
ir = (rng.standard_normal(int(1.8 * SR)) * np.exp(-np.arange(int(1.8 * SR)) / SR / 0.45)).astype(np.float32) * 0.02
def verb(x):
    L = len(x) + len(ir); n = 1 << (L - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[:len(x)].astype(np.float32)
wet = verb(tr["pad"] + tr["stab"] + tr["arp"] + 0.5 * tr["clap"] + 0.4 * tr["fx"])
mix = (tr["kick"] * 0.9 + tr["clap"] * 0.8 + tr["hat"] * 0.7 + tr["bass"] * 0.55 + tr["pad"] + tr["stab"] + tr["arp"] + tr["fx"] * 0.8 + wet * 0.35)
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix /= np.abs(mix).max() + 1e-9
with wave.open(str(ICI / "music.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 0.89 * 32767).astype(np.int16).tobytes())
print(f"musique {TOT:.1f} s · sections : intro {S['intro']:.1f} s, étapes {S['collect']:.1f}–{S['circle']:.1f} s, fin {END:.1f} s")
