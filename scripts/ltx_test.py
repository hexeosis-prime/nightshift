"""Test hexe's single LTX workflow (vid_ltx) in every mode, both aspects.  python3 scripts/ltx_test.py queue|fetch
Inputs come from the wellness proof of concept (_promo_poc/out) and the gpu-a test project (a 9:16 singer + song)."""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from nightshift.comfy import Comfy
from nightshift.workflows import Workflow

c = Comfy(os.environ.get("COMFY_URL", "http://10.0.1.171:8188"))
OUT = os.path.join(ROOT, "_promo_poc", "ltx_test")
ST = os.path.join(OUT, "state.json")
P, G = os.path.join(ROOT, "_promo_poc", "out"), os.path.join(ROOT, "runs", "gpu-a")
H, V = (1280, 768), (768, 1280)
NEG = "scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, birds"
SALT = ("A wellness center. A Himalayan salt cave relaxation room, amber and rose salt brick walls lit from behind. "
        "People rest on cushioned loungers under cream blankets, breathing slowly. Slow smooth dolly forward between the "
        "loungers. Warm low glow from the walls. The scene holds steady as haze drifts, photoreal cinematic. "
        "Quiet room tone, soft breathing, a low warm hum.")
TESTS = [
    # name, size, first, last, use_lf, audio (file, start, secs) or None, isolate, prompt, secs
    ("ff_gen_h", H, f"{P}/cave_h_v0.png", None, False, None, False, SALT, 5),
    ("ff_gen_v", V, f"{P}/cave_v_v0.png", None, False, None, False, SALT, 5),
    ("locked_h", H, f"{P}/yoga_h_v0.png", f"{P}/yoga_h_v0.png", True, None, False,
     "A wellness center. A sunlit yoga studio, oak floors, tall windows onto green trees. A small class holds warrior two "
     "pose and breathes in unison, an instructor smiles at the front. Static locked-off camera, wide shot. Morning "
     "sunlight through the windows. The scene holds steady, photoreal cinematic. Soft breathing, quiet room tone.", 5),
    ("chain_h", H, f"{P}/phone_in_h.png", f"{P}/cave_h_v0.png", True, None, False,
     "A cozy living room, then a Himalayan salt cave relaxation room. A hand holds a smartphone showing the salt cave. "
     "The camera pushes slowly forward into the phone screen until the salt cave fills the frame and becomes the real "
     "room. One continuous magical push-in, no cut. Warm light. Photoreal cinematic. Soft ambient swell.", 5),
    ("dance_v", V, f"{P}/connect_v_v0.png", None, False, (f"{G}/song/song.mp3", 6.22, 5), False,
     "A wellness center tea lounge in the late afternoon. Friends sit on floor cushions around a low wooden table. They "
     "laugh and sway to the music, one taps the rhythm on the table. Slow orbiting camera, medium shot. Warm golden "
     "window light. Lively and natural, photoreal cinematic.", 5),
    ("lipsync_v", V, f"{G}/stills/s04_edit_00001_.png", None, False, (f"{G}/song/song.mp3", 6.22, 6), True,
     "A night city street. A woman sings with feeling to the camera, the lyrics clear on her lips, body swaying with the "
     "beat. Medium shot, the camera arcs slowly around her. Neon and street light. Photoreal cinematic.", 6),
    ("lipsync_locked_v", V, f"{G}/stills/s04_edit_00001_.png", f"{G}/stills/s04_edit_00001_.png", True,
     (f"{G}/song/song.mp3", 6.22, 6), True,
     "A night city street. A woman sings with feeling to the camera, the lyrics clear on her lips. Medium shot, static "
     "locked-off camera. Neon and street light. Photoreal cinematic.", 6),
]


def cut(src, start, secs, name):
    dst = os.path.join(OUT, name + ".mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-t", str(secs + 0.5), "-i", src, dst], check=True)
    return dst


def queue():
    os.makedirs(OUT, exist_ok=True)
    st = {}
    for name, (w, h), first, last, use_lf, audio, iso, prompt, secs in TESTS:
        wf = Workflow.load("vid_ltx", [os.path.join(ROOT, "workflows")])
        wf.apply_defaults()
        f = c.upload(first, "ltx_test")
        wf.set("image", f)
        wf.set("last_image", c.upload(last, "ltx_test") if last else f)
        wf.set("toggle_use_lf", use_lf)
        wf.set("toggle_use_audio_in", bool(audio))
        wf.set("toggle_isolate_vocals", iso)
        if audio:
            wf.set("audio", c.upload(cut(audio[0], audio[1], audio[2], name), "ltx_test"))
            wf.set("audio_start", 0.0)
        else:   # the loader still needs a real file
            wf.set("audio", c.upload(cut(f"{G}/song/song.mp3", 0, secs, "dummy"), "ltx_test"))
        wf.set("prompt", prompt); wf.set("negative", NEG)
        wf.set("width", w); wf.set("height", h); wf.set("fps", 24.0); wf.set("frames", secs * 24 + 1)
        wf.seed(4440)
        wf.output(f"ltx_test/{name}")
        st[name] = c.queue_prompt(wf.to_api()); print("queued", name)
    json.dump(st, open(ST, "w"))


def fetch():
    for name, pid in json.load(open(ST)).items():
        r = c.result(pid)
        line = f"{name:18} {r['status']:8} {r.get('seconds') or ''}"
        if r["status"] == "success":
            f = [x for x in r["files"] if x["filename"].endswith(".mp4")][0]
            dst = os.path.join(OUT, name + ".mp4")
            if not os.path.exists(dst):
                c.download(f, dst)
            line += "  " + subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                           "stream=width,height,nb_frames", "-of", "csv=p=0", dst],
                                          capture_output=True, text=True).stdout.strip()
        elif r.get("error"):
            line += "  " + str(r["error"])[:300]
        print(line)


{"queue": queue, "fetch": fetch}[sys.argv[1]]()
