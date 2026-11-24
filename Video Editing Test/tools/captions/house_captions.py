"""House captions and on-screen text: the one engine for every video with speech and captions, any style, any brand.

Rulebook section 7 and 11a in code. Taken unchanged from the finished Red Light Skit (REDSKIT) template, where every
number was fitted to the reference ads and passed review. Don't write captions any other way: import from here.

  caption_img(text)       -> 1080x1920 RGBA: white text, black stroke, soft shadow, wraps to two lines (7.6, 11a)
  box_layer(spec)         -> hook / end box: CapCut system font with its bold, rounded joined bars (3.3, 11a)
  hook_img(spec)          -> hook box plus optional bracket line
  voice_onset(...)        -> where a word really starts in the audio, so captions change on that frame (7.8aa)
  BOUNCE, CLICK_DELAY     -> end-box Bounce In and the Click_Mouse_Click_02 timing (11a)
  check_spans(caps, cuts) -> hard checks: no blanks between captions (7.7), every cut on a caption change (7.8b)
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = "/Applications/CapCut.app/Contents/Resources/Font/SystemFont/en.ttf"   # CapCut's system font, as used in the reference ads
EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"
RED, WHITE = (255, 60, 60, 255), (255, 255, 255, 255)   # from the reference CapCut project

BOX_SIZE, CAP_SIZE, PAD_X = 75, 69, 22
ABOVE, PITCH = 81, 76            # baseline positions under the top of the box, fitted to the reference ads
BOX_H1, BOX_H2, STEP_UP, STEP_DOWN = 119, 195, 72, 117
EMOJI_PX, EMOJI_CENTER, EMOJI_ADV = 72, 58, 76
FPS = 30
# end-box bounce, measured frame by frame from the reference ad (box width / final width)
BOUNCE = [.225, .424, .600, .751, .879, .982, 1.053, 1.094, 1.096, 1.055, 1.029, 1.014, 1.006, 1.002]
CLICK_DELAY = 0.014   # CapCut's Click_Mouse_Click_02, timed as in the reference ad


def is_emoji(c):
    return ord(c) > 0x2600 or 0x2300 <= ord(c) <= 0x23FF


def split_runs(line):
    line = line.replace("\ufe0f", "").replace("\u200d", "")   # variation selectors aren't glyphs: counting them left blank space after the emoji (user, HEADSKIT v3)
    return [c for c in line if is_emoji(c)], "".join(c for c in line if not is_emoji(c)).rstrip()


def emoji_img(c):
    f = ImageFont.truetype(EMOJI, 160)
    im = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((110, 110), c, font=f, embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox())
    k = min(EMOJI_PX / im.width, EMOJI_PX / im.height)
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def box_layer(spec):
    """CapCut text with its background on: Metropolis with CapCut's bold, each line on a rounded bar, fused into one shape.
    Every number below is fitted to the reference ads."""
    S = 3
    f = ImageFont.truetype(FONT, BOX_SIZE * S)
    meas = ImageDraw.Draw(Image.new("L", (4, 4)))
    rows = []
    for ln in spec["lines"]:
        em, txt = split_runs(ln)
        tw = meas.textlength(txt, font=f) / S
        rows.append((txt, em, tw, tw + (20 + EMOJI_ADV * len(em) if em else 0)))
    top = spec["top"]
    spans = [r[3] for r in rows]
    if len(spans) == 2 and abs(spans[0] - spans[1]) < 70:   # a step under ~35px a side looks like a notch, not a stepped box (user, CRAZYGF v1)
        spans = [max(spans)] * 2
    r, fil = 14 * S, 10 * S
    mask = Image.new("L", (1080 * S, 1920 * S), 0)
    d = ImageDraw.Draw(mask)
    X = lambda w: ((540 - w / 2 - PAD_X) * S, (540 + w / 2 + PAD_X) * S)
    if len(spans) == 1 or spans[0] == spans[1]:
        h = BOX_H1 if len(spans) == 1 else BOX_H2
        d.rounded_rectangle([X(spans[0])[0], top * S, X(spans[0])[1], (top + h) * S], r, fill=255)
    else:
        a_wide = spans[0] > spans[1]
        seam = (top + (STEP_DOWN if a_wide else STEP_UP)) * S
        d.rounded_rectangle([X(spans[0])[0], top * S, X(spans[0])[1], seam + (0 if a_wide else 2 * r)], r, fill=255)
        d.rounded_rectangle([X(spans[1])[0], seam - (2 * r if a_wide else 0), X(spans[1])[1], (top + BOX_H2) * S], r, fill=255)
        thin = X(spans[1]) if a_wide else X(spans[0])
        sgn = 1 if a_wide else -1
        for xc, side in ((thin[0], -1), (thin[1], 1)):
            x0, x1 = sorted((xc, xc + side * fil))
            y0, y1 = sorted((seam, seam + sgn * fil))
            d.rectangle([x0, y0, x1, y1], fill=255)
            cx, cy = xc + side * fil, seam + sgn * fil
            d.ellipse([cx - fil, cy - fil, cx + fil, cy + fil], fill=0)
    txt_l = Image.new("L", (1080 * S, 1920 * S), 0)
    td = ImageDraw.Draw(txt_l)
    emojis = []
    for i, (txt, em, tw, w) in enumerate(rows):
        base = top + ABOVE + i * PITCH
        x = 540 - w / 2
        td.text((x * S, base * S), txt, font=f, fill=255, anchor="ls", stroke_width=2, stroke_fill=255)   # CapCut's bold
        for k, c in enumerate(em):
            e = emoji_img(c)
            cx = x + tw + EMOJI_CENTER + k * EMOJI_ADV
            emojis.append((e, int(cx - e.width / 2), int(base - 29 - e.height / 2)))
    soft = ImageFilter.GaussianBlur(0.6)   # the reference text isn't razor sharp
    mask = mask.resize((1080, 1920), Image.LANCZOS).filter(soft)
    txt_l = txt_l.resize((1080, 1920), Image.LANCZOS).filter(soft)
    im = Image.new("RGBA", (1080, 1920), spec["color"])      # colour everywhere, shape only in the alpha: no dark edge
    im.paste(Image.new("RGBA", (1080, 1920), spec["ink"]), (0, 0), txt_l)
    im.putalpha(mask)
    for e, x, y in emojis:
        im.alpha_composite(e, (x, y))
    return im


def wrap(text, f):
    if "\n" in text:                     # broken by hand into even lines (rulebook 7.8ac)
        return text.split("\n")
    meas = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if meas.textlength(t, font=f) > 885 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + [cur]


def outlined(lines, bases, size=CAP_SIZE, bold=False):
    """CapCut's caption effect from the reference project: white text, black stroke, soft black drop shadow to the lower right."""
    S = 3
    f = ImageFont.truetype(FONT, size * S)
    def draw(stroke, fill_w):
        lay = Image.new("L", (1080 * S, 1920 * S), 0)
        d = ImageDraw.Draw(lay)
        for ln, b in zip(lines, bases):
            w = d.textlength(ln, font=f)
            d.text((540 * S - w / 2, b * S), ln, font=f, fill=255, anchor="ls", stroke_width=stroke, stroke_fill=255)
        return lay.resize((1080, 1920), Image.LANCZOS)
    edge = draw(11, 0).filter(ImageFilter.GaussianBlur(0.7))
    shadow = Image.new("L", (1080, 1920), 0)
    shadow.paste(edge, (4, 4))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * 0.8))
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    black = Image.new("RGBA", (1080, 1920), (0, 0, 0, 255))
    im.paste(black, (0, 0), shadow)
    im.paste(black, (0, 0), edge)
    fill = draw(1 if bold else 0, 0).filter(ImageFilter.GaussianBlur(0.5))
    im.paste(Image.new("RGBA", (1080, 1920), (255, 255, 255, 255)), (0, 0), fill)
    return im


