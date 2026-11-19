# LTX 2.3 video: prompting and workflow

**hexe's reconciled master guide (18 Nov 2026), with the Nightshift findings of 18-19 Nov added.**
**Scope:** LTX-2.3 in Nightshift's `vid_ltx` ComfyUI graph: first frame only (FF), first and last frame (FF-LF), identical
first and last frame (lock-off and loops), song audio in for lip-sync, and text to video.
**Basis:** hexe's original *LTX 2.3 Video Prompting & Workflow Master Guide*, the *LTX 2.3: Nightshift field notes*
(18 Nov 2026) and version-specific LTX and ComfyUI documentation (see the references at the end).
**Not an LTX-2.5 migration guide.** Do not silently transfer model assets, encoders, LoRAs, quantizations or prompting
results between versions.

## Reading the evidence

- **[FIELD / DEFAULT]** A production finding from Nightshift testing (an RTX 3090, 24 GB). This is the recommended behavior for this particular toolkit until new A/B tests change it; it is **not** a claim of universal model behavior.
- **[OFFICIAL / CONTEXT]** A recommendation or technical fact from the model author or ComfyUI. Use to explain, qualify, or supply missing information; where it disagrees with a Nightshift finding, show both.
- **[WORKFLOW / CONFIG]** Specific to the currently reported custom workflow, model, nodes, available VRAM, LoRAs or generation method. Re-check if those change.
- **[EXPERIMENT]** A promising but unconfirmed or narrowly observed technique. Do not silently promote it to a default.

**Precedence:** reproducible Nightshift results for *this workflow* > official prompting preferences for untested situations > community suggestions. Technical facts such as encoder identity, active guidance paths and frame-count constraints remain independently verifiable. Keep workflow tests and claims of model universality separate.

---

## 1. Model basics and core directing rules

**Encoder correction [OFFICIAL]:** LTX-2.3 uses **Gemma 3**, with LTX-specific text conditioning / connectors, **not the old T5 claim** in the original guide. The exact encoder file and any quantization must match the installed workflow. Do not carry over the original guide's claimed **512-token hard maximum** as an established LTX-2.3 limit. The LTX-2.3 guidance varies: the March prompt guide favors detailed, duration-appropriate descriptions; the May adherence article suggests keeping a shot under ~200 words. Treat that as editorial guidance, not an API tokenizer limit. See sources at the end.

**Core style [FIELD + OFFICIAL]:** Supply literal, observable actions in natural present-tense prose. Prefer a coherent chronological shot description to a keyword pile. Direct **what changes in the world** separately from **what the camera does**. Do not rely on weighting syntax like `(word:1.5)` or `((word))` as a tested LTX mechanism.

**One continuous shot per generation [FIELD / DEFAULT]:** Do not ask the current Nightshift LTX-2.3 workflow to perform a succession of hard cuts. Small chronological beats are fine if physically linked, but avoid too many separate acts. Make complex transitions separate shots, especially when people walk or change position drastically.

**Camera behavior is mandatory [FIELD / DEFAULT]:** Describe **framing scale + explicit camera behavior**. A static camera *is* explicit behavior: `locked medium close-up, camera fixed on a tripod`. For a moving camera use e.g. `medium close-up, a slow push toward the subject`. Merely writing `cinematic` does not control the move. **A text-only locked-camera request is less reliable than identical FF and LF images in your tests.**

**Direct every visible actor [FIELD / DEFAULT]:** Give each person a stable role/position label (`the practitioner`, `the woman on the left`) and a simple action. Reuse the **full label** in later sentences; avoid ambiguous `she`, `he`, or `they` in multi-person shots. Pronouns are fine in a single-person shot. When a person manipulates something, name **both the owner and object**. Unassigned gestures can become motion by the object itself.

**Cast and movement [FIELD / DEFAULT]:** Prefer **three people over five**, and treat roughly **five to seven** as the practical upper edge for directed cast scenes on this setup, not a fixed architecture limit. Crowd-wide synchronized motion may be described as **one shared action** (`Together the class flows into the next pose, in unison`). Rare actions or tools are best broken into **one small, slow gesture**; otherwise substitute familiar, reliable moves. Stillness can be the intended acting direction.

**The first frame is casting [FIELD / DEFAULT]:** The source still determines the people, faces, costumes and many prop relationships. In the tested character workflow, making first frames directly from a **three-panel character sheet with FLUX 3 as reference** maintained identities better than a text still followed by face replacement. This is a Nightshift asset-pipeline finding, not a general statement about all image models.

**Text in frame:** Put intended visible words in explicit quotation marks and identify them as *a sign, printed label, phone screen, subtitle*, etc. Quotation marks are also used for spoken dialogue; state whether the text is **written or spoken** to avoid confusion. Exact legibility is not guaranteed.

