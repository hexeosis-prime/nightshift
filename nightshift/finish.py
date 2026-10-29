"""Finish a cut: grade + per-shot lifts + overlay (VP9 with alpha) + halftone + grain, in short chunks.

Chunks keep each ffmpeg call short (and resumable): a 3-minute video is ~20 chunks of 9 s, and a change late in the
video only re-renders the chunks it touches. The overlay can be one .webm or a chunk pattern (ov_%02d.webm) whose
chunks line up with these.

lifts: [[t0, t1, k], ...] in cut seconds: raises shadows/mids by k only inside those windows (e.g. a face that sits
too dark against the grade).
"""
import math
import os
import subprocess

from . import grade
from .assemble import duration


def make_halftone(out, size=(1920, 1080), cell=6, strength=0.18):
    """A subtle dot screen for the multiply pass (white paper, light grey dots)."""
    import numpy as np
    from PIL import Image
    W, H = size
    y, x = np.mgrid[0:H, 0:W]
    cx, cy = (x % cell) - cell / 2 + 0.5, (y % cell) - cell / 2 + 0.5
    d = np.sqrt(cx ** 2 + cy ** 2) / (cell / 2)
    v = 1 - strength * np.clip(1.2 - d, 0, 1)
    Image.fromarray((v * 255).astype("uint8"), "L").convert("RGB").save(out)
    return out


def _graph(look, lifts, a0, seg, overlay, halftone, grain):
    base = grade.chain(look, "[0:v]", "[g0]") + ";"
    lf = [f"curves=all='0/0 0.18/{0.18 + k:.3f} 0.5/{0.5 + k * 0.7:.3f} 1/1':enable='between(t,{t0 - a0:.3f},{t1 - a0:.3f})'"
          for t0, t1, k in lifts if t1 > a0 and t0 < a0 + seg]
    g = base + "[g0]" + (",".join(lf) if lf else "null") + "[base];"
    cur, n = "[base]", 1
    if overlay:
        g += f"{cur}[{n}:v]overlay=format=auto[o];"
        cur, n = "[o]", n + 1
    if halftone:
        g += f"[{n}:v]format=gbrp[ht];{cur}format=gbrp[og];[og][ht]blend=all_mode=multiply:all_opacity=0.45:shortest=1[h];"
        cur = "[h]"
    g += f"{cur}" + (f"noise=alls={grain}:allf=t," if grain else "") + "format=yuv420p[v]"
    return g


def chunks(cut_mp4, chunk_s=9.0):
    return math.ceil(duration(cut_mp4) / chunk_s - 1e-6)


def finish_chunk(cut_mp4, out, i, look="A2_portra_dusk_plus", lifts=(), overlay=None, halftone=None, grain=9, chunk_s=9.0, fps=24):
    dur = duration(cut_mp4)
    parts = os.path.splitext(out)[0] + "_parts"
    os.makedirs(parts, exist_ok=True)
    a = i * chunk_s
    frames = round(min(chunk_s, dur - a) * fps)
    cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", str(chunk_s), "-i", cut_mp4]
    if overlay:
        chunked = "%" in overlay
        cmd += ["-ss", "0" if chunked else str(a), "-t", str(chunk_s), "-c:v", "libvpx-vp9", "-i", (overlay % i) if chunked else overlay]
    if halftone:
        cmd += ["-loop", "1", "-framerate", str(fps), "-i", halftone]
    cmd += ["-filter_complex", _graph(look, list(lifts), a, chunk_s, overlay, halftone, grain), "-map", "[v]", "-an",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-frames:v", str(frames), os.path.join(parts, f"p{i:02d}.mp4")]
    subprocess.run(cmd, check=True)
    return os.path.join(parts, f"p{i:02d}.mp4")


def join(cut_mp4, out, chunk_s=9.0):
    parts = os.path.splitext(out)[0] + "_parts"
    n = chunks(cut_mp4, chunk_s)
    lst = os.path.join(parts, "list.txt")
    with open(lst, "w") as f:
        f.write("".join(f"file 'p{i:02d}.mp4'\n" for i in range(n)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", cut_mp4,
                    "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", "-shortest", out], check=True)
    return out


def finish(cut_mp4, out, look="A2_portra_dusk_plus", lifts=(), overlay=None, halftone=None, grain=9, chunk_s=9.0,
           redo=(), on_event=print):
    """All chunks (existing ones are kept unless listed in redo), then join."""
    n = chunks(cut_mp4, chunk_s)
    parts = os.path.splitext(out)[0] + "_parts"
    for i in range(n):
        if os.path.exists(os.path.join(parts, f"p{i:02d}.mp4")) and i not in redo:
            continue
        finish_chunk(cut_mp4, out, i, look, lifts, overlay, halftone, grain, chunk_s)
        on_event(f"finish chunk {i + 1}/{n}")
    return join(cut_mp4, out, chunk_s)


def web_copy(src, out, mbps=14):
    """Posting copy: H.264 at a fixed bitrate, AAC 320k, faststart (14 Mb/s keeps a 3-minute 1080p video under X's 512 MB)."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-c:v", "libx264", "-preset", "slow", "-b:v", f"{mbps}M",
                    "-maxrate", f"{int(mbps * 1.5)}M", "-bufsize", f"{mbps * 2}M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k",
                    "-movflags", "+faststart", out], check=True)
    return out
