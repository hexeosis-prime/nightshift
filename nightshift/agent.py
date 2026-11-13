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
 "grade": "A2_portra_dusk_plus" | "A_portra_dusk" | "B_cinestill_night" | "C_faded_pastel" | "none",
                                     // the color grade: warm Portra dusk (+ is punchier), CineStill night (cool, neon
                                     // halation), faded pastel (soft, daylight), none. Pick what suits the idea.
 "hud": false,                       // the animated lyric HUD (word-by-word on-screen lyrics). true ONLY if the user asks
                                     // for on-screen lyrics, captions, karaoke text or a HUD; otherwise false.
 "characters": {                     // 1 or 2 people (keys: lowercase, e.g. "maya", "theo"). No real or famous people.
   "<key>": {
     "noun": "woman" | "man" | "person",
     "name": "display name",
     "person": "identity words: age as a number range, face shape, eyes, hair (color, length, style), skin tone, build. 25-45 words. Concrete, no adjectives like beautiful.",
     "outfit": {"close": "top + accessories only", "medium": "top + bottoms", "wide": "full outfit including shoes"},
     "video_name": "how video prompts name them: 'the woman with short silver hair and a red bomber jacket'",
     "signature": "the one most recognisable feature",
     "never": "things that must not appear on them, comma separated",
     "voice": "female singer" | "male singer" | "female rapper" | "male rapper"
   }
 },
 "worlds": {                         // usually 1, at most 3 visual worlds; each shot names one
   "<key>": {"style": "photographic look in concrete words: film stock / lens look, light quality, time of day, color",
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

Abstract and instrumental videos: when the idea has no performer (shapes, light, landscapes, textures, a mood) or asks for
an instrumental, add "abstract": true. Then "characters" is {} and every shot has "chars": []; there are no lipsync
shots; use t2v and fflf for camera moves, and "ff" with a "location" (what the first frame shows) and an "action" (the
lens and what moves) for a first frame that comes alive. For an instrumental, "lyrics" holds only section tags
([Intro], [Instrumental], [Build], [Drop], [Outro]) and the caption says "instrumental, no vocals". An abstract video
can still have a sung song: then keep the lyrics, and the shots simply show no singer.
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
    if length == "auto":      # Full Agent Mode: one box, the agent picks the length and the shape from the idea
        user = (f"The idea:\n{idea.strip()}\n\nChoose the length from the idea: \"short\" (about {LENGTHS['short']['seconds']} s, "
                f"about {LENGTHS['short']['shots']} shots) unless the idea asks for longer: \"medium\" (about {LENGTHS['medium']['seconds']} s, "
                f"about {LENGTHS['medium']['shots']} shots) or \"full\" (about {LENGTHS['full']['seconds']} s, about {LENGTHS['full']['shots']} shots). "
                f"Choose the shape: \"9:16\" (vertical, for phones) unless the idea asks for widescreen, then \"16:9\". "
                f"Add \"length\" and \"aspect\" to the JSON, and write the lyrics, arrangement and shots for that length.")
    else:
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


def normalize(raw, length="medium", abstract=None):
    """Check and repair a plan; raises PlanError for what can't be repaired. abstract (or "abstract": true in the plan):
    no cast and no lip-sync, and the song may be instrumental."""
    if length == "auto":
        length = raw.get("length") if raw.get("length") in LENGTHS else "short"
    from .lyrics import INSTRUMENTAL, sheet_lines
    chars_in = raw.get("characters") or {}
    if isinstance(chars_in, list):
        chars_in = {c.get("key") or c.get("name") or f"c{i}": c for i, c in enumerate(chars_in)}
    if abstract is None:
        abstract = raw.get("abstract") is True or str(raw.get("abstract")).lower() == "true"
    if abstract:
        chars_in = {}
    if not chars_in and not abstract:
        raise PlanError("plan field 'characters': empty (1 or 2 people needed; an abstract plan sets \"abstract\": true)")
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
    instrumental = abstract and not lines
    if instrumental:
        lyrics = lyrics if lyrics.startswith("[") else INSTRUMENTAL.strip()
    if len(lines) < 4 and not instrumental:
        raise PlanError(f"plan field 'song.lyrics': {len(lines)} sung line(s), at least 4 needed")
    if len(caption) < 80:
        raise PlanError(f"plan field 'song.caption': {len(caption)} characters, at least 80 needed (genre, BPM, key, arrangement)")
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

    shots, used, last_line, tried = [], set(), -1, []
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
        if abstract and mode == "lipsync":
            mode = out["mode"] = "ff"
        if abstract and mode == "ff":          # a first frame of a place or an image, brought to life; nobody in it
            out.update(chars=[], action=s.get("action") or "slow drifting motion, 35mm lens",
                       location=s.get("location") or "an empty landscape at dusk", video=video or s.get("location") or
                       "Slow, continuous motion through the frame.")
        elif mode == "t2v" or (mode == "fflf" and not cs):
            out.update(chars=[], video=video or s.get("location") or "An empty place at dusk. Slow cinematic camera move.")
            if mode == "fflf":
                out.update(fit=True, action="", location=(s.get("location") or "an empty street at dusk") + ", completely empty")
        else:
            if not cs:
                cs = [next(iter(chars))]
            if mode == "lipsync":
                tried.append(s.get("anchor") or "")
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
                out["add"] = {"char": cs[1], "where": "standing beside the other person, a little behind", "expr": "natural"}
        shots.append(out)
    if len(shots) < 3:
        raise PlanError(f"plan field 'shots': {len(shots)} usable shot(s), at least 3 needed")
    if not abstract and not any(s["mode"] == "lipsync" for s in shots):
        raise PlanError("plan field 'shots[].anchor': no lip-sync shot's anchor matches the first words of a lyric line" + (f" (tried: {', '.join(repr(a) for a in tried[:4])})" if tried else ""))
    from .studio import GRADES
    grade = raw.get("grade") if raw.get("grade") in GRADES else "A2_portra_dusk_plus"
    hud = (raw.get("hud") is True or str(raw.get("hud")).lower() == "true") and not instrumental
    return {"_validated": True, "title": raw.get("title") or "Untitled", "logline": raw.get("logline") or "", "length": length,
            "abstract": abstract, "instrumental": instrumental,
            "grade": grade, "hud": hud, "aspect": raw.get("aspect") if raw.get("aspect") in ("9:16", "16:9") else None,
            "characters": chars, "worlds": worlds, "default_world": default_world,
            "song": {"caption": caption, "lyrics": lyrics}, "shots": shots}


def create_from_plan(root, plan, opts=None):
    """opts: aspect, image_model, mode, grade, overlay, comfy_url, comfy_dir, approve_looks.
    grade and overlay left out (or None/"") use the plan's own "grade" and "hud"."""
    o = dict(opts or {})
    if not o.get("grade"):
        o["grade"] = plan.get("grade")
    if o.get("overlay") is None:
        o["overlay"] = bool(plan.get("hud"))
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
    o["aspect"] = o.get("aspect") or plan.get("aspect") or "16:9"
    if plan.get("instrumental"):
        cfg["instrumental"] = True
        o["overlay"] = False                 # no words, no lyric HUD
    cfg.update({"profile": "short", "length": plan.get("length"), "aspect": o["aspect"],
                "image_model": o.get("image_model") or "flux3", "scene": "agent", "song_max_seconds": L["seconds"] + 15,
                "grade": {"look": o.get("grade") or "A2_portra_dusk_plus", "lifts": []},
                "sheets": {"approve": o.get("approve_looks", False) is not False, "yolo_source": "text"},
                "overlay": studio.overlay_cfg(plan["song"]["lyrics"], plan.get("title"), o.get("overlay"), o.get("aspect"))})
    p.save("project.json", cfg)
    p.log("agent_plan", title=plan.get("title"), shots=len(plan["shots"]), characters=list(chars), length=plan.get("length"))
    return P.Project(p.root)


HANDOFF = """NIGHTSHIFT STUDIO HANDOFF. The user typed an idea for a music video into Nightshift Studio and asked you, their agent,
to make it. Nightshift runs on their GPU machine; you drive it through its MCP server, which has every tool and guide you need.

The user's idea:
{idea}

{choices}

How:
1. Connect to the Nightshift MCP server at {mcp_url} (streamable HTTP, no auth, on their local network).
2. Call plan_format and follow it exactly: write the lyrics, the song brief, the characters, the worlds and every shot.
   You plan with your own model; don't run a model on the GPU machine (it renders).
3. Call create_from_plan with your plan and: {args}.
4. Call pipeline_run(project=<the project it returns>). It renders for {hours}; poll pipeline_status every 5-10 minutes.
   {mode_note}
5. Tell the user the project name now, and again when out/pass01.mp4 is ready. If a step fails, read the log lines in
   pipeline_status, fix the project files (read_doc / write_doc / patch_shot) and run again: finished renders are kept.
"""


def handoff_brief(idea, length, opts, mcp_url, studio_url):
    """length "auto" (Full Agent Mode): the agent chooses length, shape, grade and HUD, and the video runs to the end."""
    mode = opts.get("mode") or "yolo"
    args = [f'image_model="{opts.get("image_model") or "flux3"}"', f'mode="{mode}"']
    if length == "auto" or length not in LENGTHS:
        choices = ("You choose: the length (\"short\", about 40 s and 9 shots, unless the idea asks for longer: \"medium\" about 75 s, "
                   "\"full\" about 2.5 min), the shape (\"9:16\" vertical unless the idea asks for widescreen \"16:9\"), the color grade "
                   "(\"grade\" in the plan) and the lyric HUD (\"hud\" in the plan: on only if the idea asks for on-screen lyrics).")
        args = ['length=<your choice>', 'aspect=<your choice>'] + args
        hours = "under an hour for short, longer for medium or full"
    else:
        L = LENGTHS[length]
        choices = f"Their settings: length {length} (about {L['seconds']} s, about {L['shots']} shots), shape {opts.get('aspect') or '16:9'}."
        args = [f'length="{length}"', f'aspect="{opts.get("aspect") or "16:9"}"'] + args
        if opts.get("grade"):
            choices += f" Color grade {opts['grade']}, lyric HUD {'on' if opts.get('overlay') else 'off'}."
            args += [f'grade="{opts["grade"]}"', f'overlay={"true" if opts.get("overlay") else "false"}']
        else:
            choices += " You choose the color grade (\"grade\") and the lyric HUD (\"hud\", only if the idea asks for on-screen lyrics)."
        hours = {"short": "under an hour", "medium": "about 1.5 hours", "full": "several hours"}[length]
    mode_note = ("It runs to the end without stopping." if mode == "yolo"
                 else f"It stops at checkpoints; the user approves them in the Studio app ({studio_url}).")
    return HANDOFF.format(idea=idea.strip(), choices=choices, mcp_url=mcp_url, args=", ".join(args), hours=hours, mode_note=mode_note)


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
