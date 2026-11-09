# Findings: wellness-center proof of concept (Nov 6-7, 2026)

One overnight run, no Nightshift project: a stand-alone driver (`examples/wellness_poc/promo_tonight.py`) fed ComfyUI one
job at a time with GPU rests. Generic wellness brand, no people from real life. Banked here for the prompt and workflow
refinement session. The picks, with every prompt, seed and input, are in `examples/wellness_poc/PICKS.md`.

## The run

- 144 jobs, 0 failures, 22:57 to 05:32, two 20-minute GPU rests (after ~2 h of rendering each).
- Average render on the 3090: FLUX 3 still 26 s, FLUX 3 two-image edit 45 s, LTX first frame (5 s) 185 s,
  LTX first + last frame 194 s, LTX text to video (6 s) 236 s, MiniMax 45 s instrumental ~70 s.
- 16:9 work size 1280x768, 9:16 768x1280. The finished cut was scaled to 1920x1080 / 1080x1920.
- The rest loop (render N hours, idle 20 min) and the shot list that is re-read every cycle (`extra_shots.json`) both
  worked: hexe added shots twice while it ran, with no restart.

## What worked (hexe's picks)

- **Phone push-in, first + last frame.** First frame = a FLUX 3 photo of a hand holding a phone with a plain lit screen;
  a FLUX 3 two-image edit puts a location still on the screen ("Keep <ref_image_0> exactly ... replace only the phone's
  screen content with <ref_image_1>"); last frame = that location still. LTX pushes through the screen into the room. The
  next clip starts from the same still, so the cut is invisible. Strongest technical result; good as a stand-alone
  "check this out" piece. The plain-screen phone photos were picks by themselves.
- **The filmic look** (35mm Kodak Vision3 500T, anamorphic, low-key contrast, one motivated key, deep blacks, halation,
  heavy grain, muted earthy palette) on yoga and the tea lounge: hexe's favorite aesthetic. The commercial look (soft warm
  light) reads well but more "ad".
- **Empty spaces** (same rooms, "completely empty, no people anywhere"): clean, and they avoid people problems entirely.
- **Text-to-video landscapes** (zen rock garden, jungle waterfall, mountain valley) and the **walking-tour POVs** (gimbal,
  first person, no people).
- **hexe's monk prompt** as text to video.
- **Drone opener, first + last frame**: aerial still as first frame, a close-up of the woman on her phone in the same
  light as last frame, last frame weighted 1.0 vs 0.8. LTX did the asked-for barrel roll. hexe meant a corkscrew; for a
  real spot this needs structured camera control (see the roadmap).

## What didn't

- **Faces drift after ~6 s** in the group shots (seen ~1 s into the salt cave clip after the push-in). Keep group shots
  short, or cut on the push-in.
- **Very wide shots: people walking and birds flying move oddly.** hexe's rule from earlier LTX work: "birds chirping" in
  the prompt (audio wording) puts flying birds in the sky about a third of the time. Our retreat move said "birds crossing
  the light" and got birds. Leave birds out of prompts; put "birds" in the negative for wide shots.
- **Coast at twilight: the rocks looked like plastic.**
- **The prism / amber-glass refraction looks** (hexe's prompts): beautiful, but art pieces, not a wellness demo. Keep them
  for music videos.

## Publishing note: workflow metadata

ComfyUI's SaveImage and SaveVideo embed the full prompt and workflow (every prompt, every note) in the file: PNG text
chunks, MP4 `prompt` / `workflow` tags. Dragging the file into ComfyUI restores the graph, which is handy for us, but
raw outputs posted publicly give away the prompts. Checked: the demo cuts made by ffmpeg with a filter graph carry no
ComfyUI tags, and Nightshift's `out/pass01*.mp4` carry none either. Anything posted straight out of ComfyUI does.

## Prompt order: image vs video (hexe, Nov 9)

- **Image models: subject first, location last.** On a still, the location is the background. Nightshift's FLUX 3
  caption already does this: shot + person + outfit + action, then "Setting: ...", then style.
- **Video models: location first, like a screenplay.** Scene heading (where, when), then who is there, then what happens,
  then camera, then look and sound. In a film, the location is where the crew drives at 4 am. Nightshift's video prompts
  are free text from the plan today, so this order isn't enforced; hexe's 8-part LTX prompt assembly (to be exported as
  an API workflow) is the model for a video prompt builder.
