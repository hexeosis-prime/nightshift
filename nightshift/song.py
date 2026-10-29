"""Songs with MiniMax Music 3 running locally in ComfyUI.

The model takes two texts:
  caption  the production brief: genre, BPM, key, mood arc, vocal casting and treatment, a timed arrangement
  lyrics   the words with section tags ([Intro], [Verse 1 - Female Singer], [Rap Verse - Male Rapper], ...)
Both live in the project: song/caption.md and song/lyrics.txt. Render several seeds, listen, keep one
(nightshift song choose <file>). See docs/prompting.md for what worked.
"""
import os
import re

from .project import Project


def read_texts(project):
    cap = open(project.path("song", "caption.md"), encoding="utf-8").read()
    lyr = open(project.path("song", "lyrics.txt"), encoding="utf-8").read()
    return strip_comments(cap), lyr.strip()


def strip_comments(text):
    """Drop markdown headings and <!-- notes --> so only the brief itself goes to the model."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#")).strip()


def replace_once(text, old, new, regex=False):
    """Revise a caption safely: the pattern must match exactly once (a silent miss is how revisions get lost)."""
    if regex:
        out, n = re.subn(old, new, text, flags=re.S)
    else:
        n = text.count(old)
        out = text.replace(old, new)
    if n != 1:
        raise ValueError(f"expected one match for {old[:60]!r}, found {n}")
    return out


def tag_singers(lyrics, names):
    """Name the singer in every section tag, e.g. names={"[Verse]": "[Verse {k} - Female Singer]"}.
    Explicit per-section casting was what finally got M3 to hand a verse to a second voice."""
    out, count = [], {}
    for line in lyrics.split("\n"):
        key = line.strip()
        if key in names:
            count[key] = count.get(key, 0) + 1
            line = names[key].format(k=count[key])
        out.append(line)
    return "\n".join(out)


def build_jobs(project: Project, seeds, tag="take", caption=None, lyrics=None, max_seconds=None):
    """One job per seed: jobs/song_<tag>_<seed>.json, rendering to songs/<tag>_<seed>_*.mp3."""
    cap, lyr = read_texts(project) if caption is None or lyrics is None else (caption, lyrics)
    caption = caption if caption is not None else cap
    lyrics = lyrics if lyrics is not None else lyr
    paths = []
    for seed in seeds:
        wf = project.workflow("song")
        wf.apply_defaults()
        wf.set("caption", caption)
        wf.set("lyrics", lyrics)
        if max_seconds:
            wf.try_set("max_seconds", int(max_seconds))
        wf.seed(int(seed))
        name = f"{tag}_{seed}"
        wf.output(project.prefix("songs", name))
        paths.append(wf.save(project.path("jobs", f"song_{name}.json"), {"kind": "song", "seed": int(seed), "tag": tag}))
    return paths


def choose(project: Project, song_file):
    """Make a rendered song the project's song (copied to song/song.<ext> and staged for the video jobs)."""
    import shutil
    src = song_file if os.path.isabs(song_file) else project.path(song_file)
    ext = os.path.splitext(src)[1]
    dst = project.path("song", "song" + ext)
    shutil.copyfile(src, dst)
    cfg = project.load("project.json", {})
    cfg["song"] = project.rel(dst)
    project.save("project.json", cfg)
    project.cfg["song"] = cfg["song"]
    project.log("song_chosen", src=project.rel(src))
    return dst


def song_path(project: Project):
    p = project.cfg.get("song")
    if p:
        return project.path(p)
    for ext in (".mp3", ".wav", ".flac"):
        if os.path.exists(project.path("song", "song" + ext)):
            return project.path("song", "song" + ext)
    raise FileNotFoundError("no song chosen yet (nightshift song choose <file>)")
