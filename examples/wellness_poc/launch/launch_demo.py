"""Launch-video demo: "a wellness center in your pocket", two looks (A warm commercial, B cinematic film), 16:9.
Queues straight into ComfyUI (its queue runs on its own); every step skips what is already done.

  python3 launch_demo.py stills      phone bases for B, app-screen composites for A
  python3 launch_demo.py ui_b        app-screen composites for B (needs B bases)
  python3 launch_demo.py videos A|B  every shot, 2 takes, through vid_ltx (3 stages)
  python3 launch_demo.py music       one instrumental per look
  python3 launch_demo.py status      fetch finished files, print the table
"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))           # nightshift/
sys.path.insert(0, ROOT)
from nightshift.comfy import Comfy
from nightshift.workflows import Workflow

c = Comfy(os.environ.get("COMFY_URL", "http://10.0.1.171:8188"))
WF = [os.path.join(ROOT, "workflows")]
POC = os.path.join(ROOT, "_promo_poc", "out")
OUT = os.path.join(HERE, "out")
ST = os.path.join(HERE, "state.json")
W, H, TAKES = 1280, 768, 2

FILMIC = ("Cinematic film still from an arthouse feature, shot on 35mm Kodak Vision3 500T film with an anamorphic lens. "
          "Dramatic low-key contrast lighting: one strong motivated key light, deep shadows, rich blacks, subtle halation, "
          "heavy film grain, muted earthy palette with warm highlights. Moody, intimate, quiet. No text, no logos.")
STILL_NEG = "text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin"
VID_NEG = ("scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, "
           "birds, fast camera, still frame")

# the app screen: a calm, unbranded wellness app with one big card showing the place we are about to enter
APP = ("The photo is <ref_image_0>: {scene}. Keep that whole photo exactly as it is, same framing, same {who}, phone, "
       "room and light; <ref_image_1> is only the picture shown on the app screen. Replace only the phone's screen content with a "
       "calm modern wellness app screen: a soft warm cream background, a small greeting line \"Good evening\" at the top, "
       "one large rounded card filling most of the screen that shows the picture from <ref_image_1>, a short label under "
       "the card \"{label}\", and a row of four small round icons along the bottom. Clean, minimal, premium interface, "
       "sharp and bright on the screen. No brand name, no logo, no status bar clutter.")
PHONES = {
    "A": {"in_base": f"{POC}/phone_in_h_base.png", "out_base": f"{POC}/phone_out_h_base.png"},
    "B": {"in_prompt": "A close-up of a woman's hand holding a modern black smartphone in a dim, warm living room at dusk, "
                       "a single table lamp behind, sofa softly out of focus. The phone faces straight on to the camera, "
                       "centered, its screen lit plain soft white. " + FILMIC,
          "out_prompt": "A medium shot of a calm woman sitting on a sofa in a dim, warm living room at dusk, lamp light on her "
                        "face, holding a modern black smartphone up toward the camera in the center of the frame, its screen "
                        "lit plain soft white. " + FILMIC},
}
PLACES = {   # look -> place -> first-frame still
    "A": {k: f"{POC}/{k}_h_v0.png" for k in ("cave", "yoga", "session", "connect", "retreat")},
    "B": {k: f"{POC}/x_{k}_filmic_h.png" for k in ("cave", "yoga", "session", "connect", "retreat")},
}
LIGHT = {"A": "Warm, bright, welcoming light. Rendered as a polished photoreal commercial.",
         "B": "Low-key light with deep shadows and warm highlights. Rendered as a cinematic 35mm film, heavy grain, "
              "anamorphic."}
# 8 slots in screenplay order: genre, location, subject, action, camera, (light + style from LIGHT), sound
SHOTS = [
    ("s1_push_in", "fflf", ("ui_in", "cave"),
     "A launch film for a wellness app. A cozy living room, then a Himalayan salt cave relaxation room. A hand holds a "
     "smartphone showing a calm wellness app with the salt cave on its screen. The camera pushes slowly forward into the "
     "phone screen and through it, until the salt cave fills the frame and becomes the real room. One continuous, magical "
     "push-in, no cut. {light} Soft ambient swell."),
    ("s2_cave", "ff", ("cave",),
     "A launch film for a wellness app. A Himalayan salt cave relaxation room, glowing amber and rose salt brick walls, a "
     "floor of white salt crystals. People rest on cushioned loungers under cream blankets. They breathe slowly, one woman "
     "pulls her blanket higher and smiles with her eyes closed. Slow smooth dolly forward between the loungers, wide shot. "
     "{light} The scene holds steady as haze drifts. Quiet room tone, a low warm hum."),
    ("s3_yoga", "ff", ("yoga",),
     "A launch film for a wellness app. A sunlit yoga studio with oak floors and tall windows onto green trees. A small "
     "class and their instructor. Together they flow out of warrior pose and raise their arms overhead, breathing in "
     "unison. Slow lateral tracking shot along the row, medium wide. {light} Soft breathing, quiet room tone."),
    ("s4_session", "ff", ("session",),
     "A launch film for a wellness app. A softly lit sound healing room with linen curtains, candles and crystal singing "
     "bowls. A practitioner kneels beside a woman resting on a mat. She circles the mallet around the rim of a large "
     "crystal bowl; the woman breathes deeply and her face softens. Slow gentle push in, medium shot. {light} The deep "
     "ringing tone of a crystal singing bowl."),
    ("s5_connect", "ff", ("connect",),
     "A launch film for a wellness app. A warm tea lounge with floor cushions around a low wooden table, big windows with "
     "greenery. A group of friends. They laugh and talk, one pours tea for another, someone touches a friend's shoulder. "
     "Slow orbiting camera around the table, medium shot. {light} Warm laughter and soft conversation."),
    ("s6_retreat", "ff", ("retreat",),
     "A launch film for a wellness app. An open-air wooden yoga pavilion in lush tropical greenery, ferns and tall palms, "
     "morning mist. A small group walks along a wooden boardwalk toward the pavilion carrying rolled mats. They chat and "
     "smile as they walk, leaves move in a light breeze. Slow rising crane shot, wide. {light} Soft breeze through leaves."),
    ("s7_pull_out", "fflf", ("retreat", "ui_out"),
     "A launch film for a wellness app. A jungle retreat pavilion, then a cozy living room. The camera pulls slowly back "
     "out of the retreat, and the whole scene shrinks into the glowing screen of a smartphone held by a calm woman on her "
     "sofa. One continuous, magical pull-back reveal, no cut. {light} Soft ambient swell."),
    ("s8_end", "ff", ("ui_out",),
     "A launch film for a wellness app. A cozy living room. A calm woman holds up her phone showing a wellness app. She "
     "smiles softly at the screen. Very slow push in toward the phone, medium shot. {light} Quiet room tone."),
]
MUSIC = {
    "A": ("Instrumental, no vocals. 92 BPM, D major. Warm, lively, welcoming acoustic pop for a wellness launch film: "
          "fingerpicked acoustic guitar, soft hand percussion, light piano, warm pads, a gentle uplifting build. Bright and "
          "hopeful, never busy."),
    "B": ("Instrumental, no vocals, no drums. 70 BPM, D major. Cinematic and intimate: a sparse felt piano motif over slow "
          "string swells and a warm low pad, building gently to a quiet, emotional swell, then a long natural decay."),
}
ARR = ("\n\nArrangement: 0:00-0:05 Intro: the motif enters softly. 0:05-0:32 Body: a slow, continuous build, no sudden "
       "changes. 0:32-0:45 Outro: resolves and rings out in a long natural decay. No hard ending.")


def load():
    return json.load(open(ST)) if os.path.exists(ST) else {}


def save(st):
    json.dump(st, open(ST, "w"), indent=1)


def done(st, name):
    j = st.get(name)
    return j.get("file") if j and j.get("status") == "done" else None


def queue(st, name, wf):
    if name in st and st[name]["status"] in ("queued", "done"):
        return
    wf.output(f"launch_demo/{name}")
    st[name] = {"id": c.queue_prompt(wf.to_api()), "status": "queued"}
    save(st); print("queued", name)


def up(path):
    return c.upload(path, "launch_demo")


def ui_edit(st, look, which, base, place):
    wf = Workflow.load("edit_flux3_2image", WF)
    wf.set("image1", up(base)); wf.set("image2", up(PLACES[look][place]))
    who = "hand" if which == "in" or "in_base" in base or base.endswith("B_base_in.png") else "woman"
    scene = ("a close-up of a hand holding a smartphone in a living room" if who == "hand"
             else "a woman on a sofa holding up a smartphone")
    label = {"cave": "Salt Cave · 20 min", "retreat": "Jungle Retreat · Weekend"}[place]
    wf.set("prompt", APP.format(who=who, label=label, scene=scene))
    wf.set("width", W); wf.set("height", H); wf.seed(7701)
    queue(st, f"{look}_ui_{which}", wf)


def stills():
    st = load()
    for which in ("in", "out"):
        wf = Workflow.load("still_flux3", WF)
        wf.set("prompt", PHONES["B"][f"{which}_prompt"]); wf.set("negative", STILL_NEG + ", text on screen, app icons")
        wf.set("width", W); wf.set("height", H); wf.seed(5560)
        queue(st, f"B_base_{which}", wf)
    ui_edit(st, "A", "in", PHONES["A"]["in_base"], "cave")
    ui_edit(st, "A", "out", PHONES["A"]["out_base"], "retreat")


def redo_a_in():
    st = load()
    ui_edit(st, "A", "in", PHONES["A"]["in_base"], "cave")


def ui_b():
    st = load(); refresh(st)
    for which, place in (("in", "cave"), ("out", "retreat")):
        base = done(st, "B_base_in")     # B's sofa shot showed the back of the phone: both B app frames use the in-hand phone
        if not base:
            print("waiting on B base", which); continue
        ui_edit(st, "B", which, base, place)


def frame(st, look, key):
    if key.startswith("ui_"):
        return done(st, f"{look}_{key}")
    return PLACES[look][key]


def videos(look):
    st = load(); refresh(st)
    for name, mode, keys, prompt in SHOTS:
        imgs = [frame(st, look, k) for k in keys]
        if not all(imgs):
            print("waiting on", name, keys); continue
        for t in range(TAKES):
            wf = Workflow.load("vid_ltx", WF); wf.apply_defaults()
            first = up(imgs[0])
            wf.set("image", first); wf.set("last_image", up(imgs[1]) if mode == "fflf" else first)
            wf.set("toggle_use_lf", mode == "fflf"); wf.set("toggle_use_audio_in", False); wf.set("toggle_isolate_vocals", False)
            if mode == "fflf":
                wf.set("ff_strength", 0.8); wf.set("lf_strength", 0.9)
            wf.set("audio", up(os.path.join(HERE, "dummy.mp3")))
            wf.set("prompt", prompt.format(light=LIGHT[look])); wf.set("negative", VID_NEG)
            wf.set("width", W); wf.set("height", H); wf.set("fps", 24.0); wf.set("frames", 121)
            wf.seed(4440 + 17 * t)
            queue(st, f"{look}_{name}_t{t}", wf)


def music():
    st = load()
    for look, cap in MUSIC.items():
        wf = Workflow.load("song_minimax_m3", WF)
        wf.set("caption", cap + ARR)
        wf.set("lyrics", "[Intro]\n[Instrumental]\n\n[Body]\n[Instrumental]\n\n[Outro]\n[Instrumental]")
        wf.set("max_seconds", 45); wf.seed(4440); wf.try_set("tiled_decode", False)
        queue(st, f"{look}_music", wf)


def refresh(st):
    for name, j in st.items():
        if j["status"] != "queued":
            continue
        r = c.result(j["id"])
        if r["status"] == "success":
            f = [x for x in r["files"] if x["filename"].rsplit(".", 1)[-1] in ("png", "mp4", "mp3", "flac", "wav")][0]
            dst = os.path.join(OUT, name + os.path.splitext(f["filename"])[1])
            c.download(f, dst)
            j.update(status="done", file=dst, seconds=r.get("seconds"))
        elif r["status"] in ("error", "unknown"):
            j.update(status="error", error=str(r.get("error"))[:300])
    save(st)


def status():
    st = load(); refresh(st)
    for name, j in sorted(st.items()):
        print(f"{name:22} {j['status']:7} {j.get('seconds') or ''} {j.get('error') or ''}")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    dummy = os.path.join(HERE, "dummy.mp3")
    if not os.path.exists(dummy):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "6",
                        "-q:a", "9", dummy], check=True)
    a = sys.argv[1:]
    {"stills": stills, "redo_a_in": redo_a_in, "ui_b": ui_b, "music": music, "status": status}.get(a[0], lambda: videos(a[1]))()
