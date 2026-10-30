"""Nightshift as an MCP server: any agent that speaks MCP can run the whole pipeline.

    nightshift mcp --project-root ~/videos                       (stdio: Claude Code, Claude Desktop, Cursor, Hermes ...)
    nightshift mcp --http --host 0.0.0.0 --port 8765 --project-root ~/videos
                                                                  (streamable HTTP: an agent on another machine, e.g. a
                                                                   Mac mini running its own model, drives the GPU box)

Long steps (song analysis, assembly, overlay, finishing, a whole pass) run as background tasks: the tool returns a
task id at once and task_status() reports progress, so no client times out on a 40-minute render.
"""
import glob
import json
import os
import subprocess
import sys
import time
import uuid

try:   # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer as _Server, Image
except ImportError:  # 1.x
    from mcp.server.fastmcp import FastMCP as _Server, Image

from .project import Project, init as init_project

INSTRUCTIONS = """Nightshift makes music videos with a local ComfyUI (images: Flux 2 Klein, video: LTX 2.3, song: MiniMax Music 3).
A project is a folder: canon.json (characters, wardrobe, never-lists), shots.json (shot list), song/caption.md + song/lyrics.txt,
cut.json (the edit). The pass runs: sheets -> song -> analyze -> timeline -> stills -> sheetedits -> videos -> pick -> cut -> overlay -> finish.
Start with project_info. To run everything: pipeline_run, then poll pipeline_status every few minutes (renders take hours).
Mode 'director' stops at checkpoints (sheets_review, outfits_review, song_pick, stills_review, takes_review, pass_review): show the human the review packet
(view_image on contact sheets), apply their notes (write_doc / patch_shot / pick_take / edit_image), then pipeline_continue.
Mode 'yolo' stops only for character looks (unless project.json sheets.approve is false): you pick by face-match and lyric-coverage scores. Re-running only renders what changed.
Shot fields that matter: mode (ff|fflf|lipsync|t2v|reuse), anchor (first words of the lyric line a lip-sync shot starts on),
chars, world, framing (close|medium|wide), action, location, video (motion prompt; {lead} = the character's identity words),
seed, still ('edit' = identity-edited from the character sheet), takes (best-of-N), arrive_frame, first_frame/last_frame, expr.
Read docs/techniques.md in the repo for the craft (rescue first/last-frame, self-consistent last frames, relight edits)."""

ROOT = os.environ.get("NIGHTSHIFT_HOME")
COMFY = {"url": os.environ.get("NIGHTSHIFT_COMFY_URL") or None, "dir": os.environ.get("NIGHTSHIFT_COMFY_DIR") or None}
server = _Server("nightshift", instructions=INSTRUCTIONS)


def _project(project):
    if ROOT:
        path = os.path.abspath(os.path.join(ROOT, project))
        if os.path.commonpath([path, os.path.abspath(ROOT)]) != os.path.abspath(ROOT):
            raise ValueError("project must be inside the project root")
    else:
        path = os.path.abspath(os.path.expanduser(project))
    return Project(path)


def _safe(p, rel):
    path = os.path.abspath(os.path.join(p.root, rel))
    if os.path.commonpath([path, p.root]) != p.root:
        raise ValueError(f"{rel} is outside the project")
    return path


def _bg(p, argv, label):
    tid = time.strftime("%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
    os.makedirs(p.path("tasks"), exist_ok=True)
    log = p.path("tasks", f"{tid}.log")
    with open(log, "w") as fh:
        proc = subprocess.Popen([sys.executable, "-u", "-m", "nightshift", "-p", p.root, *argv], stdout=fh, stderr=subprocess.STDOUT,
                                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                start_new_session=os.name != "nt")
    p.save(f"tasks/{tid}.json", {"id": tid, "label": label, "argv": argv, "pid": proc.pid, "started": time.time()})
    return {"task_id": tid, "label": label, "log": p.rel(log)}


def _alive(pid):
    try:
        if os.name == "nt":
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True).stdout
            return str(pid) in out
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _tail(path, n=40):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()[-n:]
    except FileNotFoundError:
        return []


# ---- projects -------------------------------------------------------------------------------
@server.tool()
def projects() -> list:
    """Projects under the project root."""
    if not ROOT:
        return ["(no --project-root set: pass project folders as absolute paths)"]
    return sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(ROOT, "*", "project.json")))