## 2. Preferred prompt ordering: screenplay, not image-prompt ordering

**[FIELD / DEFAULT]** The preferred LTX-2.3 video prompt order is:

1. Genre / scene type / recording format
2. **Location / spatial layout**
3. Subject(s) / stable labels / appearance
4. Action / actor ownership / speech performance
5. Camera framing and explicit behavior
6. Lighting and visible atmosphere
7. Shot continuation, subtle motion or ending state
8. **Sound last** (foley, ambience, music if desired)

**Official difference [OFFICIAL / CONTEXT]:** LTX's May 2026 adherence article recommends leading with the main action, followed by motion, subject/environment, camera and lighting. The March LTX-2.3 guide gives an alternate shot/scene/action/character/camera/audio sequence. **Nightshift found location-before-subject better in its workflow**, so use the tested screenplay order. Retain action-first as an A/B candidate, not a reason to overwrite the field results.

**Chronology within action still matters.** The top-level subject/location order is not an instruction to narrate later actions before earlier ones.

**Audio-text leakage [FIELD / DEFAULT]:** Audio words can materialize visually. In wide outdoor shots, `birds chirping` has produced visible flying birds roughly one-third of the time in Nightshift tests. If birds are unwanted, omit *bird-related words from the positive prompt entirely*, including the audio section; add the corresponding NAG negative where appropriate. This is a tested tradeoff: do not request bird sounds while also hoping for no birds on screen.

**Prompt length [OFFICIAL + WORKFLOW]:** Start concise for short/simple shots, add detail when it provides concrete action, performance, camera, or audio control. There is **no verified 512-token maximum** in these materials. The official May 2026 article suggests <200 words and roughly one main action per 2–3 seconds; the March article encourages richer descriptions for longer scenes. The correct Nightshift sweet spot still needs A/B measurements.

## 3. System 1: narrative prompts (agent-written or manually written)

Supply the final model-facing prompt as **a cohesive prose paragraph**. Headings and fields below describe how to assemble it, not literal text that must be placed into the encoder.

### General first-frame-only template

```text
[Genre/recording aesthetic] in [location and spatial arrangement]. [Describe only the subject cues necessary to identify actors from the first frame, assigning a stable role label to each]. [Describe what each actor physically does in chronological order, assigning each prop interaction to one actor]. [Shot scale, camera move, and what remains framed]. [Lighting, weather, and visible details relevant to the action]. [How the action settles or continues, without a hard cut]. [Foley and environmental audio, and optional music; sound last].
```

**Image-to-video [OFFICIAL]:** The input image already establishes static looks; prioritize **new motion and camera behavior** instead of redundantly redescribing every pixel. The exception is when a concise role label helps keep multiple actors distinct.

### Locked-camera / loop template

```text
[Style] in [location]. [Named subject(s) in the supplied still]. [One or two small self-contained movements, with no prop ambiguity]. A [wide/medium/close] shot from a fixed tripod position; framing and background remain unchanged. [Lighting stays consistent]. [Subtle repeating motion while the composition returns to its starting state]. [Natural audio, if used].
```

Use the **same reference image for FF and LF** when lock-off matters (see §6). A text instruction by itself did not hold static framing reliably in the tested workflow.

### First/last-frame transition template

```text
[Style] in [location]. [Stable actor labels]. From the composition in the supplied first frame, [one clear causal progression toward the supplied last-frame pose or crop]. [Explicit framing, camera direction, and pacing]. [Lighting and look remain consistent]. [The shot approaches the specified endpoint without introducing an unrelated action]. [Audio description, if relevant].
```

The two stills provide the endpoint geometry. Do **not** over-specify complex walking/prop transfer during a strong compositional transformation.

### Speech example (spoken dialogue, not visible text)

```text
An intimate naturalistic interview inside a modest studio. The reporter in the center of frame keeps both hands relaxed. The reporter looks at the lens, pauses, and says in a warm, even voice, "The water is finally receding." A locked medium close-up holds the reporter's face and mouth. Soft side light remains unchanged. The reporter settles into a neutral expression. A faint room tone is audible, with no background music.
```

**Dialogue guidance [OFFICIAL]:** Spoken text should be quoted and paired with physical delivery directions. Break longer lines into short clauses separated by actions; one giant quoted speech block is more fragile. The original guide's parenthetical inline `([woman], [singing]): "..."` format is preserved as an optional *legacy syntax*, **not a required model parser grammar**. Narrative prose is the default. When pre-recorded audio is supplied, do not regenerate the existing lyrics into an independent contradictory speech instruction.

## 4. System 2: deterministic eight-category MAD-LIBS / WebUI builder

