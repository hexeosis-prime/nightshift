# Nightshift Master Plan

_Mirror of the shared Claude Doc that hexe and Claude edit (the master: https://claude.ai/artifact/8YDBERhm8QL2jVMxi45Pdd).
Updated by Claude on the `next` branch so Zero and hexONE can read it. Edit the doc, not this file. As of 2026-11-07._

**Final plan, agreed Nov 7.** Open items carry into the phase where they're needed. Category labels (formats, styles) may
be renamed, and a few may be added if research turns up a popular format or style we're missing; what each one contains
stays as written.

Nightshift grows from a music-video generator into a video system: formats, presets, styles and show kits on one engine.
The order is fix the bugs first, then wire up Director Mode, then build the preset system.

## How this plan works

Each item is tagged with who raised it: **E** Erik's notes (Nov 7) · **Z** Zero's notes for Claude (Nov 7) · **H** hexONE's
notes for Claude (Nov 7) · **UX** Director Mode UX notes (Nov 5) · **R** ROADMAP.md and the Nov 6-7 wellness findings.

Decisions so far (Nov 7):

- **Names:** Format / Preset / Style / Show. "Genre" now means musical genre only.
- **Order:** Phase 1 fixes, Phase 2 Director Mode UX, Phase 3 the preset system. The other sections are pulled in when a
  phase needs them.
- **Scope:** the Artificial State TV station and the x402 store are separate projects. Nightshift only writes a manifest
  entry per render.
- **Prompt refinement** is its own track, in its own session.
- **The Claude Doc is the master;** this file mirrors it.

**Don't break these** (Z, H): idempotent re-runs that keep renders and picks · the first/last-frame chain, where shot N's
end frame is shot N+1's start frame · the workflow guards the look, and agents fill only the slots · credits-first
attribution · no black gaps in anything that plays continuously · every re-release materially better than the last.

## Phase 1: Fix first

**Progress, Nov 7 night** (on `next`, tests pass):
- **Vertical: fixed, different root cause.** The graphs were fine; the starter project.json carried explicit 16:9 sizes that
  beat `"aspect": "9:16"` in hand-built projects. The aspect now owns the sizes.
- **Bricked projects: fixed.** A bad profile / aspect / image_model opens with a warning and the default; `write_doc`
  refuses to write one.
- **Watchdog: interim fix.** Video and song jobs count log silence only after half their own time limit. Progress-based
  detection still to do.
- **Workflow audit: written** (`docs/workflow-audit.md`), hexe's checklist for the ComfyUI re-export.

**Progress, Nov 13** (on `next`, tests pass):
- **Errors name the step, the shot and the field.** The shot list is checked before anything renders and whenever an agent
  writes it (`write_doc` and `patch_shot` refuse a bad value); planner errors name the plan field.
- **Watchdog on progress, not log silence.** It listens to ComfyUI's websocket (standard library, one client id per
  project so a resumed run still hears its jobs): no sampler step, node or preview for 10 min and no log line = stalled.
  No websocket: the old log rule.
- **Run health** in Studio, `nightshift status` and `pipeline_status`: running, rendering, waiting, failed (with the error),
  stopped mid-step, or stalled (20 min with nothing queued), each with what to do.
- **Abstract and instrumental plans:** `"abstract": true`, no cast, no lip-sync; an instrumental song skips the lyric
  check and timing, and the cuts follow the beats.
- **No prompts in shared files:** every Nightshift encode drops metadata; `nightshift publish` / MCP `publish` makes
  clean copies of stills, takes and songs (ComfyUI hides the prompt and workflow in each).
- **Birds** are in the default video negatives (and for empty-place moves).

- [x] **Vertical renders come out landscape** (Z, H). The LTX latent size is wired through calculator nodes to fixed
  1280x768 values, so the size setter silently does nothing. Fix: rewire every LTX workflow so the latent takes free
  width and height inputs. Test: build a 9:16 project and check the clip size.
- [x] **The watchdog kills healthy long renders** (Z, H). Fix: judge progress from ComfyUI's progress events, not log
  silence; verify the first/last-frame decode is tiled; show the watchdog settings in Studio. Test: a synthetic 2-shot run.
- [x] **One bad value bricks a project for good** (Z). Fix: validate at write time with a clear error; open with defaults
  plus a warning.
- [x] **Runs go silent between steps** (Z). Fix: detect no progress for N minutes outside a checkpoint, then resume
  automatically or show "looks stalled, restart?".
- [x] **Plan errors don't say what failed** (Z, H). Fix: every error names the field and the shot.
- [x] **Abstract and instrumental videos can't be planned** (Z). Fix: an "abstract" plan mode with no cast and no lyrics.
- [ ] ~~ComfyUI API from the Mac~~ moved out: internal studio setup for Zero, not Nightshift (H).
- [x] **Published files carry our prompts** (E, R). Fix: a publish/export step that strips metadata.
- [ ] **Dependency pin** (H): streamlit 1.50.0 pins packaging<26 and pillow<12.

