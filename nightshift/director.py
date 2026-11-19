"""Checkpoint Mode's choices: what the director sees at each checkpoint, picking one option, and "reroll" (new options with
new seeds, the same brief) while the checkpoint stays open. Phase 2 of the plan (Nov 19): every checkpoint gets choose,
reroll, accept and go back.

    choices(project, checkpoint)  -> rows, one per thing to choose (a character, the song, a shot)
    pick(project, body)           -> make one option the chosen one
    reroll_jobs(project, body)    -> the jobs that make new options (rendered by the caller), and what to do after
"""
import json
import os
import shutil

from . import build as B

STILL_TAGS = ("v", "edit", "r")


def _from_sheet(b, s):
    """A character shot whose frames are made from the sheet (the builder's from_sheet() reads "still": "edit", which the
    stills step replaces with the chosen frame's label)."""
    return bool(s.get("chars")) and b.from_sheet(dict(s, still="edit"))


def _label(sid, path):
    """stills/s02_vC1_00001_.png -> vC1 (the still label the builder reads)."""
    return os.path.basename(path)[len(sid) + 1:].split("_")[0]


def _shot_desc(s):
    mode = {"lipsync": "singing", "ff": "moving", "fflf": "camera move", "t2v": "establishing"}.get(s.get("mode"), s.get("mode", ""))
    return f"{s.get('framing', '')} · {mode}" + (f" · {s['setup']}" if s.get("setup") else "")


def choices(project, checkpoint):
    """Rows for the stills and takes checkpoints (the sheets and song rows are built in app.choices)."""
    from . import score
    b = B.Builder(project)
    rows = []
    if checkpoint == "stills_review":
        for s in b.shots:
            if s.get("dropped") or s["mode"] not in B.STILL_MODES:
                continue
            if s.get("chars"):
                files = [f for f in project.renders("stills", f"{s['id']}_*") if _label(s["id"], f).startswith(STILL_TAGS)]
                if not files:
                    continue
                ranked = score.rank(project, files, s["chars"][0], s.get("world", "real"))
                cur = b.still_label(s)
                opts = [{"file": r["file"], "score": r["face"], "by": "face match", "label": _label(s["id"], r["file"])} for r in ranked]
            else:
                files = project.renders("stills", f"{s['id']}_*")
                if not files:
                    continue
                cur = _label(s["id"], files[-1])
                opts = [{"file": project.rel(f), "score": None, "by": "", "label": _label(s["id"], f)} for f in files[::-1]]
            rows.append({"kind": "still", "shot": s["id"], "desc": _shot_desc(s), "who": bool(s.get("chars")),
                         "picked_label": cur, "options": opts, "can_reroll": _from_sheet(b, s)})
    elif checkpoint == "takes_review":
        cut = project.load("cut.json", {"shots": []})
        for c in cut["shots"]:
            s = b.by_id.get(c["id"], {})
            clips = [f for f in project.renders("clips", f"{c['id']}_*.mp4") if not f.endswith("-audio.mp4")]
            if not clips:
                continue
            if s.get("chars") and len(clips) > 1:
                ranked = score.rank_takes(project, c["id"])
                keep = {project.rel(f) for f in clips}
                opts = [{"file": r["file"], "score": r["face"], "by": "face match"} for r in ranked if r["file"] in keep]
            else:
                opts = [{"file": project.rel(f), "score": None, "by": ""} for f in clips[::-1]]
            rows.append({"kind": "take", "shot": c["id"], "desc": _shot_desc(s), "picked_file": c.get("src"),
                         "options": opts, "can_reroll": os.path.exists(project.path("jobs", f"{c['id']}_video.json"))})
    return rows


