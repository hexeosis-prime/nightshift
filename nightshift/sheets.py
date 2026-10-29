"""Character reference sheets, made before any other frame.

A sheet is one image per character and world: a full-body front view (face covered by a white circle, like an anonymized
casting photo), a full-body back view, and a macro close-up of the face, on seamless grey. Every identity
edit uses it as image 2, and the face scorer compares every still and take against it. Locking these first is the single
biggest lesson of the first video.

Two ways in, both Flux 2 Klein graphs with the sheet language built in:
  sheet_from_text   from the character's written description (canon.json person + the wide outfit for the world)
  sheet_from_image  from a picture of the character (canon.json "reference": "refs/<file>"), reformatted into a sheet
Director mode uses the picture when there is one. Yolo mode uses the description (project.json sheets.yolo_source).

For a character who appears in more than one world with a different outfit, the first world's approved sheet is edited
into the other outfits, so the face, hair and body stay the same person.

Approved sheets are saved as refs/sheets/<character>_<world>.png and written into canon.json, ready for reuse.
"""
import os
import shutil

DEFAULTS = {"candidates": 3, "approve": True, "yolo_source": "text", "seed": 7001}


def cfg(project):
    return {**DEFAULTS, **(project.cfg.get("sheets") or {})}


def _char(project, key):
    from .build import Builder
    return Builder(project, "shots.json").char(key)


def worlds(project):
    """{character: [worlds it appears in]}; the default world first when present."""
    canon = project.canon
    default = canon.get("default_world", "real")
    shots = project.shots("shots_resolved.json" if os.path.exists(project.path("shots_resolved.json")) else "shots.json")
    out = {}
    for s in shots:
        if s.get("dropped"):
            continue
        w = s.get("world") or default
        for c in list(s.get("chars") or []) + ([s["add"]["char"]] if s.get("add") else []):
            if c in canon.get("characters", {}):
                out.setdefault(c, [])
                aw = s["add"].get("world", w) if s.get("add") and s["add"]["char"] == c else w
                if aw not in out[c]:
                    out[c].append(aw)
    return {c: sorted(ws, key=lambda w, ws=ws: (w != default, ws.index(w))) for c, ws in out.items()}


def sheet_path(project, ch, world):
    p = ((project.canon["characters"][ch].get("sheet") or {}).get(world))
    return p if p and os.path.exists(project.path(p)) else None


def source(project, ch):
    c = project.canon["characters"][ch]
    ref = c.get("reference")
    if not (ref and os.path.exists(project.path(ref))):
        return "text"
    if project.cfg.get("mode") == "yolo" and cfg(project)["yolo_source"] == "text":
        return "text"
    return "image"


def description(project, ch, world):
    c = _char(project, ch)
    outfit = (c.get(f"outfit_{world}") or c.get("outfit") or {}).get("wide", "")
    pron = c["pronoun"].capitalize()
    verb = "are" if c["pronoun"] == "they" else "is"
    text = f"The character is {c.get('person', 'a person')}."
    if outfit:
        text += f" {pron} {verb} wearing {outfit}."
    return text + "\n\n"


def candidates(project, ch, world):
    return [p for p in project.renders("sheets", f"{ch}_{world}_*") if p.lower().endswith((".png", ".jpg", ".webp"))]


def build(project, ch, world, n=None, primary=None):
    """n candidate jobs for one character + world. primary: an approved sheet of the same character to dress differently."""
    k = cfg(project)
    n = n or k["candidates"]
    keys = sorted(project.canon["characters"])
    base = int(k["seed"]) + 100 * keys.index(ch) + 10 * (0 if not primary else 1)
    jobs = []
    for i in range(n):
        seed = base + 1000 * i
        if primary:
            wf = project.workflow("edit2")
            wf.apply_defaults()
            img = project.stage_input(primary, f"sheet_{ch}_primary.png")
            c = _char(project, ch)
            outfit = (c.get(f"outfit_{world}") or c.get("outfit") or {}).get("wide", "")
            wf.set("image1", img)
            wf.set("image2", img)
            wf.set("prompt", "Modify image 1. Keep the person exactly the same: face, facial structure, hair, body proportions and pose in "
                             "every view, the three-view layout, the white circle over the face in the front view, the seamless grey "
                             f"background and the lighting. Change only the clothing, in every view, to: {outfit}.")
            tag, kind = f"o{i}", "outfit"
        else:
            src = source(project, ch)
            if src == "image":
                wf = project.workflow("sheet_image")
                wf.apply_defaults()
                ref = project.canon["characters"][ch]["reference"]
                wf.set("image1", project.stage_input(ref, f"ref_{ch}{os.path.splitext(ref)[1]}"))
            else:
                wf = project.workflow("sheet_text")
                wf.apply_defaults()
                wf.set("description", description(project, ch, world))
            never = project.canon["characters"][ch].get("never")
            if never:
                wf.append("negative", ", " + never)
            tag, kind = f"c{i}", src
        wf.seed(seed)
        wf.output(project.prefix("sheets", f"{ch}_{world}_{tag}"))
        jobs.append(wf.save(project.path("jobs", f"sheet_{ch}_{world}_{tag}.json"),
                            {"kind": "sheet", "char": ch, "world": world, "seed": seed, "source": kind}))
    return jobs


def rank(project, ch, world, files=None):
    """Best first. A first-world sheet is scored on its face (one clear, large, confident detection); an outfit variant on how
    closely its face matches the approved first-world sheet."""
    from . import score
    files = files or candidates(project, ch, world)
    ws = worlds(project).get(ch, [world])
    primary = sheet_path(project, ch, ws[0]) if ws and ws[0] != world else None
    rows = []
    if primary:
        refs = score.sheet_refs(project.path(primary))
        for f in files:
            s = score.score_image(refs, f) if refs else None
            rows.append({"file": project.rel(f), "score": None if s is None else round(s, 3), "by": "match to " + ws[0]})
    else:
        for f in files:
            q = score.face_quality(f)
            rows.append({"file": project.rel(f), "score": q, "by": "face quality"})
    return sorted(rows, key=lambda r: -(r["score"] if r["score"] is not None else -1))


def pick(project, ch, world, file):
    """Approve a sheet: refs/sheets/<ch>_<world>.png, and canon.json points at it."""
    src = file if os.path.isabs(file) else project.path(file)
    dst_rel = f"refs/sheets/{ch}_{world}{os.path.splitext(src)[1] or '.png'}"
    os.makedirs(project.path("refs", "sheets"), exist_ok=True)
    shutil.copyfile(src, project.path(dst_rel))
    canon = project.load("canon.json")
    canon["characters"][ch].setdefault("sheet", {})[world] = dst_rel
    project.save("canon.json", canon)
    project.log("sheet_pick", char=ch, world=world, src=project.rel(src), sheet=dst_rel)
    return dst_rel


def sheet_grid(project, ch, world):
    from . import score
    rows = rank(project, ch, world)
    if not rows:
        return None
    out = project.path("review", f"sheets_{ch}_{world}.jpg")
    os.makedirs(project.path("review"), exist_ok=True)
    score.grid(out, [{"path": project.path(r["file"]), "face": r["score"]} for r in rows], cols=2, cell=(800, 480))
    return project.rel(out)


def status(project):
    out = []
    for ch, ws in worlds(project).items():
        for i, w in enumerate(ws):
            out.append({"char": ch, "world": w, "sheet": sheet_path(project, ch, w), "first_world": i == 0,
                        "source": source(project, ch) if i == 0 else "outfit edit of " + ws[0],
                        "candidates": [project.rel(p) for p in candidates(project, ch, w)]})
    return out
