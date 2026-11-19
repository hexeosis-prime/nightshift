# Prompting the three models

The short version. The full guides, built from hexe's Nov 18 prompting guides and component banks and this month's tests:

- [FLUX 3 images](guides/flux3-images.md): settings, the five prompt slots, character sheets, frames made from the sheet,
  the lighting test
- [LTX 2.3 video](guides/ltx-2.3-video.md): screenplay order, frame conditioning, lip-sync, NAG negatives, what LTX
  invents, runtime
- [MiniMax Music 3](guides/minimax-music-3.md): the caption's three paragraphs, lyrics and ghost timelines, background
  beds, ranking takes
- [Component banks](guides/component-banks.md): ready-made lines for every slot, the 36-location backlot, negatives by
  use

## FLUX 3 (character sheets, first frames, stills, edits)

- **Distilled model, 15-16 steps, cfg 1.** At cfg 1 the negative prompt is skipped, so say what you want instead of what
  you don't: "a plain unprinted white tee", "her hands are empty".
- **Frames come straight from the character sheet** (the sheet as the first reference, the prompt describing the new
  shot). The default layout puts the place and where its light comes from first, then the person in that light, then
  hexe's identity block, ending "as if it were another photograph of the exact same person in a different situation".
- **Light gets its own sentence**: the sources, which side, their color, how much shadow. Light in the action words is
  ignored; a style image copies its light into every shot.
- **Keep the original three-panel sheet.** Sheets made from sheets lose the face.

## LTX 2.3 (video)

- **Screenplay order, one continuous moment:** genre, location, who (as `{lead}`), what they do in order, framing and
  camera behavior, light, how it settles, sound last.
- **Always say the shot size and what the camera does**, including "locked off". A real lock-off needs the same image as
  first and last frame.
- **LTX invents whatever enters the frame later**: a hand coming into view holds a microphone, a pan finds a wall that
  wasn't there. Say what enters ("her hands stay empty"), show it in the first frame, or pin the end with a last frame.
- **Negatives are live** (the graph runs NAG): keep them short and aimed at defects you've seen.
- **Sound words can become pictures**: "birdsong" puts birds in wide shots.

## MiniMax Music 3 (the song)

- **Caption = three paragraphs and a timeline**: global metadata (specific genre, BPM and key, mood, studio sound),
  vocal details (who sings and how it's treated), arrangement (drums, low end, melodic bed), then tagged sections with
  (cues) and lyrics.
- **Ask for treatment positively**: "lush hall reverb, nothing distorted" rather than "erosion" or "granular".
- **Two singers need a casting note in capitals** at the top and the singer named in each section tag.
- **Instrumentals still get a ghost timeline**; beds under voice get the flat-dynamic-profile sentence.
- **Render four seeds and read the lyric coverage** before listening.
