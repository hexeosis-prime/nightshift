# The pass, step by step

A **pass** is one complete render of the video: song, shots, cut, finish. `nightshift run` does a pass; each step below can
also be run on its own (CLI command in brackets) or by an agent over MCP (tool name in brackets).

```
sheets ─► song ─► analyze ─► timeline ─► stills ─► sheetedits ─► videos ─► pick ─► cut ─► overlay ─► finish
```

## 0. The project folder

```
my-video/
  project.json     settings: ComfyUI address/folder, sizes, workflows, mode, grade, overlay
  canon.json       characters, wardrobe per framing and world, never-lists, sheets once approved, defaults
  shots.json       the shot list (docs/shots.md)
  song/            caption.md, lyrics.txt -> song.mp3, beatmap.json, words.json, lines.json
  refs/            pictures of the characters (optional); approved character sheets in refs/sheets/
  jobs/            every ComfyUI job built, with a .meta.json (workflow, shot, seed, frames)
  sheets/ stills/ clips/ songs/    renders, named <shot>_<label>_00001_.png / <shot>_<mode>_<still>[_t<n>]_00001.mp4
  review/          contact sheets, takes sheets, A/B reels, numbered review copies
  overlay/         face tracks, data.json, frames, alpha chunks
  out/             passNN_cut.mp4, passNN.mp4, passNN_notes.md, EDLs
  queue.json       jobs submitted to ComfyUI and their state;  log.jsonl  everything that happened;  state.json  where the pass is
```

`project.json` only needs what differs from the defaults in `nightshift/project.py`. The important ones:

| key | default | |
|---|---|---|
| `comfy.url` | `http://127.0.0.1:8188` | ComfyUI's address (start ComfyUI with `--listen` to reach it from another machine) |
| `comfy.dir` | null | the ComfyUI folder, when it is on this machine: files are copied instead of uploaded, and the watchdog reads its log |
| `work_size` / `crop` / `final_size` | 1280x768 / 1280x720 / 1920x1080 | what the models render / the 16:9 window cut from it / delivery |
| `video_frames` | 121 | default clip length (LTX wants 8n+1 frames) |
| `mode` | director | or `yolo` |
| `sheets` | 3 candidates, approve, yolo from text | character sheets (step 1) |
| `takes` | `{"default": 1, "complex": 4}` | best-of-N for shots marked `"complex": true` |
| `workflows` | see `workflows/` | which graph does which job; point any role at your own export |
| `grade.look`, `grade.lifts` | `A2_portra_dusk_plus`, `[]` | see `nightshift/grade.py`; lifts are per-shot shadow lifts `[t0, t1, k]` |
| `overlay` | disabled | docs/overlay.md |
| `watchdog` | stall 6 min | when a running job counts as stuck |

## 1. sheets (`sheets status|build|pick` · `sheets_status`, `sheets_review`, `pick_sheet`)

Character reference sheets come first, before any other frame, because every identity edit and every face score depends
on them. A sheet is one image: a full-body front view with the face covered by a white circle, a full-body back view and a
macro close-up of the face, on seamless grey. For each character in the shot list:

- **First world** (the default world): three candidates (`sheets.candidates`). With a picture of the character
  (`"reference": "refs/<file>"` on the character in canon.json) they come from `sheet_from_image`, which reformats the
  picture into the sheet layout; without one, from `sheet_from_text`, using the character's `person` words and the wide
  outfit for that world. Yolo mode always uses the description (`sheets.yolo_source`).
- **Other worlds** with a different outfit: three outfit edits of the approved first sheet, so the face, hair and body stay
  the same person.

The run stops twice, `sheets_review` and `outfits_review`, with contact sheets in `review/` (director mode always; yolo mode
while `sheets.approve` is true). Pick with `nightshift sheets pick lead real sheets/lead_real_c1_00001_.png`; anything you
don't pick gets the best-scoring candidate (face quality for first sheets, face match to the first sheet for outfits). The
approved sheet is saved as `refs/sheets/<character>_<world>.png` and written into canon.json, and from then on it is reused
everywhere. A character who already has a `sheet` in canon.json is skipped.

## 2. song (`song jobs`, `song choose` · `song_jobs`, `song_choose`)

Builds one MiniMax Music 3 job per seed from `song/caption.md` and `song/lyrics.txt` (four seeds by default) and renders them.
Then each render is transcribed and scored by **lyric coverage**: the share of the lyric sheet it actually sings, in order.
Models drop and invent lines; this number tells you before you listen. Director mode stops here (`song_pick`) with
`review/songs.json`; pick with `nightshift song choose songs/<file>` and `nightshift continue`. Yolo takes the best coverage.

Already have a song (your own, or from elsewhere)? Put it at `song/song.mp3` and the step is skipped.

## 3. analyze (`analyze` · `analyze_song`)

- `song/beatmap.json`: tempo, every beat, downbeats (4/4 assumed), automatic sections, loudness, and the **loop seam** score
  (how alike the last and first 4 seconds sound, for videos meant to loop)
- `song/words.json`: word timestamps from faster-whisper (CPU is fine). A separated vocal stem transcribes better:
  `nightshift analyze --stem vocals.wav`
- `song/lines.json`: the lyric sheet aligned to what was heard. The sheet's words, the measured timing; words the
  recogniser missed are spread across their line. The overlay prints these.

