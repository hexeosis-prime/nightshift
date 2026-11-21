"""The watchdog's ears: the websocket listener hears ComfyUI's progress messages (stdlib client against a tiny server),
and the stall rule uses them instead of log silence when it can."""
import base64, hashlib, json, os, socket, sys, threading, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from nightshift import comfy as C

GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def frame(op, payload):
    n = len(payload)
    head = bytes([0x80 | op]) + (bytes([n]) if n < 126 else bytes([126]) + n.to_bytes(2, "big"))
    return head + payload


def server(got):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)

    def run():
        conn, _ = srv.accept()
        req = b""
        while b"\r\n\r\n" not in req:
            req += conn.recv(4096)
        got["path"] = req.split(b" ")[1].decode()
        key = [l.split(b": ")[1] for l in req.split(b"\r\n") if l.lower().startswith(b"sec-websocket-key")][0]
        acc = base64.b64encode(hashlib.sha1(key + GUID).digest())
        conn.sendall(b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                     b"Sec-WebSocket-Accept: " + acc + b"\r\n\r\n")
        conn.sendall(frame(1, json.dumps({"type": "status", "data": {"status": {}}}).encode()))
        conn.sendall(frame(1, json.dumps({"type": "progress", "data": {"value": 3, "max": 20, "prompt_id": "abc", "node": "12"}}).encode()))
        conn.sendall(frame(9, b"hi"))                                    # ping: the client must answer pong
        b0, b1 = conn.recv(2)
        mask = conn.recv(4)
        data = bytes(b ^ mask[i % 4] for i, b in enumerate(conn.recv(b1 & 0x7F)))
        got["pong"] = (b0 & 0x0F, data)
        conn.sendall(frame(2, b"\x00\x00\x00\x01" + b"x" * 300))         # a preview image
        long = {"type": "executing", "data": {"node": "57", "prompt_id": "def", "pad": "y" * 300}}
        conn.sendall(frame(1, json.dumps(long).encode()))               # 126-length frame
        time.sleep(1.5)
        conn.close()
        srv.close()
    threading.Thread(target=run, daemon=True).start()
    return srv.getsockname()[1]


def main():
    got = {}
    port = server(got)
    mon = C.Progress(f"http://127.0.0.1:{port}", "nightshift-test")
    t0 = time.time()
    while not ("def" in mon.last and "pong" in got) and time.time() - t0 < 5:
        time.sleep(0.05)
    mon.stop()
    assert got["path"] == "/ws?clientId=nightshift-test", got
    assert {k: mon.info["abc"][k] for k in ("value", "max", "node")} == {"value": 3, "max": 20, "node": "12"}, mon.info
    assert got["pong"] == (0xA, b"hi"), got
    assert mon.preview and mon.info["def"]["node"] == "57"
    assert mon.quiet("abc") < 5 and mon.quiet("nobody") < 5          # a preview counts as life for the running job
    print("ok   websocket listener: progress, executing, preview, ping/pong, 126-byte frames")

    # the stall rule: with progress coming in, a quiet log doesn't kill a long job
    class P:
        cfg = {"watchdog": {"stall_minutes": 6, "progress_stall_minutes": 10}}
    assert C._progress_stall_seconds(P) == 600
    print("ok   stall rule: 10 min with no progress and no log line (was: log silence alone)")

    # the "Model Initializing" hang: a sampler node that started and never reported a step
    hang = C.Progress("http://127.0.0.1:9", "nightshift-hang")
    hang.stop()
    hang.connected = True
    msg = lambda kind, **d: hang._message(json.dumps({"type": kind, "data": dict(d, prompt_id="p1")}))
    msg("executing", node="5")                                          # a text encoder: no steps, fine
    msg("progress", node="5", value=1, max=1)
    msg("executing", node="9")                                          # the sampler starts
    hang.info["p1"]["since"] -= 200
    node, waited = hang.before_first_step("p1")
    assert node == "9" and 199 < waited < 210, hang.info
    msg("progress", node="9", value=1, max=8)                           # its first step: no longer stuck
    assert hang.before_first_step("p1") is None
    msg("executing", node="11")                                         # the upscale pass's sampler: a new clock
    assert hang.before_first_step("p1")[1] < 5
    assert "SamplerCustomAdvanced" in C.SAMPLERS
    print("ok   stuck before the first step: per node, cleared by a step, restarted by the next sampler")

    # its retry budget: one more than an ordinary stall
    class Q:
        def __init__(self):
            self.n = 0
        def queue_prompt(self, prompt):
            self.n += 1
            return f"r{self.n}"
    import tempfile
    d = tempfile.mkdtemp()
    open(os.path.join(d, "j.json"), "w").write("{}")
    class PP:
        path = staticmethod(lambda *a: os.path.join(d, *a))
        log = staticmethod(lambda *a, **k: None)
    wd = {"retries": 1}
    for extra, want in ((0, "failed"), (1, "retried")):
        st = {"jobs": []}
        j = {"job": "j.json", "prompt_id": "x", "status": "stalled", "attempts": 2}
        C._retry(PP, Q(), st, j, wd, lambda *_: None, extra=extra)
        assert j["status"] == want, (extra, j)
    print("ok   a job stuck at the start gets one extra try")

    # no websocket (an old ComfyUI, a proxy): quiet() says so and the watchdog falls back to the log
    dead = C.Progress("http://127.0.0.1:9", "nightshift-none")
    time.sleep(0.5)
    assert dead.quiet("abc") is None
    dead.stop()
    print("ok   no websocket: falls back to the log rule")

    # a GPU fault of the moment is retried once like an OOM; a real job error is not
    assert C.retryable({"exception_type": "RuntimeError", "exception_message": "Fault failed: 2\n"})
    assert C.retryable({"exception_type": "torch.OutOfMemoryError", "exception_message": "CUDA out of memory"})
    assert not C.retryable({"exception_type": "ValueError", "exception_message": "Image not found: x.png"})
    print("ok   retry: OOM and allocator faults yes, job errors no")
    print("progress ok")


if __name__ == "__main__":
    main()
