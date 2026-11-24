#!/usr/bin/env python3
"""Benefit Stack template, from the winning Stitchers ads' CapCut projects (Stitchers V1 to V3, Hunters V3).

Everything except the copy, the clips and the song is fixed here, so every ad in this style matches the winner:
timings, chip slots, text style, animations, sound effects and music level.

    benefit_stack.py <ad.json> <hook letter>     render one hook to out/<CODE>_Hook<X>.mp4
    benefit_stack.py <ad.json> preview           still frames of every text layer over a grey card, in qa/

ad.json holds the code, hooks, chips, CTA, clips and song (see camping example in style.md).
"""
import json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

B = "/Users/jackferguson/Video Editing Test/tools/venv/bin/"
FONT = "/Applications/CapCut.app/Contents/Resources/Font/SystemFont/en.ttf"   # CapCut's system font (Metropolis)
EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"
SFX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")       # copied from the CapCut cache
FPS, W, H = 30, 1080, 1920
DUR_F = 489                       # 16.3s

# Shots, in frames, from the CapCut projects: hook, chip block 1, chip block 2, product demo, close
SHOTS = [(0, 91), (91, 198), (198, 300), (300, 377), (377, 489)]
# Chip slots: (first frame, centre x, centre y, rotation in degrees, PIL sense). From CapCut transforms (x=540+540tx, y=960-960ty).
SLOTS = [[(91, 561, 744, 8.685), (110, 609, 967, 0.0), (126, 561, 1179, -7.825)],
         [(198, 540, 781, 0.0), (217, 646, 1004, -5.578), (233, 471, 1227, 8.633)]]
PRODUCT = (300, 540, 1323)        # "✅ The LuxeLight 2.0", Bounce In
CTA_F, CTA_CY, SIREN_CY = 377, 495, 324
HOOK_CY = 498
# Sound effects: (file, frame, gain) with CapCut's volumes
SOUNDS = [("correct", 91, 0.42568), ("correct", 110, 0.42568), ("correct", 126, 0.42568),
          ("ding", 198, 1.0), ("ding", 217, 1.0), ("ding", 233, 1.0),
          ("whoosh", 300, 0.35246), ("click", 377, 1.0)]
MUSIC_LUFS = -23.5                # the Stitchers songs sit at -23.0 and -24.5 LUFS in CapCut

# CapCut "Pop Up": offset along the chip's own vertical axis per frame (frame 0 hidden), and motion blur, measured from Stitchers V2
POP = [None, 1026, 247, -164, -150, -18, 64, 51, 1, -23, -11, 7, 13, 7, 1, 0]
POP_BLUR = {1: 110, 2: 46}
# CapCut "Bounce In": scale per frame (frame 0 hidden), measured from the reference ads
BOUNCE = [None, .225, .424, .600, .751, .879, .982, 1.053, 1.094, 1.096, 1.055, 1.029, 1.014, 1.006, 1.002, 1.0]

# Chip: CapCut size 11, black on a white rounded box, fitted to the reference frames
CHIP_PT, CHIP_TRACK, CHIP_H, CHIP_R = 67, 1.0, 115, 12
CHIP_EMOJI_X, CHIP_EMOJI_PX, CHIP_EMOJI_CY, CHIP_TEXT_X, CHIP_BASE, CHIP_PAD_R = 22, 66, 54.5, 109, 79, 25
# Hook and close boxes: CapCut size 12 bold, the house box (Video editing standards 11a)
BOX_PT, PAD_X, ABOVE, PITCH, BOX_H1, LINE_H, BOX_R, FIL = 75, 22, 81, 76, 119, 76, 14, 10
GREEN, BLACK, WHITE = (0, 178, 9, 255), (0, 0, 0, 255), (255, 255, 255, 255)
RED = (226, 20, 20, 255)   # for a phrase about red light, where green would contradict it
EMOJI_PX, EMOJI_CENTER, EMOJI_ADV = 72, 58, 76


