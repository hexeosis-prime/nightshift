"""Nightshift Studio: the app. A local web page that makes a project from a few answers, runs the pass on your ComfyUI,
stops at the checkpoints for you to look and choose, and plays the finished video.

    nightshift app [--root <projects folder>] [--comfy-url http://127.0.0.1:8188] [--comfy-dir <ComfyUI folder>] [--port 8189]

Standard library only (http.server + threads). One pass runs at a time, because one GPU renders one thing at a time.
Everything it does is a normal Nightshift command underneath: the CLI and the MCP server see the same projects.
"""
import base64
import json
import mimetypes
import os
import re
import shutil
import tempfile
import threading
import time
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import __version__
from . import agent, pipeline, studio
from .project import Project

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
NAME_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
TYPES = {".html": "text/html; charset=utf-8", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
         ".mp4": "video/mp4", ".webm": "video/webm", ".mp3": "audio/mpeg", ".wav": "audio/wav", ".flac": "audio/flac", ".json": "application/json"}
MEDIA = (".png", ".jpg", ".jpeg", ".webp", ".mp4", ".webm", ".mp3", ".wav", ".flac")


class Cancelled(Exception):
    pass


class Studio:
    def __init__(self, root, comfy_url, comfy_dir=None):
        self.root = os.path.abspath(os.path.expanduser(root))
        os.makedirs(self.root, exist_ok=True)
        self.comfy_url, self.comfy_dir = comfy_url, comfy_dir
        self.lock = threading.Lock()
        self.run = None            # {"project", "thread", "started", "cancel"}
        self.events = {}           # project -> [lines]
        self.plans = {}            # plan id -> {"status", "events", "plan", "error"}
        self.mcp_port, self.port = 0, 8189

    # ---- projects -------------------------------------------------------------------------------
    def project(self, name):
        if not NAME_OK.match(name or ""):
            raise ValueError("bad project name")
        return Project(os.path.join(self.root, name))

    def list(self):
        out = []
        for name in sorted(os.listdir(self.root)):
            if os.path.exists(os.path.join(self.root, name, "project.json")):
                try:
                    p = Project(os.path.join(self.root, name))
                    st = pipeline.state(p)
                    out.append({"name": name, "scene": p.cfg.get("scene"), "aspect": p.cfg.get("aspect"),
                                "pass": st.get("pass"), "step": st.get("step"),
                                "waiting": (st.get("waiting") or {}).get("checkpoint"),
                                "mtime": os.path.getmtime(p.path("project.json"))})
                except Exception as e:
                    out.append({"name": name, "error": str(e)})
        return sorted(out, key=lambda r: -r.get("mtime", 0))

    def emit(self, name, msg):
        line = f"{time.strftime('%H:%M:%S')}  {msg}"
        self.events.setdefault(name, []).append(line)
        try:
            with open(os.path.join(self.root, name, "studio.log"), "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass

    def log_lines(self, name, since=0):
        lines = self.events.get(name)
        if lines is None:
            path = os.path.join(self.root, name, "studio.log")
            lines = open(path, encoding="utf-8").read().splitlines()[-400:] if os.path.exists(path) else []
            self.events[name] = lines
        return lines[since:], len(lines)

    def create(self, form, files):
        name = studio.slug(form.get("name") or form.get("scene"))
        base, k = name, 2
        while os.path.exists(os.path.join(self.root, name)):
            name, k = f"{base}-{k}", k + 1
        tmp = tempfile.mkdtemp(prefix="ns_upload_")
        try:
            ch = dict(form.get("character") or {})
            song = dict(form.get("song") or {})
            if files.get("photo"):
                ch["photo"] = _write_upload(tmp, files["photo"])
            ch2 = dict(form.get("character2") or {}) if form.get("character2") else None
            if ch2 is not None and files.get("photo2"):
                ch2["photo"] = _write_upload(tmp, files["photo2"], "p2_")
            if files.get("audio"):
                song["audio"] = _write_upload(tmp, files["audio"])
                song["source"] = "upload"
            elif song.get("source") == "upload":
                raise ValueError("choose a track to upload, or let MiniMax Music 3 write the song")
            form = dict(form, character=ch, character2=ch2, song=song, name=name,
                        comfy_url=form.get("comfy_url") or self.comfy_url, comfy_dir=form.get("comfy_dir") or self.comfy_dir)
            p = studio.create(os.path.join(self.root, name), form)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.emit(name, f"project created: {p.cfg['length']} / {p.cfg['aspect']} / {p.cfg['image_model']} / scene {p.cfg['scene']}")
        return name

    # ---- agent mode -------------------------------------------------------------------------------
    def agent_settings(self, update=None):
        s = agent.load_settings(self.root)
        if update is not None:
            for secret in ("api_key", "hook_token"):
                if not update.get(secret):
                    update = dict(update, **{secret: s.get(secret, "")})      # an empty field keeps the saved secret
            s = agent.save_settings(self.root, {**s, **update})
        return {"base_url": s["base_url"], "model": s["model"], "has_key": bool(s.get("api_key")),
                "hook_url": s.get("hook_url", ""), "has_hook_token": bool(s.get("hook_token")),
                "mcp_url": self.mcp_url(), "studio_url": self.studio_url()}

    def mcp_url(self):
        return f"http://{lan_ip()}:{self.mcp_port}/mcp" if self.mcp_port else None

    def studio_url(self):
        return f"http://{lan_ip()}:{self.port}/"

    def handoff(self, idea, length, opts):
        if not (idea or "").strip():
            raise ValueError("describe your idea first")
        if not self.mcp_port:
            raise ValueError("start the app with --mcp-port 8765 (studio.bat: set \"NIGHTSHIFT_ARGS=--host 0.0.0.0 --mcp-port 8765\") so your agent can reach Nightshift")
        brief = agent.handoff_brief(idea, length, opts, self.mcp_url(), self.studio_url())
        s = agent.load_settings(self.root)
        if not s.get("hook_url"):
            return {"sent": False, "brief": brief}
        r = agent.send_handoff(s, brief, {"source": "nightshift-studio", "idea": idea, "length": length, "settings": opts,
                                          "mcp_url": self.mcp_url(), "studio_url": self.studio_url()})
        return {"sent": True, "brief": brief, "reply": r}

    def agent_models(self):
        try:
            return {"ok": True, "models": agent.models(agent.load_settings(self.root))}
        except Exception as e:
            return {"ok": False, "problem": str(e)[:200]}

    def start_plan(self, idea, length):
        if not (idea or "").strip():
            raise ValueError("describe your idea first")
        pid = f"p{int(time.time() * 1000)}"
        job = {"status": "planning", "events": [], "plan": None, "error": None, "idea": idea, "length": length}
        self.plans[pid] = job

        def work():
            try:
                job["plan"] = agent.plan(idea, agent.load_settings(self.root), length,
                                         on_event=lambda m: job["events"].append(f"{time.strftime('%H:%M:%S')}  {m}"))
                job["status"] = "ready"
            except Exception as e:
                job["error"], job["status"] = str(e), "failed"
        threading.Thread(target=work, daemon=True, name=pid).start()
        return pid

    def create_from_plan(self, plan, opts, run=True):
        plan = agent.normalize(plan, plan.get("length") or "medium") if "characters" in plan and "_validated" not in plan else plan
        name = studio.slug(opts.get("name") or plan.get("title"))
        base, k = name, 2
        while os.path.exists(os.path.join(self.root, name)):
            name, k = f"{base}-{k}", k + 1
        opts = dict(opts, name=name, comfy_url=opts.get("comfy_url") or self.comfy_url, comfy_dir=opts.get("comfy_dir") or self.comfy_dir)
        p = agent.create_from_plan(os.path.join(self.root, name), plan, opts)
        self.emit(name, f"project planned by the agent: \"{plan.get('title')}\", {len(plan['shots'])} shots, "
                        f"{', '.join(c['name'] for c in plan['characters'].values())}, {p.cfg['aspect']}, {p.cfg['image_model']}")
        if run:
            self.start(name)
        return name

    # ---- running -------------------------------------------------------------------------------
    def busy(self):
        r = self.run
        return r if r and r["thread"].is_alive() else None

    def start(self, name, approve=False, notes=None):
        with self.lock:
            if self.busy():
                raise RuntimeError(f"a pass is already running for '{self.run['project']}' (one GPU, one pass at a time)")
            p = self.project(name)
            if approve:
                pipeline.approve(p, notes or None)
            cancel = threading.Event()

            def on_event(msg):
                self.emit(name, msg)
                if cancel.is_set():
                    raise Cancelled()

            def work():
                try:
                    pipeline.run(Project(p.root), on_event=on_event)
                except Cancelled:
                    self.emit(name, "stopped. Press Run to carry on: finished renders are kept.")
                except Exception as e:
                    self.emit(name, f"ERROR {type(e).__name__}: {e}")
                    for line in traceback.format_exc().splitlines()[-6:]:
                        self.emit(name, "      " + line)
            t = threading.Thread(target=work, daemon=True, name=f"pass-{name}")
            self.run = {"project": name, "thread": t, "started": time.time(), "cancel": cancel}
            self.emit(name, "run" if not approve else "approved: carrying on")
            t.start()

    def stop(self, name):
        r = self.busy()
        if not r or r["project"] != name:
            return False
        r["cancel"].set()
        p = self.project(name)
        try:
            from . import comfy as C
            q = C.load_state(p)
            ids = [j["prompt_id"] for j in q["jobs"] if j["status"] in ("queued", "running")]
            if ids:
                p.client.cancel(ids)
            p.client.interrupt()
        except Exception as e:
            self.emit(name, f"could not reach ComfyUI to cancel jobs ({e})")
        self.emit(name, "stopping...")
        return True

    # ---- views -------------------------------------------------------------------------------
    def view(self, name):
        p = self.project(name)
        st = pipeline.state(p)
        from . import comfy as C
        q = C.load_state(p)
        step_jobs = [j for j in q["jobs"] if j.get("submitted", 0) >= _step_started(st)]
        counts = {}
        for j in step_jobs:
            counts[j["status"]] = counts.get(j["status"], 0) + 1
        w = st.get("waiting")
        packet = None
        if w:
            packet = {"checkpoint": w["checkpoint"], "since": w.get("since"), "files": [f for f in w.get("packet", []) if f],
                      "choices": self.choices(p, w["checkpoint"])}
        outs = sorted([f for f in os.listdir(p.path("out")) if re.match(r"pass\d+\.mp4$", f)]) if os.path.isdir(p.path("out")) else []
        busy = self.busy()
        ext = external_run(p, st)
        return {
            "name": name, "running": bool(busy and busy["project"] == name) or ext, "by_agent": ext,
            "busy_other": bool(busy and busy["project"] != name),
            "cfg": dict({k: p.cfg.get(k) for k in ("mode", "profile", "length", "aspect", "image_model", "scene", "song", "work_size", "final_size")},
                        hud=bool((p.cfg.get("overlay") or {}).get("enabled"))),
            "comfy": p.cfg["comfy"]["url"],
            "pass": st.get("pass"), "step": st.get("step"), "done": [h["step"] for h in st.get("history", [])],
            "steps": pipeline.STEPS, "jobs": counts, "waiting": packet,
            "finished": [f"out/{f}" for f in outs], "renders": self.renders(p),
        }

    def choices(self, p, checkpoint):
        """What the director picks at a checkpoint, beyond approving."""
        picks = p.load("studio_picks.json", {})
        if checkpoint in ("sheets_review", "outfits_review"):
            from . import sheets as SH
            out = []
            want_first = checkpoint == "sheets_review"
            for row in SH.status(p):
                if row["first_world"] != want_first:
                    continue
                ranked = SH.rank(p, row["char"], row["world"])
                out.append({"kind": "sheet", "char": row["char"], "world": row["world"], "picked": row["sheet"],
                            "picked_file": picks.get(f"sheet:{row['char']}:{row['world']}"),
                            "options": [{"file": r["file"], "score": r["score"], "by": r["by"]} for r in ranked]})
            return out
        if checkpoint == "song_pick":
            rows = (p.load("review/songs.json") or {}).get("songs", [])
            return [{"kind": "song", "picked": p.cfg.get("song"), "picked_file": picks.get("song"),
                     "options": [{"file": r["file"], "score": r["lyric_coverage"], "by": "of the lyric sheet sung"} for r in rows]}]
        return []

    def pick(self, name, body):
        p = self.project(name)
        kind = body.get("kind")
        f = body.get("file") or ""
        if not _inside(p.root, p.path(f)):
            raise ValueError("bad file")
        picks = p.load("studio_picks.json", {})
        if kind == "sheet":
            from . import sheets as SH
            out = SH.pick(p, body["char"], body["world"], f)
            picks[f"sheet:{body['char']}:{body['world']}"] = f
        elif kind == "song":
            from . import song
            out = p.rel(song.choose(p, f))
            picks["song"] = f
        else:
            raise ValueError(f"nothing to pick for {kind}")
        p.save("studio_picks.json", picks)
        return out

    def renders(self, p, n=24):
        files = []
        for kind in ("sheets", "stills", "clips"):
            d = p.path(kind)
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.lower().endswith(MEDIA) and not f.endswith("-audio.mp4"):
                        files.append((os.path.getmtime(os.path.join(d, f)), f"{kind}/{f}"))
        return [f for _, f in sorted(files, reverse=True)[:n]]

    def comfy_status(self, url=None):
        from .comfy import Comfy
        c = Comfy(url or self.comfy_url, None, timeout=4)
        try:
            stats = c.system_stats()
            dev = (stats.get("devices") or [{}])[0]
            ver = (stats.get("system") or {}).get("comfyui_version")
            q = c.queue()
            return {"ok": True, "url": c.url if hasattr(c, "url") else url, "gpu": dev.get("name"), "version": ver,
                    "vram_free_gb": round(dev.get("vram_free", 0) / 2**30, 1), "vram_total_gb": round(dev.get("vram_total", 0) / 2**30, 1),
                    "queue": len(q.get("running", [])) + len(q.get("pending", []))}
        except Exception as e:
            return {"ok": False, "problem": str(e)[:200]}


def lan_ip():
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def external_run(p, st):
    """A pass started by an agent over MCP (a background `nightshift run` process) that is still alive."""
    tid = st.get("task")
    if not tid or st.get("step") == "done":
        return False
    t = p.load(f"tasks/{tid}.json")
    if not t:
        return False
    from .mcp_server import _alive
    return _alive(t["pid"])


def _step_started(st):
    hist = st.get("history") or []
    if not hist:
        return 0
    try:
        return time.mktime(time.strptime(hist[-1]["t"], "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return 0


def _inside(root, path):
    root, path = os.path.abspath(root), os.path.abspath(path)
    return os.path.commonpath([root, path]) == root


def _write_upload(tmp, up, prefix=""):
    name = prefix + re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(up.get("name") or "upload.bin"))[-80:]
    path = os.path.join(tmp, name)
    data = up["data"]
    if "," in data[:100]:
        data = data.split(",", 1)[1]
    with open(path, "wb") as f:
        f.write(base64.b64decode(data))
    return path


def handler(app):
    class H(BaseHTTPRequestHandler):
        server_version = f"NightshiftStudio/{__version__}"

        def log_message(self, fmt, *args):
            pass

        def _json(self, obj, code=200):
            body = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}") if n else {}

        def _file(self, path):
            if not os.path.isfile(path):
                return self._json({"error": "not found"}, 404)
            size = os.path.getsize(path)
            ext = os.path.splitext(path)[1].lower()
            ctype = TYPES.get(ext) or mimetypes.guess_type(path)[0] or "application/octet-stream"
            rng = self.headers.get("Range")
            start, end = 0, size - 1
            if rng and rng.startswith("bytes="):
                a, _, b = rng[6:].partition("-")
                start = int(a) if a else max(0, size - int(b))
                end = int(b) if a and b else size - 1
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            else:
                self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            with open(path, "rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(1 << 20, left))
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        return
                    left -= len(chunk)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            q = dict(urllib.parse.parse_qsl(u.query))
            parts = [urllib.parse.unquote(x) for x in u.path.strip("/").split("/") if x]
            try:
                if not parts:
                    return self._file(os.path.join(WEB, "studio.html"))
                if parts[0] == "static" and len(parts) == 2:
                    return self._file(os.path.join(WEB, os.path.basename(parts[1])))
                if parts == ["api", "info"]:
                    return self._json({"version": __version__, "root": app.root, "comfy_url": app.comfy_url,
                                       "scenes": {k: {"label": v["label"], "blurb": v["blurb"]} for k, v in studio.SCENES.items()},
                                       "lengths": {k: v["label"] for k, v in studio.LENGTHS.items()},
                                       "default_lyrics": studio.DEFAULT_LYRICS, "busy": (app.busy() or {}).get("project"),
                                       "grades": studio.GRADES,
                                       "agent_lengths": {k: v["label"] for k, v in agent.LENGTHS.items()}})
                if parts == ["api", "agent", "settings"]:
                    return self._json(app.agent_settings())
                if parts == ["api", "agent", "models"]:
                    return self._json(app.agent_models())
                if len(parts) == 4 and parts[:3] == ["api", "agent", "plan"]:
                    job = app.plans.get(parts[3])
                    if not job:
                        return self._json({"error": "no such plan"}, 404)
                    return self._json({k: job[k] for k in ("status", "events", "plan", "error")})
                if parts == ["api", "comfy"]:
                    return self._json(app.comfy_status(q.get("url")))
                if parts == ["api", "projects"]:
                    return self._json({"projects": app.list()})
                if len(parts) == 3 and parts[:2] == ["api", "projects"]:
                    return self._json(app.view(parts[2]))
                if len(parts) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "log":
                    lines, n = app.log_lines(parts[2], int(q.get("since", 0)))
                    return self._json({"lines": lines, "next": n})
                if len(parts) >= 3 and parts[0] == "files":
                    p = app.project(parts[1])
                    path = p.path(*parts[2:])
                    if not _inside(p.root, path):
                        return self._json({"error": "outside the project"}, 403)
                    return self._file(path)
                return self._json({"error": "not found"}, 404)
            except (ValueError, FileNotFoundError) as e:
                return self._json({"error": str(e)}, 400)
            except Exception as e:
                return self._json({"error": f"{type(e).__name__}: {e}"}, 500)

        def do_POST(self):
            parts = [x for x in urllib.parse.urlparse(self.path).path.strip("/").split("/") if x]
            try:
                body = self._body()
                if parts == ["api", "agent", "settings"]:
                    return self._json(app.agent_settings(body))
                if parts == ["api", "agent", "plan"]:
                    return self._json({"id": app.start_plan(body.get("idea"), body.get("length") or "medium")})
                if parts == ["api", "agent", "handoff"]:
                    return self._json(app.handoff(body.get("idea"), body.get("length") or "medium", body.get("opts") or {}))
                if parts == ["api", "agent", "create"]:
                    return self._json({"name": app.create_from_plan(body["plan"], body.get("opts") or {}, body.get("run", True))})
                if parts == ["api", "projects"]:
                    name = app.create(body.get("form") or {}, body.get("files") or {})
                    if body.get("run"):
                        app.start(name)
                    return self._json({"name": name})
                if len(parts) == 4 and parts[:2] == ["api", "projects"]:
                    name, action = parts[2], parts[3]
                    if action == "run":
                        app.start(name)
                    elif action == "continue":
                        app.start(name, approve=True, notes=body.get("notes"))
                    elif action == "stop":
                        app.stop(name)
                    elif action == "pick":
                        return self._json({"picked": app.pick(name, body)})
                    else:
                        return self._json({"error": f"unknown action {action}"}, 404)
                    return self._json(app.view(name))
                return self._json({"error": "not found"}, 404)
            except (ValueError, KeyError, FileNotFoundError, RuntimeError, agent.PlanError) as e:
                return self._json({"error": str(e)}, 400)
            except Exception as e:
                return self._json({"error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}, 500)
    return H


def serve(root, comfy_url, comfy_dir=None, host="127.0.0.1", port=8189, open_browser=True, mcp_port=0):
    app = Studio(root, comfy_url, comfy_dir)
    app.port = port
    if mcp_port:
        import atexit
        import subprocess
        import sys
        cmd = [sys.executable, "-m", "nightshift", "mcp", "--http", "--host", "0.0.0.0", "--port", str(mcp_port),
               "--project-root", app.root, "--comfy-url", comfy_url] + (["--comfy-dir", comfy_dir] if comfy_dir else [])
        proc = subprocess.Popen(cmd)
        atexit.register(proc.terminate)
        app.mcp_port = mcp_port
        print(f"MCP server for agents on http://{lan_ip()}:{mcp_port}/mcp (your local network only; there is no login)")
    srv = ThreadingHTTPServer((host, port), handler(app))
    url = f"http://{'127.0.0.1' if host in ('0.0.0.0', '') else host}:{port}/"
    print(f"Nightshift Studio on {url}  (projects in {app.root}; ComfyUI at {comfy_url})")
    if host not in ("127.0.0.1", "localhost"):
        print("  listening beyond this machine: there is no login, keep it on your own network")
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return app
