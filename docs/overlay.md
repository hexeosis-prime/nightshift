# The lyric HUD overlay

An optional graphic layer: the lyric being sung, word by word on a scrolling colour gradient, placed where no face is;
brackets that lock onto faces; shot and section labels, a beat light, a waveform, a ruler, a ticker, timecode. Everything is
a pure function of the frame number, drawn on an HTML canvas and rendered frame by frame in headless Chromium, so the same
frame always renders the same way and any range can be re-rendered.

```
overlay track    face boxes per source clip (YuNet; smoothed; short gaps bridged; cuts respected)
overlay prep     map faces through the edit; gather lyrics, loudness, beats, shots, sections, style -> overlay/data.json
overlay render   PNG frames (transparent) -> overlay/frames/
overlay encode   VP9-with-alpha chunks of 9 s -> ov_00.webm ...   (finish keys them over the cut)
```

Turn it on in `project.json`:

```json
"overlay": {
  "enabled": true,
  "sections": [{"name": "THE SEED"},
               {"name": "THE FORECAST", "line": "They draw the lines"},
               {"name": "THE RETURN", "after": "Is the answer"}],
  "style": {
    "title": "WHAT DO YOU WANT",
    "label": "LOOP 01",
    "hero": "^what do you want$",
    "face_label": "SUBJECT 01  ·  UNFORECAST",
    "ticker": ["FUTURE STATUS: UNWRITTEN", "QUESTION 01: WHAT DO YOU WANT?", "THE LOOP IS OPEN"],
    "slot_by_shot": {"c02": "bl"}, "slot_by_line": {"a solved world": "bl"}, "dy_by_line": {"is the answer": -95},
    "bounce_shots": ["v01"], "no_box_shots": ["p01", "p02"],
    "widgets": {}
  }
}
```

Sections start at a lyric line (`line`, optionally `occurrence`), at the first line after another (`after`), at a time
(`t`), or at 0. Each section gets an accent colour (`accents` to set them, otherwise a palette cycle).

**Style keys:** `title` (top right), `label` (bottom left), `palette` (12 colours for the lyric gradient), `hero` (regex: lines
that get the big condensed treatment, the song's question for example; a trailing ? bounces on the beat), `face_label`,
`show_face_score`, `ticker` / `ticker_after` (tokens `{value}`, `{count}`, `{conf}`, `{n}`), `slot_by_shot` / `slot_by_line`
(force a corner: `tl`, `bl`, `ml`, `tr`), `dy_by_line` (nudge a line up or down in pixels), `bounce_shots` (lyric words hop
on the beat, `bounces` hops then settle), `no_box_shots` (no face brackets; faces still steer the lyrics), `calm` (CSS filter
on everything but the lyrics), `intro` / `outro` timing (graphics build on at the head and leave before the end for a clean
loop seam).

**Widgets** (all optional):

- `expand_line`: `{"shot": "v01", "word": "draw", "x": 1440, "y": 540}`: a short stub that stretches edge to edge as the word
  is sung.
- `merge`: `{"lines": ["They say you'll merge", "Absorbed into one", "Until nothing cuts"], "exit_shot": "p04", "early": 0.4}`:
  coloured dots that fall together into one blob over three lines, go grey, and dissipate. Placed on whichever side has no
  face.
- `illustrations`: `[{"shot": "o03", "items": [{"name": "robot", "side": -1, "cy": 300, "h": 250, "at": 12.4}, ...]}]`:
  luma-keyed line art beside the singer, landing on beats or at set times (time them to head turns with
  `nightshift score yaw`). Static images come from `overlay.illus` (`{"robot": "refs/robot.png"}`); animated ones from
  `nightshift.overlay.illus.key` (animate a still with an `ff` job, then key it). An item with `"puzzle": true` assembles cell
  by cell and drains to grey from `grey_shot`.
- `readout`: a number that climbs on the beat through some sections, scrambles at a break section, and becomes a "?":
  `{"title": "FORECAST  ·  P(DOOM)", "start_section": "THE FORECAST", "climb": {"THE FORECAST": [0.006, 0.012]},
  "break_section": "THE BLOOM", "states": {"live": "MODEL 07  ·  LIVE"}}`.

Fonts are JetBrains Mono, Barlow Condensed and Inter (installed by `npm install` in `nightshift/overlay/web`).
Rendering ran at about 20 frames a second in our tests (the merge widget's frames are slower), so a 3-minute video
(~4,000 frames) takes a few minutes. Ranges re-render on their own: `nightshift overlay render --first 1200 --last 1500`.
