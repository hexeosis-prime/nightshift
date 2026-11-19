# FLUX 3 images: stills, character sheets and frames made from the sheet

_hexe's Flux text-to-image guide and image component bank (Nov 18), merged with the Nightshift tests of Nov 17-19 on an
RTX 3090. Tags: **[FIELD]** tested here and used as the default; **[OFFICIAL]** from Black Forest Labs or ComfyUI;
**[EXPERIMENT]** promising, not proven. A tested result holds for this workflow and these model files, not for every
FLUX setup._

FLUX 3 makes every image in a Nightshift video: the character sheet, the scene stills for empty places, the first (and
last) frames of character shots, and edits such as relights. All of it goes through one ComfyUI graph, `img_flux3`
(hexe's all-in-one: text to image or edit, a prompt upsampler switch, up to four reference images, padded to black).

## 1. Settings that work

| | Text to image | Edit / frames from the sheet |
| --- | --- | --- |
| Model file | `flux3-image-klein-int8-convrot` (distilled) | same |
| Steps / cfg | 15 / 1 | 16 / 1 |
| Sampler | er_sde | euler |
| Upsampler (`image_rewrite`) | off by default; the official text-to-image instructions when on | on for frames from the sheet, off for other edits |
| Time per 1280x768 frame | about 5 s | 12-20 s (one reference), more per extra reference |

- **[FIELD] Which file is which.** The hyphenated `flux3-image-klein-int8-convrot` (the name in ComfyUI's templates) is the
  **distilled** model; the underscore `flux3_image_klein_int8_convrot` from the older mirror is the **base** model. Files
  with `-base-` are base, `_sd_` distilled. Distilled at 15-16 steps cfg 1 matches its own 50-step cfg 3.5 result in a
  fifth of the time; the base file at 15 steps breaks poses. Nightshift never swaps one family for the other.
- **[FIELD] cfg 1 means no guidance, so the negative prompt does nothing.** The graph uses a plain KSampler (no NAG). At
  cfg 1 the negative pass is skipped, which is what makes it fast. Anything you want to avoid has to be steered away from
  in the positive prompt ("a plain unprinted white tee", "her hands are empty"). A "terrible" 16-step result is usually
  cfg 0 or the base file, not the step count.
- **[FIELD] More steps don't help.** 50 steps cfg 3.5 scored no better than 16 steps cfg 1 on identity (0.64 against 0.68
  over six shots) and took four times as long.
- **[OFFICIAL] Up to 10 reference images.** Each one costs time. Nightshift uses at most four: the character sheet, a
  second character's sheet, and location plates.

### The prompt upsampler

A small language model (Qwen) that looks at the references and rewrites the prompt into one detailed instruction before
FLUX 3 sees it.

- **[FIELD] It helps composition.** With two references it puts the second reference's person into the scene; without it
  she may not appear.
- **[FIELD] It rewrites your structure.** Whatever order you write in, it comes back as "Create a photograph of the woman
  from the first reference image ..., preserve her exact identity ...". What survives is content (the light sources, the
  outfit, the action), not ordering.
- **[FIELD] It adds a frontal pose.** Nearly every rewrite says "she stands near-frontally with her face fully visible",
  even when asked not to. This is where the straight-to-camera, character-sheet look comes from.
- **[FIELD] It copies a style image's light into every shot.** A golden-hour style reference made a dusk rooftop, a diner
  and a bus at night all golden. Use a style image only when that look is wanted everywhere; otherwise put the light in
  words.
- **[FIELD] Off is a real option for frames made from the sheet**: same identity (0.78 against 0.77), the prompt reaches
  the model as written, and each frame is faster. Some shots look better with it, some without.

## 2. Writing image prompts

- **Natural language, not tag soup.** Complete sentences or clean clauses. FLUX reads structure and relationships.
- **Head-to-toe specificity.** Exact colors, materials, cuts and wear: "faded blue heavy-duty denim jeans", "scuffed
  brown leather work boots", "natural pale skin texture with visible pores and subtle freckles across nose and cheeks".
- **A frozen instant.** A still is one moment: no "starts to", "walks over", "suddenly". No sounds, music or dialogue.
- **Optical anchors.** Lens, aperture and light source do more than adjectives: "85mm portrait lens, f/1.8, shallow depth
  of field", "35mm lens look, direct on-camera flash", "sodium street lamps", "a single flickering floodlight".
- **Say what should be there, not what shouldn't.** At cfg 1 there is no negative prompt to lean on.
- **Plain means plain.** "A white tee" can come back printed; "a plain unprinted white cotton tee" doesn't. The same for
  hands: name what they hold, or say they're empty.

## 3. The five slots

