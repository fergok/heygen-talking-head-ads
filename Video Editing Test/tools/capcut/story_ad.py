#!/usr/bin/env python3
"""Build an AI-voiceover story ad from one edit file: a review MP4 and a CapCut project.

  story_ad.py <edit.json> [--hook A] [--mp4] [--capcut] [--name "<project name>"]

The edit file (see Styles/AI voiceover story/) gives the voiceover, the hook ranges,
the body range, cuts, inserts (clips that play with their own sound), captions and
shots. Caption and shot times are in the ORIGINAL voiceover's seconds; the builder
tightens pauses, removes cuts, and maps everything onto the output timeline.

The CapCut project is cloned from a template project (TEMPLATE) the way CapCut's own
Duplicate does, then its timeline is replaced. CapCut should be closed while writing.
"""
import copy
import math
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import capcut_draft as C

VENV = os.path.expanduser("~/Video Editing Test/tools/venv/bin")
FF, FP = VENV + "/ffmpeg", VENV + "/ffprobe"
TEMPLATE = "1027 (2)"            # white-box captions, one VO track, one music track
# the user's own finished GIFT4HIM v3 timeline (2026-11-06): their caption look (rulebook 11a), the
# three-box end stack, the end-box click and the sound-effect level all come from it
USER_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "gift4him_v3_user.json")
STACK = ("SHOP NOW FOR", "60-DAY GUARANTEE", "LOW STOCK")   # end stack boxes, top to bottom (style.md)
VO_VOLUME, MUSIC_VOLUME = 2.0, 0.035                          # the user's CapCut levels on GIFT4HIM v3
# Longer captions are broken into two even lines (7.8ac). Measured, not counted: "the 230-degree wide beam"
# is 24 characters but ran into the Instagram buttons on the right (user, 2026-11-06). Width of the caption
# in en.ttf at size 100: every one-line caption the user kept was <= 1184, every one they broke was >= 1234.
ONE_LINE_W = 1200
CAP_FONT = "/Applications/CapCut.app/Contents/Resources/Font/SystemFont/en.ttf"


def text_w(s):
    from PIL import ImageFont
    return ImageFont.truetype(CAP_FONT, 100).getlength(s)
CAPCUT_FONT = "/Applications/CapCut.app/Contents/Resources/Font/SystemFont/en.ttf"
W, H, FPS = 1080, 1920, 30
US = 1_000_000


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("command failed: %s\n%s" % (" ".join(cmd[:6]), r.stderr[-1500:]))
    return r


def uid():
    return str(uuid.uuid4()).upper()


_probe = {}


def probe(path):
    """duration, display width/height (rotation applied) and whether there is sound, from ffmpeg's banner."""
    if path not in _probe:
        err = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
        if not m:
            sys.exit("can't read " + path)
        dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
        v = re.search(r"Stream .*Video: .*?(\d{2,5})x(\d{2,5})", err)
        w, h = (int(v[1]), int(v[2])) if v else (0, 0)
        rot = re.search(r"rotation of (-?[\d.]+)|rotate\s*:\s*(-?\d+)", err)
        if rot and abs(round(float(rot[1] or rot[2]))) in (90, 270):
            w, h = h, w
        _probe[path] = dict(dur=dur, w=w, h=h, audio="Audio:" in err)
    return _probe[path]


# ---------------------------------------------------------------- timeline

def silences(vo, noise=-38, d=0.12):
    err = run([FF, "-i", vo, "-af", "silencedetect=noise=%ddB:d=%s" % (noise, d), "-f", "null", "-"]).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en))


def keep(rng, removals):
    """rng minus removals, as a list of (a, b)."""
    a0, b0 = rng
    out, cur = [], a0
    for a, b in sorted(removals):
        if b <= cur or a >= b0:
            continue
        if a > cur:
            out.append((cur, min(a, b0)))
        cur = max(cur, b)
    if cur < b0:
        out.append((cur, b0))
    return [(round(a, 3), round(b, 3)) for a, b in out if b - a > 0.02]


def frame_of(t):
    return int(t * FPS + 1e-6)          # round down: a caption is never late


def balance_lines(text):
    """Wider than ONE_LINE_W: two lines as even as possible, never top heavy (rulebook 7.8ac)."""
    if text_w(text) <= ONE_LINE_W or "\n" in text:
        return text
    w = text.split()
    best = min(range(1, len(w)), key=lambda i: (abs(text_w(" ".join(w[:i])) - text_w(" ".join(w[i:])))
                                              + (100 if text_w(" ".join(w[:i])) > text_w(" ".join(w[i:])) else 0)))
    return " ".join(w[:best]) + "\n" + " ".join(w[best:])


