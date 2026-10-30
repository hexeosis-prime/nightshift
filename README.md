# Nightshift

**A music-video crew that works the night shift on your own GPU.** Song (lyrics and music), key frames for every shot, multiple takes, edit, grade, animated motion-graphics lyric HUD.
Directed by you, or not.

Nightshift turns a song idea into a finished music video with open-weight models running in a local
[ComfyUI](https://github.com/comfyanonymous/ComfyUI):

- **MiniMax Music 3** writes and sings the song from a production brief and a lyric sheet
- **Flux 2 Klein 9B** paints the first frames and keeps the characters' faces and wardrobe consistent from shot to shot
  (FLUX 3 Image Klein workflows are included but not yet tested end to end, so the app doesn't offer them yet)
- **LTX 2.3** animates them: lip-sync to the song, first-to-last-frame camera moves, text-to-video establishing shots
- **Python tools** fit the shot list to the song, score every take against the character sheets, cut on the beat, grade,
  and draw a lyric HUD that steers around faces

**Nightshift Studio** (`nightshift app`) puts all of it behind one page in your browser: a photo, a song, a scene, a format,
then *Start the shift*. Or an agent runs the pipeline over [MCP](https://modelcontextprotocol.io) (Claude, or any agent that speaks MCP, including one
running on a local model), and the GPU works through the night. Direct every pass, or let it make the calls and wake up to a
finished video.

The first video made with it, while the tools were being developed at the same time: **"What Do You Want?"** (2:49, 52 shots,
nine passes), [posted October 28, 2026](https://x.com/hexeosis/status/2115545427290489287).

Entered in Comfy's [Open Source Higgsfield](https://comfy.org/open-source-higgsfield/) challenge: see [CONTEST.md](CONTEST.md)
for what was added for it and how it meets the rules. Everything renders locally on open-weight models; no partner nodes, no
closed APIs, no agent required.

---

## Nightshift Studio

```bash
nightshift app --comfy-dir C:/ComfyUI_windows_portable/ComfyUI      # or --comfy-url http://<gpu-box>:8188 for ComfyUI elsewhere
```

opens `http://127.0.0.1:8189`. **Interactive Mode** asks five things:

1. **Who's in it**: a photo (yourself, or someone who agreed) and/or a few words: look, outfit. The character sheet is
   made from the photo, or from the words.
2. **The song**: MiniMax Music 3 writes and sings it from a vibe and your lyrics, or upload your own track (it's trimmed to
   the length; paste its lyrics for lip-sync, or leave them out for an instrumental).
3. **Where**: a scene preset (Night Avenue, Desert Highway, Neon Stage, Seaside Dawn), a look plus three places that the shot
   list moves the performer through.
4. **Format and look**: short (30-40 s, 8 shots, under an hour on a 3090), medium (60-75 s, 14 shots) or full, 9:16 or
   16:9, a colour grade, and the animated lyric HUD (16:9).
5. **How much you're involved**: *Director mode* stops at each checkpoint and waits for your picks and notes. *Hands-off
   mode* stops once to approve the character's look, then runs to the end.

**About hands-off mode:** it always makes a complete video, and there is a good chance some shots come out wrong to a human
eye: a hand with too many fingers, a face that drifts, a stray word painted on a wall. Nightshift catches some of this
itself (it re-takes shots with burned-in text and keeps the take whose face best matches the character sheet), but not
all of it. Watching the result and deciding whether to run a second pass or keep the weirdness is the human's call.

The pass then runs on your ComfyUI. The page shows each step, the jobs, a wall of the latest renders and the log, and stops
at the checkpoints: pick the character sheet, pick the song, look over the first frames and takes, watch the pass.
Projects land in ComfyUI's `output/nightshift/`, so renders appear in place. Each one is an ordinary Nightshift project
that the CLI and the MCP server can open too. The same form from the command line:

```bash
nightshift new my-video --scene desert-highway --aspect 9:16 --image-model flux3 --who man \
  --look "early thirties, short dark curly hair" --outfit "a rust corduroy jacket, white t-shirt" --photo me.jpg
```

### Agent mode

**Full Agent Mode** is one box: describe the video with as few or as many details as you like (the story, the places, who is
in it, what the song is about). Then either:

- **Plan it**: an agent model writes the lyrics, the song brief, one or two characters, the worlds and every shot, and the
  app shows you the plan before anything renders. Any OpenAI-compatible server works: LM Studio or Ollama on another machine
  (don't share the GPU that renders), OpenRouter, or a closed model. With an open-weights model nothing in the loop is closed.
- **Hand off to my agent**: the idea goes to *your* agent (OpenClaw, Hermes, Claude ...) with a brief that tells it how to
  drive Nightshift on this machine over MCP: read `plan_format`, write the plan with its own model, `create_from_plan`,
  `pipeline_run`, poll, report back. Set the agent's webhook in the app, or paste the brief into its chat. Start the app
  with `--mcp-port 8765` (in `studio.local.bat`: `set "NIGHTSHIFT_ARGS=--host 0.0.0.0 --mcp-port 8765"`) so the agent can
  reach it; the project shows up in the app and you watch it render.

## What you need

| | |
|---|---|
| GPU | NVIDIA with 24 GB VRAM. Built and tested on an RTX 3090. LTX 2.3 (22B, quantized) uses most of it, so nothing else should share the card while a pass renders. |
| ComfyUI | a recent build (LTX 2.3 and MiniMax Music 3 nodes are in core; 0.41+ for FLUX 3 Klein), plus the custom node packs and model files listed in [docs/workflows.md](docs/workflows.md) |
| Python | 3.10+ with `pip install -e .` (numpy, opencv, librosa, faster-whisper, mcp) |
| ffmpeg | on the PATH (cutting, grading, review copies) |
| Node 18+ | only for the lyric/HUD overlay (headless Chromium via playwright-core) |
| An agent | optional. Claude Code / Claude Desktop, or any MCP client. The CLI does everything without one. |

Model licenses are their own and two of the three are non-commercial for the weights: read [docs/licenses.md](docs/licenses.md)
before you make anything you plan to sell.

## Install

```bash
git clone https://github.com/hexeosis-prime/nightshift
cd nightshift
pip install -e .
python scripts/get_models.py                        # face detection + recognition models (~40 MB)
python scripts/get_comfy_models.py --comfy-dir ~/ComfyUI   # the ComfyUI model files (~120 GB; --set core flux3 adds FLUX 3 Klein)
(cd nightshift/overlay/web && npm install)          # only if you want the HUD overlay
```

**Windows:** double-click `setup_windows.bat` (a private Python in `.venv` via uv or your Python, the face and speech
models, ffmpeg through winget if it's missing; ComfyUI's own Python is never touched), then `studio.bat` opens the app. Put
your ComfyUI folder in `studio.local.bat` (`set "COMFY_DIR=C:\ComfyUI_windows_portable\ComfyUI"`) so renders land in place.

In ComfyUI: install the custom nodes and models from [docs/workflows.md](docs/workflows.md), then either open the app
(`nightshift app --comfy-dir <your ComfyUI folder>`) or set up a project by hand:

```bash
nightshift init ~/ComfyUI/output/nightshift/my-video --comfy-dir ~/ComfyUI
cd ~/ComfyUI/output/nightshift/my-video
nightshift doctor          # tools, models, workflow maps, ComfyUI reachable, every node type installed
```

Putting the project inside ComfyUI's `output/` folder means renders land straight in the project. ComfyUI on another machine
works too: leave `--comfy-dir` out, set `comfy.url` in `project.json`, and inputs are uploaded and outputs downloaded over its API.

## Quick start

A project is one folder. Fill in three things, plus a picture of each character if you have one (the starter has a worked
example of each):

| file | what it is |
|---|---|
| `canon.json` | the characters (identity words, wardrobe per framing and world, never-lists), the worlds, defaults |
| `shots.json` | the shot list. Song-agnostic: lip-sync shots say which lyric line they start on, not a timecode |
| `song/caption.md`, `song/lyrics.txt` | the song brief and the lyric sheet with section tags |
| `refs/` | optional: a picture of each character. Nightshift makes the character sheets first, from the picture or from the description, and the looks are locked before any other frame |

Then:

```bash
nightshift run             # director mode: renders, then stops at each checkpoint with a review packet
nightshift continue        # after you've looked (and changed whatever you wanted)
nightshift next-pass       # notes on the finished pass? fix, next pass, run again: only changed shots re-render

nightshift run --yolo      # or: no stops after the character looks are approved (none at all with sheets.approve false)
```

## Profiles

`project.json` picks a preset for the pass and can still override any single setting:

- `"profile"`: `full` (the first video: 121-frame clips, best-of-4 on complex shots, 4 song seeds) or `short` (97-frame clips,
  one take, 4 song seeds, a 40 s song, no HUD)
- `"aspect"`: `16:9` (1280×768 renders, 1920×1080 delivery) or `9:16` (768×1280 renders, 1080×1920 delivery)
- `"image_model"`: `flux2` (Flux 2 Klein 9B) or `flux3` (FLUX 3 Image Klein for sheets, stills and identity edits)

## How a pass works

```
sheets ─► song ─► analyze ─► timeline ─► stills ─► sheetedits ─► videos ─► pick ─► cut ─► overlay ─► finish
  │        │        │           │           │          │            │         │       │       │          │
character  M3     beats,     fit shots    Flux 2    identity     LTX 2.3    face    beat-   lyric    grade, HUD,
sheets     seeds  lyric      to the       first     edit from    ff/fflf/   match   locked  HUD      texture,
first             timing     song         frames    the sheet    lipsync/   ranks   edit             review copy
                                                                 t2v,       takes
                                                                 best-of-N
```

Every step is idempotent: it only renders what is missing, so after a note ("shot 26: keep the red light into the close-up")
you change that shot and run again. See [docs/pipeline.md](docs/pipeline.md).

## Directed, or not

- **Director mode** (default) stops at the checkpoints: *character looks* (sheet candidates for every character, and their
  outfits for each world), *song pick* (every rendered song with how much of the lyric sheet it actually sings), *stills review* (first frames ranked by face match), *takes review* (contact sheets of every take; the cut
  already points at the best-scoring one) and *pass review* (the finished pass, a numbered review copy, a notes file). The
  first pass is only "first" if you want changes: if you love it, it's the final pass.
- **Yolo mode** stops at most once: to approve the character looks (`sheets.approve` in `project.json`; set it to false and
  it never stops). The agent builds the sheets from the written descriptions, then picks the song that sings the most of the
  lyric sheet, the identity edit and the take with the best face match, and delivers a finished pass.

## Plugging in an agent

`nightshift mcp` is an MCP server with the whole pipeline as tools: project files, shot patches, job building, takes,
submitting and watching ComfyUI, face scoring, contact sheets (agents with vision can look at them), picking takes, assembly,
overlay, finishing, and the full pass as a background task. Long steps return a task id at once, so no client times out on a
40-minute render.

```bash
# Claude Code
claude mcp add nightshift -- nightshift mcp --project-root ~/ComfyUI/output/nightshift

# any stdio MCP client (Claude Desktop, Cursor, ...): command "nightshift", args ["mcp", "--project-root", "<folder>"]

# an agent on another machine (streamable HTTP; keep it on your LAN or behind an SSH tunnel: there is no auth)
nightshift mcp --http --host 0.0.0.0 --port 8765 --project-root ~/ComfyUI/output/nightshift
#   -> point the agent's MCP client at http://<gpu-box>:8765/mcp
```

The agent doesn't need to be on the GPU box, and it shouldn't share the GPU: a local LLM on the same card evicts the video
model and stalls or crashes renders. A Mac mini running Hermes (or anything else) with a model that fits there, driving the
3090 over HTTP, is the intended shape. See [docs/agents.md](docs/agents.md).

## Bring your own workflows

Every workflow is a ComfyUI API export plus a small map naming its inputs (`prompt`, `image`, `seed`, `frames`, `audio` ...).
Swap in your own graph by exporting it and writing its map, or by titling its nodes `ns:prompt`, `ns:seed` and so on.
`nightshift doctor` checks every map against its graph and every node type against your ComfyUI. See
[docs/workflows.md](docs/workflows.md).

## Time and cost (RTX 3090)

| | measured |
|---|---|
| Flux 2 Klein still or identity edit | ~50-60 s each once the model is loaded |
| LTX 2.3 clip (2-8 s) | ~3-4 min typical, up to ~8.5 min for the longest first/last-frame shots |
| MiniMax Music 3 song | up to ~30 min per seed |
| one full pass, ~50 shots, best-of-4 on the hard ones | ~6.5-7 hours: one night |
| one `short` pass from the app (8 shots, 30-40 s song, 4 song seeds) | ~45 min of GPU time (measured, in minutes: sheets 2, songs ~1 each, stills ~1 each, identity edits ~2.7 each, LTX clips 2.3-3.3 each) |

Everything runs locally; the cost is electricity and, if you use one, the agent's subscription. The first video was
directed by hexeosis/Erik and orchestrated by Claude on a $20/month plan; the heaviest week reached about 85% of the plan's weekly
usage. In principle a self-hosted agent (Hermes, for example) can run the same loop for nothing but power.

## Docs

- [CONTEST.md](CONTEST.md): the Open Source Higgsfield entry, rules and prize categories
- [docs/pipeline.md](docs/pipeline.md): the pass step by step, files, commands
- [docs/shots.md](docs/shots.md): every shot field and what it does
- [docs/techniques.md](docs/techniques.md): the craft that made the difference (rescue first/last-frame, self-consistent last frames, relighting, whip-pan arrivals, fly-overs, best-of-N)
- [docs/prompting.md](docs/prompting.md): writing for Flux 2 Klein, LTX 2.3 and MiniMax Music 3, with the full guides in
  [docs/guides/](docs/guides/)
- [docs/workflows.md](docs/workflows.md): the ComfyUI graphs, custom nodes, model files, maps
- [docs/agents.md](docs/agents.md): MCP tools, director and yolo loops, remote agents
- [docs/overlay.md](docs/overlay.md): the lyric HUD and its widgets
- [docs/troubleshooting.md](docs/troubleshooting.md): stalls, OOM, lost jobs, sync gotchas
- [docs/lessons.md](docs/lessons.md): what nine passes on the first video taught us
- [docs/licenses.md](docs/licenses.md): model licenses, read before commercial use
- [diary/what-do-you-want.md](diary/what-do-you-want.md): the making of the first video
- [ROADMAP.md](ROADMAP.md): what's next (format and style templates, video-to-video, Blender blocking)

## Credits

Made by Erik (hexeosis) and Claude: [hexeosis.com](https://hexeosis.com) · [erikbuth.com](https://erikbuth.com).
The prompting guides are by Zero (HEXEBOTZERO), an OpenClaw agent at hexeosis inc., with Gemini Argon (MiniMax Music 3)
and Erik (LTX 2.3), reviewed and edited by Claude Opus 5.5.
Models by Black Forest Labs (Flux 2, FLUX 3), Lightricks (LTX 2.3) and MiniMax (Music 3); ComfyUI and the custom node authors listed
in docs/workflows.md made the graphs possible.

Code: Apache License 2.0, copyright 2026 hexeosis inc. (see [LICENSE](LICENSE) and [NOTICE](NOTICE)). The models are not
covered by this license.
