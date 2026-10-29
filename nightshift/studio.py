"""Nightshift Studio: a whole project from a few answers.

    create(root, form)  ->  Project

The form is what the app asks (or what an agent sends): who is in the video (a photo and/or a description), the song
(a brief and lyrics for MiniMax Music 3, or your own track), a scene preset, the length and the aspect. From that this
module writes canon.json, shots.json, song/caption.md, song/lyrics.txt and project.json, so the pipeline can run with
nobody editing JSON. Everything it writes is a normal project: open the files later and direct it by hand.
"""
import os
import re
import shutil
import subprocess

from . import project as P

LENGTHS = {
    "short": {"profile": "short", "seconds": 40, "shots": 8, "label": "30-40 s, 8 shots, about an hour on a 3090"},
    "medium": {"profile": "short", "seconds": 75, "shots": 14, "label": "60-75 s, 14 shots, about two hours on a 3090"},
}

# A scene preset is a look and three places. The shot pattern below moves the performer through them.
SCENES = {
    "night-avenue": {
        "label": "Night Avenue",
        "blurb": "Sodium lamps, wet asphalt, a rooftop over the city. The first video's look.",
        "switches": {"bad_photo": True, "pro_photo": False, "indoor": False, "daytime": False, "atmosphere": True},
        "style": "candid handheld 35mm film photograph at night, sodium street light and neon spill, wet reflections, light mist",
        "grade": "A2_portra_dusk_plus",
        "places": [
            "a long empty avenue in a city at night, wet asphalt reflecting sodium street lamps and shop signs with no readable text, light mist",
            "the flat gravel rooftop of an old brick building at night, water tanks, the city skyline glowing behind under low clouds",
            "a narrow side street at night, a laundromat window glowing green, puddles, steam rising from a grate",
        ],
        "establish": "Aerial drone shot at night rising slowly over a city grid, ribbons of headlights and taillights streaming along the "
                     "avenues, low clouds glowing orange from below. Smooth, cinematic camera movement.",
        "genre": "warm late-night synth pop with a dusty drum machine, 96 BPM, A minor, hopeful under the melancholy",
    },
    "desert-highway": {
        "label": "Desert Highway",
        "blurb": "Golden hour on a two-lane road, a motel sign, heat shimmer.",
        "switches": {"bad_photo": False, "pro_photo": True, "indoor": False, "daytime": True, "atmosphere": True},
        "style": "cinematic 35mm photograph at golden hour, low warm sun, long shadows, heat shimmer, dusty air",
        "grade": "C_faded_pastel",
        "places": [
            "the shoulder of an empty two-lane desert highway at golden hour, cracked asphalt, sagebrush, distant mountains",
            "the gravel lot of a small roadside motel at golden hour, a tall motel sign with no readable text, a vintage car",
            "a dry lake bed at sunset, flat cracked white earth to the horizon, a pink and orange sky",
        ],
        "establish": "Wide aerial shot gliding low along an empty two-lane highway through the desert at golden hour, the road "
                     "vanishing toward distant mountains, long shadows, dust in the air. Smooth, cinematic camera movement.",
        "genre": "dusty desert rock with reverb guitar and a slow backbeat, 84 BPM, E minor, wide open and restless",
    },
    "neon-stage": {
        "label": "Neon Stage",
        "blurb": "A dark performance space, haze and coloured light, a mirrored back wall.",
        "switches": {"bad_photo": False, "pro_photo": True, "indoor": True, "daytime": False, "atmosphere": True},
        "style": "cinematic concert photograph, deep magenta and cyan stage light, haze beams, glossy black floor reflections",
        "grade": "B_cinestill_night",
        "places": [
            "a dark empty performance stage, magenta and cyan light beams cutting through haze, a glossy black floor",
            "a long corridor backstage lit by a single red bulb, concrete walls, cables on the floor",
            "the same stage from the back of the room, a wall of small warm bulbs behind, haze, empty floor",
        ],
        "establish": "Slow dolly through an empty dark performance space, coloured light beams sweeping through thick haze, "
                     "reflections on a glossy black floor. Smooth, cinematic camera movement.",
        "genre": "dark pulsing electro pop with heavy sub bass and gated synths, 118 BPM, F minor, confident and hypnotic",
    },
    "seaside-dawn": {
        "label": "Seaside Dawn",
        "blurb": "Blue hour on an empty beach, a wooden pier, soft wind.",
        "switches": {"bad_photo": False, "pro_photo": True, "indoor": False, "daytime": True, "atmosphere": True},
        "style": "soft cinematic photograph at blue hour before dawn, cool pastel light, sea mist, gentle wind",
        "grade": "A_portra_dusk",
        "places": [
            "an empty sandy beach at blue hour before dawn, calm waves, sea mist, a pale pink horizon",
            "a long weathered wooden pier over the sea at dawn, wet planks, gulls in the distance",
            "low dunes with tall grass bending in the wind above the beach at dawn, the sea behind",
        ],
        "establish": "Slow aerial shot drifting along an empty shoreline at blue hour, gentle waves rolling in, sea mist, the first "
                     "pink light on the horizon. Smooth, cinematic camera movement.",
        "genre": "dreamy indie folk pop with fingerpicked guitar, soft piano and brushed drums, 88 BPM, D major, tender and hopeful",
    },
}

