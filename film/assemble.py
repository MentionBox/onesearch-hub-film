"""Assemble un montage rendu : recolle les tranches, ajoute la bande-son (film/mix.wav) et
sort trois fichiers dans dist/ : le 1080p complet, un 1080p léger (~15 Mo, deux passes à
1 Mb/s) et un 720p.      python film/assemble.py v2"""
import subprocess, sys
from pathlib import Path
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
ICI = Path(__file__).parent; RAC = ICI.parent
v = sys.argv[1] if len(sys.argv) > 1 else "v2"
OUT = ICI / f"out_{v}"; DIST = RAC / "dist"; DIST.mkdir(exist_ok=True)
name = {"v1": "OneSearchHub_film_V1_sobre", "v2": "OneSearchHub_film_V2_motion"}.get(v, f"OneSearchHub_film_{v}")
segs = sorted(OUT.glob("seg*.mp4"), key=lambda p: int(p.stem[3:]))
assert segs, f"aucune tranche dans {OUT} : lancer d'abord film/render.js"
(OUT / "list.txt").write_text("".join(f"file '{p.name}'\n" for p in segs))
run = lambda *a: subprocess.run([FF, "-y", "-loglevel", "error", *a], check=True, cwd=OUT)
run("-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "video.mp4")
full = DIST / f"{name}_1080p.mp4"
import json
meta = json.loads((OUT / "meta.json").read_text()) if (OUT / "meta.json").exists() else {"from": 0}
run("-i", "video.mp4", "-ss", str(meta["from"]), "-i", str(ICI / "mix.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(full))
web = DIST / f"{name}_1080p_web.mp4"
run("-i", str(full), "-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-b:v", "1000k", "-pass", "1", "-an", "-f", "mp4", "/dev/null" if sys.platform != "win32" else "NUL")
run("-i", str(full), "-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-b:v", "1000k", "-pass", "2", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(web))
run("-i", str(full), "-vf", "scale=1280:720:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(DIST / f"{name}_720p.mp4"))
for f in sorted(DIST.glob(f"{name}_*.mp4")):
    print(f"{f.relative_to(RAC)} : {f.stat().st_size / 1e6:.1f} Mo" + (f" (extrait à partir de {meta['from']:.1f} s)" if meta["from"] else ""))