- [x] **Older project shows the wrong finished video** (E): fixed Nov 7 on `next`, the player keys on project + file.

Also (R): keep birds out of wide-shot prompts and add "birds" to the default negative (done Nov 13).

## Phase 2: Director Mode UX

Every checkpoint gets the same four actions: **Choose** from 3 · **Reroll** (new seeds, same brief) · **Accept** with a
plain statement of what is approved · **Go back**, always. The backend already supports them; this is app wiring.

| Checkpoint | Today | Change |
| --- | --- | --- |
| Song pick | 4 choices, no way back | 3 choices + reroll + back |
| Cast look (sheets) | 2 choices | 3 choices + reroll |
| Stills | shows 2 per shot, can't pick | pick per shot, reroll one shot |
| Video takes | can't pick | pick per shot, reroll one shot |
| Later checkpoints | "approve" with nothing to choose | show what is approved, or auto-pass with "intervene" |
| Finished video | shown with nothing to do | download, share, revise, start new, archive |

- [ ] Optional connected-agent toggle (UX, Z) · [ ] watchdog and retry settings in the UI (Z) · [ ] Erik's web UI bug
  notes (to come)

## Phase 3: The preset system

| Layer | What it decides | Examples |
| --- | --- | --- |
| **Format** | shot-list structure, pacing, edit rules, audio plan | music video, app demo, breaking news, telenovela, YouTube explainer, UGC product ad, 30 s TV spot, cinemagraph loop, motion graphics, blipverts, channel-flip anthology |
| **Preset** | a variation inside a format (about six each) | energetic dance, dramatic ballad, dubstep anthem, hand-made indie band; captions from calm to hyper-kinetic |
| **Style** | prompt wording plus default grade and post | cinematic, indie homemade, broadcast quality, cyber future, live TV news, "Apple commercial" |
| **Show** | recurring cast, locations, Blender sets, blocking, brand rules | The Artificial State, Global Vision News, a client's brand kit |

Plus length (short / medium / long) and aspect. Style pairs with a format by default but mixes freely; a Show plugs into
any Format; the channel-flip anthology is a format of formats. Internal kits stay private, with generic public presets
derived from them. First pair to build: app demo + commercial style, seeded from the wellness proof of concept.

### Styles (decided Nov 13)

Nine Styles, named in the words clients write in briefs. Each ships with a 5-10 s reference loop: briefs carry a look with
tone words plus reference videos, not look names (hexONE's research, Nov 7), so the name is the label and the loop is the
brief.

| Style | Was (working title) | The look | Prove |
| --- | --- | --- | --- |
| Cinematic | Cinematic | 35mm, shallow focus, volumetric backlight, filmic grade, grain | 2 |
| Premium Commercial | Clean commercial | huge soft light sources, reflections tracing the product, seamless background, no camera shake | 3 |
| Broadcast | Broadcast + Live TV news | evenly lit studio, symmetrical frames, controlled color; news graphics from the News Package | 1 |
| Handheld | Indie handmade (split) | phone-shot candid: handheld shake, quick reframes, natural window light | 4 |
| Vintage | new | VHS, camcorder, 8mm: scan lines, tape wobble, 4:3 | 5 |
| Cyber Future | Cyber future | neon, haze, wet reflective surfaces, magenta and cyan rim light | 6 |
| Handmade | Indie handmade (split) | felt, clay, stop-motion, craft textures | 7 |
| Documentary | new | long-lens observational, natural light | 8 |
| Performance | new | music-video gloss: colored backlight, smoke, hard sun | 9 |

- A Style fills prompt slots (lighting, camera, style, sound of the 8-slot prompt) plus FLUX still words, LTX video words,
  negatives and a default grade; it is not adjectives on the end.
- Every Style word is marked proven, likely or to prove; to-prove words go through the prompt refinement session first.
- Live TV news is no longer a Style: Broadcast carries the look, the news Format the structure. The news Format's graphics
  module is the **News Package**: bug, lower third, ticker, chyron.
- hexe's location bank (36 locations, in image testing) fills the location slot and starts the backlot.

## Edit engine

- [ ] Snappy 2-3 s shots (E, Z) · [ ] rhythm patterns like 2,2,6,2,2,6,2,6,4 (E) · [ ] dissolves, the channel-flip glitch,
  first/last-frame match cuts (E, H, R) · [ ] cuts on the beat, including mid-shot (Z) · [ ] assembly spec: 0.75 / 1 /
  1.5 s crossfades, −16 LUFS, ambience bed, narration check (H) · [ ] one music track under the whole cut (R)

## Generation tech

Check LTX 2.5 first; it may change what's worth building.

- [ ] LTX 2.3 → 2.5, including video with alpha (E, H) · [ ] video-to-video with Blender clay renders (E, R) ·
  [ ] structured camera control, e.g. a true corkscrew (E, R) · [ ] audio path audit for beat reactivity (Z) ·
  [ ] short shots as first-class (Z) · [ ] one-click cloud-loop generator (H) · [ ] 4-angle turnaround sheets (H) ·
  [ ] optional QC pass for client work (H) · [ ] faces in wide shots and drift after ~6 s (R) · [ ] character sheet as
  an LTX reference (R) · [ ] traditional VFX techniques (E)

## Animation modules

- [ ] 3D look: hexe-viewer, more of the model library, fully emissive shaders with no lights (E, R)
- [ ] 2D look: the After Effects process rebuilt as code (E, R)
- [ ] Sharing policy, to decide once built: basic module and starter workflows public, signature templates may stay
  internal (E)

## Output and distribution

- [ ] GIF sibling for every render (Z) · [ ] metadata strip on publish · [ ] manifest entry per render in the TV station
  schema (H) · [ ] cost telemetry: renders, GPU-hours, electricity (H) · [ ] render file management and archiving (E)

## Knowledge

- [ ] Prompt and workflow refinement session (E, R) · [ ] prompt-proving pipeline as a CLI (H) · [ ] case as a control,
  cat / Cat / CAT (H) · [ ] Erik's VFX brain dump (E) · [ ] MCP driving guide (Z) · [ ] model download links (R)

## Decisions and open questions (Nov 7)

- **Checkpoints:** hard gates with an inactivity timer. After 1 hour with no pick, auto-pass with the top-ranked option and
  show an Intervene button. Every past step stays viewable (e.g. the 3 songs), with Redo from here and Branch from here.
- **Choose / Reroll:** 3 options at every checkpoint (songs, cast looks, stills per shot, takes per shot). Reroll makes 3
  new; a "keep" mark carries one over so only 2 are made.
- **Connected-agent toggle:** not in v1. Director Mode stays agent-free; full agent control stays with MCP. "Tag an agent
  in" is saved for later.
- **Finished-video screen:** Download, Revise (back to any step), Start new, Archive. No Share.
- **LAN access:** internal studio setup for Zero, not a Nightshift feature. ComfyUI has no login: allow only the Mac's
  address through the PC firewall.
- **Format build order:** 1) news crew (hexe saves its ComfyUI workflows in API format), 2) client-shaped 15-30 s
  lifestyle ad, 3) app demo template.