def vo_envelope(vo, hop=0.01):
    """10ms loudness of the voiceover in dB, for finding where words really start."""
    import numpy as np
    raw = subprocess.run([FF, "-v", "error", "-i", vo, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    n = int(16000 * hop)
    x = x[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((x ** 2).mean(1)) + 1e-9)


def onset_out(out_t, vo, env, back=0.05, fwd=0.20, hop=0.01):
    """Move a transcript word start (output seconds) to where the word is really heard.

    Whisper's word starts run early: in running speech it puts a word's start on the tail of the word
    before. The XMAS3HOOK build trusted them (and backed up further to the last silence), so every caption
    inside a voice piece came in 0.1-0.3s early, before the word was said (user, 2026-11-06 walkthrough).
    The user's own marks sit on the quiet dip between the two words, 0.03-0.15s after Whisper's start.
    So: inside the piece, from 0.05s before the transcript start to the end of the first word (0.20s at most),
    the frame before the voice's first 10dB jump, or failing that the quietest frame. Tested on the user's
    marks in their XMAS3HOOK V1: 30 of 32 captions within 2 frames, none early (was 11 off, up to 9 frames early).
    Lines that open a voice piece are snapped to the piece start afterwards (7.8ad), so this only decides
    captions inside a piece."""
    import numpy as np
    p = next((p for p in vo if p["start"] - 1e-6 <= out_t <= p["start"] + p["src_out"] - p["src_in"] + 1e-6), None)
    if not p:
        return out_t
    src = p["src_in"] + out_t - p["start"]
    lo = int(round(max(p["src_in"], src - back) / hop))
    hi = int(round(min(p["src_out"], src + fwd) / hop))
    if hi - lo < 2:
        return out_t
    # a word's attack: the frame before the voice jumps 10dB+ (the user's marks sit exactly there);
    # with no clear attack (a soft "a" or "as" running on), the quietest frame between the words
    # (or 15dB+ over two frames: "230" rises 8 then 9, and missing it put the caption mid-word)
    k = next((k for k in range(lo, hi) if env[k + 1] - env[k] >= 10 or env[k + 2] - env[k] >= 15), None)
    if k is None:
        k = lo + int(np.argmin(env[lo:hi]))
    return p["start"] + k * hop - p["src_in"]


ALIGN_LEAD = 0.03


def aligned_words(vo, txp):
    """Whisper's words with forced-alignment times (align_words.py), made once and cached beside the transcript."""
    out = re.sub(r"\.json$", "", txp) + ".aligned.json"
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(txp):
        env = dict(os.environ, PATH=VENV + ":" + os.environ.get("PATH", ""))
        subprocess.run([VENV + "/python", os.path.join(os.path.dirname(os.path.abspath(__file__)), "align_words.py"),
                        vo, txp, out], check=True, env=env)
    return json.load(open(out))["words"]


def source_cuts(clip, a, b, th=0.2):
    """Times (source seconds) of hard cuts inside clip[a:b]. Many B-roll files are edited videos with their own
    cuts; one landing mid-line makes the shot change before the caption does, and one in the last frames
    flashes the next scene (user, CHEAPGENIUS 2026-11-07: LeeAnn Headtorch, the closet clip, the end clip)."""
    r = subprocess.run([FF, "-v", "info", "-ss", "%.3f" % max(0, a), "-t", "%.3f" % max(0.05, b - a), "-i", clip,
                        "-vf", "scale=160:-2,select='gt(scene,%.2f)',showinfo" % th, "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    return [max(0, a) + float(m) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def speech_pieces(e, th=-40, wpad=0.06, lead=0.03, tail=0.15, join=0.15):
    """Every word, with no breaths or dead air (user, 2026-11-05: never hear an inhale or exhale).
    Keeps only sound that is loud enough AND sits on a transcribed word, so breaths go even when
    they are as loud as quiet speech. Tuned on the user's own GIFT4HIM cuts: 0.03s before the
    first sound, 0.15s after the last, sounds under 0.15s apart stay joined."""
    import numpy as np
    txp = e.get("vo_tx") or os.path.join(os.path.dirname(e["vo"]), "tx", os.path.splitext(os.path.basename(e["vo"]))[0] + ".json")
    words = [(w["start"], w["end"]) for sg in json.load(open(txp))["segments"] for w in sg.get("words", [])]
    env = vo_envelope(e["vo"])
    near = np.zeros(len(env), bool)
    for a, b in words:
        near[max(0, int((a - wpad) * 100)): int((b + wpad) * 100) + 1] = True
    sp = (env > th) & near
    # never drop sound inside a word: Whisper ended "$70." at 80.34 when "seventy dollars" ran to 80.73, and its
    # quiet end fell under th, so 0.15s was cut out of the word (user put it back by hand, DELIVERY 2026-11-09).
    # The forced-aligned word spans are kept whole, whatever their level.
    try:
        for w in aligned_words(e["vo"], txp):
            sp[max(0, int(w["start"] * 100)): int(w["end"] * 100) + 1] = True
    except Exception as ex:
        print("aligned words unavailable (%s): listen for clipped word ends" % ex)
    runs, i = [], 0
    while i < len(sp):
        if sp[i]:
            j = i
            while j < len(sp) and sp[j]:
                j += 1
            if runs and i / 100 - runs[-1][1] < join:
                runs[-1][1] = j / 100
            else:
                runs.append([i / 100, j / 100])
            i = j
        else:
            i += 1
    P = [[max(0.0, a - lead), b + tail] for a, b in runs]
    for x, y in zip(P, P[1:]):
        x[1] = min(x[1], y[0])
    return P


def tighten_pauses(e, pieces, stop=0.16, pause=0.15, lead=0.05, tail=0.10):
    """Cap the silence heard between two words (user, DELIVERY 2026-11-09: "at the end of sentences there's
    always a gap of dead air"). speech_pieces adds its tail after the last LOUD sound, and a word's fade runs
    past where it ends, so sentence ends kept 0.21-0.39s of silence; the user re-cut them by hand to a median
    0.18s (0.09-0.24) and mostly left comma pauses alone. Measured on the forced-aligned words, never Whisper
    (Whisper stretches a sentence's last word into the pause): after . ! ? at most `stop` of silence, after
    anything else at most `pause`. At least `tail` stays after the word (it never loses its fade, rule 4)
    and `lead` before the next one.
    Re-measured on the user's finished DELIVERY V1 (2026-11-10, "still a lot of gaps I had to cut out"): they left
    a median 0.16s after a sentence and 0.14s (max 0.20) at a comma, so the caps are now 0.16 and 0.15; the old
    0.26 comma cap left 0.22-0.25s where they had cut to 0.12-0.17."""
    txp = e.get("vo_tx") or os.path.join(os.path.dirname(e["vo"]), "tx", os.path.splitext(os.path.basename(e["vo"]))[0] + ".json")
    try:
        words = aligned_words(e["vo"], txp)
    except Exception as ex:          # no aligner: keep the cut as it is, but say so
        print("pauses not tightened (%s): listen for dead air at sentence ends" % ex)
        return pieces
    cuts = []
    for w, n in zip(words, words[1:]):
        a, b = w["end"], n["start"]
        if b - a <= 0:
            continue
        cap = stop if w["word"].strip().rstrip("\"')").endswith((".", "!", "?")) else pause
        heard = sum(max(0, min(b, y) - max(a, x)) for x, y in pieces)
        if heard > cap + 0.01:
            cuts.append((a + max(tail, cap - lead), b - lead))
    # a cut under 0.05s can't be heard, but it splits the phrase into a sliver piece that a caption then snaps to
    # ("Not" / "one tiny spot", DELIVERY re-run 2026-11-10)
    cuts = [c for c in cuts if c[1] - c[0] >= 0.05]
    return [p for r in pieces for p in keep(r, cuts)]


def keep_onsets(e, pieces, th=-45, rel=28, lead=0.03):
    """Never start a piece inside a word's first sound (user, STOCKING 2026-11-10: "you're cutting into the start
    of words now"). Forced-aligned starts sit up to 0.14s after the audible onset of soft openings ("one",
    "usually", "laughed"), and tighten_pauses cut to 0.05s before them, so 12 of 46 pieces clipped a word. Each
    piece start moves back to where the sound actually begins (level above `th`, walking back from the start),
    plus `lead`, never into the previous piece."""
    env = vo_envelope(e["vo"])
    out = []
    for i, (a, b) in enumerate(pieces):
        # the word's onset is judged against its own loudness: the faint breath or room tone before it
        # (-36 to -43 dB before "instead", which peaks at -9) moves on the meter but isn't heard (user, 2026-11-10)
        j = int(round(a * 100))
        peak = max(env[j:j + 30]) if j < len(env) else th
        floor = max(th, peak - rel)
        while j > 0 and env[min(j, len(env) - 1)] > floor and j > int(round(a * 100)) - 30:
            j -= 1
        na = max(0.0, j / 100 - lead) if j < int(round(a * 100)) else a
        if out:
            na = max(na, out[-1][1])
        out.append([min(na, a), b])
    return [tuple(p) for p in out]


def vo_features(path):
    """Per 10 ms: level (dB), voicing (autocorrelation peak at 70-400 Hz pitch) and share of energy above 2 kHz.
    A breath is unvoiced hiss (voicing under ~0.35, mostly above 2 kHz); speech vowels are voiced (0.6-0.8)."""
    import numpy as np
    cache = os.path.join(os.path.dirname(path), "tx", os.path.splitext(os.path.basename(path))[0] + ".feat.npy")
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(path):
        return np.load(cache)
    import imageio_ffmpeg
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    sr, hop, win = 16000, 160, 480
    nf = max(0, (len(x) - win) // hop)
    fr = np.fft.rfftfreq(win, 1 / sr)
    hann = np.hanning(win)
    out = np.zeros((3, nf), np.float32)
    lo, hi = int(sr / 400), int(sr / 70)
    for f in range(nf):
        seg = x[f * hop:f * hop + win]
        out[0, f] = 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9)
        s2 = seg - seg.mean()
        ac = np.correlate(s2, s2, "full")[win - 1:]
        out[1, f] = ac[lo:hi].max() / ac[0] if ac[0] > 0 else 0
        sp = np.abs(np.fft.rfft(s2 * hann)) ** 2
        out[2, f] = sp[fr > 2000].sum() / (sp.sum() + 1e-12)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    np.save(cache, out)
    return out


FRIC_START = ("s", "f", "sh", "th", "h", "ch", "c", "z", "x")
STOP_START = ("p", "t", "k", "b", "d", "g", "q")


def run_in(db, on, floor=-45):
    """First frame of a word's rising onset: walk back from the frame where it gets loud while the level keeps
    rising and stays above `floor` (the "s" of "so", the "a" of "and")."""
    f = on
    while f > 0 and db[f - 1] > floor and db[f - 1] < db[f]:
        f -= 1
    return f


def cut_breaths(e, pieces, rngs, tail_db=-42, hump_db=-46, rise=4, min_hump=0.15, voiced=0.35, onset=-30, link=0.06):
    """No inhale or exhale at a pause, ever (user, 2026-11-05, again STOCKING 2026-11-10: "how many times do I
    need to tell you"). A breath is its own burst of sound: the word fades, the level dips, then rises again for
    0.2s or so of unvoiced hiss that runs straight into the next word. In STOCKING V1 the user cut exactly three,
    after "laughed," "once," and "light," (humps of 0.17-0.28s at -36 to -45 dB after a dip to -45/-51).
    What is NOT a breath, and the user kept: a word's own fading tail ("face.", "case.", "since.": the "s" runs
    on 0.15-0.3s and falls into silence), and a stop's release ("dark,", "dark.": a burst of about 0.12s after a
    short dip, then silence). The first version of this cut every unvoiced stretch at a comma or full stop and
    took 3.6s of word endings the user kept (2026-11-10)."""
    txp = e.get("vo_tx") or os.path.join(os.path.dirname(e["vo"]), "tx", os.path.splitext(os.path.basename(e["vo"]))[0] + ".json")
    words = aligned_words(e["vo"], txp)
    F = vo_features(e["vo"])
    db, vo = F[0], F[1]
    n = len(db)

    def onset_of(w, lo):
        z0 = max(lo, int((w["start"] - 0.25) * 100))
        return next((f for f in range(z0, min(n, int(w["end"] * 100) + 5))
                     if db[f] > onset or (vo[f] >= 0.5 and db[f] > -40)), None)

    cuts, found = [], []
    for r0, r1 in rngs:
        ws = [w for w in words if r0 - 0.05 <= w["start"] < r1]
        for k in range(len(ws) - 1):
            w, nw = ws[k], ws[k + 1]
            if nw["start"] - w["end"] < 0.12:
                continue
            a = int((w["end"] - 0.03) * 100)
            on = onset_of(nw, a + 1)
            if on is None:
                continue
            ri = run_in(db, on)
            t = next((f for f in range(a, ri) if db[f] < tail_db), None)       # the word has faded
            if t is None:
                continue
            dip = min(range(t, min(ri, t + 9)), key=lambda f: db[f])
            thr = max(db[dip] + rise, hump_db)
            # the hump: the stretch after the dip that is back above the line, allowing one-frame drops
            hs = next((f for f in range(dip + 1, ri) if db[f] > thr), None)
            if hs is None:
                continue
            he, f = hs, hs
            while f < ri:
                if db[f] > thr or (f + 1 < ri and db[f + 1] > thr):
                    he = f
                    f += 1
                else:
                    break
            length = (he - hs + 1) / 100
            if length < min_hump or vo[hs:he + 1].mean() >= voiced or (ri - he - 1) / 100 > link:
                continue
            # mid-phrase, after a word ending in a stop, a short silent closure and then hiss is the next word's own
            # "s", "f" or "sh", not a breath: "makes it | so much" had a 0.04s closure and 0.2s of "s" that the
            # aligner put 0.17s late (WONXMAS 2026-11-18), the same trap as "Alex" cut to "Al" (ALEXXMAS). A breath
            # sits at a pause: after punctuation, or after at least 0.08s of quiet.
            if w["word"].strip()[-1:] not in ",.!?;:" and (hs - t) / 100 < 0.08:
                print("  kept (a consonant, not a breath): %s|%s %.2f-%.2f" % (w["word"], nw["word"], dip / 100, ri / 100 - 0.01))
                continue
            cuts.append((dip / 100, ri / 100 - 0.01))
            found.append("%s|%s %.2f-%.2f" % (w["word"], nw["word"], dip / 100, ri / 100 - 0.01))
        if ws:     # the first word of a range: no breath before it
            on = onset_of(ws[0], max(0, int((r0 - 0.3) * 100)))
            if on is not None:
                cuts.append((max(0.0, r0 - 0.05), run_in(db, on) / 100 - 0.02))
    if found:
        print("  breaths cut: " + "; ".join(found))
    out = [p for r in pieces for p in keep(r, cuts)]
    return [p for p in out if p[1] - p[0] >= 0.05]


def sound_pieces(e, rngs, floor=-45, onset_floor=-50, rel=28, lead=0.02, tail=0.03, min_gap=0.04, look=0.3, short=0.6):
    """Voice pieces cut to the sound itself, the way the user cuts by hand (STOCKING V1, 2026-11-10).
    Their cuts: a word ends about 0.03s after its sound falls below about -45 dB ("it." fades at 17.33, they cut
    at 17.37; "Year's." 22.48 -> 22.50); a word starts right where its sound begins ("and" 20.98 -> 20.97); and
    any silent dip between two words goes, even 0.04s ("way ... and", 24.39-24.43). Word timings from the aligner
    are only used to find each word: its audible span is read from the level, against the word's own peak, so a
    faint breath or room tone before or after it (-36 to -43 dB before "instead", peak -9) is not kept, and a soft
    opening ("one", "usually") is not clipped. Words within `min_gap` of each other stay joined."""
    txp = e.get("vo_tx") or os.path.join(os.path.dirname(e["vo"]), "tx", os.path.splitext(os.path.basename(e["vo"]))[0] + ".json")
    words = aligned_words(e["vo"], txp)
    env = vo_envelope(e["vo"])
    n = len(env)
    # every word plays whole (user, FAKECHECK 2026-11-11: "let them say the word properly"). In their own cut of
    # STYLE 3 they left 36 of my 40 pieces alone and moved four: "free" and "50%" start 0.08-0.10s earlier, on the
    # faint "fff" before the loud part (-57 to -64 dB, room silence is -70), and "pink", "orange", "free" end
    # 0.06-0.07s later, where the fade reaches silence (-63), not where it passes -45. So a soft opening and a
    # fading tail are followed down to 8 dB above the recording's own silence; a noisy recording keeps the old levels.
    # The longer tail is only for short pieces (under `short` seconds: list words like "pink", "orange", "free"):
    # on full sentences the user left the -45 dB ends as they were, and the longer tail there added 1.9s of air.
    import numpy as np
    quiet_db = float(np.percentile(env, 5))
    onset_floor = max(-66.0, min(onset_floor, quiet_db + 8))
    tail_floor = max(-66.0, min(floor, quiet_db + 8))

    def span(w, prev_end, next_start):
        """A word's audible span. Start: walk back from the loud part while the level stays above `floor`
        (-45 dB, where the user cuts), but keep at most 0.08s that is quieter than the word's peak - `rel`: a soft
        "f", "th" or "h" ("five", "phone", "this", "he") is kept, a long breath before the word is not. End: walk on
        while above `floor`, through a stop's closure of up to 0.05s to its release ("dark.", "stock,", "down."),
        never into the next word. A click 0.08s after "card," is not a release, and goes (user cut it too)."""
        a, b = int(round(w["start"] * 100)), int(round(w["end"] * 100))
        a, b = max(0, min(a, n - 1)), max(0, min(max(b, a + 1), n))
        peak = max(env[a:b]) if b > a else env[a]
        loud = max(floor, peak - rel)
        lo = max(0, int(round((prev_end + 0.02) * 100)), a - int(look * 100))
        hi = min(n, int(round((next_start - 0.03) * 100)), b + int(look * 100))
        # the loud part of the word: walk back from its aligned start while it stays loud, or forward to it
        # when the aligned start sits early. Never search back past the start: that found the tail of the word
        # before ("way" into "and"), and the user's 0.05s cut between them was lost
        i = a
        if env[i] > loud:
            while i > lo and env[i - 1] > loud:
                i -= 1
        else:
            i = next((k for k in range(a, b) if env[k] > loud), a)
        quiet = 0
        # a soft opening ("f" in "five", 86.15-86.21 at -44 to -46 dB) runs down to `onset_floor`
        while i > lo and env[i - 1] > onset_floor:
            if env[i - 1] <= loud:
                quiet += 1
                if quiet > 15:
                    break
            i -= 1
        j = b
        while j < hi:
            if env[j] > floor:
                j += 1
                continue
            k = next((k for k in range(j + 1, min(hi, j + 6)) if env[k] > floor), None)
            if k is None:
                break
            j = k
        # the aligned end can sit after the sound has stopped ("flashlight." left 0.07s of silence): walk back
        while j > i + 1 and env[j - 1] <= floor:
            j -= 1
        k = j                                 # the fade after the word, down to silence (0.12s at most)
        while k < min(hi, j + 12) and env[k] > tail_floor and env[k] <= env[k - 1] + 3:
            k += 1
        return i / 100, j / 100, k / 100

    out = []
    for r0, r1 in rngs:
        ws = [w for w in words if r0 - 0.05 <= w["start"] < r1]
        if not ws:
            continue
        idx = {id(w): k for k, w in enumerate(words)}
        sp = []
        for w in ws:
            k = idx[id(w)]
            pe = words[k - 1]["end"] if k else -1.0
            ns = words[k + 1]["start"] if k + 1 < len(words) else 1e9
            sp.append(span(w, pe, ns))
        for k in range(1, len(sp)):          # keep spans in order, never overlapping
            sp[k] = (max(sp[k][0], sp[k - 1][0]), max(sp[k][1], sp[k - 1][0]), max(sp[k][2], sp[k - 1][0]))

        def close(c):
            end = c[2] if c[1] - c[0] < short else c[1]
            out.append((max(0.0, c[0] - lead), end + tail))
        cur = list(sp[0])
        for a, b, full in sp[1:]:
            if a - cur[1] >= min_gap:
                close(cur)
                cur = [a, b, full]
            else:
                cur[1], cur[2] = max(cur[1], b), max(cur[2], full)
        close(cur)
    for x in range(1, len(out)):             # padding never overlaps the next piece
        if out[x][0] < out[x - 1][1]:
            mid = (out[x - 1][1] - tail + out[x][0] + lead) / 2
            out[x - 1] = (out[x - 1][0], mid)
            out[x] = (mid, out[x][1])
    return out


TALK_ZOOMS = (1.0, 1.12)


def expand_talk(shots, vo, min_new=0.4):
    """HeyGen talking-head shots ("talk": true, Styles/HeyGen talking head, 2026-11-24). The character video was
    rendered on the whole voiceover, so its lips match the VO at the same second. The builder cuts pauses out of
    the voice, so a talk shot is split at every voice piece and each part plays the character from that piece's
    own source second: the lips stay in sync, and each pause cut becomes a jump cut. Each jump gets the next
    framing in TALK_ZOOMS (wide, then punched in; rulebook 5.6), except a part under min_new seconds, which keeps
    the framing before it so a short word doesn't flash a new zoom."""
    out, k, last_zoom = [], 0, None
    for sh in shots:
        if not sh.get("talk"):
            out.append(sh)
            continue
        for p in vo:
            pf0 = int(round(p["start"] * FPS))
            pf1 = int(round((p["start"] + p["src_out"] - p["src_in"]) * FPS))
            s0, s1 = max(sh["f0"], pf0), min(sh["f1"], pf1)
            if s1 <= s0:
                continue
            if last_zoom is None or (s1 - s0) / FPS >= min_new:
                last_zoom = TALK_ZOOMS[k % len(TALK_ZOOMS)]
                k += 1
            out.append(dict(sh, f0=s0, f1=s1, start=s0 / FPS, end=s1 / FPS, speed=1, mute=True,
                            src_in=p["src_in"] + (s0 / FPS - p["start"]), zoom=last_zoom * sh.get("zoom", 1)))
        # frames between the last piece and the shot end (the ad's last tick): hold the final part
        if out and out[-1].get("talk") and out[-1]["f1"] < sh["f1"]:
            out[-1] = dict(out[-1], f1=sh["f1"], end=sh["f1"] / FPS)
    return out


def compile_timeline(e, hook):
    hook_rngs = e["hooks"][hook]
    if not isinstance(hook_rngs[0], (list, tuple)):
        hook_rngs = [hook_rngs]           # a hook can also be several VO ranges played in order
    hook_rng = hook_rngs[-1]
    cuts = [tuple(c) for c in e.get("cuts", [])]
    speech = speech_pieces(e)
    gaps = [(a[1], b[0]) for a, b in zip(speech, speech[1:]) if b[0] > a[1]]
    removals = cuts + gaps + [(0, speech[0][0]), (speech[-1][1], 1e9)]
    # a hook or body range never ends inside its last word (rule 4; CHEAPGENIUS V2 cut "$17." at 11.9 when it
    # ran to 12.12): the end moves to the aligned word end + 0.10s, stopping 0.03s before the next word
    try:
        _aw = aligned_words(e["vo"], e.get("vo_tx") or os.path.join(os.path.dirname(e["vo"]), "tx",
                                                                     os.path.splitext(os.path.basename(e["vo"]))[0] + ".json"))
    except Exception:
        _aw = []

    def finish(r):
        a, b = r
        ins = [w for w in _aw if a - 0.05 <= w["start"] < b]
        if ins and ins[-1]["end"] > b - 0.02:
            nxt = [w["start"] for w in _aw if w["start"] > ins[-1]["start"] + 1e-3]
            nb = min(ins[-1]["end"] + 0.10, (nxt[0] - 0.03) if nxt else 1e9, b + 1.0)
            b = max(b, nb)
        return (a, b)
    if e.get("trim", "sound") == "sound":
        # cut to the sound itself (sound_pieces): replaces the breath cutter, pause caps and onset fix below,
        # which together still left faint air after words and started some words late (user, 2026-11-10)
        rngs = list(hook_rngs) + [e["body"]]
        pieces = [p for p in sound_pieces(e, rngs) for p in keep(p, cuts)]
        pieces = cut_breaths(e, pieces, rngs)
        if not e.get("phrase_cuts"):
            # the voice is only cut where it pauses for punctuation (user, FAKECHECK 2026-11-11): cutting between
            # "60" and "day" and "guarantee" made it sound clippy. A cut whose last word before it has no comma or
            # full stop is undone, and the two pieces play as one, small gap included. A real pause inside a
            # phrase (0.25s or more of removed air) is still cut.
            merged, undone = [], 0
            for p in pieces:
                if merged:
                    q = merged[-1]
                    before = [w for w in _aw if (w["start"] + w["end"]) / 2 < q[1]]
                    same = any(r[0] - 0.4 <= q[0] and p[1] <= r[1] + 1.2 for r in rngs)
                    cut_here = any(q[1] - 0.02 <= c[0] and c[1] <= p[0] + 0.02 for c in cuts)
                    if (before and before[-1]["word"].strip()[-1:] not in ".,?!;:" and same and not cut_here
                            and p[0] - q[1] < 0.25):
                        merged[-1] = (q[0], p[1]); undone += 1
                        continue
                merged.append(tuple(p))
            if undone:
                print("  joined %d voice cuts that fell inside a phrase" % undone)
            pieces = merged
        # let the voice breathe at each cut (user, FAKECHECK 2026-11-11): "pink, orange" played back to back with
        # no pause, and words were starting and ending too tight. Keep a short beat of the voice's own pause at
        # every cut, most of it after the word so its tail rings out, the rest before the next word so its soft
        # opening ("fff" in "free") is never clipped. Never more than the pause that was there.
        # Measured on the user's own cut of STYLE 3 the same day: they add no pause at all, only whole words
        # (sound_pieces now does that), and the 0.10/0.07 beat made the ad 4s longer than theirs. So the beat is
        # off unless an edit asks for one with "pause": {"stop": .., "comma": ..}.
        beat = dict(dict(stop=0.0, comma=0.0), **e.get("pause", {}))
        out = [tuple(pieces[0])] if pieces else []
        for p in pieces[1:]:
            q = out[-1]
            g = p[0] - q[1]
            same = any(r[0] - 0.4 <= q[0] and p[1] <= r[1] + 1.2 for r in rngs)
            cut_here = any(q[1] - 0.02 <= c[0] and c[1] <= p[0] + 0.02 for c in cuts)
            if g > 0 and same and not cut_here and max(beat.values()) > 0:
                before = [w for w in _aw if (w["start"] + w["end"]) / 2 < q[1]]
                last = before[-1]["word"].strip()[-1:] if before else ""
                k = min(g, beat["stop"] if last in ".?!" else beat["comma"])
                if k >= g - 1e-6:                      # the whole pause is kept: no cut here at all
                    out[-1] = (q[0], p[1])
                    continue
                out[-1] = (q[0], q[1] + k * 0.6)
                p = (p[0] - k * 0.4, p[1])
            out.append(tuple(p))
        pieces = out
    else:
        pieces = [p for r in hook_rngs for p in keep(finish(r), removals)] + keep(finish(e["body"]), removals)
        pieces = tighten_pauses(e, pieces)
        pieces = keep_onsets(e, pieces)
    # a range edge that lands in the tail of a word leaves a sliver (0.07s, 0.10s in XMAS3HOOK) that
    # plays as a click or half a breath; the user deleted both by hand (2026-11-06)
    # ...but a short piece that holds a whole spoken word is a word, not a sliver: "the" in "with the free
    # case" (FAKECHECK 2026-11-11) is a 0.06s burst with silence either side, and dropping it lost the word
    _txp = e.get("vo_tx") or os.path.join(os.path.dirname(e["vo"]), "tx", os.path.splitext(os.path.basename(e["vo"]))[0] + ".json")
    _mids = [(w["start"] + w["end"]) / 2 for w in aligned_words(e["vo"], _txp)] if os.path.exists(_txp) else []
    short_words = [p for p in pieces if p[1] - p[0] < 0.15 and any(p[0] - 0.03 <= m <= p[1] + 0.03 for m in _mids)]
    for p in short_words:
        print("  kept a short word: %.2f-%.2f" % p)
    pieces = [p for p in pieces if p[1] - p[0] >= 0.15 or p in short_words]
    if e.get("vo_pieces", {}).get(hook):
        # the user's own voiceover cuts, read from their CapCut edit: use them exactly
        pieces = [tuple(p) for p in e["vo_pieces"][hook]]
    inserts = sorted(e.get("inserts", []), key=lambda i: i["at"])

    # lay pieces and inserts end to end, each piece starting on a whole frame, so caption, shot and
    # voice piece can share one tick (rulebook 7.8ad)
    vo, ins, t = [], [], 0.0
    hook_end = None
    for i, (a, b) in enumerate(pieces):
        nxt_a = pieces[i + 1][0] if i + 1 < len(pieces) else 1e9
        # CapCut moves a voice piece's start up to its next whole frame when the user saves (17.57 became 17.60 in
        # STYLE 3), which shaves up to 0.03s off the front of the word. Start on the nearest whole frame, so there
        # is nothing for it to move: that shifts a start by 0.017s at most, inside the 0.02s lead before the word.
        # (Rounding down instead added a frame of air at every cut, 1.3s over the ad.)
        a0 = round(a * FPS) / FPS
        if not vo or a0 >= vo[-1]["src_out"] - 1e-6 or a < vo[-1]["src_in"]:
            a = a0
        up = a + max(1, math.ceil((b - a) * FPS - 1e-6)) / FPS     # round up: a whole frame never cuts a word tail
        b = up if up <= nxt_a + 1e-6 else a + max(1, math.floor((nxt_a - a) * FPS + 1e-6)) / FPS   # ...nor replays the next piece
        vo.append(dict(src_in=a, src_out=b, start=t))
        t += b - a
        if b <= hook_rng[1] + 1e-6 and (i + 1 == len(pieces) or pieces[i + 1][0] >= hook_rng[1]):
            hook_end = t
        nxt = pieces[i + 1][0] if i + 1 < len(pieces) else 1e9
        for x in inserts:
            if b <= x["at"] < nxt:
                d = round((x["out"] - x["in"]) * FPS) / FPS
                ins.append(dict(x, start=t, end=t + d))
                t += d
    total_speech = t

    def omap(ts):
        """original VO second -> output second (inside a removed span: the next kept piece)."""
        for p in vo:
            if p["src_in"] - 1e-6 <= ts <= p["src_out"] + 1e-6:
                return p["start"] + ts - p["src_in"]
            if ts < p["src_in"]:
                return p["start"]
        return total_speech

    # the ad ends on the voiceover's last sound: B-roll, music and the end box stop with it (user, 2026-11-07:
    # "all of this ends when the script voiceover stops speaking"); the last piece already carries 0.15s of tail
    tail = e.get("tail", 0.0)
    total = total_speech + tail

    # Every caption starts on the frame its first word starts, read from the audio (rulebook 7.8aa).
    # No captions under the hook slot (3.2); the first caption appears the moment it ends (7.7).
    env = vo_envelope(e["vo"])
    body_caps = [c for c in e["captions"] if e["body"][0] - 0.05 <= c["t"] < e["body"][1]]
    piece_f = [int(round(p["start"] * FPS)) for p in vo]
    events, prev = [], -6                      # the first caption may start on frame 0
    txp = e.get("vo_tx") or os.path.join(os.path.dirname(e["vo"]), "tx", os.path.splitext(os.path.basename(e["vo"]))[0] + ".json")
    aligned = aligned_words(e["vo"], txp)
    for c in body_caps:
        # the line's first word, re-timed by forced alignment (rulebook 7.8aa). Whisper's own start is
        # 100-300 ms off at many boundaries; on the user's CHEAPGENIUS marks (2026-11-07) the aligned start
        # less 0.03s put 21 of 24 mid-piece captions within a frame of theirs (Whisper + attack: 13 of 24)
        w = min(aligned, key=lambda w: abs(w["w_start"] - c["t"]))
        f = frame_of(omap(w["start"] - ALIGN_LEAD))
        # a line that opens a voice piece starts on the piece's own tick (7.8ad): the word onset sits
        # a frame or two in, and a transcript start in the last piece's tail would land early
        # ...but only the piece that holds this line's own first word (by the word's middle; in a gap, the next
        # piece), never the next word's piece: "black" snapped onto "pink" said 0.5s later (crafters BF, 2026-11-19)
        mid = (w["start"] + w["end"]) / 2
        own = next((k for k, p in enumerate(vo) if mid < p["src_out"]), len(vo) - 1)
        own_f = piece_f[own] if f - 4 <= piece_f[own] <= f + 12 else None
        if own_f is not None:
            f = own_f
        f = max(f, prev + 6)                       # never shorter than 0.2s
        events.append(dict(c, f=f, own_f=own_f))
        prev = f
    for x in ins:
        x["f"] = frame_of(x["start"])
        events.append(dict(text=x["caption"], t=None, f=x["f"], insert=True))
    events.sort(key=lambda c: c["f"])
    total_f = int(round(total * FPS))
    box = e.get("end_box")
    box_f = next((c["f"] for c in events if box and c["text"] == box["at"]), total_f)
    caps = []
    for i, c in enumerate(events):
        if c["f"] >= box_f:
            break
        end_f = min(events[i + 1]["f"] if i + 1 < len(events) else total_f, box_f)   # hold until the next one: no blanks (7.7)
        # no punctuation at line ends except "?" (7.5): the user stripped every trailing comma by hand (DELIVERY 2026-11-09)
        txt = "\n".join(re.sub(r"[,.;:!]+$", "", ln.rstrip()) for ln in c["text"].split("\n"))
        caps.append(dict(text=txt, f0=c["f"], f1=end_f, start=c["f"] / FPS, end=end_f / FPS, own_f=c.get("own_f")))
    # flag a line that opens its own piece but missed that piece's tick
    off = [(c["text"], c["f0"], c["own_f"]) for c in caps if c["own_f"] is not None and c["f0"] != c["own_f"]][:20]
    for c in caps:
        c.pop("own_f", None)
    if off:
        sys.exit("caption not on its voice piece's tick (7.8ad):\n  " +
                 "\n  ".join("%r at %.2fs, piece starts %.2fs" % (t, a / FPS, p / FPS) for t, a, p in off))
    hook_f = events[0]["f"]
    hook_end = hook_f / FPS

    # B-roll starts on the same frame as the caption it belongs to (7.8b)
    cap_f = {c["t"]: c["f"] for c in events if c.get("t") is not None}
    shots = [dict(clip=e["hook_card"], src_in=0, speed=1, zoom=1, x=0, y=0, mute=True, f0=0, kind="hook")]
    for sh in e["shots"]:
        if sh["t"] in cap_f:
            sh = dict(sh, f0=cap_f[sh["t"]])
            if "zoom" not in sh and os.path.basename(sh["clip"]).startswith("hf_"):
                sh["zoom"] = 1.03                  # AI clips can have thin black edge bars (6.29)
            shots.append(sh)
    for x in ins:
        shots.append(dict(clip=x["clip"], src_in=x["in"], speed=1, zoom=x.get("zoom", 1), x=x.get("x", 0), y=x.get("y", 0),
                          mute=False, volume=x.get("volume", 1.0), f0=x["f"], kind="insert"))
    shots.sort(key=lambda s: s["f0"])
    shots[1]["f0"] = hook_f
    for i, sh in enumerate(shots):
        sh["f1"] = shots[i + 1]["f0"] if i + 1 < len(shots) else total_f
        sh["start"], sh["end"] = sh["f0"] / FPS, sh["f1"] / FPS
    shots = [sh for sh in shots if sh["f1"] > sh["f0"]]
    for sh in shots:
        need = (sh["end"] - sh["start"]) * sh.get("speed", 1)
        info = probe(sh["clip"])
        if sh["src_in"] + need > info["dur"] - 0.04:
            sh["warn"] = "clip too short: wanted %.2f-%.2f of %.2fs" % (sh["src_in"], sh["src_in"] + need, info["dur"])
            sh["src_in"] = max(0, info["dur"] - 0.04 - need)
            if sh["src_in"] == 0 and need > info["dur"]:
                sh["speed"] = round(info["dur"] / (sh["end"] - sh["start"]) * 0.98, 3)
        if sh.get("kind") in ("hook", "insert") or sh.get("talk"):
            continue
        # a shot shows one scene: the cut is ours, on the line change, never the source file's own (7.8b)
        need = (sh["end"] - sh["start"]) * sh.get("speed", 1)
        # Warn only: at a threshold low enough to catch LeeAnn's 0.24 cut, the light switching on scores as a cut
        # too (IMG_2548, 4918ACAE), and that is the shot we want. Look at the flagged frames and re-pick.
        cuts = [c for c in source_cuts(sh["clip"], sh["src_in"], sh["src_in"] + need, th=0.2) if c > sh["src_in"] + 0.02]
        if cuts:
            sh["warn"] = (sh.get("warn", "") + "; " if sh.get("warn") else "") + \
                "possible source cut at %s inside %.2f-%.2f (or the light switching): check the frames" % (
                    ", ".join("%.2f" % c for c in cuts), sh["src_in"], sh["src_in"] + need)
    end_box = dict(box, f0=box_f, start=box_f / FPS) if box and box_f < total_f else None
    if end_box and box.get("seq"):
        # end boxes that follow the close, one step per offer line as it's spoken (rulebook 10, user DELIVERY
        # 2026-11-09): each step's boxes show from its line until the next step, the last until the end
        seq = []
        for st in box["seq"]:
            f = next((c["f"] for c in events if c["text"] == st["at"]), None)
            if f is None:
                sys.exit("end box step not found among the captions: %r" % st["at"])
            seq.append(dict(st, f0=f, start=f / FPS))
        for a, b in zip(seq, seq[1:] + [dict(start=total_f / FPS)]):
            a["end"] = b["start"]
        end_box["seq"] = seq
    HT.check_spans([(c["f0"], c["f1"], c["text"]) for c in caps], [sh["f0"] for sh in shots[1:]],
                   first=hook_f, last=box_f)
    shots = expand_talk(shots, vo)
    total = total_f / FPS
    return dict(vo=vo, inserts=ins, captions=caps, shots=shots, hook_end=hook_end, total=total, end_box=end_box)


# ---------------------------------------------------------------- house text

sys.path.insert(0, os.path.expanduser("~/Video Editing Test/tools/captions"))
import house_captions as HT         # the one caption engine for every style (rulebook 7, 11a)


def text_frames(tl, work):
    """(first frame, last frame + 1, png) for every caption and the end box, on exact frames."""
    os.makedirs(work, exist_ok=True)
    sched = []
    for k, c in enumerate(tl["captions"]):
        pth = os.path.join(work, "cap%03d.png" % k)
        if tl.get("caption_style") == "lumi":      # a Lumi copy keeps their look and line breaks (Lumi RUNBOOK rule 4)
            HT.caption_img_lumi(c["text"], HT.lumi_look(tl)).save(pth, compress_level=1)
        else:
            HT.caption_img(balance_lines(c["text"])).save(pth, compress_level=1)
        sched.append((c["f0"], c["f1"], pth))
    b = tl.get("end_box")
    if b and b.get("stack") == []:            # end with no boxes: captions just stop (a copy whose end card is in the footage)
        b = None
    if b:
        # the end stack, at the user's CapCut positions (style.md). Drawn in the house box font:
        # the CapCut project's Montserrat Bold isn't matched here yet
        texts = b.get("stack") or ["SHOP NOW FOR\nUP TO 50% OFF \U0001F381", "60-DAY GUARANTEE ✅", "LOW STOCK ⚠️"]
        box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for txt, cy, red in zip(texts, (0.41, -0.30, -0.46), (False, False, True)):
            lines = txt.split("\n")
            hgt = HT.BOX_H2 if len(lines) > 1 else HT.BOX_H1
            spec = dict(lines=lines, color=HT.RED if red else HT.WHITE, ink=HT.WHITE if red else (0, 0, 0, 255),
                        top=round(H / 2 - cy * H / 2 - hgt / 2), paren=None)
            box.alpha_composite(HT.box_layer(spec))
        ys = H / 2
        f = b["f0"]
        total_f = int(round(tl["total"] * FPS))
        for k in HT.BOUNCE:
            m = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sc = box.resize((round(W * k), round(H * k)), Image.LANCZOS)
            m.alpha_composite(sc.crop((max(0, round(540 * k - 540)), max(0, round(ys * k - ys)), sc.width, sc.height)),
                              (max(0, round(540 - 540 * k)), max(0, round(ys - ys * k))))
            pth = os.path.join(work, "box%02d.png" % len(sched))
            m.save(pth, compress_level=1)
            sched.append((f, f + 1, pth))
            f += 1
        pth = os.path.join(work, "box.png")
        box.save(pth, compress_level=1)
        sched.append((f, total_f, pth))
    return sched


# ---------------------------------------------------------------- MP4

def render_mp4(e, tl, out, work, reuse=False):
    os.makedirs(work, exist_ok=True)
    segs = []
    video = os.path.join(work, "video.mp4")
    audio = os.path.join(work, "audio.wav")
    shots = [] if reuse and os.path.exists(video) else tl["shots"]
    for i, s in enumerate(shots):
        info = probe(s["clip"])
        dur = s["end"] - s["start"]
        sp = s.get("speed", 1)
        cover = max(W / info["w"], H / info["h"]) * s.get("zoom", 1)
        sw, sh = int(info["w"] * cover / 2) * 2, int(info["h"] * cover / 2) * 2
        ox = int((W - sw) / 2 + s.get("x", 0) * W / 2)
        oy = int((H - sh) / 2 - s.get("y", 0) * H / 2)
        f = os.path.join(work, "shot%03d.mp4" % i)
        vf = ("[0:v]setpts=(PTS-STARTPTS)/%s,fps=%d,scale=%d:%d,setsar=1[v];color=black:s=%dx%d:r=%d[bg];"
              "[bg][v]overlay=%d:%d:shortest=1,eq=contrast=1.03:saturation=SAT,tpad=stop_mode=clone:stop_duration=2,format=yuv420p,setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709[o]"
              % (sp, FPS, sw, sh, W, H, FPS, ox, oy)).replace("SAT", "0" if s.get("bw") else "1.05").replace("setsar=1[v]", "setsar=1%s[v]" % (",boxblur=%d:2" % s["blur"] if s.get("blur") else ""))
        run([FF, "-v", "error", "-y", "-ss", "%.3f" % s["src_in"], "-t", "%.3f" % (dur * sp + 0.3), "-i", s["clip"],
             "-filter_complex", vf, "-map", "[o]", "-frames:v", str(s["f1"] - s["f0"]), "-an", "-c:v", "libx264",
             "-preset", "veryfast", "-crf", "18", f])
        segs.append(f)
    if shots:
        lst = os.path.join(work, "shots.txt")
        open(lst, "w").write("".join("file '%s'\n" % f for f in segs))
        # re-time by frame number, so frame n of the picture is frame n of the text layer
        run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-vf", "setpts=N/(%d*TB)" % FPS, "-r", str(FPS),
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "12", video])
        got = int(re.findall(r"frame=\s*(\d+)", run([FF, "-i", video, "-map", "0:v", "-f", "null", "-"]).stderr)[-1])
        want = sum(s["f1"] - s["f0"] for s in shots)
        if got != want:
            sys.exit("picture has %d frames, timeline has %d" % (got, want))
        for f in segs:
            os.remove(f)

    # audio: VO pieces, insert sound, music bed
    inputs, parts, n = ["-i", e["vo"]], [], 1
    for j, p in enumerate(tl["vo"]):
        parts.append("[0:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,afade=t=in:d=0.008,afade=t=out:st=%.3f:d=0.008,adelay=%d:all=1[v%d]"
                     % (p["src_in"], p["src_out"], p["src_out"] - p["src_in"] - 0.008, p["start"] * 1000, j))
    labels = ["[v%d]" % j for j in range(len(tl["vo"]))]
    parts.append("%samix=inputs=%d:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[vo]" % ("".join(labels), len(labels)))
    mix = ["[vo]"]
    for x in tl["inserts"]:
        inputs += ["-i", x["clip"]]
        parts.append("[%d:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,loudnorm=I=-17:TP=-2,volume=%s,adelay=%d:all=1[i%d]"
                     % (n, x["in"], x["out"], x.get("volume", 1.0), x["start"] * 1000, n))
        mix.append("[i%d]" % n)
        n += 1
    if tl.get("end_box") and tl["end_box"].get("seq"):
        steps = tl["end_box"]["seq"]
        for k, st in enumerate(steps):      # each step its own sound, as in write_capcut (standards 10)
            sname, vol = (SFX_END[2] if k == len(steps) - 1 else SFX_END[0] if k == 0 else SFX_END[1])
            inputs += ["-i", os.path.join(SFX_DIR, sname)]
            parts.append("[%d:a]volume=%.2f,adelay=%d:all=1[ck%d]" % (n, vol, int(st["start"] * 1000), k))
            mix.append("[ck%d]" % k)
            n += 1
    elif tl.get("end_box") and e.get("click"):
        inputs += ["-i", e["click"]]
        d = int((tl["end_box"]["start"] + HT.CLICK_DELAY) * 1000)
        parts.append("[%d:a]volume=0.5,adelay=%d:all=1[ck]" % (n, d))
        mix.append("[ck]")
        n += 1
    if e.get("music"):
        inputs += ["-stream_loop", "-1", "-i", e["music"]["path"]]
        parts.append("[%d:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,loudnorm=I=%s,afade=t=out:st=%.3f:d=0.6[m]"
                     % (n, e["music"].get("in", 0), e["music"].get("in", 0) + tl["total"], e["music"].get("lufs", -37),
                        tl["total"] - 0.6))
        mix.append("[m]")
        n += 1
    # asetpts resets the mix's timestamps first: without it atrim cut LUMI1109 Hook B's audio to 3.0s (2026-11-09)
    parts.append("%samix=inputs=%d:normalize=0:duration=longest,asetpts=N/SR/TB,atrim=0:%.3f,alimiter=limit=0.82[a]"
                 % ("".join(mix), len(mix), tl["total"]))
    if shots or not os.path.exists(audio):
        run([FF, "-v", "error", "-y"] + inputs + ["-filter_complex", ";".join(parts), "-map", "[a]", "-ar", "48000", audio])

    sched = text_frames(tl, os.path.join(work, "text"))
    blank = os.path.join(work, "text", "blank.png")
    Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(blank)
    pr = subprocess.Popen([FF, "-y", "-v", "error", "-i", video, "-i", audio, "-f", "image2pipe", "-framerate", str(FPS),
                           "-c:v", "png", "-i", "-", "-filter_complex",
                           "[0:v]setpts=N/(%d*TB)[b];[2:v]format=rgba,setpts=N/(%d*TB)[t];[b][t]overlay=0:0:format=auto:shortest=1,format=yuv420p[v]" % (FPS, FPS),
                           "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-b:v", "12M",
                           "-maxrate", "14M", "-bufsize", "24M", "-r", str(FPS), "-fps_mode", "cfr", "-c:a", "aac", "-b:a", "192k",
                           "-ac", "2", "-movflags", "+faststart", "-t", "%.3f" % tl["total"], out], stdin=subprocess.PIPE)
    cache = {}
    data = lambda pth: cache.setdefault(pth, open(pth, "rb").read())
    pos, total_f = 0, int(round(tl["total"] * FPS)) + 1
    for f0, f1, pth in sorted(sched):
        for _ in range(pos, f0):
            pr.stdin.write(data(blank))
        for _ in range(max(pos, f0), f1):
            pr.stdin.write(data(pth))
        pos = max(pos, f1)
    for _ in range(pos, total_f):
        pr.stdin.write(data(blank))
    pr.stdin.close()
    if pr.wait():
        sys.exit("text pass failed")
    return out


# ---------------------------------------------------------------- CapCut

def load_draft(name):
    if name.endswith(".json") and os.path.isfile(name):    # a saved timeline in templates/
        with open(name) as f:
            return json.load(f)
    with open(C.draft_file(C.project_path(name))) as f:
        return json.load(f)


SFX_DIR = os.path.expanduser("~/Video Editing Test/Assets/sfx")
SFX_END = [("whoosh_large.mp3", 0.51), ("correct_answer_piropyrone.mp3", 0.47), ("Click_Mouse_Click_02.mp3", 0.62)]
SFX_LIBRARY = {"whoosh_large.mp3": "swish_whoosh (large)(794558)", "correct_answer_piropyrone.mp3": "Correct answer Piropyrone (Standard)",
               "Click_Mouse_Click_02.mp3": "Click_Mouse_Click_02(864360)"}     # each one's name in CapCut's own sound library


def find_audio(project, pred):
    d = load_draft(project)
    mats = by_id(d)
    for ti, t in enumerate(d["tracks"]):
        if t["type"] == "audio":
            for si, sg in enumerate(t["segments"]):
                if pred(mats[sg["material_id"]][1].get("name", "")):
                    return Proto(d, ti, si)
    sys.exit("no audio prototype in " + project)


def by_id(d):
    return {m["id"]: (k, m) for k, v in d["materials"].items() if isinstance(v, list) for m in v
            if isinstance(m, dict) and "id" in m}


class Proto:
    """A segment plus its material and extra materials, copied with fresh ids."""

    def __init__(self, draft, track_index, seg_index):
        mats = by_id(draft)
        self.track = {k: v for k, v in draft["tracks"][track_index].items() if k != "segments"}
        self.seg = draft["tracks"][track_index]["segments"][seg_index]
        self.mat = mats[self.seg["material_id"]]
        self.refs = [mats[r] for r in self.seg["extra_material_refs"] if r in mats]

    def make(self, out_mats):
        seg = copy.deepcopy(self.seg)
        kind, mat = self.mat[0], copy.deepcopy(self.mat[1])
        mat["id"] = uid()
        seg["id"] = uid()
        seg["material_id"] = mat["id"]
        seg["extra_material_refs"] = []
        refs = {}
        for k, m in self.refs:
            m = copy.deepcopy(m)
            m["id"] = uid()
            out_mats.setdefault(k, []).append(m)
            seg["extra_material_refs"].append(m["id"])
            refs[k] = m
        out_mats.setdefault(kind, []).append(mat)
        seg["keyframe_refs"] = []
        seg["common_keyframes"] = []
        return seg, mat, refs


def tr(start, dur):
    # round the end, not the duration, so back-to-back segments never overlap
    a, b = int(round(start * US)), int(round((start + dur) * US))
    return {"start": a, "duration": b - a}


def text_content(text, proto_content):
    """CapCut text content JSON in the prototype's own style (font, fill, stroke). Ranges count UTF-16 units, as CapCut does."""
    st = copy.deepcopy(json.loads(proto_content)["styles"][0])
    st["range"] = [0, len(text.encode("utf-16-le")) // 2]
    return json.dumps({"styles": [st], "text": text}, ensure_ascii=False)


def find_text(project, pred):
    d = load_draft(project)
    mats = by_id(d)
    for ti, t in enumerate(d["tracks"]):
        if t["type"] == "text":
            for si, sg in enumerate(t["segments"]):
                if pred(json.loads(mats[sg["material_id"]][1]["content"])["text"], sg):
                    return Proto(d, ti, si)
    sys.exit("no text prototype in " + project)


_hdr_cache = {}


def is_hdr(path):
    """True for HDR video (HLG or PQ transfer), read from ffmpeg's stream line; SDR and stills are False."""
    if path not in _hdr_cache:
        r = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True)
        line = next((l for l in r.stderr.splitlines() if "Video:" in l), "")
        _hdr_cache[path] = bool(re.search(r"arib-std-b67|smpte2084", line))
    return _hdr_cache[path]


def write_capcut(e, tl, name, cover_jpg):
    root = C.DRAFTS
    dest = os.path.join(root, name)
    if os.path.exists(dest):
        sys.exit("CapCut project already exists: %s" % name)
    if subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0:
        sys.exit("CapCut is open: close it before writing a project")
    tpl = load_draft(TEMPLATE)
    tidx = {t["type"]: i for i, t in enumerate(tpl["tracks"])}
    vproto = Proto(tpl, 1, 0)
    text_i = [i for i, t in enumerate(tpl["tracks"]) if t["type"] == "text"][0]
    tproto = find_text(USER_TEMPLATE, lambda txt, sg: txt == "switch to red light mode")
    sprotos = [find_text(USER_TEMPLATE, lambda txt, sg, p=p: txt.startswith(p)) for p in STACK]
    cproto = find_audio(USER_TEMPLATE, lambda n: n.startswith("Click_Mouse_Click_02"))
    audio_tracks = [i for i, t in enumerate(tpl["tracks"]) if t["type"] == "audio"]
    aproto = Proto(tpl, audio_tracks[0], 0)
    mproto = Proto(tpl, audio_tracks[-1], 0)
    d = copy.deepcopy(tpl)
    for k, v in d["materials"].items():
        if isinstance(v, list):
            d["materials"][k] = []
    mats = d["materials"]
    # d["id"] must stay the template's main timeline id: CapCut finds the timeline folder by it
    d["duration"] = int(round(tl["total"] * US))
    d["config"]["subtitle_taskinfo"] = []
    tracks = []

    def new_track(proto, typ):
        t = copy.deepcopy(proto.track)
        t.update(id=uid(), type=typ, segments=[])
        tracks.append(t)
        return t

    vt = new_track(vproto, "video")
    for i, s in enumerate(tl["shots"]):
        seg, mat, refs = vproto.make(mats)
        info = probe(s["clip"])
        sp = s.get("speed", 1)
        dur = s["end"] - s["start"]
        mat.update(path=s["clip"], material_name=os.path.basename(s["clip"]), duration=int(info["dur"] * US),
                   width=info["w"], height=info["h"], type="video")
        for key in ("media_path", "local_material_id"):
            if key in mat:
                mat[key] = "" if key == "media_path" else mat[key]
        if "speeds" in refs:
            refs["speeds"]["speed"] = sp
        fit = min(W / info["w"], H / info["h"])
        cover = max(W / info["w"], H / info["h"])
        sc = round(cover / fit * s.get("zoom", 1), 4)
        seg.update(source_timerange=tr(s["src_in"], dur * sp), target_timerange=tr(s["start"], dur), speed=sp,
                   volume=0.0 if s.get("mute", True) else s.get("volume", 1.0), render_index=i, track_render_index=0)
        seg["last_nonzero_volume"] = 1.0
        # the template's segment carries CapCut's HDR mode (4), which boosts ordinary SDR footage so it looks
        # filtered and over-saturated (BLUECOLLAR talking head, user 2026-11-20). CapCut itself gives SDR clips
        # mode 1 and keeps 4 for real HDR (iPhone HLG / PQ) files, so match that.
        if isinstance(seg.get("hdr_settings"), dict):
            seg["hdr_settings"]["mode"] = 4 if is_hdr(s["clip"]) else 1
        seg["clip"]["scale"] = {"x": sc, "y": sc}
        seg["clip"]["transform"] = {"x": s.get("x", 0), "y": s.get("y", 0)}
        vt["segments"].append(seg)

    tt = new_track(tproto, "text")
    cap_y = tproto.seg["clip"]["transform"]["y"]
    for i, c in enumerate(tl["captions"]):
        seg, mat, refs = tproto.make(mats)
        content = text_content(balance_lines(c["text"]), tproto.mat[1]["content"])
        mat.update(content=content, base_content=content, type="text", recognize_task_id="", recognize_text="",
                   words={"start_time": [], "end_time": [], "text": []})
        seg.update(target_timerange=tr(c["start"], c["end"] - c["start"]), track_render_index=1, render_index=14000 + i)
        seg["clip"]["transform"] = {"x": 0.0, "y": cap_y}
        tt["segments"].append(seg)
    b = tl.get("end_box")
    if b and b.get("stack") == []:            # end with no boxes: captions just stop (a copy whose end card is in the footage)
        b = None
    if b and b.get("seq"):
        # one step per close line: its boxes take the stack's top, middle and bottom places (style.md)
        bts = [new_track(sp, "text") for sp in sprotos]
        for st in b["seq"]:
            for k, txt in enumerate(st["boxes"]):
                sp = sprotos[k]
                seg, mat, refs = sp.make(mats)
                content = text_content(txt, sp.mat[1]["content"])
                mat.update(content=content, base_content=content)
                seg.update(target_timerange=tr(st["start"], st["end"] - st["start"]), track_render_index=len(tracks) - 1)
                bts[k]["segments"].append(seg)
    elif b:
        # the three-box end stack, each box on its own track at the user's positions (style.md)
        for k, sp in enumerate(sprotos):
            bt = new_track(sp, "text")
            seg, mat, refs = sp.make(mats)
            if b.get("stack"):
                content = text_content(b["stack"][k], sp.mat[1]["content"])
                mat.update(content=content, base_content=content)
            seg.update(target_timerange=tr(b["start"], tl["total"] - b["start"]), track_render_index=len(tracks) - 1)
            bt["segments"].append(seg)

    at = new_track(aproto, "audio")
    vo_info = probe(e["vo"])
    for p in tl["vo"]:
        seg, mat, refs = aproto.make(mats)
        mat.update(path=e["vo"], name=os.path.basename(e["vo"]), duration=int(vo_info["dur"] * US))
        seg.update(source_timerange=tr(p["src_in"], p["src_out"] - p["src_in"]),
                   target_timerange=tr(p["start"], p["src_out"] - p["src_in"]), volume=e.get("capcut_vo_volume", VO_VOLUME),
                   speed=1.0, track_render_index=2)
        at["segments"].append(seg)
    if b:
        ct = new_track(cproto, "audio")
        steps = b.get("seq") or [b]
        for k, st in enumerate(steps):
            # each step its own sound, by its place in the close, never the same click on every box (user,
            # STOCKING V1 2026-11-10): the first box the large whoosh, the middle ones the Correct answer sound,
            # the last stack the mouse click (standards 10)
            sname, vol = (SFX_END[2] if k == len(steps) - 1 else SFX_END[0] if k == 0 else SFX_END[1])
            path = os.path.join(SFX_DIR, sname)
            seg, mat, refs = cproto.make(mats)
            sdur = probe(path)["dur"]
            # the sound's own CapCut material, whole: a copy of another sound's material with only the path changed
            # keeps that sound's effect_id, and CapCut points it back at that sound's file on its next save (every
            # end-box whoosh and chime became the click; ALEXXMAS 2026-11-17)
            lib = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "sound_materials.json")))
            own = lib.get(SFX_LIBRARY.get(sname))
            if own and os.path.exists(own["path"]):
                keep = mat["id"]
                mat.clear()
                mat.update(copy.deepcopy(own))
                mat["id"] = keep
                sdur = probe(own["path"])["dur"]
            else:
                mat.update(path=path, name=sname, duration=int(sdur * US))
            dur = min(sdur, st.get("end", 1e9) - st["start"])
            seg.update(source_timerange=tr(0, dur), target_timerange=tr(st["start"], dur), volume=vol,
                       track_render_index=3)
            ct["segments"].append(seg)
    if e.get("music"):
        mt = new_track(mproto, "audio")
        m = e["music"]
        mi = probe(m["path"])
        seg, mat, refs = mproto.make(mats)
        mat.update(path=m["path"], name=os.path.basename(m["path"]), duration=int(mi["dur"] * US))
        mdur = min(tl["total"], mi["dur"] - m.get("in", 0))
        seg.update(source_timerange=tr(m.get("in", 0), mdur), target_timerange=tr(0, mdur),
                   volume=m.get("capcut_volume", MUSIC_VOLUME), speed=1.0, track_render_index=3)
        mt["segments"].append(seg)
    d["tracks"] = tracks

    # clone the template folder like CapCut's Duplicate, then swap the timeline in
    src = C.project_path(TEMPLATE)
    shutil.copytree(src, dest, ignore=shutil.ignore_patterns("*.bak", "template*.tmp", "matting", "smart_crop",
                                                              "adjust_mask", "qr_upload", "subdraft"))
    main = json.load(open(os.path.join(dest, "Timelines", "project.json")))
    now = int(time.time() * US)
    main["id"] = uid()
    main["create_time"] = main["update_time"] = now
    json.dump(main, open(os.path.join(dest, "Timelines", "project.json"), "w"))
    # CapCut can't read hidden folders like ~/.video-editing-work, so copy those files into the project
    media = os.path.join(dest, "Resources", "media")
    for k in ("videos", "audios"):
        for m in d["materials"].get(k, []):
            if "/." in m.get("path", ""):
                os.makedirs(media, exist_ok=True)
                to = os.path.join(media, os.path.basename(m["path"]))
                if not os.path.exists(to):
                    shutil.copy(m["path"], to)
                m["path"] = to
    for p in [os.path.join(dest, "draft_info.json"), os.path.join(dest, "Timelines", main["main_timeline_id"], "draft_info.json")]:
        with open(p, "w") as f:
            json.dump(d, f, ensure_ascii=False)
    if cover_jpg:
        shutil.copy(cover_jpg, os.path.join(dest, "draft_cover.jpg"))
        shutil.copy(cover_jpg, os.path.join(dest, "Timelines", main["main_timeline_id"], "draft_cover.jpg"))
    meta_p = os.path.join(dest, "draft_meta_info.json")
    meta = json.load(open(meta_p))
    draft_id = uid()
    meta.update(draft_id=draft_id, draft_name=name, draft_fold_path=dest, draft_root_path=root,
                tm_duration=d["duration"], tm_draft_create=now, tm_draft_modified=now,
                draft_timeline_materials_size_=0)
    # start with an empty media panel; the user imports their own clips (2026-11-05)
    for g in meta.get("draft_materials", []):
        g["value"] = []
    json.dump(meta, open(meta_p, "w"), ensure_ascii=False)

    rp = os.path.join(root, "root_meta_info.json")
    shutil.copy(rp, rp + ".before-%s.bak" % re.sub(r"\W+", "_", name))
    rm = json.load(open(rp))
    ent = copy.deepcopy(next(x for x in rm["all_draft_store"] if x["draft_name"] == TEMPLATE))
    ent.update(draft_id=draft_id, draft_name=name, draft_fold_path=dest, draft_root_path=root,
               draft_cover=os.path.join(dest, "draft_cover.jpg"), draft_json_file=os.path.join(dest, "draft_info.json"),
               tm_duration=d["duration"], tm_draft_create=now, tm_draft_modified=now, draft_timeline_materials_size=0)
    # a rebuild into the same folder (old one moved to the Trash) left its old entry behind, so CapCut listed
    # "BLUECOLLAR HookA" three times (user, 2026-11-21): drop any entry for this folder before adding the new one
    rm["all_draft_store"] = [x for x in rm["all_draft_store"] if x.get("draft_fold_path", "").rstrip("/") != dest.rstrip("/")]
    rm["all_draft_store"].insert(0, ent)
    json.dump(rm, open(rp, "w"), ensure_ascii=False)
    return dest


