"""nightshift command line. Every command takes -p/--project (default: the current folder)."""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

from .project import Project, init as init_project


def _p(a):
    return Project(a.project)


def _ids(s):
    return [x for x in (s or "").replace(" ", ",").split(",") if x] or None


def _show(x):
    if isinstance(x, (dict, list)):
        print(json.dumps(x, indent=1, ensure_ascii=False))
    elif x is not None:
        print(x)


def cmd_init(a):
    p = init_project(a.dir, a.name, a.comfy_url, a.comfy_dir, mode=a.mode)
    print(f"project '{p.name}' at {p.root}")
    print(f"ComfyUI renders go to output/{p.output_subdir}/ ; inputs are staged to input/{p.input_subdir}/")
    print("next: edit canon.json, shots.json, song/caption.md and song/lyrics.txt, then `nightshift doctor` and `nightshift run`")


def cmd_doctor(a):
    from . import workflows as W
    ok = True
    def line(good, msg):
        nonlocal ok
        ok &= bool(good)
        print(("  ok   " if good else "  !!   ") + msg)
    print("tools")
    for t in ("ffmpeg", "ffprobe", "node", "npm"):
        line(shutil.which(t), t + ("" if shutil.which(t) else " not found (needed for " + ("overlay" if t in ("node", "npm") else "cut/finish") + ")"))
    for mod in ("numpy", "cv2", "librosa", "faster_whisper", "PIL"):
        try:
            __import__(mod)
            line(True, f"python: {mod}")
        except Exception:
            line(False, f"python: {mod} missing (pip install -r requirements.txt)")
    from .score import MODELS
    for m in ("yunet.onnx", "sface.onnx"):
        line(os.path.exists(os.path.join(MODELS, m)), f"model {m}" + ("" if os.path.exists(os.path.join(MODELS, m)) else " (python scripts/get_models.py)"))
    try:
        p = _p(a)
    except FileNotFoundError:
        p = None
    print("workflows")
    dirs = p.workflow_dirs() if p else []
    for name in W.available(dirs):
        wf = W.Workflow.load(name, dirs)
        bad = wf.check()
        line(not bad, f"{name} ({wf.kind or 'no map'}): " + ("; ".join(bad) if bad else f"{len(wf.roles())} roles, outputs {wf.outputs()}"))
    if not p:
        print("(no project here: run inside a project folder or pass -p for the ComfyUI checks)")
        return 0 if ok else 1
    print(f"ComfyUI at {p.cfg['comfy']['url']}")
    c = p.client
    try:
        stats = c.system_stats()
        dev = (stats.get("devices") or [{}])[0]
        line(True, f"reachable: {dev.get('name', '?')}, VRAM free {dev.get('vram_free', 0) / 2**30:.1f} of {dev.get('vram_total', 0) / 2**30:.1f} GB")
        info = c.object_info()
        for role, name in p.cfg["workflows"].items():
            try:
                wf = p.workflow(role)
            except W.WorkflowError as e:
                line(False, f"{role}: {e}")
                continue
            missing = [n for n in wf.node_classes() if n not in info]
            line(not missing, f"{role} -> {wf.name}: " + (f"missing custom nodes {missing}" if missing else "all node types installed"))
            if a.models:
                for cls, m in wf.models():
                    print(f"         {cls}: {m}")
    except Exception as e:
        line(False, f"not reachable ({e})")
    if p.comfy_dir:
        line(os.path.isdir(os.path.join(p.comfy_dir, "input")), f"ComfyUI folder {p.comfy_dir}")
        line(p.renders_in_place, "project lives in ComfyUI's output folder (renders land in place)" if p.renders_in_place
             else "project is outside ComfyUI's output folder: renders are copied in after each job")
    return 0 if ok else 1


def cmd_workflows(a):
    from . import workflows as W
    dirs = []
    try:
        dirs = _p(a).workflow_dirs()
    except FileNotFoundError:
        pass
    for name, path in W.available(dirs).items():
        wf = W.Workflow.load(name, dirs)
        print(f"{name}  [{wf.kind}]  {path}")
        print(f"    roles: {', '.join(wf.roles())}")
        print(f"    outputs: {', '.join(wf.outputs())}")
        if a.models:
            for cls, m in wf.models():
                print(f"    model  {cls}: {m}")
        bad = wf.check()
        if bad:
            print("    PROBLEMS: " + "; ".join(bad))


def cmd_song(a):
    from . import song
    p = _p(a)
    if a.action == "jobs":
        _show([p.rel(x) for x in song.build_jobs(p, a.seeds, a.tag, max_seconds=a.max_seconds)])
    elif a.action == "choose":
        _show(p.rel(song.choose(p, a.file)))


