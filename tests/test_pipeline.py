"""The whole pass against a fake ComfyUI (tests/fake_comfy.py): submit, watch, OOM retry, collect, build every stage,
director checkpoints, yolo picks, cut, finish. Two layouts: project inside ComfyUI's output folder, and a 'remote' ComfyUI
reached only over HTTP (uploads and downloads)."""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from fake_comfy import serve
from test_offline import fake_song, fake_words, ff
from nightshift import pipeline
from nightshift.project import init


def prepare(p):
    src = fake_song(p, 40)
    from nightshift import song
    song.choose(p, src)
    from nightshift.beatmap import beatmap
    beatmap(p.path("song", "song.mp3"), p.path("song", "beatmap.json"))
    fake_words(p)
    cfg = p.load("project.json")
    cfg["watchdog"] = {"poll_seconds": 0.2}
    cfg["finish"] = {"chunk_seconds": 20, "halftone": "auto"}
    p.save("project.json", cfg)


def run_layout(remote, port):
    tmp = tempfile.mkdtemp(prefix="ns_pipe_")
    comfy = os.path.join(tmp, "ComfyUI")
    for d in ("input", "output"):
        os.makedirs(os.path.join(comfy, d))
    srv, fake = serve(comfy, port, render_seconds=0.05, fail_first="s03_ff")
    try:
        if remote:
            p = init(os.path.join(tmp, "projects", "demo"), "demo", comfy_url=f"http://127.0.0.1:{port}")
        else:
            p = init(os.path.join(comfy, "output", "nightshift", "demo"), "demo", comfy_url=f"http://127.0.0.1:{port}", comfy_dir=comfy)
        prepare(p)
        from nightshift.project import Project
        p = Project(p.root)
        events = []
        log = lambda m: (events.append(m), print("  ", m))

        st = pipeline.run(p, on_event=log)              # director: character sheets first
        assert st["waiting"]["checkpoint"] == "sheets_review", st
        assert len(p.renders("sheets", "lead_real_c*")) == 3 and os.path.exists(p.path("review", "sheets_lead_real.jpg"))
        from nightshift import sheets
        sheets.pick(p, "lead", "real", p.renders("sheets", "lead_real_c*")[1])     # the director's pick
        pipeline.approve(p)
        st = pipeline.run(p, on_event=log)              # the stage outfit, edited from the approved sheet
        assert st["waiting"]["checkpoint"] == "outfits_review", st
        assert len(p.renders("sheets", "lead_stage_o*")) == 3
        pipeline.approve(p)                             # no pick: the best-scoring outfit sheet is used
        st = pipeline.run(p, on_event=log)              # -> stills_review
        assert st["waiting"]["checkpoint"] == "stills_review", st
        canon = p.canon["characters"]["lead"]["sheet"]
        assert canon == {"real": "refs/sheets/lead_real.png", "stage": "refs/sheets/lead_stage.png"}, canon
        assert os.path.exists(os.path.join(comfy, "input", "nightshift", "demo", "song.mp3"))
        assert p.renders("stills", "s02_edit_*"), os.listdir(p.path("stills"))
        pipeline.approve(p, "faces fine")
        st = pipeline.run(p, on_event=log)              # -> takes_review
        assert st["waiting"]["checkpoint"] == "takes_review", st
        assert any("FAILED" in e and "s03" in e for e in events) and any("retry" in e and "s03" in e for e in events), "OOM retry"
        assert len(p.renders("clips", "s06_*")) == 4, p.renders("clips", "s06_*")     # complex shot: best-of-4
        assert os.path.exists(p.path("review", "takes_s06.jpg"))
        pipeline.approve(p)
        st = pipeline.run(p, on_event=log)              # -> pass_review
        assert st["waiting"]["checkpoint"] == "pass_review", st
        assert os.path.exists(p.path("out", "pass01.mp4")) and os.path.exists(p.path("review", "pass01_review_numbered.mp4"))
        pipeline.approve(p)
        st = pipeline.run(p, on_event=log)
        assert st["step"] == "done"

        # second pass after a note on one shot: only that shot renders
        n_jobs = len(json.load(open(p.path("queue.json")))["jobs"])
        pipeline.new_pass(p)
        for f in p.renders("clips", "s03_*"):
            os.remove(f)
        p.patch_shot("s03", {"video": "Medium shot of {lead} stopping to look back over her shoulder."})
        cfg = p.load("project.json"); cfg["mode"] = "yolo"; p.save("project.json", cfg)
        p = Project(p.root)
        st = pipeline.run(p, on_event=log)
        q = json.load(open(p.path("queue.json")))["jobs"]
        new = [j["job"] for j in q[n_jobs:]]
        assert new and all("s03" in j for j in new), new
        assert os.path.exists(p.path("out", "pass02.mp4"))
        print("ok", "remote" if remote else "local", tmp)
    finally:
        srv.shutdown()


def test_local():
    run_layout(False, 8191)


def test_remote():
    run_layout(True, 8192)


if __name__ == "__main__":
    test_local()
    test_remote()
