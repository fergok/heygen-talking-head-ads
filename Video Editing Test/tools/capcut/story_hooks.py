#!/usr/bin/env python3
"""story_ad.py, plus a filled and captioned hook slot (Lumi Light copies, RUNBOOK step 5, 2026-11-07).

  story_hooks.py <edit.json> --hook A [--mp4] [--capcut]

story_ad.py leaves the hook slot as a placeholder card with no text, because the user makes most hooks by hand.
The daily Lumi Light copies must be ready to upload, so this wrapper adds, per hook, from the edit file:
  hook_shots[hook]:    [{t, clip, src_in, speed?, zoom?, x?, y?}]  t = VO second the shot starts (first one = hook start)
  hook_captions[hook]: [{t, text}]                                  house captions under the hook voice (style.md)
  hook_text[hook]:     ["LINE 1", "LINE 2"] or [["red box lines"], ["white box lines"]]   the hook overlay (rulebook 3)
Captions start on the aligned word start (7.8aa) or the piece's own tick (7.8ad), and hold until the next (7.7).
Everything else is story_ad.py unchanged.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import story_ad as S

HT, FPS, W, H = S.HT, S.FPS, S.W, S.H
HOOK_TOP = 300          # preferred hook box top: the top of the 4:5 safe zone (y 285); place_hook_box moves it off faces
SAFE_TOP = 290          # rulebook 8.1: the 4:5 safe zone is y 285 to 1635
YUNET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models", "face_detection_yunet_2023mar.onnx")


def box_extent(ht):
    """Height and x span of the stacked hook boxes when drawn from top 0."""
    boxes = ht if isinstance(ht[0], list) else [ht]
    im = S.Image.new("RGBA", (W, H), (0, 0, 0, 0))
    top = 0
    for i, lines in enumerate(boxes):
        im.alpha_composite(HT.box_layer(dict(lines=lines, color=HT.WHITE, ink=(0, 0, 0, 255), top=top, paren=None)))
        top += (HT.BOX_H2 if len(lines) > 1 else HT.BOX_H1) + 6
    x0, y0, x1, y1 = im.getchannel("A").getbbox()
    return y1, x0, x1


def clean_frames(shots, work):
    """Frames of the hook shots as they will be framed in the render (render_mp4's scale and offset), with no text,
    every 0.25s. The box can't be judged from an export: it hides the face it covers."""
    d = os.path.join(work, "faces")
    os.makedirs(d, exist_ok=True)
    out = []
    for i, s in enumerate(shots):
        info = S.probe(s["clip"])
        cover = max(W / info["w"], H / info["h"]) * s.get("zoom", 1)
        sw, sh = int(info["w"] * cover / 2) * 2, int(info["h"] * cover / 2) * 2
        ox = int((W - sw) / 2 + s.get("x", 0) * W / 2)
        oy = int((H - sh) / 2 - s.get("y", 0) * H / 2)
        dur, t = s["end"] - s["start"], 0.0
        while t < dur:
            p = os.path.join(d, "s%02d_%04d.jpg" % (i, int(t * 100)))
            S.run([S.FF, "-v", "error", "-y", "-ss", "%.3f" % (s["src_in"] + t * s.get("speed", 1)), "-i", s["clip"],
                   "-filter_complex", "[0:v]setpts=PTS-STARTPTS,scale=%d:%d[v];color=black:s=%dx%d[bg];[bg][v]overlay=%d:%d:shortest=1" % (sw, sh, W, H, ox, oy),
                   "-frames:v", "1", "-q:v", "4", p])
            if os.path.exists(p):
                out.append((i, p))
            t += 0.25
    return out


def place_hook_box(tl, work, fixed=None):
    """Rulebook 8.1 and 8.5a: the hook box sits inside the 4:5 safe zone and covers no face (with the hair and
    forehead above it, where the headlamp is). Picks the highest top that clears every face in every sampled frame
    of the hook, above the captions. If none clears, the least-covering spot, with a warning to change the shot."""
    blk, bx0, bx1 = box_extent(tl["hook_text"])
    cap = HT.caption_img("Sample caption").getchannel("A").getbbox()
    lowest = cap[1] - 24 - blk
    if fixed is not None:
        return fixed, []
    import cv2
    det = cv2.FaceDetectorYN.create(YUNET, "", (W, H), 0.65)
    zones = []
    for i, p in clean_frames([s for s in tl["shots"] if s.get("kind") == "hookclip"], work):
        im = cv2.imread(p)
        det.setInputSize((im.shape[1], im.shape[0]))
        _, faces = det.detect(im)
        for r in ([] if faces is None else faces):
            x, y, w, h = [float(v) for v in r[:4]]
            if w < 90:
                continue
            zones.append((i, x - 0.15 * w, y - 0.45 * h, x + 1.15 * w, y + 1.1 * h))

    def cover(top):
        tot, hit = 0.0, set()
        for i, x0, y0, x1, y1 in zones:
            ow = min(x1, bx1) - max(x0, bx0)
            oh = min(y1, top + blk) - max(y0, top)
            if ow > 0 and oh > 0:
                tot += ow * oh
                hit.add(i)
        return tot, hit

    best = min(range(SAFE_TOP, max(SAFE_TOP, lowest) + 1, 5), key=lambda t: (cover(t)[0], abs(t - HOOK_TOP)))
    tot, hit = cover(best)
    warns = ["hook box still covers a face in hook shot %d: reframe it or pick another clip (8.5a)" % i for i in sorted(hit)]
    return best, warns


def omap_for(tl):
    vo = tl["vo"]

    def omap(ts):
        for p in vo:
            if p["src_in"] - 1e-6 <= ts <= p["src_out"] + 1e-6:
                return p["start"] + ts - p["src_in"]
            if ts < p["src_in"]:
                return p["start"]
        return tl["total"]
    return omap


def hook_frame(e, tl, t, omap, aligned):
    piece_f = [int(round(p["start"] * FPS)) for p in tl["vo"]]
    w = min(aligned, key=lambda w: abs(w["w_start"] - t))
    f = S.frame_of(omap(w["start"] - S.ALIGN_LEAD))
    # snap only to the tick of the piece holding this word (by its middle), never the next word's piece (story_ad)
    mid = (w["start"] + w["end"]) / 2
    own = next((k for k, p in enumerate(tl["vo"]) if mid < p["src_out"]), len(tl["vo"]) - 1)
    return piece_f[own] if f - 4 <= piece_f[own] <= f + 12 else f


def add_hook(e, tl, hook):
    omap = omap_for(tl)
    hook_f = tl["shots"][1]["f0"]                 # first body shot = first body caption (story_ad)
    txp = e.get("vo_tx") or os.path.join(os.path.dirname(e["vo"]), "tx", os.path.splitext(os.path.basename(e["vo"]))[0] + ".json")
    aligned = S.aligned_words(e["vo"], txp)

    # shots
    shots = []
    for k, sh in enumerate(e["hook_shots"][hook]):
        f0 = 0 if k == 0 else hook_frame(e, tl, sh["t"], omap, aligned)
        shots.append(dict(clip=sh["clip"], src_in=sh["src_in"], speed=sh.get("speed", 1), zoom=sh.get("zoom", 1.03 if os.path.basename(sh["clip"]).startswith("hf_") else 1),
                          x=sh.get("x", 0), y=sh.get("y", 0), mute=True, f0=f0, kind="hookclip"))
    for i, sh in enumerate(shots):
        sh["f1"] = shots[i + 1]["f0"] if i + 1 < len(shots) else hook_f
        sh["start"], sh["end"] = sh["f0"] / FPS, sh["f1"] / FPS
        need = (sh["end"] - sh["start"]) * sh["speed"]
        info = S.probe(sh["clip"])
        if sh["src_in"] + need > info["dur"] - 0.04:
            sh["warn"] = "hook clip too short: wanted %.2f-%.2f of %.2fs" % (sh["src_in"], sh["src_in"] + need, info["dur"])
            sh["src_in"] = max(0, info["dur"] - 0.04 - need)
            if sh["src_in"] == 0 and need > info["dur"]:
                sh["speed"] = round(info["dur"] / (sh["end"] - sh["start"]) * 0.98, 3)
    shots = [s for s in shots if s["f1"] > s["f0"]]
    for sh, src in zip(shots, e["hook_shots"][hook]):
        if src.get("talk"):                      # a HeyGen character hook: lips follow the cut voice (story_ad.expand_talk)
            sh["talk"] = True
    shots = S.expand_talk(shots, tl["vo"])
    tl["shots"] = shots + tl["shots"][1:]

    # captions under the hook voice
    caps = []
    for k, c in enumerate(e["hook_captions"][hook]):
        f = 0 if k == 0 else hook_frame(e, tl, c["t"], omap, aligned)
        caps.append([f, c["text"]])
    hc = []
    for i, (f, txt) in enumerate(caps):
        f1 = caps[i + 1][0] if i + 1 < len(caps) else hook_f
        if f1 > f:
            hc.append(dict(text=txt, f0=f, f1=f1, start=f / FPS, end=f1 / FPS))
    tl["hook_captions"] = hc
    tl["hook_text"] = e["hook_text"][hook]
    tl["hook_f"] = hook_f
    return tl


_orig_text_frames = S.text_frames


def text_frames(tl, work):
    """story_ad's text frames, plus the hook: the render takes one text image per frame, so each hook caption is
    drawn onto the hook box (one PNG per hook caption)."""
    sched = _orig_text_frames(tl, work)
    box = S.Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ht = tl.get("hook_text")
    if tl.get("caption_style") == "lumi":
        # their hook text IS the hook captions, in capitals on one white box, phrase by phrase (Lumi RUNBOOK rule 4)
        for k, c in enumerate(tl.get("hook_captions", [])):
            pth = os.path.join(work, "hook%03d.png" % k)
            HT.hook_caption_img_lumi(c["text"], dict(HT.lumi_look(tl), **({"offer": tl["hook_offer"]} if tl.get("hook_offer") else {}))).save(pth, compress_level=1)
            sched.append((c["f0"], c["f1"], pth))
        return sched
    if ht:
        boxes = ht if isinstance(ht[0], list) else [ht]
        top = tl.get("hook_top", HOOK_TOP)
        for i, lines in enumerate(boxes):
            red = i == 0 and len(boxes) > 1
            spec = dict(lines=lines, color=HT.RED if red else HT.WHITE, ink=HT.WHITE if red else (0, 0, 0, 255), top=top, paren=None)
            box.alpha_composite(HT.box_layer(spec))
            top += (HT.BOX_H2 if len(lines) > 1 else HT.BOX_H1) + 6
    if tl.get("hook_image"):
        # a ready-made hook overlay, such as a TikTok comment-reply bubble (Styles/HeyGen talking head): a PNG
        # scaled to "width" px and centred on x, its top at "top"
        hi = tl["hook_image"]
        im = S.Image.open(hi["path"]).convert("RGBA")
        w = int(hi.get("width", 620))
        im = im.resize((w, round(im.height * w / im.width)), S.Image.LANCZOS)
        box.alpha_composite(im, ((W - w) // 2 + int(hi.get("x", 0)), int(hi.get("top", 900))))
    caps = tl.get("hook_captions", [])
    if not caps:
        caps = [dict(text="", f0=0, f1=tl["hook_f"])]
    for k, c in enumerate(caps):
        im = box.copy()
        if c["text"]:
            im.alpha_composite(HT.caption_img(S.balance_lines(c["text"])))
        pth = os.path.join(work, "hook%03d.png" % k)
        im.save(pth, compress_level=1)
        sched.append((c["f0"], c["f1"], pth))
    return sched


S.text_frames = text_frames


def main(argv):
    edit = json.load(open(argv[1]))
    hook = argv[argv.index("--hook") + 1]
    tl = S.compile_timeline(edit, hook)
    tl = add_hook(edit, tl, hook)
    base = os.path.dirname(os.path.abspath(argv[1]))
    work = os.path.join(base, "build", "Hook" + hook)
    os.makedirs(work, exist_ok=True)
    tl["caption_style"] = edit.get("caption_style")
    tl["lumi_look"] = edit.get("lumi_look")
    tl["hook_offer"] = (edit.get("hook_offer") or {}).get(hook)
    tl["hook_image"] = (edit.get("hook_image") or {}).get(hook)
    if tl["caption_style"] == "lumi":
        tl["hook_top"], warns = HT.lumi_look(tl)["hook_top"], []
    elif not tl["hook_text"]:                     # no hook box: captions only under the hook voice
        tl["hook_top"], warns = HOOK_TOP, []
    else:
        tl["hook_top"], warns = place_hook_box(tl, work, edit.get("hook_text_top", {}).get(hook))
    print("Hook %s box top: y %d" % (hook, tl["hook_top"]))
    for w in warns:
        print("  WARN " + w)
    json.dump(tl, open(os.path.join(work, "timeline.json"), "w"), indent=1)
    print("Hook %s: %.2fs, hook %.2fs, %d shots, %d captions + %d hook captions"
          % (hook, tl["total"], tl["hook_f"] / FPS, len(tl["shots"]), len(tl["captions"]), len(tl["hook_captions"])))
    for s in tl["shots"]:
        if s.get("warn"):
            print("  WARN %.2f %s: %s" % (s["start"], os.path.basename(s["clip"]), s["warn"]))
        if s["end"] - s["start"] > 3.6:
            print("  LONG %.2f-%.2f %s" % (s["start"], s["end"], os.path.basename(s["clip"])))
    out = os.path.join(work, "%s_Hook%s.mp4" % (edit["code"], hook))
    if "--mp4" in argv:
        S.render_mp4(edit, tl, out, os.path.join(work, "parts"))
        print("mp4:", out)
    if "--capcut" in argv:
        cover = os.path.join(work, "cover.jpg")
        if os.path.exists(out):
            S.run([S.FF, "-v", "error", "-y", "-ss", "%.2f" % (tl["hook_f"] / FPS + 1), "-i", out, "-frames:v", "1", "-vf", "scale=540:-2", cover])
        dest = S.write_capcut(edit, tl, "%s Hook%s" % (edit["code"], hook), cover if os.path.exists(cover) else None)
        json.dump(S.C.normalise(dest), open(os.path.join(work, "capcut_snapshot.json"), "w"), indent=1)
        print("capcut:", dest)


if __name__ == "__main__":
    main(sys.argv)
