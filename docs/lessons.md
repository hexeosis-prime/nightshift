# Lessons from the first video

"What Do You Want?" took nine passes over about a week of nights (October 2026). The concept and the pipeline were built at
the same time, by mashing every button. These are the things we'd tell ourselves at the start.

## Order of work

1. **Song first, and let it pick the timing.** The shot list is written against lyric lines, not timecodes, so any render
   of the song can be dropped in and the timeline re-fits. Rendering the song before committing to shots saved re-cuts.
2. **Character sheets second, and lock them.** Faces changed several times while shots were already being made, so the lead
   exists in four or five slightly different versions across the cut. Lock the sheets (and a face portrait, and a smiling
   version) before the first still.
3. **Stills before video, every time.** A first frame takes a minute; a video take takes four. Fix it in the still.
4. **Video takes where they pay.** Best-of-4 only for shots doing several hard things at once.
5. **Graphics last**, after the cut is stable: they react to faces, beats and lyrics, so every re-cut moves them.

## Working with notes

- **Number everything the human sees.** Review copies have the shot number and id burned in; notes say "shot 26", the
  pass log says which take is in, and which alternates exist.
- **One shot at a time** when notes come in. Small, checkable changes; the rest of the cut doesn't move.
- **Offer alternates.** "p40 keeps the red light into the close-up, p41 has more dancing" gets a decision in one reply.
- **Keep the pass log.** `out/passNN_notes.md`: what changed and why, files, alternates. It is the memory of the project
  when sessions end and context is lost.
- **Freeze when asked.** Late in a project "don't let me change anything else" is a production decision; hold to it.
- **Check your own reading of the picture.** Twice a head-turn direction was read backwards from numbers; a crop of the
  frames settled it in seconds.
- **Check what the human means, gently.** A file named for shot 11 was really for shot 21; asking caught it before a wasted
  render.

## The machine

- **Give the GPU to the renders.** Out-of-memory crashes came when the GPU was shared with other work. One owner per GPU
  while a pass renders; the agent's own model belongs on another machine.
- **Expect stalls on long jobs and plan for them.** A watchdog that interrupts and re-queues beats waking up to an idle
  queue. Listen to the fans.
- **Every seed fixed, every job kept.** Being able to re-render any take exactly (same seed, same prompt) is what made late
  fixes cheap: shot 21 got a new first frame on the last day and kept its original seed, so the camera move stayed the
  same.
- **Cache the cut, chunk the finish.** Segment-per-shot assembly and chunked finishing meant a late note re-rendered seconds
  of video, not the whole thing.
- **Don't trust a re-copied file.** Writing a fix to the same path twice through a sync bridge delivered the old file. New
  file name for every fix.

## Taste, as it turned out

- A Portra-at-dusk grade with a touch more contrast (A+) over everything, a per-shot lift where skin sat too dark, and the
  HUD a little desaturated with the lyrics in full colour.
- Lyrics that move out of the way of faces read as designed; lyrics on faces read as a mistake.
- Speeding up shots with people walking looks wrong; landscapes and fly-overs take 2x well.
- An ending montage of one-bar shots on the downbeats, then back into the first frame for the loop.

## Next time

- Lock the faces first (see above), and try a dedicated face-swap workflow as a fallback for stubborn shots.
- Ideas: write the overlay config together with the shot list; let yolo mode make a first pass overnight, then direct from
  there.
