"""A project is one video, kept in one folder:

    project.json    settings (ComfyUI address, sizes, workflows, mode)
    canon.json      characters, wardrobe per framing, never-lists, worlds, defaults
    shots.json      the shot list (song-agnostic; lip-sync shots anchor to a lyric line)
    song/           caption.md, lyrics.txt, the chosen song, beatmap.json, words.json, lines.json
    refs/           reference images; approved character sheets land in refs/sheets/
    jobs/           built ComfyUI API jobs (+ .meta.json: workflow, shot, seeds)
    sheets/ stills/ clips/ songs/   what ComfyUI renders
    review/         contact sheets, A/B reels, numbered review copies
    overlay/        overlay data, frames, alpha chunks
    out/            passNN.mp4 + passNN_notes.md
    log.jsonl       every job submitted, finished or failed

Files ComfyUI reads (stills, sheets, audio) are staged into its input folder; files it writes land under its output
folder at <output_subdir>/<stills|clips|songs>/. Put the project inside ComfyUI's output folder (the default for
`nightshift init --comfy-dir`) and renders appear in the project with no copying. Anywhere else, `collect` copies
or downloads them.
"""
import glob
import json
import os
import shutil
import time

from . import workflows as W

DEFAULTS = {
    "name": None,
    "comfy": {"url": "http://127.0.0.1:8188", "dir": None, "output_subdir": None, "input_subdir": None},
    "fps": 24,
    "work_size": [1280, 768],       # what the video models render (LTX likes multiples of 32)
    "crop": [1280, 720],            # 16:9 cut from the work frame
    "final_size": [1920, 1080],
    "video_frames": 121,            # default clip length (8n+1)
    "mode": "director",             # director: stop for the human at checkpoints. yolo: the agent picks and carries on.
    "takes": {"default": 1, "complex": 4},
    "workflows": {
        "still": "still_flux", "edit2": "edit_flux_2image", "edit3": "edit_flux_3image",
        "ff": "vid_ltx_ff", "fflf": "vid_ltx_fflf", "lipsync": "vid_ltx_lipsync", "t2v": "vid_ltx_t2v",
        "song": "song_minimax_m3", "sheet_text": "sheet_from_text", "sheet_image": "sheet_from_image",
    },
    "sheets": {"candidates": 3, "approve": True, "yolo_source": "text", "seed": 7001},
    "timeline": {"min_seconds": 1.0, "max_seconds": 12.0, "max_fit_seconds": 15.0, "snap": 0.35},
    "grade": {"look": "A2_portra_dusk_plus", "lifts": []},
    "finish": {"chunk_seconds": 9.0, "halftone": None, "grain": 9},
    "watchdog": {"stall_minutes": 6, "max_minutes_per_frame": 0.12, "min_minutes": 4, "retries": 1, "poll_seconds": 10},
    "overlay": {},
}


