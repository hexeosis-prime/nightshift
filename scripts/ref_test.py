"""One-shot reference frames vs the current still + face edit (hexe's method, Nov 18).

    python3 scripts/ref_test.py setup        project runs/ref-test: hexe's character sheet, 6 varied shots (16:9)
    python3 scripts/ref_test.py queue        B-E: FLUX 3 frames made straight from the sheet (+ a style reference)
    (A, the current way: nightshift -p runs/ref-test build stills, submit; build sheetedits, submit)
    python3 scripts/ref_test.py report       face match to the sheet, head turn, contact sheet

Variants (same seed per shot):
  A  current: Flux 2 still from text, then the Flux 2 identity edit with the sheet
  B  FLUX 3 from the sheet, 50 steps cfg 3.5, prompt rewriter on            (hexe's settings)
  C  FLUX 3 from the sheet, 16 steps cfg 1, rewriter on                     (the fast setting)
  D  as B, rewriter off, the prompt with <ref_image_0> / <ref_image_1> tags
  E  as B, rewriter off, the same prompt with "the first / second reference image" instead of the tags
"""
import json, os, shutil, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
PROJ = os.path.join(ROOT, "runs", "ref-test")
BIN = os.path.join(os.path.dirname(ROOT), "workflow_test_bin")
SHEET, STYLE = os.path.join(PROJ, "refs", "sheets", "lead_real.png"), os.path.join(PROJ, "refs", "style.png")

WHO = ("fair skin with dense natural freckles across her cheeks and large button nose, warm hazel eyes, defined brows, "
       "and shoulder-length wavy chestnut-brown hair with subtle lighter highlights")
OUTFIT = "the same fitted plain black short-sleeve crew-neck T-shirt from the reference, with the slim black trousers and black slip-on shoes"
SHOTS = [  # id, framing words, action/expression, location
    ("r1", "close-up", "She sings with passion, mouth open mid-note, eyes half closed, head tilted slightly back",
     "a rooftop at dusk strung with warm bulb lights, the city skyline soft behind her"),
    ("r2", "medium close-up in left profile", "She looks out over the city, serious and calm, wind lifting her hair",
     "a night city street with neon shop light and wet pavement"),
    ("r3", "medium shot", "She laughs out loud with her eyes crinkled, looking off to the side at a friend out of frame",
     "a retro diner booth with red vinyl seats and a chrome-edged table"),
    ("r4", "medium shot", "She walks toward the camera mid-stride, looking ahead, arms relaxed",
     "a sunny palm-lined Los Angeles sidewalk with low stucco buildings"),
    ("r5", "wide full-body shot", "She dances with both arms raised, spinning, hair flying",
     "an empty parking garage roof at sunset with painted lines and concrete barriers"),
    ("r6", "close-up in three-quarter view", "She looks down and away, pensive, lost in thought",
     "a city bus seat by a rain-streaked window at night, blurred street lights outside"),
]


def prompt(shot, tags=True):
    sid, framing, action, loc = shot
    r0, r1 = ("<ref_image_0>", "<ref_image_1>") if tags else ("the first reference image", "the second reference image")
    return (f"Create a photograph of the woman from {r0} reference image in a {framing} for a pop music video lifestyle "
            f"b-roll section. Preserve her exact identity: {WHO}. {action}. Dress her in {OUTFIT}. "
            f"The new location for the new image is {loc}. For the newly created image, match the image tone and style "
            f"from {r1}")


def setup():
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    shutil.copyfile(os.path.join(BIN, "test_00022_.png"), SHEET)
    shutil.copyfile(os.path.join(BIN, "x_drone_cu_h_00001_.png"), STYLE)
    a = json.load(open(os.path.join(ROOT, "runs", "gpu-a", "project.json")))
    a.update(name="ref-test", aspect="16:9", image_model="flux2", mode="yolo")
    for k in ("work_size", "crop", "final_size"):
        a.pop(k, None)
    json.dump(a, open(os.path.join(PROJ, "project.json"), "w"), indent=1)
    c = json.load(open(os.path.join(ROOT, "runs", "gpu-a", "canon.json")))
    lead = c["characters"]["lead"]
    lead.update(person=f"woman, late twenties, {WHO}",
                outfit={"close": "a fitted plain black crew-neck T-shirt",
                        "medium": "a fitted plain black short-sleeve crew-neck T-shirt, slim black trousers",
                        "wide": "a fitted plain black short-sleeve crew-neck T-shirt, slim black trousers, black slip-on shoes"},
                video_name="the woman with wavy chestnut-brown hair in a black T-shirt",
                signature="shoulder-length wavy chestnut-brown hair", edit_extra="")
    c["worlds"]["real"]["style"] = "candid 35mm film photograph, natural light"
    json.dump(c, open(os.path.join(PROJ, "canon.json"), "w"), indent=1)
    fr = {"close-up": "close", "close-up in three-quarter view": "close", "medium close-up in left profile": "close"}
    shots = [{"id": sid, "world": "real", "mode": "ff", "framing": fr.get(f, "wide" if "wide" in f else "medium"),
              "seed": 2000 + i, "chars": ["lead"], "still": "edit", "action": a, "location": l,
              "video": f"{a}. The camera holds."} for i, (sid, f, a, l) in enumerate(SHOTS)]
    json.dump({"shots": shots}, open(os.path.join(PROJ, "shots.json"), "w"), indent=1)
    print("project at", PROJ)