**Goal [WORKFLOW]:** Allow the WebUI's preset selectors and natural-language inputs to run **without any LLM**, while giving the agent/CLI an optional chance to rewrite a finished draft. Keep this deterministic path; do not make prompt rewriting mandatory.

**Recommended semantic order [FIELD]:** update the renderer to output categories **1 Genre, 2 Location, 3 Subject, 4 Action, 5 Camera, 6 Lighting, 7 Continuation/Style, 8 Audio**. This differs from the *existing* physical slot mapping in the original draft (`Genre, Subject, Action, Location, Camera, Lighting, Misc, Audio`). If rewiring ComfyUI text nodes is inconvenient, **preserve the existing node IDs and remap the order at assembly time** instead. Do not rename or rewire production nodes purely for documentation alignment.

| Output order | Category | Contract and examples |
| --- | --- | --- |
| 1 | Genre / recording system | Visual medium, genre, context, e.g. `An intimate documentary-style commercial.` |
| 2 | Location | Environment and layout, e.g. `Inside a narrow florist shop at opening time, bouquets crowd the counter.` |
| 3 | Subject / cast | Identify each role and appearance, no ambiguous pronouns, e.g. `A florist in her late twenties stands behind the counter, wearing a stained apron.` |
| 4 | Action / dialogue | Who does which action, which tool, causal sequence; quote any spoken lines |
| 5 | Camera | **Shot scale and actual behavior**, including `locked off` for static shots |
| 6 | Lighting | Direction, intensity, hue, exposure continuity |
| 7 | Continuation / rendering notes | How movement develops or ends; avoid introducing a new unrelated action or cut |
| 8 | Sound | Foley, ambience, optional music, diegetic constraints; **last** |

### Robust deterministic assembly (recommended)

Store each preset as a **complete grammatical sentence or clause** designed for its slot. Join the non-empty values with single spaces, normalize adjacent punctuation, and remove absent optional slots rather than leaving dangling connectors. This produces natural prose without inventing a mandatory LLM dependency.

```text
{genre_sentence} {location_sentence} {subject_sentences} {action_sentences} {camera_sentence} {lighting_sentence} {continuation_sentence} {audio_sentence}
```

Example output from the non-LLM assembler:

```text
An intimate documentary-style commercial unfolds inside a florist shop. Rows of fresh flowers fill the narrow store at opening time. The florist, a woman in her late twenties wearing a stained apron, stands behind the counter. The florist slowly clips a rose stem with scissors, then sets it down. A handheld medium close-up pushes slightly toward the florist's hands. Soft morning light enters from the shop window. The florist pauses, leaving the scissors on the counter as the shot continues without a cut. Each cut produces a crisp snip over faint city traffic and a soft door chime, with no music.
```

**Legacy physical connector chain (original guide):**

```text
A {1} — featuring {2}. {3} — set in a {4}. The camera {5} — illuminated by {6}. {7} — layered with {8}.
```

That chain can still be retained for existing production graphs but has **three known weaknesses**: location comes after subject/action, hardcoded `a` can break grammar or duplicate prepositions, and optional slots can leave dangling separators. It is an implementation artifact rather than an LTX model requirement.

### Pre-flight validation for WebUI / API

- Confirm the **actual serialized prompt reaching the encoder**, not just the values shown in the UI. Keep existing preview-as-text debug nodes.
- Confirm model **LTX-2.3**, actual text encoder, model/LoRAs, active NAG and active negative prompt path.
- Distinguish the requested mode: FF only, FF-LF, identical FF=LF, or image+audio.
- Verify first-frame headcount, labels for every visible actor, and ownership for any prop motion.
- Ensure explicit shot scale **and** camera behavior; do not accidentally demand a dolly and a tripod lock-off together.
- Keep sound last; audit audio words for accidental visual objects (especially unwanted birds).
- Reject or flag strong contradictory instructions (e.g. `no movement` plus `subtle motion`; `camera movement` plus `locked camera`).
- Skip empty slots safely; normalize sentence boundaries without reordering chronological actions.
- Record the resolved workflow JSON and prompt for reproducibility, especially when branch switches change loaders or image conditioning.

## 5. Audio, music, dialogue and pre-existing tracks

### Generated audio [FIELD / DEFAULT]

Keep the **sound section at the end** of the prompt, using only layers relevant to the shot:

1. **Foley** tied to identifiable visible action (`scissors snip as the florist trims one stem`).
2. **Environment/room tone** (`faint traffic outside`, `low HVAC hum`). Avoid audio nouns that would generate unwanted imagery.
3. **Optional music** including instrumentation, genre, rhythm and mix priority where appropriate.
4. **Dialogue** may be quoted with actor identity and performance cues in the action flow when synchronization matters; the closing audio sentence can describe voice quality and mixing. Avoid making the ending audio slot a disconnected second script for the actor.

