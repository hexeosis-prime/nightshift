# Roadmap

Where Nightshift goes after the first video. Nothing here is built yet.

## Next phase: prompts and faces (after the contest)

- **Faces in wide shots.** A face-detail pass: crop the face from a wide first frame, run the identity edit large, paste it
  back. hexe has ideas to try.
- **Audit every embedded prompt for FLUX 3.** The still, sheet and edit prompts were written for Flux 2 Klein and moved
  over; check them against FLUX 3's own prompting guidance and update what's changed. No "pores" or "skin texture" wording
  anywhere (it made skin look wrong before).
- **Try an "improve" pass in the edit prompts.** A tip to test: asking for the best *overall improved* image (the source
  prompt said "In terms of photoshopping, show me your best overall improved image?"). Reword it in our own language without
  "photoshopping"; "best overall improved" seems to be the part that matters. A/B it on identity edits and stills.
- **Fold in hexe's other tested prompts** for the jobs they fit.
- **Character sheet layout tests.** hexe collected alternative sheet tips and layouts to A/B against the seven-panel sheet.
  First test: a darker mid-gray background (around #808080; today's is #B8B8B8) against blown-out highlights on
  reflective or white clothing, and cleaner hair edges.
- **Vocalise mode** (hexe's experimental genre: vocals used as an instrument, invented language, Sigur Rós style). Whisper's
  lyric coverage can't rank takes without real words, and lip-sync anchors need recognizable lines. Instead: rank takes
  without coverage (or by vocal presence), and find vocal phrases from the separated vocal stem's energy (where singing
  starts and stops) to place lip-sync shots and HUD sections. Zero's MiniMax runs today: ~450 s for a 3-minute track.
- **Prompt and workflow refinement session** (hexe, planned): A/B tests to find the wording each model responds to, starting
  from `docs/findings/2026-11-07-wellness-poc.md` and the picks in `examples/wellness_poc/PICKS.md`. Includes the filmic vs
  commercial look, wide-shot people and birds, plastic-looking rocks, and faces drifting after ~6 s.
- **Birds out of wide shots**: no birds in prompts, "birds" in the default negative for wide and aerial shots.
- **Can LTX 2.3 use the character sheet as a reference?** Today LTX gets the identity-edited first frame (and a last
  frame on first/last-frame shots). Check the current LTX 2.3 docs and ComfyUI nodes for an identity/reference input, or
  whether a sheet crop placed as a keyframe helps faces hold through a shot.

## hexeosis 2D loops as code

- **Rebuild hexe's 2D After Effects loop process as a code renderer**, next to hexe-viewer (the 3D look). Steps:
  1. hexe talks through the concept first: each subcomp as a node (what goes in, the one thing it does, what comes out),
     how nesting chains them, and the perceptual choices (color change, motion) tuned by eye.
  2. Claude writes an ExtendScript that exports the AE template's full structure to text (comp/precomp nesting, layer
     order, blend modes, effects and settings, keyframes and easing, expressions, loop lengths, time remapping).
  3. Rebuild as a small node graph where one or two root time signals drive everything downstream, and the seamless loop
     comes from the structure: the end state is the start state ("as at the end, so at the beginning"), not a crossfade.
  4. Render perfect loops at any size with per-piece parameters; Nightshift can call it as a shot source.

## Format templates

Starter projects for other kinds of video: a shot-list skeleton, a song or voice-over brief, cut rules and an overlay config
for each.

- **Music video**: what ships today (`projects/starter`)
- **Serialized telenovela clips**: recurring cast and sets across episodes, dialogue instead of a song
- **YouTube explainer**: voice-over driven, with diagrams and on-screen text
- **Advertising and UGC product videos**: product shots, presenter-to-camera, short vertical cuts

## Style templates

Canon and workflow presets for a look, usable with any format:

- **Photoreal people in real locations**: the first video's look
- **Motion-graphics animation**
  - lyric videos with dynamic, music-reactive type
  - app demo ads
  - style presets
- **2D animation**: anime, traditional hand-drawn
- **3D animation, 3D characters and 3D worlds**: low poly, retro PS2 game, high-end Octane-style renders

## Features

- **Video-to-video workflow** (an LTX 2.3 graph was started during the first video)
- **Blender clay renders** for complex camera moves and precise character blocking, used as guides for the video model
- **hexe-viewer animated elements** in the overlay
- **Image glitch effects** (an FL Glitch utility graph was used during the first video)
- **Structured camera control** for signature moves (a true corkscrew drone descent landing on a close-up): camera paths
  from Blender or a keyframe guide instead of prompt wording alone
- **Strip ComfyUI metadata on publish**: an export option (and a check) so files leaving Nightshift carry no embedded
  prompt or workflow; keep the metadata on the working copies
- **Promo / launch-video template** from the wellness proof of concept: phone push-in and pull-back (FLUX 3 screen
  composite + first/last frame), location stills, empty-space and tour b-roll, an ambient track under the whole cut
- **Overnight queue runner** with GPU rests and a hot-reloaded shot list (`examples/wellness_poc/promo_tonight.py`)
- **Model download links**, or a script, for every file the workflows load
