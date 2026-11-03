"""Clicks through the Studio home page in a headless browser and checks every control changes the form state.
Needs Python Playwright with Chromium (pip install playwright; playwright install chromium). No ComfyUI needed."""
import os, socket, subprocess, sys, tempfile, time
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("skip: Python Playwright is not installed"); return
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    root = tempfile.mkdtemp(prefix="ns_ui_")
    app = subprocess.Popen([sys.executable, "-m", "nightshift", "app", "--root", root, "--no-browser", "--port", str(port)],
                           cwd=os.path.dirname(HERE), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(3)
        with sync_playwright() as pw:
            b = pw.chromium.launch(); p = b.new_page(viewport={"width": 1300, "height": 1000})
            errors = []; p.on("pageerror", lambda e: errors.append(str(e)))
            p.goto(f"http://127.0.0.1:{port}/"); p.wait_for_timeout(1200)
            st = lambda k: p.evaluate(f"state[{k!r}]")
            checks = []
            p.click(".dir[data-v=yolo]"); checks.append(("06 Run to End", st("mode") == "yolo"))
            p.click(".dir[data-v=director]"); checks.append(("06 Checkpoint", st("mode") == "director"))
            p.click(".scene[data-v=desert-highway]"); checks.append(("03 one place", st("scenes") == ["desert-highway"]))
            p.click(".scene[data-v=snow-motel]"); checks.append(("03 click moves it", st("scenes") == ["snow-motel"]))
            p.hover(".scene[data-v=living-room]"); p.click(".scene[data-v=living-room] .add")
            checks.append(("03 + adds", st("scenes") == ["snow-motel", "living-room"]))
            p.click(".scene[data-v=snow-motel] .ord"); checks.append(("03 number removes", st("scenes") == ["living-room"]))
            for seg, key, v in (("aspect", "aspect", "16:9"), ("length", "length", "medium"), ("ovLyrics", "ovLyrics", "on"),
                                ("ovHud", "ovHud", "on"), ("lyrCol", "lyrCol", "contrast"), ("songSrc", "songSrc", "upload"),
                                ("who", "who", "man")):
                p.click(f"#{seg} button[data-v='{v}']"); checks.append((f"{seg} -> {v}", st(key) == v))
            p.click("#tabs button[data-v=agent]"); checks.append(("tab: Full Agent Mode", st("tab") == "agent"))
            b.close()
        bad = [n for n, ok in checks if not ok]
        print("\n".join(f"{'ok  ' if ok else 'FAIL'} {n}" for n, ok in checks))
        if errors or bad:
            raise SystemExit(f"UI test failed: {bad} {errors}")
        print("ui ok")
    finally:
        app.terminate()


if __name__ == "__main__":
    main()