hexe's image workflow builds a prompt from four inputs, each one line from a bank of presets. Nightshift adds a fifth,
**light**, because the backlot locations deliberately leave light out and the tests showed light needs its own sentence.
Each slot holds only its own kind of detail, so any line combines with any other.

| Slot | What goes in | What stays out | Formula |
| --- | --- | --- | --- |
| Person | age, archetype, eyes and brows, nose and jaw, hair (length, part, color, texture), build, skin texture | clothes, pose, light, place | The character is a [age/archetype] with [eyes] and a [nose/jaw], [hair], [build], [skin]. |
| Outfit | outerwear, top, bottoms, legwear, footwear, accessories with exact left/right placement, fabrics | body, pose, place | She is wearing a [top, color, fabric] over [bottoms], [legwear], [footwear], [accessories]. |
| Action | posture, hands, head angle, gaze, the prop in use, the lens | movement over time, camera moves, background | standing under a streetlight, looking down at the phone in her right hand, 50mm lens |
| Location | the place in five parts: [scale/material] [place], [surface/structure], [furniture/object], [small prop] and [small detail] | people, light | narrow rain-slicked city alley, wet brick walls and fire escapes, metal dumpsters, glowing shop signs, puddles and crumpled paper |
| Light | the sources in the place, which side, their color, how much shadow | everything else | a warm sodium lamp high on her left, green spill from a shop window on the right, half her face in shadow |

