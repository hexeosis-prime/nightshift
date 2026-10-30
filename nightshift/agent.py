"""Agent mode: one idea in, a whole Nightshift project out.

    plan(idea, settings)          -> a plan (characters, worlds, song brief, lyrics, shot list) from any agent model
    create_from_plan(root, plan)  -> a normal project folder, ready for `nightshift run`

The agent model is anything that speaks the OpenAI chat-completions API: LM Studio or Ollama on this machine or another
one on your network, OpenRouter, a hosted open-weights model, or a closed one. Use an open-weights model and nothing in the
loop is closed. The model writes what a director and an assistant director would: the lyrics, the producer's brief for
MiniMax Music 3, who the characters are (identity words copied into every prompt), where the video happens, and every
shot with its framing, action, lens and camera move. Nightshift validates the plan, fixes what it can (anchors that don't
match a lyric line, unknown characters, missing fields) and refuses what it can't.

The API key is never written into the project.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request

from . import project as P
from . import studio

LENGTHS = {
    "short": {"seconds": 40, "shots": 9, "label": "30-40 s, about 9 shots, under an hour on a 3090"},
    "medium": {"seconds": 75, "shots": 16, "label": "60-75 s, about 16 shots, about 1.5 hours on a 3090"},
    "full": {"seconds": 150, "shots": 32, "label": "2-3 min, about 32 shots, overnight on a 3090"},
}
MODES = ("lipsync", "ff", "fflf", "t2v")

SYSTEM = """You are the director and assistant director of NIGHTSHIFT, a music-video pipeline that renders with open-weight
models in ComfyUI: MiniMax Music 3 writes and sings the song from your brief and lyrics, Flux paints a first frame for each
shot, an identity edit puts the cast's exact face and wardrobe into it, and LTX 2.3 animates it (lip-sync to the song,
camera moves). You turn the user's idea into the complete production plan. Reply with ONE JSON object and nothing else.

JSON shape:
{
 "title": "short title",
 "logline": "one sentence: what the video is",
 "characters": {                     // 1 or 2 people (keys: lowercase, e.g. "maya", "theo"). No real or famous people.
   "<key>": {
     "noun": "woman" | "man" | "person",
     "name": "display name",
     "person": "identity words: age as a number range, face shape, eyes, hair (colour, length, style), skin tone, build. 25-45 words. Concrete, no adjectives like beautiful.",
     "outfit": {"close": "top + accessories only", "medium": "top + bottoms", "wide": "full outfit including shoes"},
     "video_name": "how video prompts name them: 'the woman with short silver hair and a red bomber jacket'",
     "signature": "the one most recognisable feature",
     "never": "things that must not appear on them, comma separated",
     "voice": "female singer" | "male singer" | "female rapper" | "male rapper"
   }
 },
 "worlds": {                         // usually 1, at most 3 visual worlds; each shot names one
   "<key>": {"style": "photographic look in concrete words: film stock / lens look, light quality, time of day, colour",
             "daytime": true|false, "indoor": true|false}
 },
 "song": {
   "caption": "the producer's brief for MiniMax Music 3, in three paragraphs: (1) Genre in specific words (not 'pop'), BPM, key, mood arc, production texture. (2) Vocal details: who sings what, range, timbre, treatment; with two singers, start the caption with a casting note in capitals saying which singer sings which sections. (3) Arrangement with timestamps (0:00-0:12 Intro: ...) adding up to the target length, ending with a natural decay.",
   "lyrics": "the lyrics with section tags on their own lines: [Intro], [Verse 1 - Female Singer], [Chorus - Male Singer], [Bridge], [Outro]. Name the singer in the tag when there are two. Short singable lines, 4-8 words. Original words only."
 },
 "shots": [                          // in edit order
   {
     "mode": "lipsync" | "ff" | "fflf" | "t2v",
     "chars": ["<key>"],             // who is in the frame (first one drives the shot); [] for t2v and empty-place shots
     "world": "<world key>",
     "framing": "close" | "medium" | "wide",
     "anchor": "for lipsync shots: the FIRST 3-5 WORDS of the lyric line they start on, copied exactly from the lyrics",
     "location": "the place in concrete physical words: surfaces, light sources, weather. No readable text or signs.",
     "action": "what the person does in the still, ending with a lens: '..., 85mm lens'",
     "expr": "facial expression for the first frame ('lips gently closed, about to sing' for lip-sync shots)",
     "video": "the LTX motion prompt: one continuous moment in order: shot size and subject as {<key>}, where, what happens, then the camera move (dolly, push in, arc, crane up, handheld drift, static). 2-3 sentences."
   }
 ]
}

