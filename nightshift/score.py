"""Scoring takes so a person (director mode) or the agent (yolo mode) can pick fast.

face identity  YuNet detection + SFace embedding, cosine against the faces on the character sheet.
               ~0.36+ is the usual same-person threshold; higher = closer to the sheet. In practice it caught faces
               that drifted (age, narrower face) before a human noticed, and it ranks seed/wording variants well.
yaw            head turn from the 5 YuNet landmarks: negative = looking toward screen-left. Used to time graphics to
               head turns and to catch takes that end in profile.
mouth activity mean frame-to-frame change in the lower third of the face: a rough "is she actually singing" check.
Models: scripts/get_models.py downloads yunet.onnx and sface.onnx into models/.
"""
import glob
import json
import os

import numpy as np

MODELS = os.environ.get("NIGHTSHIFT_MODELS", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models")))
_det = _rec = None


def _cv():
    import cv2
    return cv2


def _models():
    global _det, _rec
    if _det is None:
        cv2 = _cv()
        y, s = os.path.join(MODELS, "yunet.onnx"), os.path.join(MODELS, "sface.onnx")
        if not (os.path.exists(y) and os.path.exists(s)):
            raise FileNotFoundError(f"face models missing in {MODELS}: run python scripts/get_models.py")
        _det = cv2.FaceDetectorYN.create(y, "", (320, 320), 0.6)
        _rec = cv2.FaceRecognizerSF.create(s, "")
    return _det, _rec


def faces(img):
    det, _ = _models()
    cv2 = _cv()
    h, w = img.shape[:2]
    s = 1280 / max(h, w)
    if s < 1:
        img = cv2.resize(img, (int(w * s), int(h * s)))
        h, w = img.shape[:2]
    det.setInputSize((w, h))
    _, f = det.detect(img)
    return img, ([] if f is None else sorted(f, key=lambda r: -r[2] * r[3]))


def embed(img, f):
    _, rec = _models()
    return rec.feature(rec.alignCrop(img, f))


def sheet_refs(path, n=6):
    """Embeddings of up to n faces on a character sheet (front, 3/4, profile ...)."""
    cv2 = _cv()
    im = cv2.imread(path)
    if im is None:
        raise FileNotFoundError(path)
    im, fs = faces(im)
    return [embed(im, f) for f in fs[:n]]


def match(refs, e):
    cv2 = _cv()
    _, rec = _models()
    return max(rec.match(e, r, cv2.FaceRecognizerSF_FR_COSINE) for r in refs)


def score_image(refs, path_or_img):
    cv2 = _cv()
    im = cv2.imread(path_or_img) if isinstance(path_or_img, str) else path_or_img
    if im is None:
        return None
    im, fs = faces(im)
    if not len(fs):
        return None
    return float(match(refs, embed(im, fs[0])))


def face_quality(path):
    """How usable the face on a sheet is: detector confidence x size x sharpness, 0..1 (None = no face found)."""
    cv2 = _cv()
    im = cv2.imread(path)
    if im is None:
        return None
    im, fs = faces(im)
    if not len(fs):
        return None
    f = fs[0]
    x, y, w, h = [max(0, int(v)) for v in f[:4]]
    crop = cv2.cvtColor(im[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY) if w > 0 and h > 0 else None
    sharp = float(cv2.Laplacian(crop, cv2.CV_64F).var()) if crop is not None and crop.size else 0.0
    area = (w * h) / float(im.shape[0] * im.shape[1])
    return round(float(f[14]) * min(1.0, area * 25) * (0.5 + 0.5 * min(1.0, sharp / 300.0)), 3)


def yaw(f):
    """Signed head turn from YuNet landmarks: nose offset from the eye midpoint, in eye-distances."""
    rex, rey, lex, ley, nx, ny = f[4], f[5], f[6], f[7], f[8], f[9]
    mid = (rex + lex) / 2
    d = max(abs(lex - rex), 1e-3)
    return float((nx - mid) / d)


def clip_frames(path, fractions=(0.15, 0.5, 0.85)):
    cv2 = _cv()
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out = []
    for fr in fractions:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(n * fr))
        ok, im = cap.read()
        if ok:
            out.append((int(n * fr), im))
    return out


def score_clip(refs, path, fractions=(0.15, 0.5, 0.85)):
    sc = [s for _, im in clip_frames(path, fractions) if (s := score_image(refs, im)) is not None]
    return float(np.median(sc)) if sc else None


def yaw_series(path, step=1):
    cv2 = _cv()
    cap = cv2.VideoCapture(path)
    out, i = [], 0
    while True:
        ok, im = cap.read()
        if not ok:
            break
        if i % step == 0:
            _, fs = faces(im)
            out.append(round(yaw(fs[0]), 3) if len(fs) else None)
        i += 1
    return out


def mouth_activity(path, windows=None):
    cv2 = _cv()
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ok, im = cap.read()
        if not ok:
            break
        frames.append(im)
    windows = windows or [(0, len(frames))]
    res = []
    for a, b in windows:
        vals, prev = [], None
        for i in range(a, min(b, len(frames))):
            im, fs = faces(frames[i])
            if not len(fs):
                prev = None
                continue
            x, y, w, h = [int(v) for v in fs[0][:4]]
            m = im[y + int(h * 0.62): y + h, x + int(w * 0.2): x + int(w * 0.8)]
            if m.size == 0:
                prev = None
                continue
            m = cv2.resize(cv2.cvtColor(m, cv2.COLOR_BGR2GRAY), (48, 24)).astype(float)
            if prev is not None:
                vals.append(np.abs(m - prev).mean())
            prev = m
        res.append({"window": [a, b], "activity": round(float(np.mean(vals)), 2) if vals else None, "samples": len(vals)})
    return res


# ---- project-level -------------------------------------------------------------------------------
def refs_for(project, ch_key, world, cache={}):
    c = project.canon["characters"][ch_key]
    p = (c.get("sheet") or {}).get(world) or (c.get("sheet") or {}).get("real")
    path = p if os.path.isabs(p) else project.path(p)
    if not os.path.exists(path) and project.comfy_dir:
        path = os.path.join(project.comfy_dir, "input", p)
    key = (path,)
    if key not in cache:
        cache[key] = sheet_refs(path)
    return cache[key]


def rank(project, files, ch_key, world="real"):
    """Score stills or clips against a character; best first."""
    refs = refs_for(project, ch_key, world)
    rows = []
    for f in files:
        f = f if os.path.isabs(f) else project.path(f)
        s = score_clip(refs, f) if f.lower().endswith((".mp4", ".mov", ".webm")) else score_image(refs, f)
        rows.append({"file": project.rel(f), "face": None if s is None else round(s, 3)})
    return sorted(rows, key=lambda r: -(r["face"] or -1))


def rank_takes(project, sid):
    """All rendered takes of a shot (clips/<id>_*.mp4), ranked by face match (+ mouth activity for lip-sync)."""
    s = project.shot(sid) or {}
    files = project.renders("clips", f"{sid}_*.mp4")
    if not s.get("chars"):
        return [{"file": project.rel(f), "face": None} for f in reversed(files)]
    rows = rank(project, files, s["chars"][0], s.get("world", "real"))
    if s.get("mode") == "lipsync":
        for r in rows:
            r["mouth"] = mouth_activity(project.path(r["file"]))[0]["activity"]
    return rows


def cut_report(project, cut_name="cut.json"):
    """Face score of every person shot in the cut: catches identity drift across the whole video."""
    cut = project.load(cut_name)
    out = []
    for n, c in enumerate(cut["shots"], 1):
        s = project.shot(c["id"]) or {}
        if not s.get("chars") or not c.get("src"):
            continue
        refs = refs_for(project, s["chars"][0], s.get("world", "real"))
        sc = score_clip(refs, project.path(c["src"]))
        out.append({"n": n, "id": c["id"], "char": s["chars"][0], "framing": s.get("framing"), "face": None if sc is None else round(sc, 3), "src": c["src"]})
    return out


def grid(out, rows, label_key="face", cols=3, cell=(480, 270)):
    """Contact sheet of ranked stills/clips (first frame for clips), score in the corner."""
    cv2 = _cv()
    cells = []
    for r in rows:
        p = r["path"]
        if p.lower().endswith((".mp4", ".mov", ".webm")):
            fr = clip_frames(p, (0.5,))
            im = fr[0][1] if fr else None
        else:
            im = cv2.imread(p)
        if im is None:
            continue
        im = cv2.resize(im, cell)
        cv2.rectangle(im, (0, 0), (cell[0], 24), (0, 0, 0), -1)
        val = r.get(label_key)
        txt = f'{"--" if val is None else f"{val:.3f}"}  {os.path.basename(p).split("_000")[0]}'
        cv2.putText(im, txt, (5, 17), 0, 0.55, (0, 255, 255), 1)
        cells.append(im)
    while len(cells) % cols:
        cells.append(np.zeros((cell[1], cell[0], 3), np.uint8))
    if not cells:
        raise ValueError("nothing to put on the sheet")
    cv2.imwrite(out, np.vstack([np.hstack(cells[i:i + cols]) for i in range(0, len(cells), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    return out
