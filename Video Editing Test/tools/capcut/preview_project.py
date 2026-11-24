"""Review-app preview of a CapCut project as it stands: its own clips, voice pieces, music, sound effects and clip
sound, with the captions and text boxes drawn in the house look.

    preview_project.py "<project name>" <out.mp4>

For hook versions made by swap_hook.py from an ad the user finished: the body is theirs (clips with their own sound,
a re-recorded close from a second voice file, music split for a volume change: GIFTGIVER2, 2026-11-16), which the
story_ad.py preview can't play because it knows one voice file and no clip sound. Not drawn: blur, stickers, effects,
filters, animations, fonts and colours of the user's own text (every box is the white house box at its own height).
"""
import json, os, re, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut_draft as C
import story_ad as S
from PIL import Image

HT, FF, W, H, FPS, US = S.HT, S.FF, S.W, S.H, S.FPS, 1e6


def has_audio(path):
    return "Audio:" in subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr


def plain_text(txt, font, px, rotation, alpha, align=1, color=(255, 255, 255), shadow=True):
    """White text with a soft shadow, as CapCut draws an unboxed text: returns an RGBA tile."""
    from PIL import ImageDraw, ImageFont, ImageFilter
    f = ImageFont.truetype(font, max(8, int(round(px))))
    lines = txt.split("\n")
    ws = [f.getlength(l) for l in lines]
    lh = int(px * 1.12)
    pad = int(px * 0.4) + 12
    tw, th = int(max(ws)) + 2 * pad, lh * len(lines) + 2 * pad
    def draw(fill):
        im = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        for i, l in enumerate(lines):
            x = pad + (0 if align == 0 else (max(ws) - ws[i]) / 2)
            dr.text((x, pad + i * lh), l, font=f, fill=fill)
        return im
    sh = draw((0, 0, 0, 150)).filter(ImageFilter.GaussianBlur(max(3, px * 0.06)))
    tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    if shadow:
        tile.alpha_composite(sh, (3, 4))
    tile.alpha_composite(draw(tuple(color) + (255,)))
    if rotation:
        tile = tile.rotate(-rotation, expand=True, resample=Image.BICUBIC)   # CapCut turns clockwise
    if alpha < 1:
        tile.putalpha(tile.getchannel("A").point(lambda v: int(v * alpha)))
    return tile


def kf_value(seg, prop, tsec, base):
    for k in seg.get("common_keyframes") or []:
        if k["property_type"] == prop:
            pts = [(q["time_offset"] / US, q["values"][0]) for q in k["keyframe_list"]]
            if tsec <= pts[0][0]:
                return pts[0][1]
            for (ta, va), (tb, vb) in zip(pts, pts[1:]):
                if tsec <= tb:
                    return va + (vb - va) * (tsec - ta) / max(tb - ta, 1e-6)
            return pts[-1][1]
    return base


def composite(d, mats, real, total_f, out):
    import cv2, numpy as np
    pipe = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
                             "-i", "-", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "14", "-pix_fmt", "yuv420p", out],
                            stdin=subprocess.PIPE)
    caps, stills = {}, {}

    def frame_of(seg, path, ts):
        if path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            if path not in stills:
                stills[path] = cv2.cvtColor(np.array(Image.open(path).convert("RGBA")), cv2.COLOR_RGBA2BGRA)
            return stills[path]
        c = caps.get(seg["id"])
        if c is None:
            cap = cv2.VideoCapture(path)
            c = caps[seg["id"]] = dict(cap=cap, fps=cap.get(cv2.CAP_PROP_FPS) or 30, idx=-10, img=None)
        idx = max(0, int(round(ts * c["fps"])))
        if idx != c["idx"]:
            if idx != c["idx"] + 1:
                c["cap"].set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, img = c["cap"].read()
            if ok:
                c["img"] = img
            c["idx"] = idx
        return c["img"]

    for f in range(total_f):
        t = f / FPS * US
        canvas = np.zeros((H, W, 3), np.uint8)
        live = set()
        for tk in d["tracks"]:
            if tk["type"] == "effect":
                for s in tk["segments"]:
                    tr = s["target_timerange"]
                    if tr["start"] <= t < tr["start"] + tr["duration"] and "blur" in (mats[s["material_id"]].get("name") or "").lower():
                        canvas = cv2.GaussianBlur(canvas, (0, 0), 28)
                continue
            if tk["type"] != "video":
                continue
            for s in tk["segments"]:
                tr = s["target_timerange"]
                if not (tr["start"] <= t < tr["start"] + tr["duration"]) or not s.get("visible", True):
                    continue
                live.add(s["id"])
                m = mats[s["material_id"]]
                sp = s.get("speed") or 1
                ts = ((s.get("source_timerange") or {}).get("start", 0) + (t - tr["start"]) * sp) / US
                img = frame_of(s, real(m["path"]), ts)
                if img is None:
                    continue
                cr = m.get("crop") or {}
                ih, iw = img.shape[:2]
                x0, x1 = int(cr.get("upper_left_x", 0) * iw), int(cr.get("upper_right_x", 1) * iw)
                y0, y1 = int(cr.get("upper_left_y", 0) * ih), int(cr.get("lower_left_y", 1) * ih)
                img = img[y0:y1, x0:x1]
                ih, iw = img.shape[:2]
                c = s["clip"]
                sc = kf_value(s, "KFTypeScaleX", ts, c["scale"]["x"]) * min(W / iw, H / ih)
                px = kf_value(s, "KFTypePositionX", ts, c["transform"]["x"])
                py = kf_value(s, "KFTypePositionY", ts, c["transform"]["y"])
                al = kf_value(s, "KFTypeAlpha", ts, c.get("alpha", 1.0))
                rot = kf_value(s, "KFTypeRotation", ts, c.get("rotation", 0.0))
                if al <= 0.004:
                    continue
                M = cv2.getRotationMatrix2D((iw / 2, ih / 2), -rot, sc)
                M[0, 2] += W / 2 + px * W / 2 - iw / 2
                M[1, 2] += H / 2 - py * H / 2 - ih / 2
                if c.get("flip", {}).get("horizontal"):
                    img = img[:, ::-1]
                warped = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
                if img.shape[2] == 4:
                    mask = warped[:, :, 3:4].astype(np.float32) / 255 * al
                    warped = warped[:, :, :3]
                else:
                    mask = cv2.warpAffine(np.full((ih, iw), 255, np.uint8), M, (W, H), flags=cv2.INTER_LINEAR)[:, :, None].astype(np.float32) / 255 * al
                canvas = (canvas * (1 - mask) + warped * mask).astype(np.uint8)
        for k in [k for k in caps if k not in live]:
            caps.pop(k)["cap"].release()
        pipe.stdin.write(canvas.tobytes())
    pipe.stdin.close()
    if pipe.wait():
        sys.exit("picture pass failed")


