"""The HUD overlay: lyrics that dodge faces, face brackets, beat-synced furniture, optional widgets.

Pipeline (after the cut is assembled):
  track()    face boxes per source clip (YuNet; smoothed, gaps bridged, cuts respected)
  mapfaces() map clip tracks through the edit (in / speed / conform / crop / scale) -> per-frame faces of the cut
  prep()     everything the page needs in one data.json: lyric lines with word timing, loudness per frame, beats,
             shots, faces, sections, style (project.json "overlay")
  render()   headless Chromium draws every frame to a transparent PNG (overlay/web/render.mjs)
  encode()   PNG frames -> VP9-with-alpha chunks of 9 s (216 frames) that finish.py keys over the cut
"""
import csv
import json
import os
import subprocess

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")


# ---- face tracks -------------------------------------------------------------------------------
def facetrack(src, out, cut_frames=None):
    """Per-frame face boxes [x, y, w, h] (or null) in the clip's pixel space (YuNet, the same detector the scorer uses)."""
    import cv2
    from ..score import _models
    det, _ = _models()
    cap = cv2.VideoCapture(src)
    fps = cap.get(cv2.CAP_PROP_FPS)
    Wd, Hd = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    scale = 640 / max(Wd, Hd)
    sw, sh = int(Wd * scale), int(Hd * scale)
    det.setInputSize((sw, sh))
    raw, cuts, prev_hist = [], [], None
    while True:
        ok, f = cap.read()
        if not ok:
            break
        small = cv2.resize(f, (sw, sh))
        g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        hist = cv2.normalize(cv2.calcHist([g], [0], None, [32], [0, 256]), None).flatten()
        cuts.append(prev_hist is not None and cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA) > 0.35)
        prev_hist = hist
        _, fs = det.detect(small)
        if fs is not None and len(fs):
            x, y, w, h = max(fs, key=lambda b: b[2] * b[3])[:4]
            raw.append([float(x) / scale, float(y) / scale, float(w) / scale, float(h) / scale])
        else:
            raw.append(None)
    n = len(raw)
    faces = [None] * n
    bounds = (list(cut_frames) if cut_frames else [i for i in range(n) if cuts[i]]) + [n]
    start = 0
    for end in bounds:   # smooth within shots, bridge gaps up to 8 frames, drop shots where the face is a blip
        seg = list(range(start, end))
        hits = [i for i in seg if raw[i] is not None]
        if len(hits) >= max(6, 0.33 * len(seg)):
            for i in seg:
                if raw[i] is None:
                    near = [j for j in hits if abs(j - i) <= 8]
                    if near:
                        raw[i] = raw[min(near, key=lambda j: abs(j - i))]
            state = None
            for i in seg:
                if raw[i] is None:
                    state = None
                    continue
                b = np.array(raw[i], float)
                state = b if state is None else state * 0.8 + b * 0.2
                faces[i] = [round(float(v), 1) for v in state]
        start = end
    with open(out, "w") as f:
        json.dump({"fps": fps, "w": Wd, "h": Hd, "faces": faces, "cuts": bounds[:-1]}, f)
    return sum(x is not None for x in faces), n


def track(project, cut_name="cut.json", on_event=print):
    """Track every clip in the cut that has no track yet (overlay/tracks/<clip>.json)."""
    cut = project.load(cut_name)
    d = project.path("overlay", "tracks")
    os.makedirs(d, exist_ok=True)
    done = []
    for s in cut["shots"]:
        src = project.path(s["src"]) if s.get("src") else None
        if not src or src.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue
        out = os.path.join(d, os.path.basename(src) + ".json")
        if os.path.exists(out):
            continue
        hit, n = facetrack(src, out)
        on_event(f"tracked {s['id']}: face on {hit}/{n} frames")
        done.append(s["id"])
    return done


def mapfaces(project, edl, cut_name="cut.json", out=None):
    """Per-frame face boxes of the finished cut, in final-frame pixels."""
    cut = {sh["id"]: sh for sh in project.load(cut_name)["shots"]}
    W, H = project.cfg["work_size"]
    CW, CH = project.cfg["crop"]
    FW, FH = project.cfg["final_size"]
    fps = project.cfg["fps"]
    cy = (H - CH) // 2
    cx = (W - CW) // 2
    s = FW / CW
    faces = []
    for r in csv.DictReader(open(edl)):
        n = int(r["frames"])
        tp = project.path("overlay", "tracks", os.path.basename(r["source"]) + ".json")
        tr = json.load(open(tp)) if os.path.exists(tp) else None
        sh = cut.get(r["shot"], {})
        for i in range(n):
            b = None
            if tr:
                src = tr["faces"]
                j = min(round(sh.get("in", 0.0) * fps + i * sh.get("speed", 1.0)), len(src) - 1)
                kx, ky = W / tr["w"], H / tr["h"]
                if j >= 0 and src[j]:
                    x, y, w, h = src[j]
                    b = [round((x * kx - cx) * s, 1), round((y * ky - cy) * s, 1), round(w * kx * s, 1), round(h * ky * s, 1)]
            faces.append(b)
    out = out or project.path("overlay", "faces.json")
    with open(out, "w") as f:
        json.dump({"faces": faces}, f)
    return out