def cmd_sheets(a):
    from . import sheets
    p = _p(a)
    if a.action == "status":
        _show(sheets.status(p))
    elif a.action == "build":
        ch, w = a.args[0], a.args[1]
        ws = sheets.worlds(p).get(ch, [w])
        prim = sheets.sheet_path(p, ch, ws[0]) if ws and ws[0] != w else None
        _show([p.rel(j) for j in sheets.build(p, ch, w, a.n, p.path(prim) if prim else None)])
    elif a.action == "rank":
        _show(sheets.rank(p, a.args[0], a.args[1]))
    elif a.action == "grid":
        _show(sheets.sheet_grid(p, a.args[0], a.args[1]))
    elif a.action == "pick":
        _show(sheets.pick(p, a.args[0], a.args[1], a.args[2]))


def cmd_analyze(a):
    from . import lyrics
    _show(lyrics.analyze(_p(a), model=a.model, stem=a.stem))


def cmd_timeline(a):
    from . import timeline
    p = _p(a)
    if a.action == "resolve":
        print(timeline.resolve(p, a.shots))
    elif a.action == "fill":
        _show(timeline.fill(p, only_empty=not a.all))
    elif a.action == "pick":
        f = {k: getattr(a, k) for k in ("in_", "speed", "beats", "seconds") if getattr(a, k) is not None}
        if "in_" in f:
            f["in"] = f.pop("in_")
        _show(timeline.pick(p, a.shot, a.src, **f))


def cmd_build(a):
    from . import build
    picks = dict(x.split("=", 1) for x in a.pick or [])
    _show(build.build(_p(a), a.stage, _ids(a.ids), picks, a.shots))


def cmd_variants(a):
    from . import build
    _show(build.variants(_p(a), _ids(a.ids), a.wordings, a.per, a.tag))


def cmd_takes(a):
    from . import takes
    _show(takes.takes(_p(a), a.job, a.n, a.seed, a.tag))


def cmd_edit(a):
    from . import takes
    _show(takes.edit(_p(a), a.base, a.id, a.seed, a.text, a.ref, a.ref2))


def cmd_submit(a):
    from . import comfy
    p = _p(a)
    jobs = [j for pat in a.jobs for j in (glob.glob(p.path(pat)) or [pat])]
    added = comfy.submit(p, jobs)
    print(f"queued {len(added)} job(s)")
    if a.watch:
        _show(comfy.watch(p, a.timeout))


def cmd_watch(a):
    from . import comfy
    _show(comfy.watch(_p(a), a.timeout))


def cmd_status(a):
    from . import comfy, pipeline
    p = _p(a)
    _show({"pipeline": pipeline.state(p), "queue": comfy.status(p)})


def cmd_score(a):
    from . import score
    p = _p(a)
    if a.action == "rank":
        files = [f for g in a.files for f in sorted(glob.glob(p.path(g)))]
        rows = score.rank(p, files, a.char, a.world)
        if a.sheet:
            score.grid(p.path(a.sheet), [{"path": p.path(r["file"]), "face": r["face"]} for r in rows])
        _show(rows)
    elif a.action == "takes":
        _show(score.rank_takes(p, a.shot))
    elif a.action == "cut":
        for r in score.cut_report(p):
            face = "--" if r["face"] is None else "%.3f" % r["face"]
            print(f'{r["n"]:3d} {r["id"]:8} {r["char"]:8} {str(r["framing"]):7} {face}  {r["src"]}')
    elif a.action == "yaw":
        _show(score.yaw_series(p.path(a.files[0])))


