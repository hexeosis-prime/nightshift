"""project.json safety: the aspect owns the sizes, and one bad value can't lock a project."""
import json, os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from nightshift import project as P


def make(cfg):
    d = tempfile.mkdtemp()
    json.dump(cfg, open(os.path.join(d, "project.json"), "w"))
    return P.Project(d)


def main():
    # an old project.json with explicit 16:9 sizes plus "aspect": "9:16" renders vertical (Zero's three landscape projects)
    p = make({"aspect": "9:16", "work_size": [1280, 768], "crop": [1280, 720], "final_size": [1920, 1080]})
    assert p.cfg["work_size"] == [768, 1280] and p.cfg["final_size"] == [1080, 1920], p.cfg["work_size"]
    print("ok   aspect 9:16 wins over old explicit sizes")
    starter = json.load(open(os.path.join(os.path.dirname(__file__), "..", "projects", "starter", "project.json")))
    assert "work_size" not in starter and starter.get("aspect") == "16:9"
    st = dict(starter, aspect="9:16")
    p = make(st)
    assert p.cfg["work_size"] == [768, 1280]
    print("ok   starter copy switched to 9:16 renders vertical")
    # a bad profile opens with a warning instead of raising (it used to lock every later call, even the fix)
    p = make({"profile": "medium"})
    assert p.warnings and p.cfg["profile"] == "full", (p.warnings, p.cfg.get("profile"))
    print("ok   bad profile opens with a warning:", p.warnings[0])
    assert P.check_config({"profile": "medium"}) and not P.check_config({"profile": "short", "aspect": "9:16"})
    print("ok   check_config catches it before write")
    print("config ok")


if __name__ == "__main__":
    main()