def is_emoji(c):
    return ord(c) > 0x2600 or 0x2300 <= ord(c) <= 0x23FF


def emoji_img(c, px):
    f = ImageFont.truetype(EMOJI, 160)
    im = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((110, 110), c, font=f, embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox())
    k = min(px / im.width, px / im.height)
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def chip_img(text):
    """One chip, unrotated, on its own canvas: ✅ then the text."""
    S = 3
    f = ImageFont.truetype(FONT, CHIP_PT * S)
    adv = sum(f.getlength(ch) / S + CHIP_TRACK for ch in text)
    w = round(CHIP_TEXT_X + adv + CHIP_PAD_R)
    im = Image.new("RGBA", (w * S, CHIP_H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, CHIP_H * S - 1], CHIP_R * S, fill=WHITE)
    x = CHIP_TEXT_X * S
    for ch in text:
        d.text((x, CHIP_BASE * S), ch, font=f, fill=BLACK, anchor="ls")
        x += f.getlength(ch) + CHIP_TRACK * S
    im = im.resize((w, CHIP_H), Image.LANCZOS)
    e = emoji_img("✅", CHIP_EMOJI_PX)
    im.alpha_composite(e, (CHIP_EMOJI_X, round(CHIP_EMOJI_CY - e.height / 2)))
    return im


def box_img(lines, pt=BOX_PT):
    """The house white box for any number of lines, centred on x=540, on a tight canvas.
    lines: list of [(text, colour), ...] runs; emoji go at the end of a line."""
    S = 3
    k = pt / BOX_PT
    f = ImageFont.truetype(FONT, round(pt * S))
    meas = ImageDraw.Draw(Image.new("L", (4, 4)))
    rows = []
    for runs in lines:
        txt = "".join(t for t, _ in runs)
        em = [c for c in txt if is_emoji(c)]
        runs = [("".join(c for c in t if not is_emoji(c)), col) for t, col in runs]
        plain = "".join(t for t, _ in runs).rstrip()
        tw = meas.textlength(plain, font=f) / S
        rows.append((runs, em, tw, tw + ((20 + EMOJI_ADV * len(em)) * k if em else 0)))
    n = len(rows)
    hgt = (BOX_H1 + LINE_H * (n - 1)) * k
    spans = [r[3] for r in rows]
    cw, ch = W, round(hgt + 4)
    mask = Image.new("L", (cw * S, ch * S), 0)
    d = ImageDraw.Draw(mask)
    r, fil = BOX_R * k * S, FIL * k * S
    pad = PAD_X * k
    X = lambda wd: ((540 - wd / 2 - pad) * S, (540 + wd / 2 + pad) * S)
    # Lines of near-equal width share one bar. Where widths step, the seam sits 117px into the upper line when it is
    # the wider one and 72px when the lower one is wider (the house box, fitted to the reference ads).
    for i in range(n - 1):
        if abs(spans[i] - spans[i + 1]) < 28:
            spans[i] = spans[i + 1] = max(spans[i], spans[i + 1])
    seams = []
    for i in range(n - 1):
        if spans[i] == spans[i + 1]:
            seams.append(None)
        else:
            seams.append((PITCH * i + (117 if spans[i] > spans[i + 1] else 72)) * k * S)
    tops, bots = [0.0] * n, [hgt * S] * n
    for i, sm in enumerate(seams):
        if sm is None:
            tops[i + 1] = tops[i]
            continue
        if spans[i] > spans[i + 1]:
            bots[i], tops[i + 1] = sm, sm - 2 * r
        else:
            bots[i], tops[i + 1] = sm + 2 * r, sm
    for i in range(n - 1, 0, -1):          # equal-width neighbours: carry the lower edge up
        if seams[i - 1] is None:
            bots[i - 1] = bots[i]
    for i in range(n):
        x0, x1 = X(spans[i])
        d.rounded_rectangle([x0, tops[i], x1, bots[i]], r, fill=255)
    for i, sm in enumerate(seams):
        if sm is None:
            continue
        upper_wide = spans[i] > spans[i + 1]
        narrow = X(spans[i + 1]) if upper_wide else X(spans[i])
        sgn = 1 if upper_wide else -1
        for xc, side in ((narrow[0], -1), (narrow[1], 1)):
            x0, x1 = sorted((xc, xc + side * fil))
            y0, y1 = sorted((sm, sm + sgn * fil))
            d.rectangle([x0, y0, x1, y1], fill=255)
            cx, cy = xc + side * fil, sm + sgn * fil
            d.ellipse([cx - fil, cy - fil, cx + fil, cy + fil], fill=0)
    txt_l = Image.new("RGBA", (cw * S, ch * S), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt_l)
    emojis = []
    for i, (runs, em, tw, wd) in enumerate(rows):
        base = (ABOVE + i * PITCH) * k
        x = (540 - wd / 2) * S
        for t, col in runs:
            t = t if t is not runs[-1][0] else t.rstrip()
            td.text((x, base * S), t, font=f, fill=col, anchor="ls", stroke_width=2, stroke_fill=col)   # CapCut's bold
            x += meas.textlength(t, font=f)
        for j, c in enumerate(em):
            e = emoji_img(c, EMOJI_PX * k)
            cx = 540 - wd / 2 + tw + (EMOJI_CENTER + j * EMOJI_ADV) * k
            emojis.append((e, int(cx - e.width / 2), int(base - 29 * k - e.height / 2)))
    soft = ImageFilter.GaussianBlur(0.6)
    mask = mask.resize((cw, ch), Image.LANCZOS).filter(soft)
    im = Image.new("RGBA", (cw, ch), WHITE)
    im.putalpha(mask)
    tl = txt_l.resize((cw, ch), Image.LANCZOS).filter(soft)
    im.alpha_composite(tl)
    for e, x, y in emojis:
        im.alpha_composite(e, (x, y))
    return im


