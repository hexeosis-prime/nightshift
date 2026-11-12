# Review: wellness launch demo, Nov 12 (hexe, shot by shot)

Each note: what hexe saw, its priority, the cause, the fix, and the rule it becomes.
Priority tiers (hexe: knowing which metrics matter is a creative-director skill):
**must fix** before sharing · **should fix** · **can slide** for now.

## A, shot 1: phone push-in into the salt cave

- **App text garbled.** Can slide: temp text on a temp UI. FLUX gets text right by the 4th or 5th roll, so it's a
  hit-rate item (render more takes of UI frames, or composite real screens, which client work does anyway).
- **Camera reverses at the end of the push-in.** Must fix. The frames show it: the push goes in past the card and
  closes on a tight view of the loungers, then the room widens back out to the full wide still. Cause: the first
  frame's screen card shows a portrait crop of the cave, and the last frame is the full wide cave, so landing on the
  last frame means zooming out. Fix: the last frame must be tighter than what the card shows, never wider: card =
  the full wide cave, last frame = a zoomed-in crop of it (or a closer still), and the next shot starts there and keeps
  moving forward. Rule: in a push-through transition, the camera only ever moves in one direction; every frame
  downstream is tighter than the one before it.

## A, shot 2: salt cave

- **A blanket floats up by itself.** Must fix (breaks physics). The left foreground blanket on an empty lounger lifts
  mid-shot. Cause: the action slot asked for "one woman pulls her blanket a little higher" in a wide shot full of
  identical blankets, and LTX attached the action to the wrong one. Fix: in wide shots with many similar objects, use
  self-contained actions (breathing, a slow head turn, eyes opening) or name the exact person and place ("the man in
  the red shirt, nearest lounger"); add "objects moving by themselves, floating fabric" to the negative.
  Rule: an object-interaction action needs one clear owner in the frame.
- hexe's broader rule from his group-shot tests: direct every actor by label with action and timing; cap groups at
  5-7, prefer 3. Logged in `docs/video-prompt-slots.md`.
