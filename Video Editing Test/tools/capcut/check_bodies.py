"""Check that every version of an ad has the same body (B-roll, captions, voice), so only the hooks differ.

  check_bodies.py "Cheap or Genius"            every CapCut project whose name starts with this
  check_bodies.py "<project A>" "<project B>" ...

Why: CHEAPGENIUS (user, 2026-11-09). The user corrected the body in V1, and V2 was rebuilt on it, but V3's hook
was made in a project that still had the old B-roll, and that V3 was exported and uploaded. The user has seen this
happen a few times. The versions are compared from the END of the ad (the body is the same length in every version,
the hooks are not), over everything after the longest possible hook. Exit code 1 if any version differs from the
others. It never guesses which body is right: in CHEAPGENIUS the stale project was the one edited last. Pass
--ref "<project>" for the version the user corrected; otherwise all versions must simply match each other.
"""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut_draft as C

US = 1_000_000
MAX_HOOK = 8.0      # seconds; hooks are 3-7s, so everything later than this from the start is body


def project_names(args):
    if len(args) > 1:
        return args
    probe = os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft")
    return sorted(n for n in os.listdir(probe) if n.startswith(args[0]) and os.path.isdir(os.path.join(probe, n)))


def body_items(name):
    """(seconds from the end, kind, what) for every clip, caption and voice piece."""
    f = C.draft_file(C.project_path(name))
    d = json.load(open(f))
    mats = {}
    for k, v in d["materials"].items():
        if isinstance(v, list):
            for m in v:
                if isinstance(m, dict) and "id" in m:
                    mats[m["id"]] = m
    # the end is where the last clip ends, not the project's length: STOCKING V1 (2026-11-10) had music running
    # 33s past its last clip, and every item then looked out of place
    tot = max(s["target_timerange"]["start"] + s["target_timerange"]["duration"]
              for t in d["tracks"] if t["type"] == "video" for s in t["segments"])
    items = []
    for t in d["tracks"]:
        for s in t["segments"]:
            st, du = s["target_timerange"]["start"], s["target_timerange"]["duration"]
            if st >= tot:
                continue
            if t["type"] == "audio" and (du > 8 * US or (st == 0 and du >= tot - US)):
                continue                                  # music: may differ per version (CHEAPGENIUS V1-V3 all differ)
            m = mats.get(s["material_id"], {})
            if t["type"] == "video":
                what = "%s @%.2f" % (os.path.basename(m.get("path", "?")), (s.get("source_timerange") or {}).get("start", 0) / US)
            elif t["type"] == "text":
                try:
                    what = json.loads(m["content"])["text"]
                except Exception:
                    what = m.get("name", "?")
            elif t["type"] == "audio":
                what = "%s @%.2f" % (os.path.basename(m.get("path", "?")), s["source_timerange"]["start"] / US)
            else:
                continue
            items.append((round((tot - st) / US, 2), t["type"], what.replace("\n", " ")))
    return tot / US, os.path.getmtime(f), items


def compare(names, ref=None):
    info = {n: body_items(n) for n in names}
    window = min(v[0] for v in info.values()) - MAX_HOOK
    body = lambda n: frozenset(x for x in info[n][2] if x[0] <= window)
    groups = {}
    for n in names:
        groups.setdefault(body(n), []).append(n)
    print("comparing the last %.1fs of %d versions" % (window, len(names)))
    if len(groups) == 1 and (ref is None or ref in names):
        print("  OK: every version has the same body")
        return True
    base = body(ref) if ref else max(groups, key=len)
    for g, ns in groups.items():
        tag = "CORRECT BODY" if ref and g == base else ("BODY" if g == base else "DIFFERENT BODY")
        print("  %s: %s" % (tag, ", ".join(ns)))
        if g != base:
            diff = sorted((base - g) | (g - base), reverse=True)
            print("    %d items differ, first ones:" % len(diff))
            for x in diff[:6]:
                print("      %.2fs before the end, %s %s: %s" % (x[0], "missing" if x in base else "extra", x[1], x[2]))
    return False


if __name__ == "__main__":
    a = sys.argv[1:]
    ref = None
    if "--ref" in a:
        i = a.index("--ref"); ref = a[i + 1]; del a[i:i + 2]
    names = project_names(a)
    if ref and ref not in names:
        names.append(ref)
    sys.exit(0 if compare(names, ref) else 1)