To request raw diegetic sound, use e.g. `Only natural location sound and foley, with no music.` This is a prompt preference, not an absolute output guarantee.

### Existing song / dialogue conditioning [FIELD / CONFIG]

- Use **MelBand RoFormer vocal isolation inside the graph**, feeding the vocal stem for clearer mouth shapes than the full mix in Nightshift tests.
- **Trim audio to shot duration before it enters the generation graph**. In the tested 24 fps convention, nominal elapsed time is `(frames - 1) / fps` (for instance, 121 frames = 5 s between first and last frame); align the exact audio window to the workflow's clip duration policy. Do not hand the graph the complete source song.
- Treat supplied vocals as the temporal authority. Prompt actor labels, facial acting, camera and framing; do not write a separate song that could conflict with the audio.
- If the shot's primary purpose is **clearly readable lip sync**, use FF-LF locked medium close-up with **mouth closed in a neutral still, hands relaxed or outside frame**.
- For shots where lip readability is secondary, permit the more expressive FF-only free camera. It may arc around and eventually lose the singer's face.
- FF-LF with **two different stills of the same character** can introduce pose change while retaining identity. This has worked in your tests.
- An **8-second** FF-LF shot with generated audio maintained identity in your observations; this is one result, not proof of arbitrarily long consistency.

## 6. Frame conditioning, camera and shot design

### FF only

[FIELD] Good for freer, more expressive camera moves. It is less reliable for compositing back over a static plate: the camera often drifts despite verbal lock-off instructions. Do not assume `static shot` solves this by itself.

### FF-LF different images

[FIELD] Both stills must describe the same world where continuity matters: match character, costume, environment and lighting. Compose the last image to lie **along the intended camera trajectory**. For a push-through into a monitor or image, make the last frame **tighter** than the first, otherwise the generation may reverse camera direction near the end. Use exact changes, not overly complicated simultaneous walking.

When joining shots, use **the last frame from the actual rendered and selected outgoing take**, not the pre-generation source still. This prevents an unexplained cut between divergent endpoints.

### Identical FF and LF: lock-off and loop

[FIELD] Supplying the **identical image** for both endpoints anchors framing and character identity. Useful for reporters, singing close-ups, flat paintings, cinemagraphs and approximately repeating movement. **Some takes barely move**: budget **4–6 candidate renders** and select the strongest in the tested loop use case.

[EXPERIMENT retained from original guide] An earlier recipe suggested **0.9 conditioning/reference strengths** at both ends and subtly perturbing the last still with micro-noise / an Img2Img pass around 0.1 denoise. The newer field notes demonstrate identical images work for lock-off and loop-friendly output **without establishing that micro-noise is required**. Keep the micro-noise approach as an optional A/B, not a mandatory step. Actual rendered endpoints can morph from reference frames, so a visually closed loop is **not automatically a pixel-perfect loop**; inspect seams before delivery.

Recommended instruction: `A locked wide shot from a fixed tripod position. The room stays geometrically fixed while a candle flame subtly flickers and returns to its starting posture.` Do not put both `no movement` and `subtle motion` in the same negative/positive scheme.

### Faces, actors and movement thresholds

[FIELD] Group faces start drifting after **roughly 6 seconds** in the tested shots. Wide scenes with around **12 people** can render faces only **20–30 pixels** high, leaving too little facial detail for robust continuity. Fix by cutting earlier, using closer framing/fewer characters, or a post face-detail pass. These are observed practical thresholds, not a guaranteed global limit.

[FIELD] Complex transition shots with moving pedestrians led to backward walking when endpoint requirements removed the pedestrians from frame. Keep people still/slow through strong transitions. Give walking a dedicated FF-only shot instead.

### What enters the frame is invented [FIELD, 19 Nov]

LTX only knows what the first frame shows. Anything that comes into view later (a hand rising into frame, the far side of a
pan or turn, the lower half of a shirt as the person steps back) is filled in from what the model expects to be there,
not from your character or location. Seen on the Nov 18 vertical run:

- a singer's hand entering frame came up holding a **microphone** (singers "usually" hold one);
- a plain white tee showed a **printed graphic** once the walking figure revealed more of it;
- a close-up with a camera turn swung from the side of an outdoor stucco building onto an **interior wall** of the same
  color for its last 10 frames.

Ways around it, cheapest first:

1. **Name what enters or is revealed.** "Her hands stay empty", "the camera turns to reveal the brick wall of the same
   building", "the plain unprinted white tee". The Nightshift planner now writes this into its video prompts.
