"""One pass, end to end, with the human in the loop or not.

    song -> analyze -> timeline -> stills -> sheetedits -> videos -> pick -> cut -> overlay -> finish

director mode (default): the run stops at checkpoints and leaves a review packet in review/:
    song_pick      the rendered songs, with how much of the lyric sheet each one actually sings
    stills_review  contact sheets of first frames, ranked by face match
    takes_review   contact sheets of every take; the cut already points at the best-scoring one
    pass_review    out/passNN.mp4 + a numbered review copy + passNN_notes.md
  The director answers in notes; the agent patches shots.json / cut.json (or new stills), and `nightshift run`
  again only renders what changed. If the first pass is loved, the first pass is the final pass.
yolo mode: no stops. The agent picks the song with the best lyric coverage, the identity edit and the take with the
  best face match, and delivers a finished pass.

Every step is idempotent: it skips shots whose renders already exist, so re-running after a fix is cheap.
"""
import json
import os
import time

from . import build as B
from . import comfy as C
from .project import Project

STEPS = ["sheets", "song", "analyze", "timeline", "stills", "sheetedits", "videos", "check", "pick", "cut", "overlay", "finish"]
CHECKPOINTS = {"song": "song_pick", "sheetedits": "stills_review", "pick": "takes_review", "finish": "pass_review"}
LOOKS = ("sheets_review", "outfits_review")      # character looks: approved once, kept across passes


class Stop(Exception):
    pass


class Paused(Exception):
    """run(..., seconds=N) ran out of time while ComfyUI still has jobs: run again to carry on."""


_DEADLINE = {}


def _remaining(project):
    d = _DEADLINE.get(project.root)
    return None if d is None else max(1.0, d - time.time())


def _watch(project, on_event):
    res = C.watch(project, timeout_s=_remaining(project), on_event=on_event)
    if res.get("open"):
        raise Paused(f"{len(res['open'])} job(s) still rendering")
    return res


def state(project):
    st = project.load("state.json", None) or {}
    for k, v in (("pass", 1), ("done", []), ("waiting", None), ("history", [])):
        st.setdefault(k, v)        # a state.json written by hand or by an older run may lack any of these
    return st


def save_state(project, st):
    project.save("state.json", st)


def _pass_name(st):
    return f"pass{st['pass']:02d}"


def _run_jobs(project, paths, on_event):
    if not paths:
        return
    on_event(f"rendering {len(paths)} job(s)")
    C.submit(project, paths)
    res = _watch(project, on_event)
    if res["failed"]:
        on_event(f"{len(res['failed'])} job(s) failed: " + "; ".join(f"{f['job']}: {f['error']}" for f in res["failed"][:5]))


def _shots(project):
    return project.shots("shots_resolved.json" if os.path.exists(project.path("shots_resolved.json")) else "shots.json")


def _checkpoint(project, st, step, on_event, packet, name=None, even_in_yolo=False):
    name = name or CHECKPOINTS.get(step)
    if not name or (project.cfg.get("mode") == "yolo" and not even_in_yolo):
        return
    if name in st.get("approved", []):
        return
    st["waiting"] = {"checkpoint": name, "packet": packet, "since": time.strftime("%Y-%m-%d %H:%M")}
    save_state(project, st)
    on_event(f"CHECKPOINT {name}: review {', '.join(packet) if packet else '(see review/)'} then run `nightshift continue`")
    raise Stop(name)


