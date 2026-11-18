"""Test hexe's Nov 17 all-in-one graphs on the GPU: vid_ltx (video) and img_flux3 (images).
    python3 scripts/wf_test.py queue|fetch
Jobs go through Workflow.resolved(), as Nightshift queues them (switches resolved, unused loaders dropped). Inputs come from
the wellness proof of concept (_promo_poc/out) and the gpu-a test project (a 9:16 singer + song)."""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from nightshift.comfy import Comfy
from nightshift.workflows import Workflow

c = Comfy(os.environ.get("COMFY_URL", "http://10.0.1.171:8188"))
OUT = os.path.join(ROOT, "_promo_poc", "wf_test")
ST = os.path.join(OUT, "state.json")
P, G = os.path.join(ROOT, "_promo_poc", "out"), os.path.join(ROOT, "runs", "gpu-a")
WF = [os.path.join(ROOT, "workflows")]
H, V = (1280, 768), (768, 1280)
NEG = "scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, birds"
SALT = ("A wellness center. A Himalayan salt cave relaxation room, amber and rose salt brick walls lit from behind. "
        "People rest on cushioned loungers under cream blankets, breathing slowly. Slow smooth dolly forward between the "
        "loungers. Warm low glow from the walls. The scene holds steady as haze drifts, photoreal cinematic. "
        "Quiet room tone, soft breathing, a low warm hum.")
SING = ("A night city street. A woman sings with feeling to the camera, the lyrics clear on her lips, body swaying with "
        "the beat. Medium shot, the camera arcs slowly around her. Neon and street light. Photoreal cinematic.")
VIDEO = [  # name, size, first, last (None = first frame only), audio (start, secs) or None, prompt, secs
    ("v_ff_h", H, f"{P}/cave_h_v0.png", None, None, SALT, 5),
    ("v_ff_v", V, f"{P}/cave_v_v0.png", None, None, SALT, 5),
    ("v_locked_h", H, f"{P}/yoga_h_v0.png", f"{P}/yoga_h_v0.png", None,
     "A wellness center. A sunlit yoga studio, oak floors, tall windows onto green trees. A small class holds warrior two "
     "pose and breathes in unison, an instructor smiles at the front. Static locked-off camera, wide shot. Morning "
     "sunlight through the windows. The scene holds steady, photoreal cinematic. Soft breathing, quiet room tone.", 5),
    ("v_lipsync_v", V, f"{G}/stills/s04_edit_00001_.png", None, (6.22, 6), SING, 6),
]
YOGA = ("A sunlit yoga studio with oak floors and tall windows onto green trees. A woman in a sage green top holds warrior "
        "two pose at the front of a small class. Morning light, shot on 35mm film, natural colors.")
IMAGES = [  # name, size, refs, prompt, enhancer, cfg
    ("i_t2i_off", H, [], YOGA, False, 3.5),
    ("i_t2i_on", H, [], YOGA, True, 3.5),
    ("i_t2i_v", V, [], YOGA, False, 3.5),
    ("i_edit1_cfg35", H, [f"{P}/yoga_h_v0.png"],
     "<ref_image_0> at dusk: the windows show a deep blue evening sky and warm paper lamps glow along the walls. "
     "Everything else exactly as in <ref_image_0>.", False, 3.5),
    ("i_edit1_cfg1", H, [f"{P}/yoga_h_v0.png"],
     "<ref_image_0> at dusk: the windows show a deep blue evening sky and warm paper lamps glow along the walls. "
     "Everything else exactly as in <ref_image_0>.", False, 1.0),
    ("i_edit2_off", H, [f"{P}/connect_h_v0.png", f"{G}/stills/s04_edit_00001_.png"],
     "The tea lounge from <ref_image_0>. The woman from <ref_image_1> sits at the low table with the friends, holding a "
     "cup of tea and laughing. Same light and colors as <ref_image_0>.", False, 3.5),
    ("i_edit2_on", H, [f"{P}/connect_h_v0.png", f"{G}/stills/s04_edit_00001_.png"],
     "The tea lounge from <ref_image_0>. The woman from <ref_image_1> sits at the low table with the friends, holding a "
     "cup of tea and laughing. Same light and colors as <ref_image_0>.", True, 3.5),
    # which file is which: the templates call the distilled file flux3-image-klein-int8-convrot (15-16 steps, cfg 1)
    # and the base flux3-image-klein-base-int8-convrot; the Comfy blog's underscore names say the opposite
    ("i_t2i_15cfg1", H, [], YOGA, False, {"steps": 15, "cfg": 1.0, "sampler": "er_sde"}),
    ("i_t2i_old_file", H, [], YOGA, False, {"unet": "flux3_image_klein_int8_convrot.safetensors"}),
    ("i_t2i_old_15cfg1", H, [], YOGA, False, {"unet": "flux3_image_klein_int8_convrot.safetensors", "steps": 15, "cfg": 1.0,
                                             "sampler": "er_sde"}),
    ("i_edit1_16cfg1", H, [f"{P}/yoga_h_v0.png"],
     "<ref_image_0> at dusk: the windows show a deep blue evening sky and warm paper lamps glow along the walls. "
     "Everything else exactly as in <ref_image_0>.", False, {"steps": 16, "cfg": 1.0}),
    ("i_t2i_on_t2isys", H, [], YOGA, True, {"t2i_system": True}),
    ("i_edit4", H, [f"{P}/cave_h_v0.png", f"{P}/yoga_h_v0.png", f"{P}/connect_h_v0.png", f"{G}/stills/s04_edit_00001_.png"],
     "A calm wellness center lobby. Through an arch at left, the salt cave room from <ref_image_0>; through an arch at "
     "right, the yoga studio from <ref_image_1>. In front, the low tea table and cushions from <ref_image_2>. The woman "
     "from <ref_image_3> stands in the middle, smiling. Warm, soft light.", False, 3.5),
]