def pick(project, body):
    """still: that frame becomes the shot's first frame (its old clips are moved aside, so the shot animates again);
    take: that clip goes in the cut."""
    kind, sid, f = body.get("kind"), body.get("shot"), body.get("file") or ""
    if kind == "still":
        label = _label(sid, f)
        b = B.Builder(project)
        if b.by_id.get(sid, {}).get("still") == label:
            return label
        project.patch_shot(sid, {"still": label}, "shots_resolved.json")
        picks = project.load("review/still_picks.json", {}) or {}      # kept across re-plans and passes (step_sheetedits)
        picks[sid] = label
        os.makedirs(project.path("review"), exist_ok=True)
        project.save("review/still_picks.json", picks)
        aside(project, sid)
        project.log("still_pick", shot=sid, still=label)
        return label
    if kind == "take":
        cut = project.load("cut.json")
        for c in cut["shots"]:
            if c["id"] == sid:
                c["src"], c["picked"] = f, True
        project.save("cut.json", cut)
        project.log("take_pick", shot=sid, src=f)
        return f
    raise ValueError(f"nothing to pick for {kind}")


def aside(project, sid):
    """Move a shot's clips (and their jobs' take files) into clips/_aside/: renders are never deleted."""
    moved = []
    for f in project.renders("clips", f"{sid}_*"):
        d = project.path("clips", "_aside")
        os.makedirs(d, exist_ok=True)
        shutil.move(f, os.path.join(d, os.path.basename(f)))
        moved.append(os.path.basename(f))
    if moved:
        cut = project.load("cut.json", {"shots": []})
        for c in cut.get("shots", []):
            if c["id"] == sid:
                c.pop("src", None), c.pop("picked", None), c.pop("takes_seen", None)
        if os.path.exists(project.path("cut.json")):
            project.save("cut.json", cut)
    return moved


def reroll_jobs(project, body):
    """New options for one row, with new seeds (the existing ones stay): (job paths, kind)."""
    from . import sheets as SH
    from . import song as SONG
    from . import takes as T
    kind = body.get("kind")
    if kind == "sheet":
        ch, w = body["char"], body["world"]
        have = len(SH.candidates(project, ch, w))
        n = SH.cfg(project)["candidates"]
        return [project.rel(j) for j in _sheet_jobs(project, ch, w, n, have)], kind
    if kind == "song":
        used = set()
        for f in os.listdir(project.path("jobs")) if os.path.isdir(project.path("jobs")) else []:
            if f.startswith("song_take_") and f.endswith(".json") and not f.endswith(".meta.json"):
                try:
                    used.add(int(f[len("song_take_"):-5]))
                except ValueError:
                    pass
        n = len(project.cfg.get("song_seeds") or [1, 2, 3])
        start = (max(used) if used else 0) + 1111
        seeds = [start + 101 * i for i in range(n)]
        return [project.rel(j) for j in SONG.build_jobs(project, seeds, max_seconds=project.cfg.get("song_max_seconds"))], kind
    if kind == "still":
        b = B.Builder(project)
        s = b.by_id[body["shot"]]
        n = len(project.renders("stills", f"{s['id']}_v*_*"))
        if not _from_sheet(b, s):
            raise ValueError("new frames for this shot come from the CLI (nightshift variants)")
        s = dict(s, still="edit")
        return [project.rel(b.sheet_frame_job(s, seed=int(s["seed"]) + 20000 + 1000 * (n + k), tag=f"vX{n + k}")) for k in range(2)], kind
    if kind == "take":
        sid = body["shot"]
        jp = project.path("jobs", f"{sid}_video.json")
        if not os.path.exists(jp):
            raise ValueError(f"shot {sid} has no video job yet")
        n = len(project.renders("clips", f"{sid}_*.mp4"))
        meta = json.load(open(jp[:-5] + ".meta.json"))
        return T.takes(project, jp, 1, base_seed=int(meta.get("seed", 1)) + 30000 + 1000 * n, tag=f"r{n}"), kind
    raise ValueError(f"nothing to reroll for {kind}")


def _sheet_jobs(project, ch, w, n, start):
    """n more sheet candidates, numbered after the ones there are."""
    from . import sheets as SH
    return SH.build(project, ch, w, n=n, start=start)