# ---- data.json -------------------------------------------------------------------------------
def _sections(cfg, lines, secs):
    out = []
    txt = lambda l: " ".join(w["w"] for w in l["words"]).lower()
    for sec in cfg or []:
        t = None
        if sec.get("t") is not None:
            t = float(sec["t"])
        elif sec.get("line"):
            hits = [l for l in lines if txt(l) == sec["line"].lower()]
            k = int(sec.get("occurrence", 1)) - 1
            t = hits[k]["start"] if len(hits) > k else None
        elif sec.get("after"):
            q = next((l["end"] for l in lines if txt(l) == sec["after"].lower()), None)
            t = next((l["start"] for l in lines if q is not None and l["start"] > q), None)
        else:
            t = 0.0
        if t is not None and t < secs:
            out.append({"name": sec["name"], "t": max(0.0, t - 0.3)})
    return sorted(out, key=lambda s: s["t"])


def prep(project, edl, faces_json, out=None, seconds=None):
    import librosa
    from ..song import song_path
    fps = project.cfg["fps"]
    shots, f = [], 0
    for r in csv.DictReader(open(edl)):
        n = int(r["frames"])
        shots.append({"id": r["shot"], "f0": f, "f1": f + n})
        f += n
    secs = float(seconds) if seconds else f / fps
    nf = round(secs * fps)
    lines = [l for l in project.load("song/lines.json", {"lines": []})["lines"] if l["start"] < secs]
    y, sr = librosa.load(song_path(project), sr=22050, mono=True, duration=secs + 1)
    hop = sr // fps
    rms = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop)[0][:nf]
    rms = (rms / (np.percentile(rms, 98) + 1e-9)).clip(0, 1)
    bm = project.load("song/beatmap.json")
    ocfg = project.cfg.get("overlay", {})
    people = sorted({s["id"] for s in project.shots("shots_resolved.json" if os.path.exists(project.path("shots_resolved.json")) else "shots.json") if s.get("chars")})
    faces_all = json.load(open(faces_json))["faces"]
    data = {"bpm": round(bm["tempo_bpm_detected"]), "fps": fps, "frames": nf, "seconds": secs, "lines": lines,
            "rms": [round(float(v), 3) for v in rms], "beats": [x for x in bm["beats"] if x < secs],
            "downbeats": [x for x in bm["downbeats"] if x < secs], "shots": shots, "faces": faces_all[:nf], "people": people,
            "sections": _sections(ocfg.get("sections"), lines, secs), "style": ocfg.get("style", {})}
    illus = {}
    for name, p in (ocfg.get("illus") or {}).items():
        illus[name] = "file://" + os.path.abspath(project.path(p)).replace("\\", "/")
    if illus:
        data["illus"] = illus
    anim = project.load("overlay/illus_anim.json")
    if anim:
        data["illusAnim"] = anim
    out = out or project.path("overlay", "data.json")
    with open(out, "w") as fh:
        json.dump(data, fh)
    return {"out": out, "lines": len(lines), "sections": [(s["name"], round(s["t"], 2)) for s in data["sections"]], "frames": nf}


# ---- render + encode -------------------------------------------------------------------------------
def ensure_node_deps():
    if not os.path.isdir(os.path.join(WEB, "node_modules", "playwright-core")):
        subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=WEB, check=True, shell=os.name == "nt")


def render(data_json, frames_dir, first=0, last=None):
    ensure_node_deps()
    cmd = ["node", os.path.join(WEB, "render.mjs"), os.path.abspath(data_json), os.path.abspath(frames_dir), str(first)]
    if last is not None:
        cmd.append(str(last))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-3000:])
    return (r.stdout + r.stderr).strip()


def encode(frames_dir, out_dir, first_chunk=0, last_chunk=None, chunk_frames=216, fps=24):
    """PNG frames -> ov_00.webm, ov_01.webm ... (VP9 with alpha), chunk_frames each."""
    os.makedirs(out_dir, exist_ok=True)
    n = len([f for f in os.listdir(frames_dir) if f.endswith(".png")])
    last_chunk = (n - 1) // chunk_frames if last_chunk is None else last_chunk
    outs = []
    for i in range(first_chunk, last_chunk + 1):
        o = os.path.join(out_dir, f"ov_{i:02d}.webm")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-start_number", str(i * chunk_frames),
                        "-i", os.path.join(frames_dir, "f%05d.png"), "-frames:v", str(chunk_frames), "-c:v", "libvpx-vp9",
                        "-pix_fmt", "yuva420p", "-crf", "32", "-b:v", "0", "-deadline", "realtime", "-cpu-used", "8",
                        "-auto-alt-ref", "0", "-row-mt", "1", o], check=True)
        outs.append(o)
    return outs