2. **Put it in the first frame.** Frame the still a little wider than the move needs, with both hands and the full outfit
   visible, so LTX continues what it was shown.
3. **Pin the end of a move** with a first-and-last-frame shot, so the last frame decides what the camera finds.
4. **Targeted NAG negatives** for the known inventions: `microphone, object in hand, printed graphic, logo on clothing`
   (the negatives are live in this workflow, section 7).
5. **Reroll.** It is a per-seed event; the other candidate is often clean.

Not every invention is a defect: the turned-wall close-up was the favorite shot of that run (the camera turn, the singer's
turn and the light moving across her face); the background change only shows if you look for it.

### Duration and pacing

[FIELD] The model can partially reinterpret roughly the **first and last 10–12 frames** of guide images, including lighting, depth and facial proportions. Generated actions commonly ease in and out. For editorial, plan **around a second of head handle**, and an equivalent tail handle when an LF is used, where shot length permits. A successful observed remedy for a stalled join was to cut one 5-second push at **4.0 seconds** and start the next at **0.6 seconds** after its opening ease. This is an editing example, not an automatic trim for every shot.

**Note:** Building in a 1-second head and tail is an editorial target, not a guarantee you can discard 2 seconds from a 5-second performance without losing a lyric or critical action. Plan duration and the supplied audio slice accordingly.

### Realistic handheld / phone POV (retained from original guide)

1. Define camera medium and perspective early: raw phone footage, first-person operator position, orientation, environment.
2. Describe **the cause** of camera instability (`the operator stumbles over debris and the phone jolts sharply`) instead of relying only on `shaky handheld`.
3. Replace abstract mood labels with observed physiology and gestures: breath, flinch, interrupted grip, stumbling footsteps.
4. Sequence one causal action into the next; avoid a simultaneous list of unrelated disasters.
5. If rough footage is the intention, name concrete visual imperfections: focus hunting, compression, motion blur, clipped highlights. Don't blindly use `terrible footage` in every scene.
6. Use diegetic reactions and environmental sound, and request no music if appropriate. Check for sound nouns that create unwanted visual subjects.

## 7. Negative guidance: CFG is not NAG

**[WORKFLOW / CONFIG]** The tested Nightshift setup uses **a distilled INT8 ConvRot LTX-2.3 model plus NAG with negative prompting**. Keep negative prompts because they are active in this particular configuration. Do not describe them as merely `via CFG` without inspecting the sampler.

**[TECHNICAL / COMFYUI]** In ordinary **CFGGuider at CFG = 1**, the unconditioned/negative pass is skipped. A November 2026 ComfyUI template issue confirmed that default LTX-2.3 templates shipped populated negatives that were inert at CFG=1. **NAG is a separate guidance mechanism** and is a relevant approach for making negative conditioning active in a distilled workflow. Verify NAG is enabled in the **queued API graph** rather than assuming a negative text node is live. See source [3].

**Starter negative** (adapt to render style, not a guaranteed cure):

```text
watermark, unwanted captions, unrequested text, low quality, distorted anatomy, inconsistent faces, floating objects, motion reversal
```

**Targeted defect overrides [FIELD]:**

| Observed defect | Targeted negative text | More reliable upstream fix |
| --- | --- | --- |
| Unwanted birds from sound cues | `birds, flock of birds, birds chirping` | Remove bird words from *all positive slots*, including audio |
| People walking backward | `walking backwards, people moving in reverse` | Remove walkers from dramatic FF-LF transitions; render walking separately |
| Floating fabric / autonomous props | `objects moving by themselves, floating objects` | Name one actor and one object for each interaction |
| Camera drift in a lock-off | `camera movement, reframing, scene transition` | Identical FF and LF images |
| Letterboxing from a source still | `black bars, letterbox` (test) | Remove bars in **the source image** or crop during editing |

**Do not blindly copy the old giant negatives.** The original locked-loop list included **`no movement`** (which can suppress your desired internal motion). The extended list included **`static`**, **`film grain`**, **`cartoon`** and **`noise`**, all potentially legitimate aesthetic targets. Keep negatives purpose-built for the specific image and mode; test their actual influence under NAG.

## 8. Known quirks and observed fixes

