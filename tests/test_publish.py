"""Shared files carry no prompts: ComfyUI-style metadata in a PNG and an MP4 is gone from publish() copies and from
Nightshift's own encodes."""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from PIL import Image, PngImagePlugin
from nightshift import publish as PUB
from nightshift.project import init


def main():
    d = tempfile.mkdtemp(prefix="ns_pub_")
    p = init(os.path.join(d, "demo"), "demo")
    png = p.path("stills", "s01_flux_00001_.png")
    info = PngImagePlugin.PngInfo()
    info.add_text("prompt", json.dumps({"3": {"inputs": {"text": "a secret prompt"}}}))
    info.add_text("workflow", "{}")
    Image.new("RGB", (64, 48), (200, 30, 30)).save(png, pnginfo=info)
    mp4 = p.path("clips", "s01_ff_00001.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=128x96:r=24", "-t", "0.5", "-c:v", "libx264",
                    "-metadata", "comment=" + json.dumps({"prompt": "a secret prompt"}), "-metadata", "title=workflow", mp4], check=True)
    assert PUB.carried(png) == ["prompt", "workflow"], PUB.carried(png)
    assert "comment" in PUB.carried(mp4) and "title" in PUB.carried(mp4)
    rows = PUB.publish(p, ["stills/*.png", "clips/*.mp4"])
    assert [r["file"] for r in rows] == ["out/publish/s01_flux_00001_.png", "out/publish/s01_ff_00001.mp4"], rows
    for r in rows:
        assert PUB.carried(p.path(r["file"])) == [], r
    assert Image.open(p.path(rows[0]["file"])).getpixel((5, 5)) == (200, 30, 30)
    print("ok   publish: PNG text chunks and video tags removed, pixels kept")

    # Nightshift's own encodes drop the clip's tags (a plain re-encode would carry them into the cut)
    from nightshift.finish import web_copy
    out = web_copy(mp4, os.path.join(d, "web.mp4"))
    assert PUB.carried(out) == [], PUB.carried(out)
    print("ok   own encodes carry nothing (posting copy checked)")
    print("publish ok")


if __name__ == "__main__":
    main()
