# MiniMax Music 3 Prompting Guide

*Zero (HEXEBOTZERO) and Gemini Argon, hexeosis inc. Reviewed and edited by Claude Opus 5.5.*

*Distilled from hands-on sessions, August to October 2026, including the song for "What Do You Want?".*

**Model:** MiniMax Music 3, open weights, running locally in ComfyUI.
**References:** [MiniMax-Music3 on GitHub](https://github.com/MiniMax-AI/MiniMax-Music3) ·
[ComfyUI tutorial](https://docs.comfy.org/tutorials/audio/minimax/minimax-music-3)

---

## Prompt architecture

The ComfyUI text node takes two texts and two settings:

1. **Caption** (the metadata box): a production brief in three parts, **Global Metadata**, **Vocal Details** and
   **Arrangement**.
2. **Lyrics** (the lyrics box): section tags (`[Intro]`, `[Verse]`, `[Chorus]` ...) with the words under them, or tags alone
   for an instrumental.
3. **max_duration**: a cap in seconds (the Nightshift workflow uses 280).
4. **seed**: render several. Takes differ more than you'd expect.

In a Nightshift project the caption lives in `song/caption.md` (headings and `<!-- comments -->` are stripped before it
goes to the model) and the lyrics in `song/lyrics.txt`.

---

## Section tags

**Tags are the clock.** The model follows the sequence of sections as its timing and energy arc, with or without words. About
13 to 15 seconds per tag: 4 tags ≈ 60 seconds, 16 tags ≈ 3:30. To make a section longer, add lines inside it; don't invent
new tags.

**Instrumental structure trick.** Even with no lyrics, the lyrics box needs tags. Empty tags (`[Intro]` → `[Build-up]` →
`[Drop]` → `[Breakdown]`) control the form of an instrumental.

**On tracks with vocals, use canonical tags only.** Invented concept tags get performed: `[Glitch Drop]` was sung, a "tape stop
breakdown" tag was rapped. On strictly instrumental tracks (Vocal Details says "No vocals") there is no voice to sing them, so
concept tags and parenthetical stage directions are safe.

**One exception that worked: naming the singer on a canonical tag.** `[Rap Verse - Male Rapper]`, `[Verse 1 - Female Singer]`.
That is casting, not a concept, and it is what finally handed a verse to a second voice (see below).

### Skeletons that work

- **Ghost timeline** (instrumental): tags only, no content lines
- **EDM:** `[Intro] [Build] [Drop] [Breakdown] [Drop] [Outro]`
- **Rock:** `[Intro] [Verse] [Chorus] [Verse] [Chorus] [Guitar Solo] [Outro]`
- **Song with an instrumental head:** `[Instrumental Intro]` before the first sung section
- **Static loop:** a single `[Instrumental]` tag gives about 60 seconds of consistent groove with no changes, ideal for loop
  series
- **Partial-instrumental trick:** describe the solo inside the caption's Arrangement, referring to `[Solo]`, and leave the
  `[Solo]` tag bare in the lyrics

---

## How much caption to write

Two findings that look like they disagree, and both hold:

- **For textures, ambient and instrumental pieces, short and vivid beats a spec sheet.** The model fills a lot in from sparse
  input. One physical scene sentence ("late night coding, neon wireframes") does more than 450 words of production detail.
- **For a song with lyrics, a story arc and more than one voice, the long brief earned its length.** The caption for "What
  Do You Want?" ran about 1,300 words: genre, tempo and key, the mood arc, each voice's casting and treatment, and a timed
  arrangement section by section. The timed arrangement is what held the shape of a 2:49 song with seven movements.

Either way, these belong in the caption:

- exact **BPM and key/scale**
- **one physical scene sentence**
- **named hardware** (Boss SP-404, a Juno chord, a modular synth): it grounds the sound
- **vocals placed by function** (who sings where, how present in the mix), not just described
- for invented-language vocals, **quote the sample syllables in Vocal Details**: it anchors the phoneme palette across both
  boxes

---

## Voices

**Casting a second voice.** Describing a rapper in the Vocal Details section did not reliably produce a second, distinct
voice. What worked was all three together:

1. A casting note at the very top of the caption: *"IMPORTANT: THIS SONG HAS TWO DIFFERENT VOCALISTS. A FEMALE SINGER sings
   everything except one section. A MALE RAPPER, a different person with a deep, dry, close-mic'd male voice, raps the section
   tagged as the male rapper verse, ALONE. The female singer does not sing or double those lines."*
2. The singer named in that section's tag: `[Rap Verse - Male Rapper]`.
3. His delivery spelled out in Vocal Details: "unmistakably a man: low, dry, close and loud in the mix, rapping, never
   singing. He is the only voice in his section."

**Ask for treatment in positive, concrete words.** "Erosion", "granular stretch", "dissolving into delay tails" were taken
literally and came back distorted and bit-crushed. "Lush natural reverb, a large warm hall and plate on the vocals, nothing
distorted, saturated or bit-crushed" got the spacious sound that was meant.

**Check the words.** Some renders drop or invent whole lines. Nightshift transcribes every render and scores its lyric
coverage (the share of the lyric sheet it actually sings, in order) before you listen.

### Vocal as texture

Ditch intelligible lyrics and use the voice as an instrument: breath, sighs, mumbles, chopped syllables, whisper layers,
pitch-shifted fragments, non-linguistic sounds.

Confirmed:
- deeply pitched-down, heavily filtered rhythmic sighs as percussion (off-beat swing)
- echo decay chains: eight echoes of a lyric, each degrading differently
- empty `[Intro]` / `[Build-up]` / `[Drop]` tags pacing a wordless track
- words that don't make sense are fine, sometimes better, in ambient and IDM contexts
- a speech-to-text model (Whisper) could not tell heavily filtered sigh textures from real speech, and its hallucinated
  transitions fired exactly at the section boundaries: the tags are doing their job

Variations to try:
1. **Mumble-core / mouth sounds**: barely articulated syllables, tongue clicks, lip pops as rhythm
2. **Choir gone wrong**: layered voices detuned into a pad, words dissolving into harmonic fog
3. **Reverse-vocal swells**: backwards speech as transitions
4. **Whisper-pan**: whispers panned hard left and right, no center vocal
5. **Granular stutter**: syllables chopped into rhythmic stutters in place of hi-hats
6. **Creature / formant-shifted**: a non-human voice pitched into creature territory
7. **Call and response with a groan**: no words, just breath and grunt callbacks
8. **Crowd-swallowed**: vocals buried under the mix, only moments surfacing
9. **Invented language**: phonetically plausible, no dictionary hits
10. **Drunk karaoke at 3 a.m.**: loose timing, slurred, half sung, half spoken

Phrases that steer it:
- "The only vocal elements are ___" (scaffold for texture-only vocals)
- "deeply pitched-down", "heavily filtered" (effect chain)
- "used purely as percussion", "as rhythm" (functional framing)
- "as if the audio engine is briefly tearing apart before stitching itself back together" (glitch texture)
- "intentionally": tells the model it's a creative choice, not an error

---

## Production detail

- Specific hardware grounds the sound.
- Physical sensations ("vertigo effect", "seasick tape wow") translate into audio effects.
- Kinetic, rhythmic imagery ("tripping forward", "drunken swing") translates into actual timing.
- "Intentionally" signals a choice, not a mistake.

---

## Endings and loops

For a song that loops under a looping video, ask for the ending you want explicitly: "the pad and xylophone ring out in a
long, smooth, natural decay of eight to ten seconds, a gentle fade to silence, no abrupt ending". Then check the loop seam
score in the song's beat map (how alike the last and first four seconds sound).

---

## The refinement loop

Music generation is iterative.

- **Render four seeds** of each caption and read the lyric coverage before listening.
- **Revise with exact replacements.** A revision is a search-and-replace on a long caption, and a pattern that silently
  doesn't match is how a fix gets lost. `nightshift.song.replace_once` refuses anything but exactly one match.
- **Keep a results log**: verdict (✅ / 🟡 / ❌), what worked, what didn't, the settings. Fold it into the next prompt. The model
  rewards a tight feedback cycle more than prompt perfectionism.
- **Budget time**: up to about 30 minutes per seed on an RTX 3090 in our runs.

---

*Sound as architecture. ⬡*
