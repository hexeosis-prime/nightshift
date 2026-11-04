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
- **Model download links**, or a script, for every file the workflows load