- **User Library:** every install gets a Library folder set in Settings, outside the app folder, for the user's own
  songs, characters, show kits and presets. Updates never touch it. Our private kits are our Library.
- **Style names (working titles):** Cinematic, Indie handmade, Broadcast, Cyber future, Live TV news, Clean commercial. **Decided Nov 13** from hexONE's research: see Phase 3, Styles.
  **Research: hexONE** — what words clients and briefs use for these looks, and which prompt words the models respond to
  for each. Claude builds with the working titles meanwhile.
- **Workflow consistency audit** (Phase 1): Claude lists how each workflow sets size, frames and seconds; hexe fixes them
  in ComfyUI and re-exports UI + API versions.
- **Still to share:** the v2v / Blender workflow research. The drone prompt uses "corkscrew" for now; the exact one comes
  with the prompt refinement session.

## Added Nov 9-11 (from the shared doc)

**Phase 1 progress:** hexe rebuilt the four LTX graphs as one, `vid_ltx` (`workflows/vid_ltx.json`, found by `ns_`
titles): one INT8 ConvRot model, one LoRA set, 3 stages everywhere, toggles for first+last frame, song audio in and
isolated vocals. All 7 mode tests passed Nov 11 (`scripts/ltx_test.py`). Next: switch the builder to it.

**Findings** (`docs/video-prompt-slots.md`, `docs/findings/`): video prompts in screenplay order (location before
subject), hexe's 8 slots with include/exclude rules; 3 stages beat 2; same still as first and last frame = locked-off
camera; lip-sync with first + last frame works with two different stills of the same character; a "must show the
words" shot needs first + last frame, a medium close-up and a neutral start; the locked-seed reporter benchmark.

**New items:**
- Video prompt builder in screenplay order; prompt-part bank in the Library (one folder per slot, `## name` entries);
  builders separate from models; text labeled `ns_fixed_` / `ns_toggle_` / `ns_slot_`.
- Shots match the song's mood: the song's mood and energy set shot length, edit pace, camera speed, transitions, look and
  expressions, for performers and abstract videos alike.
- Prompt variables (`[COLOR-1]`), filled from the Show kit or swept across a run.
- Render size by card (24 GB: 1280x768 + upscale; 32 GB+: native 1920x1088); upscaler A/B against hexe's After Effects
  Detail-preserving Upscale.
- A small Nightshift node pack, later: `ns_inputs`, `ns_prompt_video` / `ns_prompt_image`, `ns_prompt_bank` (named
  entries in a dropdown, lists from Library files), `ns_save` with metadata strip.
- One-shot frames from references (character sheet + location plate) instead of text-then-face-edit.
- The backlot: location presets with location sheets, like character sheets.
- Load 3D (core node) for composing stills from 3D models.
- Archive option for ComfyUI's duplicate outputs; a sweep of the local Nightshift folder.