def cut(start, secs, name):
    dst = os.path.join(OUT, name + ".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(start), "-t", f"{secs + 0.05:.3f}", "-i",
                    f"{G}/song/song.mp3", "-ac", "2", "-ar", "48000", dst], check=True)
    return dst


def queue(only=None):
    os.makedirs(OUT, exist_ok=True)
    st = json.load(open(ST)) if os.path.exists(ST) else {}
    for name, (w, h), first, last, audio, prompt, secs in VIDEO:
        if only and name not in only.split(","):
            continue
        wf = Workflow.load("vid_ltx", WF); wf.apply_defaults()
        wf.set("image", c.upload(first, "wf_test"))
        wf.set("toggle_use_lf", bool(last))
        if last:
            wf.set("last_image", c.upload(last, "wf_test"))
        wf.set("toggle_use_audio_in", bool(audio)); wf.set("toggle_isolate_vocals", bool(audio))
        if audio:
            wf.set("audio", c.upload(cut(audio[0], audio[1], name), "wf_test"))
        wf.set("prompt", prompt); wf.set("negative", NEG)
        wf.set("width", w); wf.set("height", h); wf.set("fps", 24.0); wf.set("frames", secs * 24 + 1)
        wf.seed(4440); wf.output(f"wf_test/{name}")
        st[name] = c.queue_prompt(wf.to_api()); print("queued", name)
    for name, (w, h), refs, prompt, enh, cfg in IMAGES:
        if only and name not in only.split(","):
            continue
        wf = Workflow.load("img_flux3", WF); wf.apply_defaults()
        wf.set("text_to_image", not refs); wf.set("prompt_enhancer", enh)
        for i, r in enumerate(refs):
            wf.set(f"image{i + 1}", c.upload(r, "wf_test"))
        wf.use_refs(len(refs))
        o = cfg if isinstance(cfg, dict) else {"cfg": cfg}
        wf.set("prompt", prompt); wf.set("width", w); wf.set("height", h); wf.set("cfg", o.get("cfg", 3.5))
        if o.get("steps"):
            wf.set("steps", o["steps"])
        if o.get("sampler"):
            for n in ("7", "5786"):
                wf.graph[n]["inputs"]["sampler_name"] = o["sampler"]
        if o.get("unet"):
            wf.graph["1"]["inputs"]["unet_name"] = o["unet"]
        if o.get("t2i_system"):   # the official text-to-image upsampler instructions instead of the edit ones
            wf.graph["5807"]["inputs"]["value"] = open(os.path.join(ROOT, "workflows", "flux3_t2i_upsampler_system.txt"),
                                                       encoding="utf-8").read()
        wf.seed(4440); wf.output(f"wf_test/{name}")
        st[name] = c.queue_prompt(wf.to_api()); print("queued", name)
    json.dump(st, open(ST, "w"), indent=1)


def fetch():
    for name, pid in json.load(open(ST)).items():
        r = c.result(pid)
        line = f"{name:16} {r['status']:8} {r.get('seconds') or ''}"
        if r["status"] == "success":
            f = [x for x in r["files"] if x["filename"].endswith((".mp4", ".png"))][0]
            dst = os.path.join(OUT, name + os.path.splitext(f["filename"])[1])
            if not os.path.exists(dst):
                c.download(f, dst)
            line += "  " + subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                           "stream=width,height,nb_frames", "-of", "csv=p=0", dst],
                                          capture_output=True, text=True).stdout.strip()
            txt = r.get("texts") or []
            if txt:
                line += "  rewritten: " + str(txt[0])[:120]
        elif r.get("error"):
            line += "  " + str(r["error"])[:300]
        print(line)


if __name__ == "__main__":
    {"queue": lambda: queue(sys.argv[2] if len(sys.argv) > 2 else None), "fetch": fetch}[sys.argv[1]]()