def caption_img(text):
    f = ImageFont.truetype(FONT, CAP_SIZE)
    ls = wrap(text, f)
    return outlined(ls, [1465] if len(ls) == 1 else [1430, 1500])


def hook_img(h):
    im = box_layer(h)
    if h["paren"]:
        im.alpha_composite(outlined([h["paren"]], [1243], bold=True))
    return im


def fr(t):
    return round(t * FPS) / FPS


def voice_onset(cap_t, t, e, voiced, prev, word_ends=()):
    """The audio's real start of the word. Whisper can be a few frames late or early, so it only says roughly where to look.
    Never searches back past the end of the word before it (word_ends, from tx/skit.json)."""
    import numpy as np
    i = int(np.searchsorted(t, cap_t))
    before = [w for w in word_ends if w <= cap_t + 0.02]
    lo = int(np.searchsorted(t, max(cap_t - 0.30, prev + 0.1, before[-1] if before else 0)))
    if voiced[i]:
        j = i
        while j > lo and voiced[j]:
            j -= 1
        if not voiced[j]:           # silence just before: the word starts where it ends
            return float(t[j + 1])
        a, b = int(np.searchsorted(t, cap_t - 0.12)), int(np.searchsorted(t, cap_t + 0.06))
        return float(t[a + int(np.argmin(e[a:b + 1]))])   # no silence in continuous speech: take the dip between words
    j = i
    while j < len(t) - 1 and not voiced[j] and t[j] < cap_t + 0.4:
        j += 1
    return float(t[j]) if voiced[j] else cap_t


