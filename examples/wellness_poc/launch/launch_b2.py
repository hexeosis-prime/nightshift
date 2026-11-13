"""Launch B v3: redo the sound session, tea and jungle-walk shots and the pull-back with the review's rules
(labels not pronouns, every actor directed, small cast, simple common actions, stillness, 1 s head handles,
pull-back chained from the walk shot's last used frame, app card showing the same retreat).

  python3 launch_b2.py stills   new session + retreat stills (fewer bowls / 3 walkers, no letterbox)
  python3 launch_b2.py ui       app frame whose card shows the new retreat
  python3 launch_b2.py videos   session, tea, walk (2 takes, 6 s with a 1 s head)
  python3 launch_b2.py pull T   pull-back chained from walk take T (its frame at HEAD + WALK_USE seconds)
"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import launch_demo as L
from nightshift.workflows import Workflow

HEAD, WALK_USE = 1.0, 3.5
LIGHT = L.LIGHT["B"]
NEG = L.VID_NEG + ", walking backwards, people moving in reverse, objects moving by themselves, floating objects"

STILLS = {
    "B2_session": ("A softly lit sound healing room at dusk, linen curtains, a low wooden floor. A practitioner in a pale "
                   "linen tunic kneels upright beside a client who lies on a cushioned mat under a light blanket, eyes "
                   "closed. Three frosted crystal singing bowls sit on the floor beside the practitioner, one large bowl "
                   "in front of her. A few tea-light candles in small amber glass holders stand apart on a low shelf "
                   "behind them. " + L.FILMIC),
    "B2_retreat": ("Full frame image, no black bars, no letterbox. An open-air wooden yoga pavilion in lush tropical "
                   "greenery, ferns and tall palms, soft morning mist and golden light through the leaves. Three people "
                   "walk along a wooden boardwalk toward the pavilion, seen from behind and slightly to the side, each "
                   "carrying a rolled yoga mat: a woman in a white top at left, a man in a green shirt in the middle, a "
                   "woman in a grey top at right. " + L.FILMIC),
}
SHOTS = {
    "s4_session": ("B2_session",
        "A launch film for a wellness app. A softly lit sound healing room with linen curtains and three crystal "
        "singing bowls. The practitioner in the linen tunic kneels beside the client on the mat. The practitioner "
        "gently strikes the large crystal bowl once with a soft mallet, then rests both hands in her lap and closes "
        "her eyes while it rings. The client on the mat lies completely still, eyes closed, breathing slowly. Slow "
        "gentle push in, medium shot. " + LIGHT + " The scene holds still and calm. The deep ringing tone of a crystal "
        "singing bowl."),
    "s5_connect": ("x_connect_filmic_h",
        "A launch film for a wellness app. A warm tea lounge with floor cushions around a low wooden table, big windows "
        "onto greenery. Four friends sit around the table. The woman at left lifts the teapot and slowly pours tea "
        "into the cup of the woman beside her. The woman in the middle laughs softly. The woman at right holds her "
        "cup in both hands and smiles at her friends. Only the woman at left touches the teapot. Slow orbiting "
        "camera, medium shot. " + LIGHT + " Warm laughter and soft conversation."),
    "s6_walk": ("B2_retreat",
        "A launch film for a wellness app. A wooden boardwalk through lush tropical greenery leading to an open-air "
        "yoga pavilion, morning mist. The woman in the white top, the man in the green shirt and the woman in the grey "
        "top walk slowly forward along the boardwalk, away from the camera, toward the pavilion, at an easy, steady "
        "pace. Leaves move in a light breeze. Slow rising crane shot following them from behind, wide. " + LIGHT +
        " Soft breeze through leaves."),
}
PULL = ("A launch film for a wellness app. A jungle retreat boardwalk, then a dim living room at dusk. The three "
        "people on the boardwalk keep walking slowly away toward the pavilion. The camera pulls slowly back out of the "
        "retreat, and the whole scene shrinks into the glowing screen of a smartphone held in a hand in a dim, warm "
        "living room. One continuous, magical pull-back reveal, no cut. " + LIGHT + " Soft ambient swell.")


def path(name):
    if name.startswith("x_"):
        return os.path.join(L.POC, name + ".png")
    return L.done(L.load(), name)


def stills():
    st = L.load()
    for name, prompt in STILLS.items():
        wf = Workflow.load("still_flux3", L.WF)
        wf.set("prompt", prompt); wf.set("negative", L.STILL_NEG + ", black bars, letterbox, extra people")
        wf.set("width", L.W); wf.set("height", L.H); wf.seed(6900)
        L.queue(st, name, wf)


def ui():
    st = L.load(); L.refresh(st)
    ret = L.done(st, "B2_retreat")
    if not ret:
        print("waiting on B2_retreat"); return
    L.PLACES["B"]["retreat2"] = ret
    wf = Workflow.load("edit_flux3_2image", L.WF)
    wf.set("image1", L.up(L.done(st, "B_base_in"))); wf.set("image2", L.up(ret))
    wf.set("prompt", L.APP.format(who="hand", label="Jungle Retreat · Weekend",
                                  scene="a close-up of a hand holding a smartphone in a living room"))
    wf.set("width", L.W); wf.set("height", L.H); wf.seed(7702)
    L.queue(st, "B2_ui_out", wf)


def video(st, name, first, last, prompt, frames, seed):
    wf = Workflow.load("vid_ltx", L.WF); wf.apply_defaults()
    f = L.up(first)
    wf.set("image", f); wf.set("last_image", L.up(last) if last else f)
    wf.set("toggle_use_lf", bool(last)); wf.set("toggle_use_audio_in", False); wf.set("toggle_isolate_vocals", False)
    if last:
        wf.set("ff_strength", 0.9); wf.set("lf_strength", 0.9)
    wf.set("audio", L.up(os.path.join(HERE, "dummy.mp3")))
    wf.set("prompt", prompt); wf.set("negative", NEG)
    wf.set("width", L.W); wf.set("height", L.H); wf.set("fps", 24.0); wf.set("frames", frames)
    wf.seed(seed)
    L.queue(st, name, wf)


def videos():
    st = L.load(); L.refresh(st)
    for shot, (src, prompt) in SHOTS.items():
        first = path(src)
        if not first:
            print("waiting on", src); continue
        for t in range(2):
            video(st, f"B2_{shot}_t{t}", first, None, prompt, 145, 5550 + 31 * t)   # 6 s: 1 s head + 5 s


def pull(take):
    st = L.load(); L.refresh(st)
    walk, ui_out = L.done(st, f"B2_s6_walk_t{take}"), L.done(st, "B2_ui_out")
    if not (walk and ui_out):
        print("waiting on walk / ui"); return
    first = os.path.join(L.OUT, f"B2_walk_t{take}_last_used.png")   # the frame the edit leaves the walk on
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(HEAD + WALK_USE), "-i", walk, "-frames:v", "1",
                    first], check=True)
    for t in range(2):
        video(st, f"B2_s7_pull_out_t{t}", first, ui_out, PULL, 121, 5650 + 31 * t)


if __name__ == "__main__":
    a = sys.argv[1:]
    {"stills": stills, "ui": ui, "videos": videos}.get(a[0], lambda: pull(int(a[1])))()
