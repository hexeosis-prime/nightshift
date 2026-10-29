"""Review material: what the director looks at between passes.

numbered()  review copy with "NN  shot-id" burned top-left (1280 wide), so notes can say "shot 26" and mean one thing
ab()        old take | new take side by side, each in its song slot with the song underneath
frames()    contact sheet: first / middle / last frame of each clip, labelled (cheap to send, quick to read)
"""
import csv
import json
import os
import subprocess

from .assemble import Cut, duration

FONT_CANDIDATES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/lato/Lato-Black.ttf",
                   "C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf"]


def _font():
    f = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
    return f"fontfile='{f.replace(':', chr(92) + ':')}':" if f else ""


def numbered(src, edl, out, parts=4, on_event=print):
    rows = list(csv.DictReader(open(edl)))
    T = float(rows[-1]["song_out_s"]) - float(rows[0]["song_in_s"])
    t_first = float(rows[0]["song_in_s"])
    pdir = os.path.splitext(out)[0] + "_rparts"
    os.makedirs(pdir, exist_ok=True)
    font = _font()
    for i in range(parts):
        a = round(T * i / parts * 24) / 24
        b = round(T * (i + 1) / parts * 24) / 24
        dt = []
        for k, r in enumerate(rows, 1):
            s0, s1 = float(r["song_in_s"]) - t_first - a, float(r["song_out_s"]) - t_first - a
            if s1 <= 0 or s0 >= b - a:
                continue
            dt.append(f"drawtext={font}text='{k:02d}  {r['shot']}':x=20:y=16:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.55:"
                      f"boxborderw=8:enable='between(t,{max(0, s0):.3f},{s1 - 0.001:.3f})'")
        fs = os.path.join(pdir, f"f{i}.txt")
        with open(fs, "w") as f:
            f.write("scale=1280:-2" + ("," + ",".join(dt) if dt else ""))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.4f}", "-t", f"{b - a:.4f}", "-i", src, "-filter_script:v", fs, "-an",
                        "-c:v", "libx264", "-crf", "24", "-preset", "veryfast", os.path.join(pdir, f"r{i}.mp4")], check=True)
        on_event(f"review part {i + 1}/{parts}")
    with open(os.path.join(pdir, "list.txt"), "w") as f:
        f.write("".join(f"file 'r{i}.mp4'\n" for i in range(parts)))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(pdir, "list.txt"), "-i", src,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], check=True)
    return out


def ab(project, pairs, out, cut_name="cut.json"):
    """pairs: [(shot_id, new_clip)] -> old (the cut's src) | new, in the shot's slot, with the song."""
    cut = Cut(project.path(cut_name))
    slot = {s["id"]: (cut.cuts[i], cut.cuts[i + 1], s) for i, s in enumerate(cut.shots)}
    d = project.path("review", "ab_parts")
    os.makedirs(d, exist_ok=True)
    segs = []
    for sid, new in pairs:
        t0, t1, s = slot[sid]
        dur = t1 - t0
        old = cut.P(s["src"])
        new = new if os.path.isabs(new) else project.path(new)
        seg = os.path.join(d, f"{sid}_{os.path.basename(new)}.mp4")
        fc = ("[0:v]scale=960:540:force_original_aspect_ratio=increase,crop=960:540,fps=24,setsar=1[a];"
              "[1:v]scale=960:540:force_original_aspect_ratio=increase,crop=960:540,fps=24,setsar=1[b];[a][b]hstack[v]")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(s.get("in", 0)), "-t", str(dur), "-i", old, "-t", str(dur), "-i", new,
                        "-ss", str(t0), "-t", str(dur), "-i", cut.song, "-filter_complex", fc, "-map", "[v]", "-map", "2:a",
                        "-c:v", "libx264", "-crf", "26", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", seg],
                       check=True)
        segs.append(seg)
    with open(os.path.join(d, "list.txt"), "w") as f:
        f.write("".join(f"file '{s}'\n" for s in segs))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(d, "list.txt"), "-c", "copy", out], check=True)
    return out


def frames(clips, out, fractions=(0.0, 0.5, 0.97), width=400):
    """One row per clip: frames at the given fractions, file name on the first."""
    import cv2
    import numpy as np
    rows = []
    for c in clips:
        cap = cv2.VideoCapture(c)
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        cells = []
        for fr in fractions:
            cap.set(cv2.CAP_PROP_POS_FRAMES, min(n - 1, int(n * fr)))
            ok, im = cap.read()
            if not ok:
                im = np.zeros((int(width * 0.6), width, 3), np.uint8)
            h = int(im.shape[0] * width / im.shape[1])
            cells.append(cv2.resize(im, (width, h)))
        h = min(x.shape[0] for x in cells)
        row = np.hstack([x[:h] for x in cells])
        cv2.rectangle(row, (0, 0), (row.shape[1], 22), (0, 0, 0), -1)
        cv2.putText(row, os.path.basename(c)[:90], (6, 16), 0, 0.5, (0, 255, 255), 1)
        rows.append(row)
    if not rows:
        raise ValueError("no clips")
    w = max(r.shape[1] for r in rows)
    rows = [np.pad(r, ((0, 0), (0, w - r.shape[1]), (0, 0))) for r in rows]
    cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 82])
    return out


def takes_sheet(project, sid, out=None):
    clips = project.renders("clips", f"{sid}_*.mp4")
    out = out or project.path("review", f"takes_{sid}.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    return frames(clips, out)
