# LTX 2.3 Prompting Guide

*Erik (hexeosis) and Zero (HEXEBOTZERO), hexeosis inc. Reviewed and edited by Claude Opus 5.5.*

*Best practices for LTX 2.3 video in ComfyUI, revised after the 52 shots of "What Do You Want?" (October 2026).*

---

## Core principles

- **Sentences, not tags.** LTX 2.3 reads the prompt with Gemma 3 12B (the text encoder in the Nightshift workflows), so
  write it the way you'd describe the shot to a camera operator. Two to four sentences works best; the shots in the first
  video ran 30 to 70 words, plus the sung line on lip-sync shots.
- **One continuous moment per clip.** Two or three beats in order are fine ("she stops, then turns to look back over her
  shoulder"). A string of separate events is not: split it into shots.
- **Always name the camera move.** A missing camera cue is the most common weak spot. Give the camera its own sentence and
  tie it to the subject or the space: "The camera dollies sideways alongside her, the fence sliding past in the foreground."
  Examples: `slow push-in`, `handheld drift around her`, `static wide shot`, `cranes up and over her`, `orbits a quarter turn`.
- **Describe subject motion and camera motion as two things.** What the person does, then what the camera does.
- **No weight syntax.** `(word:1.5)` does nothing useful. Say what you want plainly.
- **Identity words are copied, never paraphrased.** The same description of the same person in every shot ("the woman in her
  mid-twenties with wavy brunette hair in a black t-shirt"). Pin an age; "young" drifts.
- **Lengths are 8n+1 frames at 24 fps.** 121 frames is 5 seconds; Nightshift sizes every clip to its slot in the edit.

---

## What bit us, and the fix

| problem | fix |
|---|---|
| Quoted words appear on screen as subtitles or signs | Quotes ask for text in frame. Quote lyrics only in lip-sync prompts; if a take still shows text, drop the quote (`"no_lyric": true`) and keep `subtitles, captions, text` in the negative |
| The subject spins or turns 180° mid-shot | `spinning, turning around` in the negative unless the turn is the point |
| Extra people walk in, or the person duplicates | `extra people, crowd, bystanders, duplicate person` in the negative on people shots |
| Singers grow a microphone | `microphone, mic stand, holding a microphone` in the negative |
| A cut appears inside one clip | `scene cut, jump cut` in the negative |
| A logo or emblem appears on clothing late in the take | "plain, no lettering or print" in the wardrobe text, `logo, text on clothing` in the negative |
| The face or hair snaps in the last frames of a first + last frame shot | The last frame differs from where the motion is going. Take the last frame from the take itself, so the two frames differ only in what should change |
| People look like puppets after a speed-up | Don't speed up shots with people walking; landscapes and fly-overs take 2x well |
| A long first + last frame shot stalls ComfyUI | On a 24 GB card 185 frames ran and 225 stalled three times: keep them at 185 or under, or use the lip-sync graph |

Nightshift adds the per-mode negatives above automatically.

---

## By mode

**First frame (image to video).** Briefly restate who and where, so the model knows what it's looking at, then spend the
words on what moves and what the camera does. For a dance shot, the first frame should already catch the person mid-move.

**Lip-sync.** The song section drives the mouth; the prompt says who sings, what, and how:

```
The woman sings the lyric words "What do you want"

([woman], [singing]): "What do you want", warm, expressive singing style
```

For a rapper: `The man raps the lyric words "..."` and `([man], [rapping]): "...", confident, playful, rhythmic rap delivery`.
If the singing starts late in the shot, the first frame needs a closed mouth, or the take opens mouthing nonsense.

**First + last frame.** Describe the motion between the two frames, not the frames themselves. Techniques that worked:
- *Rescue*: a take that drifts (face changes, light changes, wrong ending) is redone with the song as audio, a closed-mouth
  first frame and the exact frame it has to land on.
- *Arrive frame*: land the last frame mid-shot (`arrive_frame`, a multiple of 8) for a whip-pan that arrives on the singer
  and then lets her perform.
- *Fly-over*: a tighter crop of the first frame as the last frame makes the camera fly forward into the scene.
- *Relight*: relight both frames from a frame of the next shot, so the cut matches.
- *Change over time*: winter tree to blossom, bleached reef to living, night to dawn.

**Text to video.** Shots without people: aerials, timelapses, weather, establishing shots. Ending with "Fast, smooth,
cinematic camera movement" helps.

**Audio.** LTX 2.3 generates sound with the picture. In a music video the clip audio is replaced by the song, so describing
sound in first-frame and text-to-video prompts spends words on nothing; in lip-sync and first + last frame shots with the song
attached, the song is the audio. For standalone clips where the sound matters, use the narrative system below.

---

## System 1: narrative scene prompts

Full-scene prompts for continuous cinematic shots with sound. One paragraph, in chronological order: the order of the prompt
is the timeline of the clip.

### Conventions

- **One paragraph, no markdown.**
- **Chronological flow.** Actions and camera moves in the order they happen.
- **Camera moves tied to the scene.** The camera moves with a purpose relative to the subject or the space, in its own clause.
- **Audio layered in order:** foley, then ambience, then music, then dialogue or voice-over. Mixing words ("layered lightly",
  "without dominating", "blending beneath") keep the sound from turning to mud.
- **Exact quoted dialogue with a voice description.** Non-negotiable for speech and voice-over.
- **Texture and adverbs matter:** "crisp and precise", "glistening with dew", "subtly tilts", "brief arpeggios, then fading
  back beneath the surface".

### Dialogue format

```
[scene description], ([who], [manner]): "[what they say]", [speaking style]
```

```
a woman sitting close to a microphone in warm dim lighting, (woman, southern accent, whispering): "close your eyes and listen"
a man at a desk late at night, (man, speaking softly): "I've been thinking about this all day"
a woman doing a skincare routine, (woman, whispering quietly): "this is my favorite step", intimate ASMR
```

### Template: long

```
Style: [visual style] with [lighting/atmosphere]. A [shot type, e.g. handheld close-up] begins on [setting]. [Light or weather]
[falls/streams/casts] over [the space]. The camera [weaves/follows/pushes/tilts/pans] [direction, purpose] through [scene
elements]. [Subject: age, appearance, clothing, posture]. [Subject action with precise physical detail]. [Foley] over
[ambience]. [More ambient layers]. [Optional music: genre, instruments, mixing role]. [Subject looks/turns] and says in a
[voice quality] voice, "[exact dialogue]". The camera [moves] toward [next element] as [action continues]. [Final image or
sound].
```

### Template: short

The first + last frame workflow's prompt builder assembles exactly this order from its preset lists:

```
A {genre / scene type} — featuring {person / subject}. {action / dialogue} — set in a {location}. The camera {camera movement
and framing} — illuminated by {lighting}. {continued action / style notes} — layered with {music / sound}.
```

### Examples

**Forest, atmospheric:**

> A young woman with long, flowing black hair and pale skin stands in a dimly lit, overgrown forest clearing. She wears a
> simple, dark green dress that blends into the surrounding foliage. Soft, diffused light filters through the dense canopy
> above, casting dappled shadows on her face and the ground. The air is thick with humidity and the scent of damp earth and
> decaying leaves. Subtle ambient sounds of rustling leaves, distant birdsong and the gentle dripping of water create an
> immersive atmosphere. Her expression is serene, her eyes closed as she slowly turns her head, as if listening to the forest
> itself. A faint, ethereal hum resonates in the background, growing slightly louder as she turns, with the soft crunch of
> leaves under her bare feet.

**Florist shop, commercial with dialogue:**

> Realistic, with soft morning lighting. A close-up, handheld shot begins inside a narrow florist shop at opening time. Soft
> morning light streams through the front glass, lighting dust motes in the air. The camera weaves between colorful bouquets
> and the hands of a florist, a woman in her late 20s with tied-back auburn hair and a smudged apron. She trims stems with
> sharp scissors, the sound crisp and precise against the room tone. Paper crinkles softly as she unwraps fresh roses, lilies
> and tulips, their colors catching the light. Water fills a bucket with a gentle gurgle. A door chime rings faintly, mixed with
> distant street noise. The florist looks into the camera, calm and content, and says in a warm, slightly husky voice, "Can't
> beat the smell of fresh cut flowers." The camera pans slowly across a row of flowers as the front door opens on a blurred
> figure entering the shop.

**Nature documentary, voice-over:**

> Realistic nature documentary, a handheld shot of coastal wildflowers and rocks above the ocean. At eye level, the camera
> takes in the view from a cliff over turquoise water, then slowly pushes toward the sea: sandy beaches below in warm
> sunlight, a path through coastal plants and daisies leading to clear water where gentle waves break into white foam. The
> handheld frame tilts down toward the shore. Crashing waves, birds calling from the brush and dry leaves in the breeze make a
> rich soundscape; layered lightly on top, a soft harp and xylophone play brief arpeggios, then fade back beneath without
> dominating. After a beat, a narrator with an authoritative British accent begins, "Not many have even heard of the Ocean
> before," pauses for effect, then continues over the same soundscape, "Most believe it to be merely imaginary. A fable."

---

## From "What Do You Want?"

These ran in the first video, with the character's identity words in place of `{lead}`.

**Lip-sync, close-up (first frame + song):**

> Close-up of the woman in her mid-twenties with wavy brunette hair in a black t-shirt on a rooftop parking level at night,
> the downtown skyline and storm clouds behind her. Wind whips her hair across her face; she pushes it back with one hand as
> she sings, eyes half closed, then lifting toward the sky. Handheld camera drifting slowly around her.

**Lip-sync, moving camera:**

> Medium shot of the woman in her mid-twenties with wavy brunette hair in a black t-shirt walking across a caged pedestrian
> bridge over a freeway at night, her fingers trailing along the chain-link fence as red and white traffic light trails stream
> beneath her. She sings, turning her head from the traffic to the camera. The camera dollies sideways alongside her, the
> fence sliding past in the foreground.

**Text to video, aerial:**

> Aerial drone shot at night rising and slowly rotating over the stacked four-level freeway interchange in downtown Los
> Angeles, ribbons of white headlights and red taillights streaming along every curve like lines drawn across the city, the
> downtown towers glowing behind under dark storm clouds. Fast, smooth, cinematic camera movement.

**First + last frame, loop seam (the last shot ends on the first shot's frame):**

> A wide, low-angle shot of the empty top level of a parking structure in downtown Los Angeles at night. The storm clouds slow
> and settle over the skyline, sodium lamps glow, puddles still. The camera drifts slowly backward along the painted lines.