@server.tool()
def project_init(project: str, mode: str = "director", comfy_url: str = "", comfy_dir: str = "") -> dict:
    """Create a project from the starter template. mode: director | yolo."""
    path = os.path.join(ROOT, project) if ROOT else project
    p = init_project(path, os.path.basename(path), comfy_url or COMFY["url"], comfy_dir or COMFY["dir"], mode=mode)
    return {"root": p.root, "output_subdir": p.output_subdir, "next": "fill canon.json, shots.json, song/caption.md, song/lyrics.txt"}


@server.tool()
def plan_format() -> str:
    """The production-plan format and rules for create_from_plan: read this first when you plan a video from an idea."""
    from . import agent
    return agent.SYSTEM


@server.tool()
def create_from_plan(plan: dict, name: str = "", length: str = "medium", aspect: str = "16:9", image_model: str = "flux2",
                     grade: str = "A2_portra_dusk_plus", overlay: bool = False, mode: str = "yolo") -> dict:
    """Make a whole project from a plan in plan_format's JSON shape (characters, worlds, song caption + lyrics, shots).
    length: short | medium | full. aspect: 16:9 | 9:16. image_model: flux2 | flux3. mode: yolo (runs to the end) | director
    (stops at checkpoints for the human in Nightshift Studio). Then call pipeline_run(project)."""
    from . import agent, studio
    if not ROOT:
        raise ValueError("start the server with --project-root")
    pl = agent.normalize(plan, length)
    nm = studio.slug(name or pl.get("title"))
    base, k = nm, 2
    while os.path.exists(os.path.join(ROOT, nm)):
        nm, k = f"{base}-{k}", k + 1
    p = agent.create_from_plan(os.path.join(ROOT, nm), pl, {"aspect": aspect, "image_model": image_model, "grade": grade,
                               "overlay": overlay, "mode": mode, "comfy_url": COMFY["url"], "comfy_dir": COMFY["dir"]})
    with open(p.path("studio.log"), "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')}  project planned by an agent over MCP: \"{pl.get('title')}\", {len(pl['shots'])} shots\n")
    return {"project": nm, "title": pl.get("title"), "shots": len(pl["shots"]), "characters": list(pl["characters"]),
            "next": f"pipeline_run(project='{nm}'), then poll pipeline_status every few minutes"}


@server.tool()
def project_info(project: str) -> dict:
    """Settings, pipeline state, what exists, and what to do next."""
    from . import comfy, pipeline
    p = _project(project)
    st = pipeline.state(p)
    count = lambda k, pat="*": len(p.renders(k, pat))
    shots = p.shots("shots_resolved.json" if os.path.exists(p.path("shots_resolved.json")) else "shots.json")
    return {"name": p.name, "mode": p.cfg["mode"], "comfy": p.cfg["comfy"]["url"], "pipeline": st, "queue": comfy.status(p)["counts"],
            "shots": len(shots), "stills": count("stills"), "clips": count("clips", "*.mp4"), "songs": count("songs"),
            "song_chosen": p.cfg.get("song"), "has_cut": os.path.exists(p.path("cut.json")),
            "passes": sorted(os.path.basename(x) for x in glob.glob(p.path("out", "pass*.mp4")) if "_cut" not in x)}


@server.tool()
def read_doc(project: str, name: str) -> str:
    """Read a project file (canon.json, shots.json, shots_resolved.json, cut.json, song/caption.md, song/lyrics.txt, out/pass01_notes.md ...)."""
    p = _project(project)
    with open(_safe(p, name), encoding="utf-8") as f:
        return f.read()


@server.tool()
def write_doc(project: str, name: str, content: str) -> str:
    """Write a project file. JSON files are validated before they are written."""
    p = _project(project)
    path = _safe(p, name)
    if name.endswith(".json"):
        json.loads(content)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    p.log("write_doc", name=name)
    return f"wrote {name} ({len(content)} chars)"


@server.tool()
def patch_shot(project: str, shot_id: str, fields: dict, file: str = "shots.json") -> dict:
    """Change fields of one shot (null deletes a field). Patch shots.json for lasting changes; shots_resolved.json for this
    pass only (it is regenerated when shots.json changes)."""
    return _project(project).patch_shot(shot_id, fields, file)


@server.tool()
def list_files(project: str, pattern: str = "clips/*.mp4", path: str = "") -> list:
    """Files in the project matching a glob (pattern, or path: "out/*.mp4", "stills/s02_*"), oldest first."""
    p = _project(project)
    return [p.rel(f) for f in sorted(glob.glob(_safe(p, path or pattern)), key=os.path.getmtime)]


