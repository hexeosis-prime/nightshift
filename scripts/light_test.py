"""Does the character take the scene's light? Frames made from the sheet, five prompt versions (Nov 18).

    python3 scripts/light_test.py setup <project> <test dir> <comfy dir>   copy a finished project (sheet, canon, shots)
    python3 scripts/light_test.py queue <test dir> [variants]              queue the frames (same seed per shot)
    python3 scripts/light_test.py report <test dir>                        face match, face vs scene brightness, grid

Variants (16 steps cfg 1, upsampler on, the sheet as the only reference):
  A  v1, as the merge test ran: who first, no light words for the person, the world style last
  B  v1 plus a "Lighting: ..." sentence for the shot (the words alone, at the end)
  C  scene first: the place, where its light comes from, the person placed in it and lit by it
  D  C with hexe's identity block instead of "use the sheet only for who she is"
  E  D plus one line in the upsampler's instructions: carry the person over, never the reference's light
"""
import json, os, shutil, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# the light in each shot as a planner would write it: the sources in the place, their side, color, how much shadow
LIGHTS = {
    "s02": "sodium street lamps behind her and to the right: a warm orange rim on her hair and cheek, the front of her face "
           "in soft shadow, faintly colored by the glow of the shop signs",
    "s03": "the glow of the city skyline behind her and one warm lamp on a water tank to the right, cool dim blue light from "
           "the low clouds, the front of her body mostly in shadow",
    "s04": "the green glow of the laundromat window on her left, a warm sodium street lamp high behind her on the right, "
           "steam catching the light, deep shadows between",
    "s05": "bright sodium street lamps far behind her: she is almost a silhouette, a warm rim of light along her hair and "
           "shoulders, her face dark",
    "s06": "one warm lamp to the side lighting half of her face, the other half in deep shadow, the cool blue glow of the city "
           "behind her",
    "s07": "green spill from the laundromat window on one side and warm sodium light from a street lamp on the other, the "
           "steam glowing between them",
}
VARIANTS = {"A": dict(style="v1", light=False, rw=False), "B": dict(style="v1", light=True, rw=False),
            "C": dict(style="scene", light=True, rw=False), "D": dict(style="scene_id", light=True, rw=False),
            "E": dict(style="scene_id", light=True, rw=True)}


def setup(src, dst, comfy_dir):
    os.makedirs(dst, exist_ok=True)
    for f in ("canon.json", "shots.json", "shots_resolved.json"):
        shutil.copyfile(os.path.join(src, f), os.path.join(dst, f))
    shutil.copytree(os.path.join(src, "refs"), os.path.join(dst, "refs"), dirs_exist_ok=True)
    cfg = json.load(open(os.path.join(src, "project.json")))
    cfg["name"] = os.path.basename(dst.rstrip("/"))
    cfg["comfy"] = dict(cfg.get("comfy") or {}, dir=comfy_dir, url=os.environ.get("COMFY_URL", "http://10.0.1.171:8188"))
    for k in ("input_subdir", "output_subdir"):
        cfg["comfy"].pop(k, None)
    json.dump(cfg, open(os.path.join(dst, "project.json"), "w"), indent=1)
    print("test project at", dst)


def shots(p):
    return [s for s in p.load("shots_resolved.json")["shots"] if s.get("chars") and s["id"] in LIGHTS]


def queue(dst, only=None):
    from nightshift.build import Builder
    from nightshift.project import Project
    p = Project(dst)
    b = Builder(p)
    st_path = os.path.join(dst, "light_state.json")
    st = json.load(open(st_path)) if os.path.exists(st_path) else {}
    prompts = {}
    for v, o in VARIANTS.items():
        if only and v not in only:
            continue
        for s in shots(p):
            s = dict(s, still="edit")
            s.pop("light", None)
            if o["light"]:
                s["light"] = LIGHTS[s["id"]]
            jp = b.sheet_frame_job(s, seed=s["seed"], tag=f"L{v}", style=o["style"], rewriter_light=o["rw"])
            job = json.load(open(jp, encoding="utf-8"))
            st[f"{v}_{s['id']}"] = p.client.queue_prompt(job)
            prompts[f"{v}_{s['id']}"] = next(n["inputs"]["value"] for n in job.values()
                                             if n.get("_meta", {}).get("title") == "ns_prompt")
    json.dump(st, open(st_path, "w"), indent=1)
    old = json.load(open(os.path.join(dst, "light_prompts.json"))) if os.path.exists(os.path.join(dst, "light_prompts.json")) else {}
    json.dump(dict(old, **prompts), open(os.path.join(dst, "light_prompts.json"), "w"), indent=1)
    print("queued", len(prompts))


