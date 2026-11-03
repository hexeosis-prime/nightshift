"""Nightshift Studio: a whole project from a few answers.

    create(root, form)  ->  Project

The form is what the app asks (or what an agent sends): who is in the video (a photo and/or a description), the song
(a brief and lyrics for MiniMax Music 3, or your own track), a scene preset, the length and the aspect. From that this
module writes canon.json, shots.json, song/caption.md, song/lyrics.txt and project.json, so the pipeline can run with
nobody editing JSON. Everything it writes is a normal project: open the files later and direct it by hand.
"""
import os
import random
import re
import shutil
import subprocess

from . import project as P

LENGTHS = {
    "short": {"profile": "short", "seconds": 40, "shots": 8, "label": "30-40 s, 8 shots, under an hour on a 3090"},
    "medium": {"profile": "short", "seconds": 75, "shots": 14, "label": "60-75 s, 14 shots, about 1.5 hours on a 3090"},
    "full": {"profile": "short", "seconds": 150, "shots": 26, "label": "2-3 min, 26 shots, overnight on a 3090"},
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
        "blurb": "A dark performance space, haze and colored light, a mirrored back wall.",
        "switches": {"bad_photo": False, "pro_photo": True, "indoor": True, "daytime": False, "atmosphere": True},
        "style": "cinematic concert photograph, deep magenta and cyan stage light, haze beams, glossy black floor reflections",
        "grade": "B_cinestill_night",
        "places": [
            "a dark empty performance stage, magenta and cyan light beams cutting through haze, a glossy black floor",
            "a long corridor backstage lit by a single red bulb, concrete walls, cables on the floor",
            "the same stage from the back of the room, a wall of small warm bulbs behind, haze, empty floor",
        ],
        "establish": "Slow dolly through an empty dark performance space, colored light beams sweeping through thick haze, "
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
    "rain-tavern": {
        "label": "Rain Tavern",
        "blurb": "A dim old bar on a rainy night, practical lamps, warm skin tones.",
        "switches": {"bad_photo": False, "pro_photo": True, "indoor": True, "daytime": False, "atmosphere": True},
        "style": "cinematic 35mm film photograph in a dim tavern at night, warm tungsten practical lamps, soft amber skin tones, rain on the windows",
        "grade": "A_portra_dusk",
        "places": [
            "a long wooden bar in a dim old tavern at night, brass taps, small warm table lamps, rain streaking the front windows",
            "a corner booth with worn red leather seats under a low hanging lamp, rain-blurred street lights through the glass",
            "the tavern doorway at night from the street, warm light spilling onto wet cobblestones, heavy rain in the lamplight",
        ],
        "establish": "Slow push in from a rainy street at night toward the glowing windows of an old tavern, rain falling through "
                     "the warm light, puddles rippling. Smooth, cinematic camera movement.",
        "genre": "smoky late-night soul with brushed drums, upright bass and a Rhodes piano, 78 BPM, D minor, intimate and warm",
    },
    "golden-warehouse": {
        "label": "Golden Warehouse",
        "blurb": "Golden hour in an empty factory: tall windows, dust in the light beams.",
        "switches": {"bad_photo": False, "pro_photo": True, "indoor": True, "daytime": True, "atmosphere": True},
        "style": "cinematic 35mm photograph in an industrial space at golden hour, low sun through tall windows, dust in the light beams, warm highlights",
        "grade": "A2_portra_dusk_plus",
        "places": [
            "the empty floor of an old brick warehouse at golden hour, long beams of sun through tall factory windows, dust floating",
            "a steel mezzanine walkway in the warehouse, rivets and railings, the low sun flaring through grimy glass",
            "a wide loading dock door open to the evening, warm light flooding in across concrete, a few wooden pallets",
        ],
        "establish": "Slow dolly across the empty floor of a vast brick warehouse at golden hour, sunbeams slanting through tall "
                     "windows, dust drifting in the light. Smooth, cinematic camera movement.",
        "genre": "anthemic indie rock with big room drums and chiming guitars, 104 BPM, G major, rising and triumphant",
    },
    "cathedral-light": {
        "label": "Cathedral Light",
        "blurb": "A vast stone hall, shafts of light through tall windows, slow camera moves.",
        "switches": {"bad_photo": False, "pro_photo": True, "indoor": True, "daytime": True, "atmosphere": True},
        "style": "cinematic photograph in a vast old stone hall, volumetric shafts of daylight through tall arched windows, soft haze, cool stone and warm light",
        "grade": "C_faded_pastel",
        "places": [
            "the long central aisle of a vast empty stone hall, shafts of light through tall arched windows, haze in the air",
            "the foot of a wide stone staircase under high vaulted ceilings, a single beam of light falling across the steps",
            "a high gallery walkway overlooking the hall, carved stone columns, light pouring through stained glass with no figures or text",
        ],
        "establish": "Slow crane up through a vast empty stone hall, shafts of daylight cutting through haze from tall arched windows, "
                     "dust glittering in the beams. Smooth, cinematic camera movement.",
        "genre": "cinematic ambient pop with choir pads, deep piano and a slow heartbeat kick, 70 BPM, C minor, vast and reverent",
    },
    "snow-motel": {
        "label": "Snow Motel",
        "blurb": "A roadside motel in falling snow, fluorescent lot lights, glowing curtains.",
        "switches": {"bad_photo": True, "pro_photo": False, "indoor": False, "daytime": False, "atmosphere": True},
        "style": "candid 35mm film photograph at night in falling snow, cold blue night, buzzing fluorescent lot lights, warm curtains glowing in motel windows",
        "grade": "B_cinestill_night",
        "places": [
            "the snowy parking lot of a small roadside motel at night, fluorescent lights, a row of doors with curtains glowing warm",
            "the outdoor walkway of the motel's second floor at night, snow drifting past the railing, an ice machine humming",
            "an empty two-lane road beside the motel at night, snowbanks, a lone streetlight, snow falling in its beam",
        ],
        "establish": "Wide shot slowly pushing toward a lonely roadside motel at night in falling snow, fluorescent lights buzzing "
                     "over the lot, warm curtains glowing in the windows. Smooth, cinematic camera movement.",
        "genre": "lo-fi dream pop with a drum machine, warm tape-saturated synths and a soft vocal, 88 BPM, B minor, lonely but tender",
    },
    "living-room": {
        "label": "Living Room",
        "blurb": "A suburban ranch house at night: dim lamps, modern art, Los Angeles under dark clouds outside.",
        "switches": {"bad_photo": False, "pro_photo": True, "indoor": True, "daytime": False, "atmosphere": True},
        "style": "photographic living room in a suburban ranch style home at night, dim lighting, dark corners and shadows, "
                 "Portra film look, low warm lamp light, 50mm lens look, shallow depth of field",
        "grade": "A2_portra_dusk_plus",
        "places": [
            "a living room in a suburban ranch style home at night, dim lighting, dark corners, shadows, a beige fabric couch with "
            "square pillows, a coffee table, potted plants, modern art paintings on the wall, a sisal rug",
            "the same living room seen from the couch toward the big window, a view outside of Los Angeles at night under dark "
            "cloudy skies, potted plants silhouetted against the city lights",
            "a corner of the living room at night, modern art paintings on the wall, a potted plant, deep shadows, the sisal rug in "
            "a pool of dim lamp light",
        ],
        "establish": "Wide establishing shot of a living room in a suburban ranch style home at night, dim lighting and dark corners, "
                     "a beige couch, modern art on the walls, Los Angeles glowing under dark cloudy skies through the window, no people. "
                     "Slow, smooth cinematic camera move.",
        "genre": "warm bedroom electro pop with a soft four-on-the-floor kick, humming synth bass and glassy plucks, 108 BPM, C minor, cozy and late-night",
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
# The shot bank: proven music-video setups per (mode, framing), each a still action + expression + LTX motion prompt.
# Every video draws its own mix from it with a seed (repeatable: the seed is saved in shots.json), never the same setup twice
# in a row. {lead} = the performer, {pr} = her / him / them, {po} = her / his / their.
BANK = {
    ("lipsync", "close"): [
        ("handheld drift", "singing softly to the camera, eyes half closed, 85mm lens", "calm, lips gently closed, about to sing",
         "Close-up of {lead} singing softly, the background a soft blur of light. Handheld camera drifting slowly around {pr}."),
        ("slow push in", "looking straight into the lens, very still, 85mm lens", "intent, lips gently closed, about to sing",
         "Close-up of {lead} singing straight into the lens. The camera pushes in slowly and steadily toward {po} face."),
        ("profile turn", "in profile, about to turn toward the camera, 85mm lens", "calm, lips gently closed, about to sing",
         "Close-up of {lead} in profile, turning toward the camera and singing. Static camera, shallow focus."),
        ("light sweep", "singing with eyes closed, soft light on one side of the face, 85mm lens", "lost in the song, lips gently closed",
         "Close-up of {lead} singing as a soft band of light slowly sweeps across {po} face. Slow handheld drift."),
    ],
    ("lipsync", "medium"): [
        ("slow arc", "singing with feeling, one hand moving with the music, 50mm lens", "open, singing",
         "Medium shot of {lead} singing with feeling. The camera arcs slowly around {pr}, steady."),
        ("walk and sing", "singing while walking toward the camera, 50mm lens", "open, singing",
         "Medium shot of {lead} singing while walking toward the camera. The camera dollies backward ahead of {pr}, steady."),
        ("low angle rise", "singing, seen from a low angle, chin up, 35mm lens", "strong, singing",
         "Low-angle medium shot of {lead} singing with feeling. The camera rises slowly, looking up at {pr}."),
        ("half orbit", "singing, turning slightly with the music, 50mm lens", "open, singing",
         "Medium shot of {lead} singing. The camera orbits slowly halfway around {pr}, smooth and steady."),
        ("backlit rim", "singing with the brightest light behind, a bright rim around the hair and shoulders, 50mm lens", "open, singing",
         "Medium shot of {lead} singing, backlit with a bright rim of light. The camera drifts slowly sideways."),
    ],
    ("ff", "medium"): [
        ("walk toward", "walking slowly toward the camera, arms loose, looking past the lens, 35mm lens", "restless, searching",
         "Medium shot of {lead} walking slowly toward the camera. The camera tracks backward in front of {pr}, steady."),
        ("side track", "walking through the scene from left to right, looking ahead, 35mm lens", "focused, moving on",
         "Medium shot of {lead} walking through the scene. The camera tracks alongside {pr} at walking pace."),
        ("follow from behind", "walking away from the camera, seen from behind, head turned a little to one side, 35mm lens", "determined",
         "The camera follows close behind {lead} at shoulder height through the scene, smooth and steady."),
        ("groove", "dancing loosely to the beat, shoulders moving, 35mm lens", "joyful, lost in the music",
         "Medium shot of {lead} dancing loosely to the beat. Handheld camera moving with {pr}, bouncing slightly."),
    ],
    ("ff", "wide"): [
        ("look back", "standing alone in the middle of the frame, turning to look over the shoulder, 24mm lens", "thoughtful",
         "Wide shot of {lead} standing alone, turning to look over {po} shoulder as the air moves {po} hair. The camera pushes in slowly."),
        ("crane reveal", "standing small in the frame, looking up, 24mm lens", "awed",
         "Wide shot of {lead} standing still. The camera cranes up slowly to reveal the whole place around {pr}."),
        ("walk away", "walking away from the camera into the distance, 24mm lens", "resolute",
         "Wide shot of {lead} walking away from the camera into the distance. Static camera, the figure growing smaller."),
        ("spin", "spinning slowly with arms out, 24mm lens", "free, smiling",
         "Wide shot of {lead} spinning slowly with arms out. The camera circles slowly around {pr}."),
        ("silhouette", "standing in silhouette against the brightest light in the place, 24mm lens", "still, thoughtful",
         "Wide shot of {lead} in silhouette against the light, hair moving in the air. The camera pushes in slowly."),
    ],
}
ACTIONS = {k: v[0][1:3] for k, v in BANK.items()}      # the first setup of each kind (kept for anything that reads these)
VIDEO = {k: v[0][3] for k, v in BANK.items()}


class _Deck:
    """Draws setups for each (mode, framing) in a shuffled order, reshuffling when used up, never repeating back to back."""
    def __init__(self, seed):
        self.rng, self.decks, self.last = random.Random(seed), {}, {}

    def draw(self, key):
        if not self.decks.get(key):
            order = list(range(len(BANK[key])))
            self.rng.shuffle(order)
            if len(order) > 1 and order[0] == self.last.get(key):
                order.append(order.pop(0))
            self.decks[key] = order
        i = self.decks[key].pop(0)
        self.last[key] = i
        return BANK[key][i]


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


def voice_label(c, other=None):
    """The singer name used in lyric section tags and the caption's casting note."""
    v = {"woman": "Female Singer", "man": "Male Singer"}.get(c["noun"], "Singer")
    if other is not None and voice_label(other) == v:            # two women, two men, two people: number them
        v = "First " + v if c.get("_first") else "Second " + v
    return v


def tag_sections(lyrics):
    """Lyrics typed without [Section] tags get them: each block of lines (separated by an empty line) becomes a section,
    verses and choruses alternating; a block that repeats is the chorus. Tagged lyrics are left as they are."""
    text = (lyrics or "").strip()
    if not text or re.search(r"^\s*\[[^\]]+\]\s*$", text, re.M):
        return lyrics
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    counts = {b: blocks.count(b) for b in blocks}
    chorus = max(counts, key=counts.get) if max(counts.values()) > 1 else None
    out, v = [], 0
    for i, b in enumerate(blocks):
        if len(blocks) == 1:
            tag = "Verse"
        elif b == chorus or (chorus is None and i % 2 == 1):
            tag = "Chorus"
        else:
            v += 1
            tag = f"Verse {v}"
        out.append(f"[{tag}]\n{b}")
    return "\n\n".join(out)


def tag_duet(lyrics, ch, ch2):
    """Name a singer in every section tag (alternating, starting with the lead) unless the tags already name one.
    Returns (tagged lyrics, {lyric line index: "lead" | "partner"})."""
    v1, v2 = voice_label(ch, ch2), voice_label(ch2, ch)
    out, owner, who, k, li = [], {}, None, 0, 0
    for raw in (lyrics or "").splitlines():
        t = raw.strip()
        if t.startswith("[") and t.endswith("]"):
            name, _, tag_singer = t[1:-1].partition(" - ")
            if tag_singer:
                low = tag_singer.lower()
                who = "partner" if (v2.lower() in low or (v2 != v1 and v2.split()[0].lower() in low)) else "lead"
            else:
                who = "lead" if k % 2 == 0 else "partner"
                t = f"[{name.strip()} - {v1 if who == 'lead' else v2}]"
            k += 1
            out.append(t)
            continue
        if t:
            owner[li] = who or "lead"
            li += 1
        out.append(raw)
    return "\n".join(out), owner


def shots(scene, lyrics, n_shots, ch=None, seed0=1000, ch2=None, owner=None, shot_seed=None):
    """scene: one scene key, or a list of up to three; with several, the video moves through them in order and each shot
    carries its place's look."""
    keys = [scene] if isinstance(scene, str) else list(scene)[:3]
    scs = [SCENES[k] for k in keys]
    sc = scs[0]
    lines = lyric_lines(lyrics)
    owner = owner or {}
    n_ff = 0
    pattern = [PATTERN[0]] + [PATTERN[1 + (i % 6)] for i in range(n_shots - 2)] + [PATTERN[-1]]
    sung = [i for i, p in enumerate(pattern) if p[4]]
    anchors = pick_anchors(lines, len(sung))
    shot_seed = random.randrange(1, 10 ** 6) if shot_seed is None else int(shot_seed)
    deck = _Deck(shot_seed)
    out = []
    for i, (mode, framing, place, with_char, sings) in enumerate(pattern):
        sid = f"s{i + 1:02d}"
        section = "intro" if i == 0 else "outro" if i == len(pattern) - 1 else "body"
        s = {"id": sid, "section": section, "world": "real", "mode": mode, "framing": framing, "seed": seed0 + i + 1}
        sc = scs[min(len(scs) - 1, i * len(scs) // len(pattern))]       # the place block this shot is in
        if len(scs) > 1:
            s.update(style=sc["style"], switches=dict(sc["switches"]))
        if mode == "t2v":
            s.update(chars=[], video=sc["establish"])
        elif mode == "fflf":
            s.update(chars=[], fit=True, action="", location=sc["places"][place] + ", completely empty",
                     video=f"A wide shot of the empty place where the video began: {sc['places'][place]}. The camera glides slowly "
                           f"forward and rises as the light fades.")
        else:
            who = "lead"
            if sings and i in sung and sung.index(i) < len(anchors):
                s["anchor"] = anchors[sung.index(i)]
                if ch2:
                    who = owner.get(lines.index(s["anchor"]), "lead")
            else:
                if ch2:
                    who = "lead" if n_ff % 2 == 0 else "partner"
                    n_ff += 1
                mode = s["mode"] = "ff" if mode == "lipsync" else mode
                if framing == "close":
                    s["framing"] = framing = "medium"
            key = (mode, framing) if (mode, framing) in BANK else ("ff", "wide")
            setup, act, expr, video = deck.draw(key)
            s["setup"] = setup
            c = ch2 if who == "partner" else ch
            obj, pos = {"she": ("her", "her"), "he": ("him", "his")}.get((c or {}).get("pronoun"), ("them", "their"))
            if mode == "lipsync":
                s["no_lyric"] = True                 # quoted lyrics can burn in as subtitles; the song audio drives the mouth
            s.update(chars=[who], still="edit", wording="C", expr=expr, action=act, location=sc["places"][place],
                     video=video.replace("{pr}", obj).replace("{po}", pos).replace("{lead}", "{" + who + "}"))
            if ch2 and mode == "ff" and framing == "wide" and not any(x.get("add") for x in out):
                other = "partner" if who == "lead" else "lead"
                s["add"] = {"char": other, "where": "standing a few steps away, facing them", "expr": "natural"}
                s["video"] = (f"Wide shot of {{{who}}} and {{{other}}} together, a few steps apart, the wind moving their hair. "
                              f"The camera pushes in slowly.")
        out.append(s)
    return {"_readme": "Written by Nightshift Studio from a scene preset and the shot bank (studio.BANK; \"setup\" names the one "
                       "each shot drew). Song-agnostic: lip-sync shots start on the lyric line in \"anchor\". Edit freely; fields: "
                       "docs/shots.md.", "_shot_seed": shot_seed, "shots": out}


def _ts(sec):
    return f"{int(sec) // 60}:{int(sec) % 60:02d}"


def caption(scene, vibe, noun, seconds, instrumental=False, duet=None):
    sc = SCENES[scene]
    voice = {"woman": "One female lead vocal", "man": "One male lead vocal", "person": "One lead vocal"}[noun]
    vocal = "Instrumental, no vocals." if instrumental else (
        f"{voice}: close and sincere, every word clear, doubled softly in the chorus. No other voices.")
    cast = ""
    if duet and not instrumental:
        v1, v2 = duet
        cast = (f"THIS SONG HAS TWO DIFFERENT VOCALISTS. A {v1.upper()} sings only the sections tagged {v1}. A {v2.upper()} "
                f"sings only the sections tagged {v2}. They never sing or double each other's lines.\n\n")
        vocal = (f"Two lead vocals with clearly different voices: the {v1.lower()} close and sincere, the {v2.lower()} warm and "
                 f"lower. Every word clear. Each sings only their own tagged sections.")
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
            f"before the text goes to the model. See docs/prompting.md. -->\n\n{cast}## Global metadata\nGenre: {sc['genre']}."
            + (f" {vibe.strip().rstrip('.')}." if vibe and vibe.strip() else "") +
            f"\nA short song of about {seconds} seconds with a real ending.\n\n## Vocal details\n{vocal}\n\n## Arrangement\n" + arr)


def trim_audio(src, dst, start, seconds):
    """Cut an uploaded track to the profile length, with a short fade out."""
    fade = min(2.0, seconds / 10)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{float(start):.3f}", "-t", f"{seconds:.3f}", "-i", src,
                    "-af", f"afade=t=out:st={max(0.0, seconds - fade):.3f}:d={fade:.3f}", "-ar", "44100", "-b:a", "320k", dst],
                   check=True)
    return dst


def custom_scene(place, daytime=False, indoor=False):
    """A scene from one typed location: three views of it."""
    place = (place or "").strip().rstrip(".") or "an empty city street at night"
    light = ("soft daylight" if daytime else "night, practical lights and deep shadows") + (", indoors" if indoor else ", outdoors")
    return {
        "label": "Custom", "blurb": place,
        "switches": {"bad_photo": False, "pro_photo": True, "indoor": bool(indoor), "daytime": bool(daytime), "atmosphere": True},
        "style": f"cinematic 35mm film photograph, {light}, natural color, gentle atmosphere",
        "grade": "A2_portra_dusk_plus",
        "places": [place, f"{place}, seen from a different angle", f"{place}, a quieter corner of it"],
        "establish": f"Wide establishing shot of {place}, no people. Slow, smooth cinematic camera move.",
        "genre": "modern cinematic pop with a steady groove and warm synths, 100 BPM, A minor, bittersweet and hopeful",
    }


GRADES = {
    "A2_portra_dusk_plus": "Portra dusk +",
    "A_portra_dusk": "Portra dusk",
    "B_cinestill_night": "CineStill night",
    "C_faded_pastel": "Faded pastel",
    "none": "Ungraded",
}


def create(root, form):
    """form: {name, length, aspect, image_model, mode, scene, comfy_url, comfy_dir,
              character: {noun, look, outfit, shoes, never, photo (path)},
              song: {source: "generate" | "upload", vibe, lyrics, audio (path), start}}"""
    length = LENGTHS[form.get("length") or "short"]
    keys = [k for k in (form.get("scenes") or [form.get("scene") or "night-avenue"]) if k][:3] or ["night-avenue"]
    if "custom" in keys:
        SCENES["custom"] = custom_scene(form.get("custom_place"), form.get("custom_daytime"), form.get("custom_indoor"))
    for k in keys:
        if k not in SCENES:
            raise ValueError(f"unknown scene '{k}' (one of {', '.join(SCENES)})")
    scene = keys[0]
    song = form.get("song") or {}
    upload = song.get("source") == "upload"
    lyrics = (song.get("lyrics") or "").strip()
    if not upload and not lyrics:
        lyrics = DEFAULT_LYRICS if length["seconds"] < 60 else DEFAULT_LYRICS_LONG
    lyrics = tag_sections(lyrics)
    instrumental = upload and not lyric_lines(lyrics)
    p = P.init(root, form.get("name") or os.path.basename(root), form.get("comfy_url"), form.get("comfy_dir"),
               mode=form.get("mode") or "director", skip=("refs/README.md", "README.md"))   # the starter's notes are about its own example
    ch = character(form.get("character") or {})
    photo = (form.get("character") or {}).get("photo")
    f2 = form.get("character2") or {}
    ch2 = character(f2) if f2 else None
    owner = {}
    if ch2:
        ch["_first"] = True
        if ch2["name"] == ch["name"]:
            ch2["name"] = "Partner"
        if lyric_lines(lyrics):
            lyrics, owner = tag_duet(lyrics, ch, ch2)
    if photo:
        ext = os.path.splitext(photo)[1].lower() or ".png"
        os.makedirs(p.path("refs"), exist_ok=True)
        shutil.copyfile(photo, p.path("refs", "lead" + ext))
        ch["reference"] = f"refs/lead{ext}"
    if ch2 and f2.get("photo"):
        ext = os.path.splitext(f2["photo"])[1].lower() or ".png"
        os.makedirs(p.path("refs"), exist_ok=True)
        shutil.copyfile(f2["photo"], p.path("refs", "partner" + ext))
        ch2["reference"] = f"refs/partner{ext}"
    duet = (voice_label(ch, ch2), voice_label(ch2, ch)) if ch2 else None
    for c in (ch, ch2):
        if c:
            c.pop("_first", None)
    sc = SCENES[scene]
    canon = {
        "_readme": "Written by Nightshift Studio. Who is in the video and what never changes; identity words are copied by the "
                   "builder into every job.",
        "characters": {"lead": ch, **({"partner": ch2} if ch2 else {})},
        "worlds": {"real": {"still_model": "flux", "switches": sc["switches"], "style": sc["style"]}},
        "default_world": "real",
        "location": sc["places"][0],
        "never_common": "text, letters, watermarks, logos",
        "image_switches_default": {"safe": True, "pro_photo": False, "bad_photo": True, "pov": False, "indoor": False,
                                   "daytime": False, "atmosphere": True, "suffix": False},
        "negatives": {},
    }
    p.save("canon.json", canon)
    p.save("shots.json", shots(keys, lyrics, length["shots"], ch, ch2=ch2, owner=owner, shot_seed=form.get("shot_seed")))
    os.makedirs(p.path("song"), exist_ok=True)
    with open(p.path("song", "caption.md"), "w", encoding="utf-8") as f:
        f.write(caption(scene, song.get("vibe"), ch["noun"], length["seconds"], instrumental, duet))
    with open(p.path("song", "lyrics.txt"), "w", encoding="utf-8") as f:
        f.write((lyrics or "[Instrumental]") + "\n")
    cfg = p.load("project.json")
    for k in ("fps", "work_size", "crop", "final_size", "video_frames", "takes", "song_seeds", "finish", "overlay", "sheets"):
        cfg.pop(k, None)                         # the profile decides these; project.json can still override any of them
    cfg.update({
        "profile": length["profile"], "length": form.get("length") or "short",
        "aspect": form.get("aspect") or "16:9", "image_model": form.get("image_model") or "flux2",
        "scene": "+".join(keys), "song_max_seconds": length["seconds"],
        "grade": {"look": form.get("grade") if form.get("grade") in GRADES else sc["grade"], "lifts": []},
        "overlay": overlay_cfg(lyrics, form.get("name"), form.get("overlay"), form.get("aspect") or "16:9"),
        "sheets": {"approve": form.get("approve_looks", False) is True,   # hands-off never pauses; director mode stops for the look anyway
                   "yolo_source": "image" if photo else "text"},
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


def overlay_cfg(lyrics, title=None, enabled=False, aspect="16:9"):
    """The lyric HUD settings for a project: sections from the lyric sheet's [tags], the most repeated line as the hero.
    The HUD is drawn at the final size: 1920x1080, or 1080x1920 for vertical with the platform UI bands kept clear.
    enabled: True (lyrics + HUD graphics) or {lyrics, hud, color: rainbow | solid | contrast, solid: "#rrggbb"}."""
    o = enabled if isinstance(enabled, dict) else {"lyrics": bool(enabled), "hud": bool(enabled)}
    if not (o.get("lyrics") or o.get("hud")):
        return {"enabled": False}
    sections, seen, pending = [], {}, None
    lines = []
    for raw in (lyrics or "").splitlines():
        t = raw.strip()
        if not t:
            continue
        if t.startswith("[") and t.endswith("]"):
            pending = re.sub(r"\s*-\s*.*$", "", t[1:-1]).strip().upper() or "SECTION"
            continue
        lines.append(t)
        seen[t] = seen.get(t, 0) + 1
        if pending:
            sec = {"name": pending}
            if sections:
                sec["line"] = t
                if seen[t] > 1:
                    sec["occurrence"] = seen[t]
            sections.append(sec)
            pending = None
    hero = max(seen, key=lambda k: (seen[k], -lines.index(k))) if seen else None
    style = {"title": (title or "NIGHTSHIFT").upper()[:32], "label": "PASS 01", "face_label": "SUBJECT 01",
             "ticker": ["NIGHT SHIFT", "ALL CHANNELS OPEN", "TAKE {count}"], "widgets": {},
             "show_lyrics": bool(o.get("lyrics")), "show_hud": bool(o.get("hud")),
             "lyric_color": o.get("color") if o.get("color") in ("rainbow", "solid", "contrast") else "rainbow"}
    if style["lyric_color"] == "solid":
        style["lyric_solid"] = o.get("solid") if re.fullmatch(r"#[0-9a-fA-F]{6}", str(o.get("solid") or "")) else "#f5f2ea"
    if hero and seen[hero] > 1:
        style["hero"] = "^" + re.escape(hero.lower()).replace("\\ ", " ") + "$"
    return {"enabled": True, "sections": sections or [{"name": "INTRO"}], "style": style}
