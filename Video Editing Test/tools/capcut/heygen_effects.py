#!/usr/bin/env python3
"""Put the HeyGen-style effects into CapCut projects, so the user's export has them (XMASCUTOFF, 2026-11-24).

  heygen_effects.py <assets dir> [--bubble "<project>"] "<project>" ...

The MP4 renderer draws black-and-white fakes, the blurred marketplace scroll and the comment-reply bubble itself;
the CapCut writer doesn't. This swaps those clips for ready-made copies (BW_<name>.mp4, BLUR_amazon_scroll.mp4 in the
assets dir, copied into the project's own Resources/media) and, for --bubble, lays reply_bubble.png over the hook.
Timing, scale and everything else the user set on those clips stay as they are. Safe to run twice.
"""
import copy, json, os, shutil, subprocess, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut_draft as C
US = 1_000_000
uid = lambda: str(uuid.uuid4()).upper()
BLUR_SRC = "ScreenRecording_11-06-2026 16-40-25_1.MP4"


def main(argv):
    if subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0:
        raise SystemExit("CapCut is open: close it first")
    assets, args, bubble = argv[1], argv[2:], set()
    names = []
    while args:
        a = args.pop(0)
        if a == "--bubble":
            n = args.pop(0); bubble.add(n); names.append(n)
        else:
            names.append(a)
    swaps = {}
    for f in os.listdir(assets):
        if f.startswith("BW_"):
            swaps[os.path.splitext(f[3:])[0]] = f
    for name in names:
        proj = C.project_path(name)
        files = [os.path.join(proj, "draft_info.json")]
        tl = json.load(open(os.path.join(proj, "Timelines", "project.json")))["main_timeline_id"]
        files.append(os.path.join(proj, "Timelines", tl, "draft_info.json"))
        d = json.load(open(C.draft_file(proj)))
        vids = d["materials"]["videos"]
        ph = next(m["path"].split("/Resources/")[0] for m in vids if m.get("path", "").startswith("##_draftpath_placeholder_"))
        media = os.path.join(proj, "Resources", "media")
        os.makedirs(media, exist_ok=True)
        done = []
        for m in vids:
            base = os.path.basename(m.get("path", ""))
            new = swaps.get(os.path.splitext(base)[0]) or ("BLUR_amazon_scroll.mp4" if base == BLUR_SRC else None)
            if not new:
                continue
            shutil.copy2(os.path.join(assets, new), os.path.join(media, new))
            m.update(path=ph + "/Resources/media/" + new, has_audio=False)
            for k in ("material_name", "name"):
                if k in m:
                    m[k] = new
            done.append(new)
        if name in bubble and not any(os.path.basename(m.get("path", "")) == "reply_bubble.png" for m in vids):
            from PIL import Image
            png = os.path.join(assets, "reply_bubble.png")
            w, h = Image.open(png).size
            shutil.copy2(png, os.path.join(media, "reply_bubble.png"))
            main_t = max((t for t in d["tracks"] if t["type"] == "video"), key=lambda t: len(t["segments"]))
            vo = max((t for t in d["tracks"] if t["type"] == "audio"), key=lambda t: len(t["segments"]))
            # the hook ends where the first caption starts
            cap_t = max((t for t in d["tracks"] if t["type"] == "text"), key=lambda t: len(t["segments"]))
            hook_end = min(s["target_timerange"]["start"] for s in cap_t["segments"])
            proto = min(main_t["segments"], key=lambda s: s["target_timerange"]["start"])
            pm = next(m for m in vids if m["id"] == proto["material_id"])
            nm = copy.deepcopy(pm)
            nm.update(id=uid(), type="photo", path=ph + "/Resources/media/reply_bubble.png", width=w, height=h,
                      duration=10800 * US, has_audio=False)
            for k in ("material_name", "name"):
                if k in nm:
                    nm[k] = "reply_bubble.png"
            vids.append(nm)
            byid = {}
            for key, lst in d["materials"].items():
                if isinstance(lst, list):
                    for m in lst:
                        if isinstance(m, dict) and "id" in m:
                            byid[m["id"]] = (key, m)
            seg = copy.deepcopy(proto)
            refs = []
            for r in proto.get("extra_material_refs", []):
                key, m = byid[r]
                c = copy.deepcopy(m); c["id"] = uid()
                d["materials"][key].append(c); refs.append(c["id"])
            # 640px wide on the 1080 canvas, top at y 1010 (over her chest), as in the MP4
            sc = 640 / 1080
            cy = 1010 + h * 640 / w / 2
            seg.update(id=uid(), material_id=nm["id"], extra_material_refs=refs, speed=1.0, volume=0.0,
                       source_timerange={"start": 0, "duration": hook_end}, target_timerange={"start": 0, "duration": hook_end})
            seg["clip"]["scale"] = {"x": sc, "y": sc}
            seg["clip"]["transform"] = {"x": 0.0, "y": (960 - cy) / 960}
            if "uniform_scale" in seg:
                seg["uniform_scale"] = {"on": True, "value": sc}
            # an overlay track above the main one, free during the hook; else a new one
            home = next((t for t in d["tracks"] if t["type"] == "video" and t is not main_t and t["segments"]
                         and d["tracks"].index(t) > d["tracks"].index(main_t)
                         and all(s["target_timerange"]["start"] >= hook_end for s in t["segments"])), None)
            if home is None:
                home = copy.deepcopy(main_t); home.update(id=uid(), segments=[])
                d["tracks"].insert(d["tracks"].index(main_t) + 1, home)
            else:
                o = home["segments"][0]
                seg["render_index"], seg["track_render_index"] = o.get("render_index", 0) + 1, o.get("track_render_index", 0)
            home["segments"].insert(0, seg)
            done.append("reply_bubble.png 0-%.2fs" % (hook_end / US))
        for p in files:
            json.dump(d, open(p, "w"), ensure_ascii=False)
        print("%s: %s" % (name, ", ".join(done)))


if __name__ == "__main__":
    main(sys.argv)
