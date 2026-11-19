# MiniMax Music 3: songs and background beds

_hexe's MiniMax M3 guide and song library (Nov 18), with what Nightshift learned writing and ranking songs. Tags:
**[FIELD]** tested here; **[OFFICIAL]** from MiniMax or ComfyUI; **[EXPERIMENT]** not proven._

MiniMax Music 3 runs locally in ComfyUI (`song_minimax_m3`). It takes two texts: a **caption** (the production brief) and
**lyrics** (the words with section tags). In a project they live in `song/caption.md` (headings and `<!-- notes -->` are
stripped before it goes to the model) and `song/lyrics.txt`.

## 1. The caption: three paragraphs and a timeline

Write it like a producer's brief:

```text
Global Metadata: [Decade/era + sub-genres]. [Exact BPM + feel], [key + mode or chord color]. [Emotional arc + one
concrete visual scene]. [Studio: room acoustics, separation, hardware, EQ and bus compression].

Vocal Details: [Who sings: gender, range, delivery, phrasing]. [Mic technique, pitch correction, reverb/delay chain,
where it sits in the mix]. (Or: "No vocals. Strictly instrumental.")

Arrangement: [Drums: kit or samples, quantization or swing, kick and snare]. [Low end: instrument, technique, amp].
[Melodic bed: guitars, synths, acoustic instruments, pedals, panning]. [Optional: what each section adds or drops.]

[A structural timeline with section tags, (parenthetical cues) and lyrics]
```

- **Genre in specific words.** Not "electronic" or "rock": "late-1970s cold post-punk with a cavernous room sound",
  "1990s drill 'n' bass, braindance".
- **Lock tempo and key together**: "80 BPM, F major with jazzy 7th and 9th extensions", "138 BPM, D minor", "80 BPM with a
  half-speed 40 BPM drag feel", "free tempo, no grid" for spoken word or ambient.
- **One visual anchor** sets the atmosphere: "an abandoned factory, staring at a concrete wall", "late-night coding, neon
  wireframes".
- **The studio and mix bus**: "a large concrete room, high separation, dry early reflections"; "an SP-404 workflow:
  extreme sidechain ducking to the kick, low-passed, vinyl crackle, tape hiss, slight wow and flutter".
- **Describe genres, don't name artists.** "Cold post-punk, deadpan baritone" works; a band's name may be ignored or
  refused, and a public repo shouldn't carry it.
- **[FIELD] Nightshift checks length:** a planner-written caption under 80 characters is refused. Captions of a few
  hundred words are normal.

### Vocal details that work

- **Engineer the voice**: "detached baritone, low chest resonance, deadpan phrasing with sudden strained dynamics,
  close-miked dynamic microphone, light tape saturation, no pitch correction, a cold plate reverb with long pre-delay,
  sitting low in the mix like another instrument."
- **Buried unison**: "two whispered voices, male and female, in unison, buried at the level of the guitars, drenched in
  reverse reverb and soft tape delay."
- **Bright pop lead**: "bright chest voice rising into an airy head voice, crisp modern tuning, tight stacked harmonies on
  the hook, short-room vocal compression."
- **Vocal textures without singing**: "No lead vocals. Distant wordless sighs in a huge shimmer reverb, buried like a pad"
  or "pitch-shifted vocal chops used only as percussion."

### [FIELD] What we learned on the first songs

- **Ask for treatment positively and concretely.** "Erosion", "granular", "dissolving into delay" were taken literally:
  the vocal came back distorted and bit-crushed. "Lush natural reverb, a large warm hall and plate, nothing distorted,
  saturated or bit-crushed" got the spacious sound that was meant.
