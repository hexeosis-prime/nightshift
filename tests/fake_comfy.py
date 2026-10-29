"""A stand-in ComfyUI for tests: speaks the HTTP API, 'renders' placeholder files where the save nodes say.

    python tests/fake_comfy.py <comfy_dir> [port]
"""
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SAVE = {"SaveImage": ("images", ".png", "_"), "SaveVideo": ("images", ".mp4", "_"), "VHS_VideoCombine": ("gifs", ".mp4", ""),
        "SaveAudioAdvanced": ("audio", ".mp3", "_")}


class Fake:
    def __init__(self, root, render_seconds=0.2, fail_first=None):
        self.root = root
        self.queue, self.running, self.history = [], None, {}
        self.lock = threading.Lock()
        self.render_seconds = render_seconds
        self.fail_first = fail_first          # substring of a prefix: first job matching it fails with OOM
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        while True:
            with self.lock:
                job = self.queue.pop(0) if self.queue and not self.running else None
                if job:
                    self.running = job
            if not job:
                time.sleep(0.05)
                continue
            pid, prompt = job
            t0 = time.time() * 1000
            time.sleep(self.render_seconds)
            outputs, err = {}, None
            for nid, node in prompt.items():
                spec = SAVE.get(node["class_type"])
                if not spec:
                    continue
                key, ext, tail = spec
                prefix = node["inputs"]["filename_prefix"]
                if self.fail_first and self.fail_first in prefix:
                    self.fail_first = None
                    err = {"node_id": nid, "node_type": node["class_type"], "exception_type": "torch.OutOfMemoryError",
                           "exception_message": "CUDA out of memory"}
                    break
                sub, base = os.path.split(prefix)
                d = os.path.join(self.root, "output", sub)
                os.makedirs(d, exist_ok=True)
                n = 1
                while os.path.exists(os.path.join(d, f"{base}_{n:05d}{tail}{ext}")):
                    n += 1
                fn = f"{base}_{n:05d}{tail}{ext}"
                path = os.path.join(d, fn)
                if ext == ".png":
                    cmd = ["-f", "lavfi", "-i", "testsrc2=s=1280x768", "-frames:v", "1"]
                elif ext == ".mp4":
                    cmd = ["-f", "lavfi", "-i", "testsrc2=s=1280x768:r=24", "-t", "13", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast"]
                else:
                    cmd = ["-f", "lavfi", "-i", "sine=frequency=330:duration=20"]
                subprocess.run(["ffmpeg", "-v", "error", "-y", *cmd, path], check=True)
                outputs[nid] = {key: [{"filename": fn, "subfolder": sub, "type": "output"}]}
            msgs = [["execution_start", {"timestamp": t0}]]
            if err:
                msgs.append(["execution_error", {**err, "timestamp": time.time() * 1000}])
            else:
                msgs.append(["execution_success", {"timestamp": time.time() * 1000}])
            with self.lock:
                self.history[pid] = {"prompt": [0, pid, prompt], "outputs": {} if err else outputs,
                                     "status": {"status_str": "error" if err else "success", "completed": not err, "messages": msgs}}
                self.running = None


def serve(root, port=8199, **kw):
    fake = Fake(root, **kw)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _json(self, obj, code=200):
            b = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            if self.path.startswith("/system_stats"):
                return self._json({"devices": [{"name": "fake GPU", "vram_total": 24 * 2**30, "vram_free": 20 * 2**30}]})
            if self.path.startswith("/object_info"):
                return self._json({})
            if self.path.startswith("/queue"):
                with fake.lock:
                    run = [[0, fake.running[0], {}, {}, []]] if fake.running else []
                    pend = [[i, p[0], {}, {}, []] for i, p in enumerate(fake.queue)]
                return self._json({"queue_running": run, "queue_pending": pend})
            if self.path.startswith("/history/"):
                pid = self.path.split("/")[-1]
                with fake.lock:
                    h = fake.history.get(pid)
                return self._json({pid: h} if h else {})
            if self.path.startswith("/view"):
                from urllib.parse import parse_qs, urlparse
                q = parse_qs(urlparse(self.path).query)
                p = os.path.join(root, q["type"][0], q.get("subfolder", [""])[0], q["filename"][0])
                b = open(p, "rb").read()
                self.send_response(200)
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)
                return
            self._json({}, 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(n)
            if self.path == "/prompt":
                prompt = json.loads(body)["prompt"]
                pid = str(uuid.uuid4())
                with fake.lock:
                    fake.queue.append((pid, prompt))
                return self._json({"prompt_id": pid, "number": len(fake.queue), "node_errors": {}})
            if self.path == "/upload/image":
                # minimal multipart parse: good enough for our own client
                ctype = self.headers["Content-Type"]
                boundary = ctype.split("boundary=")[1].encode()
                fields, fname, data = {}, None, None
                for part in body.split(b"--" + boundary):
                    if b"Content-Disposition" not in part:
                        continue
                    head, _, val = part.partition(b"\r\n\r\n")
                    val = val[:-2] if val.endswith(b"\r\n") else val
                    name = head.split(b'name="')[1].split(b'"')[0].decode()
                    if b"filename=" in head:
                        fname, data = head.split(b'filename="')[1].split(b'"')[0].decode(), val
                    else:
                        fields[name] = val.decode()
                d = os.path.join(root, fields.get("type", "input"), fields.get("subfolder", ""))
                os.makedirs(d, exist_ok=True)
                open(os.path.join(d, fname), "wb").write(data)
                return self._json({"name": fname, "subfolder": fields.get("subfolder", ""), "type": fields.get("type", "input")})
            if self.path in ("/interrupt", "/free", "/queue"):
                return self._json({})
            self._json({}, 404)

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, fake


if __name__ == "__main__":
    root = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8199
    for d in ("input", "output"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    serve(root, port)
    print(f"fake ComfyUI on http://127.0.0.1:{port} serving {root}")
    while True:
        time.sleep(3600)
