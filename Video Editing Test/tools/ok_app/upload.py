#!/usr/bin/env python3
"""Put finished ads into the OK App queue (Deliverables > Ready for Upload) without the browser.

  upload.py <spec.json> [--dry-run]

The OK App keeps deliverables in the team's Supabase project: files in the private "deliverables" bucket at
<brand>/<deliverable id>/<n>.<ext> with a "<n>.<ext>.thumb.jpg" beside each, one row in public.deliverables, one row
per file in public.deliverable_files, and a "created" row in public.activity_log. This does the same thing the app's
own Upload page does, with the site's public key (settings in ~/.video-editing-work/ok_app.json).

spec.json: {"brand": "luxelight", "name": "[CLAUDE] BF Free Case", "files": ["/path/V1.mp4", ...], "page": "Luxelight",
            "ad_copy": "...", "headline": "...", "description": "...", "landing_page": "https://...", "cta": "Shop Now", "notes": null}
Files are named "<name> - V<n> - <creator>.mp4" (user, 2026-11-24) and the deliverable takes the first file's name.
One deliverable per concept. Only run it on ads the user has approved, and only when they ask for the upload.
"""
import json, os, subprocess, sys, tempfile, urllib.request, urllib.error, urllib.parse, uuid
CFG = json.load(open(os.path.expanduser("~/.video-editing-work/ok_app.json")))
FF = os.path.expanduser("~/Video Editing Test/tools/venv/bin/ffmpeg")
HDR = {"apikey": CFG["key"], "Authorization": "Bearer " + CFG["key"]}

def call(method, path, data=None, headers=None):
    req = urllib.request.Request(CFG["url"] + path, data=data, method=method, headers=dict(HDR, **(headers or {})))
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        sys.exit("OK App refused %s %s: %s %s" % (method, path, e.code, e.read().decode()[:400]))

def put_object(path, blob, ctype):
    return call("POST", "/storage/v1/object/%s/%s" % (CFG["bucket"], urllib.parse.quote(path)), blob, {"Content-Type": ctype, "x-upsert": "false"})

def main():
    spec = json.load(open(sys.argv[1])); dry = "--dry-run" in sys.argv
    did = str(uuid.uuid4()); brand = spec["brand"]
    names = ["%s - V%d - %s%s" % (spec["name"], i + 1, CFG["creator"], os.path.splitext(f)[1]) for i, f in enumerate(spec["files"])]
    title = os.path.splitext(names[0])[0]
    for f in spec["files"]:
        if not os.path.exists(f): sys.exit("missing file: " + f)
    dup = json.loads(call("GET", "/rest/v1/deliverables?select=id,status&brand=eq.%s&title=eq.%s" % (brand, urllib.parse.quote(title)))[1])
    if dup: sys.exit("already in the OK App: %s (%s). Not uploading it twice." % (title, dup[0]["status"]))
    print("deliverable:", title, "| files:", names)
    if dry: return print("dry run: nothing uploaded")
    rows = []
    for i, (f, n) in enumerate(zip(spec["files"], names)):
        ext = os.path.splitext(f)[1].lstrip(".").lower(); path = "%s/%s/%d.%s" % (brand, did, i, ext)
        put_object(path, open(f, "rb").read(), "video/mp4" if ext == "mp4" else "application/octet-stream")
        th = os.path.join(tempfile.mkdtemp(), "t.jpg")
        subprocess.run([FF, "-v", "error", "-y", "-ss", "1", "-i", f, "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "4", th], check=True)
        put_object(path + ".thumb.jpg", open(th, "rb").read(), "image/jpeg")
        rows.append(dict(deliverable_id=did, file_path=path, file_name=n, file_type="video/mp4", file_size=os.path.getsize(f), sort_order=i, thumb_path=path + ".thumb.jpg"))
        print("  uploaded", n)
    js = {"Content-Type": "application/json", "Prefer": "return=minimal"}
    d = dict(id=did, brand=brand, content_type="video", title=title, ad_copy=spec["ad_copy"], headline=spec["headline"], description=spec["description"],
             landing_page=spec["landing_page"], cta=spec["cta"], page=spec["page"], notes=spec.get("notes"), created_by=CFG["created_by"], status="ready_for_upload")
    call("POST", "/rest/v1/deliverables", json.dumps(d).encode(), js)
    call("POST", "/rest/v1/deliverable_files", json.dumps(rows).encode(), js)
    call("POST", "/rest/v1/activity_log", json.dumps(dict(brand=brand, action="created", deliverable_id=did)).encode(), js)
    print("created", did)

main()
