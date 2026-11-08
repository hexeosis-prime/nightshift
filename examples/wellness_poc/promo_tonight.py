"""Wellness center in your pocket: a generic proof of concept, queued into ComfyUI with GPU rest breaks.

  python promo_tonight.py night     run all night: feeds ComfyUI one job at a time, rests the GPU every few hours
  python promo_tonight.py status    what is done / waiting / failed

Every job is in plan() below, in priority order. A job waits until the files it needs exist.
Extra shots: add them to extra_shots.json next to this file at any time (the loop re-reads it every cycle):
  [{"name": "drone_open", "mode": "t2v", "aspect": "9:16", "secs": 8, "takes": 2, "prompt": "..."},
   {"name": "cave_orbit", "mode": "ff", "image": "cave_h_v0", "secs": 5, "prompt": "..."}]
"""
import json, os, struct, sys, time, wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))          # the nightshift folder
from nightshift.comfy import Comfy                       # noqa: E402
from nightshift import workflows as W                    # noqa: E402

URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
WF_DIRS = [os.path.join(HERE, "..", "workflows")]
STATE, EXTRA, LOG = (os.path.join(HERE, n) for n in ("state.json", "extra_shots.json", "night.log"))
OUT = os.path.join(HERE, "out")
FPS = 24
SIZES = {"h": (1280, 768), "v": (768, 1280)}
WORK_BEFORE_REST = 2 * 3600       # seconds of rendering, then
REST = 20 * 60                    # a rest with the GPU idle

LOOK = ("Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, "
        "shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed "
        "genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.")
STILL_NEG = "text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin"
VID_NEG = "scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera"

LOC = {
    "cave": {
        "still": "Inside a Himalayan salt cave relaxation room at a modern wellness center. The walls and arched ceiling are "
                 "built from glowing amber and rose salt bricks lit from behind, the floor is a bed of fine white salt "
                 "crystals. People recline on cushioned zero-gravity loungers wrapped in soft cream blankets, eyes closed, "
                 "peaceful. Warm low glow, a faint haze in the air.",
        "move": "Slow smooth dolly forward through the glowing salt cave between the loungers. The people breathe slowly and "
                "rest, one woman pulls her blanket a little higher and smiles with her eyes closed. Warm light flickers softly "
                "across the salt walls. Calm, steady camera.",
        "t2v": "A slow cinematic glide through a glowing Himalayan salt cave relaxation room, amber and rose salt brick walls "
               "lit from behind, a floor of white salt crystals, people resting under cream blankets on loungers, warm haze "
               "drifting in the light. Photoreal, warm, peaceful, smooth steady camera.",
    },
    "yoga": {
        "still": "A bright sunlit yoga studio with warm oak floors and tall floor-to-ceiling windows that look out onto lush "
                 "green trees. A small class of adults on natural-color mats hold warrior two pose, an instructor in front "
                 "guides them with a warm smile. Hanging plants, golden morning sunbeams across the room.",
        "move": "Slow lateral tracking shot along the row of people as they flow together out of warrior pose and raise their "
                "arms overhead, breathing in unison. The instructor smiles and nods. Sunbeams shift gently across the floor. "
                "Smooth, steady camera.",
        "t2v": "Morning in a sunlit yoga studio with oak floors and tall windows onto green trees. A small class flows slowly "
               "from warrior pose into a deep stretch together, golden sunbeams and dust motes in the air, an instructor "
               "smiling at the front. Photoreal, warm, smooth slow tracking camera.",
    },
    "session": {
        "still": "A calm sound healing session in a softly lit treatment room with linen curtains and candles. A practitioner "
                 "with kind eyes kneels beside a woman lying on a cushioned mat under a light blanket, and plays a large "
                 "frosted crystal singing bowl with a mallet. More bowls of different sizes sit around them, dried flowers, "
                 "warm candlelight.",
        "move": "Slow gentle push in toward the practitioner as she circles the mallet around the rim of the crystal bowl. "
                "The woman on the mat breathes deeply and her face softens. Candle flames flicker. Calm, steady camera.",
    },
    "connect": {
        "still": "A warm tea lounge at a wellness center in the late afternoon. Friends sit on floor cushions around a low "
                 "wooden table with clay teacups and a teapot, laughing together mid-conversation. Big windows with greenery "
                 "behind them, woven textures, plants, warm golden light.",
        "move": "Slow orbiting camera around the low table as the friends laugh and talk, one pours tea for another, someone "
                "leans in and touches a friend's shoulder. Lively, warm, natural moment. Smooth, steady camera.",
    },
    "retreat": {
        "still": "An open-air wooden pavilion retreat surrounded by lush tropical greenery, ferns and tall palms, soft morning "
                 "mist drifting through the jungle. A small group of people walk along a wooden boardwalk toward the "
                 "pavilion carrying rolled yoga mats, chatting and smiling. Golden hour light through the leaves.",
        "move": "Slow rising crane shot as the group walks along the boardwalk toward the pavilion, mist drifting through the "
                "trees, leaves moving in a light breeze, birds crossing the light. Smooth, steady camera.",
        "t2v": "A slow aerial drone shot gliding over a lush tropical jungle at golden hour, morning mist between tall palms, "
               "revealing an open-air wooden yoga pavilion and boardwalks where small groups of people walk with rolled mats. "
               "Photoreal, warm, serene, smooth steady drone movement.",
    },
}
EXTRA_T2V = {
    "arrival": "A slow aerial drone shot at sunrise over a serene wellness retreat nestled in green hills: low wooden buildings "
               "with planted roofs, a reflecting pool, gardens and winding stone paths, a few people walking. Soft golden mist, "
               "warm light. Photoreal, smooth steady drone push forward.",
}