# ---- steps -------------------------------------------------------------------------------
def step_sheets(project, st, on_event):
    """Character sheets before anything else. Stops for the director (and in yolo mode too while sheets.approve is on)."""
    from . import sheets as SH
    k = SH.cfg(project)
    need = [(ch, ws) for ch, ws in SH.worlds(project).items() if any(not SH.sheet_path(project, ch, w) for w in ws)]
    if not need:
        return []
    stop = project.cfg.get("mode") != "yolo" or k["approve"]
    for phase, name in ((0, "sheets_review"), (1, "outfits_review")):
        todo = []
        for ch, ws in need:
            if phase == 0:
                todo.append((ch, ws[0], None))
            else:
                first = SH.sheet_path(project, ch, ws[0])
                todo += [(ch, w, project.path(first)) for w in ws[1:] if first]
        todo = [(ch, w, prim) for ch, w, prim in todo if not SH.sheet_path(project, ch, w)]
        if not todo:
            continue
        jobs = []
        for ch, w, prim in todo:
            if not SH.candidates(project, ch, w):
                jobs += SH.build(project, ch, w, primary=prim)
        _run_jobs(project, jobs, on_event)
        if stop and name not in st.get("approved", []):
            packet = [g for g in (SH.sheet_grid(project, ch, w) for ch, w, _ in todo) if g]
            on_event("pick a sheet with `nightshift sheets pick <character> <world> <file>`; anything not picked gets the best-scoring one")
            _checkpoint(project, st, "sheets", on_event, packet, name=name, even_in_yolo=True)
        for ch, w, _ in todo:                         # approved (or yolo): anything still unpicked gets the best candidate
            if SH.sheet_path(project, ch, w):
                continue
            ranked = SH.rank(project, ch, w)
            if ranked:
                SH.pick(project, ch, w, ranked[0]["file"])
                on_event(f"sheet {ch} / {w}: {ranked[0]['file']} ({ranked[0]['by']} {ranked[0]['score']})")
    return []


def step_song(project, st, on_event):
    from . import lyrics, song
    try:
        song.song_path(project)
        return []
    except FileNotFoundError:
        pass
    rendered = project.renders("songs", "*.mp3") + project.renders("songs", "*.wav") + project.renders("songs", "*.flac")
    if not rendered:
        seeds = project.cfg.get("song_seeds", [101, 202, 303, 404])
        _run_jobs(project, song.build_jobs(project, seeds, max_seconds=project.cfg.get("song_max_seconds")), on_event)
        rendered = project.renders("songs", "*.mp3") + project.renders("songs", "*.wav") + project.renders("songs", "*.flac")
    if not rendered:
        raise RuntimeError("no songs rendered; check ComfyUI and the song workflow")
    sheet = lyrics.sheet_lines(open(project.path("song", "lyrics.txt"), encoding="utf-8").read())
    rows = []
    for f in rendered:
        wj = project.path("review", os.path.basename(f) + ".words.json")
        if not os.path.exists(wj):
            lyrics.transcribe(f, wj, prompt=". ".join(sheet[:6]))
        cov = lyrics.coverage(sheet, json.load(open(wj))["words"])
        rows.append({"file": project.rel(f), "lyric_coverage": cov})
        on_event(f"song {os.path.basename(f)}: sings {cov:.0%} of the lyric sheet")
    rows.sort(key=lambda r: -r["lyric_coverage"])
    project.save("review/songs.json", {"songs": rows})
    if project.cfg.get("mode") == "yolo":
        song.choose(project, rows[0]["file"])
        on_event(f"picked {rows[0]['file']}")
        return []
    _checkpoint(project, st, "song", on_event, ["review/songs.json"] + [r["file"] for r in rows])
    return []


def step_analyze(project, st, on_event):
    from . import lyrics
    if os.path.exists(project.path("song", "lines.json")) and os.path.exists(project.path("song", "beatmap.json")):
        return []
    r = lyrics.analyze(project)
    on_event(f"song: {r['duration_s']} s, {r['bpm']} bpm, {r['lines_timed']}/{r['lines_on_sheet']} lyric lines timed, coverage {r['coverage']:.0%}")
    return []


def step_timeline(project, st, on_event):
    from . import timeline
    if os.path.exists(project.path("shots_resolved.json")) and os.path.getmtime(project.path("shots_resolved.json")) >= os.path.getmtime(project.path("shots.json")):
        return []
    on_event(timeline.resolve(project))
    return []


def _has_still(project, s, label):
    return bool(project.renders("stills", f"{s['id']}_{label}_*"))


def step_stills(project, st, on_event):
    b = B.Builder(project)
    need = []
    for s in b.shots:
        if s.get("dropped") or s["mode"] not in B.STILL_MODES or s.get("still_from") or s.get("first_frame"):
            continue
        base = s.get("edit_base") if s.get("still") == "edit" else b.still_label(s)
        if not _has_still(project, s, base or b.default_model(s)) and not _has_still(project, s, b.still_label(s)):
            need.append(s["id"])
    res = b.run("stills", need) if need else {"written": [], "skipped": []}
    _run_jobs(project, res["written"], on_event)
    return res["written"]


