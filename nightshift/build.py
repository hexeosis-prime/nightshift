"""Shot builder: canon + shot list -> ComfyUI jobs.

Stages (run in this order, each after the previous renders are in):
  stills      one text-to-image job per shot that needs a first frame (modes ff, lipsync, fflf)
  sheetedits  identity edits: the shot's still + the character sheet -> the same frame with the right face,
              hair and wardrobe (shots with "still": "edit"); "add" puts a second character in with a third image
  edits       free two-image edits (shots with "edit_ref" + "edit_prompt")
  videos      one video job per shot, by mode: ff (first frame), fflf (first + last frame, song audio),
              lipsync (first frame + song section), t2v (text only). "reuse" shots are skipped.

Rules applied here so nobody has to remember them:
  - wardrobe text follows framing (shoes only in a wide shot) and world (outfit_<world> if the canon has one)
  - each character's never-list goes to the negative prompt, plus a per-mode negative list
  - every seed is fixed and written next to the job (jobs/<name>.meta.json)
  - {lead}-style placeholders in video prompts become the character's video_name, so identity words are identical
    in every shot
Which still a video uses: "still" on the shot (a model output name like "flux", "edit", or any label you gave a
file: drop stills/<id>_<label>_00001_.png and set "still": "<label>"), overridable per run with picks {id: label}.
"""
import json
import math
import os
import re

from .project import Project

NEG = {
    "lipsync": ", microphone, mic stand, holding a microphone, subtitles, captions, text on clothing, letters, logo, extra people, "
               "crowd, bystanders, spinning, turning around, scene cut, words, writing, title card, lower third, watermark",
    "ff": ", scene cut, jump cut, spinning, turning around, extra people, crowd, text, subtitles, microphone",
    "t2v": ", text, letters, subtitles, captions, scene cut",
    "fflf_people": ", microphone, captions, text on clothing, extra people, crowd, bystanders, duplicate person, spinning, turning around, morphing face",
}
VOICES = {"woman": ("sings", "singing", "warm, expressive singing style"), "man": ("sings", "singing", "warm, expressive singing style")}
STILL_MODES = ("ff", "lipsync", "fflf")


