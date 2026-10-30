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
    """Subtitle-like text boxes in one frame: [(x, y, w, h)] in 0-1 frame units."""
    import cv2
    H, W = frame.shape[:2]
    boxes, conf = _detector().detect(frame)
    out = []
    for b in boxes:
        pts = np.array(b, dtype=np.float32)
        x, y, w, h = cv2.boundingRect(pts)
        if w < 0.18 * W or w < 3.0 * h or h < 0.015 * H:      # a line of words: wide, short, not a speck
            continue
        cx, cy = (x + w / 2) / W, (y + h / 2) / H
        if not 0.15 < cx < 0.85 or cy < 0.3:                  # subtitles sit across the middle and low, not at an edge or the top
            continue
        out.append((round(x / W, 3), round(y / H, 3), round(w / W, 3), round(h / H, 3)))
    return out


def burned_text(clip, n=6, min_frames=2):
    """{"text": bool, "frames": k of n frames with a subtitle-like line, "boxes": [...]}"""
    if not available():
        return {"text": False, "frames": 0, "boxes": [], "skipped": "no text_det.onnx (python scripts/get_models.py)"}
    hits, boxes = 0, []
    for fr in _frames(clip, n):
        b = text_lines(fr)
        if b:
            hits += 1
            boxes.append(b)
    return {"text": hits >= min_frames, "frames": hits, "of": n, "boxes": boxes[:3]}


def flagged(project):
    """Clip file names the check found burned-in text in."""
    return {k for k, v in (project.load("review/qc.json", {}) or {}).items() if v.get("text")}
