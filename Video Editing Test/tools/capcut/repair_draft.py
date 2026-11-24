"""Repair a CapCut project written by an older story_ad.py: timeline id must match
the timeline folder, media must be outside hidden folders, and back-to-back segments must not overlap. CapCut must be closed.
usage: repair_draft.py "<project name>" [...]"""
import json, os, shutil, sys
sys.path.insert(0, os.path.dirname(__file__))
import capcut_draft as C

def repair(d, timeline_id, root):
    fixes = []
    # CapCut can't read hidden folders like ~/.video-editing-work: copy into the project
    media = os.path.join(root, "Resources", "media")
    for k in ("videos", "audios"):
        for m in d["materials"].get(k, []):
            if "/." in m.get("path", ""):
                os.makedirs(media, exist_ok=True)
                to = os.path.join(media, os.path.basename(m["path"]))
                if not os.path.exists(to):
                    shutil.copy(m["path"], to)
                m["path"] = to
                fixes.append("moved " + os.path.basename(to))
    if d["id"] != timeline_id:
        fixes.append("timeline id")
        d["id"] = timeline_id
    for t in d["tracks"]:
        segs = sorted(t["segments"], key=lambda s: s["target_timerange"]["start"])
        for a, b in zip(segs, segs[1:]):
            ta, tb = a["target_timerange"], b["target_timerange"]
            over = ta["start"] + ta["duration"] - tb["start"]
            if 0 < over <= 1000:  # rounding slips only, never real overlaps
                ta["duration"] -= over
                fixes.append("%s overlap %dus at %.3fs" % (t["type"], over, tb["start"] / 1e6))
            elif over > 1000:
                raise SystemExit("real overlap on %s track at %.3fs, not touching it" % (t["type"], tb["start"] / 1e6))
    return fixes

for name in sys.argv[1:]:
    root = C.project_path(name)
    tid = json.load(open(os.path.join(root, "Timelines", "project.json")))["main_timeline_id"]
    for p in [os.path.join(root, "draft_info.json"), os.path.join(root, "Timelines", tid, "draft_info.json")]:
        d = json.load(open(p))
        fixes = repair(d, tid, root)
        with open(p, "w") as f:
            json.dump(d, f, ensure_ascii=False)
        print(name, os.path.relpath(p, root), "->", len(fixes), "fixes:", ", ".join(fixes[:3]), "..." if len(fixes) > 3 else "")