DEFAULT_LYRICS = """[Intro]
Every light is burning for someone

[Chorus]
Tell me what you're chasing
Tell me where it goes
Every road is open
Only the night knows

[Outro]
Only the night knows"""

DEFAULT_LYRICS_LONG = """[Intro]
Every light is burning for someone

[Verse]
Somebody left the radio on
Three floors up and the window wide
I can hear the city breathing
Slow and even, side to side

[Chorus]
Tell me what you're chasing
Tell me where it goes
Every road is open
Only the night knows

[Outro]
Only the night knows"""

# the eight-shot pattern: (mode, framing, place, with the character, sings)
PATTERN = [
    ("t2v", "wide", None, False, False),
    ("lipsync", "close", 0, True, True),
    ("ff", "medium", 1, True, False),
    ("lipsync", "medium", 2, True, True),
    ("ff", "wide", 0, True, False),
    ("lipsync", "close", 1, True, True),
    ("ff", "wide", 2, True, False),
    ("fflf", "wide", 0, False, False),
]
ACTIONS = {
    ("lipsync", "close"): ("singing softly to the camera, eyes half closed, 85mm lens", "calm, lips gently closed, about to sing"),
    ("lipsync", "medium"): ("singing with feeling, one hand moving with the music, 50mm lens", "open, singing"),
    ("ff", "medium"): ("walking slowly toward the camera, arms loose, looking past the lens, 35mm lens", "restless, searching"),
    ("ff", "wide"): ("standing alone in the middle of the frame, turning to look over the shoulder, 24mm lens", "thoughtful"),
}
VIDEO = {
    ("lipsync", "close"): "Close-up of {lead} singing softly, the background a soft blur of light. Handheld camera drifting slowly around {pr}.",
    ("lipsync", "medium"): "Medium shot of {lead} singing with feeling. The camera arcs slowly around {pr}, steady.",
    ("ff", "medium"): "Medium shot of {lead} walking slowly toward the camera. The camera tracks backward in front of {pr}, steady.",
    ("ff", "wide"): "Wide shot of {lead} standing alone, turning to look over {po} shoulder as the wind moves {po} hair. The camera "
                    "pushes in slowly.",
}