def check_spans(caps, cut_frames, first=None, last=None):
    """caps: [(first frame, end frame, text)] in order. Fails loudly instead of letting a broken edit reach the reviewer."""
    errs = []
    for (a0, a1, at), (b0, b1, bt) in zip(caps, caps[1:]):
        if a1 != b0:
            errs.append("blank or overlap between %r (ends %d) and %r (starts %d)" % (at, a1, bt, b0))
    starts = {c[0] for c in caps}
    if last is not None:
        starts.add(last)
    for f in cut_frames:
        if (first is None or f >= first) and (last is None or f <= last) and f not in starts:
            errs.append("shot change at frame %d (%.2fs) is not on a caption change" % (f, f / FPS))
    f = ImageFont.truetype(FONT, CAP_SIZE)
    for a0, a1, t in caps:
        if len(wrap(t, f)) > 2:
            errs.append("caption over two lines: %r" % t)
        if a1 - a0 < 6:
            errs.append("caption under 0.2s: %r" % t)
    if errs:
        raise SystemExit("caption check failed:\n  " + "\n  ".join(errs))
    return True


# ---------------------------------------------------------------- competitor looks (Lumi Light copies)
# competitor-replication/RUNBOOK.md rule 4 (user, 2026-11-08): a Lumi copy uses THEIR text look, measured off their
# ad (LUMI1108 source, 720x1280, scaled x1.5). Same timing engine; only the drawing differs.
LUMI = dict(size=56, bold=2, top1=1344, pitch=64, brand=(241, 126, 10, 255), brand_words=("LuxeLight",),
            hook_size=56, hook_top=1149, hook_pad_x=24, hook_pad_y=15, hook_pitch=61, hook_radius=12)


def lumi_look(tl):
    """LUMI with the per-ad overrides an edit sets in "lumi_look" (each Lumi ad has its own sizes and positions;
    measured off that ad's frames). Extra keys: hook_upper (False = their sentence case), offer (a one-line white box
    shown with every hook caption, e.g. their "Buy 5, get 5 cases free!"), offer_size, offer_top, offer_pad_x."""
    d = dict(LUMI)
    d.update({k: tuple(v) if isinstance(v, list) else v for k, v in (tl.get("lumi_look") or {}).items()})   # colours come back from JSON as lists
    return d


