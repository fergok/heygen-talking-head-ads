"""Pre-send QC. Transcribes each finished video and checks it against the script and captions.

Reports: missing words, captions starting early or late, dead air, the hook hard cut, and loudness.
Writes work/qc/strip_<version>.jpg (the caption area once a second) and hook_<version>.jpg (frames around the hook cut)
to look at by eye. Exits non-zero if something fails.

Usage: python -I check.py <project> [version-name]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I leaves the script folder off the path
import difflib, json, re, subprocess, sys

from faster_whisper import WhisperModel

from common import FF, config, norm, project, run

project()
CFG = config()
model = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=4)
LABEL = "drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:text='%{pts\\:hms}':x=2:y=2:fontsize=12:fontcolor=yellow:box=1:boxcolor=black"
only = sys.argv[2] if len(sys.argv) > 2 else None
failed = False

gaps = subprocess.run([FF, "-nostdin", "-i", "work/vo_tight.wav", "-af", "silencedetect=noise=-31dB:d=0.2", "-f", "null", "-"],
                      capture_output=True, text=True).stderr.count("silence_start")

for v in CFG["versions"]:
    name = v["name"]
    if only not in (None, name): continue
    log = json.load(open(f"work/log_{name}.json")); path = log["final"]
    wav = f"work/qc_{name}.wav"
    run(["-i", path, "-vn", "-ac", "1", "-ar", "16000", wav])
    segs, _ = model.transcribe(wav, word_timestamps=True)
    heard = [(norm(x.word), x.start) for s in segs for x in s.words if norm(x.word)]

    # align caption words to heard words, so a word that occurs twice can't match the wrong occurrence
    script, first = [], []
    for t, cap in log["captions"]:
        first.append((len(script), t, cap)); script += [norm(w) for w in cap.split()]
    sm = difflib.SequenceMatcher(a=script, b=[h for h, _ in heard], autojunk=False)
    index = {}
    for b in sm.get_matching_blocks():
        for k in range(b.size): index[b.a + k] = b.b + k
    lost = [script[a:b] for tag, a, b, _, _ in sm.get_opcodes() if tag in ("delete", "replace") and b - a >= 3]
    # the first body caption is pinned to the cut by design, so only later captions are timed
    off = [(t - heard[index[i]][1], cap, t) for i, t, cap in first if i in index and t > log["hook_end"] + 0.1]
    bad = [o for o in off if abs(o[0]) > 0.2]
    # spoken words after the hook that no caption covers
    uncaptioned = [heard[k] for tag, _, _, c0, c1 in sm.get_opcodes() if tag == "insert" for k in range(c0, c1)
                   if heard[k][1] > log["hook_end"] + 0.1]

    hook_end = log["hook_end"]
    ld = subprocess.run([FF, "-nostdin", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", ld)[-1]

    # the last hook frame and first body frame must differ in the hook-text area
    run(["-ss", f"{max(hook_end - 0.4, 0):.2f}", "-t", "0.8", "-i", path, "-vf",
         f"fps=30,scale=150:-2,{LABEL},tile=24x1", "-frames:v", "1", f"work/qc/hook_{name}.jpg"])
    run(["-i", path, "-vf", f"fps=1,crop=iw:ih*0.13:0:ih*0.72,scale=300:-2,{LABEL},tile=4x20", "-frames:v", "1", f"work/qc/strip_{name}.jpg"])

    ok = not lost and not bad and not uncaptioned
    failed |= not ok
    print(f"{name}: {'PASS' if ok else 'FAIL'} | {len(script)} caption words, runs of 3+ missing: {len(lost)} | "
          f"spoken with no caption: {len(uncaptioned)} | captions off by >0.2s: {len(bad)} of {len(off)} | {lufs} LUFS | {log['duration']:.1f}s | hook ends {hook_end:.2f}s")
    for chunk in lost: print("   missing speech:", " ".join(chunk))
    for w, t in uncaptioned: print(f"   no caption: {w} at {t:.2f}s")
    for o, cap, t in bad: print(f"   {t:6.2f}s {o:+.2f}s  {cap}")
print(f"Pauses over 0.2s left in the voiceover: {gaps}")
print("Now look at work/qc/strip_*.jpg (a caption on every second after the hook) and hook_*.jpg (text gone on the first body frame).")
sys.exit(1 if failed or gaps else 0)