| Symptom [FIELD] | Preferred intervention |
| --- | --- |
| Birds appear when prompted as sound only | Remove the bird words from positives; targeted NAG negative |
| One character fails to act | Explicitly direct that actor using a stable label |
| Similar blankets/cups move by themselves | Give each interacting object one owner; simplify gestures |
| Mallet becomes a brush | Use a familiar action or single small slow stroke, then stillness |
| White bowls merge with white candles | Redesign first frame with fewer objects and visibly different silhouettes/colors |
| `breathes deeply` makes lying subject move | Replace with a precise instruction to lie completely still |
| A requested `barrel roll` produces a different move than intended | Use the exact camera term; trial unfamiliar camera geometry before a production run |
| 12-person wide shot loses face details | Smaller cast, tighter shot, or detail pass |
| Subject changes face/lighting at endpoint | Expect guide-frame reinterpretation; plan handle trims or edits |
| Video inherits letterbox / black bars | Omit bars when making the first still; crop/edit fallback |
| A hand entering frame holds a microphone; a revealed shirt has a print | Name what enters ("her hands stay empty", "plain unprinted tee"); show it in the first frame; targeted NAG negative; reroll |
| A turning or panning camera finds a different background | Describe what the move reveals; pin the end with an LF; keep the move small |
| Bright polished shot reveals generated faults | Low-key lighting concealed small flaws in Nightshift tests; use only when appropriate to creative brief |

**Additional A/B candidates [EXPERIMENT]:** `a blue shirt, a cotton shirt` versus `a blue cotton shirt` (anchored modifiers), and repeating full actor labels in every sentence versus only when ambiguity arises. The field notes explicitly mark these as tests to perform, not successes to assert.

## 9. Runtime and reliability on the tested 24 GB system

**Observed platform [FIELD]:** RTX **3090, 24 GB** in the field report. Do not present these speeds or ceilings as general limits for another GPU. The current stated recipe includes **one INT8 ConvRot `ltx-2.3-22b-distilled-1.1`**, **OmniNFT RL**, **Crisp Enhance** LoRAs, and **NAG negative prompting**. Check exact local filenames and LoRA weights against actual API workflow export before publishing as reproducible defaults.

- **Three stages beat two** on the *same seed in the waterfront reporter benchmark*. This is a local controlled result, not universal proof every scene or checkpoint benefits.
- **Valid frame counts:** `F = 8n + 1` in the tested setup. At **24 fps**, 121 frames span 5 seconds, 145 span 6 seconds, and 193 span 8 seconds (`(F-1)/24` elapsed time). Distinguish this from the exported container/file duration, which may be calculated differently by a player or tool.
- **Working size:** 1280×768 (or 768×1280) followed by upscale. The field report found native **1920×1088** to need a 32 GB+ card for that recipe. This is a local capacity observation, not a general model minimum.
- **Render times:** typically **145–250 seconds per five-second clip**; rare **450–650-second** outliers were linked to model swapping in VRAM when mixed image/video jobs alternated. Group queued jobs by model when practical.
- **Allocator faults [FIELD, 18 Nov]:** ComfyUI's dynamic VRAM loader once failed to map memory in the LTX text encoder
  (`Fault failed: 2`, `VRAM Allocation failed (non OOM)`, `device not ready`); the next jobs rendered fine. Nightshift's
  watchdog now frees memory and re-queues such a job once, as it does for out-of-memory. One clip in the same run took
  583 s against a usual 125-250 s.
- **Branch trap:** ComfyUI checks loader nodes even on branches that won't execute; unresolved loader paths can invalidate a combined graph. Nightshift resolves switches **before queue submission**. Validate file availability in the exact queued graph.

**Regression benchmark [FIELD]:** sunny-waterfront news reporter, **medium close-up, neutral starting image**, identical image and seed. Re-run it whenever a model/LoRA, stage recipe, encoder, NAG setting or upscaler changes. Log quantitative render time and qualitative lip movement, actor stability, camera, endpoint fidelity and seam artifacts.

### Suggested test log columns

`date | comfy_version | model_file/hash | encoder_file/hash | loras_and_weights | nag_config | seed | FF/LF mode | audio_stem | frame_count | fps | resolution | stages | exact_positive | exact_negative | clip_seconds | runtime_seconds | facial_stability | camera_drift | artifact_notes | acceptance`

A/B **one changed variable at a time** where practical, while comparing representative shots outside the reporter benchmark so that improvements are not overfit to one scene.

## 10. Agent, MCP and CLI prompt authoring

**Two valid paths, same generation graph:**

- **Deterministic path:** WebUI fields, presets and toggles → normalized eight-slot draft → optional rewriter → API JSON injection. **No agent required.**
- **Agent path:** CLI/MCP agent inspects supplied images or shot brief and writes a model-ready prompt directly using the field rules. It can bypass the deterministic draft, but should not bypass workflow-state validation.

### Agent instructions, recommended (replace original overly speculative wording)