def step_sheetedits(project, st, on_event):
    from . import score
    b = B.Builder(project)
    todo = [s for s in b.shots if s.get("chars") and s.get("still") == "edit" and s["mode"] in B.STILL_MODES and not s.get("dropped")
            and not _has_still(project, s, "edit")]
    yolo = project.cfg.get("mode") == "yolo"
    written = []
    for s in todo:
        if yolo and project.cfg.get("yolo_variants", True):
            written += B.variants(project, [s["id"]], "AC", 2, tag="v")
        else:
            written.append(project.rel(b.sheet_job(s)))
    _run_jobs(project, written, on_event)
    packet = []
    if yolo:
        for s in todo:
            cands = project.renders("stills", f"{s['id']}_v*_*")
            if not cands:
                continue
            ranked = score.rank(project, cands, s["chars"][0], s.get("world", "real"))
            best = ranked[0]["file"]
            label = os.path.basename(best)[len(s["id"]) + 1:].split("_")[0]
            project.patch_shot(s["id"], {"still": label}, "shots_resolved.json")
            on_event(f"{s['id']}: identity edit {label} (face {ranked[0]['face']})")
    else:
        os.makedirs(project.path("review"), exist_ok=True)
        people = [s for s in b.shots if s.get("chars") and s["mode"] in B.STILL_MODES and not s.get("dropped")]
        for ch in sorted({s["chars"][0] for s in people}):
            rows = []
            for s in people:
                if s["chars"][0] != ch:
                    continue
                files = project.renders("stills", f"{s['id']}_{b.still_label(s)}_*")
                if files:
                    rows += score.rank(project, files[-1:], ch, s.get("world", "real"))
            if rows:
                out = project.path("review", f"stills_{ch}.jpg")
                score.grid(out, [{"path": project.path(r["file"]), "face": r["face"]} for r in rows])
                packet.append(project.rel(out))
        _checkpoint(project, st, "sheetedits", on_event, packet)
    return written


def step_videos(project, st, on_event):
    from . import takes as T
    b = B.Builder(project)
    need = [s["id"] for s in b.shots if not s.get("dropped") and s["mode"] in ("ff", "fflf", "lipsync", "t2v")
            and not project.renders("clips", f"{s['id']}_*.mp4")]
    res = b.run("videos", need) if need else {"written": [], "skipped": []}
    for sk in res["skipped"]:
        on_event("skipped " + sk)
    jobs = []
    for jp in res["written"]:
        meta = json.load(open(project.path(jp[:-5] + ".meta.json")))
        s = b.by_id[meta["shot"]]
        n = int(s.get("takes", project.cfg["takes"]["complex"] if s.get("complex") else project.cfg["takes"]["default"]))
        jobs += T.takes(project, jp, n, tag="t") if n > 1 else [jp]
    _run_jobs(project, jobs, on_event)
    return jobs


def step_check(project, st, on_event):
    """Burned-in text: every take is checked before the cut; a shot with no clean take gets a new take with a new seed
    (project.json qc.retakes, default 2). Flagged takes are never cut in while a clean one exists."""
    from . import qc
    from . import takes as T
    if not project.cfg.get("qc", {}).get("text", True):
        return []
    if not qc.available():
        on_event("WARN text check skipped: models/text_det.onnx missing (python scripts/get_models.py)")
        return []
    res = project.load("review/qc.json", {}) or {}
    retakes = int(project.cfg.get("qc", {}).get("retakes", 2))
    b = B.Builder(project)
    for rnd in range(retakes + 1):
        bad = []
        for s in b.shots:
            if s.get("dropped") or s["mode"] not in ("ff", "fflf", "lipsync", "t2v"):
                continue
            clips = project.renders("clips", f"{s['id']}_*.mp4")
            for c in clips:
                k = os.path.basename(c)
                if k not in res:
                    res[k] = qc.burned_text(c)
                    if res[k]["text"]:
                        on_event(f"text check: burned-in text in {k}")
            if clips and all(res[os.path.basename(c)]["text"] for c in clips):
                bad.append(s)
        project.save("review/qc.json", res)
        if not bad or rnd == retakes:
            break
        on_event(f"text check: new take for {', '.join(s['id'] for s in bad)}")
        jobs = []
        for s in bad:
            jp = project.path("jobs", f"{s['id']}_video.json")
            if os.path.exists(jp):
                jobs += T.takes(project, jp, 1, base_seed=int(s["seed"]) + 7000 + 1000 * rnd, tag=f"q{rnd}")
        _run_jobs(project, jobs, on_event)
    if bad:
        on_event(f"WARN text still burned into {', '.join(s['id'] for s in bad)} after {retakes} new take(s): look at them in the takes review")
    return []


