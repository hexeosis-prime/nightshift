"""Clean copies for sharing.

ComfyUI writes the whole prompt and workflow into what it saves: text chunks in every PNG ("prompt", "workflow"), tags in
videos and songs. A file sent out like that hands over the prompts. Nightshift's own outputs (the cut, the finished pass,
review copies, posting copies) are written without metadata; publish() makes clean copies of anything else (a still, a
sheet, a take, a song), and carried() says what a file still holds.

    nightshift -p <project> publish stills/s02_edit_00001_.png clips/s05_*.mp4      -> out/publish/
"""
import glob
import json
import os
import shutil
import subprocess

IMAGES = (".png", ".jpg", ".jpeg", ".webp")
MEDIA = (".mp4", ".mov", ".m4v", ".webm", ".mkv", ".mp3", ".flac", ".wav", ".m4a", ".ogg")
# container bookkeeping, not content: harmless to keep
HARMLESS = {"major_brand", "minor_version", "compatible_brands", "encoder", "handler_name", "vendor_id", "language",
            "duration", "creation_time", "encoder-settings"}


def carried(path):
    """The metadata keys a file carries beyond container bookkeeping (empty = clean)."""
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGES:
        from PIL import Image
        with Image.open(path) as im:
            keys = [k for k in im.info if k not in ("dpi", "gamma", "srgb", "transparency", "icc_profile", "chromaticity",
                                                       "aspect", "progressive", "progression", "jfif", "jfif_version",
                                                       "jfif_unit", "jfif_density", "adobe", "adobe_transform", "loop",
                                                       "duration", "background", "lossless")]
            if im.getexif():
                keys.append("exif")
        return sorted(set(keys))
    if ext in MEDIA:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags:stream_tags", "-of", "json", path],
                             capture_output=True, text=True).stdout or "{}"
        d = json.loads(out)
        keys = set((d.get("format") or {}).get("tags") or {})
        for s in d.get("streams") or []:
            keys |= set(s.get("tags") or {})
        return sorted(k for k in keys if k.lower() not in HARMLESS)
    return []


def clean(src, dst):
    """A copy of src at dst with no prompt, workflow or other metadata. Pixels and streams are untouched (images are
    re-saved losslessly for PNG; video and audio streams are copied, not re-encoded)."""
    os.makedirs(os.path.dirname(os.path.abspath(dst)) or ".", exist_ok=True)
    ext = os.path.splitext(src)[1].lower()
    if ext in IMAGES:
        from PIL import Image
        with Image.open(src) as im:
            im.load()
            fmt = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}[ext[1:]]
            kw = {"quality": 95} if fmt == "JPEG" else ({"lossless": True} if fmt == "WEBP" and im.info.get("lossless") else {})
            img = im.convert("RGB") if fmt == "JPEG" and im.mode not in ("RGB", "L") else im
            img.save(dst, fmt, **kw)          # no pnginfo / exif passed: nothing carried over
    elif ext in MEDIA:
        tmp = dst + ".part" + ext
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0", "-c", "copy", "-map_metadata", "-1",
               "-map_metadata:s", "-1", "-map_chapters", "-1"]
        if ext in (".mp4", ".mov", ".m4v", ".m4a"):
            cmd += ["-movflags", "+faststart"]
        subprocess.run(cmd + [tmp], check=True)
        os.replace(tmp, dst)
    else:
        shutil.copyfile(src, dst)
    return dst


def publish(project, patterns, dest=None):
    """Clean copies of project files (globs allowed) into dest (default out/publish/). Returns [{file, removed}]."""
    dest = dest or project.path("out", "publish")
    rows = []
    for pat in patterns:
        hits = sorted(glob.glob(pat if os.path.isabs(pat) else project.path(pat))) or [pat]
        for src in hits:
            src = src if os.path.isabs(src) else project.path(src)
            if not os.path.exists(src):
                raise FileNotFoundError(f"no file {pat}")
            before = carried(src)
            dst = clean(src, os.path.join(dest, os.path.basename(src)))
            left = carried(dst)
            if left:
                raise RuntimeError(f"{os.path.basename(src)} still carries {', '.join(left)} after cleaning")
            rows.append({"file": project.rel(dst), "removed": before})
    project.log("publish", files=[r["file"] for r in rows])
    return rows