def slug(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return s[:40] or "video"


def lyric_lines(lyrics):
    from .lyrics import sheet_lines
    return sheet_lines(lyrics or "")


def pick_anchors(lines, n):
    """n lyric lines spread over the song, in order (the lip-sync shots start on them)."""
    if not lines or n <= 0:
        return []
    if n >= len(lines):
        return list(lines)
    step = len(lines) / n
    return [lines[int(i * step)] for i in range(n)]


def character(form_char):
    noun = (form_char.get("noun") or "woman").strip().lower()
    if noun not in ("woman", "man", "person"):
        noun = "person"
    pron = {"woman": ("she", "her", "her"), "man": ("he", "him", "his"), "person": ("they", "them", "their")}[noun]
    look = (form_char.get("look") or "").strip().rstrip(".") or {
        "woman": "woman in her late twenties, oval face, dark brown eyes, straight black shoulder-length hair, light olive skin",
        "man": "man in his early thirties, short dark curly hair, warm brown eyes, light stubble, medium brown skin",
        "person": "person in their late twenties, short bleached hair, grey eyes, freckles"}[noun]
    if not re.match(rf"^(a |an )?{noun}\b", look):
        look = f"{noun}, {look}"
    look = re.sub(r"^(a|an) ", "", look)
    outfit = (form_char.get("outfit") or "").strip().rstrip(".") or "a plain charcoal crew-neck sweater, dark wide-leg trousers"
    top = outfit.split(",")[0].strip()
    shoes = (form_char.get("shoes") or "").strip() or "white canvas sneakers"
    hair = next((p.strip() for p in look.split(",") if "hair" in p), "")
    c = {
        "name": form_char.get("name") or "Lead",
        "noun": noun, "pronoun": pron[0], "possessive": pron[2],
        "count": {"female": 1 if noun == "woman" else 0, "male": 1 if noun == "man" else 0},
        "person": look + ", clear healthy skin",
        "outfit": {"close": top, "medium": outfit, "wide": f"{outfit}, {shoes}"},
        "never": (form_char.get("never") or "logos, readable text on clothing, heavy makeup, airbrushed plastic skin").strip(),
        "video_name": f"the {noun}" + (f" with {hair}" if hair else "") + f" in {top}",
        "signature": hair,
        "reference": None,
        "edit_extra": f"{pron[2]} skin is clear and healthy.".capitalize(),
        "voice": {"verb": "sings", "gerund": "singing", "style": "warm, close, expressive singing"},
    }
    return c


def shots(scene, lyrics, n_shots, ch=None, seed0=1000):
    sc = SCENES[scene]
    lines = lyric_lines(lyrics)
    pattern = [PATTERN[0]] + [PATTERN[1 + (i % 6)] for i in range(n_shots - 2)] + [PATTERN[-1]]
    sung = [i for i, p in enumerate(pattern) if p[4]]
    anchors = pick_anchors(lines, len(sung))
    out = []
    for i, (mode, framing, place, with_char, sings) in enumerate(pattern):
        sid = f"s{i + 1:02d}"
        section = "intro" if i == 0 else "outro" if i == len(pattern) - 1 else "body"
        s = {"id": sid, "section": section, "world": "real", "mode": mode, "framing": framing, "seed": seed0 + i + 1}
        if mode == "t2v":
            s.update(chars=[], video=sc["establish"])
        elif mode == "fflf":
            s.update(chars=[], fit=True, action="", location=sc["places"][place] + ", completely empty",
                     video=f"A wide shot of the empty place where the video began: {sc['places'][place]}. The camera glides slowly "
                           f"forward and rises as the light fades.")
        else:
            if sings and i in sung and sung.index(i) < len(anchors):
                s["anchor"] = anchors[sung.index(i)]
            else:
                mode = s["mode"] = "ff" if mode == "lipsync" else mode
                if framing == "close":
                    s["framing"] = framing = "medium"
            key = (mode, framing) if (mode, framing) in ACTIONS else ("ff", "wide")
            act, expr = ACTIONS[key]
            obj, pos = {"she": ("her", "her"), "he": ("him", "his")}.get((ch or {}).get("pronoun"), ("them", "their"))
            s.update(chars=["lead"], still="edit", expr=expr, action=act, location=sc["places"][place],
                     video=VIDEO[key].replace("{pr}", obj).replace("{po}", pos))
        out.append(s)
    return {"_readme": "Written by Nightshift Studio from a scene preset. Song-agnostic: lip-sync shots start on the lyric line in "
                       "\"anchor\". Edit freely; fields: docs/shots.md.", "shots": out}


def _ts(sec):
    return f"{int(sec) // 60}:{int(sec) % 60:02d}"


def caption(scene, vibe, noun, seconds, instrumental=False):
    sc = SCENES[scene]
    voice = {"woman": "One female lead vocal", "man": "One male lead vocal", "person": "One lead vocal"}[noun]
    vocal = "Instrumental, no vocals." if instrumental else (
        f"{voice}: close and sincere, every word clear, doubled softly in the chorus. No other voices.")
    if seconds < 60:
        a, b = round(seconds * 0.2), round(seconds * 0.8)
        arr = (f"{_ts(0)}-{_ts(a)} Intro: the first line sung over a sparse bed.\n"
               f"{_ts(a)}-{_ts(b)} Chorus: the full groove, the hook sung twice.\n"
               f"{_ts(b)}-{_ts(seconds)} Outro: the last line, the music rings out in a natural decay. No hard ending.\n")
    else:
        a, b, c = 8, round(seconds * 0.42), seconds - 12
        arr = (f"{_ts(0)}-{_ts(a)} Intro: the first line sung over a sparse bed.\n{_ts(a)}-{_ts(b)} Verse: drums and bass enter.\n"
               f"{_ts(b)}-{_ts(c)} Chorus: everything opens up, the hook sung twice.\n"
               f"{_ts(c)}-{_ts(seconds)} Outro: the last line, a natural decay. No hard ending.\n")
    return (f"# Song brief (the MiniMax Music 3 caption)\n<!-- Written by Nightshift Studio. Headings and comments are stripped "
            f"before the text goes to the model. See docs/prompting.md. -->\n\n## Global metadata\nGenre: {sc['genre']}."
            + (f" {vibe.strip().rstrip('.')}." if vibe and vibe.strip() else "") +
            f"\nA short song of about {seconds} seconds with a real ending.\n\n## Vocal details\n{vocal}\n\n## Arrangement\n" + arr)


def trim_audio(src, dst, start, seconds):
    """Cut an uploaded track to the profile length, with a short fade out."""
    fade = min(2.0, seconds / 10)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{float(start):.3f}", "-t", f"{seconds:.3f}", "-i", src,
                    "-af", f"afade=t=out:st={max(0.0, seconds - fade):.3f}:d={fade:.3f}", "-ar", "44100", "-b:a", "320k", dst],
                   check=True)
    return dst