def step_pick(project, st, on_event):
    from . import review, score, timeline
    if not os.path.exists(project.path("cut.json")):
        raise RuntimeError("no cut.json: run the timeline step")
    cut = project.load("cut.json")
    before = json.dumps(cut, sort_keys=True)
    b = B.Builder(project)
    packet = []
    for c in cut["shots"]:
        if c.get("src") and c.get("picked"):
            continue
        s = b.by_id.get(c["id"], {})
        if s.get("mode") == "reuse" and s.get("src"):
            c["src"] = s["src"]
            continue
        clips = project.renders("clips", f"{c['id']}_*.mp4")
        if not clips:
            continue
        from .qc import flagged
        bad = flagged(project)
        clean = [f for f in clips if os.path.basename(f) not in bad] or clips
        seen = f"{len(clips)}:{os.path.basename(clips[-1])}"
        if c.get("src") and c.get("takes_seen") == seen and os.path.exists(project.path(c["src"])):
            continue                     # same takes as last time: keep the pick
        c["takes_seen"] = seen
        if s.get("chars") and len(clean) > 1:
            keep = {project.rel(f) for f in clean}
            ranked = [r for r in score.rank_takes(project, c["id"]) if r["file"] in keep]
            c["src"] = ranked[0]["file"]
            c["score"] = ranked[0]["face"]
        else:
            c["src"] = project.rel(clean[-1])
        if len(clips) > 1 and project.cfg.get("mode") != "yolo":
            packet.append(project.rel(review.takes_sheet(project, c["id"])))
    if json.dumps(cut, sort_keys=True) != before:     # untouched cut keeps its mtime, so cut/finish can skip
        project.save("cut.json", cut)
    missing = [c["id"] for c in cut["shots"] if not c.get("src")]
    if missing:
        on_event(f"no clip yet for: {', '.join(missing)}")
    if packet:                                   # one take per shot (the short profile): nothing to choose between
        _checkpoint(project, st, "pick", on_event, packet)
    return []


def step_cut(project, st, on_event):
    from .assemble import assemble
    out = project.path("out", f"{_pass_name(st)}_cut.mp4")
    os.makedirs(project.path("out"), exist_ok=True)
    if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(project.path("cut.json")):
        return [project.rel(out)]
    r = assemble(project.path("cut.json"), out, on_event=on_event)
    for w in r["warnings"]:
        on_event("WARN " + w)
    return [project.rel(out)]


def step_overlay(project, st, on_event):
    from . import overlay as O
    if not project.cfg.get("overlay", {}).get("enabled"):
        return []
    import shutil
    if not (shutil.which("node") and shutil.which("npm")):
        on_event("WARN lyric HUD skipped: Node.js (node + npm) not found; install it from nodejs.org to get the overlay")
        return []
    pn = _pass_name(st)
    edl = project.path("out", f"{pn}_cut_edl.csv")
    O.track(project, on_event=on_event)
    faces = O.mapfaces(project, edl)
    r = O.prep(project, edl, faces)
    on_event(f"overlay data: {r['lines']} lines, sections {r['sections']}")
    frames = project.path("overlay", "frames")
    O.render(r["out"], frames)
    O.encode(frames, project.path("overlay", pn))
    return []


