"""Piste finale : voix posée à ses instants, musique baissée sous la voix (compression
déclenchée par la voix), puis loudness à -14 LUFS."""
import json, subprocess, wave
from pathlib import Path
import numpy as np, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
ICI = Path(__file__).parent; RAC = ICI.parent
T = json.loads((ICI / "timing.json").read_text())
SR = 48000; N = int((T["total"] + 3) * SR)
v = np.zeros(N, np.float32)
for s in T["scenes"]:
    w = wave.open(str(RAC / "vo_final" / f"{s['key']}.wav")); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768; w.close()
    i = int(s["vo_at"] * SR); v[i:i + len(a)] += a[:N - i]
with wave.open(str(ICI / "vo_track.wav"), "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(v, -1, 1) * 32767).astype(np.int16).tobytes())
fc = ("[1:a]aresample=48000,volume=0.42[m];[0:a]asplit=2[vo][sc];"
      "[m][sc]sidechaincompress=threshold=0.02:ratio=5:attack=15:release=350:makeup=1[md];"
      "[vo]highpass=f=70,acompressor=threshold=0.1:ratio=3:attack=5:release=120:makeup=1.6[vc];"
      "[vc][md]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.2:LRA=9[out]")
subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(ICI / "vo_track.wav"), "-i", str(ICI / "music.wav"),
                "-filter_complex", fc, "-map", "[out]", "-ar", "48000", "-ac", "2", str(ICI / "mix.wav")], check=True)
print("mix ok")