The banks (one entry per line, ready for ComfyUI's multi-line selector nodes) are in [component-banks.md](component-banks.md),
including the 36-location backlot.

## 4. The character sheet

One landscape image, three views, made from the character description or a photo:

```text
Film character sheet, photorealistic commercial studio photography. Three views of the exact same person from the
attached reference image, standing in a row on a seamless neutral grey #B8B8B8 background: full-body front view,
full-body back view, and a macro close-up portrait of the face. Identical person, outfit, hairstyle and styling in all
three views, matched true to the reference photo.

In the full-body front view the person stands upright in a relaxed neutral pose facing the camera, head level. The
full-body back view shows the person from behind, feet to head fully in frame. The macro close-up shows the face fully
and clearly, looking straight into the lens, sharp focused eyes, natural skin texture with visible pores.

Soft even studio lighting with smooth falloff, clean commercial catalogue look, crisp fabric detail, accurate face, body
proportions and clothing carried over exactly from the reference image.
```

- **[FIELD] Three panels beat seven.** Over six varied shots the three-panel sheet scored 0.66 on identity, a seven-panel
  sheet made from it 0.58, the body panels and the face close-up given as two separate references 0.60.
- **[FIELD] Never make a sheet from a sheet.** The seven-panel sheet came out with lighter freckles and a softer face, and
  every frame made from it inherited that. Keep the original; make new views from the source photo.
- **[FIELD] Landscape**, so the three views sit side by side at a usable size.
- hexe's variant puts a flat white circle over the face in the full-body front view, like an anonymized casting photo, so
  the face exists only in the close-up panel.

## 5. Frames made straight from the sheet

This is how Nightshift makes every first frame with a person in it (hexe's method, Nov 18). There is no scene still and
no face swap: the sheet is the first reference, a second character's sheet the next, location plates after that, and
the prompt describes the new shot. The face comes from the sheet; the framing, place and light come from the words.

**[FIELD] Why:** over six varied shots it scored 0.68 on identity against 0.58 for the old way (a text still, then an
identity edit), at 27 s a frame against about 3 minutes. Expressions and head angles follow the prompt (frontal to full
profile); freckles, eyes and hair hold in every frame. On a full merge-test run the chosen frames scored 0.56-0.91.

### The prompt (`sheet_prompt: "scene_id"`, the default)

Scene first, then the person placed into its light, then hexe's identity block:

```text
Create a cinematic film still, a [framing], in [location]. The light here comes from [light].
In this scene is the [woman] from the character sheet in the first reference image ([person words]), wearing [outfit].
[Action, as a sentence.]
She is lit only by the light of this place, in its color, direction and contrast: part of her face falls into shadow,
and her skin, hair and clothes pick up the color of the light around her, exposed the same as the rest of the scene,
with no extra light on her face.
The exact same person must remain recognizable regardless of pose, expression, camera angle, perspective, lighting,
environment or composition. Preserve facial identity above all other elements: same eyes, eye spacing, face shape, nose,
mouth, freckles, hair color, hairline and overall facial proportions. Photorealistic, realistic skin texture, natural
asymmetry, realistic hair, realistic anatomy. Do not redesign or reinterpret the character. Generate the image as if it
were another photograph of the exact same person in a different situation.
[World style.]
```

The last sentence of the identity block does the most work: it treats the sheet as one photo of the person among many,
not a template to copy. "Regardless of ... lighting" tells the model her identity survives a change of light. Nightshift
leaves "clothing, hairstyle" out of hexe's original list because these shots keep the outfit.

### What the lighting test found (Nov 18, six shots x two seeds, same sheet)

| Version | Face match | Notes |
| --- | --- | --- |
| A: who first, light only in the world style line | 0.76 | the face lit like the sheet |
| B: A plus a light sentence at the end | 0.71 | most of the visible change comes from just naming the light |
| C: scene first + "use the sheet only for who she is" | 0.68 | two identity misses |
| **D: scene first + hexe's identity block** | **0.77** | no misses, warmer and more side light |
| E: D plus a no-copy-the-light line in the upsampler's instructions | 0.69 | two misses; the rewrite still said "near-frontal" |
| **F: D with the upsampler off** | **0.78** | no misses, faster |

- **[FIELD] Light in its own sentence, early.** Two shots in a full run already had light in their action words
  ("standing in silhouette against the brightest light", "soft light on one side of the face"); FLUX 3 ignored both and lit
  her like the sheet.
- **[FIELD] It moves the light part of the way.** D and F are warmer and dimmer with some side shadow; faces are still
  mostly front-lit. Real silhouettes and half-face shadow didn't happen in any version. One version took "silhouette"
  literally and turned her back to the camera.
- **[FIELD] Identity costs nothing.** D and F hold the same face match as the old layout.
- **[EXPERIMENT] Next:** a relight pass on the finished frame (identity locked from the frame itself, only the light
  changed); a character sheet shot in directional light, so there is less flat light to copy; D or F by shot type.

### Picking and rerolling

- Each character shot renders two candidates; Nightshift keeps the one whose face best matches the sheet (SFace cosine:
  0.9 is the sheet's own face, 0.6-0.8 a good frame at a different angle or light, below 0.4 likely someone else).
- Below a floor (close 0.5, medium 0.45, wide 0.3) it tries two more seeds.
- **[FIELD] Small faces score low.** A full-body wide puts the face at 30-60 pixels; 0.3-0.5 is normal there. Look at the
  frame rather than trusting the number.
- **[FIELD] Single-seed scores are noisy**, especially wide shots (the same prompt went from 0.02 to 0.34 on two seeds).
  Compare prompt versions over at least two seeds.

## 6. More than one reference

- **Name references by position.** "the first reference image", "the second reference image"; with the upsampler off,
  `<ref_image_0>` tags and words gave near-identical results.
- **A second character**: their sheet goes second. Say where they are: "The man from the second reference image stands
  beside her, a little behind."
- **Location plates** (the backlot idea): an image of the place goes after the character sheets, and the prompt says "in
  the place shown in the third reference image". One plate per location keeps a place consistent from shot to shot.
- hexe's three-image compositing prompt, for putting a sheet's person into an existing scene image:

```text
using [reference_image1] as the base, update the appearance of the woman to match the film character sheet from
[reference_image2] using accurate face, body proportions and clothing carried over exactly from the [reference_image2] and
then add in the man character from [reference_image3] so that he appears naturally and realistically added into the shot
in the background on the left side of the frame. keep the outfits clothing and costumes exactly the same as the
reference images and make the face expressions look happy.
```

## 7. Edits and relights

- **[FIELD] Scene edits work on the distilled model at 16 steps cfg 1.** A dusk relight of a daytime still matched the
  50-step cfg 3.5 version in 12 s instead of 58 s; four references composed as asked.
- **[FIELD] Identity edits don't carry a face.** Replacing the person in an existing still with the sheet's face kept the
  original still almost unchanged (face match 0.11-0.40). Make the frame from the sheet instead (section 5).
- An edit prompt says what changes, then what stays: "Change the windows to a deep blue evening sky and add warm paper
  lamps along the walls. Everything else exactly as in the first reference image."

## 8. Structured JSON prompts

For strict era or style emulation (a 2003 game engine look, a product ad with exact copy), hexe's library has prompts
written as a JSON object (`subject`, `lighting`, `camera`, `materials`, `render_distance_logic`, ...). FLUX reads the
structure well. Nightshift doesn't generate these; write them by hand for one-off stills.

## Checklist

- [ ] Distilled file, 15-16 steps, cfg 1.
- [ ] Positive wording for everything you'd normally put in a negative.
- [ ] The light named as sources, side, color and shadow, in its own sentence.
- [ ] The original three-panel sheet as the first reference; no sheets made from sheets.
- [ ] No style image unless its light should be everywhere.
- [ ] Plain clothing said as plain; hands empty unless something is named.
- [ ] Compare versions over two seeds or more, and look at wide shots rather than trusting their scores.