```text
You are preparing one LTX-2.3 video prompt for the Nightshift custom ComfyUI workflow.
Read the requested generation mode: FF only, FF-LF different frames, FF=LF lock-off/loop, or reference image + existing audio.
If reference images are supplied, use them as the visual ground truth. Do not invent people or objects that are absent unless the task explicitly allows it.
Write plain natural-language prose in one paragraph with this preferred order: genre/recording format; location; named subjects; chronological actions; shot scale and camera behavior; lighting; continuation/end state; audio last.
Direct every visible actor. Reuse stable labels instead of ambiguous pronouns; assign every prop interaction to one owner. Favor one simple continuous action. Use exact quoted dialogue and physical delivery cues only when speech should be generated by the model.
For FF-only, emphasize movement; for identical FF/LF, describe a locked camera plus subtle internal motion; for different FF/LF, describe a plausible continuous transformation between the provided compositions. Do not make people walk through complex transitions.
For supplied song/dialogue audio, treat the trimmed vocal input as the timing authority; do not invent conflicting lyrics. Prioritize visible lip readability only if the shot requires it.
Always specify shot size and whether the camera moves or is locked. Put incidental sound descriptions last; avoid audio words that might create undesired visible objects. No cuts unless explicitly requested as separate generations.
Output only the final model-ready prompt. Do not include headings, markdown, timecodes, rationale, or unsupported certainty.
```

### Optional draft rewriter contract

The rewriter may **improve grammar, camera specificity, causal sequencing and actor naming**, but it must preserve: actor count/identities, specified objects and ownership, chosen FF/LF mode, audio-conditioned lyrics, no-music flag, negative-positive exclusions, shot end state, and every explicit user constraint. It should return only revised prompt prose. Log both the **assembled draft** and **rewritten output** so results can be compared without losing the deterministic baseline.

### Short image-to-video request template (retained intent of legacy Agent 2)

```text
For this reference image, write one LTX-2.3 Nightshift image-to-video shot. Preserve the scene and the number of visible people. Describe one natural evolution from the starting pose, with precise small performances and one explicit camera behavior. Use the Nightshift screenplay order, stable actor labels and sound last. Keep it concise for a short shot, avoid cuts, and output a single model-ready prose paragraph.
```

## 10b. How Nightshift fills the prompt

