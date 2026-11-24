"""Shared helpers for the ai-voiceover-ads scripts."""
import json, os, re, subprocess, sys

import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())


def project():
    """Project folder from argv[1]; refuses iCloud-synced locations, where macOS offloads media mid-job."""
    if len(sys.argv) < 2: raise SystemExit("usage: <script> <project-folder> [...]")
    p = os.path.abspath(os.path.expanduser(sys.argv[1]))
    home = os.path.expanduser("~")
    if p.startswith((f"{home}/Documents", f"{home}/Desktop", f"{home}/Library/Mobile Documents")):
        raise SystemExit(f"{p} is in an iCloud-synced folder, where clips can be offloaded mid-job. Use ~/.video-editing-work/<brand>/<ad>.")
    os.chdir(p)
    for d in ("src", "proxy", "out", "work/ovl", "work/qc"): os.makedirs(d, exist_ok=True)
    return p


def config():
    return json.load(open("config.json"))


def run(cmd):
    """Run at low priority so the rest of the machine stays usable."""
    r = subprocess.run(["nice", "-n", "10", FF, "-nostdin", "-y", "-loglevel", "error", *cmd], capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stderr[-2000:])
    return r


def probe_duration(path):
    err = subprocess.run([FF, "-nostdin", "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
