"""Cut the shots onto the song.

cut.json
  song, beatmap          paths relative to the cut file
  fps, work_size         every shot is conformed to work_size first (what the models render)
  crop, crop_y           the 16:9 window taken from it (crop_y null = centred)
  final_size             delivery size (null = keep the crop)
  start, until           song range
  shots: [{"id", "src", "beats" | "seconds", "in", "speed"}]
     beats   the shot ends on the Nth beat after it starts (cuts land on the grid)
     seconds plain duration; the last shot runs to "until"
     in      seconds skipped at the head of the clip
     speed   playback rate: 2 = twice as fast, 0.94 = stretched 6% to fill a slot instead of freezing the tail
     src may be a still (.png/.jpg): it is held for the slot.

Segments are encoded once per shot into segs/ next to the output (one generation: conform, crop, scale). Each segment's file name
carries a fingerprint of its source, trim, speed, length and geometry, so after any change to the cut only the shots
that changed are re-encoded. join() concatenates them and lays the song under the picture; an EDL (CSV) is
written next to the output.
"""
import csv
import hashlib
import json
import os
import subprocess

STILL_EXT = (".png", ".jpg", ".jpeg", ".webp")


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("ffmpeg failed:\n" + " ".join(cmd) + "\n" + r.stderr[-2000:])
    return r.stdout


def duration(p):
    return float(_run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).strip())


def _tc(n, fps):
    s, f = divmod(n, fps)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"


class Cut:
    def __init__(self, cut_path):
        self.path = os.path.abspath(cut_path)
        self.base = os.path.dirname(self.path)
        self.cfg = json.load(open(cut_path, encoding="utf-8"))
        c = self.cfg
        self.fps = int(c.get("fps", 24))
        self.W, self.H = c.get("work_size", [1280, 768])
        self.cw, self.ch = c.get("crop", [1280, 720])
        cy = c.get("crop_y")
        self.cy = (self.H - self.ch) // 2 if cy is None else int(cy)
        self.final = c.get("final_size", [1920, 1080])
        self.song = self.P(c["song"])
        self.start = float(c.get("start", 0.0))
        self.until = min(float(c["until"]), duration(self.song)) if c.get("until") else duration(self.song)
        self.beats = json.load(open(self.P(c["beatmap"])))["beats"] if c.get("beatmap") else None
        self.shots = c["shots"]
        cuts, t = [self.start], self.start
        for i, s in enumerate(self.shots):
            if i == len(self.shots) - 1:
                t = self.until
            elif "beats" in s:
                if not self.beats:
                    raise ValueError(f"shot {s['id']} uses beats but the cut has no beatmap")
                ahead = [b for b in self.beats if b > t + 0.5 / self.fps]
                n = int(s["beats"])
                t = ahead[n - 1] if len(ahead) >= n else t + n * (self.beats[-1] - self.beats[-2])
            else:
                t = t + float(s["seconds"])
            cuts.append(min(t, self.until))
        self.cuts = cuts
        self.fr = [round((c - self.start) * self.fps) for c in cuts]   # frame-accurate, never drifts

    def P(self, p):
        return p if os.path.isabs(p) else os.path.join(self.base, p)

    def slots(self):
        return [(i, s, self.fr[i + 1] - self.fr[i]) for i, s in enumerate(self.shots)]

    def vf(self):
        return (f"fps={self.fps},scale={self.W}:{self.H}:force_original_aspect_ratio=increase,crop={self.W}:{self.H},setsar=1,"
                f"crop={self.cw}:{self.ch}:0:{self.cy}" + (f",scale={self.final[0]}:{self.final[1]}:flags=lanczos" if self.final else "")
                + ",format=yuv420p")

    def segname(self, i, s, n):
        key = json.dumps([s.get("src"), s.get("in", 0.0), s.get("speed"), n, self.vf()], sort_keys=True)
        return f"{i:03d}_{s['id']}_{hashlib.md5(key.encode()).hexdigest()[:8]}.mp4"

    def segdir(self, out):
        d = os.path.join(os.path.dirname(os.path.abspath(out)), "segs")   # shared by every pass: names carry fingerprints
        os.makedirs(d, exist_ok=True)
        return d

    def segs(self, out, first=0, last=None, redo=(), on_event=print):
        """Encode segments first..last-1 (skips existing ones unless their shot id is in redo)."""
        d = self.segdir(out)
        warnings = []
        for i, s, n in self.slots()[first:last]:
            seg = os.path.join(d, self.segname(i, s, n))
            if n <= 0:
                continue
            if os.path.exists(seg) and s["id"] not in redo:
                continue
            if not s.get("src"):
                raise ValueError(f"shot {s['id']} has no src in the cut")
            src = self.P(s["src"])
            if src.lower().endswith(STILL_EXT):
                inp, pre = ["-loop", "1", "-i", src], ""
            else:
                have = round(duration(src) * self.fps)
                if s.get("speed"):
                    have = round(have / float(s["speed"]))
                have -= round(float(s.get("in", 0.0)) * self.fps)
                if have < n:
                    warnings.append(f"{s['id']}: clip has {have} frames for a {n}-frame slot (last frame holds)")
                inp, pre = ["-ss", str(s.get("in", 0.0)), "-i", src], (f"setpts=PTS/{s['speed']}," if s.get("speed") else "")
            _run(["ffmpeg", "-v", "error", "-y", *inp, "-vf", pre + self.vf() + f",tpad=stop_mode=clone:stop_duration={n / self.fps + 1}",
                  "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-r", str(self.fps), seg + ".part.mp4"])
            os.replace(seg + ".part.mp4", seg)
            on_event(f"seg {i:03d} {s['id']} {n}f")
        return warnings

    def join(self, out):
        d = self.segdir(out)
        segs = [os.path.join(d, self.segname(i, s, n)) for i, s, n in self.slots() if n > 0]
        missing = [p for p in segs if not os.path.exists(p)]
        if missing:
            raise FileNotFoundError(f"missing {len(missing)} segments, e.g. {missing[0]} (run segs first)")
        lst = os.path.join(d, "list.txt")
        with open(lst, "w") as f:
            f.write("".join(f"file '{p}'\n" for p in segs))
        total = self.fr[-1] / self.fps
        _run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-ss", str(self.start), "-t", str(total), "-i", self.song,
              "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", "-shortest", out])
        edl = os.path.splitext(out)[0] + "_edl.csv"
        with open(edl, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["shot", "source", "record_in", "record_out", "frames", "song_in_s", "song_out_s"])
            for i, s, n in self.slots():
                if n > 0:
                    w.writerow([s["id"], s["src"], _tc(self.fr[i], self.fps), _tc(self.fr[i + 1], self.fps), n,
                                round(self.cuts[i], 3), round(self.cuts[i + 1], 3)])
        return {"out": out, "edl": edl, "seconds": round(total, 3), "shots": len(segs)}


def assemble(cut_path, out, redo=(), on_event=print):
    c = Cut(cut_path)
    warnings = c.segs(out, redo=redo, on_event=on_event)
    res = c.join(out)
    res["warnings"] = warnings
    return res