class Builder:
    def __init__(self, project: Project, shots_name="shots_resolved.json", picks=None):
        self.p = project
        self.canon = project.canon
        name = shots_name if os.path.exists(project.path(shots_name)) else "shots.json"
        self.shots_name = name
        self.shots = project.shots(name)
        self.by_id = {s["id"]: s for s in self.shots}
        self.picks = picks or {}
        self.neg = dict(NEG, **self.canon.get("negatives", {}))
        self.fps = project.cfg["fps"]

    # ---- helpers -------------------------------------------------------------------------------
    def char(self, key):
        c = dict(self.canon.get("characters", {}).get(key) or {})
        male = (c.get("count") or {}).get("male", 0) and not (c.get("count") or {}).get("female", 0)
        c.setdefault("noun", "man" if male else "woman")
        c.setdefault("pronoun", "he" if c["noun"] == "man" else "she")
        c.setdefault("possessive", "his" if c["noun"] == "man" else "her")
        c.setdefault("signature", "")
        return c

    def world(self, s):
        return s.get("world") or self.canon.get("default_world", "real")

    def world_cfg(self, s):
        return (self.canon.get("worlds") or {}).get(self.world(s), {})

    def default_model(self, s):
        return self.world_cfg(s).get("still_model") or self.canon.get("still_model", "flux")

    def names(self, text, s):
        """{lead} -> the character's video_name (world-specific video_name_<world> if present)."""
        def rep(m):
            c = self.canon.get("characters", {}).get(m.group(1))
            if not c:
                return m.group(0)
            return c.get(f"video_name_{self.world(s)}") or c.get("video_name") or c.get("person", m.group(1))
        return re.sub(r"\{([A-Za-z0-9_]+)\}", rep, text or "")

    def input_file(self, path, name=None):
        """A project file (refs/x.png) is staged into ComfyUI's input; anything else is assumed to be there already."""
        if not path:
            return path
        local = path if os.path.isabs(path) else self.p.path(path)
        return self.p.stage_input(local, name) if os.path.exists(local) else path

    def frames(self, s):
        return int(s.get("frames", self.p.cfg["video_frames"]))

    def still_label(self, s):
        return self.picks.get(s["id"]) or s.get("still") or self.default_model(s)

    def stage_still(self, s, label=None):
        label = label or self.still_label(s)
        src = self.p.latest_still(s["id"], label)
        return self.p.stage_input(src, f"{s['id']}_{label}.png"), label

    def sheet(self, ch_key, world, override=None):
        c = self.char(ch_key)
        p = override or (c.get("sheet") or {}).get(world) or (c.get("sheet") or {}).get("real")
        if not p:
            raise ValueError(f"character {ch_key} has no sheet for world {world} in canon.json")
        return self.input_file(p)

    def save(self, wf, name, meta):
        return wf.save(self.p.path("jobs", name), meta)

    def size(self, wf):
        """Graphs that render at a fixed size get the project's work size (16:9 or 9:16)."""
        w, h = self.p.cfg["work_size"]
        wf.try_set("width", w)
        wf.try_set("height", h)
        wf.try_set("long_edge", max(w, h))

    def caption(self, s, person, outfit, action, loc, framing, people):
        """One full caption for caption-style graphs (FLUX 3 Klein): what the switch-built Flux 2 prompt says, in prose."""
        sw = dict(self.canon.get("image_switches_default", {}), **self.world_cfg(s).get("switches", {}), **s.get("switches", {}))
        shot = {"close": "Close-up", "medium": "Medium shot", "wide": "Wide shot"}.get(framing, "Shot")
        parts = []
        if person:
            subject = f"{shot} of a {person}" + (f", wearing {outfit}" if outfit else "")
            parts.append(subject + (f", {action}" if action else "") + ".")
        else:
            parts.append(f"{shot}" + (f": {action}" if action else "") + ".")
        if loc:
            parts.append(f"Setting: {loc}.")
        look = self.world_cfg(s).get("style") or self.canon.get("style")
        if not look:
            look = ("professional cinematic photograph" if sw.get("pro_photo") else "candid handheld film photograph, natural imperfections")
            look += ", " + ("daylight" if sw.get("daytime") else "night") + ", " + ("indoors" if sw.get("indoor") else "outdoors")
            if sw.get("atmosphere"):
                look += ", atmospheric haze and depth"
        parts.append(f"Style: {look}, photorealistic film still, natural skin texture.")
        if person:
            parts.append("Only one person in the frame." if people <= 1 else "")
        parts.append("No text, no letters, no logos, no watermark.")
        return " ".join(p for p in parts if p)

    # ---- stills -------------------------------------------------------------------------------
    def still_job(self, s):
        wf = self.p.workflow("still")
        wf.apply_defaults()
        chars = [self.char(c) for c in s.get("chars", [])]
        loc = (s.get("location") or self.world_cfg(s).get("location") or self.canon.get("location", "")) + \
              (", " + s["location_extra"] if s.get("location_extra") else "")
        framing = s.get("framing", "medium")
        person = outfit = action = ""
        fem = male = 0
        if chars:
            ch = chars[0]   # the structured prompt is built for one person; add a second with a 3-image sheet edit
            outfits = ch.get(f"outfit_{self.world(s)}") or ch.get("outfit") or {}
            person, outfit, action = ch.get("person", ""), outfits.get(framing, ""), s.get("action", "")
            fem, male = (ch.get("count") or {}).get("female", 0), (ch.get("count") or {}).get("male", 0)
        else:
            action = s.get("action", "")
        if wf.has("person"):
            wf.set("person", person)
            wf.set("outfit", outfit)
            wf.set("action", action)
            wf.set("location", loc)
            wf.try_set("female_count", fem)
            wf.try_set("male_count", male)
        elif wf.spec.get("prompt_style") == "caption":
            wf.set("prompt", self.caption(s, person, outfit, action, loc, framing, fem + male))
        else:
            wf.set("prompt", ", ".join(x for x in (person, ("wearing " + outfit) if outfit else "", action, loc) if x))
        sw = dict(self.canon.get("image_switches_default", {}), **self.world_cfg(s).get("switches", {}), **s.get("switches", {}))
        for k, v in sw.items():
            wf.try_set(f"switch.{k}", bool(v))
        wf.try_set("switch.closeup", framing == "close" and bool(chars))
        w, h = self.p.cfg["work_size"]                  # still size follows the video size
        wf.try_set("long_edge", max(w, h))
        wf.try_set("short_edge", min(w, h))
        wf.try_set("vertical", h > w)
        wf.try_set("width", w)
        wf.try_set("height", h)
        wf.seed(s["seed"])
        never = ", ".join([c.get("never", "") for c in chars if c.get("never")] + ([self.canon["never_common"]] if self.canon.get("never_common") else []))
        if never:
            wf.append("negative", ", " + never)
        label = self.still_label(s)
        keep = label if label in wf.outputs() else (s.get("edit_base") if s.get("edit_base") in wf.outputs() else self.default_model(s))
        if keep not in wf.outputs():
            keep = wf.outputs()[0]
        for o in wf.outputs():
            wf.output(self.p.prefix("stills", f"{s['id']}_{o}"), which=o)
        if s.get("prune", True) and len(wf.outputs()) > 1:
            wf.prune_outputs(keep)
        return self.save(wf, f"{s['id']}_still.json", {"kind": "still", "shot": s["id"], "seed": s["seed"], "model": keep})

    # ---- identity edits -------------------------------------------------------------------------------
    def sheet_text(self, s, wording):
        ch_key = s["chars"][0]
        c = self.char(ch_key)
        who, pos = c["noun"], c["possessive"]
        expr = s.get("expr") or "natural"
        extra = c.get("edit_extra", "")
        if wording == "C":    # BFL "image N" naming + exhaustive preservation, skin tone not carried from the sheet
            sig = (c["signature"] + ", ") if c["signature"] else ""
            return (f"Modify image 1 using image 2 for reference. Replace the {who} in image 1 with the {who} from the film character sheet in image 2, "
                    f"carrying over {pos} exact face, facial structure, eyes, nose, mouth, jawline, {sig}body proportions and clothing from image 2. "
                    f"The {who}'s facial expression is {expr}. {extra} "
                    f"Preserve image 1 exactly: the pose, body position, hand positions, camera angle, framing, lens, lighting direction and color, background and composition stay unchanged. "
                    f"Only one {who} in the image. Style: photorealistic cinematic film still, natural clear healthy skin, flattering soft light on the face.")
        return (f"using [reference_image1] as the base, update the appearance of the {who} to match the film character sheet from [reference_image2] "
                f"using accurate face, hair, body proportions and clothing carried over exactly from [reference_image2]. keep the exact same pose, "
                f"body position, camera angle, framing, lens, lighting, colors and background as [reference_image1]. "
                f"the {who}'s facial expression is {expr}. {extra} "
                f"photorealistic, clear healthy even skin, flattering soft light on the face, plain clothing with no lettering or print, only one {who} in the image.")

    def sheet_job(self, s, wording=None, seed=None, tag="edit"):
        ch_key = s["chars"][0]
        world = self.world(s)
        base_label = s.get("edit_base") or self.default_model(s)
        img, _ = self.stage_still(s, base_label)
        add = s.get("add")
        if add:
            wf = self.p.workflow("edit3")
            a, c = self.char(add["char"]), self.char(ch_key)
            wf.set("image3", self.sheet(add["char"], add.get("world", world)))
            text = (f"using [reference_image1] as the base, update the appearance of the {c['noun']} to match the film character sheet from [reference_image2] "
                    f"using accurate face, body proportions and clothing carried over exactly from the [reference_image2] and then add in the {a['noun']} character "
                    f"from [reference_image3] so that {a['pronoun']} appears naturally and realistically added into the shot, {add.get('where', '')}. keep the outfits clothing and "
                    f"costumes exactly the same as the reference images. keep the camera angle, framing, lighting and background of [reference_image1]. "
                    f"make the {c['noun']}'s facial expression {s.get('expr') or 'natural'} and the {a['noun']}'s expression {add.get('expr', 'natural')}. "
                    f"both people have clear healthy even skin. {c.get('edit_extra', '')} {a.get('edit_extra', '')}")
        else:
            wf = self.p.workflow("edit2")
            text = self.sheet_text(s, wording or s.get("wording", "A"))
        wf.apply_defaults()
        self.size(wf)
        wf.set("image1", img)
        wf.set("image2", self.sheet(ch_key, world, s.get("sheet_ref")))
        if s.get("edit_light"):
            text += " " + s["edit_light"]
        wf.set("prompt", text)
        seed = s["seed"] if seed is None else seed
        wf.seed(seed)
        wf.output(self.p.prefix("stills", f"{s['id']}_{tag}"))
        return self.save(wf, f"{s['id']}_{tag}.json", {"kind": "edit", "shot": s["id"], "seed": seed, "label": tag, "wording": wording or s.get("wording", "A")})

    def edit_job(self, s):
        wf = self.p.workflow("edit2")
        wf.apply_defaults()
        self.size(wf)
        img, _ = self.stage_still(s, s.get("edit_base") or self.default_model(s))
        wf.set("image1", img)
        wf.set("image2", self.input_file(s["edit_ref"]))
        wf.set("prompt", s["edit_prompt"])
        wf.seed(s["seed"])
        wf.output(self.p.prefix("stills", f"{s['id']}_edit"))
        return self.save(wf, f"{s['id']}_edit.json", {"kind": "edit", "shot": s["id"], "seed": s["seed"], "label": "edit"})

    # ---- videos -------------------------------------------------------------------------------
    def sung(self, s):
        if not s.get("lyric") or s.get("no_lyric"):   # quoting the words burned subtitles into some shots: no_lyric turns it off
            return self.names(s["video"], s)
        c = self.char(s["chars"][0]) if s.get("chars") else {"noun": "woman"}
        verb, gerund, style = (c.get("voice") or {}).get("verb"), (c.get("voice") or {}).get("gerund"), (c.get("voice") or {}).get("style")
        dv, dg, ds = VOICES.get(c["noun"], VOICES["woman"])
        verb, gerund, style = verb or dv, gerund or dg, style or ds
        who = c["noun"]
        return f'{self.names(s["video"], s)} The {who} {verb} the lyric words "{s["lyric"]}"\n\n([{who}], [{gerund}]): "{s["lyric"]}", {style}\n'

    def video_job(self, s):
        mode, sid = s["mode"], s["id"]
        n = self.frames(s)
        meta = {"kind": mode, "shot": sid, "seed": s["seed"], "frames": n}
        if mode == "ff":
            wf = self.p.workflow("ff")
            wf.apply_defaults()
            self.size(wf)
            img, label = (self.input_file(s["first_frame"]), "file") if s.get("first_frame") else self.stage_still(s)
            wf.set("image", img)
            wf.set("prompt", self.names(s["video"], s))
            wf.append("negative", self.neg["ff"])
            wf.set("frames", n)
            name = f"{sid}_ff_{label}"
        elif mode == "t2v":
            wf = self.p.workflow("t2v")
            wf.apply_defaults()
            wf.set("prompt", self.names(s["video"], s))
            wf.append("negative", self.neg["t2v"])
            wf.set("frames", n)
            w, h = self.p.cfg["work_size"]
            wf.try_set("width", w)
            wf.try_set("height", h)
            label, name = "t2v", f"{sid}_t2v"
        elif mode == "fflf":
            wf = self.p.workflow("fflf")
            wf.apply_defaults()
            self.size(wf)
            src_id = s.get("start_shot") or s.get("still_from")
            src = self.by_id[src_id] if src_id else s
            if s.get("still_from") and src.get("dropped"):   # loop seam: end on the first live shot's still
                src = next(x for x in self.shots if not x.get("dropped") and x["mode"] in STILL_MODES and not x.get("still_from"))
            if s.get("first_frame"):
                img, label = self.input_file(s["first_frame"]), "file"
            else:
                img, label = self.stage_still(src)
            end = img
            if s.get("last_frame"):
                end = self.input_file(s["last_frame"])
            elif s.get("end_shot"):
                end, _ = self.stage_still(self.by_id[s["end_shot"]], s.get("end_still"))
            wf.set("image", img)
            wf.set("last_image", end)
            wf.set("prompt", self.names(s["video"], s))
            secs = math.ceil((n - 1) / self.fps - 1e-6) if "frames" in s else int(s.get("seconds", 5))
            wf.set("seconds", secs)
            if s.get("audio"):
                wf.set("audio", s["audio"])
                wf.try_set("audio_start", s["audio_start"])
                wf.try_set("audio_end", s["audio_start"] + secs)
                wf.try_set("audio_seconds", secs)
            if s.get("arrive_frame") is not None:   # the end guide lands mid-shot (multiple of 8); free performance after
                wf.set("arrive_frame", int(s["arrive_frame"]))
            if s.get("arrive_strength"):
                wf.set("last_strength", float(s["arrive_strength"]))
            if s.get("chars"):
                wf.append("negative", self.neg["fflf_people"])
            meta["frames"] = secs * self.fps + 1
            name = f"{sid}_fflf_{label}"
        elif mode == "lipsync":
            wf = self.p.workflow("lipsync")
            wf.apply_defaults()
            self.size(wf)
            img, label = (self.input_file(s["first_frame"]), "file") if s.get("first_frame") else self.stage_still(s)
            wf.set("image", img)
            wf.set("prompt", self.sung(s))
            wf.append("negative", self.neg["lipsync"])
            dur = (n - 1) / self.fps + 0.001 if "frames" in s else s["audio_seconds"]
            wf.set("audio", s["audio"])
            wf.set("audio_start", s["audio_start"])
            wf.set("audio_seconds", dur)
            name = f"{sid}_lipsync_{label}"
        else:
            return None
        if s.get("negative_extra"):
            wf.append("negative", ", " + s["negative_extra"])
        wf.seed(s["seed"])
        wf.output(self.p.prefix("clips", name))
        meta["still"] = label
        return self.save(wf, f"{sid}_video.json", meta)

    # ---- driver -------------------------------------------------------------------------------
    def run(self, stage, ids=None):
        written, skipped = [], []
        for s in self.shots:
            if ids and s["id"] not in ids:
                continue
            if s.get("dropped") or s["mode"] == "reuse":
                continue
            try:
                if stage == "stills" and s["mode"] in STILL_MODES and not s.get("still_from") and not s.get("first_frame"):
                    written.append(self.still_job(s))
                elif stage == "sheetedits" and s.get("chars") and s.get("still") == "edit" and s["mode"] in STILL_MODES:
                    written.append(self.sheet_job(s))
                elif stage == "edits" and s.get("edit_ref"):
                    written.append(self.edit_job(s))
                elif stage == "videos":
                    p = self.video_job(s)
                    if p:
                        written.append(p)
            except FileNotFoundError as e:
                skipped.append(f"{s['id']}: {e}")
        return {"written": [self.p.rel(w) for w in written], "skipped": skipped}


def build(project, stage, ids=None, picks=None, shots_name="shots_resolved.json"):
    return Builder(project, shots_name, picks).run(stage, ids)


def variants(project, ids, wordings="AC", per_wording=3, tag="v", seed_offset=30000, shots_name="shots_resolved.json"):
    """Seed x wording grid of the identity edit, for picking the best face: stills/<id>_<tag><W><k>_*.png"""
    b = Builder(project, shots_name)
    out = []
    for sid in ids:
        s = b.by_id[sid]
        for w in wordings:
            for k in range(per_wording):
                out.append(b.sheet_job(s, wording=w, seed=s["seed"] + seed_offset + 1000 * k, tag=f"{tag}{w}{k}"))
    return [project.rel(p) for p in out]