def report(dst, order="ABCDE"):
    import numpy as np
    from nightshift import score
    from nightshift.project import Project
    p = Project(dst)
    c = p.client
    cv2 = score._cv()
    out = os.path.join(dst, "light_out"); os.makedirs(out, exist_ok=True)
    st = json.load(open(os.path.join(dst, "light_state.json")))
    texts = {}
    for name, pid in st.items():
        r = c.result(pid)
        if r["status"] != "success":
            print(name, r["status"], r.get("error")); continue
        f = os.path.join(out, name + ".png")
        if not os.path.exists(f):
            c.download([x for x in r["files"] if x["filename"].endswith(".png")][0], f)
        if r.get("texts"):
            texts[name] = str(r["texts"][0])
    json.dump(texts, open(os.path.join(out, "rewritten.json"), "w"), indent=1)
    sheet = p.path(json.load(open(p.path("canon.json")))["characters"]["lead"]["sheet"]["real"])
    refs = score.sheet_refs(sheet)

    def lit(path):
        """Face brightness over scene brightness (1 = the face as bright as the frame; studio-lit faces sit well above)."""
        im, fs = score.faces(cv2.imread(path))
        if not len(fs):
            return None
        x, y, w, h = [int(v) for v in fs[0][:4]]
        L = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)[:, :, 0].astype(float)
        face = L[max(0, y):y + h, max(0, x):x + w]
        return round(float(face.mean() / max(1.0, L.mean())), 2)
    shot_ids = [s["id"] for s in shots(p)]
    table = {}
    for v in order:
        for sid in shot_ids:
            f = os.path.join(out, f"{v}_{sid}.png")
            if os.path.exists(f):
                m = score.score_image(refs, f)
                table[(v, sid)] = (round(m, 2) if m is not None else None, lit(f))
    print("face match / face-to-scene brightness")
    print("variant " + "  ".join(f"{sid:>11}" for sid in shot_ids) + "   mean face  mean bright")
    for v in order:
        cells = [table.get((v, sid)) for sid in shot_ids]
        fm = [x[0] for x in cells if x and x[0] is not None]
        br = [x[1] for x in cells if x and x[1] is not None]
        print(f"{v:7} " + "  ".join(f"{(str(x[0]) + '/' + str(x[1])) if x else '-':>11}" for x in cells)
              + (f"   {np.mean(fm):.2f}" if fm else "   -") + (f"       {np.mean(br):.2f}" if br else ""))
    json.dump({f"{k[0]}_{k[1]}": v for k, v in table.items()}, open(os.path.join(out, "scores.json"), "w"), indent=1)
    F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = f"fontfile={F}:" if os.path.exists(F) else ""
    rows = []
    for v in order:
        ins, fl = [], ""
        for k, sid in enumerate(shot_ids):
            f = os.path.join(out, f"{v}_{sid}.png")
            ins += ["-i", f if os.path.exists(f) else sheet]
            sc = table.get((v, sid))
            lab = f"{v} {sid}  {sc[0] if sc else '-'}"
            fl += (f"[{k}:v]scale=400:225:force_original_aspect_ratio=increase,crop=400:225,drawtext={font}"
                   f"text='{lab}':x=6:y=6:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.6[a{k}];")
        row = os.path.join(out, f"row_{v}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex",
                        fl + "".join(f"[a{k}]" for k in range(len(shot_ids))) + f"hstack={len(shot_ids)}", "-frames:v", "1",
                        row], check=True)
        rows.append(row)
    grid = os.path.join(out, f"light_test_{order}.jpg")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *sum([["-i", r] for r in rows], []), "-filter_complex",
                    f"vstack={len(rows)}", "-q:v", "3", grid], check=True)
    print(grid)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "setup":
        setup(*sys.argv[2:5])
    elif cmd == "queue":
        queue(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        report(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "ABCDE")
