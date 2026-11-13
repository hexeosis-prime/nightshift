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

## A, shot 3: yoga class

- **Mostly OK; faces a bit smooshy.** Should fix (can slide for a demo). Cause: about 12 people in a wide shot, so each
  face is roughly 20-30 px tall at 1280x768, and only a few latent pixels in the first stage (640x384). LTX can't hold
  detail that small, and the 1.5x upscale shows it. Fixes, cheapest first: fewer people (the cast-size rule: 5 or so
  for a class), framing closer (medium wide, front row only), the face-detail pass for wide shots (roadmap), a bigger
  render or a better upscaler. What worked: one action for the whole group ("together they flow ... in unison") moved
  everyone coherently, a good pattern for crowds that must move as one.

## A, shot 4: sound healing session

- **Visually right, actions wrong for the context.** Must fix. People, space, camera and light all read real and stay
  consistent; the details and the actions don't. The singing-bowl mallet turns into a paintbrush, then into a basting
  brush ("basting a roast with BBQ sauce"); the woman lying down makes odd motions; candles and bowls blur together.
  Prompt (action slot): "She circles the mallet around the rim of a large crystal bowl; the woman breathes deeply and her
  face softens."
  Causes: (1) playing a singing bowl is a rare, specialized motion, so LTX substitutes a common one with a similar
  hand path (brushing, basting); (2) "mallet" is vague and the object becomes whatever fits the motion it chose;
  (3) in the still, white bowls and white pillar candles look alike, so they merge; (4) "breathes deeply" on a lying
  body gives the model license to move it.
  Fixes: pick actions with lots of real-world footage behind them, or keep the specialized one minimal (a single gentle
  strike, then stillness while it rings; or hands hovering still above the client, reiki-style); make the still
  readable (2 or 3 bowls, candles set apart and a different shape/color); direct the client to lie completely still,
  eyes closed. Stillness is a valid action and the easiest one to get right.
- **hexe's pattern from many tests:** faces in close-ups and medium shots look fully real; LTX builds coherent spaces;
  human motion, and especially interaction with objects in context, is where it struggles.
  Rule: choose actions LTX has seen a thousand times; the rarer the action, the smaller and slower it should be.
- hexe on the prompt itself: "She circles the mallet..." and "the woman breathes..." never say WHICH woman; both are
  women, and the pronoun flips between them. Rule: name each character by role or placement ("the practitioner",
  "the client on the mat", "the woman at left") and repeat that label every time; never use she/he when two people
  could match.
- hexe: certain combinations work better because they're well represented in the training data. Prompt refinement
  should find and bank those combos (prompt-part bank, tested entries).

## A, shot 5: tea lounge, five friends

- **Really good.** Can slide: the toasting arm motions read more like clinking beer bottles than tea cups (the training
  data again: toasting is a beer/wine gesture). Five people held together here because they share one simple,
  common social action (laughing, pouring, a touch on the shoulder). Worth noting against the cast-size rule: five
  works when the action is common and shared.

## A, shot 6 into shot 7: jungle retreat, then the pull-back

- **Far faces smooshy, foreground three OK.** Should fix. Same scale limit as shot 3: faces too small for the first
  stage. Fixes as shot 3 (fewer people deep in frame, closer framing, face-detail pass).
- **A break where shot 6 joins shot 7.** Must fix. Cause: my edit. The pull-back (shot 7) was built with the retreat
  STILL as its first frame, the same frame shot 6 starts from. So after 3.5 s of shot 6 the walkers jump back to their
  starting positions, and the short dissolve can't hide it. Fix: chain them. Shot 7's first frame = the last frame
  shot 6 actually uses (extract it), so the pull-back starts exactly where shot 6 leaves off. Or drop shot 6 and let
  the pull-back's own first seconds be the retreat moment. Rule: a shot that continues another starts from that
  shot's last used frame, never from the shared source still. (Nightshift's chained first/last-frame shots already
  do this; the demo script didn't.)

## A, shot 7: the pull-back

