# Techniques

What made the difference on the first video, in the order you'll need it. Each one is a few fields in a shot or a cut entry.

## Faces: settle them first, then keep them

**Lock the character sheets before anything else.** Nightshift makes them as the first step of a pass: one image per
character and world with a front full-body view (the face covered by a white circle), a back view and a macro close-up
of the face. Approve them before anything else renders; every still is identity-edited from them and every
take is scored against them. On the first video the sheets kept moving while shots were being made, and the lead ended up
as four or five slightly different people across the cut; every later fix was a repair of that.

**Identity edit, then score.** Shots with `"still": "edit"` go through a two-image Flux edit: image 1 is the shot's still
(pose, framing, light), image 2 the sheet (face, hair, body, wardrobe). Render a small grid of seeds x wordings
(`nightshift variants --ids c01,c02 --wordings AC --per 3`) and let the face scorer rank them. SFace cosine against the sheet:
~0.36 is the usual same-person line; moving a shot from 0.28 to 0.41, or 0.35 to 0.56, was visible to everyone.

**Words that drift.** "young" ages faces unpredictably: pin a number ("in her mid-twenties"). Skin-detail words (pores,
stubble shadow) made skin worse, not better: "clear healthy skin" works, and so does leaving out "smooth". Expression words carry into the whole face: one
character kept coming out angrier than intended until "friendlier eyes" went into his identity words. Don't let the edit carry skin tone over from a
differently lit sheet (wording C says so explicitly).

**Identity words are copied, never retyped.** Video prompts say `{lead}`; the builder substitutes the character's
`video_name` so every shot uses exactly the same words.

**Wardrobe follows framing.** Shoes only in a wide; the close-up outfit is just what's visible. "Plain, no lettering or
print" on every garment, or logos and emblems appear mid-shot (one take grew a small white emblem in its last three seconds).

**More references.** A smiling sheet for upbeat shots and a close-up face portrait for close-ups
(`"sheet_ref"`). For a stubborn first frame, use the face from a neighbouring shot that already looks right as the
reference: matching shot 3 to shot 2's face took the match from 0.28 to 0.41.

## First frames that animate well

- **Singing starts late in the shot? Closed mouth in the first frame** (`"expr": "lips gently closed, about to sing"`).
  Otherwise the take opens mid-word and mouths nonsense until the vocal arrives.
- **Dance shots: catch her mid-move.** A static pose animates as a static pose.
- **Style suffixes off for Flux stills.** The generic "cinematic" suffix injected light rays and moonbeams into everything.
- **Quoted lyrics can burn in as subtitles.** If a lip-sync take shows text, set `"no_lyric": true` (the audio still drives
  the mouth).
- **720p still, 768 render:** mirror-pad 1280x720 to 1280x768 (`nightshift.takes.pad_mirror`); the cut crops exactly the
  padding back off.

## Takes

**Best-of-N where it pays.** Singing + dancing + a camera move in one shot: four takes, and one is usually clearly better.
Everything else: one take, re-roll only on a note. `"complex": true` on the shot.

**Rank, then look.** `nightshift score takes --shot c02` ranks by face match (and mouth activity for lip-sync);
`nightshift review takes c02` makes a first/middle/last-frame sheet. The score finds drift; only eyes find a sixth finger.

## First/last frame (fflf): the precision tool

**Rescue mode.** When a first-frame take wanders (the face changes by the end, the light drifts, the move goes the wrong
way), redo it as `fflf` with the song as audio: first frame with a closed mouth, last frame exactly where the shot has to
land. The singer still lip-syncs; the camera and the face are pinned at both ends.

**Self-consistent last frames remove end pops.** If the last frame differs from where the motion is naturally going, LTX
rushes to it in the final frames: hair snaps, a face morphs. Take the last frame from the take itself (same seed, a frame near
the end: `nightshift.takes.extract_frame`), so first and last frame differ only in what is meant to change.

**Relight both ends from the next shot.** The dance shot cut into a close-up with a strong red key from the left; the dance
shot was lit differently, so the cut jumped. Relight its first and last frame with a Flux edit using a frame of the next shot
as the light reference (`edit_light`, or `nightshift edit --base ... --ref ...`), then fflf between them: the cut matches.

**Arrive mid-shot.** `"arrive_frame": 64` lands the last frame at frame 64 (a multiple of 8) instead of the end; after it
the performance runs free. A whip-pan that lands on the singer, then lets her perform.

**Fly-overs.** A last frame that is a tighter crop of the first (`nightshift.takes.zoom_crop`, 60% for example) makes LTX
fly forward into the scene. A dead reef in the first frame and a 60% crop of the living reef as the last: the camera flies
over it while the colour comes back. Same trick for a forward glide down a street.

**Environment changes over a shot.** First frame winter tree, last frame the same tree in blossom (a Flux edit of the first:
`nightshift edit --base stills/tree.png --id tree_spring --text "..."`). Bleached to living, night to dawn, empty to busy.

**Keep fflf shots at 185 frames or under on 24 GB.** 185 frames ran; a 225-frame fflf stalled ComfyUI three times in a row; the lip-sync
graph (first frame only) rendered the same length without trouble.

## The cut

- **Cut on the grid.** `"beats": 8` ends a shot on the eighth beat after it starts. The first video's closing montage is
  six one-bar shots cut on the downbeats.
- **`speed`** compresses a slow move (2 = double speed) but makes people walk like puppets; keep shots with walking people at
  normal speed and pick the best second or two with `in`.
- **Stretch, don't freeze.** A clip a few percent short of its slot: `"speed": 0.94` instead of a frozen last frame.
- **Loop seam.** The last shot is an fflf from the first shot's still back to itself (`"still_from"`), the song is asked for a
  long natural decay (no hard ending), and the first cut entry's `in` lands exactly on the first frame.
- **Lip-sync takes are locked to their audio window.** You can't trim the head or extend it without breaking sync: plan the
  run-up with `lead` on the shot instead.

## Finish

- **Grade the footage, not the graphics.** The look goes on the cut; the HUD is desaturated a little and keyed on top; the
  lyrics stay full colour.
- **Fix skin per shot, not globally.** A face that sat too dark under the grade got a shadow/mid lift only inside its shot's
  time window (`grade.lifts`), leaving everything else alone.
- **eq before RGB.** In the bloom (screen blend), ffmpeg's eq runs in YUV; everything after it must run in RGB or the blend
  tints chroma magenta (`grade.chain` handles this).
- **Chunks.** Finishing in 9-second chunks means a late change re-renders one or two chunks; unchanged chunks are reused byte
  for byte.

## Graphics that know where the faces are

- Lyric lines pick one placement for their whole time on screen, scored against the union of face boxes (plus margin and
  head-room) over those frames, and against any illustrations on screen. Per-shot or per-line overrides when taste disagrees
  (`slot_by_shot`, `slot_by_line`, `dy_by_line`).
- Head turns drive timing: `nightshift score yaw clips/x.mp4` gives a per-frame head turn (negative = looking screen-left).
  Time an illustration to land where she looks. Check the direction on a crop before trusting it: we misread it twice.
- Everything leaves before the end of a looping video, so the seam is clean.
