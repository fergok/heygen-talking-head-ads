"""Thumbnail sheets for reviewing clips. Writes work/sheet_NN.jpg.

Usage: python -I sheets.py <project>            every clip in src/, 4 frames each, 8 clips per sheet
       python -I sheets.py <project> <clip> [fps]   one clip with timecodes, for choosing an exact in-point
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I leaves the script folder off the path
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw, ImageFont

from common import FF, probe_duration, project, run

project()
if len(sys.argv) > 2:
    n, fps = sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "1"
    run(["-i", f"src/{n}.mov", "-vf", f"fps={fps},scale=150:-2,drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:"
         "text='%{pts\\:hms}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black,tile=9x5", "-frames:v", "1", f"work/t_{n}.jpg"])
    raise SystemExit(f"work/t_{n}.jpg")

os.makedirs("work/thumbs", exist_ok=True)
names = sorted(os.path.splitext(f)[0] for f in os.listdir("src") if f.lower().endswith((".mov", ".mp4")))
ext = {os.path.splitext(f)[0]: f for f in os.listdir("src")}

def thumbs(n):
    d = probe_duration(f"src/{ext[n]}"); out = []
    for k, fr in enumerate((0.08, 0.35, 0.62, 0.9)):
        o = f"work/thumbs/{n}_{k}.jpg"
        if not os.path.exists(o):
            subprocess.run(["nice", "-n", "10", FF, "-nostdin", "-loglevel", "error", "-ss", f"{d * fr:.2f}", "-i", f"src/{ext[n]}",
                            "-frames:v", "1", "-vf", "scale=150:266:force_original_aspect_ratio=decrease,pad=150:266:(ow-iw)/2:(oh-ih)/2", "-y", o])
        out.append(o)
    return n, d, out

with ThreadPoolExecutor(4) as ex: rows = list(ex.map(thumbs, names))
fnt = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
for s in range(0, len(rows), 8):
    chunk = rows[s:s + 8]
    sheet = Image.new("RGB", (1280, ((len(chunk) + 1) // 2) * 300), "white"); d = ImageDraw.Draw(sheet)
    for i, (n, du, ths) in enumerate(chunk):
        x0, y0 = (i % 2) * 640, (i // 2) * 300
        d.text((x0 + 4, y0 + 2), f"{n} ({du:.0f}s)", fill="black", font=fnt)
        for k, t in enumerate(ths):
            if os.path.exists(t): sheet.paste(Image.open(t), (x0 + 4 + k * 156, y0 + 28))
    sheet.save(f"work/sheet_{s // 8:02d}.jpg", quality=80)
print(len(rows), "clips,", -(-len(rows) // 8), "sheets in work/")
