"""ComfyUI over its HTTP API (no extra dependencies), plus the queue runner with a stall/OOM watchdog.

Works against a ComfyUI on this machine or across the network (--listen on the GPU box). The watchdog judges a running
job by ComfyUI's own progress messages (its websocket: a tick per sampler step, a message per node, decode progress), so
a long render that is working is never taken for a stall. When the websocket can't be reached it falls back to the log
file (project comfy.dir): a log that stops moving for long enough while a job is "running" is a stall.
"""
import base64
import hashlib
import json
import mimetypes
import os
import socket
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


class ComfyError(Exception):
    pass


class Progress:
    """Listens to ComfyUI's websocket (/ws?clientId=...) in a background thread and remembers, per prompt, when it last
    showed a sign of life: a sampler step, a node starting or finishing, a preview image. Only prompts queued with the
    same client id are reported to us, which is why a project keeps one client id across runs (Project.client).
    Standard library only: a minimal RFC 6455 client (text, binary, ping/pong, close)."""
    LIFE = ("progress", "progress_state", "executing", "executed", "execution_start", "execution_cached")

    def __init__(self, url, client_id):
        u = urllib.parse.urlparse(url)
        self.host, self.port = u.hostname or "127.0.0.1", u.port or (443 if u.scheme == "https" else 80)
        self.path = (u.path.rstrip("/") or "") + "/ws?clientId=" + urllib.parse.quote(client_id)
        self.connected, self.since, self.error = False, None, None
        self.last, self.info, self.preview = {}, {}, None
        self._stop, self._buf = False, b""
        self.thread = threading.Thread(target=self._loop, daemon=True, name="comfy-progress")
        self.thread.start()

    def stop(self):
        self._stop = True

    def quiet(self, prompt_id, started=None):
        """Seconds since this prompt last showed life (counted from when we started listening or the job started, if
        later), or None when the websocket isn't connected."""
        if not self.connected:
            return None
        marks = [self.since or 0, started or 0, self.last.get(prompt_id) or 0, self.preview or 0]
        return time.time() - max(marks)

    # ---- the socket -------------------------------------------------------------------------------
    def _loop(self):
        wait = 2
        while not self._stop:
            try:
                self._session()
                wait = 2
            except Exception as e:
                self.error = str(e)[:200]
            self.connected = False
            if self._stop:
                break
            time.sleep(wait)
            wait = min(wait * 2, 30)

    def _recv(self, sock, n):
        while len(self._buf) < n:
            chunk = sock.recv(65536)
            if not chunk:
                raise ConnectionError("websocket closed")
            self._buf += chunk
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def _send(self, sock, op, payload=b""):
        mask = os.urandom(4)
        head = bytes([0x80 | op])
        n = len(payload)
        head += bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + n.to_bytes(2, "big")
        sock.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def _session(self):
        sock = socket.create_connection((self.host, self.port), timeout=15)
        try:
            key = base64.b64encode(os.urandom(16)).decode()
            sock.sendall((f"GET {self.path} HTTP/1.1\r\nHost: {self.host}:{self.port}\r\nUpgrade: websocket\r\n"
                          f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
            self._buf = b""
            while b"\r\n\r\n" not in self._buf:
                chunk = sock.recv(4096)
                if not chunk:
                    raise ConnectionError("no websocket handshake")
                self._buf += chunk
            head, self._buf = self._buf.split(b"\r\n\r\n", 1)
            if b" 101" not in head.split(b"\r\n", 1)[0]:
                raise ConnectionError("websocket refused: " + head.split(b"\r\n", 1)[0].decode(errors="replace"))
            self.connected, self.since, self.error = True, time.time(), None
            sock.settimeout(30)
            while not self._stop:
                try:
                    b0, b1 = self._recv(sock, 2)
                except socket.timeout:
                    continue                      # a quiet socket is fine; ComfyUI only talks when something happens
                op, n = b0 & 0x0F, b1 & 0x7F
                if n == 126:
                    n = int.from_bytes(self._recv(sock, 2), "big")
                elif n == 127:
                    n = int.from_bytes(self._recv(sock, 8), "big")
                mask = self._recv(sock, 4) if b1 & 0x80 else None
                data = self._recv(sock, n) if n else b""
                if mask:
                    data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
                if op == 0x8:
                    raise ConnectionError("websocket closed by ComfyUI")
                if op == 0x9:
                    self._send(sock, 0xA, data)
                elif op == 0x2:
                    self.preview = time.time()    # a preview image: the sampler is moving
                elif op == 0x1:
                    self._message(data)
        finally:
            sock.close()

    def _message(self, data):
        try:
            m = json.loads(data)
        except ValueError:
            return
        kind, d = m.get("type"), m.get("data") or {}
        pid = d.get("prompt_id")
        if kind in self.LIFE and pid:
            self.last[pid] = time.time()
            if kind == "progress":
                self.info[pid] = {"value": d.get("value"), "max": d.get("max"), "node": d.get("node")}
            elif kind == "executing" and d.get("node"):
                self.info.setdefault(pid, {})["node"] = d.get("node")


_LISTENERS, _LISTENERS_LOCK = {}, threading.Lock()


class Comfy:
    def __init__(self, url="http://127.0.0.1:8188", comfy_dir=None, timeout=60, client_id=None):
        self.url = url.rstrip("/")
        self.dir = comfy_dir
        self.timeout = timeout
        self.client_id = client_id or "nightshift-" + uuid.uuid4().hex[:8]
        self._progress = None

    def progress(self):
        """The websocket listener for this client id, one per process (started on first use). ComfyUI keeps one socket
        per client id, so two listeners with the same id would keep knocking each other off."""
        if self._progress is None:
            with _LISTENERS_LOCK:
                key = (self.url, self.client_id)
                if key not in _LISTENERS:
                    _LISTENERS[key] = Progress(self.url, self.client_id)
                self._progress = _LISTENERS[key]
        return self._progress

    # ---- raw -------------------------------------------------------------------------------
    def _req(self, method, path, body=None, headers=None, raw=False):
        data = None
        hdrs = dict(headers or {})
        if body is not None and not isinstance(body, (bytes, bytearray)):
            data = json.dumps(body).encode()
            hdrs["Content-Type"] = "application/json"
        elif body is not None:
            data = bytes(body)
        req = urllib.request.Request(self.url + path, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                out = r.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            raise ComfyError(f"{method} {path} -> HTTP {e.code}: {detail[:4000]}") from None
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            raise ComfyError(f"ComfyUI not reachable at {self.url} ({e})") from None
        if raw:
            return out
        return json.loads(out) if out else {}

    # ---- api -------------------------------------------------------------------------------
    def alive(self):
        try:
            self.system_stats()
            return True
        except ComfyError:
            return False

    def system_stats(self):
        return self._req("GET", "/system_stats")

    def object_info(self, node_class=None):
        return self._req("GET", "/object_info" + (f"/{urllib.parse.quote(node_class)}" if node_class else ""))

    def model_names(self, prompt):
        """Model files can be saved under a slightly different name than the workflow asks for (hyphens vs underscores, case,
        as mirrors of the same file often are). Swap in the name ComfyUI actually has when it is the same name otherwise."""
        cache = self.__dict__.setdefault("_choices", {})
        norm = lambda s: s.lower().replace("-", "_").replace(" ", "_")
        # known mirrors that name the same checkpoint differently (DeepBeepMeep/Flux3: no suffix = the full model, _sd_ = distilled)
        alias = {"flux3_image_klein_base_int8_convrot.safetensors": "flux3_image_klein_int8_convrot.safetensors",
                 "flux3_image_klein_int8_convrot.safetensors": "flux3_image_klein_sd_int8_convrot.safetensors"}
        for node in prompt.values():
            if not isinstance(node, dict):
                continue
            cls = node.get("class_type", "")
            for k, v in (node.get("inputs") or {}).items():
                if not (isinstance(v, str) and v.lower().endswith((".safetensors", ".gguf", ".ckpt", ".pt", ".pth", ".bin", ".sft"))):
                    continue
                if cls not in cache:
                    try:
                        req = self.object_info(cls).get(cls, {}).get("input", {})
                        cache[cls] = {kk: vv[0] for part in ("required", "optional") for kk, vv in (req.get(part) or {}).items()
                                      if isinstance(vv, (list, tuple)) and vv and isinstance(vv[0], list)}
                    except Exception:
                        cache[cls] = {}
                have = cache[cls].get(k) or []
                if have and v not in have:
                    want = norm(os.path.basename(v))
                    alt = next((h for h in have if isinstance(h, str) and norm(os.path.basename(h)) == want), None) or \
                        next((h for h in have if isinstance(h, str) and norm(os.path.basename(h)) == alias.get(want)), None)
                    if alt:
                        node["inputs"][k] = alt
        return prompt

    def queue_prompt(self, prompt):
        prompt = self.model_names(prompt)
        try:
            r = self._req("POST", "/prompt", {"prompt": prompt, "client_id": self.client_id})
        except ComfyError as e:
            raise ComfyError(f"ComfyUI rejected the job: {e}") from None
        if r.get("node_errors"):
            raise ComfyError(f"node errors: {json.dumps(r['node_errors'])[:4000]}")
        return r["prompt_id"]

    def queue(self):
        q = self._req("GET", "/queue")
        return {"running": [x[1] for x in q.get("queue_running", [])], "pending": [x[1] for x in q.get("queue_pending", [])]}

    def history(self, prompt_id=None, max_items=None):
        path = f"/history/{prompt_id}" if prompt_id else "/history" + (f"?max_items={max_items}" if max_items else "")
        return self._req("GET", path)

    def result(self, prompt_id):
        """status: pending | running | success | error | unknown, plus output files and the error if any."""
        h = self.history(prompt_id).get(prompt_id)
        if h:
            st = h.get("status", {})
            files = []
            for node_out in h.get("outputs", {}).values():
                for v in node_out.values():
                    if isinstance(v, list):
                        files += [x for x in v if isinstance(x, dict) and "filename" in x]
            err, t0, t1 = None, None, None
            for name, msg in st.get("messages", []):
                if name == "execution_start":
                    t0 = msg.get("timestamp")
                if name in ("execution_success", "execution_error", "execution_interrupted"):
                    t1 = msg.get("timestamp")
                if name == "execution_error":
                    err = {k: msg.get(k) for k in ("node_id", "node_type", "exception_type", "exception_message")}
                if name == "execution_interrupted":
                    err = {"exception_type": "interrupted"}
            ok = st.get("status_str") == "success" and not err
            secs = round((t1 - t0) / 1000, 1) if t0 and t1 else None
            return {"status": "success" if ok else "error", "files": files, "error": err, "seconds": secs}
        q = self.queue()
        if prompt_id in q["running"]:
            return {"status": "running"}
        if prompt_id in q["pending"]:
            return {"status": "pending", "position": q["pending"].index(prompt_id)}
        return {"status": "unknown"}

    def interrupt(self, prompt_id=None):
        self._req("POST", "/interrupt", {"prompt_id": prompt_id} if prompt_id else {})

    def cancel(self, prompt_ids):
        self._req("POST", "/queue", {"delete": list(prompt_ids)})

    def free(self, unload_models=True):
        self._req("POST", "/free", {"unload_models": unload_models, "free_memory": True})

    def upload(self, path, subfolder="", name=None, kind="input"):
        """POST /upload/image (ComfyUI stores any file type this way, audio included)."""
        name = name or os.path.basename(path)
        boundary = "----nightshift" + uuid.uuid4().hex
        ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
        parts = []
        for k, v in (("type", kind), ("subfolder", subfolder), ("overwrite", "true")):
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        with open(path, "rb") as f:
            blob = f.read()
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{name}"\r\n'
                     f"Content-Type: {ctype}\r\n\r\n".encode() + blob + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        r = self._req("POST", "/upload/image", b"".join(parts), {"Content-Type": f"multipart/form-data; boundary={boundary}"})
        return (r.get("subfolder") + "/" if r.get("subfolder") else "") + r.get("name", name)

    def download(self, f, dst):
        q = urllib.parse.urlencode({"filename": f["filename"], "subfolder": f.get("subfolder", ""), "type": f.get("type", "output")})
        data = self._req("GET", "/view?" + q, raw=True)
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        with open(dst + ".part", "wb") as out:
            out.write(data)
        os.replace(dst + ".part", dst)
        return dst

    def log_age(self):
        """Seconds since ComfyUI last wrote its log (None when the folder isn't known)."""
        if not self.dir:
            return None
        for p in (os.path.join(self.dir, "user", "comfyui.log"), os.path.join(self.dir, "comfyui.log")):
            if os.path.exists(p):
                return time.time() - os.path.getmtime(p)
        return None


# ---- queue runner -------------------------------------------------------------------------------
def _limit_minutes(project, job_meta):
    wd = project.cfg["watchdog"]
    frames = job_meta.get("frames") or 0
    mult = 2.0 if job_meta.get("kind") in ("fflf",) else 1.0
    return max(wd["min_minutes"], frames * wd["max_minutes_per_frame"] * mult) + (30 if job_meta.get("kind") == "song" else 0)


LONG_KINDS = ("ff", "fflf", "t2v", "lipsync", "song")


def _progress_stall_seconds(project):
    """With ComfyUI's progress messages coming in, a running job counts as stalled after this long with no sign of life
    from it (no sampler step, no node, no preview) and no line in the log."""
    wd = project.cfg["watchdog"]
    return max(wd["stall_minutes"], wd.get("progress_stall_minutes", 10)) * 60


def _stall_seconds(project, job_meta):
    """How long ComfyUI's log may stay silent before a running job counts as stalled. Video and song jobs sample for many
    minutes without writing a line (a 288-frame first/last-frame shot is silent 6+ min, and the old 6-minute rule killed 8
    of 11 healthy renders on Zero's night), so for them silence only counts after half the job's own time limit; the
    time limit still catches a real hang."""
    wd = project.cfg["watchdog"]
    base = wd["stall_minutes"] * 60
    if job_meta.get("kind") in LONG_KINDS:
        return max(base, _limit_minutes(project, job_meta) * 60 / 2)
    return base


def _state_path(project):
    return project.path("queue.json")


def load_state(project):
    return project.load("queue.json", {"jobs": []})


def save_state(project, st):
    project.save("queue.json", st)


def submit(project, job_paths):
    """Queue built jobs. Returns the queue entries."""
    from .workflows import load_job_meta
    st = load_state(project)
    c = project.client
    added = []
    for jp in job_paths:
        jp = jp if os.path.isabs(jp) else project.path(jp)
        prompt = json.load(open(jp, encoding="utf-8"))
        pid = c.queue_prompt(prompt)
        e = {"job": project.rel(jp), "prompt_id": pid, "status": "queued", "attempts": 1, "submitted": time.time(),
             "meta": load_job_meta(jp)}
        st["jobs"].append(e)
        added.append(e)
        project.log("submitted", job=e["job"], prompt_id=pid)
    save_state(project, st)
    return added


def status(project):
    st = load_state(project)
    open_jobs = [j for j in st["jobs"] if j["status"] in ("queued", "running")]
    counts = {}
    for j in st["jobs"]:
        counts[j["status"]] = counts.get(j["status"], 0) + 1
    return {"counts": counts, "open": [{"job": j["job"], "status": j["status"], "prompt_id": j["prompt_id"],
                                        **({"progress": j["progress"]} if j.get("progress") else {})} for j in open_jobs],
            "failed": [{"job": j["job"], "error": j.get("error")} for j in st["jobs"] if j["status"] == "failed"]}


def watch(project, timeout_s=None, on_event=print):
    """Poll open jobs until they finish (or timeout_s passes). Collects outputs, retries OOMs and stalls once."""
    st = load_state(project)
    c = project.client
    wd = project.cfg["watchdog"]
    t_end = time.time() + timeout_s if timeout_s else None
    down_since = None
    mon = None
    if wd.get("progress", True):
        try:
            mon = c.progress()
        except Exception:
            mon = None
    while True:
        open_jobs = [j for j in st["jobs"] if j["status"] in ("queued", "running")]
        if not open_jobs:
            break
        if t_end and time.time() > t_end:
            break
        try:
            q = c.queue()
            down_since = None
        except Exception as e:
            down_since = down_since or time.time()
            if time.time() - down_since > 120:
                on_event(f"ComfyUI has been unreachable for 2 minutes ({e}). Restart it, then run 'nightshift watch' again.")
                save_state(project, st)
                return status(project)
            time.sleep(wd["poll_seconds"])
            continue
        for j in open_jobs:
            pid = j["prompt_id"]
            if pid in q["running"]:
                if j["status"] != "running":
                    j["status"], j["started"] = "running", time.time()
                    on_event(f"running  {j['job']}")
                limit = _limit_minutes(project, j.get("meta", {})) * 60
                age = c.log_age()
                quiet = mon.quiet(pid, j["started"]) if mon else None
                if quiet is not None:                      # ComfyUI's own progress messages: the reliable signal
                    if mon.info.get(pid):
                        j["progress"] = mon.info[pid]
                    calm = _progress_stall_seconds(project)
                    stalled = quiet > calm and (age is None or age > calm)
                    why_stall = "stalled (no progress from ComfyUI for %d min)" % (quiet // 60)
                else:                                       # no websocket: fall back to the log file
                    stalled = age is not None and age > _stall_seconds(project, j.get("meta", {}))
                    why_stall = "stalled (log silent %d min)" % ((age or 0) // 60)
                overtime = time.time() - j["started"] > limit
                if stalled or overtime:
                    why = why_stall if stalled else "over its time limit (%d min)" % (limit // 60)
                    on_event(f"WATCHDOG {j['job']} {why}: interrupting")
                    project.log("watchdog", job=j["job"], prompt_id=pid, reason=why)
                    try:
                        c.interrupt(pid)
                    except Exception:
                        pass
                    j["status"], j["error"] = "stalled", why
                    _retry(project, c, st, j, wd, on_event)
                continue
            if pid in q["pending"]:
                continue
            r = c.result(pid)
            if r["status"] == "success":
                j["status"], j["seconds"] = "done", r.get("seconds")
                j["outputs"] = [project.rel(p) for p in project.collect(r["files"])]
                on_event(f"done     {j['job']}  {r.get('seconds')} s  -> {', '.join(j['outputs']) or '(no files in project)'}")
                project.log("done", job=j["job"], prompt_id=pid, seconds=r.get("seconds"), outputs=j["outputs"])
            elif r["status"] == "error":
                err = r.get("error") or {}
                j["status"], j["error"] = "failed", err
                project.log("failed", job=j["job"], prompt_id=pid, error=err)
                oom = "OutOfMemory" in str(err.get("exception_type", "")) or "out of memory" in str(err.get("exception_message", "")).lower()
                on_event(f"FAILED   {j['job']}  {err.get('exception_type')}: {str(err.get('exception_message'))[:200]}")
                if oom:
                    try:
                        c.free()
                    except Exception:
                        pass
                    _retry(project, c, st, j, wd, on_event)
            elif r["status"] == "unknown" and time.time() - j["submitted"] > 30:
                j["status"], j["error"] = "lost", "not in queue or history (ComfyUI restarted?)"
                on_event(f"LOST     {j['job']}  (not in queue or history; ComfyUI restarted?)")
                _retry(project, c, st, j, wd, on_event)
        save_state(project, st)
        time.sleep(wd["poll_seconds"])
    save_state(project, st)
    return status(project)


def _retry(project, c, st, j, wd, on_event):
    if j.get("attempts", 1) > wd["retries"]:
        j["status"] = "failed"
        return
    try:
        prompt = json.load(open(project.path(j["job"]), encoding="utf-8"))
        pid = c.queue_prompt(prompt)
    except Exception as e:
        j["status"], j["error"] = "failed", f"retry failed: {e}"
        return
    j["status"] = "failed" if j["status"] == "failed" else j["status"]
    st["jobs"].append({**j, "prompt_id": pid, "status": "queued", "attempts": j.get("attempts", 1) + 1, "submitted": time.time(),
                       "error": None, "retry_of": j["prompt_id"]})
    j["status"] = "retried"
    on_event(f"retry    {j['job']}")
    project.log("retry", job=j["job"], prompt_id=pid)


def run(project, job_paths, timeout_s=None, on_event=print):
    submit(project, job_paths)
    return watch(project, timeout_s, on_event)