- **Modes** (`shots.json` `mode`): `lipsync` (a still plus the shot's slice of the song, vocals isolated in the graph),
  `ff` (a first frame comes alive), `fflf` (first and last frame; with the same still twice, `"locked": true`, a
  lock-off), `t2v` (text only, for empty places). All run through one graph, `vid_ltx`, with toggles for the last frame,
  audio in and vocal isolation.
- **People are placeholders.** Video prompts say `{lead}` and Nightshift writes the character's identity words in, so a
  character reads the same in every shot. Never retype a description.
- **Audio** is cut to the shot before it enters the graph: `(frames - 1) / fps` plus 0.05 s, as a WAV, starting where
  the shot sits in the song.
- **Frames:** `8n + 1` at 24 fps; 1280x768 or 768x1280 working size, upscaled in the graph.
- **Negatives** are built per mode (scene cuts, spinning around, extra people, microphones on singers, subtitles and
  text, birds in wide and aerial shots) and active through NAG.
- **The planner** (`nightshift plan`, Studio's agent mode) writes each shot's `video` prompt in the screenplay order above
  and, since Nov 19, says what enters the frame.

## 11. Inherited narrative examples (from original guide)

These are useful **stylistic/structural examples preserved from the original document**, **not individually validated by the 18 Nov field notes**. For production, adapt them to screenplay order, simplify actions if required, keep actor ownership explicit, and **remove birdsong** if no birds should appear on screen.

* **Atmospheric Forest Scene:**
  > Style: A woman with long, flowing black hair and pale skin stands in a dimly lit, overgrown forest clearing. She wears a simple, dark green dress that blends into the surrounding foliage. Soft, diffused light filters through the dense canopy above, casting dappled shadows on her face and the ground. The air is thick with humidity and the scent of damp earth and decaying leaves. Subtle ambient sounds of rustling leaves, distant birdsong, and the gentle dripping of water create an immersive atmosphere. The woman's expression is serene, her eyes closed as she slowly rotates her head, seemingly listening to the forest itself. A faint, ethereal hum resonates subtly in the background, growing slightly louder as she continues to turn, accompanied by the soft crunching of leaves under her bare feet.

* **Commercial Florist Scene (with Dialogue):**
  > Style: realistic with soft morning lighting. A close-up, handheld shot begins within a narrow florist shop at opening time. Soft morning light streams through the front glass, illuminating dust motes dancing in the air. The camera weaves intimately between colorful bouquets and the hands of a florist, a woman in her late 20s with tied-back auburn hair and a smudged apron. She trims stems with sharp scissors, the sound crisp and precise against the background ambiance. Paper crinkling softly as she unwraps fresh flowers—roses, lilies, and tulips—their vibrant colors catching the light. Water fills a bucket with a gentle gurgle, reflecting the soft glow. A faint door chime rings subtly in the background, mingled with distant street noise. The florist looks directly into the camera, her expression calm and content, and says in a warm, slightly husky voice, "Can't beat the smell of fresh cut flowers." The camera slowly pans across a row of flowers catching the morning light as the front door opens, revealing a blurred figure entering the shop.

* **Nature Documentary Scene (with Voiceover):**
  > Style: realistic nature documentary with crisp natural lighting. A handheld eye-level shot begins atop a windswept cliff overlooking turquoise waters. Warm sunlight illuminates pale sandy beaches below, where coastal daisies and sea grasses sway near a narrow path descending to the shore. The camera slowly pushes forward and subtly tilts down toward the waterline, maintaining steady focus. Gentle waves crash against the rocks, their rhythmic foam blending with distant seabird calls and dry leaves rustling in the coastal breeze. Soft ambient harp melodies interweave with sparse xylophone arpeggios, layered quietly beneath the natural soundscape without overpowering it. After a brief pause, a Voice Over narrator speaks in a measured, authoritative British accent: "Not many have even heard of the ocean before." He pauses, letting the waves fill the silence, then continues seamlessly: "Most believe it to be merely imaginary. A fable." The camera holds on the receding tide as the narration fades into the ambient shore sounds.

---

## 12. Reconciliation notes: where our defaults differ

| Area | Original or official guidance | Nightshift evidence and reconciled decision |
| --- | --- | --- |
| Encoder | Original guide claimed T5 + 512 max tokens | **Correct to Gemma 3**; no sourced 512-token hard cap |
| Ordering | Original MAD-LIBS put subject/action before location; official May advice leads with action | **Use location-before-subject screenplay order**, while noting the official alternative |
| Prompt length | March LTX favors detailed prompts; May adherence article recommends <200 words | Keep detail proportional to shot/duration; benchmark the Nightshift sweet spot |
| Camera lock | Text says `static` | **Use identical FF and LF images** when a reliable locked plate is needed |
| Loop recipe | Original claims FF/LF 0.9 and micro-noise are required | **Identical images work** but often freeze; micro-noise and exact strengths remain optional tests |
| Casting | Original has generic subject/action slots | Stable labels for **every actor**, one prop owner; smaller casts |
| Sound | Original puts all audio last as semantic anchor | Keep sound last **but audit audio-to-image leakage**; omit unwanted bird terms |
| Negative prompts | Original said `via CFG` | **Use NAG in the reported distilled recipe**; normal CFG=1 negative boxes may be inert |
| Audio lip-sync | Original supplied generic spoken dialogue formats | **Trim vocal stem to shot; neutral FF=LF for must-read lips**; creative movement when not mandatory |
| FF-LF transition | Original describes 20-second interpolation and exact pacing beats | Prioritize simpler plausible endpoint trajectories; tested success at shorter shots does not validate 20 seconds |
| Editing | Original largely ended at generation | Plan guide-frame changes, ease handles and cuts on motion; chain from **actual last render** |
| Performance | Original had no measured recipe | Keep 3090 24 GB, 3 stages, 8n+1, 1280×768, VRAM queue observations **as scoped field findings** |

## 13. References / provenance

**Primary in-house documents**

- hexe's original *LTX 2.3 Video Prompting & Workflow Master Guide*: the baseline (all three examples preserved; the
  legacy connector chain kept for compatibility).
- *LTX 2.3: Nightshift field notes* (18 Nov 2026): production observations, treated as the preferred workflow defaults.
- The Nov 18 merge-test runs (16:9 and 9:16): off-frame invention, allocator faults.

**Official / technical references verified 18 Nov 2026**

1. LTX, *LTX-2.3 Prompt Guide* (10 Mar 2026): https://ltx.io/blog/ltx-2-3-prompt-guide
2. LTX, *How To Improve LTX-2.3 Prompt Adherence* (13 May 2026): https://ltx.io/blog/how-to-improve-ltx-2-3-prompt-adherence
3. Comfy-Org, *LTX-2.3 template negatives inactive at CFG=1*, issue #919; contributor confirmation 11 Nov 2026: https://github.com/Comfy-Org/workflow_templates/issues/919
4. Lightricks, *LTX-2 repository / prompting and ComfyUI integration*: https://github.com/Lightricks/LTX-2
5. LTX docs, *Workflow & Asset Compatibility*: https://docs.ltx.io/open-source-model/reference/workflow-asset-compatibility/

**Do not mistake LTX hosted API advice or LTX-2.5 docs for evidence about every behavior of the custom local LTX-2.3 workflow.**
