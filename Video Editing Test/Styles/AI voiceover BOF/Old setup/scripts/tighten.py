"""Remove dead air: every pause in the voiceover becomes a short breath. Writes work/vo_tight.wav.

Usage: python -I tighten.py <project> [noise_db=-31] [min_pause=0.13]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I leaves the script folder off the path
import re, subprocess, sys

from common import FF, config, probe_duration, project, run

project()
noise = sys.argv[2] if len(sys.argv) > 2 else "-31"
min_pause = sys.argv[3] if len(sys.argv) > 3 else "0.13"
EDGE = 0.04  # kept either side of each pause, so a pause becomes an ~80ms breath and word tails survive

vo = config()["voiceover"]
total = probe_duration(vo)
log = subprocess.run([FF, "-nostdin", "-i", vo, "-af", f"silencedetect=noise={noise}dB:d={min_pause}", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
ends += [total] * (len(starts) - len(ends))

keep, t = [], 0.0
for a, b in zip(starts, ends):
    if a > t: keep.append((t, min(a + EDGE, total)))
    t = max(b - EDGE, 0.0)
if t < total - 0.05: keep.append((t, total))

n = len(keep)
fc = f"[0:a]asplit={n}" + "".join(f"[i{k}]" for k in range(n)) + ";"
fc += "".join(f"[i{k}]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st={b - a - 0.008:.3f}:d=0.008[p{k}];"
              for k, (a, b) in enumerate(keep))
fc += "".join(f"[p{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1[a]"
run(["-i", vo, "-filter_complex", fc, "-map", "[a]", "-ar", "48000", "work/vo_tight.wav"])
print(f"{len(starts)} pauses trimmed: {total:.2f}s -> {probe_duration('work/vo_tight.wav'):.2f}s")
