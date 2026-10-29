"""ComfyUI over its HTTP API (no extra dependencies), plus the queue runner with a stall/OOM watchdog.

Works against a ComfyUI on this machine or across the network (--listen on the GPU box). When the ComfyUI folder is
known (project comfy.dir), the watchdog also watches its log file: on a long LTX job the log keeps moving (sampler
progress bars, model loads), so a log that stops moving while a job is "running" is a stall.
"""
import json
import mimetypes
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


class ComfyError(Exception):
    pass


class Comfy:
    def __init__(self, url="http://127.0.0.1:8188", comfy_dir=None, timeout=60):
        self.url = url.rstrip("/")
        self.dir = comfy_dir
        self.timeout = timeout
        self.client_id = "nightshift-" + uuid.uuid4().hex[:8]

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

    def queue_prompt(self, prompt):
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
    return {"counts": counts, "open": [{"job": j["job"], "status": j["status"], "prompt_id": j["prompt_id"]} for j in open_jobs],
            "failed": [{"job": j["job"], "error": j.get("error")} for j in st["jobs"] if j["status"] == "failed"]}


def watch(project, timeout_s=None, on_event=print):
    """Poll open jobs until they finish (or timeout_s passes). Collects outputs, retries OOMs and stalls once."""
    st = load_state(project)
    c = project.client
    wd = project.cfg["watchdog"]
    t_end = time.time() + timeout_s if timeout_s else None
    down_since = None
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
                stalled = age is not None and age > wd["stall_minutes"] * 60
                overtime = time.time() - j["started"] > limit
                if stalled or overtime:
                    why = "stalled (log silent %d min)" % (age // 60) if stalled else "over its time limit (%d min)" % (limit // 60)
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
