"""Render one or all versions of an AI-voiceover ad from config.json. See references/config.md.

Usage: python -I render.py <project> [version-name]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I leaves the script folder off the path
import hashlib, json, os, re, subprocess, sys

from PIL import Image, ImageDraw, ImageFont

from common import FF, config, norm, probe_duration, project, run

project()
CFG = config()
W, H, FPS = CFG.get("width", 1080), CFG.get("height", 1920), CFG.get("fps", 30)
BOX_H = W * 5 // 4                 # the 4:5 safe box: what shows in the feed before anyone taps in
SAFE_TOP, SAFE_BOT = (H - BOX_H) // 2, (H + BOX_H) // 2
ENCODERS = subprocess.run([FF, "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
VIDEO = ["-c:v", "h264_videotoolbox", "-profile:v", "high"] if "h264_videotoolbox" in ENCODERS else ["-c:v", "libx264", "-preset", "veryfast", "-threads", "4"]
TAGS = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]

# ---------- word timings, with the transcription fixes from config ----------
words = json.load(open("work/words.json"))
for wrong, right in CFG.get("fixes", {}).items():
    p = wrong.lower().split(); out, i = [], 0
    while i < len(words):
        if [x["w"].lower() for x in words[i:i + len(p)]] == p:
            if right: out.append(dict(w=right, s=words[i]["s"], e=words[i + len(p) - 1]["e"]))
            i += len(p)
        else:
            out.append(words[i]); i += 1
    words = out
END = round(min(words[-1]["e"] + 0.8, probe_duration("work/vo_tight.wav")), 2)


def find(phrase, after=0.0):
    """Index of the first word of the first time `phrase` is spoken after a given time."""
    p = [norm(x) for x in phrase.split()]
    for i in range(len(words) - len(p) + 1):
        if words[i]["s"] >= after - 0.05 and [norm(w["w"]) for w in words[i:i + len(p)]] == p:
            return i
    raise SystemExit(f'Cue not found in the voiceover: "{phrase}". Check work/words.json.')


def at(phrase, after=0.0):
    """Cut point for a cue: just before its first word."""
    return max(round(words[find(phrase, after)]["s"] - 0.03, 2), 0.0)


def layout(shots, start, end):
    """[[cue, clip, in]...] -> [(a, b, clip, in)]; each shot runs until the next cue."""
    times, t = [], start
    for k, (cue, _, _) in enumerate(shots):
        t = start if k == 0 else at(cue, t); times.append(t)
    return [(a, b, s[1], s[2]) for a, b, s in zip(times, times[1:] + [end], shots)]


# ---------- proxies ----------
def source(clip):
    for ext in (".mov", ".mp4", ".MOV", ".MP4"):
        if os.path.exists(f"src/{clip}{ext}"): return f"src/{clip}{ext}"
    raise SystemExit(f"Clip not found in src/: {clip}")


BT709 = "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709"  # or the first clip's tags label the whole video
def sdr(clip):
    """Tone-map an HDR clip to SDR. Left alone, one HDR clip gives a colour cast and can tag the whole file as HDR."""
    info = subprocess.run([FF, "-nostdin", "-i", source(clip)], capture_output=True, text=True).stderr
    if not re.search("arib-std-b67|smpte2084", info): return ""
    return "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,"


def proxy(clip, ss, frames):
    """Cached shot cut once at output size. Every proxy shares one pixel format and range: a format change
    mid-concat re-initialises the final filter graph, which blanks captions for the length of the odd clip."""
    o = f"proxy/{clip}_{hashlib.md5(f'{W}x{H}|{ss:.3f}|{frames}|sdr709'.encode()).hexdigest()[:10]}.mp4"
    if not os.path.exists(o):
        run(["-ss", f"{ss:.3f}", "-i", source(clip),
             "-vf", f"{sdr(clip)}scale={W}:{H}:force_original_aspect_ratio=increase:out_range=tv,crop={W}:{H},setsar=1,fps={FPS},format=yuv420p,{BT709}",
             "-frames:v", str(frames), "-an", *VIDEO, "-b:v", "16M", *TAGS, "-video_track_timescale", "15360", o])
    return o


# ---------- text ----------
AV = "/System/Library/Fonts/Avenir Next.ttc"
def font(style, size):
    for i in range(12):
        f = ImageFont.truetype(AV, size, index=i)
        if f.getname()[1] == style: return f
    raise ValueError(style)
EMOJI = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", 160)
EMO = re.compile("[\U0001F300-\U0001FAFF☀-➿‼️]+")
CAP_FONT, HOOK_SIZE = font("Demi Bold", 60), CFG.get("hook_font_size", 62)


def emoji_img(e, h):
    im = Image.new("RGBA", (220 * len(e), 220), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), e, font=EMOJI, embedded_color=True)
    im = im.crop(im.getbbox()); return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)


def pill(text, fg, bg, size=HOOK_SIZE):
    """CapCut's System font with Bold on: SF at regular weight, thickened with a stroke. Matched against a CapCut frame.
    Drawn at 4x, because the stroke is under a pixel wide at full size."""
    Z = 4
    hf = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", size * Z)
    hf.set_variation_by_axes([100, 17, 400, 400])  # width, optical size, grade, weight
    stroke = round(size * Z * 0.013)
    m = EMO.search(text); emo = m.group(0) if m else ""; txt = EMO.sub("", text).strip()
    l, _, r, _ = hf.getbbox(txt); tw = r - l
    _, ct, _, cb = hf.getbbox("H")
    padx, gap = int(size * Z * 0.31), int(size * Z * 0.34)
    ei = emoji_img(emo, size * Z) if emo else None
    w = tw + (ei.width + gap if ei else 0) + 2 * padx
    h = int(size * Z * (1.7 if ei else 1.55))  # CapCut's box grows to fit an emoji
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), int(size * Z * 0.19), fill=bg)
    d.text((padx - l, (h - ct - cb) // 2), txt, font=hf, fill=fg, stroke_width=stroke, stroke_fill=fg)
    if ei: im.alpha_composite(ei, (padx + tw + gap, (h - ei.height) // 2))
    return im.resize((w // Z, h // Z), Image.LANCZOS)


def hook_png(name, lines, y=None, size=None):
    """Two stacked boxes, just inside the top of the safe box. On screen for the whole hook."""
    size = size or HOOK_SIZE
    f = Image.new("RGBA", (W, H), (0, 0, 0, 0)); y = y or CFG.get("hook_y", SAFE_TOP + 40)
    styles = [tuple(tuple(c) if isinstance(c, list) else c for c in s) for s in CFG.get("hook_styles", [("white", (238, 45, 66)), ("black", "white")])]
    for k, line in enumerate(lines):
        p = pill(line, *styles[min(k, 1)], size)
        if p.width > W - 40: raise SystemExit(f'Hook line too wide for the frame: "{line}"')
        f.alpha_composite(p, ((W - p.width) // 2, y)); y += p.height + int(size * 0.22)
    path = f"work/ovl/hook_{name}.png"; f.save(path); return path


def caption_png(text):
    """White text with a black outline, just inside the bottom of the safe box, two lines at most."""
    path = f"work/ovl/cap_{hashlib.md5(text.encode()).hexdigest()[:10]}.png"
    if os.path.exists(path): return path
    lines = [text]
    if CAP_FONT.getlength(text) > W * CFG.get("caption_wrap", 0.8):
        ws = text.split()
        k = min(range(1, len(ws)), key=lambda k: abs(CAP_FONT.getlength(" ".join(ws[:k])) - CAP_FONT.getlength(" ".join(ws[k:]))))
        lines = [" ".join(ws[:k]), " ".join(ws[k:])]
    f = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(f); lh = 72
    y = CFG.get("caption_bottom", SAFE_BOT - 60) - lh * len(lines)
    for j, ln in enumerate(lines):
        d.text((W // 2, y + j * lh), ln, font=CAP_FONT, fill="white", anchor="ma", stroke_width=6, stroke_fill=(0, 0, 0, 240))
    f.save(path); return path


# ---------- captions: spoken sections that never cross a sentence ----------
BREAK = {"and", "to", "with", "from", "like", "if", "when", "or", "but", "then", "before", "into", "about", "because",
         "at", "on", "is", "that", "once", "going", "right", "how", "all"}
MAX_WORDS = CFG.get("caption_max_words", 4)


def chunk_words():
    if CFG.get("captions"):  # exact caption lines from the config, used to copy a reference ad's captions
        chunks, i = [], 0
        for line in CFG["captions"]:
            n = len(line.split()); chunks.append(words[i:i + n]); i += n
            if [norm(w["w"]) for w in chunks[-1]] != [norm(x) for x in line.split()]:
                raise SystemExit(f'Caption "{line}" does not match the voiceover: {" ".join(w["w"] for w in chunks[-1])}')
        if i != len(words): raise SystemExit(f"Captions stop before the voiceover ends, at: {words[i]['w']}")
        return chunks
    # With pauses removed the transcriber can run sentences together, so its punctuation alone can't be trusted.
    # Every planned cut also ends a caption: nothing spans a cut, or a hook into the body.
    all_shots = CFG["body"]["shots"] + [s for v in CFG["versions"] for s in v["shots"]]
    cuts = {find(s[0]) for s in all_shots} | {find(v["end"]) for v in CFG["versions"] if v.get("end")}
    sentences, cur = [], []
    for i, w in enumerate(words):
        if i in cuts and cur: sentences.append(cur); cur = []
        cur.append(w)
        if w["w"][-1] in ".?!": sentences.append(cur); cur = []
    if cur: sentences.append(cur)
    chunks = []
    for s in sentences:
        parts, cur = [], []
        for w in s:
            cur.append(w)
            if w["w"][-1] in ",.?!": parts.append(cur); cur = []
        if cur: parts.append(cur)
        out = []
        for p in parts:
            cur = []
            for k, w in enumerate(p):
                joiner = len(cur) >= 2 and len(p) - k >= 3 and re.sub(r"\W", "", w["w"].lower()) in BREAK
                if cur and (len(cur) >= MAX_WORDS or joiner): out.append(cur); cur = []
                cur.append(w)
            if len(cur) == 1 and len(p) > 1 and len(out[-1]) <= MAX_WORDS: out[-1] = out[-1] + cur
            else: out.append(cur)
        merged = []
        for p in out:  # no lonely one-word captions
            if merged and len(merged[-1]) == 1 and len(p) < MAX_WORDS + 1: merged[-1] = merged[-1] + p
            else: merged.append(list(p))
        if len(merged) > 1 and len(merged[-1]) == 1:
            tail = merged.pop(); merged[-1] = merged[-1] + tail
        chunks += merged
    return chunks


def clean(ws):
    s = re.sub(r"[.,!?]+(\s|$)", r"\1", " ".join(x["w"] for x in ws)).strip()
    keep = {p.lower(): p for p in CFG.get("proper_nouns", [])}
    out = []
    for t in s.split():
        low = t.lower()
        if low in keep: out.append(keep[low])
        elif t in ("I", "I'm", "I've", "I'll", "I'd"): out.append(t)
        else: out.append(low)
    return " ".join(out)


CHUNKS = chunk_words()


# ---------- one version ----------
def render(v):
    name = v["name"]
    body_cfg = CFG["body"]; body_at = at(body_cfg["shots"][0][0])
    hook_at = at(v["shots"][0][0]) if v["shots"][0][0] else 0.0
    if hook_at < 0.2: hook_at = 0.0
    hook_end = at(v["end"], hook_at) if v.get("end") else body_at
    segments = [(hook_at, hook_end), (body_at, END)]
    master = layout(v["shots"], hook_at, hook_end) + layout(body_cfg["shots"], body_at, END)
    dur = sum(b - a for a, b in segments); hook_len = hook_end - hook_at

    def remap(t):
        off = 0.0
        for a, b in segments:
            if a <= t < b: return off + t - a
            off += b - a
        return None

    # picture: exact frame counts, so cuts stay locked to the voiceover
    files, f0, t = [], 0, 0.0
    for a, b, clip, ss in master:
        t += b - a; f1 = round(t * FPS)
        files.append(proxy(clip, ss, f1 - f0)); f0 = f1
    with open(f"work/concat_{name}.txt", "w") as fh:
        fh.writelines(f"file '{os.path.abspath(f)}'\n" for f in files)

    # text track: the hook hard-cuts on the first body frame, and the first caption takes over on that same frame
    hook_card = hook_png(name, v["hook"], v.get("hook_y"), v.get("hook_font_size")); in_hook = CFG.get("captions_in_hook", False)
    events = [] if in_hook else [(0.0, hook_card)]; log = []
    for c in CHUNKS:
        t = remap(c[0]["s"])
        if t is None or (t < hook_len - 0.01 and not in_hook): continue
        text = clean(c)
        log.append((round(t, 3), text))
        png = caption_png(text)
        if t < hook_len - 0.01:  # a caption during the hook sits on the same frame as the hook card
            both = Image.open(hook_card).convert("RGBA"); both.alpha_composite(Image.open(png).convert("RGBA"))
            png = f"work/ovl/hook_{name}_{len(events)}.png"; both.save(png)
        events.append((t, png))
    events.sort(key=lambda e: e[0])
    first_body = next(k for k, e in enumerate(events) if e[0] >= hook_len - 0.01 and e[1] != hook_card)
    # A text change lands on the next whole frame, so it's set just before the frame of the picture cut.
    # Set exactly at hook_len, the hook text can stay up for one frame of the new shot.
    events[first_body] = (round(hook_len * FPS) / FPS - 0.005, events[first_body][1])
    events[0] = (0.0, events[0][1])
    with open(f"work/ovl_{name}.txt", "w") as fh:
        for k, (t, p) in enumerate(events):
            nxt = events[k + 1][0] if k + 1 < len(events) else dur
            # framerate: stills default to a 25fps clock, which pushes text changes up to a frame off the 30fps picture
            fh.write(f"file '{os.path.abspath(p)}'\noption framerate {FPS}\nduration {nxt - t:.3f}\n")
        fh.write(f"file '{os.path.abspath(events[-1][1])}'\noption framerate {FPS}\n")

    # audio is built in its own passes: filtering it inside the video render silently lost seconds of speech
    cuts = "[0:a]asplit=2[i0][i1];" + "".join(f"[i{k}]atrim={a}:{b},asetpts=PTS-STARTPTS[s{k}];" for k, (a, b) in enumerate(segments))
    run(["-i", "work/vo_tight.wav", "-filter_complex", cuts + "[s0][s1]concat=n=2:v=0:a=1[a]", "-map", "[a]", f"work/vo_{name}.wav"])
    vol = CFG.get("music_volume", 0.09)
    mix = (f"[0:a]aresample=48000,volume=1.6,apad=whole_dur={dur}[vo];"
           f"[1:a]aresample=48000,atrim=0:{dur},volume={vol},afade=t=out:st={dur - 1.5}:d=1.5[mu];"
           "[vo][mu]amix=inputs=2:duration=first:normalize=0")
    inputs = ["-i", f"work/vo_{name}.wav", "-i", CFG["music"]] if CFG.get("music") else ["-i", f"work/vo_{name}.wav", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    measured = subprocess.run([FF, "-nostdin", *inputs, "-filter_complex", mix + ",loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json[a]",
                               "-map", "[a]", "-t", f"{dur:.3f}", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(measured[measured.rindex("{"):measured.rindex("}") + 1])
    second = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    run([*inputs, "-filter_complex", f"{mix},{second},aresample=48000,aformat=channel_layouts=stereo[a]", "-map", "[a]",
         "-t", f"{dur:.3f}", f"work/mix_{name}.wav"])

    final = f"out/{CFG['name']}_{name}.mp4"
    run(["-reinit_filter", "0", "-display_rotation", "0", "-f", "concat", "-safe", "0", "-i", f"work/concat_{name}.txt",
         "-f", "concat", "-safe", "0", "-i", f"work/ovl_{name}.txt", "-i", f"work/mix_{name}.wav",
         "-filter_complex", f"[1:v]fps={FPS},format=rgba[ov];[0:v][ov]overlay=0:0:eof_action=pass,format=yuv420p[v]",
         "-map", "[v]", "-map", "2:a", "-t", f"{dur:.3f}", *VIDEO, "-b:v", "12M", *TAGS,
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final])
    json.dump(dict(final=final, duration=dur, hook_end=hook_len, captions=log,
                   shots=[(round(a, 2), round(b, 2), c, s) for a, b, c, s in master]), open(f"work/log_{name}.json", "w"), indent=0)
    print(f"{final}  {dur:.2f}s  {len(master)} shots  {len(log)} captions")


only = sys.argv[2] if len(sys.argv) > 2 else None
for version in CFG["versions"]:
    if only in (None, version["name"]): render(version)
