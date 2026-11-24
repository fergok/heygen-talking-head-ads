"""Make a hook variant from a CapCut project the user has finished.

Copies the project like CapCut's Duplicate, then swaps only the hook: everything before the body's first voiceover
piece is taken out (hook clips, hook title, hook voice pieces), the new hook's voice pieces go in, and the whole body
moves along by the difference. The body stays exactly as the user cut it. The hook clip slot, on the main track, gets the placeholder card,
since the user makes hook visuals by hand.

  swap_hook.py <spec.json>

spec: {"source": "<project>", "name": "<new project>", "card": "<placeholder mp4>",
       "pieces": [[src_in, src_out], ...]  (seconds in the voiceover file, breaths already left out),
       "title": "line one\\nline two 🎁"  (optional: draft hook title in the user's own title box),
       "subtitle": "(...)"  (optional: the second title box under it, if the source has one),
       "clips": [{"path": "...", "src_in": 0.0, "until": 2.63}, ...]  (optional, only when the user names the clips:
                by default the hook slot is the blank card for the user's own B-roll, standards 5.4aa; real clips in place of the
                card, each running until `until` seconds into the new hook; the last one runs to the hook's end),
       "captions": [["I spent under $90", 3.54], ...]  (optional: captions for the new hook's words, each with the
                second its first word starts in the voiceover file, styled like the body's captions),
       "title_y": 0.05  (optional: where the title box sits; the hook clips differ from the source's),
       "music_from_start": true  (optional: music that started after a clip hook now starts at 0 with the voice),
       "body_from": 15.1, "ignore_versions": [...]}
The ad always ends where the last clip ends: music or sound left running past it is cut there (STOCKING V1,
2026-11-10, had music running 33s past the last clip).
"""
import copy, json, os, re, shutil, subprocess, sys, time, uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut_draft as C

US, FPS = 1_000_000, 30


def uid():
    return str(uuid.uuid4()).upper()


def f2us(sec):
    return int(round(round(sec * FPS) / FPS * US))


def probe(path):
    """(width, height, seconds) of a clip."""
    import imageio_ffmpeg
    o = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", path], capture_output=True, text=True).stderr
    hh, mm, ss = re.search(r"Duration: (\d+):(\d+):([\d.]+)", o).groups()
    w, h = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", o).groups()
    return int(w), int(h), int(hh) * 3600 + int(mm) * 60 + float(ss)


def utf16(s):
    return len(s.encode("utf-16-le")) // 2