Rules that matter:
- Modes: "lipsync" = the character sings a lyric line to camera (needs chars and an anchor). "ff" = a person moves (walks,
  turns, dances) from a first frame. "fflf" = a camera move through an empty place (chars []). "t2v" = text-to-video
  establishing shot of an empty place (chars [], no location/action needed, the whole description goes in "video").
- Start with a t2v or fflf establishing shot and end on an fflf or ff shot. About half the shots are lipsync, spread over
  the song; anchors appear in lyric order and each anchors a different line where possible.
- With two characters, each one lip-syncs only the lines their voice sings; give each character shots of their own and a
  few shots with both (put both keys in chars; the first is the one singing).
- In "video" prompts refer to people only as {<key>} (e.g. {maya}); never retype their description.
- Locations: use every place the user named, in a sensible order; repeat a place across several shots so it reads as a
  scene. No readable text, signs, logos, microphones or instruments in hands.
- Everything lawful and safe for work. Invent original people; never describe a real or famous person.
"""


class PlanError(Exception):
    pass


def settings_path(root):
    return os.path.join(root, "studio_agent.json")


def load_settings(root):
    s = {"base_url": "http://127.0.0.1:1234/v1", "model": "", "api_key": "", "hook_url": "", "hook_token": ""}
    try:
        s.update(json.load(open(settings_path(root), encoding="utf-8")))
    except (OSError, ValueError):
        pass
    if os.environ.get("NIGHTSHIFT_AGENT_URL"):
        s["base_url"] = os.environ["NIGHTSHIFT_AGENT_URL"]
    if os.environ.get("NIGHTSHIFT_AGENT_MODEL"):
        s["model"] = os.environ["NIGHTSHIFT_AGENT_MODEL"]
    if os.environ.get("NIGHTSHIFT_AGENT_KEY"):
        s["api_key"] = os.environ["NIGHTSHIFT_AGENT_KEY"]
    return s


def save_settings(root, s):
    keep = {k: s.get(k, "") for k in ("base_url", "model", "api_key", "hook_url", "hook_token")}
    with open(settings_path(root), "w", encoding="utf-8") as f:
        json.dump(keep, f, indent=1)
    return keep


def chat(settings, messages, timeout=900, json_mode=True):
    url = settings["base_url"].rstrip("/") + "/chat/completions"
    body = {"model": settings.get("model") or "default", "messages": messages, "temperature": 0.7, "max_tokens": 16000}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    headers = {"Content-Type": "application/json"}
    if settings.get("api_key"):
        headers["Authorization"] = f"Bearer {settings['api_key']}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        if json_mode and e.code in (400, 422) and "response_format" in detail:
            return chat(settings, messages, timeout, json_mode=False)
        raise PlanError(f"agent model at {url} answered {e.code}: {detail}") from None
    except urllib.error.URLError as e:
        raise PlanError(f"agent model not reachable at {url} ({e.reason})") from None
    try:
        return out["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise PlanError(f"unexpected answer from {url}: {str(out)[:300]}") from None


def models(settings):
    url = settings["base_url"].rstrip("/") + "/models"
    headers = {"Authorization": f"Bearer {settings['api_key']}"} if settings.get("api_key") else {}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10) as r:
        return [m.get("id") for m in json.loads(r.read()).get("data", [])]


def _json_from(text):
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        raise PlanError("the agent did not answer with a JSON plan")
    try:
        return json.loads(text[a:b + 1])
    except ValueError as e:
        raise PlanError(f"the agent's JSON did not parse ({e})") from None


def plan(idea, settings, length="medium", on_event=print, tries=2):
    L = LENGTHS[length]
    user = (f"The idea:\n{idea.strip()}\n\nTarget: a music video of about {L['seconds']} seconds with about {L['shots']} shots. "
            f"Write the lyrics and arrangement for that length.")
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
    last = None
    for attempt in range(tries):
        t0 = time.time()
        on_event(f"asking the agent ({settings.get('model') or 'default model'}) for a plan" + (" again" if attempt else ""))
        text = chat(settings, messages)
        on_event(f"plan received in {time.time() - t0:.0f} s")
        try:
            raw = _json_from(text)
            return normalize(raw, length)
        except PlanError as e:
            last = e
            on_event(f"plan rejected: {e}")
            messages += [{"role": "assistant", "content": text[:20000]},
                         {"role": "user", "content": f"That plan can't be used: {e}. Reply with the corrected JSON object only."}]
    raise last


def _key(s):
    k = re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")
    return k[:20] or "lead"


def normalize(raw, length="medium"):
    """Check and repair a plan; raises PlanError for what can't be repaired."""
    from .lyrics import sheet_lines
    chars_in = raw.get("characters") or {}
    if isinstance(chars_in, list):
        chars_in = {c.get("key") or c.get("name") or f"c{i}": c for i, c in enumerate(chars_in)}
    if not chars_in:
        raise PlanError("no characters")
    chars, rename = {}, {}
    for k, c in list(chars_in.items())[:2]:
        nk = _key(k)
        rename[k] = nk
        noun = (c.get("noun") or "person").lower()
        noun = noun if noun in ("woman", "man", "person") else "person"
        outfit = c.get("outfit") or {}
        if isinstance(outfit, str):
            outfit = {"close": outfit.split(",")[0], "medium": outfit, "wide": outfit}
        pron = {"woman": ("she", "her"), "man": ("he", "his"), "person": ("they", "their")}[noun]
        chars[nk] = {
            "name": c.get("name") or nk.title(), "noun": noun, "pronoun": pron[0], "possessive": pron[1],
            "count": {"female": int(noun == "woman"), "male": int(noun == "man")},
            "person": (c.get("person") or f"{noun} in their late twenties").strip().rstrip(".") + ", clear healthy skin",
            "outfit": {f: (outfit.get(f) or outfit.get("medium") or "plain dark clothes").strip() for f in ("close", "medium", "wide")},
            "never": c.get("never") or "logos, readable text on clothing, heavy makeup, airbrushed plastic skin",
            "video_name": c.get("video_name") or f"the {noun} with {c.get('signature') or 'dark hair'}",
            "signature": c.get("signature") or "",
            "reference": None,
            "edit_extra": f"{pron[1].capitalize()} skin is clear and healthy.",
            "voice": {"verb": "sings", "gerund": "singing", "style": "warm, close, expressive singing"},
            "_voice": c.get("voice") or "",
        }
    worlds_in = raw.get("worlds") or {"real": {}}
    worlds, wrename = {}, {}
    for k, w in list(worlds_in.items())[:3]:
        nk = _key(k)
        wrename[k] = nk
        worlds[nk] = {"still_model": "flux", "style": w.get("style") or "cinematic 35mm film photograph",
                      "switches": {"daytime": bool(w.get("daytime")), "indoor": bool(w.get("indoor")), "pro_photo": True,
                                   "bad_photo": False, "atmosphere": True}}
    default_world = next(iter(worlds))
    song = raw.get("song") or {}
    lyrics = (song.get("lyrics") or "").strip()
    caption = (song.get("caption") or "").strip()
    lines = sheet_lines(lyrics)
    if len(lines) < 4:
        raise PlanError("the lyrics are missing or too short")
    if len(caption) < 80:
        raise PlanError("the song caption is missing or too short")
    norm = lambda t: re.sub(r"[^a-z0-9' ]", "", t.lower()).split()

    def match_anchor(a, used):
        aw = norm(a)
        if not aw:
            return None
        best, score = None, 0
        for i, l in enumerate(lines):
            lw = norm(l)
            n = 0
            for x, y in zip(aw, lw):
                if x != y:
                    break
                n += 1
            sc = n + (0.5 if i not in used else 0)
            if n >= min(2, len(aw)) and sc > score:
                best, score = i, sc
        if best is None:
            for i, l in enumerate(lines):
                if " ".join(aw[:3]) in " ".join(norm(l)):
                    return i
        return best

    shots, used, last_line = [], set(), -1
    for i, s in enumerate(raw.get("shots") or []):
        mode = s.get("mode") if s.get("mode") in MODES else "ff"
        cs = [rename.get(c, _key(c)) for c in (s.get("chars") or [])]
        cs = [c for c in cs if c in chars][:2]
        world = wrename.get(s.get("world"), _key(s.get("world") or default_world))
        world = world if world in worlds else default_world
        framing = s.get("framing") if s.get("framing") in ("close", "medium", "wide") else "medium"
        sid = f"s{len(shots) + 1:02d}"
        out = {"id": sid, "section": s.get("section") or "", "world": world, "mode": mode, "framing": framing,
               "seed": 1000 + len(shots) + 1}
        video = s.get("video") or ""
        for k, nk in rename.items():
            video = video.replace("{" + k + "}", "{" + nk + "}")
        if mode == "t2v" or (mode == "fflf" and not cs):
            out.update(chars=[], video=video or s.get("location") or "An empty place at dusk. Slow cinematic camera move.")
            if mode == "fflf":
                out.update(fit=True, action="", location=(s.get("location") or "an empty street at dusk") + ", completely empty")
        else:
            if not cs:
                cs = [next(iter(chars))]
            if mode == "lipsync":
                li = match_anchor(s.get("anchor") or "", used)
                if li is None or li <= last_line - 2:
                    mode = out["mode"] = "ff"
                else:
                    out["anchor"] = " ".join(lines[li].split()[:5])
                    used.add(li)
                    last_line = li
                    out["no_lyric"] = True
            if not re.search(r"\{[a-z0-9_]+\}", video):
                video = f"{framing.capitalize()} shot of {{{cs[0]}}}. " + video
            out.update(chars=cs[:1], still="edit", wording="C", expr=s.get("expr") or "natural",
                       action=s.get("action") or "standing still, looking into the distance, 50mm lens",
                       location=s.get("location") or "an empty street at night", video=video)
            if len(cs) > 1:
                out["add"] = {"char": cs[1], "where": "standing beside them, a little behind", "expr": "natural"}
        shots.append(out)
    if len(shots) < 3:
        raise PlanError("the shot list is missing or too short")
    if not any(s["mode"] == "lipsync" for s in shots):
        raise PlanError("no lip-sync shot has an anchor that matches a lyric line")
    return {"_validated": True, "title": raw.get("title") or "Untitled", "logline": raw.get("logline") or "", "length": length,
            "characters": chars, "worlds": worlds, "default_world": default_world,
            "song": {"caption": caption, "lyrics": lyrics}, "shots": shots}