def main(name, out):
    proj = C.project_path(name)
    d = json.load(open(C.draft_file(proj)))
    mats = {x["id"]: x for v in d["materials"].values() if isinstance(v, list) for x in v if isinstance(x, dict) and "id" in x}
    real = lambda p: re.sub(r"##_draftpath_placeholder_[^#]*_##", proj, p)
    fr = lambda us: int(round(us / US * FPS))
    total_f = fr(d["duration"])
    work = tempfile.mkdtemp(prefix="preview_")

    # picture: every video track layered bottom to top as CapCut does, each clip with its crop, size, place, tilt,
    # opacity and keyframes; a Blur effect blurs what is under it (the user's collage and blurred review card were
    # missing from the first previews: ALEXXMAS notes, 2026-11-17)
    video, audio = os.path.join(work, "video.mp4"), os.path.join(work, "audio.wav")
    composite(d, mats, real, total_f, video)
    clips = [s for t in d["tracks"] if t["type"] == "video" for s in t["segments"]]

    # sound: every audio piece at the user's volume, plus the sound of clips they left on
    inputs, parts, labels = [], [], []
    def add(path, src, dur, start, vol, speed=1):
        k = len(labels)
        inputs.extend(["-i", path])
        tempo = ",atempo=%s" % speed if abs(speed - 1) > 1e-3 else ""
        parts.append("[%d:a]atrim=%.4f:%.4f,asetpts=PTS-STARTPTS%s,afade=t=in:d=0.008,volume=%.4f,adelay=%d:all=1[a%d]"
                     % (k, src, src + dur * speed, tempo, vol, round(start * 1000), k))
        labels.append("[a%d]" % k)
    for t in d["tracks"]:
        for s in t["segments"]:
            vol = s.get("volume") or 0
            if t["type"] not in ("audio", "video") or vol <= 0 or not s.get("source_timerange"):
                continue
            path = real(mats[s["material_id"]]["path"])
            if not os.path.exists(path) or (t["type"] == "video" and not has_audio(path)):
                continue
            tr = s["target_timerange"]
            add(path, s["source_timerange"]["start"] / US, tr["duration"] / US, tr["start"] / US, vol, s.get("speed") or 1)
    parts.append("%samix=inputs=%d:normalize=0:duration=longest,asetpts=N/SR/TB,atrim=0:%.3f,loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.82[a]"
                 % ("".join(labels), len(labels), total_f / FPS))
    script = os.path.join(work, "audio.txt")
    open(script, "w").write(";".join(parts))
    S.run([FF, "-v", "error", "-y"] + inputs + ["-filter_complex_script", script, "-map", "[a]", "-ar", "48000", audio])

    # text: the caption track in the house caption, any other text as a white box at its own height
    tdir = os.path.join(work, "text")
    os.makedirs(tdir)
    ttracks = [t for t in d["tracks"] if t["type"] == "text" and t["segments"]]
    capt = max(ttracks, key=lambda t: len(t["segments"])) if ttracks else None
    sched = []
    for t in ttracks:
        for s in t["segments"]:
            txt = json.loads(mats[s["material_id"]]["content"])["text"]
            tr = s["target_timerange"]
            pth = os.path.join(tdir, "t%03d.png" % len(sched))
            st0 = json.loads(mats[s["material_id"]]["content"])["styles"][0]
            # a text with its own background box (the user's hook box, the end boxes) is drawn as a house box in its
            # own colours, emoji included, whichever track or font it is on: the end boxes (Montserrat) came out as
            # bare text with no emoji, and a hook box on the caption track came out as a caption (XMASCUTOFF 2026-11-24)
            mat = mats[s["material_id"]]
            boxed = bool(mat.get("background_style")) and mat.get("background_alpha", 0) > 0
            if not boxed and "effectStyle" not in st0 and not st0.get("font", {}).get("path", "").endswith("en.ttf"):
                # plain text in its own font, size, tilt, see-through and place, with any position keyframes
                # (founder-style captions, ALEXXMAS 2026-11-17); 6.3 px per CapCut size point at 1080 wide
                tile = plain_text(txt, st0["font"]["path"], st0.get("size", 11) * 6.3, s["clip"].get("rotation", 0),
                                  s["clip"].get("alpha", 1.0), mats[s["material_id"]].get("alignment", 1),
                                  tuple(int(c * 255) for c in st0["fill"]["content"]["solid"]["color"]), "shadows" in st0)
                kx = {k["property_type"]: [(q["time_offset"] / US, q["values"][0]) for q in k["keyframe_list"]]
                      for k in s.get("common_keyframes") or []}
                f0, f1 = fr(tr["start"]), fr(tr["start"] + tr["duration"])
                def at(prop, tsec, base):
                    pts = kx.get(prop)
                    if not pts:
                        return base
                    if tsec <= pts[0][0]:
                        return pts[0][1]
                    for (ta, va), (tb, vb) in zip(pts, pts[1:]):
                        if tsec <= tb:
                            return va + (vb - va) * (tsec - ta) / max(tb - ta, 1e-6)
                    return pts[-1][1]
                steps = range(f0, f1) if kx else [f0]
                for f in steps:
                    x = at("KFTypePositionX", (f - f0) / FPS, s["clip"]["transform"]["x"])
                    y = at("KFTypePositionY", (f - f0) / FPS, s["clip"]["transform"]["y"])
                    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    px, py = int(W / 2 + x * W / 2 - tile.width / 2), int(H / 2 - y * H / 2 - tile.height / 2)
                    layer.paste(tile, (px, py), tile)
                    pth = os.path.join(tdir, "t%04d.png" % len(sched))
                    layer.save(pth, compress_level=1)
                    sched.append((f, f + 1 if kx else f1, pth))
                continue
            if t is capt and not boxed:
                HT.caption_img(S.balance_lines(txt.replace("\n", " "))).save(pth, compress_level=1)
            else:
                lines = txt.split("\n")
                hgt = HT.BOX_H2 if len(lines) > 1 else HT.BOX_H1
                cy = s["clip"]["transform"]["y"]
                layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                bg, ink = HT.WHITE, (0, 0, 0, 255)
                if boxed:
                    hx = (mat.get("background_color") or "#ffffff").lstrip("#")
                    bg = tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
                    ink = tuple(int(c * 255) for c in st0["fill"]["content"]["solid"]["color"]) + (255,)
                layer.alpha_composite(HT.box_layer(dict(lines=lines, color=bg, ink=ink,
                                                        top=round(H / 2 - cy * H / 2 - hgt / 2), paren=None)))
                layer.save(pth, compress_level=1)
            sched.append((fr(tr["start"]), fr(tr["start"] + tr["duration"]), pth))
    pr = subprocess.Popen([FF, "-y", "-v", "error", "-i", video, "-i", audio, "-f", "image2pipe", "-framerate", str(FPS),
                           "-c:v", "png", "-i", "-", "-filter_complex",
                           "[0:v]setpts=N/(%d*TB)[b];[2:v]format=rgba,setpts=N/(%d*TB)[t];[b][t]overlay=0:0:format=auto:shortest=1,format=yuv420p[v]" % (FPS, FPS),
                           "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-b:v", "12M",
                           "-maxrate", "14M", "-bufsize", "24M", "-r", str(FPS), "-fps_mode", "cfr", "-c:a", "aac", "-b:a", "192k",
                           "-ac", "2", "-movflags", "+faststart", "-t", "%.3f" % (total_f / FPS), out], stdin=subprocess.PIPE)
    cache = {}
    def frame(paths):
        if paths not in cache:
            im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            for p in paths:
                im.alpha_composite(Image.open(p).convert("RGBA"))
            fp = os.path.join(tdir, "f%04d.png" % len(cache))
            im.save(fp, compress_level=1)
            cache[paths] = open(fp, "rb").read()
        return cache[paths]
    for f in range(total_f + 1):
        pr.stdin.write(frame(tuple(p for a, b, p in sched if a <= f < b)))
    pr.stdin.close()
    if pr.wait():
        sys.exit("text pass failed")
    print("%s: %.2fs, %d clips, %d sounds, %d texts -> %s" % (name, total_f / FPS, len(clips), len(labels), len(sched), out))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
