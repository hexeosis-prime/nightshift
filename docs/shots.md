# Shot fields

`shots.json` is a list of shots in edit order. Only `id`, `mode` and a prompt are required; everything else has a default.
The timeline step adds the timing fields (marked *resolved*) to `shots_resolved.json`; don't write those by hand.

## Identity and placement

| field | example | |
|---|---|---|
| `id` | `"c02"` | short and unique; it names every file the shot produces |
| `section` | `"chorus"` | free text, for you |
| `mode` | `"lipsync"` | `ff`, `fflf`, `lipsync`, `t2v`, `reuse` (docs/pipeline.md) |
| `anchor` | `"Tell me what you're chasing"` | first words of the lyric line this shot starts on (lip-sync shots, and any shot that must hit a line) |
| `lead` | `0.8` | start this many seconds before the anchor (a run-up into the line) |
| `fit` | `true` | allows a long slot (15 s instead of 12): first/last-frame moves, intros, loop seams |
| `voice` + `fallback_mode` | `"male"`, `"ff"` | if the chosen song has no such voice (`project.json` `song_voices`), the shot becomes `fallback_mode` |
| `takes` / `complex` | `4` / `true` | best-of-N; `complex` uses `project.json` `takes.complex` |
| `dropped` | `true` | leave the shot out (the timeline also drops slots under 1 s) |

## The first frame

| field | example | |
|---|---|---|
| `chars` | `["lead"]` | characters in the shot (keys of `canon.json` `characters`); the first one drives the prompt and the identity edit |
| `world` | `"stage"` | picks `outfit_<world>`, `video_name_<world>`, the world's still model and style switches, and which sheet to use |
| `framing` | `"close"` | `close` / `medium` / `wide`: picks the outfit text (shoes only in wide) and the close-up prefix |
| `action` | `"leaning on the rooftop ledge, singing, 50mm lens"` | what the person is doing, plus the lens |
| `location` / `location_extra` | | overrides the world's/canon's default location / adds to it |
| `switches` | `{"daytime": true}` | style switches for the still workflow (`safe`, `pro_photo`, `bad_photo`, `pov`, `indoor`, `daytime`, `atmosphere`, `suffix`) |
| `seed` | `3022` | every seed is fixed; takes use seed + 1000·i |
| `still` | `"edit"` | which still the video starts from: an output name (`flux`, `edit`) or any label of a file in `stills/<id>_<label>_*` |
| `edit_base` | `"flux"` | which still the identity edit starts from |
| `expr` | `"warm smile, lips closed, about to sing"` | facial expression for the identity edit |
| `wording` | `"C"` | identity edit wording (A: reference-image phrasing, C: BFL "image 1 / image 2" phrasing with exhaustive preservation) |
| `sheet_ref` | `"refs/lead_face.png"` | a different reference than the world's sheet (a smiling sheet, a close-up face portrait) |
| `edit_light` | `"A directional red key light hits the left side of her face."` | appended to the identity edit: relight in the same pass |
| `add` | `{"char": "second", "where": "standing behind her on the left", "expr": "grinning"}` | second character via the three-image edit |
| `edit_ref` + `edit_prompt` | | a free two-image edit (stage `edits`) |
| `still_from` | `"s01"` | reuse another shot's still (the loop seam: the last shot ends on the first shot's frame) |
| `first_frame` | `"refs/my_frame.png"` | a file as the first frame, skipping the still stages |

## The video

| field | example | |
|---|---|---|
| `video` | `"Close-up of {lead} under a street lamp ..."` | the motion prompt. `{lead}` becomes the character's `video_name`, so identity words are identical in every shot |
| `frames` | *resolved* | slot length in frames (8n+1) |
| `audio`, `audio_start`, `lyric` | *resolved* | the song, where the slot starts in it, and the words sung in the slot |
| `no_lyric` | `true` | don't quote the lyric in the prompt (quoted words burned subtitles into a few shots) |
| `negative_extra` | `"wink, closed eyes"` | added to this shot's negative prompt |
| `start_shot` / `end_shot` / `end_still` | `"v06rA"` | first/last frame from other shots' stills (`fflf`) |
| `last_frame` | `"stills/v06_lf.png"` | a file as the last frame (`fflf`), e.g. a frame taken from a take itself |
| `arrive_frame` | `64` | `fflf`: land the last frame at this frame (multiple of 8) instead of the end; the performance runs free after it |
| `arrive_strength` | `0.7` | how hard the last frame pulls (0.6-0.9 works) |
| `src` | `"clips/old_take.mp4"` | for `reuse` shots |

## The edit (in cut.json, not shots.json)

| field | |
|---|---|
| `src` | the take used |
| `beats` / `seconds` | slot length: ends on the Nth beat, or plain seconds; the last shot runs to the end |
| `in` | seconds trimmed from the head of the take |
| `speed` | 2 = twice as fast (a busy montage), 0.94 = stretched to fill a slot |
| `picked` | set by `timeline pick`: the scorer leaves this shot alone |