def step_finish(project, st, on_event):
    from . import finish as F
    from . import review
    pn = _pass_name(st)
    cut_mp4 = project.path("out", f"{pn}_cut.mp4")
    out = project.path("out", f"{pn}.mp4")
    fcfg, gcfg = project.cfg["finish"], project.cfg["grade"]
    ov = project.path("overlay", pn, "ov_%02d.webm") if project.cfg.get("overlay", {}).get("enabled") else None
    if ov and not os.path.exists(ov % 0):
        ov = None                                   # the HUD was skipped or failed: finish without it
    ht = fcfg.get("halftone")
    if ht == "auto":
        ht = project.path("overlay", "halftone.png")
        if not os.path.exists(ht):
            F.make_halftone(ht, tuple(project.cfg["final_size"]))
    rv = project.path("review", f"{pn}_review_numbered.mp4")
    fresh = lambda p: os.path.exists(p) and os.path.getmtime(p) >= os.path.getmtime(cut_mp4)
    if not (fresh(out) and fresh(rv)):         # already finished from this cut: nothing to redo
        F.finish(cut_mp4, out, gcfg["look"], gcfg.get("lifts", []), ov, ht, fcfg.get("grain", 9), fcfg["chunk_seconds"], on_event=on_event)
        review.numbered(out, project.path("out", f"{pn}_cut_edl.csv"), rv, on_event=on_event)
    notes = project.path("out", f"{pn}_notes.md")
    if not os.path.exists(notes):
        with open(notes, "w", encoding="utf-8") as f:
            f.write(f"# {pn}\n\nFiles: out/{pn}.mp4 (master) · review/{pn}_review_numbered.mp4\nCut: cut.json\n\n"
                    "Shot notes (numbers as burned into the review copy):\n\n")
    packet = [project.rel(out), project.rel(rv), project.rel(notes)]
    on_event(f"pass ready: {project.rel(out)}")
    _checkpoint(project, st, "finish", on_event, packet)
    return packet


FUNCS = {"sheets": step_sheets, "song": step_song, "analyze": step_analyze, "timeline": step_timeline, "stills": step_stills,
         "sheetedits": step_sheetedits, "videos": step_videos, "check": step_check, "pick": step_pick, "cut": step_cut,
         "overlay": step_overlay, "finish": step_finish}


def run(project: Project, start=None, until=None, on_event=print, seconds=None):
    """seconds: stop (cleanly, nothing lost) after about this long while ComfyUI is still rendering; run again to carry on."""
    st = state(project)
    if st.get("waiting"):
        on_event(f"waiting at checkpoint {st['waiting']['checkpoint']}: run `nightshift continue` (or approve) first")
        return st
    if seconds:
        _DEADLINE[project.root] = time.time() + seconds
    try:
        return _run(project, st, start, until, on_event)
    except Paused as e:
        on_event(f"paused: {e}; run again to carry on")
        return state(project)
    finally:
        _DEADLINE.pop(project.root, None)


def _run(project, st, start, until, on_event):
    if any(j["status"] in ("queued", "running") for j in C.load_state(project)["jobs"]):
        on_event("picking up jobs already queued on ComfyUI")       # a restarted run never queues the same work twice
        _watch(project, on_event)
    steps = STEPS[STEPS.index(start):] if start else STEPS
    if until:
        steps = steps[:steps.index(until) + 1]
    for name in steps:
        on_event(f"== {name}")
        st["step"] = name
        save_state(project, st)
        try:
            FUNCS[name](project, st, on_event)
        except Stop:
            return state(project)
        st.setdefault("history", []).append({"step": name, "t": time.strftime("%Y-%m-%d %H:%M:%S")})
        save_state(project, st)
    if until and until != STEPS[-1]:
        on_event(f"stopped after {until}")
        return st
    st["step"] = "done"
    save_state(project, st)
    on_event(f"{_pass_name(st)} done")
    return st


def approve(project, notes=None):
    """Clear the current checkpoint so the next run carries on past it."""
    st = state(project)
    w = st.get("waiting")
    if not w:
        return st
    st.setdefault("approved", []).append(w["checkpoint"])
    st["waiting"] = None
    if notes:
        st.setdefault("notes", []).append({"checkpoint": w["checkpoint"], "notes": notes, "t": time.strftime("%Y-%m-%d %H:%M")})
    save_state(project, st)
    return st


def new_pass(project):
    """Start the next pass: checkpoints come back, pass number goes up. Renders and picks are kept."""
    st = state(project)
    st["pass"] = st.get("pass", 1) + 1
    st["approved"] = [c for c in st.get("approved", []) if c in ("song_pick",) + LOOKS]
    st["waiting"] = None
    st["step"] = None
    save_state(project, st)
    return st