def parse_runs(line, green, red=()):
    """'WHY CAMPERS ARE' with green words ['OBSESSED'] -> coloured runs."""
    out, rest = [], line
    colour = {**{g: GREEN for g in green}, **{r: RED for r in red}}
    while rest:
        hits = [(rest.find(g), g) for g in colour if g and rest.find(g) >= 0]
        if not hits:
            out.append((rest, BLACK))
            break
        i, g = min(hits)
        if i:
            out.append((rest[:i], BLACK))
        out.append((g, colour[g]))
        rest = rest[i + len(g):]
    return out


def place(canvas, im, cx, cy):
    canvas.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))


def pop_frame(chip, n, cx, cy, rot):
    """Chip n frames into CapCut's Pop Up, or None while hidden."""
    if n <= 0:
        return None
    off = POP[n] if n < len(POP) else 0
    im = chip
    blur = POP_BLUR.get(n, 0)
    if blur:
        pad = Image.new("RGBA", (chip.width, chip.height + 2 * blur), (0, 0, 0, 0))
        pad.alpha_composite(chip, (0, blur))
        im = _vblur(pad, blur)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    a = math.radians(rot)
    return im, cx + off * math.sin(a), cy + off * math.cos(a)


def _vblur(im, length):
    """Vertical motion blur: average of the image shifted through `length` pixels."""
    steps = 12
    acc = None
    for s in range(steps):
        dy = round((s / (steps - 1) - 0.5) * length)
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sh.alpha_composite(im, (0, dy)) if dy >= 0 else sh.alpha_composite(im.crop((0, -dy, im.width, im.height)), (0, 0))
        acc = sh if acc is None else Image.blend(acc, sh, 1 / (s + 1))
    return acc


def bounce_frame(im, n):
    if n <= 0:
        return None
    k = BOUNCE[n] if n < len(BOUNCE) else 1.0
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


