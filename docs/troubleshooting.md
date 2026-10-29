# Troubleshooting

**ComfyUI "stalls": the job shows as running, the GPU fans go quiet, nothing happens.** It happened on long LTX jobs,
especially a 225-frame first/last-frame shot (three times in a row). The watchdog interrupts a running job when ComfyUI's log
has been silent for `watchdog.stall_minutes` (needs `comfy.dir`, so it can see the log) or when the job runs past its time
limit, and re-queues it once. If the same shot stalls again: shorten it (fflf at 185 frames or under on 24 GB), or render it
with the lip-sync graph, which handled the same length.

**CUDA out of memory.** Usually something else is on the GPU: another app, a second ComfyUI job you started by hand, a local
LLM. The watchdog frees ComfyUI's memory and retries once. If it keeps happening, restart ComfyUI and keep the GPU to itself
while a pass renders.

**Jobs "lost" after a ComfyUI restart.** Queued jobs don't survive a restart. `nightshift watch` notices they're gone and
re-queues them; `nightshift status` shows what is open.

**A file you replaced comes back old.** Sync tools and remote file bridges can hand back a cached copy when a file is written
to the same path twice. Write fixes under a new name (`_v2`) instead of overwriting, and check (size, checksum) before you
trust a copy.

**Text, subtitles, logos in a take.** Quoted lyrics in the prompt can burn in as subtitles: `"no_lyric": true`. Logos on
clothing: "plain, no lettering or print" in the outfit, and `logo, text on clothing` in `negative_extra`.

**The end of an fflf take pops (hair snaps, the face morphs in the last frames).** The last frame differs from where the
motion was going. Take the last frame from the take itself (techniques.md: self-consistent last frames).

**A 720p still won't go into a 768-high render.** `nightshift.takes.pad_mirror` pads it to 1280x768 by mirroring the edges.

**Face scores of `--` / None.** No face found (profile, small, dark). Score a different frame, or ignore the score for that shot.

**Every take in clips/ shows up twice.** LTX's save node can write a separate `-audio.mp4`; Nightshift ignores those.

**`nightshift doctor` says a node type is missing.** Install the pack (docs/workflows.md) or point that job at your own graph.

**The overlay renders without fonts.** Run `npm install` in `nightshift/overlay/web`. Chromium not found: `npx playwright
install chromium`, or set `NIGHTSHIFT_CHROME` to a Chrome/Chromium executable.

**Windows paths.** ComfyUI reports subfolders with backslashes; Nightshift normalises them. Keep project names free of
spaces to keep ffmpeg concat lists simple.

**`comfy validate` says the fflf graph's image and audio loaders "feed no output node".** They feed rgthree Any Switch
nodes, which validators can't trace through. The graph runs fine.