def _lumi_line_runs(line, brand_words):
    runs, rest = [], line
    while rest:
        hits = [(rest.find(b), b) for b in brand_words if rest.find(b) >= 0]
        if not hits:
            runs.append((rest, False)); break
        i, b = min(hits)
        if i: runs.append((rest[:i], False))
        runs.append((b, True)); rest = rest[i + len(b):]
    return runs


def caption_img_lumi(text, look=LUMI):
    """Lumi Light's captions: white bold lowercase, soft dark shadow, brand name orange, centred at y ~1340-1400."""
    S = 2
    f = ImageFont.truetype(FONT, look["size"] * S)
    lines = text.split("\n")
    meas = ImageDraw.Draw(Image.new("L", (4, 4)))
    fill = Image.new("RGBA", (1080 * S, 1920 * S), (0, 0, 0, 0))
    sh = Image.new("L", (1080 * S, 1920 * S), 0)
    df, ds = ImageDraw.Draw(fill), ImageDraw.Draw(sh)
    top = look["top1"] if len(lines) == 1 else look["top1"] - look["pitch"] // 2
    for k, ln in enumerate(lines):
        runs = _lumi_line_runs(ln, look["brand_words"])
        tw = sum(meas.textlength(t, font=f) for t, _ in runs)
        x = 540 * S - tw / 2
        y = (top + k * look["pitch"]) * S
        for t, br in runs:
            col = look["brand"] if br else WHITE
            df.text((x, y), t, font=f, fill=col, stroke_width=look["bold"] * S, stroke_fill=col)
            ds.text((x, y + 3 * S), t, font=f, fill=255, stroke_width=(look["bold"] + 2) * S, stroke_fill=255)
            x += meas.textlength(t, font=f)
    sh = sh.filter(ImageFilter.GaussianBlur(5 * S)).point(lambda v: int(v * 0.8))
    out = Image.new("RGBA", (1080 * S, 1920 * S), (0, 0, 0, 0))
    out.putalpha(sh)
    out.alpha_composite(fill)
    return out.resize((1080, 1920), Image.LANCZOS)


def hook_caption_img_lumi(text, look=LUMI):
    """Lumi Light's hook: the hook captions in capitals, black bold on one tight white box (max two lines)."""
    S = 2
    f = ImageFont.truetype(FONT, look["hook_size"] * S)
    lines = (text.upper() if look.get("hook_upper", True) else text).split("\n")
    assert len(lines) <= 2, "hook text is never more than two lines (rulebook 3.3)"
    meas = ImageDraw.Draw(Image.new("L", (4, 4)))
    asc, desc = f.getmetrics()
    cap = f.getbbox("H")[3] - f.getbbox("H")[1]
    w = max(meas.textlength(l, font=f) for l in lines) + 2 * look["hook_pad_x"] * S
    h = cap + (len(lines) - 1) * look["hook_pitch"] * S + 2 * (look["hook_pad_y"] + 6) * S
    im = Image.new("RGBA", (1080 * S, 1920 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = 540 * S - w / 2, look["hook_top"] * S
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], look["hook_radius"] * S, fill=WHITE)
    for k, ln in enumerate(lines):
        tw = meas.textlength(ln, font=f)
        ty = y0 + (look["hook_pad_y"] + 6) * S + k * look["hook_pitch"] * S - f.getbbox("H")[1]
        d.text((540 * S - tw / 2, ty), ln, font=f, fill=(0, 0, 0, 255), stroke_width=look["bold"] * S, stroke_fill=(0, 0, 0, 255))
    if look.get("offer"):
        # their one-line offer box under the hook (white box, black text, a red "!" for their red exclamation emoji)
        fo = ImageFont.truetype(FONT, look["offer_size"] * S)
        txt = look["offer"].rstrip("!")
        bang = look["offer"].endswith("!")
        tw = meas.textlength(txt, font=fo) + (meas.textlength("!", font=fo) + 4 * S if bang else 0)
        capo = fo.getbbox("H")[3] - fo.getbbox("H")[1]
        px, py = look.get("offer_pad_x", 22) * S, 22 * S
        x0, y0 = 540 * S - tw / 2 - px, look["offer_top"] * S
        d.rounded_rectangle([x0, y0, x0 + tw + 2 * px, y0 + capo + 2 * py], look["hook_radius"] * S, fill=WHITE)
        ty = y0 + py - fo.getbbox("H")[1]
        d.text((x0 + px, ty), txt, font=fo, fill=(0, 0, 0, 255), stroke_width=look["bold"] * S, stroke_fill=(0, 0, 0, 255))
        if bang:
            bx = x0 + px + meas.textlength(txt, font=fo) + 4 * S
            d.text((bx, ty), "!", font=fo, fill=(226, 32, 32, 255), stroke_width=(look["bold"] + 1) * S, stroke_fill=(226, 32, 32, 255))
    return im.resize((1080, 1920), Image.LANCZOS)