- **The concept doesn't read.** Must fix; it's the payoff of the whole idea. A doesn't pull back into the phone: it
  dissolves (in-model and in my edit) to a woman holding a phone, and her screen shows a different picture and place
  (a mountain landscape, not the retreat). I saw the wrong card when checking the app frames and let it pass; it
  should have been redone. Fixes: the app frame's card must show the exact place we pull back from (re-roll until it
  does, or composite the still into the screen directly); start the pull-back from the walking shot's last frame (see
  shot 6); cut it straight, no dissolve. B's pull-back (retreat shrinking into the phone in her hand) is the model.
- **People walk backwards, and some walk impossibly.** Must fix. Seen in both looks. Likely cause: a first+last frame
  shot asks LTX to get every walker from their spots in the first frame to a frame where they no longer exist (inside
  a phone), while the camera moves the other way; some walkers get solved by reversing. Separately, walking in wide
  shots is a known weak motion. Fixes to test: transition shots use still or slow subjects (standing, seated, a calm
  pause), not walkers; walking lives in its own shot with no last frame. Rule: a morph or transition and complex
  human motion don't mix in one shot. hexe has workflow ideas to test too.

## A, shot 8: the end shot

- **The phone floats in front of her hand,** not in the same focal plane. Must fix. Cause: the app-screen edit
  rebuilt the phone as a pasted layer (bigger, sharper, not gripped), and the slow push-in separates it further, like
  a 2.5D card. Fixes: generate the phone-in-hand frame in one pass with the app screen described in the prompt (no
  edit), or keep the edit tight to the screen only and check the grip: fingers wrap the phone, the phone shares her
  focus and light. Add a QC check for hand contact on held objects.

## B (cinematic): overall

- **Much better overall.** The darkness hides a lot of small generation faults (low-key light as a practical cover,
  not only a look), and the opening push-in really works.
- **A pause where shots 1 and 2 join.** Should fix. Measured frame-to-frame motion: the push-in accelerates to a peak
  around 3.5 s, then eases almost to a stop as it lands on its last frame (4.5-5 s); the cave shot then eases in from
  rest. Ease-out + ease-in = a stall at the join. Fix (done, `launch_B_v2.mp4`): cut on motion. The push-in ends at
  4.0 s while still moving, and the cave shot starts 0.6 s in, after its ease-in. The stall is gone. Rule: first/last
  frame shots land softly; when chaining them, trim the landing and the next shot's start. Longer term: put the last
  frame guide a little before the clip's end, so the move arrives at speed.
- **Idea (hexe):** open with the push-in, but end with the corkscrew move from the earlier drone test instead of the
  straight pull-back: spiral up and out of the retreat and land on the phone.

## B v3 (Nov 12): spa, tea, walk and pull-back redone with the rules above

`launch_B_v3.mp4` (28.2 s) + email copy. Changes: spa = new still (bowls and candles apart), one strike then stillness,
labels not pronouns; tea = each woman directed by position, only the woman at left touches the pot; walk = new still,
3 labeled walkers going away from camera, no letterbox; pull-back chained from the walk's last used frame, with an app
card showing that same retreat; new end shot from that app frame; 1 s head handles on the new shots.
Edit: the chained pull-back holds the walk ~3.5 s before pulling back, so it carries the retreat moment and the
separate walk shot was dropped. Noticed: a 4th walker appears during the pull-back (from 3 in the still), and the end
line sits over the phone as the push-in closes in. Both can slide for a demo; hexe to judge.

## B4 "lively" alt (Nov 12 night), `launch_B4_lively.mp4` (32.8 s, no tag line)

Same look, open and close as B v3; inside, each place gets a close-up face reaction plus the wide (tea: CU, wide, CU),
straight cuts, ~2-2.5 s shots, a livelier 104 BPM track (of 2 takes, the one that builds steadily; the other had
dropouts at 25 s and 35 s), a bowl-free session (hands resting on the client's shoulders, both still).
Close-ups = hexe's crop-and-scale trick + a FLUX 3 re-photograph pass (crop as ref 0, full still as ref 1). First
pass with the filmic look darkened the sunny yoga close-up into a moody one; re-run with "keep the light and color of
ref 1" matched. Faces read real at close-up scale, as hexe's tests predicted. Watch: the re-photograph pass can drift
identity (the yoga instructor came out older than the woman in the wide); one cave close-up take had the woman turn
away and leave frame (other take used). Shared the queue with Zero's vertical re-render all evening without trouble.