def cmd_assemble(a):
    from .assemble import assemble
    p = _p(a)
    out = p.path(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    _show(assemble(p.path(a.cut), out, redo=_ids(a.redo) or ()))


def cmd_review(a):
    from . import review
    p = _p(a)
    if a.action == "numbered":
        _show(review.numbered(p.path(a.args[0]), p.path(a.args[1]), p.path(a.args[2])))
    elif a.action == "ab":
        pairs = [x.split("=", 1) for x in a.args[1:]]
        _show(review.ab(p, pairs, p.path(a.args[0])))
    elif a.action == "takes":
        _show(review.takes_sheet(p, a.args[0]))
    elif a.action == "frames":
        clips = [f for g in a.args[1:] for f in sorted(glob.glob(p.path(g)))]
        _show(review.frames(clips, p.path(a.args[0])))


def cmd_grade(a):
    from . import grade
    p = _p(a)
    _show(grade.preview([p.path(f) for f in a.frames], p.path(a.out), a.looks.split(",") if a.looks else None))


def cmd_finish(a):
    from . import finish
    p = _p(a)
    lifts = json.loads(a.lifts) if a.lifts else p.cfg["grade"].get("lifts", [])
    _show(finish.finish(p.path(a.cut), p.path(a.out), a.look or p.cfg["grade"]["look"], lifts,
                        p.path(a.overlay) if a.overlay else None, p.path(a.halftone) if a.halftone else None,
                        p.cfg["finish"].get("grain", 9), p.cfg["finish"]["chunk_seconds"], redo=[int(x) for x in _ids(a.redo) or []]))
    if a.web:
        _show(finish.web_copy(p.path(a.out), p.path(a.out)[:-4] + "_web.mp4"))


def cmd_overlay(a):
    from . import overlay as O
    p = _p(a)
    if a.action == "track":
        _show(O.track(p))
    elif a.action == "prep":
        faces = O.mapfaces(p, p.path(a.edl))
        _show(O.prep(p, p.path(a.edl), faces))
    elif a.action == "render":
        print(O.render(p.path("overlay", "data.json"), p.path("overlay", "frames"), a.first, a.last))
    elif a.action == "encode":
        _show(O.encode(p.path("overlay", "frames"), p.path(a.out or "overlay/chunks")))


def cmd_run(a):
    from . import pipeline
    p = _p(a)
    if a.yolo:
        p.cfg["mode"] = "yolo"
    _show(pipeline.run(p, a.start, a.until))


def cmd_continue(a):
    from . import pipeline
    p = _p(a)
    st = pipeline.approve(p, a.notes)
    print(f"checkpoint cleared; pass {st['pass']}")
    if not a.no_run:
        _show(pipeline.run(p))


def cmd_next_pass(a):
    from . import pipeline
    _show(pipeline.new_pass(_p(a)))


def cmd_mcp(a):
    from . import mcp_server
    mcp_server.main(a.http, a.host, a.port, a.project_root)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="nightshift", description="Music videos from a local ComfyUI, directed or not.")
    ap.add_argument("-p", "--project", default=os.environ.get("NIGHTSHIFT_PROJECT", "."))
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="new project folder from the starter template")
    s.add_argument("dir"); s.add_argument("--name"); s.add_argument("--comfy-url"); s.add_argument("--comfy-dir")
    s.add_argument("--mode", choices=["director", "yolo"], default="director"); s.set_defaults(f=cmd_init)

    s = sub.add_parser("doctor", help="check tools, models, workflows and ComfyUI"); s.add_argument("--models", action="store_true"); s.set_defaults(f=cmd_doctor)
    s = sub.add_parser("workflows", help="list workflows, their roles and problems"); s.add_argument("--models", action="store_true"); s.set_defaults(f=cmd_workflows)

    s = sub.add_parser("song", help="song jobs / choose the song")
    s.add_argument("action", choices=["jobs", "choose"]); s.add_argument("file", nargs="?")
    s.add_argument("--seeds", type=int, nargs="+", default=[101, 202, 303, 404]); s.add_argument("--tag", default="take")
    s.add_argument("--max-seconds", type=int); s.set_defaults(f=cmd_song)

    s = sub.add_parser("sheets", help="character reference sheets: status | build <char> <world> | rank | grid | pick <char> <world> <file>")
    s.add_argument("action", choices=["status", "build", "rank", "grid", "pick"]); s.add_argument("args", nargs="*")
    s.add_argument("-n", type=int); s.set_defaults(f=cmd_sheets)

    s = sub.add_parser("analyze", help="beat map + lyric timing of the chosen song")
    s.add_argument("--model", default="small.en"); s.add_argument("--stem", help="separated vocal stem (transcribes better)"); s.set_defaults(f=cmd_analyze)

    s = sub.add_parser("timeline", help="resolve shots against the song / fill or pick takes in the cut")
    s.add_argument("action", choices=["resolve", "fill", "pick"]); s.add_argument("shot", nargs="?"); s.add_argument("src", nargs="?")
    s.add_argument("--shots", default="shots.json"); s.add_argument("--all", action="store_true")
    s.add_argument("--in", dest="in_", type=float); s.add_argument("--speed", type=float); s.add_argument("--beats", type=int); s.add_argument("--seconds", type=float)
    s.set_defaults(f=cmd_timeline)

    s = sub.add_parser("build", help="write ComfyUI jobs for a stage")
    s.add_argument("stage", choices=["stills", "sheetedits", "edits", "videos"]); s.add_argument("--ids")
    s.add_argument("--pick", nargs="*", help="id=label: use stills/<id>_<label>_* for this run"); s.add_argument("--shots", default="shots_resolved.json")
    s.set_defaults(f=cmd_build)

    s = sub.add_parser("variants", help="seed x wording grid of identity edits"); s.add_argument("--ids", required=True)
    s.add_argument("--wordings", default="AC"); s.add_argument("--per", type=int, default=3); s.add_argument("--tag", default="v"); s.set_defaults(f=cmd_variants)

    s = sub.add_parser("takes", help="clone a job into N seeds"); s.add_argument("job"); s.add_argument("-n", type=int, default=4)
    s.add_argument("--seed", type=int); s.add_argument("--tag", default="t"); s.set_defaults(f=cmd_takes)

    s = sub.add_parser("edit", help="ad-hoc Flux edit job"); s.add_argument("--base", required=True); s.add_argument("--ref"); s.add_argument("--ref2")
    s.add_argument("--id", required=True); s.add_argument("--seed", type=int, default=1); s.add_argument("--text", required=True); s.set_defaults(f=cmd_edit)

    s = sub.add_parser("submit", help="queue jobs on ComfyUI"); s.add_argument("jobs", nargs="+"); s.add_argument("--watch", action="store_true")
    s.add_argument("--timeout", type=float); s.set_defaults(f=cmd_submit)
    s = sub.add_parser("watch", help="wait for queued jobs (watchdog: stalls, OOM, restarts)"); s.add_argument("--timeout", type=float); s.set_defaults(f=cmd_watch)
    s = sub.add_parser("status", help="pipeline state + queue"); s.set_defaults(f=cmd_status)

    s = sub.add_parser("score", help="face scores"); s.add_argument("action", choices=["rank", "takes", "cut", "yaw"])
    s.add_argument("files", nargs="*"); s.add_argument("--char"); s.add_argument("--world", default="real"); s.add_argument("--shot")
    s.add_argument("--sheet", help="also write a contact sheet here"); s.set_defaults(f=cmd_score)

    s = sub.add_parser("assemble", help="cut.json -> video on the song"); s.add_argument("--cut", default="cut.json")
    s.add_argument("--out", default="out/cut.mp4"); s.add_argument("--redo"); s.set_defaults(f=cmd_assemble)

    s = sub.add_parser("review", help="numbered copy / A-B reel / takes sheet / frame sheet")
    s.add_argument("action", choices=["numbered", "ab", "takes", "frames"]); s.add_argument("args", nargs="+"); s.set_defaults(f=cmd_review)

    s = sub.add_parser("grade", help="look preview grid"); s.add_argument("out"); s.add_argument("frames", nargs="+"); s.add_argument("--looks"); s.set_defaults(f=cmd_grade)

    s = sub.add_parser("finish", help="grade + overlay + texture"); s.add_argument("cut"); s.add_argument("out"); s.add_argument("--look")
    s.add_argument("--overlay", help="ov_%%02d.webm pattern or one .webm"); s.add_argument("--halftone"); s.add_argument("--lifts")
    s.add_argument("--redo"); s.add_argument("--web", action="store_true"); s.set_defaults(f=cmd_finish)

    s = sub.add_parser("overlay", help="HUD overlay steps"); s.add_argument("action", choices=["track", "prep", "render", "encode"])
    s.add_argument("--edl"); s.add_argument("--first", type=int, default=0); s.add_argument("--last", type=int); s.add_argument("--out"); s.set_defaults(f=cmd_overlay)

    s = sub.add_parser("run", help="run the pass (stops at checkpoints in director mode)")
    s.add_argument("--from", dest="start"); s.add_argument("--until"); s.add_argument("--yolo", action="store_true"); s.set_defaults(f=cmd_run)
    s = sub.add_parser("continue", help="approve the checkpoint and carry on"); s.add_argument("--notes"); s.add_argument("--no-run", action="store_true"); s.set_defaults(f=cmd_continue)
    s = sub.add_parser("next-pass", help="start pass N+1 (keeps renders and picks)"); s.set_defaults(f=cmd_next_pass)

    s = sub.add_parser("mcp", help="MCP server for agents (stdio, or --http for agents on another machine)")
    s.add_argument("--http", action="store_true"); s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=8765)
    s.add_argument("--project-root", help="folder that holds projects (agents address them by name)"); s.set_defaults(f=cmd_mcp)

    a = ap.parse_args(argv)
    return a.f(a) or 0


if __name__ == "__main__":
    sys.exit(main())
