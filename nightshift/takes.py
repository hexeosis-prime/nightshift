"""Takes and quick edits.

takes(): clone a built job into N takes with different seeds (base + 1000*i, so every take is reproducible).
         Best-of-N is the cheapest quality lever: a 3090 renders a 5 s LTX shot in about 3-4 minutes, and on shots where
         singing, dancing and a camera move all happen at once, one take in four is usually clearly better.
edit():  ad-hoc two-image Flux edit (base + reference + instruction): relight a frame from a reference frame, swap a
         face from a sheet, change a season. With ref=None the base is its own reference (an environment edit).
extract_frame(): pull a frame out of a take, e.g. to use a take's own frame as a last frame (self-consistent LF).
pad_mirror(): pad a 1280x720 still to 1280x768 by mirroring the edges, so a 16:9 frame can drive a 1280x768 render
         and the edit crops exactly the padding back off.
"""
import json
import os
import shutil
import subprocess

from .workflows import job_workflow


def takes(project, job, n, base_seed=None, tag="t"):
    jp = job if os.path.isabs(job) else project.path(job)
    wf, meta = job_workflow(jp, project.workflow_dirs())
    base = int(base_seed if base_seed is not None else meta.get("seed", 1))
    prefixes = {o: wf.output_prefix(o) for o in wf.outputs() if wf.spec["outputs"][o]["node"] in wf.graph}
    graph0 = json.dumps(wf.graph)
    out = []
    for i in range(n):
        wf.graph = json.loads(graph0)
        seed = base + 1000 * i
        wf.seed(seed)
        for o, p in prefixes.items():
            wf.output(f"{p}_{tag}{i}", which=o)
        p = jp[:-5] + f"_{tag}{i}.json"
        wf.save(p, {**meta, "seed": seed, "take": f"{tag}{i}"})
        out.append(project.rel(p))
    return out


def edit(project, base, out_id, seed, text, ref=None, ref2=None):
    role = "edit3" if ref2 else "edit2"
    wf = project.workflow(role)
    wf.apply_defaults()
    b = project.stage_input(base, f"{out_id}_base{os.path.splitext(base)[1] or '.png'}")
    wf.set("image1", b)
    wf.set("image2", project.stage_input(ref, f"{out_id}_ref{os.path.splitext(ref)[1] or '.png'}") if ref else b)
    if ref2:
        wf.set("image3", project.stage_input(ref2, f"{out_id}_ref2{os.path.splitext(ref2)[1] or '.png'}"))
    wf.set("prompt", text)
    wf.seed(int(seed))
    wf.output(project.prefix("stills", f"{out_id}_edit"))
    return project.rel(wf.save(project.path("jobs", f"{out_id}_edit.json"), {"kind": "edit", "shot": out_id, "seed": int(seed)}))


def extract_frame(src, frame, dst):
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"select=eq(n\\,{int(frame)})", "-frames:v", "1", dst], check=True)
    return dst


def pad_mirror(src, dst, size=(1280, 768)):
    from PIL import Image, ImageOps
    im = Image.open(src).convert("RGB")
    W, H = size
    if im.width != W:
        im = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
    top = (H - im.height) // 2
    if top <= 0:
        im.crop((0, -top, W, -top + H)).save(dst)
        return dst
    out = Image.new("RGB", (W, H))
    out.paste(im, (0, top))
    out.paste(ImageOps.flip(im.crop((0, 0, W, top))), (0, 0))
    bot = H - top - im.height
    out.paste(ImageOps.flip(im.crop((0, im.height - bot, W, im.height))), (0, top + im.height))
    out.save(dst)
    return dst


def zoom_crop(src, dst, scale=0.6, center=(0.5, 0.5)):
    """A tighter crop of a still, scaled back to full size: as a last frame it makes LTX fly forward into the scene."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = int(im.width * scale), int(im.height * scale)
    x = int(min(max(center[0] * im.width - w / 2, 0), im.width - w))
    y = int(min(max(center[1] * im.height - h / 2, 0), im.height - h))
    im.crop((x, y, x + w, y + h)).resize(im.size, Image.LANCZOS).save(dst)
    return dst


def drop_in(project, file, sid, label):
    """Use your own still for a shot: copied to stills/<id>_<label>_00001_.png; then set the shot's "still" to the label."""
    dst = project.path("stills", f"{sid}_{label}_00001_{os.path.splitext(file)[1] or '.png'}")
    shutil.copyfile(file, dst)
    return project.rel(dst)