def create_from_plan(root, plan, opts=None):
    """opts: aspect, image_model, mode, grade, overlay, comfy_url, comfy_dir, approve_looks"""
    o = dict(opts or {})
    L = LENGTHS[plan.get("length") or "medium"]
    p = P.init(root, o.get("name") or os.path.basename(root), o.get("comfy_url"), o.get("comfy_dir"),
               mode=o.get("mode") or "yolo", skip=("refs/README.md", "README.md"))
    chars = {k: {kk: vv for kk, vv in c.items() if not kk.startswith("_")} for k, c in plan["characters"].items()}
    canon = {"_readme": f"Planned by the agent: {plan.get('logline', '')}", "characters": chars, "worlds": plan["worlds"],
             "default_world": plan["default_world"], "never_common": "text, letters, watermarks, logos",
             "image_switches_default": {"safe": True, "pro_photo": True, "bad_photo": False, "pov": False, "indoor": False,
                                        "daytime": False, "atmosphere": True, "suffix": False},
             "negatives": {}}
    p.save("canon.json", canon)
    p.save("shots.json", {"_readme": f"Planned by the agent for \"{plan.get('title')}\". Edit freely; fields: docs/shots.md.",
                          "shots": plan["shots"]})
    with open(p.path("song", "caption.md"), "w", encoding="utf-8") as f:
        f.write(f"# Song brief (the MiniMax Music 3 caption), written by the agent\n\n{plan['song']['caption']}\n")
    with open(p.path("song", "lyrics.txt"), "w", encoding="utf-8") as f:
        f.write(plan["song"]["lyrics"].strip() + "\n")
    p.save("plan.json", {k: v for k, v in plan.items() if k != "shots"})
    cfg = p.load("project.json")
    for k in ("fps", "work_size", "crop", "final_size", "video_frames", "takes", "song_seeds", "finish", "overlay", "sheets"):
        cfg.pop(k, None)
    cfg.update({"profile": "short", "length": plan.get("length"), "aspect": o.get("aspect") or "16:9",
                "image_model": o.get("image_model") or "flux2", "scene": "agent", "song_max_seconds": L["seconds"] + 15,
                "grade": {"look": o.get("grade") or "A2_portra_dusk_plus", "lifts": []},
                "sheets": {"approve": o.get("approve_looks", False) is not False, "yolo_source": "text"},
                "overlay": studio.overlay_cfg(plan["song"]["lyrics"], plan.get("title"), o.get("overlay"), o.get("aspect"))})
    p.save("project.json", cfg)
    p.log("agent_plan", title=plan.get("title"), shots=len(plan["shots"]), characters=list(chars), length=plan.get("length"))
    return P.Project(p.root)


