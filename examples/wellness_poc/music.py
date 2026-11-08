"""Queue instrumental ambient tracks for the demo (MiniMax Music 3), then fetch them.  python3 music.py queue|fetch"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from nightshift.comfy import Comfy
from nightshift import workflows as W
c = Comfy(os.environ.get("COMFY_URL", "http://10.0.1.171:8188"))
ST = os.path.join(HERE, "demo", "music.json")
BASE = ("Instrumental, no vocals, no drums, no percussion. 60 BPM, D major, free-floating. Spacious night-sky ambient in the "
        "tradition of late-night space music radio: deep slowly evolving analog synth pads, a soft low drone, long reverb tails, "
        "starlight shimmer, a calm and weightless meditative mood. ")
T = {
 "space_pads": BASE + "Gentle crystal singing bowl tones ring out now and then, a slow rising warmth, no melody hooks.",
 "space_piano": BASE + "Sparse soft felt piano notes float over the pads, each note left to decay, tender and hopeful.",
 "space_strings": BASE + "Slow airy string swells and a faint harp shimmer drift in and out, elegant and serene.",
}
ARR = ("\n\nArrangement: 0:00-0:06 Intro: the pad fades in from silence. 0:06-0:34 Body: textures slowly bloom and breathe, no "
       "sudden changes. 0:34-0:45 Outro: everything rings out in a long natural decay. No hard ending.")
def queue():
    st = {}
    for i, (n, cap) in enumerate(T.items()):
        wf = W.Workflow.load("song_minimax_m3", [os.path.join(HERE, "..", "workflows")])
        wf.set("caption", cap + ARR); wf.set("lyrics", "[Intro]\n[Instrumental]\n\n[Body]\n[Instrumental]\n\n[Outro]\n[Instrumental]")
        wf.set("max_seconds", 45); wf.seed(4440 + i); wf.try_set("tiled_decode", False)
        wf.output(f"promo_poc/music_{n}")
        st[n] = c.queue_prompt(wf.to_api()); print("queued", n)
    json.dump(st, open(ST, "w"))
def fetch():
    for n, pid in json.load(open(ST)).items():
        r = c.result(pid); print(n, r["status"], r.get("seconds"), r.get("error"))
        if r["status"] == "success":
            f = [x for x in r["files"] if x["filename"].endswith((".mp3", ".flac", ".wav"))][0]
            c.download(f, os.path.join(HERE, "demo", f"music_{n}" + os.path.splitext(f["filename"])[1]))
{"queue": queue, "fetch": fetch}[sys.argv[1]]()