@server.tool()
def view_image(project: str, path: str, max_width: int = 1600):
    """Look at a still or contact sheet (jpg/png); a video returns its middle frame."""
    from PIL import Image as PI
    p = _project(project)
    src = _safe(p, path)
    if src.lower().endswith((".mp4", ".mov", ".webm")):
        from .score import clip_frames
        import cv2
        fr = clip_frames(src, (0.5,))
        im = PI.fromarray(cv2.cvtColor(fr[0][1], cv2.COLOR_BGR2RGB))
    else:
        im = PI.open(src).convert("RGB")
    if im.width > max_width:
        im = im.resize((max_width, round(im.height * max_width / im.width)))
    out = p.path("review", "_view.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out, quality=85)
    return Image(path=out)


# ---- pipeline -------------------------------------------------------------------------------
@server.tool()
def pipeline_run(project: str, start: str = "", until: str = "", yolo: bool = False) -> dict:
    """Run the pass in the background (steps: song analyze timeline stills sheetedits videos pick cut overlay finish).
    Poll pipeline_status. In director mode it stops at checkpoints."""
    p = _project(project)
    argv = ["run"] + (["--from", start] if start else []) + (["--until", until] if until else []) + (["--yolo"] if yolo else [])
    r = _bg(p, argv, "pipeline")
    st = p.load("state.json", {})
    st["task"] = r["task_id"]
    p.save("state.json", st)
    return r


@server.tool()
def pipeline_status(project: str) -> dict:
    """Where the pass is: step, checkpoint waiting for review (with its packet of files), queue, recent log lines."""
    from . import comfy, pipeline
    p = _project(project)
    st = pipeline.state(p)
    out = {"state": st, "queue": comfy.status(p)}
    if st.get("task"):
        out["task"] = task_status(project, st["task"])
    return out


@server.tool()
def pipeline_continue(project: str, notes: str = "") -> dict:
    """Approve the current checkpoint (after applying the director's notes) and carry on in the background."""
    from . import pipeline
    p = _project(project)
    pipeline.approve(p, notes or None)
    return pipeline_run(project)


@server.tool()
def next_pass(project: str) -> dict:
    """Start pass N+1: checkpoints come back, renders and picks are kept, only changed shots re-render."""
    from . import pipeline
    return pipeline.new_pass(_project(project))


@server.tool()
def task_status(project: str, task_id: str) -> dict:
    """Status of a background task: running or finished, and the last lines of its log."""
    p = _project(project)
    t = p.load(f"tasks/{task_id}.json")
    if not t:
        return {"error": f"no task {task_id}"}
    running = _alive(t["pid"])
    return {"task_id": task_id, "label": t["label"], "running": running, "minutes": round((time.time() - t["started"]) / 60, 1),
            "log": _tail(p.path("tasks", f"{task_id}.log"))}


@server.tool()
def task_stop(project: str, task_id: str) -> str:
    """Stop a background task (queued ComfyUI jobs keep running; cancel them with cancel_jobs)."""
    import signal
    p = _project(project)
    t = p.load(f"tasks/{task_id}.json")
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(t["pid"]), "/T", "/F"], capture_output=True)
        else:
            os.killpg(t["pid"], signal.SIGTERM)
    except Exception as e:
        return f"could not stop: {e}"
    return "stopped"


# ---- character sheets -------------------------------------------------------------------------------
@server.tool()
def sheets_status(project: str) -> list:
    """Every character x world the shots need: approved sheet (if any), how it will be made (text or image), candidates."""
    from . import sheets
    return sheets.status(_project(project))


@server.tool()
def sheets_review(project: str, character: str, world: str) -> dict:
    """Rank a character's sheet candidates and make a contact sheet (look at it with view_image)."""
    from . import sheets
    p = _project(project)
    return {"ranked": sheets.rank(p, character, world), "sheet": sheets.sheet_grid(p, character, world)}


@server.tool()
def pick_sheet(project: str, character: str, world: str, file: str) -> str:
    """Approve a sheet candidate: saved as refs/sheets/<character>_<world>.png and written into canon.json."""
    from . import sheets
    p = _project(project)
    return sheets.pick(p, character, world, _safe(p, file))


# ---- song -------------------------------------------------------------------------------
@server.tool()
def song_jobs(project: str, seeds: list[int], caption: str = "", lyrics: str = "", submit: bool = True) -> dict:
    """Build (and queue) MiniMax Music 3 jobs, one per seed. Caption/lyrics default to song/caption.md and song/lyrics.txt."""
    from . import comfy, song
    p = _project(project)
    jobs = song.build_jobs(p, seeds, caption=caption or None, lyrics=lyrics or None)
    if submit:
        comfy.submit(p, jobs)
    return {"jobs": [p.rel(j) for j in jobs], "queued": submit}


