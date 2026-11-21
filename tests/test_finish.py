"""Finish on a vertical (1080-wide) cut: the frame is widened to a multiple of 64 for the grade and cropped back, so the
right edge matches its neighbors (Nov 20: every 9:16 finish had a flat wrong-colored 8-pixel stripe down the right edge)."""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nightshift import finish as F


def edge(path, x, w=8):
    """Mean RGB of a w-wide column strip starting at x, over the middle half of the first frame."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-frames:v", "1", "-vf", f"crop={w}:ih/2:{x}:ih/4,scale=1:1:flags=area",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return tuple(out[:3])


def main():
    g = F._graph("A_portra_dusk", [], 0, 9, None, "/h.png", 9, (1080, 1920))
    assert g.startswith("[0:v]pad=1088:1920:0:0,fillborders=right=8:mode=smear,") and "crop=1080:1920:0:0,format=yuv420p[v]" in g, g
    assert "pad=" not in F._graph("A_portra_dusk", [], 0, 9, None, None, 9, (1920, 1080))
    print("ok   graph: 1080 wide is padded to 1088 and cropped back; 1920 untouched")

    d = tempfile.mkdtemp(prefix="ns_finish_")
    cut = os.path.join(d, "cut.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "gradients=s=1080x1920:d=1:r=24:c0=0x8899bb:c1=0xd8c8a0",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", cut], check=True)
    part = F.finish_chunk(cut, os.path.join(d, "pass.mp4"), 0, look="A_portra_dusk", grain=0, chunk_s=9.0)
    assert F.size(part) == (1080, 1920), F.size(part)
    a, b = edge(part, 1064), edge(part, 1072)
    assert max(abs(x - y) for x, y in zip(a, b)) <= 12, (a, b)
    print("ok   finish: 1080x1920 out, right edge", b, "matches its neighbor", a)
    print("finish ok")


if __name__ == "__main__":
    main()