PHONE = {   # a photo with a plain lit screen, then an edit puts a location still on the screen
    "phone_in": {"src": "cave",
                 "base": "A close-up photograph of a woman's hand holding a modern black smartphone in a bright, cozy living "
                         "room with plants, a sofa softly out of focus behind. The phone faces straight on to the camera, "
                         "centered, filling the middle of the frame, its screen lit plain soft white. " + LOOK,
                 "move": "The camera pushes slowly forward toward the phone screen and passes through it, the glowing salt cave "
                         "on the screen grows until it fills the whole frame and becomes the real salt cave room. Smooth, "
                         "continuous, magical push-in, no cut."},
    "phone_out": {"src": "retreat",
                  "base": "A medium photograph of a smiling woman sitting on a sofa in a bright, cozy living room, holding a "
                          "modern black smartphone up toward the camera in the center of the frame, its screen lit plain soft "
                          "white. Window light, plants. " + LOOK,
                  "move": "The camera pulls slowly back out of the jungle retreat, the scene shrinks into the glowing screen of a "
                          "smartphone held by a smiling woman in a cozy living room. Smooth, continuous, magical pull-back "
                          "reveal, no cut."},
}
SCREEN_EDIT = ("Keep <ref_image_0> exactly: the same person, hand, phone, room and light. Replace only the phone's screen content "
               "with the picture from <ref_image_1>, fitted edge to edge inside the screen, bright and sharp. No text, no app "
               "icons, no status bar.")