HANDOFF = """NIGHTSHIFT STUDIO HANDOFF. The user started a music video in Nightshift Studio and asked you, their agent, to direct it.
Drive Nightshift on their GPU machine through its MCP server and make the whole video.

The user's idea:
{idea}

Their settings: length {length} (about {seconds} s, about {shots} shots), aspect {aspect}, image model {image_model},
colour grade {grade}, lyric HUD {overlay}, direction {mode}.

How:
1. Connect to the Nightshift MCP server at {mcp_url} (streamable HTTP, no auth, on their local network).
2. Call plan_format and follow it exactly: write the lyrics, the song brief, the characters, the worlds and every shot.
   You write the creative plan with your own model; do not run a model on the GPU machine.
3. Call create_from_plan with your plan and these settings: length="{length}", aspect="{aspect}", image_model="{image_model}",
   grade="{grade}", overlay={overlay_py}, mode="{mode}".
4. Call pipeline_run(project=<the project it returns>). It renders for {hours}. Poll pipeline_status every 5-10 minutes.
   In director mode the user approves checkpoints in the Studio app ({studio_url}); in yolo mode it runs to the end.
5. Tell the user the project name now, and again when out/pass01.mp4 is ready. If a step fails, read the log lines in
   pipeline_status, fix the project files (read_doc / write_doc / patch_shot) and run again: finished renders are kept.
"""


