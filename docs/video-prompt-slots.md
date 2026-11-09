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
