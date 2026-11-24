"""Learn the user's B-roll picks and timings from a CapCut project they finished.

    learn_picks.py add "<project>" --ad STOCKING [--hook-end 2.8] [--log <brand clip-log.json>]
    learn_picks.py report [--log ...]

`add` reads the project and records, for every video shot: the captions it sits under,
the clip and folder, the in-point, length, speed, zoom, whether its own sound is kept,
and when the picture changes sharply inside the shot (a light switching on or off),
measured against the start of the caption it lands in. It also logs the sound effects
and the caption each one sits on. Shots before --hook-end are marked as hook shots, and
clips outside the B-roll library (Downloads, AI clips made for one ad) as one-offs, so
the report can leave them out of the go-to counts.

`report` reads the whole log and prints the user's patterns: their go-to clips per
folder with how often and in which ads they used them, shot lengths, captions per shot,
speeds, sound kept by folder, and how far into a line the action lands.
"""
import argparse, collections, json, os, statistics, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut_draft as C

US = 1e6
LIB = "LuxeLight BROLL Folders/"
DEFAULT_LOG = os.path.expanduser("~/Documents/LuxeLight Claude/clip-log.json")
_VENV_FF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "venv", "bin", "ffmpeg")
FFMPEG = os.environ.get("FFMPEG") or (_VENV_FF if os.path.exists(_VENV_FF) else "ffmpeg")


def materials(d):
    m = {}
    for k, v in d["materials"].items():
        if isinstance(v, list):
            for x in v:
                if isinstance(x, dict) and "id" in x:
                    m[x["id"]] = (k, x)
    return m