def finish_words(vo_path, pieces, tx=None, gap=0.03, tail=0.10, most=1.0):
    """Push each piece's end out so it never cuts off the last word.

    Whisper's word ends run early, worst on numbers: it ended "$17." at 11.52 when "seventeen dollars" ran
    to 12.12, so the V2 hook was cut at 11.77, mid-word (user, CHEAPGENIUS 2026-11-07; they moved it to 12.23).
    So the end is checked against the forced-aligned words (align_words.py): if the last word that starts
    inside the piece is still sounding at the end, the end moves to that word's aligned end plus 0.10s of tail,
    stopping 0.03s before the next word. A piece that already ends after its last word is left alone, so
    deliberate cuts in a pause (breaths taken out) are kept. Loudness alone can't tell: room tone and breaths
    sit at -45 to -50 dB, the same as a word's fading tail."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import story_ad as S
    tx = tx or os.path.join(os.path.dirname(vo_path), "tx", re.sub(r"\.\w+$", ".json", os.path.basename(vo_path)))
    if not os.path.exists(tx):
        print("no transcript at %s: hook piece ends not checked, so listen to them" % tx)
        return [list(x) for x in pieces]
    words = S.aligned_words(vo_path, tx)
    out = []
    for a, b in pieces:
        inside = [w for w in words if a - 0.05 <= w["start"] < b]
        nb = b
        if inside and inside[-1]["end"] > b - 0.02:
            nxt = [w["start"] for w in words if w["start"] > inside[-1]["start"] + 1e-3]
            nb = inside[-1]["end"] + tail
            if nxt:
                nb = min(nb, nxt[0] - gap)
            nb = round(min(max(nb, b), b + most), 3)
            print("piece %.2f-%.2f cut off \"%s\": end moved to %.2f" % (a, b, inside[-1]["word"], nb))
        out.append([a, nb])
    return out


def main(spec):
    if subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0:
        raise SystemExit("CapCut is open: close it first")
    src = C.project_path(spec["source"])
    root = os.path.dirname(src)
    # every version must sit on the user's corrected body: CHEAPGENIUS V3 went out on the old B-roll (user, 2026-11-09)
    import check_bodies
    fam = spec["source"].split(" - V")[0]
    sibs = [n for n in os.listdir(root) if n.startswith(fam + " - V") and os.path.isdir(os.path.join(root, n))
            and n not in spec.get("ignore_versions", [])]
    if len(sibs) > 1 and not check_bodies.compare(sorted(sibs), ref=spec["source"]):
        raise SystemExit("the versions of %s don't all have the same body: rebuild the odd ones from the corrected "
                         "body first, or list retired projects in the spec's ignore_versions" % fam)
    dest = os.path.join(root, spec["name"])
    if os.path.exists(dest):
        raise SystemExit("already exists: " + dest)
    d = json.load(open(C.draft_file(src)))
    auds = {m["id"]: m for m in d["materials"]["audios"]}
    # the voice track is the audio track with the most pieces. Taking the first one with more than 5 picked a
    # sound-effects track the user had dragged four voice pieces onto (FAKECHECK STYLE 3, 2026-11-11: 8 pieces
    # against the voice track's 37), and the copy came out 10s long
    vo_track = max((t for t in d["tracks"] if t["type"] == "audio"), key=lambda t: len(t["segments"]))
    vo_segs = sorted(vo_track["segments"], key=lambda s: s["target_timerange"]["start"])
    # main track: the video track with the most clips (CHEAPGENIUS: track 1, flag 2; DELIVERY: track 0, flag 0)
    main_t = max((t for t in d["tracks"] if t["type"] == "video"), key=lambda t: len(t["segments"]))
    if spec.get("body_from") is not None:
        # the hook ends where the body's voice starts: "body_from" is that second in the voiceover file. Needed
        # when the hook is a clip on the main track itself (DELIVERY V1, 2026-11-09: a found video with its own
        # sound and no voiceover, so the main track starts at 0)
        hook_end = next(s["target_timerange"]["start"] for s in vo_segs
                        if s["source_timerange"]["start"] >= (spec["body_from"] - 0.05) * US)
    else:
        # the hook ends where the first body clip starts on the main track
        hook_end = min(s["target_timerange"]["start"] for s in main_t["segments"])
    hook_vo = [s for s in vo_segs if s["target_timerange"]["start"] < hook_end]

    # new hook voice pieces, each running until the voice stops, frame-aligned and back to back
    vo_path = auds[hook_vo[0]["material_id"]]["path"] if hook_vo else auds[vo_segs[0]["material_id"]]["path"]
    new_len, pieces = 0, []
    for a, b in finish_words(vo_path, spec["pieces"]):
        dur = f2us(b - a)
        pieces.append((int(a * US), dur, new_len))
        new_len += dur
    delta = new_len - hook_end

    title_proto = sub_proto = title_track = sub_track = card_proto = card_main = None
    card_track = None
    for t in d["tracks"]:
        keep = []
        stretched = set()
        for s in sorted(t["segments"], key=lambda s: s["target_timerange"]["start"]):
            st = s["target_timerange"]["start"]
            if t is vo_track:
                continue
            en = st + s["target_timerange"]["duration"]
            # music the user started under the hook and split part-way for a volume change (GIFTGIVER2, 2026-11-16:
            # 0.17-27.3s then 27.3s to the end) is not a hook piece: it runs on, so it is stretched like whole-ad music
            runs_on = t["type"] == "audio" and st < hook_end and en > hook_end + US // 2
            # a short sound the user put just before the body to lead into it (NOBODYPRETEND V1, 2026-11-20: a
            # page-turn 0.24s before the body) belongs to the body: it moves with it, at its own length, not stretched
            lead_in = t["type"] == "audio" and hook_end - US <= st < hook_end and en - st < 3 * US and en > hook_end
            if lead_in:
                s["target_timerange"]["start"] = st + delta
                keep.append(s)
                continue
            if st < hook_end and not runs_on and s["target_timerange"]["duration"] < d["duration"] - US:   # hook-only pieces
                if t["type"] == "text":
                    if title_proto is None:
                        title_proto = s
                    elif sub_proto is None and t is not title_track:
                        sub_proto, sub_track = s, t
                    if title_proto is s:
                        title_track = t
                if t["type"] == "video" and (t is not main_t or card_main is None) and card_proto is None:
                    if t is main_t:
                        card_main = s       # fallback: the hook clip sat on the main track itself
                    else:
                        card_proto, card_track = s, t
                continue
            if st >= hook_end:
                s["target_timerange"]["start"] = st + delta
                if auds.get(s["material_id"], {}).get("path") in stretched and s.get("source_timerange"):   # a split makes a new material: match the file
                    s["source_timerange"]["start"] += delta      # the rest of the same music carries straight on
            else:                           # runs under the whole ad (music): fit it to the new length
                s["target_timerange"]["duration"] += delta
                s["source_timerange"]["duration"] = s["target_timerange"]["duration"]
                stretched.add(auds.get(s["material_id"], {}).get("path", s["material_id"]))
            keep.append(s)
        t["segments"] = keep

    # voice track: new hook pieces, then the body pieces moved along
    vo_new = []
    # a hook with no voice of its own (DELIVERY V1: a clip with its own sound) gives no piece to copy, so the
    # new hook's voice is modelled on the first body piece; without this the hook went in silent
    protos = hook_vo or [s for s in vo_segs if s["target_timerange"]["start"] >= hook_end][:1]
    for (a, dur, at), proto in zip(pieces, (protos * len(pieces))[:len(pieces)]):
        s = copy.deepcopy(proto)
        s["id"] = uid()
        s["source_timerange"] = {"start": a, "duration": dur}
        s["target_timerange"] = {"start": at, "duration": dur}
        vo_new.append(s)
    for s in vo_segs:
        if s["target_timerange"]["start"] >= hook_end:
            s["target_timerange"]["start"] += delta
            vo_new.append(s)
    vo_track["segments"] = vo_new

    # hook clip slot: the user's hook clips if the spec names them, else the placeholder card
    card_proto = card_proto or card_main
    vids = {m["id"]: m for m in d["materials"]["videos"]}
    slots = spec.get("clips") or [{"path": spec["card"], "src_in": 0.0, "card": True}]
    # CapCut is sandboxed and can't open files outside its own folders: a hook clip pointing at the work folder
    # showed as missing in CapCut (BLUECOLLAR V2/V3, 2026-11-21) while the preview still played it. Real clips go
    # in the project's own Resources/media, under the same placeholder path the body's media use, reusing a copy
    # that's already there (the talking-head file the body is cut from).
    ph = next((m["path"].split("/Resources/")[0] for m in vids.values()
               if m.get("path", "").startswith("##_draftpath_placeholder_") and "/Resources/" in m["path"]), None)
    to_copy = []
    def project_path(path):
        if ph is None:
            return path
        name = os.path.basename(path)
        if not os.path.exists(os.path.join(src, "Resources", "media", name)):
            to_copy.append(path)
        return ph + "/Resources/media/" + name
    body_scale = next((dict(s["clip"]["scale"]) for s in sorted(main_t["segments"], key=lambda s: s["target_timerange"]["start"])
                       if s["target_timerange"]["start"] >= hook_end + delta), None)
    t0 = 0
    for k, cl in enumerate(slots):
        t1 = new_len if k == len(slots) - 1 else f2us(cl["until"])
        w, h, dur = probe(cl["path"])       # the card too: a hook can run past 15s (ALEXXMAS, 2026-11-17)
        cm = copy.deepcopy(vids[card_proto["material_id"]])
        cm.update(id=uid(), path=cl["path"] if cl.get("card") else project_path(cl["path"]),
                  width=w, height=h, duration=int(dur * US))
        for key in ("material_name", "name"):
            if key in cm:
                cm[key] = os.path.basename(cl["path"])
        d["materials"]["videos"].append(cm)
        cs = copy.deepcopy(card_proto)
        cs.update(id=uid(), material_id=cm["id"], speed=1.0, volume=0.0)
        cs["source_timerange"] = {"start": f2us(cl.get("src_in", 0.0)), "duration": t1 - t0}
        cs["target_timerange"] = {"start": t0, "duration": t1 - t0}
        if cs["source_timerange"]["start"] + cs["source_timerange"]["duration"] > dur * US:
            raise SystemExit("hook clip too short: %s" % cl["path"])
        # a real clip of the same shot as the body (talking head) takes the body's zoom, so the cut doesn't jump
        cs["clip"]["scale"] = body_scale if (body_scale and not cl.get("card")) else {"x": 1.0, "y": 1.0}
        cs["clip"]["transform"] = {"x": 0.0, "y": 0.0}
        # on the main track, as the user puts hook clips (Hooks B and C, 2026-11-06). When the hook clip's own track
        # carries straight on into the body (GIFTGIVER2: hook clip then the first body clip on CapCut's bottom
        # track, the rest of the body on the track above), the card goes back there, so that track still starts at 0
        home = main_t
        if card_track is not None and any(x["target_timerange"]["start"] == hook_end + delta for x in card_track["segments"]):
            home = card_track
        home["segments"].append(cs)
        t0 = t1

    # captions for the new hook's words, copied from the body's first caption
    if spec.get("captions"):
        texts = {m["id"]: m for m in d["materials"]["texts"]}
        cap_t = next(t for t in d["tracks"] if t["type"] == "text" and t["segments"] and any(
            s["target_timerange"]["start"] == hook_end + delta for s in t["segments"]))
        cproto = min(cap_t["segments"], key=lambda s: s["target_timerange"]["start"])
        def at(sec):
            for a, dur, st in pieces:
                if a / US - 0.06 <= sec < (a + dur) / US:
                    return f2us(st / US + max(0.0, sec - a / US))
            raise SystemExit("caption word at %.2fs is not in the hook's voice" % sec)
        starts = [0] + [at(t) for _, t in spec["captions"][1:]]
        for (txt, _), st, en in zip(spec["captions"], starts, starts[1:] + [new_len]):
            tm = copy.deepcopy(texts[cproto["material_id"]])
            tm["id"] = uid()
            c = json.loads(tm["content"])
            c["text"] = txt
            for sty in c["styles"]:
                sty["range"] = [0, utf16(txt)]
            tm["content"] = json.dumps(c, ensure_ascii=False, separators=(",", ":"))
            d["materials"]["texts"].append(tm)
            ts = copy.deepcopy(cproto)
            ts.update(id=uid(), material_id=tm["id"])
            ts["target_timerange"] = {"start": st, "duration": en - st}
            cap_t["segments"].append(ts)

    # draft hook title in the user's own title box
    if spec.get("title") and title_proto:
        texts = {m["id"]: m for m in d["materials"]["texts"]}
        tm = copy.deepcopy(texts[title_proto["material_id"]])
        tm["id"] = uid()
        c = json.loads(tm["content"])
        c["text"] = spec["title"]
        for st in c["styles"]:
            st["range"] = [0, utf16(spec["title"])]
        tm["content"] = json.dumps(c, ensure_ascii=False, separators=(",", ":"))
        d["materials"]["texts"].append(tm)
        ts = copy.deepcopy(title_proto)
        ts.update(id=uid(), material_id=tm["id"])
        ts["target_timerange"] = {"start": 0, "duration": new_len}
        if spec.get("title_y") is not None:
            ts["clip"]["transform"]["y"] = spec["title_y"]
        if spec.get("captions"):
            title_track["segments"].insert(0, ts)     # its own track: the hook's captions run under it
        else:
            for t in d["tracks"]:
                if t["type"] == "text" and t["segments"] and any(
                        s["target_timerange"]["start"] == hook_end + delta for s in t["segments"]):
                    t["segments"].insert(0, ts)     # the caption track, where the user's title sat
                    break

    # second title box (the user's bracketed line under the title, CHEAPGENIUS 2026-11-07)
    if spec.get("subtitle") and sub_proto:
        texts = {m["id"]: m for m in d["materials"]["texts"]}
        tm = copy.deepcopy(texts[sub_proto["material_id"]])
        tm["id"] = uid()
        c = json.loads(tm["content"])
        c["text"] = spec["subtitle"]
        for st in c["styles"]:
            st["range"] = [0, utf16(spec["subtitle"])]
        tm["content"] = json.dumps(c, ensure_ascii=False, separators=(",", ":"))
        d["materials"]["texts"].append(tm)
        ts = copy.deepcopy(sub_proto)
        ts.update(id=uid(), material_id=tm["id"])
        ts["target_timerange"] = {"start": 0, "duration": new_len}
        sub_track["segments"].insert(0, ts)

    d["duration"] += delta
    if spec.get("music_from_start"):
        for t in d["tracks"]:
            if t["type"] != "audio" or t is vo_track:
                continue
            segs = sorted(t["segments"], key=lambda s: s["target_timerange"]["start"])
            if segs and segs[0]["target_timerange"]["start"] == hook_end + delta and \
                    sum(s["target_timerange"]["duration"] for s in segs) > 8 * US:
                for s in segs:      # pull the whole music track back to 0, so it runs on unbroken
                    if s is segs[0]:
                        s["target_timerange"]["start"] = 0
                        s["target_timerange"]["duration"] += hook_end + delta
                        s["source_timerange"]["duration"] = s["target_timerange"]["duration"]
                    else:
                        s["source_timerange"]["start"] += hook_end + delta
    end = max(s["target_timerange"]["start"] + s["target_timerange"]["duration"]
              for t in d["tracks"] if t["type"] == "video" for s in t["segments"])
    for t in d["tracks"]:
        keep = []
        for s in t["segments"]:
            tr = s["target_timerange"]
            if tr["start"] >= end:
                continue
            if tr["start"] + tr["duration"] > end:
                tr["duration"] = end - tr["start"]
                if s.get("source_timerange"):
                    s["source_timerange"]["duration"] = int(round(tr["duration"] * (s.get("speed") or 1.0)))
            keep.append(s)
        t["segments"] = keep
    d["duration"] = end
    for t in d["tracks"]:
        t["segments"].sort(key=lambda s: s["target_timerange"]["start"])
        for x, y in zip(t["segments"], t["segments"][1:]):
            if x["target_timerange"]["start"] + x["target_timerange"]["duration"] > y["target_timerange"]["start"]:
                raise SystemExit("overlap on a %s track at %.2fs" % (t["type"], y["target_timerange"]["start"] / US))

    # write the copy
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("*.bak", "template*.tmp", "matting", "smart_crop",
                                                             "adjust_mask", "qr_upload", "subdraft"))
    for path in to_copy:
        os.makedirs(os.path.join(dest, "Resources", "media"), exist_ok=True)
        shutil.copy2(path, os.path.join(dest, "Resources", "media", os.path.basename(path)))
    proj_p = os.path.join(dest, "Timelines", "project.json")
    proj = json.load(open(proj_p))
    now = int(time.time() * US)
    proj["id"] = uid()
    proj["create_time"] = proj["update_time"] = now
    json.dump(proj, open(proj_p, "w"))
    if d.get("id") != proj["main_timeline_id"]:
        raise SystemExit("timeline id mismatch")
    for p in [os.path.join(dest, "draft_info.json"),
              os.path.join(dest, "Timelines", proj["main_timeline_id"], "draft_info.json")]:
        json.dump(d, open(p, "w"), ensure_ascii=False)
    meta_p = os.path.join(dest, "draft_meta_info.json")
    meta = json.load(open(meta_p))
    draft_id = uid()
    meta.update(draft_id=draft_id, draft_name=spec["name"], draft_fold_path=dest, draft_root_path=root,
                tm_duration=d["duration"], tm_draft_create=now, tm_draft_modified=now)
    json.dump(meta, open(meta_p, "w"), ensure_ascii=False)
    rp = os.path.join(root, "root_meta_info.json")
    shutil.copy(rp, rp + ".before-%s.bak" % re.sub(r"\W+", "_", spec["name"]))
    rm = json.load(open(rp))
    ent = copy.deepcopy(next(x for x in rm["all_draft_store"] if x["draft_fold_path"].rstrip("/") == src.rstrip("/")))
    ent.update(draft_id=draft_id, draft_name=spec["name"], draft_fold_path=dest, draft_root_path=root,
               draft_cover=os.path.join(dest, "draft_cover.jpg"), draft_json_file=os.path.join(dest, "draft_info.json"),
               tm_duration=d["duration"], tm_draft_create=now, tm_draft_modified=now)
    # never leave a second entry for the same folder (duplicate "BLUECOLLAR HookA" listings, 2026-11-21)
    rm["all_draft_store"] = [x for x in rm["all_draft_store"] if x.get("draft_fold_path", "").rstrip("/") != dest.rstrip("/")]
    rm["all_draft_store"].insert(0, ent)
    json.dump(rm, open(rp, "w"), ensure_ascii=False)
    print("%s: hook %.2fs (was %.2fs), total %.2fs" % (spec["name"], new_len / US, hook_end / US, d["duration"] / US))
    return dest


if __name__ == "__main__":
    main(json.load(open(sys.argv[1])))
