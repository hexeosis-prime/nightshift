"""Overlay on the offline test project: tracks, data.json, a few hundred frames rendered in Chromium, alpha chunks, finish."""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from nightshift.project import Project
from nightshift import overlay as O, finish

def run(root):
    p = Project(root)
    cfg = p.load("project.json")
    cfg["overlay"]["enabled"] = True
    cfg["overlay"]["style"]["widgets"] = {
        "expand_line": {"shot": "s03", "word": "light"},
        "merge": {"lines": ["Tell me what you're chasing", "Tell me where it goes", "Only the night knows"]},
        "readout": {"title": "READOUT", "start_section": "VERSE", "climb": {"VERSE": [0.01, 0.02]}, "break_section": "CHORUS"}}
    p.save("project.json", cfg); p = Project(root)
    print(O.track(p))
    edl = p.path("out", "pass01_cut_edl.csv")
    faces = O.mapfaces(p, edl)
    # pretend a face is on screen in the second shot so placement logic runs
    fj = json.load(open(faces)); fj["faces"] = [[800, 200, 260, 320] if 80 <= i < 400 else f for i, f in enumerate(fj["faces"])]
    json.dump(fj, open(faces, "w"))
    r = O.prep(p, edl, faces); print(r)
    t0 = time.time()
    print(O.render(r["out"], p.path("overlay", "frames"), 0, 432))
    print("frames/s", round(432 / (time.time() - t0), 1))
    outs = O.encode(p.path("overlay", "frames"), p.path("overlay", "chunks"), 0, 1)
    print(outs)
    out = finish.finish_chunk(p.path("out", "pass01_cut.mp4"), p.path("out", "pass01_ov.mp4"), 0,
                              overlay=p.path("overlay", "chunks", "ov_%02d.webm"), halftone=p.path("overlay", "halftone.png"))
    print(out)

if __name__ == "__main__":
    run(sys.argv[1])