@server.tool()
def song_choose(project: str, file: str) -> str:
    """Make a rendered song the project's song."""
    from . import song
    p = _project(project)
    return p.rel(song.choose(p, file))


@server.tool()
def analyze_song(project: str) -> dict:
    """Beat map + lyric timing (background task, a few minutes on CPU)."""
    return _bg(_project(project), ["analyze"], "analyze")


@server.tool()
def resolve_timeline(project: str) -> str:
    """Fit the shot list to the song: anchors, slots, frames, audio windows. Writes shots_resolved.json and cut.json."""
    from . import timeline
    return timeline.resolve(_project(project))


# ---- jobs -------------------------------------------------------------------------------
@server.tool()
def build_jobs(project: str, stage: str, ids: list[str] | None = None, picks: dict | None = None) -> dict:
    """Write ComfyUI jobs. stage: stills | sheetedits | edits | videos. picks {shot: still label} override the still a video uses."""
    from . import build
    return build.build(_project(project), stage, ids, picks)


@server.tool()
def make_takes(project: str, job: str, n: int = 4, tag: str = "t") -> list:
    """Clone a built job into n seeds (best-of-n)."""
    from . import takes
    return takes.takes(_project(project), job, n, None, tag)


@server.tool()
def identity_variants(project: str, ids: list[str], wordings: str = "AC", per_wording: int = 2, tag: str = "v") -> list:
    """Seed x wording grid of the character-sheet identity edit for these shots."""
    from . import build
    return build.variants(_project(project), ids, wordings, per_wording, tag)


@server.tool()
def edit_image(project: str, base: str, out_id: str, text: str, ref: str = "", ref2: str = "", seed: int = 1, submit: bool = True) -> dict:
    """Flux 2 edit: base image (+ reference, + second reference) + instruction. Refer to them as image 1 / image 2 / image 3."""
    from . import comfy, takes
    p = _project(project)
    job = takes.edit(p, _safe(p, base), out_id, seed, text, _safe(p, ref) if ref else None, _safe(p, ref2) if ref2 else None)
    if submit:
        comfy.submit(p, [job])
    return {"job": job, "queued": submit, "output": f"stills/{out_id}_edit_*.png"}


@server.tool()
def submit_jobs(project: str, jobs: list[str]) -> dict:
    """Queue job files (globs allowed, e.g. jobs/*_video_t*.json)."""
    from . import comfy
    p = _project(project)
    files = [f for pat in jobs for f in sorted(glob.glob(_safe(p, pat)))]
    added = comfy.submit(p, files)
    return {"queued": len(added), "jobs": [a["job"] for a in added]}


@server.tool()
def watch_jobs(project: str, seconds: int = 45) -> dict:
    """Wait up to `seconds` for queued jobs (collects outputs, retries OOM/stalls). Call again until nothing is open."""
    from . import comfy
    return comfy.watch(_project(project), timeout_s=seconds, on_event=lambda m: None)


@server.tool()
def queue_status(project: str) -> dict:
    """Open, finished and failed jobs of this project."""
    from . import comfy
    return comfy.status(_project(project))


@server.tool()
def cancel_jobs(project: str) -> dict:
    """Cancel this project's queued jobs and interrupt the running one."""
    from . import comfy
    p = _project(project)
    st = comfy.load_state(p)
    ids = [j["prompt_id"] for j in st["jobs"] if j["status"] in ("queued", "running")]
    c = p.client
    c.cancel(ids)
    for j in st["jobs"]:
        if j["status"] == "running":
            c.interrupt(j["prompt_id"])
        if j["status"] in ("queued", "running"):
            j["status"] = "cancelled"
    comfy.save_state(p, st)
    return {"cancelled": len(ids)}


@server.tool()
def comfy_health(project: str) -> dict:
    """Is ComfyUI up, which GPU, how much VRAM is free, what is in its queue."""
    p = _project(project)
    c = p.client
    s = c.system_stats()
    return {"devices": s.get("devices"), "queue": c.queue(), "log_seconds_since_write": c.log_age()}


@server.tool()
def workflows_list(project: str) -> list:
    """Workflows with their roles, outputs and any map problems."""
    from . import workflows as W
    p = _project(project)
    out = []
    for name in W.available(p.workflow_dirs()):
        wf = W.Workflow.load(name, p.workflow_dirs())
        out.append({"name": name, "kind": wf.kind, "roles": wf.roles(), "outputs": wf.outputs(), "problems": wf.check()})
    return out