class Layers:
    def __init__(self, ad, hook):
        hk = ad["hooks"][hook]
        if hk.get("image"):   # a ready-made hook graphic (e.g. a TikTok comment reply) in place of the box, path relative to ad.json
            self.hook = Image.open(hk["image"]).convert("RGBA")
        else:
            self.hook = box_img([parse_runs(l, hk.get("green", []), hk.get("red", [])) for l in hk["lines"]], BOX_PT * hk.get("size", 12) / 12)
        self.chips = [[chip_img(t) for t in blk] for blk in ad["chips"]]
        self.product = chip_img(ad.get("product", "The LuxeLight 2.0"))
        self.cta = box_img([[(l, BLACK)] for l in ad["cta"]])
        self.siren = emoji_img("\U0001F6A8", 80)
        # Text never covers a face or the product: a hook or close box can move down for its clip ("cy"), as Stitchers V1's hook did
        self.hook_cy = hk.get("cy", HOOK_CY)
        self.cta_cy = ad.get("cta_cy", CTA_CY)

    def frame(self, f):
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if f < SHOTS[0][1]:
            place(c, self.hook, 540, self.hook_cy)
        for b, (s0, s1) in enumerate((SHOTS[1], SHOTS[2])):
            if s0 <= f < s1:
                for chip, (start, cx, cy, rot) in zip(self.chips[b], SLOTS[b]):
                    p = pop_frame(chip, f - start, cx, cy, rot)
                    if p:
                        place(c, *p)
        if SHOTS[3][0] <= f < SHOTS[3][1]:
            p = bounce_frame(self.product, f - PRODUCT[0])
            if p:
                place(c, p, PRODUCT[1], PRODUCT[2])
        if f >= CTA_F:
            place(c, self.siren, 540, self.cta_cy - (CTA_CY - SIREN_CY))
            p = bounce_frame(self.cta, f - CTA_F)
            if p:
                place(c, p, 540, self.cta_cy)
        return c


def base_video(ad, out, hook_clip=None):
    """The five shots, cut on CapCut's frames. Each clip: file, in-point, speed, zoom, optional HDR flag.
    Each hook can open on its own clip ("clip" in that hook), as the Stitchers versions did."""
    cmd = [B + "ffmpeg", "-y", "-v", "error"]
    parts, labels = [], []
    clips = [hook_clip or ad["clips"][0]] + ad["clips"][1:]
    for i, ((f0, f1), clip) in enumerate(zip(SHOTS, clips)):
        dur = (f1 - f0) / FPS
        spd = clip.get("speed", 1.0)
        cmd += ["-ss", str(clip["in"]), "-t", f"{dur * spd + 0.3:.3f}", "-i", clip["file"]]
        tone = "eq=saturation=1.5:contrast=1.08:gamma=0.95," if clip.get("hdr") else ""
        z = clip.get("zoom", 1.0)
        # "anchor": where the zoomed crop sits, 0 top to 1 bottom; 1 lifts a face above the chips
        ay = clip.get("anchor", 0.5)
        parts.append(f"[{i}:v]{tone}scale={round(W * z)}:{round(H * z)}:force_original_aspect_ratio=increase,"
                     f"crop={W}:{H}:(iw-{W})/2:(ih-{H})*{ay},setsar=1,setpts=(PTS-STARTPTS)/{spd},fps={FPS},trim=end_frame={f1 - f0},setpts=PTS-STARTPTS,format=yuv420p[s{i}]")
        labels.append(f"[s{i}]")
    parts.append("".join(labels) + f"concat=n={len(labels)}:v=1:a=0[v]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[v]", "-c:v", "libx264", "-preset", "fast", "-crf", "12", out]
    subprocess.run(cmd, check=True)