def main(argv):
    edit = json.load(open(argv[1]))
    hook = argv[argv.index("--hook") + 1] if "--hook" in argv else "A"
    tl = compile_timeline(edit, hook)
    base = os.path.dirname(os.path.abspath(argv[1]))
    work = os.path.join(base, "build", "Hook" + hook)
    os.makedirs(work, exist_ok=True)
    json.dump(tl, open(os.path.join(work, "timeline.json"), "w"), indent=1)
    print("Hook %s: %.2fs, hook slot %.2fs, %d shots, %d captions, %d VO pieces"
          % (hook, tl["total"], tl["hook_end"], len(tl["shots"]), len(tl["captions"]), len(tl["vo"])))
    for s in tl["shots"]:
        if s.get("warn"):
            print("  WARN %.2f %s: %s" % (s["start"], os.path.basename(s["clip"]), s["warn"]))
        if s["end"] - s["start"] > 3.2 and s.get("kind") != "hook":
            print("  LONG %.2f-%.2f %s" % (s["start"], s["end"], os.path.basename(s["clip"])))
    if "--mp4" in argv:
        out = os.path.join(work, "%s_Hook%s.mp4" % (edit["code"], hook))
        render_mp4(edit, tl, out, os.path.join(work, "parts"), reuse="--reuse" in argv)
        print("mp4:", out)
    if "--capcut" in argv:
        name = argv[argv.index("--name") + 1] if "--name" in argv else "%s Hook%s" % (edit["code"], hook)
        cover = os.path.join(work, "cover.jpg")
        mp4 = os.path.join(work, "%s_Hook%s.mp4" % (edit["code"], hook))
        if os.path.exists(mp4):
            run([FF, "-v", "error", "-y", "-ss", "%.2f" % (tl["hook_end"] + 1), "-i", mp4, "-frames:v", "1", "-vf", "scale=540:-2", cover])
        dest = write_capcut(edit, tl, name, cover if os.path.exists(cover) else None)
        snap = os.path.join(work, "capcut_snapshot.json")
        json.dump(C.normalise(dest), open(snap, "w"), indent=1)
        print("capcut:", dest, "\nsnapshot:", snap)


if __name__ == "__main__":
    main(sys.argv)
