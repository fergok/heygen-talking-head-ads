#!/usr/bin/env python3
"""UGC skit template, from the finished Red Light Skit (REDSKIT). Keeps the skit's cut and audio, adds b-roll and house text.

For a new video, copy this into the working folder and replace: BROLL_SPEC, SPEED, HDR_CLIPS, CAPS, RAW_CUTS, OVERRIDE, HOOKS, CTA, MUSIC, DUR, CTA_START.
Expects raw/skit.mov, pb/<clip>.mov, click.mp3 and song.mp3 (from Assets/), and qa/spk.npz (voice activity read).
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

B = "/Users/jackferguson/Video Editing Test/tools/venv/bin/"
C = os.path.expanduser("~/Movies/CapCut/User Data/Cache/effect/")
sys.path.insert(0, os.path.expanduser("~/Video Editing Test/tools/captions"))
from house_captions import *   # the one caption and text engine for every style (rulebook 7, 11a)
DUR = 103.6
CTA_START = 98.60   # the camera pulls back to both of them

# (start, end, clip, in-point, words it illustrates, what it shows)
BROLL_SPEC = [
    (23.16, 24.50, "IMG_2705", 8.0, "in the garage", "man working in a garage wearing the headtorch"),
    (24.50, 25.60, "IMG_6502", 9.0, "dog walks", "POV night dog walk, beam on the grass"),
    (29.14, 30.48, "IMG_8585", 16.6, "230 degree beam", "orange torch held in both hands with the beam on"),
    (30.48, 32.40, "IMG_7568", 8.0, "beam", "person outdoors, wide beam lighting path and trees"),
    (32.40, 33.20, "IMG_2586", 18.9, "wave sensor", "woman wearing the torch waves her hand and it switches on"),
    (33.20, 34.60, "usb3", 11.0, "USB charging", "hands plugging the USB cable into the torch"),
    (40.50, 42.03, "IMG_6610", 0.0, "any time at night", "real man at night wearing the torch in red mode"),
    (57.08, 58.90, "hf_183646", 0.0, "stables for the horses", "girl walking with a horse in red light"),
    (58.90, 61.24, "hf_192330", 1.0, "softer on their eyes", "calm horse at a gate in red light"),
    (70.42, 73.98, "IMG_8586", 2.5, "the pink and the orange", "hands holding pink and orange torches"),
    (73.98, 74.88, "hf_101350", 1.0, "currently", "hands pitching a tent in red light"),
    (74.88, 75.90, "IMG_6614", 3.2, "a sale", "real person outdoors, trees lit by the red light"),
    (75.90, 78.00, "04RL", 0.6, "30% off", "real man waves at the torch on his head and the red light comes on"),
    (84.46, 88.22, "IMG_7339", 2.5, "free carry case", "hands unzip the logo case and open it, torch inside"),
    (93.60, 95.70, "IMG_8694", 4.0, "get one for everyone", "three torches with cases and boxes"),
]
SPEED = {"IMG_7339": 1.3}   # sped up so the whole unzip and open fits the line
HDR_CLIPS = {"IMG_8585", "IMG_8586", "IMG_8694"}   # iPhone HLG: must be converted to SDR or the colours look off

CAPS = [
    (7.03, "no I didn't look"), (8.36, "yeah a LuxeLight"), (9.12, "I've got one"), (10.50, "use your eyes babe"),
    (11.76, "yeah it's a LuxeLight"), (12.66, "oh my god"), (13.20, "use your eyes"), (14.16, "an orange LuxeLight"),
    (15.52, "yes"), (15.90, "an orange LuxeLight"), (17.28, "limited edition"), (19.02, "oh"), (19.34, "I do like the look of that"),
    (20.32, "yeah but babe"), (20.90, "this is even better"), (21.68, "right"), (21.92, "so it's still got all the same things"),
    (23.16, "because I know you use your other one"), (24.06, "in the garage"), (24.50, "and on dog walks"), (25.32, "whatever"),
    (25.60, "yeah"), (26.14, "but this one"), (27.12, "has a new feature"), (28.16, "you ready"), (28.74, "yeah"),
    (29.14, "so it's got your 230 degree beam"), (30.48, "as you love when you go on about it"),
    (32.40, "it's got your wave sensor"), (33.20, "USB charging"), (34.64, "but"), (35.20, "oh"), (35.58, "red light"),
    (36.30, "yes"), (37.04, "oh"), (37.30, "that is handy"), (38.12, "I could use this one"), (39.38, "camping"), (39.84, "fishing"),
    (40.50, "any time at night really"), (42.02, "the white light attracts bugs"), (43.06, "in my face"),
    (43.66, "I know"), (44.06, "chewing them"), (44.60, "I know"), (44.98, "it's not fun"),
    (45.76, "and the bright white is"), (47.30, "quite hard for my eyes to adjust to"),
    (48.72, "so this would probably be a lot better for that"), (50.18, "it would"), (50.76, "wouldn't it babe"),
    (51.34, "wouldn't it just be"), (51.92, "so lovely"), (53.72, "pink"), (55.26, "switch"), (55.92, "no"), (56.32, "you're not having this one"),
    (57.08, "I'm going to take this to the stables"), (58.26, "for the horses"), (58.90, "because the red light"),
    (60.04, "you know it's going to be"), (60.50, "softer on their eyes"), (61.24, "it's not going to startle"),
    (61.84, "well then you can bloody"), (62.68, "walk the dogs for once"), (64.44, "no"), (64.82, "that's your job"),
    (66.34, "come on now"), (67.36, "no"), (67.82, "you come on now"), (68.52, "and do you understand how difficult"),
    (69.56, "it was to get these"), (70.42, "right these colours are"), (71.32, "limited edition"),
    (72.16, "the pink and the orange"), (73.26, "right"), (73.98, "and they're currently"), (74.88, "doing a sale"),
    (75.90, "I think it's like 30% off"), (77.14, "or something"), (77.66, "and so they are always selling out"),
    (79.98, "I knew you would love it"), (81.32, "I do love it"), (81.88, "so I'm thinking that"),
    (84.46, "oh it also comes with"), (85.14, "a free carry case"), (85.78, "so there's one"),
    (86.54, "you probably didn't open that package yet"), (88.22, "but I'm thinking"), (89.54, "if we want to"),
    (90.46, "because they sell out all the time"), (91.52, "we probably should buy some soon"),
    (92.96, "yeah"), (93.20, "100%"), (93.60, "get one for your brother"), (94.64, "get one for everyone"),
    (95.70, "yeah"), (96.22, "okay"), (97.04, "cool"), (97.24, "fine"), (97.78, "so good present"),
]
# the skit's own camera cuts: text changes land on these when they're close
RAW_CUTS = [1.17, 4.57, 7.03, 8.07, 9.03, 10.50, 11.50, 12.67, 14.00, 18.90, 20.23, 30.93, 32.30, 34.47, 35.27, 38.10, 42.03,
            45.17, 46.13, 51.30, 53.67, 54.17, 63.87, 64.47, 78.00, 80.03, 97.60, 98.60]

HOOKS = {
    "A": dict(lines=["Marriage counselling", "is booked \U0001F923"], color=RED, ink=(255, 255, 255, 255), top=984, paren=None),
    "B": dict(lines=["He owes her an apology", "after this one \U0001F633"], color=WHITE, ink=(0, 0, 0, 255), top=984, paren=None),
    "C": dict(lines=["Meltdown pending \U0001F440\u23F3"], color=WHITE, ink=(0, 0, 0, 255), top=1049, paren="(wait for it....)"),
    "D": dict(lines=["Jealous husband", "unlocked \U0001F440"], color=WHITE, ink=(0, 0, 0, 255), top=973, paren="(over this of all things)"),
    "E": dict(lines=["Christmas gift", "drama \U0001F633\U0001F384"], color=RED, ink=(255, 255, 255, 255), top=973, paren="(he\u2019s not happy)"),
}
MUSIC = {"A", "E"}            # the two versions with the Christmas song under the dialogue
MUSIC_GAIN = 0.085            # with the compressor below: the loud part of the song sits about 5 dB lower than v5, the quiet part about 2.5 dB lower
CTA = dict(lines=["Click Shop Now for", "30% OFF + FREE CASE \U0001F6A8"], color=WHITE, ink=(0, 0, 0, 255), top=984, paren=None)



# checked by hand against the audio: speaker changes where whisper was off
OVERRIDE = {"and so they are always selling out": 78.00, "no I didn't look": 7.03, "so it's got your 230 degree beam": 29.14, "but this one": 26.06}



def snapped_caps():
    """Start each caption on the frame its first word starts, or on the skit's own camera cut if that's within a frame."""
    import numpy as np
    z = np.load("qa/spk.npz")
    t, e, voiced = z["t"], z["e"], z["lab"] != "."
    tx = json.load(open("tx/skit.json"))
    ends = sorted(w["end"] for seg in tx["segments"] for w in seg["words"])
    out, prev = [], 0.0
    for cap_t, txt in CAPS:
        new = OVERRIDE.get(txt, voice_onset(cap_t, t, e, voiced, prev, ends))
        near = [c for c in RAW_CUTS if abs(c - new) <= 0.04]
        if near:
            new = min(near, key=lambda c: abs(c - new))
        new = max(int(new * FPS + 1e-6) / FPS, prev + 6 / FPS)      # never late, and never shorter than 0.2s
        out.append((round(new, 4), txt))
        prev = new
    return out


def caption_spans():
    """Every caption holds until the next one starts, so the screen is never empty between lines."""
    caps = snapped_caps()
    return [(t, caps[i + 1][0] if i + 1 < len(caps) else fr(CTA_START), txt) for i, (t, txt) in enumerate(caps)]


def broll_shots():
    """B-roll starts and ends exactly when a caption starts, so picture and text change on the same frame."""
    starts = [t for t, _ in snapped_caps()] + [fr(CTA_START)]
    def anchor(x):
        best = min(starts, key=lambda c: abs(c - x))
        assert abs(best - x) < 0.45, x
        return best
    return [(anchor(a), anchor(b)) + tuple(rest) for a, b, *rest in BROLL_SPEC]


def build_text_track(variant):
    os.makedirs(f"text/{variant}", exist_ok=True)
    blank = f"text/{variant}/blank.png"
    Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)).save(blank)
    spans = caption_spans()
    segs = [(0.0, spans[0][0], hook_img(HOOKS[variant]))]
    for t, e, txt in spans:
        segs.append((t, e, caption_img(txt)))
    cta = box_layer(CTA)
    ys = CTA["top"] + BOX_H2 / 2
    t = fr(CTA_START)
    for k in BOUNCE:                              # scale the box about its centre, frame by frame
        m = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        sc = cta.resize((round(1080 * k), round(1920 * k)), Image.LANCZOS)
        m.alpha_composite(sc.crop((max(0, round(540 * k - 540)), max(0, round(ys * k - ys)), sc.width, sc.height)),
                          (max(0, round(540 - 540 * k)), max(0, round(ys - ys * k))))
        segs.append((t, t + 1 / FPS, m))
        t += 1 / FPS
    segs.append((t, DUR, cta))
    schedule = []   # (first frame, last frame + 1, png): exact frame numbers, so text and b-roll change on the same frame
    for i, (a, b, im) in enumerate(segs):
        p = f"text/{variant}/{i:03d}.png"
        im.save(p, compress_level=1)
        schedule.append((round(a * FPS), round(b * FPS), p))
    json.dump(schedule, open(f"text/{variant}/schedule.json", "w"))
    return schedule, blank


def render_base():
    shots = broll_shots()
    cmd = [B + "ffmpeg", "-y", "-v", "error", "-i", "raw/skit.mov", "-i", "click.mp3"]
    for (t0, t1, clip, inp, *_r) in shots:
        cmd += ["-ss", str(inp), "-t", f"{(t1 - t0 + 0.2) * SPEED.get(clip, 1):.3f}", "-i", f"pb/{clip}.mov"]
    parts = ["[0:v]scale=1080:1920,fps=30,format=yuv420p,setsar=1[v0]"]
    prev = "v0"
    for i, (t0, t1, clip, *_r) in enumerate(shots, 2):
        tone = "eq=saturation=1.5:contrast=1.08:gamma=0.95," if clip in HDR_CLIPS else ""
        parts.append(f"[{i}:v]{tone}scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p,setsar=1,setpts=(PTS-STARTPTS)/{SPEED.get(clip, 1)}+{t0:.4f}/TB,fps=30[b{i}]")
        parts.append(f"[{prev}][b{i}]overlay=0:0:enable='between(t,{t0 - 0.005:.4f},{t1 - 0.005:.4f})':eof_action=pass[v{i}]")
        prev = f"v{i}"
    d = int((fr(CTA_START) + CLICK_DELAY) * 1000)
    parts.append("[0:a]loudnorm=I=-14:TP=-2.0:LRA=11,aresample=48000,aformat=channel_layouts=stereo[vo]")
    parts.append(f"[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.5,adelay={d}|{d}[ck]")
    parts.append("[vo][ck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.8:level=disabled[a]")
    cmd += ["-filter_complex", ";".join(parts), "-map", f"[{prev}]", "-map", "[a]", "-t", str(DUR),
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "10", "-c:a", "aac", "-b:a", "256k", "base.mp4"]   # intermediate only: the text pass does the real encode
    subprocess.run(cmd, check=True)


def render_variant(variant):
    schedule, blank = build_text_track(variant)
    out = f"out/REDSKIT_Hook{variant}.mp4"
    os.makedirs("out", exist_ok=True)
    audio = (f"[2:a]aresample=48000,aformat=channel_layouts=stereo,acompressor=threshold=0.05:ratio=3:attack=30:release=500,lowpass=f=6500,volume={MUSIC_GAIN}[m];"
             "[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.8:level=disabled[a]"
             if variant in MUSIC else "[0:a]anull[a]")
    p = subprocess.Popen([B + "ffmpeg", "-y", "-v", "error", "-i", "base.mp4", "-f", "image2pipe", "-framerate", "30", "-c:v", "png", "-i", "-", "-i", "song.mp3",
                          "-filter_complex", "[1:v]format=rgba[t];[0:v][t]overlay=0:0:format=auto:shortest=1,format=yuv420p[v];" + audio,
                          "-map", "[v]", "-map", "[a]", "-t", str(DUR), "-c:v", "libx264", "-preset", "medium", "-b:v", "12M", "-maxrate", "14M", "-bufsize", "24M",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    cache = {}
    def data(path):
        if path not in cache:
            cache[path] = open(path, "rb").read()
        return cache[path]
    total = round(DUR * FPS) + 1
    pos = 0
    for a, b, path in schedule:
        for _ in range(pos, a):
            p.stdin.write(data(blank))
        for _ in range(a, b):
            p.stdin.write(data(path))
        pos = b
    for _ in range(pos, total):
        p.stdin.write(data(blank))
    p.stdin.close()
    if p.wait():
        raise SystemExit("render failed")
    return out


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "preview":
        os.makedirs("qa", exist_ok=True)
        for v, h in HOOKS.items():
            Image.alpha_composite(Image.open(f"refs/v1_cap.png").convert("RGBA"), hook_img(h)).convert("RGB").save(f"qa/hook{v}.png")
        Image.alpha_composite(Image.open("refs/v1_cap.png").convert("RGBA"), box_layer(CTA)).convert("RGB").save("qa/cta.png")
        Image.alpha_composite(Image.open("refs/v1_cap.png").convert("RGBA"), caption_img("ranking every Christmas gift")).convert("RGB").save("qa/cap.png")
    elif what == "base":
        render_base()
    else:
        print(render_variant(what))