def music_gain(path, start):
    r = subprocess.run([B + "ffmpeg", "-hide_banner", "-nostats", "-ss", str(start), "-t", f"{DUR_F / FPS}", "-i", path,
                        "-af", "ebur128=framelog=quiet", "-f", "null", "-"], capture_output=True, text=True).stderr
    lufs = [float(l.split()[1]) for l in r.splitlines() if l.strip().startswith("I:")][-1]
    return 10 ** ((MUSIC_LUFS - lufs) / 20)


def render(ad, hook, workdir="."):
    code = ad["code"]
    os.makedirs(os.path.join(workdir, "out"), exist_ok=True)
    hook_clip = ad["hooks"][hook].get("clip")
    base = os.path.join(workdir, f"base_{hook}.mp4" if hook_clip else "base.mp4")
    if not os.path.exists(base) or os.path.getmtime(base) < os.path.getmtime(ad["_path"]):
        base_video(ad, base, hook_clip)
    song = ad["hooks"][hook]["music"]
    g = music_gain(song["file"], song.get("start", 0))
    out = os.path.join(workdir, "out", f"{code}_Hook{hook}.mp4")
    # the base can inherit an iPhone clip's rotation flag although its pixels are already upright: ignore it
    cmd = [B + "ffmpeg", "-y", "-v", "error", "-display_rotation", "0", "-i", base,
           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-ss", str(song.get("start", 0)), "-i", song["file"]]
    for name, *_ in SOUNDS:
        cmd += ["-i", os.path.join(SFX, name + ".mp3")]
    au = [f"[2:a]aresample=48000,aformat=channel_layouts=stereo,volume={g:.4f},atrim=0:{DUR_F / FPS}[m]"]
    for i, (name, f, gain) in enumerate(SOUNDS, 3):
        ms = round(f / FPS * 1000)
        au.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,volume={gain},adelay={ms}|{ms}[x{i}]")
    mix = "[m]" + "".join(f"[x{i}]" for i in range(3, 3 + len(SOUNDS)))
    au.append(f"{mix}amix=inputs={1 + len(SOUNDS)}:duration=first:normalize=0,alimiter=limit=0.76:level=disabled[a]")
    cmd += ["-filter_complex", "[1:v]format=rgba,settb=1/30,setpts=N[t];[0:v]settb=1/30,setpts=N[b];[b][t]overlay=0:0:format=auto:shortest=1,format=yuv420p[v];" + ";".join(au),
            "-map", "[v]", "-map", "[a]", "-frames:v", str(DUR_F), "-r", str(FPS), "-fps_mode", "cfr", "-c:v", "libx264", "-preset", "medium", "-b:v", "12M",
            "-maxrate", "14M", "-bufsize", "24M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    L = Layers(ad, hook)
    blank = bytes(W * H * 4)
    last = None
    for f in range(DUR_F):
        im = L.frame(f)
        p.stdin.write(im.tobytes() if im.getbbox() else blank)
    p.stdin.close()
    if p.wait():
        raise SystemExit("render failed")
    # sidecar for /video-qa: copy it next to the export as <stem>.plan.json so QA uses the benefit-stack profile
    json.dump({"style": "benefit-stack", "brand": ad.get("brand", "LuxeLight")}, open(out[:-4] + ".plan.json", "w"))
    return out


if __name__ == "__main__":
    ad = json.load(open(sys.argv[1]))
    ad["_path"] = sys.argv[1]
    wd = os.path.dirname(os.path.abspath(sys.argv[1]))
    if sys.argv[2] == "preview":
        os.makedirs(os.path.join(wd, "qa"), exist_ok=True)
        for hk in ad["hooks"]:
            L = Layers(ad, hk)
            for f in (45, 150, 260, 340, 450):
                bg = Image.new("RGBA", (W, H), (90, 90, 90, 255))
                bg.alpha_composite(L.frame(f))
                bg.convert("RGB").save(os.path.join(wd, "qa", f"hook{hk}_f{f}.png"))
    else:
        print(render(ad, sys.argv[2], wd))
