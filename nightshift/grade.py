"""Grade looks as ffmpeg filter strings, shared by the look preview and finish.

A2_portra_dusk_plus is the look the first video shipped with: Portra-at-dusk balance (teal-blue shadows, warm
practicals, lifted blacks) with half of B's S-curve for a touch more contrast, plus a soft highlight bloom.
"""
import os
import subprocess

LOOKS = {
    # Portra at dusk: teal-blue shadows, warm amber practicals, gently lifted blacks, soft bloom
    "A_portra_dusk": ("curves=r='0/0.03 0.5/0.5 1/0.97':g='0/0.045 0.5/0.5 1/0.96':b='0/0.06 0.5/0.49 1/0.92',"
                      "colorbalance=rs=-0.06:gs=0.02:bs=0.03:rm=0.01:gm=0.0:bm=-0.02:rh=0.04:gh=0.02:bh=-0.05,eq=saturation=0.85:contrast=0.97", 0.12),
    # A with a touch more contrast: half of B's S-curve on top of A's lifted blacks and warm/teal balance
    "A2_portra_dusk_plus": ("curves=r='0/0.03 0.25/0.228 0.5/0.5 0.75/0.772 1/0.97':g='0/0.045 0.25/0.24 0.5/0.5 0.75/0.762 1/0.96':"
                            "b='0/0.06 0.25/0.25 0.5/0.49 0.75/0.742 1/0.92',"
                            "colorbalance=rs=-0.06:gs=0.02:bs=0.03:rm=0.01:gm=0.0:bm=-0.02:rh=0.04:gh=0.02:bh=-0.05,eq=saturation=0.85:contrast=1.0", 0.12),
    # CineStill-style night: cyan shadows, orange highlights, more contrast
    "B_cinestill_night": ("curves=r='0/0.02 0.25/0.21 0.75/0.79 1/0.97':g='0/0.04 0.25/0.245 0.75/0.765 1/0.96':b='0/0.06 0.25/0.26 0.75/0.73 1/0.9',"
                          "colorbalance=rs=-0.09:gs=0.03:bs=0.04:rm=0.02:bm=-0.03:rh=0.06:gh=0.02:bh=-0.07,eq=saturation=0.82", 0.16),
    # faded pastel: low contrast, peach highlights, milky teal blacks
    "C_faded_pastel": ("curves=r='0/0.06 0.5/0.52 1/0.95':g='0/0.07 0.5/0.5 1/0.94':b='0/0.08 0.5/0.48 1/0.9',"
                       "colorbalance=rs=-0.04:gs=0.02:bs=0.02:rh=0.05:gh=0.02:bh=-0.03,eq=saturation=0.74:contrast=0.92", 0.10),
    # no grade, only the soft bloom
    "none": ("null", 0.0),
}


def chain(look, src="[0:v]", out="[g]"):
    """Grade + soft highlight bloom (screen-blended blurred highlights).
    eq works in YUV; everything after it (and the screen blend) runs in RGB, or the blend tints chroma magenta."""
    fx, bloom = LOOKS[look]
    parts = fx.split(",")
    eq = [x for x in parts if x.startswith("eq=")]
    rest = [x for x in parts if not x.startswith("eq=") and x != "null"]
    fx = ",".join(eq + ["format=gbrp"] + rest)
    if not bloom:
        return f"{src}{fx}{out}"
    return (f"{src}{fx},split[a][b];[b]curves=all='0/0 0.6/0 1/1',gblur=sigma=18,colorchannelmixer=rr=1:gg=0.78:bb=0.5[hl];"
            f"[a][hl]blend=all_mode=screen:all_opacity={bloom}{out}")


def preview(frames, out, looks=None, width=640):
    """Grid: one row per frame, one column per look (ungraded first)."""
    looks = looks or list(k for k in LOOKS if k != "none")
    tmp = os.path.splitext(out)[0] + "_tmp"
    os.makedirs(tmp, exist_ok=True)
    rows = []
    for i, f in enumerate(frames):
        cells = []
        for j, lk in enumerate(["orig"] + looks):
            dst = os.path.join(tmp, f"{i}_{j}.png")
            fc = f"[0:v]scale={width}:-2[s];" + (chain(lk, "[s]", "[g]") if lk != "orig" else "[s]null[g]") + \
                 f";[g]drawtext=text='{lk}':x=8:y=8:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.5[o]"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-filter_complex", fc, "-map", "[o]", "-frames:v", "1", dst], check=True)
            cells.append(dst)
        rows.append(cells)
    import cv2
    import numpy as np
    ims = [[cv2.imread(c) for c in r] for r in rows]
    h = min(im.shape[0] for r in ims for im in r)
    grid = np.vstack([np.hstack([im[:h] for im in r]) for r in ims])
    cv2.imwrite(out, grid, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return out