## 4. timeline (`timeline resolve` · `resolve_timeline`)

Fits the song-agnostic shot list to this song (writes `shots_resolved.json` and `cut.json`):

- a shot with `"anchor": "first words of a line"` starts just before that line (minus `lead` seconds). Anchors are matched in
  order, so the third "What do you want" lands on the third one
- shots between anchors share the gap (lip-sync shots weigh 2), cut points snap to beats within 0.35 s
- slots under 1 s are dropped and their time goes to the neighbour; over 12 s gets a warning (15 s for `"fit": true` shots)
- every shot is rendered at exactly its slot length (8n+1 frames): no frozen tails, no wasted frames
- lip-sync and first/last-frame shots get the song as audio from their slot start, and the words sung in the slot

Edit `shots.json` and run it again any time; `cut.json` keeps the takes you already picked.

## 5. stills (`build stills` · `build_jobs stage=stills`)

One text-to-image job per shot that needs a first frame (modes `ff`, `lipsync`, `fflf`). The prompt is assembled from the
canon: the character's identity words, the outfit for this framing (shoes only in a wide) and this world, the shot's action
and location, the world's style switches. Never-lists go to the negative. Renders land as `stills/<id>_flux_00001_.png`.

Your own still for a shot: `stills/<id>_<label>_00001_.png` (or `nightshift.takes.drop_in`) and set the shot's `"still"` to
the label.

## 6. sheetedits (`build sheetedits`, `variants` · `build_jobs stage=sheetedits`, `identity_variants`)

For shots with `"still": "edit"`: a two-image Flux edit takes the shot's still (image 1: pose, framing, light) and the
character sheet (image 2: face, hair, body, wardrobe) and returns the same frame with the right person in it. `"add"`
brings a second character in with a third image. Two wordings exist (`"wording": "A"` or `"C"`, see docs/prompting.md);
`variants` renders a seed x wording grid so the face scorer can pick.

Director mode stops here (`stills_review`) with contact sheets of every first frame ranked by face match.

## 7. videos (`build videos`, `takes` · `build_jobs stage=videos`, `make_takes`)

One LTX 2.3 job per shot, by mode:

| mode | graph | what it is for |
|---|---|---|
| `ff` | first frame | the still comes alive: dance, walk, camera move |
| `lipsync` | first frame + song section | singing; the vocal is separated in the graph and drives the mouth |
| `fflf` | first + last frame (+ song audio) | planned moves: push-ins, fly-overs, reveals, loop seams, and singing that has to land on a frame |
| `t2v` | text only | aerials, timelapses, establishing shots |
| `reuse` | none | an existing clip (`"src"`) |

Shots with `"takes": n` (or `"complex": true`) are cloned into n seeds (base + 1000·i) and all rendered.

## 8. pick (`timeline pick` · `rank_takes`, `takes_sheet`, `pick_take`)

Every take of a person shot is scored against the character sheet (median of three frames; lip-sync takes also get a mouth
activity number) and the cut points at the best one. Director mode stops (`takes_review`) with a contact sheet per shot
(first/middle/last frame of every take); with one take per shot (the `short` profile) there is nothing to choose and it
doesn't stop. Override with `nightshift timeline pick <shot> clips/<file> [--in 0.5] [--speed 2]`;
a hand pick is never overridden by the scorer again.

## 9. cut (`assemble` · `assemble_cut`)

`cut.json` is the edit: per shot a source and a length in `beats` (ends on the Nth beat after it starts) or `seconds`, plus
`in` (trim the head) and `speed` (2 = double speed; 0.94 = stretch a slightly short clip instead of freezing its tail). Each
shot is conformed, cropped to 16:9 and scaled in one generation into a cached segment; the segment name carries a fingerprint
of its settings, so after a change only that shot re-encodes. The song goes under the picture and an EDL (CSV) is written.

## 10. overlay (`overlay track|prep|render|encode` · `overlay_build`)

Optional lyric HUD. See docs/overlay.md.

## 11. finish (`finish` · `finish_video`)

Grade (a look + per-shot lifts), the overlay keyed on top, a halftone multiply and film grain, rendered in 9-second chunks
(resumable; a late change only re-renders its chunks), joined with the song. Then a numbered review copy
(`review/passNN_review_numbered.mp4`, shot numbers burned in so notes can say "shot 26") and `out/passNN_notes.md`.
`--web` adds a posting copy (14 Mb/s keeps 3 minutes of 1080p under X's 512 MB).

Director mode stops (`pass_review`). Notes go to the agent (or you), shots get patched, `nightshift next-pass`, run.

## Running pieces by hand

```bash
nightshift build videos --ids s06,s07              # rebuild two shots' video jobs
nightshift takes jobs/s06_video.json -n 4          # best-of-4
nightshift submit "jobs/s06_video_t*.json" --watch
nightshift score takes --shot s06                  # ranked
nightshift review takes s06                        # contact sheet -> review/takes_s06.jpg
nightshift timeline pick s06 clips/s06_lipsync_edit_t2_00001.mp4
nightshift assemble --out out/pass02_cut.mp4
nightshift finish out/pass02_cut.mp4 out/pass02.mp4 --halftone overlay/halftone.png --web
```
