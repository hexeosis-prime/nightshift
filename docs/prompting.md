# Prompting the three models

The short version, from what worked on the first video. The full guides:
[MiniMax Music 3](guides/minimax-music-3-prompting-guide.md) (Zero and Gemini Argon) ·
[Flux 2 Klein](guides/flux2-klein-prompting-guide.md) (Zero) ·
[LTX 2.3](guides/ltx-2.3-prompting-guide.md) (Erik and Zero), each reviewed and edited by Claude Opus 5.5.

## MiniMax Music 3 (the song)

The model takes a **caption** (the production brief) and **lyrics** (the words with section tags). Both live in the project:
`song/caption.md` (headings and `<!-- comments -->` are stripped) and `song/lyrics.txt`.

A caption that works reads like a producer's brief, in this order:

1. **Global metadata**: genre in specific words (not "pop": "warm late-night synth pop with a dusty drum machine"), BPM, key,
   the mood arc in a sentence, the production texture.
2. **Vocal details**: who sings, their range and timbre, how each voice is treated and where it changes.
3. **Arrangement**: timestamped sections saying what enters, what drops out and what the voice does.

What we learned writing the first song:

- **Ask for treatment positively and concretely.** "Erosion", "granular", "dissolving into delay" were taken literally:
  the vocal came back distorted and bit-crushed. "Lush natural reverb, a large warm hall and plate, nothing distorted,
  saturated or bit-crushed" got the spacious sound that was meant.
- **Two voices need casting, not just description.** Describing the rapper in the caption's vocal section did not reliably
  give a distinct second voice. What worked: a casting note at the very top of the caption ("THIS SONG HAS TWO DIFFERENT VOCALISTS. A
  FEMALE SINGER sings everything except one section. A MALE RAPPER ... raps the section tagged as the male rapper verse, ALONE.
  The female singer does not sing or double those lines.") and naming the singer in that section's tag
  (`[Rap Verse - Male Rapper]`). `nightshift.song.tag_singers` renames tags for you.
- **For a looping video, ask for a long natural decay at the end** ("the pad rings out over eight to ten seconds, no hard
  ending"); then check the loop seam score in `song/beatmap.json`.
- **Render four seeds and read the lyric coverage** (`review/songs.json`) before listening: some renders drop or invent
  whole lines.
- **Revise captions with `replace_once`.** Revisions are search-and-replace on a long text; a pattern that silently doesn't
  match is how a fix gets lost. `nightshift.song.replace_once` refuses anything but exactly one match.

`max_seconds` caps the length (the graph's default is 280). Expect up to ~30 minutes per seed on a 3090.

More in the [MiniMax Music 3 guide](guides/minimax-music-3-prompting-guide.md).

## Flux 2 Klein 9B (first frames and edits)

Klein reads full sentences (its text encoder is Qwen3 8B) and does no prompt upsampling, so what you write is all it gets:
specific beats vague, and positive steering beats negative lists.

**Stills.** The still prompt is assembled from the canon, so one character reads identically in every shot:
identity words (`person`) + the outfit for this framing and world + the shot's `action` (end it with a lens: "85mm lens")
+ `location` + the world's style switches. Lens, light source and time of day do more than adjectives
("sodium street lamps", "a single flickering floodlight", "harsh flickering fluorescent tubes").

**Identity edits** (image 1 = the shot's still, image 2 = the sheet). Two wordings ship:

- **A** (`[reference_image1]` phrasing): "using [reference_image1] as the base, update the appearance of the woman to match the
  film character sheet from [reference_image2] using accurate face, hair, body proportions and clothing carried over exactly
  ... keep the exact same pose, body position, camera angle, framing, lens, lighting, colors and background ..."
- **C** (Black Forest Labs' own "image 1 / image 2" naming plus an exhaustive preservation clause): "Modify image 1 using
  image 2 for reference. Replace the woman in image 1 with the woman from the film character sheet in image 2, carrying over
  her exact face, facial structure, eyes, nose, mouth, jawline, hair, body proportions and clothing from image 2 ...
  Preserve image 1 exactly: the pose, body position, hand positions, camera angle, framing, lens, lighting direction and
  color, background and composition stay unchanged."

Neither wins everywhere: render both (`variants`) and let the face scorer pick. Append light changes to the same edit
(`edit_light`: "A directional red fill light hits the left side of her face.") rather than doing a second pass.

**Free edits** (`nightshift edit`): name images by position ("image 1", "image 2"), say what changes, then list everything
that must not change. Season changes, relights from a reference frame, removing people, a second character from a third
image.

More in the [Flux 2 Klein guide](guides/flux2-klein-prompting-guide.md).

## LTX 2.3 (video)

**One continuous moment, described in order:** shot size and subject (the identity words, via `{lead}`), where, what
happens first and then, and what the camera does. "Medium shot of {lead} walking toward the camera down a wet avenue at
night. She stops and looks back over her shoulder. The camera tracks backward in front of her, steady."

- **Name the camera move.** Dolly, push in, arc, crane up, handheld drift, static. Without one, LTX picks for you.
- **Light that moves sells the shot:** flickering tubes, sweeping beams, passing headlights.
- **The negatives that mattered** are built in per mode: scene cuts, spinning or turning around (LTX loves a 180° turn),
  extra people, microphones on singers, subtitles and text.
- **Lip-sync prompts** get the words as well as the audio: `The woman sings the lyric words "..."` followed by
  `([woman], [singing]): "...", warm, expressive singing style`. If quoting the words burns in subtitles, set `no_lyric`.
- **Text-to-video** is for shots without people: aerials, timelapses, weather. "Fast, smooth, cinematic camera movement"
  at the end helps.
- **First/last frame** shots: describe the motion between the two frames, not the frames. If the two frames differ in more
  than what should change, LTX will morph whatever differs (see techniques: self-consistent last frames).

More in the [LTX 2.3 guide](guides/ltx-2.3-prompting-guide.md).