- **Two voices need casting, not just description.** Put a casting note in capitals at the very top ("THIS SONG HAS TWO
  DIFFERENT VOCALISTS. A FEMALE SINGER sings everything except one section. A MALE RAPPER raps the section tagged as the
  male rapper verse, ALONE. The female singer does not sing or double those lines."), and name the singer in that
  section's tag: `[Rap Verse - Male Rapper]`. `nightshift.song.tag_singers` renames tags for you.
- **For a looping video, ask for a long natural decay**: "the pad rings out over eight to ten seconds, no hard ending".
  Then check the loop seam score in `song/beatmap.json`.
- **Revise captions with `replace_once`.** A pattern that silently doesn't match is how a fix gets lost;
  `nightshift.song.replace_once` refuses anything but exactly one match.

## 2. Lyrics and the timeline

- **Section tags on their own lines**: `[Intro]`, `[Verse 1]`, `[Chorus]`, `[Bridge]`, `[Outro]`. With two singers, name
  the singer in the tag: `[Chorus - Male Singer]`.
- **Short singable lines**, 4-8 words. Original words only.
- **(Parenthetical cues)** inside the timeline steer instruments and mix: `(Drums suddenly stop)`, `(Acid bassline fades in,
  filtering up)`.
- **Standard skeletons**:
  - rock or pop: `[Intro] [Verse] [Chorus] [Verse] [Chorus] [Guitar Solo] [Outro]`
  - EDM: `[Intro] [Build] [Drop] [Breakdown] [Drop] [Outro]`
  - lo-fi beat tape: `[Intro] [Beat Drops] [Verse 1] [Breakdown] [Beat Drops] [Outro]`
  - a steady 60-second loop: `[Instrumental]`
- **An instrumental solo inside a vocal song**: in the Arrangement paragraph, "During the [Solo] section the vocals stop
  completely and an overdriven guitar plays a fast melodic solo before the Outro"; in the timeline, an empty `[Solo]` tag
  between the last chorus and the outro.

### Instrumentals still need a "ghost timeline"

With no words, still give the section skeleton with cues, so the track builds, drops and resolves:

```text
[Intro]
(Warm, floating ambient synth pads)

[Build-up]
(Fast stuttering snare rolls begin)
(Acid bassline fades in, filtering up)

[Drop]
(Explosive chopped breakbeats)
(Aggressive squelching acid bass)

[Breakdown]
(Drums suddenly stop)
(Return to floating ambient synths, subtle tape echo)

[Drop]
(Breakbeats return at double speed)

[Outro]
(Sudden hard stop)
```

Nightshift's abstract and instrumental projects write `[Intro] [Instrumental] [Build] [Drop] [Outro]` and a caption that
says "instrumental, no vocals"; the song step then skips the lyric check and the cuts follow the beats.

## 3. Background beds for video and voice-over

Music under a voice or a looping visual must not peak. Say so outright:

```text
Maintain a consistent energy level and a flat dynamic profile throughout the piece, ensuring there are no climaxes,
sudden shifts, or builds so it functions as a seamless background bed.
```

Example (hexe's library):

```text
Compose a gritty, mid-tempo desert-blues instrumental featuring raw acoustic slide guitar, a steady percussive shaker, and
an atmospheric, low-end drone. The track should evoke a weathered and desolate mood, mirroring a sun-bleached,
post-apocalyptic landscape of rusted classic cars and dusty industrial ruins. Maintain a consistent energy level and a
flat dynamic profile throughout the piece, ensuring there are no climaxes, sudden shifts, or builds so it functions as a
seamless background bed.
```

**[EXPERIMENT] Progressive decay.** For evolving, avant-garde pieces: a caption with a multi-section trajectory ("seven
sections, Intro, Chant, Drift, Choir, Erosion, Vowel Field, Outro, echoed syllables that degrade darker each repeat") and
phonetically spelled lyrics that lose their consonants as they go (`Aeveleu shimorae...` to `Aaaa... euuu...` to
`Haa... O...`).

## 4. A full example (instrumental, from hexe's library)

```text
Global Metadata: Classic underground lo-fi hip hop, chillhop instrumental. 80 BPM, Key of F major (with jazzy 7th and 9th
extensions). Relaxed, dreamy state, evoking a cozy bedroom studio on a rainy night. Production is heavily degraded and
nostalgic: low-passed EQ with rolled-off highs, heavy vinyl crackle, tape hiss, and subtle wow-and-flutter pitch wobble.
Extreme sidechain compression ducking the entire mix to the kick drum for a heavy pumping groove.

Vocal Details: No vocals. Strictly instrumental.

Arrangement: The rhythm section is a dusty, sampled boom-bap drum loop with a soft, rounded kick drum and a crisp, dry
snare. The hi-hats are slightly unquantized, dragging lazily behind the beat with organic swing. A deep, warm sub-bass
mirrors the root notes of the chords. The melodic bed is a looped, warm analog synth pad and a vintage Rhodes electric
piano playing slow, melancholic jazz chords.

[Intro]
(Heavy vinyl crackle and rain sounds begin)
(Warm Rhodes piano plays a solitary chord progression)

[Beat Drops]
(Dusty boom-bap drum loop enters)
(Deep sub bass and warm synth pads fade in)

[Breakdown]
(Kick and snare suddenly drop out)
(Rhodes piano and vinyl crackle remain)

[Beat Drops]
(Drums return with a subtle jazz guitar lick over the synth pads)

[Outro]
(Drums fade out)
(A final Rhodes chord slowly detunes and warbles to silence)
```

## 5. Trigger words: analog gear and pedals

`heavy analog chorus pedal` · `slapback tape delay` · `overdriven tube amp on the edge of breakup` · `slight tape warble
and wow/flutter` · `SP-404 bitcrush on vocal tails` · `seasick tape wow, beating detune harmonies` · `vinyl-brake tape
stops` · `extreme sidechain compression ducking the entire mix to the kick drum`

## 6. Rendering and picking a take in Nightshift

- **[FIELD] Render several seeds** (`song_seeds`, four by default) and let Nightshift rank them by **lyric coverage**:
  Whisper transcribes each take and measures how much of the lyric sheet is actually sung; takes that sing every line are
  ranked by **clarity** (how confidently the words were heard). The top take is picked; listen before a long render.
- **[FIELD] How the words are heard (fixed Nov 19).** Whisper's voice-activity filter cut sung lines over music, and the
  lyric sheet given as a prompt made it skip ahead and echo lines back at one instant: one Nov 18 song showed 2 of 6
  lines timed, and the takes scored 21-86% though all four sang every line. Nightshift now transcribes without the voice
  filter, once without and once with the lyric prompt, drops echoed bursts, repeats and zero-confidence words, and keeps
  the pass that times more lines. The same song: 6 of 6 lines, starts within 0.2 s of the words' own timing.
- **[FIELD] Speed on a 3090**: about a minute per take for a 40-second song; about 7-8 minutes for a 3-minute track.
- **`max_seconds`** caps the length (`song_max_seconds` comes from the project length: 40 s for a short).
- **Lyric timing** (for lip-sync anchors and the on-screen lyrics) is measured on the separated vocal stem
  (`song/lines.json`).
- **Upload your own track** instead (Studio: song source "upload"); a track with no words becomes an instrumental project.
- **[FIELD] Vocalise** (vocals as an instrument, invented language) can't be ranked by lyric coverage; see ROADMAP.md.

## Checklist

- [ ] Three paragraphs (metadata, vocals, arrangement), then a tagged timeline.
- [ ] Genre in specific words, BPM and key together, one visual anchor, the studio sound.
- [ ] Treatment asked for positively ("lush hall reverb, nothing distorted").
- [ ] Two singers: a casting note in capitals at the top and the singer named in each tag.
- [ ] Instrumentals: "No vocals. Strictly instrumental." and a ghost timeline.
- [ ] Beds: the flat-dynamic-profile sentence.
- [ ] Four seeds, read the coverage, listen to the top take.
