"""Shared helpers for the Lumi Light copies' make_edit.py scripts (competitor-replication/RUNBOOK.md step 5).
Captions and shots are anchored to the voiceover's words, as in CHEAPGENIUS's make_edit.py."""
import json, os, re

H = os.path.expanduser
L = H("~/Documents/LuxeLight BROLL Folders/")
norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())


class VO:
    def __init__(self, work):
        self.work = work
        self.words = [(w["word"].strip(), w["start"], w["end"]) for s in json.load(open(work + "/inputs/tx/vo.json"))["segments"]
                      for w in s["words"]]
        self.cur = 0

    def at(self, phrase, start=None):
        """VO time of the first word of phrase, searching forward from the last match."""
        if start is not None:
            self.cur = start
        toks = [norm(t) for t in phrase.split() if norm(t)]
        for i in range(self.cur, len(self.words)):
            seq = "".join(norm(w) for w, _, _ in self.words[i:i + len(toks) + 3])
            if norm(self.words[i][0]) == toks[0] and seq.startswith("".join(toks)):
                self.cur = i + 1
                return round(self.words[i][1], 3), i
        raise SystemExit("not found after word %d: %s" % (self.cur, phrase))

    def boundary(self, phrase):
        """Midpoint of the pause before phrase (for hook and body ranges)."""
        t, i = self.at(phrase, 0)
        return round((self.words[i - 1][2] + t) / 2, 3) if i else 0.0, i


def resolve(p):
    p = p if p.startswith("/") else L + p
    if os.path.exists(p):
        return p
    d, stem = os.path.split(p)
    stem = os.path.splitext(stem)[0][:20]
    hits = [f for f in os.listdir(d) if f.startswith(stem)]
    if len(hits) != 1:
        raise SystemExit("no single match for %s: %s" % (p, hits))
    return os.path.join(d, hits[0])


def build(work, code, B, hooks, end_at, music, hook_spec, out_name="edit.json", stack=None):
    """B: [(caption, find or None, shot or None)]; shot = (clip, in, extras).
    hooks: {"A": (first words of hook A), ...} in VO order, then "body": first words of the body.
    hook_spec: {hook: dict(text=[...], caps=[(caption, find)], shots=[(find or None, clip, in, extras)])}"""
    v = VO(work)
    order = list(hooks.items())
    bounds = [v.boundary(ph)[0] for _, ph in order]
    end = round(v.words[-1][2] + 0.5, 3)
    rng = {k: [bounds[i], bounds[i + 1] if i + 1 < len(bounds) else end] for i, (k, _) in enumerate(order)}
    body = rng.pop("body")
    v.cur = v.boundary(order[-1][1])[1]
    caps, shots = [], []
    for text, find, shot in B:
        t, _ = v.at(find or text)
        caps.append(dict(t=t, text=text))
        if shot:
            clip, src, extra = shot
            shots.append(dict(t=t, clip=resolve(clip), src_in=src, **extra))
    hs, hc, ht = {}, {}, {}
    for k, spec in hook_spec.items():
        v.cur = v.boundary(hooks[k])[1]
        hc[k] = [dict(t=v.at(find or text)[0], text=text) for text, find in spec["caps"]]
        v.cur = v.boundary(hooks[k])[1]
        hs[k] = []
        for find, clip, src, extra in spec["shots"]:
            t = rng[k][0] if find is None else v.at(find)[0]
            hs[k].append(dict(t=t, clip=resolve(clip), src_in=src, **extra))
        ht[k] = spec["text"]
    e = {
        "code": code,
        "vo": work + "/inputs/vo.mp3",
        "hook_card": H("~/.video-editing-work/luxe-light/gift-for-him-vo/hook_card.mp4"),
        "max_pause": 0.10,
        "hooks": rng,
        "body": body,
        "cuts": [], "inserts": [],
        "end_box": dict(at=end_at, **({"stack": stack} if stack else {})),
        "click": H("~/Video Editing Test/Assets/Click_Mouse_Click_02.mp3"),
        "captions": caps,
        "shots": shots,
        "hook_shots": hs, "hook_captions": hc, "hook_text": ht,
        "music": music,
    }
    json.dump(e, open(os.path.join(work, out_name), "w"), indent=1, ensure_ascii=False)
    print(code, "hooks", rng, "body", body, "|", len(caps), "captions,", len(shots), "shots")
    return e