def luma_jump(path, src_in, src_len, fps=12):
    """Biggest brightness change inside the used part of a clip: (seconds into source range, size)."""
    if not os.path.exists(path) or src_len < 0.4:
        return None
    w, h = 16, 28
    try:
        raw = subprocess.run([FFMPEG, "-v", "error", "-ss", "%.3f" % src_in, "-t", "%.3f" % src_len, "-i", path,
                              "-vf", "fps=%d,scale=%d:%d,format=gray" % (fps, w, h), "-f", "rawvideo", "-"],
                             capture_output=True, timeout=60).stdout
    except Exception:
        return None
    n = len(raw) // (w * h)
    if n < 4:
        return None
    means = [sum(raw[i * w * h:(i + 1) * w * h]) / (w * h) for i in range(n)]
    gap = max(1, fps // 4)  # compare frames a quarter second apart
    best = max(range(n - gap), key=lambda i: abs(means[i + gap] - means[i]))
    size = means[best + gap] - means[best]
    return ((best + gap / 2) / fps, size)


def read_project(name, hook_end):
    d = json.load(open(C.draft_file(C.project_path(name))))
    mats = materials(d)
    text_tracks = [t for t in d["tracks"] if t["type"] == "text"]
    cap_track = max(text_tracks, key=lambda t: len(t["segments"])) if text_tracks else {"segments": []}
    caps = []
    for s in cap_track["segments"]:
        tr = s["target_timerange"]
        k, m = mats.get(s["material_id"], ("?", {}))
        try:
            txt = json.loads(m["content"])["text"].replace("\n", " ")
        except Exception:
            continue
        caps.append((tr["start"] / US, (tr["start"] + tr["duration"]) / US, txt))
    caps.sort()
    shots, sfx = [], []
    for t in d["tracks"]:
        for s in t["segments"]:
            tr = s["target_timerange"]
            a, b = tr["start"] / US, (tr["start"] + tr["duration"]) / US
            k, m = mats.get(s["material_id"], ("?", {}))
            if t["type"] == "video":
                path = m.get("path", "")
                if "black_bg" in path:
                    continue
                sr = s.get("source_timerange") or {}
                cl = s.get("clip") or {}
                rel = path.split(LIB)[-1] if LIB in path else path.replace(os.path.expanduser("~"), "~")
                shots.append(dict(start=round(a, 3), end=round(b, 3), path=path, clip=rel,
                                  folder=rel.split("/")[0] if LIB in path else "(one-off)",
                                  library=LIB in path, hook=a < hook_end - 0.05,
                                  src_in=round(sr.get("start", 0) / US, 3), src_len=round(sr.get("duration", 0) / US, 3),
                                  speed=round(s.get("speed", 1), 2), zoom=round(cl.get("scale", {}).get("x", 1), 2),
                                  sound=bool(s.get("volume"))))
            elif t["type"] == "audio":
                nm = m.get("name", "")
                if (b - a) < 3 and "vo" not in os.path.basename(m.get("path", "")):
                    under = [c[2] for c in caps if c[0] <= a + 0.05 < c[1]]
                    sfx.append(dict(at=round(a, 3), name=nm, level=round(s.get("volume", 1), 2),
                                    caption=under[0] if under else None))
    shots.sort(key=lambda x: x["start"])
    for sh in shots:
        sh["lines"] = [c[2] for c in caps if c[0] < sh["end"] - 0.05 and c[1] > sh["start"] + 0.05]
        j = luma_jump(sh["path"], sh["src_in"], sh["src_len"])
        if j and abs(j[1]) >= 18:
            at = sh["start"] + j[0] / max(sh["speed"], 0.01)
            cap = [c for c in caps if c[0] <= at < c[1]]
            sh["action"] = dict(at=round(at, 2), kind="gets brighter" if j[1] > 0 else "gets darker",
                                into_shot=round(at - sh["start"], 2),
                                into_line=round(at - cap[0][0], 2) if cap else None,
                                line=cap[0][2] if cap else None)
        del sh["path"]
    return dict(captions=len(caps), shots=shots, sfx=sfx)


def cmd_add(a):
    log = json.load(open(a.log)) if os.path.exists(a.log) else {"ads": {}}
    entry = read_project(a.project, a.hook_end)
    entry.update(project=a.project, hook_end=a.hook_end)
    log["ads"][a.ad] = entry
    json.dump(log, open(a.log, "w"), indent=1, ensure_ascii=False)
    for s in entry["shots"]:
        tag = "HOOK " if s["hook"] else ("     " if s["library"] else "1-off")
        act = ""
        if s.get("action"):
            x = s["action"]
            act = " | %s %.2fs into the shot, %ss into \"%s\"" % (x["kind"], x["into_shot"], x["into_line"], x["line"])
        print("%s %6.2f-%6.2f %-55s in %6.2f x%.2f%s | %s%s" % (tag, s["start"], s["end"], s["clip"][-55:], s["src_in"], s["speed"],
                                                           " sound" if s["sound"] else "", " / ".join(s["lines"]), act))
    print("logged %d shots and %d sound effects for %s in %s" % (len(entry["shots"]), len(entry["sfx"]), a.ad, a.log))


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else 0


def cmd_report(a):
    log = json.load(open(a.log))
    body = [(ad, s) for ad, e in log["ads"].items() for s in e["shots"] if not s["hook"]]
    lib = [(ad, s) for ad, s in body if s["library"]]
    print("ads: %s" % ", ".join(log["ads"]))
    print("body shots: %d (%d from the library, %d one-offs)\n" % (len(body), len(lib), len(body) - len(lib)))
    lens = [s["end"] - s["start"] for _, s in body]
    print("shot length: median %.2fs, 10%% under %.2fs, 90%% under %.2fs, longest %.2fs" % (
        statistics.median(lens), pct(lens, .1), pct(lens, .9), max(lens)))
    per = collections.Counter(len(s["lines"]) for _, s in body)
    print("captions per shot: " + ", ".join("%d: %d%%" % (k, round(100 * v / len(body))) for k, v in sorted(per.items())))
    sp = collections.Counter(s["speed"] for _, s in body if s["speed"] != 1)
    print("speed changes: " + ", ".join("%sx (%d)" % (k, v) for k, v in sorted(sp.items())))
    acts = [s["action"]["into_line"] for _, s in body if s.get("action") and s["action"]["into_line"] is not None]
    if acts:
        print("light changes inside a shot: %d, landing a median %.2fs after their caption starts (10%% %.2f, 90%% %.2f)" % (
            len(acts), statistics.median(acts), pct(acts, .1), pct(acts, .9)))
    print("\nown sound kept, by folder:")
    fs = collections.defaultdict(list)
    for _, s in body:
        fs[s["folder"]].append(s["sound"])
    for f, v in sorted(fs.items(), key=lambda x: -len(x[1])):
        print("  %-28s %d of %d" % (f, sum(v), len(v)))
    print("\ngo-to clips (library clips used in more than one ad):")
    use = collections.defaultdict(list)
    for ad, s in lib:
        use[s["clip"]].append((ad, s["src_in"], " / ".join(s["lines"])[:60]))
    for clip, v in sorted(use.items(), key=lambda x: -len({u[0] for u in x[1]})):
        if len({u[0] for u in v}) > 1:
            print("  %s" % clip)
            for ad, i, l in v:
                print("      %-12s from %6.2fs  \"%s\"" % (ad, i, l))
    print("\nsound effects:")
    for ad, e in log["ads"].items():
        for x in e["sfx"]:
            print("  %-12s %6.2fs %-40s %.2f on \"%s\"" % (ad, x["at"], x["name"][:40], x["level"], x["caption"]))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("add"); q.add_argument("project"); q.add_argument("--ad", required=True)
    q.add_argument("--hook-end", type=float, default=0.0); q.add_argument("--log", default=DEFAULT_LOG)
    r = sub.add_parser("report"); r.add_argument("--log", default=DEFAULT_LOG)
    a = p.parse_args()
    cmd_add(a) if a.cmd == "add" else cmd_report(a)


if __name__ == "__main__":
    main()
