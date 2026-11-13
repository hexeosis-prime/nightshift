"""Abstract / instrumental plans: no cast, no lyrics. Planned, made into a project and run through the cut against the fake
ComfyUI (the song step skips the lyric check, analyze times nothing and the cuts follow the beats). Also: a broken shot
list stops before rendering with errors that name the shot and the field, and pipeline health reports it."""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from fake_comfy import serve
from nightshift import agent, pipeline
from nightshift.project import Project

PLAN = {
    "abstract": True, "title": "Prism Drift", "logline": "Light breaking through glass, slowly.",
    "characters": {}, "grade": "none",
    "worlds": {"glass": {"style": "macro photograph of glass and light, rainbow caustics on black", "daytime": False, "indoor": True}},
    "song": {"caption": "Instrumental, no vocals. 92 BPM ambient electronica in D minor: glassy pads, a soft pulsing sub bass, "
                        "slow swells. 0:00-0:10 Intro, 0:10-0:30 Build, 0:30-0:40 Outro with a long natural decay.",
             "lyrics": "[Intro]\n[Instrumental]\n\n[Build]\n[Instrumental]\n\n[Outro]\n[Instrumental]"},
    "shots": [
        {"mode": "t2v", "chars": [], "video": "Darkness, then a thin beam of light finds a glass prism. Slow push in."},
        {"mode": "ff", "chars": [], "location": "a glass prism on black velvet", "action": "rainbow caustics, 100mm macro lens",
         "video": "Rainbow caustics drift slowly across the black velvet. Static macro shot."},
        {"mode": "fflf", "chars": [], "location": "a cave of clear crystals", "video": "Slow push through the crystals."},
        {"mode": "ff", "chars": [], "location": "ripples on dark water", "action": "light reflections, 85mm lens",
         "video": "Light reflections shimmer on slow ripples. Slow drift left."},
    ],
}


def main():
    pl = agent.normalize(PLAN, "short")
    assert pl["abstract"] and pl["instrumental"] and not pl["hud"] and not pl["characters"]
    assert all(s["chars"] == [] for s in pl["shots"]) and not any(s["mode"] == "lipsync" for s in pl["shots"])
    try:
        agent.normalize(dict(PLAN, abstract=False), "short")
        raise AssertionError("a cast-less plan that isn't abstract must be refused")
    except agent.PlanError as e:
        assert "characters" in str(e)
    print("ok   abstract plan: no cast, no lip-sync, instrumental lyrics, HUD off")

    tmp = tempfile.mkdtemp(prefix="ns_abstract_")
    comfy = os.path.join(tmp, "ComfyUI")
    for d in ("input", "output"):
        os.makedirs(os.path.join(comfy, d))
    srv, _ = serve(comfy, 8193, render_seconds=0.05)
    try:
        p = agent.create_from_plan(os.path.join(comfy, "output", "nightshift", "prism"), pl,
                                   {"comfy_url": "http://127.0.0.1:8193", "comfy_dir": comfy, "mode": "yolo"})
        assert p.cfg.get("instrumental") is True and not p.cfg["overlay"].get("enabled")
        cfg = p.load("project.json")
        cfg["watchdog"] = {"poll_seconds": 0.2}
        cfg["song_seeds"] = [101, 202]
        cfg.setdefault("qc", {})["text"] = False
        p.save("project.json", cfg)
        p = Project(p.root)
        events = []
        st = pipeline.run(p, until="cut", on_event=lambda m: (events.append(m), print("  ", m)))
        assert st["step"] != "done" and "cut" in [h["step"] for h in st["history"]], st
        assert any("instrumental" in e for e in events)
        assert p.load("song/words.json") == {"words": []}
        cut = p.load("cut.json")
        assert len(cut["shots"]) >= 3 and all(c.get("src") for c in cut["shots"]), cut
        assert os.path.exists(p.path("out", "pass01_cut.mp4"))
        print("ok   instrumental abstract project runs through the cut:", len(cut["shots"]), "shots")

        # a broken shot list stops before rendering, naming the shot and the field
        doc = p.load("shots.json")
        doc["shots"][1]["mode"] = "ffl"
        doc["shots"][2]["chars"] = ["ghost"]
        p.save("shots.json", doc)
        try:
            pipeline.run(Project(p.root), start="stills", on_event=lambda m: None)
            raise AssertionError("a bad shot list must stop the run")
        except pipeline.StepError as e:
            msg = str(e)
            assert "s02, field 'mode'" in msg and "s03, field 'chars'" in msg and "'ghost'" in msg, msg
        h = pipeline.health(Project(p.root))
        assert h["status"] == "failed" and "field 'mode'" in h["error"], h
        print("ok   bad shot list stops before rendering:", msg[:110], "...")
        print("ok   health:", h["status"], "-", h["advice"])
        try:
            Project(p.root).patch_shot("s01", {"mode": "zoom"})
            raise AssertionError("patch_shot must refuse a bad mode")
        except ValueError as e:
            refused = str(e)
        assert "field 'mode'" in refused, refused
        print("ok   patch_shot refuses a bad value:", refused)
    finally:
        srv.shutdown()
    print("abstract ok")


if __name__ == "__main__":
    main()
