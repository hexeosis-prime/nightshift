"""Animated illustrations for the overlay: neon line art on black, animated with a first-frame video job, then keyed.

1. Make a still of the art on pure black (Flux: "neon line drawing ... on a pure black background").
2. Animate it (an ff video job of a few seconds: sparks, flicker, a slow turn).
3. key(): crop each clip to the art's box and luma-key it: alpha = max(R,G,B) through a soft curve, colour
   un-premultiplied so glows keep their hue. Writes overlay/illus/il_<name>_%03d.png and overlay/illus_anim.json,
   which prep() hands to the page.
"""
import json
import os
import subprocess

import numpy as np


def key(project, items, height=360, pad=24):
    """items: {name: {"clip": "clips/x.mp4", "box": [x, y, w, h] (in clip pixels) or null for the whole frame}}"""
    from PIL import Image
    out = project.path("overlay", "illus")
    os.makedirs(out, exist_ok=True)
    anim = project.load("overlay/illus_anim.json", {})
    for name, it in items.items():
        clip = project.path(it["clip"])
        tmp = os.path.join(out, f"_raw_{name}")
        os.makedirs(tmp, exist_ok=True)
        vf = "null"
        aspect = None
        if it.get("box"):
            x, y, w, h = it["box"]
            cw, ch = it.get("clip_size", project.cfg["work_size"])
            x0, y0 = max(0, x - pad), max(0, y - pad)
            x1, y1 = min(cw, x + w + pad), min(ch, y + h + pad)
            ow = round(height * (x1 - x0) / (y1 - y0))
            vf = f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0},scale={ow}:{height}:flags=lanczos"
            aspect = (x1 - x0) / (y1 - y0)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-vf", vf, os.path.join(tmp, "f_%03d.png")], check=True)
        frames = sorted(os.listdir(tmp))
        for i, fn in enumerate(frames):
            a = np.asarray(Image.open(os.path.join(tmp, fn)).convert("RGB")).astype(np.float32) / 255
            m = np.clip((a.max(axis=2) - 0.06) / 0.94, 0, 1)            # crush the near-black noise floor
            alpha = np.clip(m ** 0.8 * 1.15, 0, 1)
            rgb = np.where(alpha[..., None] > 1e-3, a / np.maximum(a.max(axis=2, keepdims=True), 1e-3), 0)
            rgb = rgb * np.clip(m[..., None] / np.maximum(alpha[..., None], 1e-3), 0, 1) ** 0.5
            img = np.dstack([np.clip(rgb, 0, 1) * 255, alpha * 255]).astype(np.uint8)
            Image.fromarray(img, "RGBA").save(os.path.join(out, f"il_{name}_{i + 1:03d}.png"), compress_level=3)
        anim[name] = {"base": "file://" + os.path.abspath(os.path.join(out, f"il_{name}_%03d.png")).replace("\\", "/"),
                      "count": len(frames), "fps": project.cfg["fps"], "aspect": aspect}
    project.save("overlay/illus_anim.json", anim)
    return anim