# ---- review -------------------------------------------------------------------------------
@server.tool()
def rank_images(project: str, files: list[str], character: str, world: str = "real", sheet_out: str = "") -> list:
    """Face-match stills or clips against a character's sheet (globs allowed), best first; optional contact sheet."""
    from . import score
    p = _project(project)
    fl = [f for g in files for f in sorted(glob.glob(_safe(p, g)))]
    rows = score.rank(p, fl, character, world)
    if sheet_out:
        score.grid(_safe(p, sheet_out), [{"path": p.path(r["file"]), "face": r["face"]} for r in rows])
    return rows


@server.tool()
def rank_takes(project: str, shot_id: str) -> list:
    """All takes of a shot, best face match first (lip-sync shots also get mouth activity)."""
    from . import score
    return score.rank_takes(_project(project), shot_id)


@server.tool()
def takes_sheet(project: str, shot_id: str) -> str:
    """Contact sheet (first / middle / last frame) of every take of a shot. Look at it with view_image."""
    from . import review
    p = _project(project)
    return p.rel(review.takes_sheet(p, shot_id))


@server.tool()
def cut_report(project: str) -> list:
    """Face score of every person shot in the cut (spot identity drift)."""
    from . import score
    return score.cut_report(_project(project))


@server.tool()
def pick_take(project: str, shot_id: str, src: str, in_seconds: float | None = None, speed: float | None = None,
              beats: int | None = None, seconds: float | None = None) -> dict:
    """Use this clip for the shot in cut.json; optionally trim the head (in), change speed, or set the slot in beats/seconds."""
    from . import timeline
    f = {k: v for k, v in (("in", in_seconds), ("speed", speed), ("beats", beats), ("seconds", seconds)) if v is not None}
    return timeline.pick(_project(project), shot_id, src, **f)


@server.tool()
def assemble_cut(project: str, out: str = "out/cut.mp4") -> dict:
    """Cut the picked takes onto the song (background task)."""
    return _bg(_project(project), ["assemble", "--out", out], "assemble")


@server.tool()
def finish_video(project: str, cut: str, out: str, overlay: str = "", web_copy: bool = True) -> dict:
    """Grade + overlay + texture in chunks, plus a posting copy (background task)."""
    argv = ["finish", cut, out] + (["--overlay", overlay] if overlay else []) + (["--web"] if web_copy else [])
    return _bg(_project(project), argv, "finish")


@server.tool()
def review_copy(project: str, video: str, edl: str, out: str) -> dict:
    """Review copy with shot numbers burned in (background task)."""
    return _bg(_project(project), ["review", "numbered", video, edl, out], "review")


@server.tool()
def overlay_build(project: str, edl: str) -> dict:
    """Face tracks -> overlay data -> rendered HUD frames -> alpha chunks (background task chain)."""
    p = _project(project)
    script = ["overlay", "track"], ["overlay", "prep", "--edl", edl], ["overlay", "render"], ["overlay", "encode", "--out", "overlay/chunks"]
    tid = time.strftime("%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
    os.makedirs(p.path("tasks"), exist_ok=True)
    log = p.path("tasks", f"{tid}.log")
    cmd = " && ".join(" ".join([f'"{sys.executable}"', "-u", "-m", "nightshift", "-p", f'"{p.root}"', *s]) for s in script)
    with open(log, "w") as fh:
        proc = subprocess.Popen(cmd, shell=True, stdout=fh, stderr=subprocess.STDOUT, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    p.save(f"tasks/{tid}.json", {"id": tid, "label": "overlay", "argv": script, "pid": proc.pid, "started": time.time()})
    return {"task_id": tid, "chunks": "overlay/chunks/ov_%02d.webm"}


def main(http=False, host="127.0.0.1", port=8765, project_root=None, comfy_url=None, comfy_dir=None):
    global ROOT
    if project_root:
        ROOT = os.path.abspath(os.path.expanduser(project_root))
    if comfy_url:
        COMFY["url"] = comfy_url
    if comfy_dir:
        COMFY["dir"] = os.path.abspath(os.path.expanduser(comfy_dir))
    if not http:
        server.run("stdio")
        return
    try:
        server.run("streamable-http", host=host, port=port)
    except TypeError:   # SDK 1.x takes host/port as settings
        server.settings.host, server.settings.port = host, port
        server.run("streamable-http")


if __name__ == "__main__":
    main()