def _merge(a, b):
    out = dict(a)
    for k, v in (b or {}).items():
        out[k] = _merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def _load(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _dump(data, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)
    return path


class Project:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        if not os.path.exists(self.path("project.json")):
            raise FileNotFoundError(f"{self.root} has no project.json (nightshift init <folder> makes one)")
        self.cfg = _merge(DEFAULTS, _load(self.path("project.json"), {}))
        self.name = self.cfg.get("name") or os.path.basename(self.root)
        self._client = None

    # ---- paths -------------------------------------------------------------------------------
    def path(self, *p):
        return os.path.join(self.root, *p)

    def rel(self, p):
        return os.path.relpath(os.path.abspath(p), self.root).replace(os.sep, "/")

    @property
    def comfy_dir(self):
        d = self.cfg["comfy"].get("dir")
        return os.path.abspath(os.path.expanduser(d)) if d else None

    @property
    def output_subdir(self):
        """Where ComfyUI writes this project's renders, relative to its output folder."""
        sub = self.cfg["comfy"].get("output_subdir")
        if sub:
            return sub.strip("/")
        if self.comfy_dir:
            out = os.path.join(self.comfy_dir, "output")
            if os.path.commonpath([out, self.root]) == out:
                return os.path.relpath(self.root, out).replace(os.sep, "/")
        return f"nightshift/{self.name}"

    @property
    def input_subdir(self):
        return (self.cfg["comfy"].get("input_subdir") or f"nightshift/{self.name}").strip("/")

    @property
    def renders_in_place(self):
        """True when ComfyUI's output folder for this project IS the project folder."""
        if not self.comfy_dir:
            return False
        return os.path.abspath(os.path.join(self.comfy_dir, "output", self.output_subdir)) == self.root

    def prefix(self, kind, name):
        """filename_prefix for a ComfyUI save node: <output_subdir>/<kind>/<name>"""
        return f"{self.output_subdir}/{kind}/{name}"

    def workflow_dirs(self):
        return [self.path("workflows")]

    def workflow(self, role):
        name = self.cfg["workflows"].get(role, role)
        return W.Workflow.load(name, self.workflow_dirs())

    # ---- documents -------------------------------------------------------------------------------
    def load(self, name, default=None):
        return _load(self.path(name), default)

    def save(self, name, data):
        return _dump(data, self.path(name))

    @property
    def canon(self):
        return self.load("canon.json", {})

    def shots(self, name="shots.json"):
        return self.load(name, {"shots": []})["shots"]

    def shot(self, sid, name=None):
        for n in ([name] if name else ["shots_resolved.json", "shots.json"]):
            for s in self.load(n, {"shots": []})["shots"]:
                if s["id"] == sid:
                    return s
        return None

    def patch_shot(self, sid, fields, name="shots.json"):
        doc = self.load(name, {"shots": []})
        for s in doc["shots"]:
            if s["id"] == sid:
                for k, v in fields.items():
                    if v is None:
                        s.pop(k, None)
                    else:
                        s[k] = v
                self.save(name, doc)
                return s
        raise KeyError(f"no shot {sid} in {name}")

    def log(self, event, **kw):
        rec = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **kw}
        with open(self.path("log.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        return rec

    # ---- ComfyUI -------------------------------------------------------------------------------
    @property
    def client(self):
        if self._client is None:
            from .comfy import Comfy
            self._client = Comfy(self.cfg["comfy"]["url"], self.comfy_dir)
        return self._client

    def stage_input(self, src, name=None):
        """Make a local file readable by ComfyUI's LoadImage / LoadAudio nodes. Returns the name to put in the node."""
        src = src if os.path.isabs(src) else self.path(src)
        if not os.path.exists(src):
            raise FileNotFoundError(src)
        name = name or os.path.basename(src)
        if self.comfy_dir:
            dst_dir = os.path.join(self.comfy_dir, "input", *self.input_subdir.split("/"))
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, name)
            if not (os.path.exists(dst) and os.path.samefile(src, dst)):
                shutil.copyfile(src, dst)
        else:
            self.client.upload(src, self.input_subdir, name)
        return f"{self.input_subdir}/{name}"

    def collect(self, files):
        """Bring rendered files (ComfyUI history entries) into the project folder; returns local paths."""
        out = []
        for f in files:
            sub = (f.get("subfolder") or "").replace("\\", "/")
            if f.get("type", "output") != "output" or not (sub == self.output_subdir or sub.startswith(self.output_subdir + "/")):
                continue
            rel = sub[len(self.output_subdir):].strip("/")
            dst = self.path(*([p for p in rel.split("/") if p] + [f["filename"]]))
            if not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                src = os.path.join(self.comfy_dir, "output", *sub.split("/"), f["filename"]) if self.comfy_dir else None
                if src and os.path.exists(src):
                    shutil.copyfile(src, dst)
                else:
                    self.client.download(f, dst)
            out.append(dst)
        return out

    # ---- renders on disk -------------------------------------------------------------------------------
    def renders(self, kind, pattern="*"):
        """Rendered files in stills/, clips/ or songs/, oldest first; ignores LTX's separate -audio.mp4 files."""
        hits = [p for p in glob.glob(self.path(kind, pattern)) if not p.endswith("-audio.mp4")]
        return sorted(hits, key=os.path.getmtime)

    def latest_still(self, sid, model):
        hits = [p for p in self.renders("stills", f"{sid}_{model}_*") if p.lower().endswith((".png", ".jpg", ".webp"))]
        if not hits:
            raise FileNotFoundError(f"no '{model}' still for shot {sid} yet (stills/{sid}_{model}_*.png)")
        return hits[-1]


def init(root, name=None, comfy_url=None, comfy_dir=None, template=None, mode="director"):
    """Create a project folder from the starter template."""
    root = os.path.abspath(root)
    starter = template or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "projects", "starter"))
    if os.path.exists(os.path.join(root, "project.json")):
        raise FileExistsError(f"{root} already has a project.json")
    os.makedirs(root, exist_ok=True)
    for dirpath, _, files in os.walk(starter):
        rel = os.path.relpath(dirpath, starter)
        os.makedirs(os.path.join(root, rel), exist_ok=True)
        for f in files:
            dst = os.path.join(root, rel, f)
            if not os.path.exists(dst):
                shutil.copyfile(os.path.join(dirpath, f), dst)
    for d in ("jobs", "sheets", "stills", "clips", "songs", "review", "overlay", "out", "workflows"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    cfg = _load(os.path.join(root, "project.json"), {})
    cfg["name"] = name or os.path.basename(root)
    cfg.setdefault("comfy", {})
    if comfy_url:
        cfg["comfy"]["url"] = comfy_url
    if comfy_dir:
        cfg["comfy"]["dir"] = comfy_dir
    cfg["mode"] = mode
    _dump(cfg, os.path.join(root, "project.json"))
    return Project(root)