# ---------------------------------------------------------------- native TikTok text (hook look the user asked for, CRAZYGF 2026-11-10)
# TikTok's own "Classic" text: Proxima Nova Semibold, white with a thin black outline, no box, centred, wrapping at
# about 60% of the width. Measured off the user's reference screenshot ("my girlfriend crashing out bc of this ban.").
NATIVE_FONT = os.path.expanduser("~/Movies/CapCut/User Data/Cache/effect/3914283/a9ba51ec06f2a6bc1566b464fa961bf3/ProximaNova-Semibold.ttf")
NATIVE = dict(size=40, stroke=2, pitch=46, wrap=640, emoji=40)


def native_text_img(text, top, look=NATIVE):
    """1080x1920 RGBA: the text as TikTok's native text tool draws it. `top` is the first line's top edge.
    A "\n" in the text forces a line break (to keep "1 to 10" together); otherwise it wraps like TikTok."""
    S = 3
    f = ImageFont.truetype(NATIVE_FONT, look["size"] * S)
    meas = ImageDraw.Draw(Image.new("L", (4, 4)))
    em_w = (look["emoji"] + 6) * S
    width = lambda s: meas.textlength("".join(c for c in s if not is_emoji(c)), font=f) + em_w * sum(map(is_emoji, s))
    lines = []
    for part in text.split("\n"):
        cur = ""
        for w in part.split():
            t = (cur + " " + w).strip()
            if width(t) > look["wrap"] * S and cur:
                lines.append(cur)
                cur = w
            else:
                cur = t
        lines.append(cur)
    im = Image.new("RGBA", (1080 * S, 1920 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    asc = f.getmetrics()[0]
    for i, ln in enumerate(lines):
        y = (top + i * look["pitch"]) * S
        x = 540 * S - width(ln) / 2
        for run in re.split(r"(\s+)", ln):
            if not run:
                continue
            if all(is_emoji(c) for c in run.strip()) and run.strip():
                for c in run.strip():
                    e = emoji_img(c)
                    k = look["emoji"] * S / max(e.size)                # keep the emoji's shape (the phone is tall)
                    e = e.resize((max(1, round(e.width * k)), max(1, round(e.height * k))), Image.LANCZOS)
                    cx, cy = x + em_w / 2, y + asc - look["emoji"] * S * 0.4
                    im.alpha_composite(e, (int(cx - e.width / 2), int(cy - e.height / 2)))
                    x += em_w
            else:
                d.text((x, y), run, font=f, fill=(255, 255, 255, 255), stroke_width=look["stroke"] * S, stroke_fill=(0, 0, 0, 255))
                x += meas.textlength(run, font=f)
    return im.resize((1080, 1920), Image.LANCZOS)
