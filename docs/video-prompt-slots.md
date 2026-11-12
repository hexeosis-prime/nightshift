# Video prompt slots (hexe's 8-part LTX assembly)

_hexe's tested system, Nov 9, 2026. Order changed to screenplay order (location before subject): hexe hadn't tried
location first in this setup yet, so the first runs are an A/B against his current order._

| Order | Slot | Include | Exclude |
| --- | --- | --- | --- |
| 1 | **Genre / scene type** | high-level context and vibe: `cinematic medical drama`, `vertical social media format`, sometimes one phrase like `a documentary` | subjects, locations, actions, camera |
| 2 | **Location / setting** | pure environment and spatial layout: `narrow florist shop with glass front` | subjects, camera, mood, lighting |
| 3 | **Person / subject / character** | the focal entity and its appearance only: `woman in late 20s with tied-back auburn hair` | movement, location, dialogue, lighting |
| 4 | **Action / dialogue** | one continuous motion, plus dialogue in exact LTX format | camera moves, lighting, cuts or transitions |
| 5 | **Camera movement and framing** | must include the framing scale AND an explicit motion: `close-up handheld shot that slowly pushes in` | subject behavior, lighting, style |
| 6 | **Lighting** | quality, direction and color of light only: `soft morning light streaming through glass` | post-process tags, camera, subject |
| 7 | **Continued action / style notes** | how the shot unfolds over time + rendering treatment: `scene holds steady as ambient details drift naturally, rendered in photorealistic cinematic style` | new actions, audio, hard cuts |
| 8 | **Music / sound / audio** | soundscape, music, ambience. Always last, for LTX audio conditioning | visuals, dialogue |

hexe's original order: 1 genre, 2 subject, 3 action, 4 location, 5 camera, 6 lighting, 7 continued, 8 audio.

## Notes

- **Sound words leak into the picture.** "Birds chirping" in the audio slot puts flying birds in the sky about a third of
  the time (hexe). Wide shots: no birds in any slot, "birds" in the negative.
- **Each slot's exclude list is checkable.** The builder can flag a camera word in the action slot, or a light word in the
  location slot, before anything renders. That is the lint for agent-written prompts.
- The wellness run's camera-move prompts broke these rules: the yoga move opens with the camera, mixes action and
  light ("sunbeams shift"), and the retreat move put birds in. The video prompts get rewritten into slots for the
  refinement session.

## Locked-off camera: same image as first and last frame (hexe, Nov 11)

For any fixed-camera shot (a stand-up news reporter, a performer singing to a locked-off camera), load the same image
as both the first and the last frame. LTX holds the frame like a locked-off camera, and character consistency improves.
Worked for lip-sync too. Nightshift: prefer first + last = same still whenever a shot's camera move is "static".

### Test, Nov 11 (vid_ltx, 6 s 9:16 lip-sync, vocals isolated)

- **Locked (first = last frame):** the lip-sync matches the lyric, but anything in the still repeats for the whole shot.
  Her hand stayed raised in the same place and the start-frame mouth shape kept coming back, which reads oddly. The
  trick needs a **neutral still**: medium close-up, mouth closed, hands relaxed or out of frame. hexe's news reporter
  test (medium close-up, neutral) worked well.
- **Free (first frame only, "camera arcs slowly around her"):** creatively the better shot; the arc is lovely and the
  lyrics we do see are good, but she turns away and the face is lost by mid-shot.
- **Rule:** a shot flagged *must show the words* (a key lyric line, dialogue, a reporter) = first = last frame, medium
  close-up, neutral still. Every other lip-sync shot may move freely.

## The benchmark shot (hexe's A/B reference, Nov 11)

hexe's locked-seed test for every model / LoRA / stage change: a news reporter at a sunny waterfront, medium close-up,
neutral start (image kept on the PC as `_promo_poc/ltx_test/bench_reporter.png`). Same image and seed every time; it
showed 3 stages clearly beating 2 and settled the LoRA set and the single ConvRot model. Prompt:

> Style: realistic - cinematic - The woman smiles confidently and is speaking clearly in a professional, articulate voice
> with Australian English accent, "Good morning, viewers. We're live here at the waterfront, where preparations are
> underway for the upcoming festival. It looks like a perfect summer day, everything is going well so far." Gentle waves
> lap against the seawall, creating a soft, rhythmic sound, as a news reporter's microphone subtly picks up ambient
> sounds of the harbor—distant boat horns. She gestures slightly with her right hand as she speaks, maintaining eye
> contact with the viewer

Run it again before trusting any change: LTX 2.5, a new LoRA, a stage recipe, the upscaler A/B.

## Direct every actor (hexe, Nov 12)

An LTX shot is a scene: the prompt directs every person in the frame by name or label (the woman in the red shirt,
the instructor, the man nearest camera) and says what each does and when. People in the frame who aren't mentioned
mostly stand there, or at worst do something random (the floating blanket was an action given to no clear owner).

**Cast size:** fewer people, less to go wrong. A group is 5 to 7 people at most; 3 is often better than 5. Set the
headcount at the still (the still decides the cast), and Nightshift can count faces in a still (`score.people_in`) and
re-roll one over the cap. In the action slot, every person in the still gets a line of direction.

**Labels, not pronouns:** name each person by role or placement ("the practitioner", "the client on the mat",
"the woman at left") and repeat the same label every time. Never "she" or "he" when two people could match.
Exceptions (hexe): one person in the shot = pronouns are fine. Don't over-label; too verbose has its own costs,
so the A/B below sets how far to go.

## Anchored modifiers and repeated labels (hexe, Nov 12; to A/B)

Newer models seem to bind descriptions better when every modifier sits next to its noun:
"wearing a blue shirt, a cotton shirt, an untucked shirt" rather than "wearing a blue cotton untucked shirt".
For characters, repeat the whole label in every sentence:
"The tall man in the white shirt walks to frame left. The tall man in the white shirt lifts his right hand and tips
his hat. The tall man in the white shirt leaves the room through the front door." rather than
"A man walks left, tips his hat and leaves."
Why it may work: each modifier-noun pair is its own clear match for the text encoder, so attributes and actions don't
drift to the wrong object or person (the floating blanket, the bowl/brush swap). Test in the refinement session: same
seed and still, compact vs anchored/repeated wording, on a 2-3 person shot and the benchmark reporter.
