#!/usr/bin/env python3
"""Contact sheets for choosing B-roll: one timestamped sheet per clip, then labelled pages of four to read.

    contact_sheets.py <workdir> <clip> [<clip> ...]   writes <workdir>/sheets/*.jpg and <workdir>/page_NN.jpg
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

B = os.path.expanduser("~/Video Editing Test/tools/venv/bin/")
FONT = os.path.expanduser("~/Video Editing Test/tools/fonts/Arial Black.ttf")


def sheet(args):
    wd, f = args
    n = os.path.splitext(os.path.basename(f))[0]
    # this ffprobe build always prints JSON, so read duration from it
    j = json.loads(subprocess.run([B + "ffprobe", "-v", "error", "-of", "json", "-show_entries", "format=duration", f],
                                  capture_output=True, text=True).stdout)
    d = float(j["format"]["duration"])
    step = max(0.4, d / 12)
    font = os.path.join(wd, "font.ttf")   # drawtext can't take a path with spaces
    subprocess.run([B + "ffmpeg", "-v", "error", "-y", "-i", f, "-vf",
                    f"fps=1/{step:.3f},scale=200:-2,drawtext=fontfile={font}:text='%{{pts\\:flt}}':x=3:y=3:fontsize=14:fontcolor=yellow:box=1:boxcolor=black,tile=6x2",
                    "-frames:v", "1", os.path.join(wd, "sheets", n + ".jpg")])
    return n, d


if __name__ == "__main__":
    wd, clips = sys.argv[1], sys.argv[2:]
    os.makedirs(os.path.join(wd, "sheets"), exist_ok=True)
    subprocess.run(["cp", FONT, os.path.join(wd, "font.ttf")])
    with ThreadPoolExecutor(8) as ex:
        for n, d in ex.map(sheet, [(wd, c) for c in clips]):
            print(f"{n} {d:.1f}s")
    fs = sorted(os.path.join(wd, "sheets", x) for x in os.listdir(os.path.join(wd, "sheets")) if x.endswith(".jpg"))
    f = ImageFont.truetype(FONT, 26)
    for g in range(0, len(fs), 4):
        ims = [(x, Image.open(x)) for x in fs[g:g + 4]]
        cw = max(i.width for _, i in ims); ch = max(i.height for _, i in ims) + 34
        out = Image.new("RGB", (cw * 2, ch * 2))
        for k, (x, i) in enumerate(ims):
            X, Y = (k % 2) * cw, (k // 2) * ch
            ImageDraw.Draw(out).text((X + 5, Y + 3), os.path.basename(x)[:-4], fill=(0, 255, 255), font=f)
            out.paste(i, (X, Y + 34))
        out.save(os.path.join(wd, f"page_{g // 4:02d}.jpg"), quality=82)
