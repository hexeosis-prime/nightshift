"""Nightshift Studio end to end against the fake ComfyUI: make a project over the app's HTTP API (a photo, your own track,
9:16, FLUX 3 Klein), run it, pick a sheet at the first checkpoint, approve the rest, and check the finished 1080x1920 pass.

    python tests/test_app.py            (add --keep to leave the folder for a look, --serve to keep the app up afterwards)
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from fake_comfy import serve as fake_serve
from test_offline import ff, fake_words
from nightshift import app as A
from nightshift.project import Project


def call(base, path, body=None):
    req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="GET" if body is None else "POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def wait(base, name, until, timeout=1200):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = call(base, f"/api/projects/{name}")
        if until(v):
            return v
        if not v["running"] and not v["waiting"] and v["step"] != "done" and time.time() - t0 > 3:
            log = call(base, f"/api/projects/{name}/log")["lines"]
            raise AssertionError("run ended early:\n" + "\n".join(log[-25:]))
        time.sleep(0.3)
    raise AssertionError(f"timeout waiting; last view {json.dumps(v)[:800]}")


def main(keep=False, stay=False):
    tmp = tempfile.mkdtemp(prefix="ns_app_")
    comfy = os.path.join(tmp, "ComfyUI")
    for d in ("input", "output"):
        os.makedirs(os.path.join(comfy, d))
    fsrv, _ = fake_serve(comfy, 18288, render_seconds=0.05)
    studio = A.Studio(os.path.join(comfy, "output", "nightshift"), "http://127.0.0.1:18288", comfy)
    srv = ThreadingHTTPServer(("127.0.0.1", 18289), A.handler(studio))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:18289"
    try:
        html = urllib.request.urlopen(base + "/").read().decode()
        assert "Nightshift Studio" in html
        info = call(base, "/api/info")
        assert set(info["scenes"]) >= {"night-avenue", "desert-highway"} and "short" in info["lengths"]
        assert call(base, "/api/comfy")["ok"]

        song = os.path.join(tmp, "my track.mp3")
        ff("-f", "lavfi", "-i", "sine=frequency=220:duration=70", "-f", "lavfi",
           "-i", "aevalsrc='0.9*sin(2*PI*60*t)*exp(-30*mod(t,0.5))':d=70", "-filter_complex", "amix=inputs=2", song)
        photo = os.path.join(tmp, "me.png")
        ff("-f", "lavfi", "-i", "testsrc2=s=600x800", "-frames:v", "1", photo)
        b64 = lambda f: "data:application/octet-stream;base64," + base64.b64encode(open(f, "rb").read()).decode()
        form = {"name": "Desert Test", "length": "short", "aspect": "9:16", "image_model": "flux3", "mode": "director",
                "scene": "desert-highway",
                "character": {"noun": "man", "look": "early thirties, short dark curly hair", "outfit": "a rust corduroy jacket, white t-shirt"},
                "song": {"source": "upload", "lyrics": info["default_lyrics"], "start": 10}}
        r = call(base, "/api/projects", {"form": form, "files": {"photo": {"name": "me.png", "data": b64(photo)},
                                                                   "audio": {"name": "my track.mp3", "data": b64(song)}}})
        name = r["name"]
        assert name == "desert-test", name
        p = Project(os.path.join(comfy, "output", "nightshift", name))
        assert p.renders_in_place
        assert p.cfg["work_size"] == [768, 1280] and p.cfg["final_size"] == [1080, 1920]
        assert p.cfg["workflows"]["still"] == "still_flux3" and p.cfg["workflows"]["sheet_image"] == "sheet_from_image_flux3"
        assert p.canon["characters"]["lead"]["reference"] == "refs/lead.png"
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    p.path("song", "song.mp3")], capture_output=True, text=True).stdout)
        assert 39 < dur < 41, dur                         # trimmed to the profile length
        # the test can't transcribe: give the song a beat map and a pretend transcript, and poll fast
        from nightshift.beatmap import beatmap
        beatmap(p.path("song", "song.mp3"), p.path("song", "beatmap.json"))
        fake_words(p)
        cfg = p.load("project.json")
        cfg["watchdog"] = {"poll_seconds": 0.2}
        p.save("project.json", cfg)

        call(base, f"/api/projects/{name}/run", {})
        v = wait(base, name, lambda v: v["waiting"])
        assert v["waiting"]["checkpoint"] == "sheets_review", v["waiting"]
        ch = v["waiting"]["choices"][0]
        assert ch["kind"] == "sheet" and len(ch["options"]) == 2, ch
        job = json.load(open(p.path("jobs", "sheet_lead_real_c0.json")))
        assert any(n["class_type"] == "ReferenceMultiLatent" for n in job.values()), "photo -> FLUX 3 sheet from image"
        call(base, f"/api/projects/{name}/pick", {"kind": "sheet", "char": "lead", "world": "real", "file": ch["options"][1]["file"]})
        v = call(base, f"/api/projects/{name}")
        assert v["waiting"]["choices"][0]["picked_file"] == ch["options"][1]["file"]
        try:
            call(base, f"/api/projects/{name}/pick", {"kind": "sheet", "char": "lead", "world": "real", "file": "../../../etc/passwd"})
            raise AssertionError("path outside the project was accepted")
        except urllib.error.HTTPError as e:
            assert e.code == 400

        seen = ["sheets_review"]
        while True:
            call(base, f"/api/projects/{name}/continue", {"notes": f"ok {seen[-1]}"})
            v = wait(base, name, lambda v: v["waiting"] or v["step"] == "done")
            if v["step"] == "done":
                break
            seen.append(v["waiting"]["checkpoint"])
            assert len(seen) < 8, seen
        assert seen == ["sheets_review", "stills_review", "pass_review"], seen     # one take per shot: no takes review
        assert v["finished"] == ["out/pass01.mp4"], v["finished"]
        wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0",
                             p.path("out", "pass01.mp4")], capture_output=True, text=True).stdout.strip()
        assert wh == "1080,1920", wh
        edit = json.load(open(p.path("jobs", "s02_edit.json")))
        txt = next(n["inputs"]["text"] for n in edit.values() if n.get("_meta", {}).get("title") == "prompt")
        assert "<ref_image_1>" in txt and "[reference_image" not in txt, txt[:200]
        size = next(n["inputs"] for n in edit.values() if n["class_type"] == "EmptyFlux2LatentImage")
        assert (size["width"], size["height"]) == (768, 1280)
        ff_job = next(f for f in sorted(os.listdir(p.path("jobs"))) if f.endswith("_video.meta.json")
                      and json.load(open(p.path("jobs", f)))["kind"] == "ff")
        vid = json.load(open(p.path("jobs", ff_job.replace(".meta.json", ".json"))))
        assert any(n["class_type"] == "EmptyImage" and n["inputs"]["width"] == 768 for n in vid.values())
        # files are served with ranges (video seeking)
        req = urllib.request.Request(base + f"/files/{name}/out/pass01.mp4", headers={"Range": "bytes=0-99"})
        with urllib.request.urlopen(req) as r:
            assert r.status == 206 and len(r.read()) == 100
        print("app ok:", name, "checkpoints", seen, "->", wh)
        if stay:
            print("serving on", base, "(ctrl-c to stop)")
            while True:
                time.sleep(1)
    finally:
        srv.shutdown()
        fsrv.shutdown()
        if keep or stay:
            print("kept", tmp)
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main("--keep" in sys.argv, "--serve" in sys.argv)