def create(root, form):
    """form: {name, length, aspect, image_model, mode, scene, comfy_url, comfy_dir,
              character: {noun, look, outfit, shoes, never, photo (path)},
              song: {source: "generate" | "upload", vibe, lyrics, audio (path), start}}"""
    length = LENGTHS[form.get("length") or "short"]
    scene = form.get("scene") or "night-avenue"
    if scene not in SCENES:
        raise ValueError(f"unknown scene '{scene}' (one of {', '.join(SCENES)})")
    song = form.get("song") or {}
    upload = song.get("source") == "upload"
    lyrics = (song.get("lyrics") or "").strip()
    if not upload and not lyrics:
        lyrics = DEFAULT_LYRICS if length["seconds"] < 60 else DEFAULT_LYRICS_LONG
    instrumental = upload and not lyric_lines(lyrics)
    p = P.init(root, form.get("name") or os.path.basename(root), form.get("comfy_url"), form.get("comfy_dir"),
               mode=form.get("mode") or "director")
    for junk in ("refs/README.md", "README.md"):          # the starter's notes describe its own example, not this video
        if os.path.exists(p.path(junk)):
            os.remove(p.path(junk))
    ch = character(form.get("character") or {})
    photo = (form.get("character") or {}).get("photo")
    if photo:
        ext = os.path.splitext(photo)[1].lower() or ".png"
        os.makedirs(p.path("refs"), exist_ok=True)
        shutil.copyfile(photo, p.path("refs", "lead" + ext))
        ch["reference"] = f"refs/lead{ext}"
    sc = SCENES[scene]
    canon = {
        "_readme": "Written by Nightshift Studio. Who is in the video and what never changes; identity words are copied by the "
                   "builder into every job.",
        "characters": {"lead": ch},
        "worlds": {"real": {"still_model": "flux", "switches": sc["switches"], "style": sc["style"]}},
        "default_world": "real",
        "location": sc["places"][0],
        "never_common": "text, letters, watermarks, logos",
        "image_switches_default": {"safe": True, "pro_photo": False, "bad_photo": True, "pov": False, "indoor": False,
                                   "daytime": False, "atmosphere": True, "suffix": False},
        "negatives": {},
    }
    p.save("canon.json", canon)
    p.save("shots.json", shots(scene, lyrics, length["shots"], ch))
    os.makedirs(p.path("song"), exist_ok=True)
    with open(p.path("song", "caption.md"), "w", encoding="utf-8") as f:
        f.write(caption(scene, song.get("vibe"), ch["noun"], length["seconds"], instrumental))
    with open(p.path("song", "lyrics.txt"), "w", encoding="utf-8") as f:
        f.write((lyrics or "[Instrumental]") + "\n")
    cfg = p.load("project.json")
    for k in ("fps", "work_size", "crop", "final_size", "video_frames", "takes", "song_seeds", "finish", "overlay", "sheets"):
        cfg.pop(k, None)                         # the profile decides these; project.json can still override any of them
    cfg.update({
        "profile": length["profile"], "length": form.get("length") or "short",
        "aspect": form.get("aspect") or "16:9", "image_model": form.get("image_model") or "flux2",
        "scene": scene, "song_max_seconds": length["seconds"],
        "grade": {"look": sc["grade"], "lifts": []},
        "sheets": {"approve": form.get("approve_looks", True) is not False, "yolo_source": "image" if photo else "text"},
    })
    if upload:
        src = song["audio"]
        dst = p.path("song", "song.mp3")
        trim_audio(src, dst, song.get("start") or 0, length["seconds"])
        cfg["song"] = "song/song.mp3"
        if instrumental:
            cfg["song_voices"] = []
    p.save("project.json", cfg)
    p.log("studio_create", scene=scene, length=cfg["length"], aspect=cfg["aspect"], image_model=cfg["image_model"],
          song="upload" if upload else "generate", photo=bool(photo))
    return P.Project(p.root)