# ---- the plan: (name, kind, needs, builder) in priority order -------------------------------------------------------
def plan():
    jobs = []
    for loc, d in LOC.items():                                   # stills: 2 horizontal + 2 vertical per place
        for a in "hv":
            for t in range(2):
                jobs.append((f"{loc}_{a}_v{t}", "still", [], dict(prompt=d["still"] + " " + LOOK, aspect=a, seed=4440 + 101 * t + len(loc))))
    for name, d in PHONE.items():
        for a in "hv":
            jobs.append((f"{name}_{a}_base", "still", [], dict(prompt=d["base"], aspect=a, seed=5550, neg=", text on screen, app icons")))
    for name, d in PHONE.items():                                # screen composites
        for a in "hv":
            jobs.append((f"{name}_{a}", "edit", [f"{name}_{a}_base", f"{d['src']}_{a}_v0"], dict(prompt=SCREEN_EDIT, aspect=a, seed=7770)))
    for name, d in PHONE.items():                                # through-the-screen transitions
        for a in "hv":
            first, last = (f"{name}_{a}", f"{d['src']}_{a}_v0") if name == "phone_in" else (f"{d['src']}_{a}_v0", f"{name}_{a}")
            for t in range(2):
                jobs.append((f"{name}_{a}_fflf_v{t}", "fflf", [first, last], dict(prompt=d["move"], aspect=a, secs=5, seed=9300 + t)))
    for t in range(2):                                           # image to video from every still
        for loc, d in LOC.items():
            for a in "hv":
                src = f"{loc}_{a}_v{t}"
                jobs.append((f"{src}_ff", "ff", [src], dict(prompt=d["move"], aspect=a, secs=5, seed=9100 + t)))
    t2v = {k: d["t2v"] for k, d in LOC.items() if "t2v" in d} | EXTRA_T2V    # text to video
    for k, p in t2v.items():
        for a in "hv":
            jobs.append((f"{k}_{a}_t2v", "t2v", [], dict(prompt=p, aspect=a, secs=6, seed=9500)))
    for e in _extras():                                          # shared later in extra_shots.json
        a = {"16:9": "h", "9:16": "v", "h": "h", "v": "v"}.get(e.get("aspect", "16:9"), "h")
        mode, secs = e.get("mode", "t2v"), e.get("secs", 6)
        for t in range(int(e.get("takes", 1))):
            n = f"x_{e['name']}_{a}" + (f"_v{t}" if mode != "still" else "")
            ref = lambda k: e[k].replace("{a}", a)          # "x_drone_wide_{a}" -> the same-aspect still
            if mode == "still":
                jobs.append((n, "still", [], dict(prompt=e["prompt"] + " " + LOOK * e.get("look", True), aspect=a, seed=e.get("seed", 6660))))
                break
            if mode == "ff":
                jobs.append((n, "ff", [ref("image")], dict(prompt=e["prompt"], aspect=a, secs=secs, seed=9700 + t)))
            elif mode == "fflf":
                jobs.append((n, "fflf", [ref("first"), ref("last")], dict(prompt=e["prompt"], aspect=a, secs=secs, seed=9700 + t,
                                                                          first_strength=e.get("first_strength"), last_strength=e.get("last_strength"))))
            else:
                jobs.append((n, "t2v", [], dict(prompt=e["prompt"], aspect=a, secs=secs, seed=9700 + t)))
    return jobs


def _extras():
    try:
        return json.load(open(EXTRA, encoding="utf-8")) if os.path.exists(EXTRA) else []
    except Exception as e:
        log(f"extra_shots.json unreadable: {e}")
        return []


# ---- workflow builders ----------------------------------------------------------------------------------------
def frames(secs):
    return int(secs) * FPS + 1          # 8n+1 at 24 fps


def build(c, kind, needs, o, st):
    w, h = SIZES[o["aspect"]]
    files = [c.upload(st["jobs"][n]["file"], "promo_poc") for n in needs]
    if kind == "still":
        wf = W.Workflow.load("still_flux3", WF_DIRS)
        wf.set("negative", STILL_NEG + o.get("neg", ""))
    elif kind == "edit":
        wf = W.Workflow.load("edit_flux3_2image", WF_DIRS)
        wf.set("image1", files[0]); wf.set("image2", files[1])
    elif kind == "ff":
        wf = W.Workflow.load("vid_ltx_ff", WF_DIRS); wf.apply_defaults()
        wf.set("image", files[0]); wf.set("negative", VID_NEG); wf.set("frames", frames(o["secs"]))
    elif kind == "t2v":
        wf = W.Workflow.load("vid_ltx_t2v", WF_DIRS); wf.apply_defaults()
        wf.set("negative", VID_NEG); wf.set("frames", frames(o["secs"]))
    elif kind == "fflf":
        wf = W.Workflow.load("vid_ltx_fflf", WF_DIRS); wf.apply_defaults()
        wf.set("image", files[0]); wf.set("last_image", files[1]); wf.set("seconds", o["secs"])
        wf.set("audio", c.upload(silence(o["secs"]), "promo_poc"))
        wf.try_set("audio_start", 0); wf.try_set("audio_end", o["secs"]); wf.try_set("audio_seconds", o["secs"])
        wf.try_set("negative", VID_NEG)
        for k in ("first_strength", "last_strength"):
            if o.get(k) is not None:
                wf.set(k, float(o[k]))
    wf.set("prompt", o["prompt"])
    wf.set("width", w); wf.set("height", h)
    wf.seed(o["seed"])
    return wf