VARIANTS = {"B": dict(steps=50, cfg=3.5, rw=True, tags=True), "C": dict(steps=16, cfg=1.0, rw=True, tags=True),
            "D": dict(steps=50, cfg=3.5, rw=False, tags=True), "E": dict(steps=50, cfg=3.5, rw=False, tags=False)}


def queue(only=None):
    from nightshift.comfy import Comfy
    from nightshift.workflows import Workflow
    c = Comfy(os.environ.get("COMFY_URL", "http://10.0.1.171:8188"))
    st_path = os.path.join(PROJ, "ref_state.json")
    st = json.load(open(st_path)) if os.path.exists(st_path) else {}
    sheet, style = c.upload(SHEET, "ref_test"), c.upload(STYLE, "ref_test")
    for v, o in VARIANTS.items():
        if only and v not in only:
            continue
        for i, shot in enumerate(SHOTS):
            wf = Workflow.load("img_flux3", [os.path.join(ROOT, "workflows")]); wf.apply_defaults()
            wf.set("text_to_image", False); wf.use_refs(2)
            wf.set("image1", sheet); wf.set("image2", style)
            wf.set("prompt_enhancer", o["rw"])
            wf.set("prompt", prompt(shot, o["tags"]))
            wf.set("width", 1280); wf.set("height", 768); wf.set("steps", o["steps"]); wf.set("cfg", o["cfg"])
            wf.seed(2000 + i); wf.output(f"ref_test/{v}_{shot[0]}")
            st[f"{v}_{shot[0]}"] = c.queue_prompt(wf.to_api())
    json.dump(st, open(st_path, "w"), indent=1)
    print("queued", len(st))


def report():
    from nightshift import score
    from nightshift.comfy import Comfy
    c = Comfy(os.environ.get("COMFY_URL", "http://10.0.1.171:8188"))
    out = os.path.join(PROJ, "ref_out"); os.makedirs(out, exist_ok=True)
    st = json.load(open(os.path.join(PROJ, "ref_state.json")))
    times = {}
    for name, pid in st.items():
        r = c.result(pid)
        if r["status"] != "success":
            print(name, r["status"], r.get("error")); continue
        dst = os.path.join(out, name + ".png")
        if not os.path.exists(dst):
            c.download([f for f in r["files"] if f["filename"].endswith(".png")][0], dst)
        times[name] = r.get("seconds")
    for sid, *_ in SHOTS:   # A: the current way, the latest identity edit per shot
        eds = sorted(f for f in os.listdir(os.path.join(PROJ, "stills")) if f.startswith(f"{sid}_edit_"))
        if eds:
            shutil.copyfile(os.path.join(PROJ, "stills", eds[-1]), os.path.join(out, f"A_{sid}.png"))
    refs = score.sheet_refs(SHEET)
    cv2 = score._cv()

    def turn(path):   # head turn of the biggest face, in eye-distances (0 = frontal)
        _, fs = score.faces(cv2.imread(path))
        return round(score.yaw(fs[0]), 2) if len(fs) else None
    _, sfs = score.faces(cv2.imread(SHEET))
    sheet_yaws = sorted(round(score.yaw(f), 2) for f in sfs)
    table = {}
    for v in "ABCDE":
        for sid, *_ in SHOTS:
            f = os.path.join(out, f"{v}_{sid}.png")
            if not os.path.exists(f):
                continue
            m = score.score_image(refs, f)
            table[(v, sid)] = (round(m, 2) if m is not None else None, turn(f), times.get(f"{v}_{sid}"))
    print("sheet faces' head turn:", sheet_yaws)
    print("variant " + "  ".join(f"{sid:>16}" for sid, *_ in SHOTS) + "   mean")
    for v in "ABCDE":
        cells = [table.get((v, sid)) for sid, *_ in SHOTS]
        ms = [x[0] for x in cells if x and x[0] is not None]
        print(f"{v:7} " + "  ".join(f"{(str(x[0]) + ' yaw ' + str(x[1])) if x else '-':>16}" for x in cells)
              + f"   {sum(ms) / len(ms):.2f}" if ms else "")
    json.dump({f"{k[0]}_{k[1]}": v for k, v in table.items()}, open(os.path.join(out, "scores.json"), "w"), indent=1)
    # contact sheet: a row per variant
    F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    for v in "ABCDE":
        ins, fl = [], ""
        for k, (sid, *_) in enumerate(SHOTS):
            f = os.path.join(out, f"{v}_{sid}.png")
            ins += ["-i", f if os.path.exists(f) else SHEET]
            sc = table.get((v, sid))
            lab = f"{v} {sid}  {sc[0] if sc else '-'}"
            fl += (f"[{k}:v]scale=320:192:force_original_aspect_ratio=increase,crop=320:192,drawtext=fontfile={F}:"
                   f"text='{lab}':x=6:y=6:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.6[a{k}];")
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex",
                        fl + "".join(f"[a{k}]" for k in range(len(SHOTS))) + f"hstack={len(SHOTS)}", "-frames:v", "1",
                        os.path.join(out, f"row_{v}.png")], check=True)
    rows = [os.path.join(out, f"row_{v}.png") for v in "ABCDE"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *sum([["-i", r] for r in rows], []), "-filter_complex",
                    f"vstack={len(rows)}", "-q:v", "3", os.path.join(out, "ref_test_sheet.jpg")], check=True)
    print(os.path.join(out, "ref_test_sheet.jpg"))


if __name__ == "__main__":
    {"setup": setup, "queue": lambda: queue(sys.argv[2] if len(sys.argv) > 2 else None), "report": report}[sys.argv[1]]()
