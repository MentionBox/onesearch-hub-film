"""Sons des planches : une réplique par planche (vo_final/<clé>.wav) et la bande-son complète
du film (film/mix.wav), encodées en AAC dans audio/ pour les lecteurs de la page."""
import subprocess
from pathlib import Path
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
ICI = Path(__file__).parent; A = ICI / "audio"; A.mkdir(exist_ok=True)
for w in sorted((ICI / "vo_final").glob("*.wav")):
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(w), "-c:a", "aac", "-b:a", "96k", str(A / f"{w.stem}.mp4")], check=True)
subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(ICI / "film" / "mix.wav"), "-c:a", "aac", "-b:a", "160k", str(A / "voix-off.mp4")], check=True)
print(len(list(A.glob("*.mp4"))), "fichiers dans audio/")