def silence(secs):
    p = os.path.join(HERE, f"silence_{secs}s.wav")
    if not os.path.exists(p):
        with wave.open(p, "wb") as f:
            f.setnchannels(2); f.setsampwidth(2); f.setframerate(44100)
            f.writeframes(struct.pack("<hh", 0, 0) * 44100 * (secs + 1))
    return p


# ---- state + loop -----------------------------------------------------------------------------------------------
def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load():
    return json.load(open(STATE)) if os.path.exists(STATE) else {"jobs": {}, "worked": 0}


def save(st):
    json.dump(st, open(STATE + ".tmp", "w"), indent=1)
    os.replace(STATE + ".tmp", STATE)


def refresh(c, st):
    """Returns the seconds of rendering that finished since the last call."""
    worked = 0
    for name, j in st["jobs"].items():
        if j["status"] != "queued":
            continue
        r = c.result(j["id"])
        if r["status"] == "success":
            f = r["files"][0]
            dst = os.path.join(OUT, name + os.path.splitext(f["filename"])[1])
            c.download(f, dst)
            j.update(status="done", file=dst, seconds=r.get("seconds"))
            worked += r.get("seconds") or 0
            log(f"done  {name}  {r.get('seconds')}s")
        elif r["status"] == "error":
            j.update(status="error", error=r.get("error"), tries=j.get("tries", 0) + 1)
            log(f"FAIL  {name}  {r.get('error')}")
        elif r["status"] == "unknown":
            j.update(status="error", error="lost (ComfyUI restarted?)", tries=j.get("tries", 0) + 1)
    save(st)
    return worked


def next_job(st):
    for name, kind, needs, o in plan():
        j = st["jobs"].get(name)
        if j and (j["status"] in ("done", "queued") or j.get("tries", 0) >= 2):
            continue
        if all(st["jobs"].get(n, {}).get("status") == "done" for n in needs):
            return name, kind, needs, o
    return None


def blocked(st):
    left = [n for n, *_ in plan() if st["jobs"].get(n, {}).get("status") != "done"
            and st["jobs"].get(n, {}).get("tries", 0) < 2]
    return left


def night():
    os.makedirs(OUT, exist_ok=True)
    c, st = Comfy(URL), load()
    log(f"night run starting, {len(plan())} jobs in the plan")
    idle_since = None
    while True:
        try:
            st["worked"] = st.get("worked", 0) + refresh(c, st)
            q = c.queue()
            if q["running"] or q["pending"]:
                time.sleep(15); continue
            if st["worked"] >= WORK_BEFORE_REST:
                log(f"GPU rest for {REST // 60} min after {st['worked'] / 3600:.1f} h of rendering")
                st["worked"] = 0; save(st)
                time.sleep(REST); continue
            job = next_job(st)
            if not job:
                if not blocked(st):
                    idle_since = idle_since or time.time()
                    if time.time() - idle_since > 3600:
                        log("all jobs done, nothing new in extra_shots.json for an hour: stopping"); break
                time.sleep(30); continue
            idle_since = None
            name, kind, needs, o = job
            wf = build(c, kind, needs, o, st)
            wf.output(f"promo_poc/{name}")
            st["jobs"][name] = {"id": c.queue_prompt(wf.to_api()), "kind": kind, "status": "queued",
                                "tries": st["jobs"].get(name, {}).get("tries", 0), "t": time.time()}
            save(st)
            log(f"queue {name}")
        except KeyboardInterrupt:
            log("stopped by hand"); break
        except Exception as e:
            log(f"loop error: {e!r}  (retrying in 60 s)")
            time.sleep(60)


def status():
    st, by = load(), {}
    for n, *_ in plan():
        j = st["jobs"].get(n, {"status": "waiting"})
        by.setdefault(j["status"], []).append(n + (f" ({j['seconds']}s)" if j.get("seconds") else ""))
    for k, v in by.items():
        print(f"{k} [{len(v)}]: " + ", ".join(v))
    for n, j in st["jobs"].items():
        if j["status"] == "error":
            print("ERR", n, j.get("error"))


if __name__ == "__main__":
    {"night": night, "status": status}[sys.argv[1] if len(sys.argv) > 1 else "status"]()
