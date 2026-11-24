#!/usr/bin/env python3
"""Make a version from the user's corrected V1 body plus the hook the user made in another project.

  graft_hook.py "<V1 project>" "<project with the hook>" "<new project name>" <body_from>

body_from is the second in the voiceover file where the body starts (the same in both projects). Everything before
it in the hook project (clips on any track, title text, hook voice pieces) is carried over exactly as the user left
it, with its own music for the whole ad (each version has its own song, rulebook 5.4ab). Everything from it on comes
from V1, moved along by the difference in hook length. Unlike swap_hook.py, which builds a draft hook, this keeps a
hook the user has already edited by hand (XMASCUTOFF, 2026-11-24).
"""
import copy, json, os, re, shutil, subprocess, sys, time, uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut_draft as C

US = 1_000_000
uid = lambda: str(uuid.uuid4()).upper()
start = lambda s: s["target_timerange"]["start"]
end = lambda s: s["target_timerange"]["start"] + s["target_timerange"]["duration"]


def vo_track(d):
    return max((t for t in d["tracks"] if t["type"] == "audio"), key=lambda t: len(t["segments"]))


def body_start(d, body_from):
    return min(start(s) for s in vo_track(d)["segments"] if s["source_timerange"]["start"] >= (body_from - 0.05) * US)


def is_music(d, t):
    """An audio track that isn't the voice and holds a long piece (the song), possibly split for volume changes."""
    return t["type"] == "audio" and t is not vo_track(d) and sum(s["target_timerange"]["duration"] for s in t["segments"]) > 20 * US


def main(v1_name, hook_name, new_name, body_from):
    if subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0:
        raise SystemExit("CapCut is open: close it first")
    src, hsrc = C.project_path(v1_name), C.project_path(hook_name)
    root = os.path.dirname(src)
    dest = os.path.join(root, new_name)
    if os.path.exists(dest):
        raise SystemExit("already exists: " + dest)
    d = json.load(open(C.draft_file(src)))
    h = json.load(open(C.draft_file(hsrc)))
    b1, bh = body_start(d, body_from), body_start(h, body_from)
    delta = bh - b1

    # V1: keep the body, moved along; drop its hook and its song
    v1_vo = vo_track(d)
    for t in d["tracks"]:
        if is_music(d, t):
            t["segments"] = []
            continue
        keep = []
        for s in t["segments"]:
            if start(s) < b1:
                continue
            s["target_timerange"]["start"] += delta
            keep.append(s)
        t["segments"] = keep
    body_end = max(end(s) for t in d["tracks"] if t["type"] == "video" for s in t["segments"])

    # hook project: every piece that starts before its body, plus its song
    have = {m["id"] for lst in d["materials"].values() if isinstance(lst, list) for m in lst if isinstance(m, dict) and "id" in m}
    hmat = {}
    for key, lst in h["materials"].items():
        if isinstance(lst, list):
            for m in lst:
                if isinstance(m, dict) and "id" in m:
                    hmat[m["id"]] = (key, m)
    h_vo = vo_track(h)
    moved = []
    for t in h["tracks"]:
        music = is_music(h, t)
        take = [s for s in t["segments"] if music and s["target_timerange"]["duration"] > 5 * US or start(s) < bh and not music]
        if not take:
            continue
        take = copy.deepcopy(take)
        for s in take:
            if end(s) > body_end:
                s["target_timerange"]["duration"] = body_end - start(s)
                if s.get("source_timerange"):
                    s["source_timerange"]["duration"] = int(round(s["target_timerange"]["duration"] * (s.get("speed") or 1.0)))
            for mid in [s.get("material_id")] + list(s.get("extra_material_refs") or []):
                if mid in hmat and mid not in have:
                    key, m = hmat[mid]
                    d["materials"].setdefault(key, []).append(copy.deepcopy(m))
                    have.add(mid)
        # home: the voice goes on the voice track; anything else on the first track of its type with room, else a new one
        if t is h_vo:
            home = v1_vo
        else:
            home = next((x for x in d["tracks"] if x["type"] == t["type"] and x is not v1_vo and x.get("flag") == t.get("flag")
                         and not any(start(a) < end(b) and start(b) < end(a) for a in take for b in x["segments"])), None)
            if home is None:
                home = next((x for x in d["tracks"] if x["type"] == t["type"] and x is not v1_vo
                             and not any(start(a) < end(b) and start(b) < end(a) for a in take for b in x["segments"])), None)
        if home is None:
            home = copy.deepcopy(t)
            home.update(id=uid(), segments=[])
            d["tracks"].append(home)
        home["segments"].extend(take)
        moved.append((t["type"], len(take)))
    for t in d["tracks"]:
        t["segments"].sort(key=start)
        for x, y in zip(t["segments"], t["segments"][1:]):
            if end(x) > start(y):
                raise SystemExit("overlap on a %s track at %.2fs" % (t["type"], start(y) / US))
    d["duration"] = body_end

    # write the copy (as swap_hook.py does)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("*.bak", "template*.tmp", "matting", "smart_crop",
                                                             "adjust_mask", "qr_upload", "subdraft"))
    proj_p = os.path.join(dest, "Timelines", "project.json")
    proj = json.load(open(proj_p))
    now = int(time.time() * US)
    proj["id"] = uid()
    proj["create_time"] = proj["update_time"] = now
    json.dump(proj, open(proj_p, "w"))
    if d.get("id") != proj["main_timeline_id"]:
        raise SystemExit("timeline id mismatch")
    for p in [os.path.join(dest, "draft_info.json"), os.path.join(dest, "Timelines", proj["main_timeline_id"], "draft_info.json")]:
        json.dump(d, open(p, "w"), ensure_ascii=False)
    meta_p = os.path.join(dest, "draft_meta_info.json")
    meta = json.load(open(meta_p))
    draft_id = uid()
    meta.update(draft_id=draft_id, draft_name=new_name, draft_fold_path=dest, draft_root_path=root,
                tm_duration=d["duration"], tm_draft_create=now, tm_draft_modified=now)
    json.dump(meta, open(meta_p, "w"), ensure_ascii=False)
    rp = os.path.join(root, "root_meta_info.json")
    shutil.copy(rp, rp + ".before-%s.bak" % re.sub(r"\W+", "_", new_name))
    rm = json.load(open(rp))
    ent = copy.deepcopy(next(x for x in rm["all_draft_store"] if x["draft_fold_path"].rstrip("/") == src.rstrip("/")))
    ent.update(draft_id=draft_id, draft_name=new_name, draft_fold_path=dest, draft_root_path=root,
               draft_cover=os.path.join(dest, "draft_cover.jpg"), draft_json_file=os.path.join(dest, "draft_info.json"),
               tm_duration=d["duration"], tm_draft_create=now, tm_draft_modified=now)
    rm["all_draft_store"] = [x for x in rm["all_draft_store"] if x.get("draft_fold_path", "").rstrip("/") != dest.rstrip("/")]
    rm["all_draft_store"].insert(0, ent)
    json.dump(rm, open(rp, "w"), ensure_ascii=False)
    print("%s: hook %.2fs (V1's was %.2fs), total %.2fs, carried over %s" % (new_name, bh / US, b1 / US, body_end / US, moved))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]))
