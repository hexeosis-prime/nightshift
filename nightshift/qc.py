"""Quality checks on rendered clips, run before the cut so a bad take never reaches the video.

burned_text(clip)  LTX sometimes writes the sung words into the picture as subtitles. A small text detector (PP-OCRv3 DB,
                   OpenCV Zoo, Apache 2.0) looks at a few frames for subtitle-like text: a wide line of text that stays
                   on screen across several frames. Signs and textures in the scene rarely look like that.
"""
import os

import numpy as np

from .score import MODELS

MODEL = os.path.join(MODELS, "text_det.onnx")
_DET = None


def available():
    return os.path.exists(MODEL)


def _detector():
    global _DET
    if _DET is None:
        import cv2
        d = cv2.dnn_TextDetectionModel_DB(MODEL)
        d.setBinaryThreshold(0.3)
        d.setPolygonThreshold(0.5)
        d.setMaxCandidates(200)
        d.setUnclipRatio(2.0)
        d.setInputParams(1.0 / 255.0, (736, 736), (122.67891434, 116.66876762, 104.00698793))
        _DET = d
    return _DET


def _frames(clip, n):
    import cv2
    cap = cv2.VideoCapture(clip)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    idx = [int(total * (i + 0.5) / n) for i in range(n)] if total else []
    out = []
    for i in idx:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, fr = cap.read()
        if ok:
            out.append(fr)
    cap.release()
    return out


def text_lines(frame):
    """Text in one frame that looks burned in: {"sub": [...], "big": [...]} boxes (x, y, w, h) in 0-1 frame units.
    sub: a subtitle line (wide, short, across the middle, below the top third).
    big: title-size letters (LTX sometimes paints giant garbled words), word-shaped: at least twice as wide as tall."""
    import cv2
    H, W = frame.shape[:2]
    boxes, conf = _detector().detect(frame)
    out = {"sub": [], "big": []}
    for b in boxes:
        x, y, w, h = cv2.boundingRect(np.array(b, dtype=np.float32))
        box = (round(x / W, 3), round(y / H, 3), round(w / W, 3), round(h / H, 3))
        cx, cy = (x + w / 2) / W, (y + h / 2) / H
        if w >= 0.18 * W and w >= 3.0 * h and h >= 0.015 * H and 0.15 < cx < 0.85 and cy >= 0.3:
            out["sub"].append(box)
        elif h >= 0.1 * H and w >= 0.15 * W and w >= 2.0 * h:
            out["big"].append(box)
    return out


def burned_text(clip, n=6, min_frames=2, min_big_frames=4):
    """{"text": bool, "frames": k of n frames with subtitle-like text, "big": k with giant words, "boxes": [...]}
    A subtitle on 2 of 6 sampled frames, or giant words on 4 of 6 (they persist; a window or a poster that merely looks
    text-like rarely does), flags the take."""
    if not available():
        return {"text": False, "frames": 0, "boxes": [], "skipped": "no text_det.onnx (python scripts/get_models.py)"}
    subs = bigs = 0
    boxes = []
    for fr in _frames(clip, n):
        t = text_lines(fr)
        subs += bool(t["sub"])
        bigs += bool(t["big"])
        if t["sub"] or t["big"]:
            boxes.append(t["sub"] + t["big"])
    return {"text": subs >= min_frames or bigs >= min_big_frames, "frames": subs, "big": bigs, "of": n, "boxes": boxes[:3]}


def flagged(project):
    """Clip file names the check found burned-in text in."""
    return {k for k, v in (project.load("review/qc.json", {}) or {}).items() if v.get("text")}
