"""Launch B4, the "lively" alt: same look, open and close as launch_B_v3_noline; inside the world each place gets a
close-up face reaction plus the wide shot (tea gets two close-ups), a brisker cut, a bowl-free session, livelier music.
Close-up first frames = crop + scale of the place's still, then a FLUX 3 re-photograph pass (hexe's trick) so the
close-up's perspective and detail read as a real close-up lens. Close-ups are first-frame-only (never a crop as a
first/last pair).

  python3 launch_b4.py prep              session still, music, close-up crops + re-photograph passes
  python3 launch_b4.py crop NAME x y w   crop one more close-up (e.g. from the new session still), then its pass
  python3 launch_b4.py videos            all close-ups + the session wide (2 takes, 1 s head)
"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import launch_demo as L
from nightshift.workflows import Workflow

LIGHT = L.LIGHT["B"]
NEG = (L.VID_NEG + ", walking backwards, people moving in reverse, objects moving by themselves, floating objects, "
       "singing bowls")
P = L.POC
# name: (source still, x, y, w)  - crop is w x 0.6w (5:3, the frame's own shape), scaled up to 1280x768
CROPS = {
    "C_cave": (f"{P}/x_cave_filmic_h.png", 60, 300, 480),
    "C_yoga": (f"{P}/x_yoga_filmic_h.png", 560, 120, 480),
    "C_tea1": (f"{P}/x_connect_filmic_h.png", 600, 170, 480),
    "C_tea2": (f"{P}/x_connect_filmic_h.png", 360, 170, 480),
}
WHO = {"C_cave": "the woman resting on the lounger", "C_yoga": "the smiling yoga instructor",
       "C_tea1": "the laughing woman in the dark sweater", "C_tea2": "the smiling woman in the cream sweater",
       "C_session": "the client lying on the mat"}
REPHOTO = ("<ref_image_0> is a rough enlargement of part of the photo <ref_image_1>. Recreate <ref_image_0> as a real "
           "close-up photograph taken with a close-up lens: {who}, the same face, hair, clothes, pose and expression, "
           "the same room, light and color, with natural close-up perspective, a softly blurred background and sharp, "
           "natural detail in the face and eyes. Natural clear healthy skin. Keep exactly the light, brightness and color "
           "grade of <ref_image_1>, with the room still visible softly behind. Shot on 35mm film, fine grain.")
SESSION = ("A minimal, calm energy healing session at dusk in a softly lit room with linen curtains and a wooden floor. "
           "A practitioner in a pale linen tunic kneels beside a client who lies on a cushioned mat under a light "
           "blanket, eyes closed, a soft smile. The practitioner rests both hands lightly on the client's shoulders. "
           "A few tea-light candles in small amber glass holders on a low shelf behind them. Nothing else in the room. "
           + L.FILMIC)
CU = {   # video prompts, 8 slots, every actor labeled
    "C_cave": "A launch film for a wellness app. A glowing Himalayan salt cave relaxation room. The woman resting on "
              "the lounger, close-up. The woman resting on the lounger slowly opens her eyes and breaks into a warm, "
              "contented smile, then lets her head sink back into the cushion. Static close-up with a very slight push "
              "in. " + LIGHT + " Quiet room tone.",
    "C_yoga": "A launch film for a wellness app. A sunlit yoga studio with tall windows onto green trees. The yoga "
              "instructor, close-up. The yoga instructor holds warrior pose, takes a deep breath and smiles broadly, "
              "eyes bright with joy, glancing toward her class. Close-up, slow gentle drift. " + LIGHT +
              " Soft breathing.",
    "C_tea1": "A launch film for a wellness app. A warm tea lounge with greenery behind. The woman in the dark sweater, "
              "close-up. The woman in the dark sweater laughs out loud, tips her head back a little, then laughs again, "
              "looking at her friend just off-screen to the left. Close-up, gentle handheld. " + LIGHT +
              " Warm laughter.",
    "C_tea2": "A launch film for a wellness app. A warm tea lounge with greenery behind. The woman in the cream "
              "sweater, close-up. The woman in the cream sweater smiles, nods, then laughs at something a friend says, "
              "looking just off-screen to the right. Close-up, gentle handheld. " + LIGHT + " Warm laughter.",
    "C_session": "A launch film for a wellness app. A softly lit healing room at dusk. The client lying on the mat, "
                 "close-up of her face. The client lying on the mat keeps her eyes closed, breathes slowly, and a "
                 "peaceful smile spreads across her face. Static close-up. " + LIGHT + " Quiet room tone.",
}
SESSION_WIDE = ("A launch film for a wellness app. A minimal healing room at dusk, linen curtains, candles on a shelf. "
                "The practitioner in the linen tunic and the client lying on the mat. The practitioner rests both hands "
                "lightly on the client's shoulders and stays completely still, eyes closed. The client lying on the mat "
                "stays still, eyes closed, with a soft smile. Slow gentle push in, medium wide. " + LIGHT +
                " Quiet room tone.")
MUSIC = ("Instrumental, no vocals. 104 BPM, D major. Cinematic and uplifting for a lively wellness launch film: a bright, "
         "rhythmic felt piano figure, pulsing staccato strings, light hand percussion and claps, a warm low pad, "
         "building to a joyful, open chorus. Warm, alive, hopeful, never busy.")


def crop(name, src, x, y, w):
    h = int(w * 0.6)
    dst = os.path.join(L.OUT, f"{name}_crop.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf",
                    f"crop={w}:{h}:{x}:{y},scale={L.W}:{L.H}:flags=lanczos", dst], check=True)
    st = L.load()
    wf = Workflow.load("edit_flux3_2image", L.WF)
    wf.set("image1", L.up(dst)); wf.set("image2", L.up(src))
    wf.set("prompt", REPHOTO.format(who=WHO[name]))
    wf.set("width", L.W); wf.set("height", L.H); wf.seed(8800)
    if st.get(name, {}).get("status") == "done" and os.environ.get("REDO"):
        st.pop(name)
    L.queue(st, name, wf)


def prep():
    st = L.load()
    wf = Workflow.load("still_flux3", L.WF)
    wf.set("prompt", SESSION); wf.set("negative", L.STILL_NEG + ", singing bowls, bowls, black bars, letterbox")
    wf.set("width", L.W); wf.set("height", L.H); wf.seed(6950)
    L.queue(st, "B4_session", wf)
    for t in range(2):
        wf = Workflow.load("song_minimax_m3", L.WF)
        wf.set("caption", MUSIC + L.ARR)
        wf.set("lyrics", "[Intro]\n[Instrumental]\n\n[Body]\n[Instrumental]\n\n[Outro]\n[Instrumental]")
        wf.set("max_seconds", 45); wf.seed(4450 + t); wf.try_set("tiled_decode", False)
        L.queue(st, f"B4_music_t{t}", wf)
    for name, (src, x, y, w) in CROPS.items():
        crop(name, src, x, y, w)


def video(st, name, first, prompt, frames, seed):
    wf = Workflow.load("vid_ltx", L.WF); wf.apply_defaults()
    f = L.up(first)
    wf.set("image", f); wf.set("last_image", f)
    wf.set("toggle_use_lf", False); wf.set("toggle_use_audio_in", False); wf.set("toggle_isolate_vocals", False)
    wf.set("audio", L.up(os.path.join(HERE, "dummy.mp3")))
    wf.set("prompt", prompt); wf.set("negative", NEG)
    wf.set("width", L.W); wf.set("height", L.H); wf.set("fps", 24.0); wf.set("frames", frames)
    wf.seed(seed)
    L.queue(st, name, wf)


def videos():
    st = L.load(); L.refresh(st)
    for name, prompt in CU.items():
        img = L.done(st, name)
        if not img:
            print("waiting on", name); continue
        for t in range(2):
            video(st, f"B4_{name}_t{t}", img, prompt, 97, 5800 + 31 * t)      # 4 s: 1 s head + 3 s
    ses = L.done(st, "B4_session")
    if ses:
        for t in range(2):
            video(st, f"B4_session_wide_t{t}", ses, SESSION_WIDE, 145, 5900 + 31 * t)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "crop":
        st = L.load(); L.refresh(st)
        src = L.done(st, "B4_session") if a[1] == "C_session" else CROPS[a[1]][0]
        crop(a[1], src, int(a[2]), int(a[3]), int(a[4]))
    else:
        {"prep": prep, "videos": videos}[a[0]]()