def handoff_brief(idea, length, opts, mcp_url, studio_url):
    L = LENGTHS[length]
    return HANDOFF.format(idea=idea.strip(), length=length, seconds=L["seconds"], shots=L["shots"],
                          aspect=opts.get("aspect") or "16:9", image_model=opts.get("image_model") or "flux2",
                          grade=opts.get("grade") or "A2_portra_dusk_plus", overlay="on" if opts.get("overlay") else "off",
                          overlay_py="true" if opts.get("overlay") else "false", mode=opts.get("mode") or "yolo",
                          mcp_url=mcp_url, studio_url=studio_url,
                          hours={"short": "under an hour", "medium": "about 1.5 hours", "full": "several hours"}[length])


def send_handoff(settings, brief, payload):
    """POST the brief to the user's agent (an OpenClaw / Hermes webhook, or anything that takes JSON)."""
    url = settings["hook_url"]
    if url.rstrip("/").endswith("/notes"):              # a plain-text drop box the agent polls (e.g. a LAN notes endpoint)
        data, headers = brief.encode(), {"Content-Type": "text/plain; charset=utf-8"}
    else:                                               # an agent webhook: OpenClaw /hooks/agent takes {"message"}, wake takes {"text"}
        data, headers = json.dumps(dict(payload, message=brief, text=brief)).encode(), {"Content-Type": "application/json"}
    if settings.get("hook_token"):
        headers["Authorization"] = f"Bearer {settings['hook_token']}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"status": r.status, "reply": r.read(2000).decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        raise PlanError(f"your agent's webhook answered {e.code}: {e.read(300).decode('utf-8', 'replace')}") from None
    except urllib.error.URLError as e:
        raise PlanError(f"your agent's webhook is not reachable ({e.reason})") from None
