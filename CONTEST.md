# Nightshift × Open Source Higgsfield

Nightshift was built before the [Comfy "Open Source Higgsfield" challenge](https://comfy.org/open-source-higgsfield/) was
announced: the first commit in this repo is the pipeline as it was used to make "What Do You Want?", a 2:49 music
video. The commits after it (dated October 29, 2026) adapt it to the challenge's brief, *"build a working app that makes it
easy for someone else to create their own"*. They add an app, a profile that finishes in about an hour instead of a
night, vertical video, your-own-track input, and FLUX 3 Image Klein as an image model option.

## What the entry is

**Nightshift Studio** (`nightshift app`) is a local web app on top of your own ComfyUI. You give it a performer (a photo
of yourself, or a written description), a song (MiniMax Music 3 writes and sings it from your lyrics, or you upload
your track), a scene and a format. It then directs a complete music video:

1. **Character sheet first.** The app makes a front/back/face sheet with Flux 2 Klein or FLUX 3 Klein and you pick the look.
   Every later frame is edited toward that sheet and every take is scored against it with face recognition.
2. **Song.** MiniMax Music 3 renders a song for each seed and the app shows how much of your lyric sheet each one actually
   sings. Then the song gets a beat map and word timing from faster-whisper.
3. **Shot list fitted to the song.** Lip-sync shots start on lyric lines and cuts snap to beats.
4. **First frames.** Each shot gets a text-to-image still, then an identity edit from the approved sheet.
5. **LTX 2.3 video.** That means audio-driven lip-sync, first-to-last-frame camera moves and a text-to-video establishing
   shot, with a watchdog for stalls and OOMs.
6. **Pick, cut, grade.** The best take is chosen by face match, cut on the beat and graded, giving a finished
   1080×1920 or 1920×1080 video.

Director mode stops at each checkpoint in the app so you can choose. Hands-off mode stops once, to approve the look.

## How it meets the requirements

| requirement | where |
|---|---|
| Built with ComfyUI, run however you like | Every render is a ComfyUI API job: the 15 graphs in [`workflows/`](workflows/), each with a map naming its inputs. It runs entirely local, against ComfyUI on the same machine or another one on your network. |
| A working app | `nightshift app` ([nightshift/app.py](nightshift/app.py), [nightshift/web/studio.html](nightshift/web/studio.html)). Underneath it: the CLI (`nightshift new`, `nightshift run`) and an MCP server for agents (`nightshift mcp`), all on the same project folders. |
| Repo: app code, workflow files, open-source license, setup to run it locally | Apache 2.0 ([LICENSE](LICENSE)). Setup: [README](README.md#install), plus custom nodes and model files with download links in [docs/workflows.md](docs/workflows.md). `nightshift doctor` checks tools, workflows, node types and ComfyUI. |
| Other tools explained | ffmpeg (cut, grade), librosa (beats), faster-whisper (lyric timing), OpenCV YuNet + SFace (face scoring), all open source. Claude helped write the code and orchestrated the first video over MCP; the app needs no agent at all. |
| Lawful, SFW, no unlicensed IP or likenesses | The demo characters are generated personas described in text. The app asks for a photo of yourself or of someone who agreed. |
| Demo video ≤ 2 min, social post #OpenSourceHiggsfield | linked from the submission |

## Prize categories it fits

- **Open Weights Only.** No partner nodes and no closed-source APIs, at render time or anywhere in the app. The models
  are LTX 2.3 (LTX-2 Community License), Flux 2 Klein 9B or FLUX 3 Image Klein (BFL non-commercial/Kommunity licenses)
  and MiniMax Music 3 (open weights, CC BY-NC 4.0), all running in ComfyUI on one RTX 3090. The optional agent can be
  a local model too (see [docs/agents.md](docs/agents.md)). Licenses: [docs/licenses.md](docs/licenses.md).
- **VFX workflow built with LTX.** LTX 2.3 is the only video model and renders every shot: lip-sync from the song,
  first/last-frame moves and text to video.
- **Built with FLUX.** With `image_model: flux3` (the FLUX 3 Klein button in the app), FLUX 3 Image Klein makes the
  character sheets, every first frame and every identity edit (multi-reference edits through `Set Reference Multi Latent`).
- **Most Innovative.** It's a whole production pipeline, not one graph: a crew that writes the song, casts and locks the
  character, shoots, scores takes against the cast sheet and edits on the beat. It is drivable by a person in a browser
  or by any agent over MCP, overnight, on one consumer GPU.

## Profiles

| | `full` (the first video) | `short` (the app default) | `short`, medium length |
|---|---|---|---|
| song | 2-3 min, 4 seeds | 40 s, 4 seeds | 75 s, 4 seeds |
| shots | ~50, hand-written | 8, from a scene preset | 14, from a scene preset |
| takes | best-of-4 on complex shots | 1 | 1 |
| RTX 3090 | ~6.5-7 hours | about an hour | about two hours |

The aspect (`16:9` or `9:16`) and the image model (`flux2` or `flux3`) work with any profile. They go in `project.json`:
`"profile": "short", "aspect": "9:16", "image_model": "flux3"`.
