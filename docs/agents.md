# Agents

Nightshift doesn't care which agent runs it. `AGENTS.md` at the repo root is a one-page briefing to give any agent. Everything is a CLI command and an MCP tool; the agent's job is judgement:
writing the canon and shot list with you, reading contact sheets, turning notes into shot changes, and keeping the GPU busy.

## Connecting

```bash
nightshift mcp --project-root ~/ComfyUI/output/nightshift                    # stdio
nightshift mcp --http --host 0.0.0.0 --port 8765 --project-root <folder>     # streamable HTTP at http://<host>:8765/mcp
```

- **Claude Code:** `claude mcp add nightshift -- nightshift mcp --project-root <folder>`
- **Claude Desktop / Cursor / other stdio clients:** command `nightshift`, args `["mcp", "--project-root", "<folder>"]`
- **An agent on another machine** (Hermes on a Mac mini, a server, a laptop): run the HTTP server on the GPU box and give the
  agent `http://<gpu-box>:8765/mcp`. There is no authentication: keep it on your LAN, or bind to 127.0.0.1 and reach it
  through an SSH tunnel.

**Don't put the agent's model on the render GPU.** LTX 2.3 takes most of a 24 GB card. Running, say, Hermes with
llama-server on the same 3090 as ComfyUI means constant CUDA evictions: models reload for minutes per job, renders stall
and run out of memory. Run the agent's model somewhere else (a Mac mini with a model that fits it, another GPU, or a hosted
model) and let it drive the GPU box over the network.

## The tools

| group | tools |
|---|---|
| projects | `projects`, `project_init`, `project_info`, `read_doc`, `write_doc`, `patch_shot`, `list_files`, `view_image` |
| the pass | `pipeline_run`, `pipeline_status`, `pipeline_continue`, `next_pass`, `task_status`, `task_stop` |
| sheets | `sheets_status`, `sheets_review`, `pick_sheet` |
| song | `song_jobs`, `song_choose`, `analyze_song`, `resolve_timeline` |
| jobs | `build_jobs`, `make_takes`, `identity_variants`, `edit_image`, `submit_jobs`, `watch_jobs`, `queue_status`, `cancel_jobs`, `comfy_health`, `workflows_list` |
| review | `rank_images`, `rank_takes`, `takes_sheet`, `cut_report`, `pick_take` |
| finishing | `assemble_cut`, `overlay_build`, `finish_video`, `review_copy` |
| plans | `plan_format` (the plan JSON shape and rules), `create_from_plan` (a whole project from a plan: lyrics, song brief, cast, worlds, shots) |

`read_doc` returns the file's raw text (JSON files included: parse it yourself), and `write_doc` replaces the whole file, so
read, change, write back. In `project.json` the project's name is `"name"`; keys starting with `_` are notes. To make a video
from an idea: `plan_format` → write the plan with your own model → `create_from_plan` → `pipeline_run` → poll
`pipeline_status`. In yolo mode nothing waits for a human; in director mode call `pipeline_continue` when the human approves. `list_files(project, "out/*.mp4")` finds the finished pass. When Nightshift Studio is running, every project file is also
served over HTTP at `http://<gpu-box>:8189/files/<project>/<path>` (range requests work), handy for checking a video.

Long steps (a pass, song analysis, assembly, overlay, finishing) return a task id immediately; `task_status` shows the log.
`view_image` hands contact sheets, stills and video frames to agents that can see.

## Director mode: the loop

1. **Brief.** With the human: the song idea, the characters, the worlds, the story beats. The agent writes `canon.json`,
   `song/caption.md`, `song/lyrics.txt`, `shots.json` (`write_doc`). If the human has a picture of a character, it goes in
   `refs/` and the character's `reference` points at it.
2. **`pipeline_run`**, then check `pipeline_status` every few minutes. The first stops are the character looks
   (`sheets_review`, then `outfits_review`): show the contact sheets (`view_image`), let the human choose (`pick_sheet`) or
   ask for changes to the description and re-render (`sheets_status` shows what exists). At every later checkpoint, show
   the packet the same way.
3. **Notes become changes.** "Shot 26: the light changes at the end, keep the red" becomes a relight edit and a rescue fflf
   on that shot (`patch_shot`, `edit_image`). "Faster on the ending" becomes `speed` or `beats` in `cut.json`. Keep a pass
   log in `out/passNN_notes.md`: what changed, which take, why, and the alternates.
4. **`pipeline_continue`.** Only what changed re-renders. After `pass_review`: `next_pass` and around again.
5. **Stop when the human loves it.** The first pass is the final pass if nothing needs changing.

Good habits from the first video: work one shot at a time when the human is giving notes; say which shot number (as burned
into the review copy) and which take; offer alternates rather than asking open questions; when the human says "don't let me
change anything else", don't.

## Yolo mode

`pipeline_run(yolo=true)` or `"mode": "yolo"` in `project.json`. Character sheets are made from the written descriptions
(the text graph), and the run stops once for the human to approve the looks unless `sheets.approve` is false (projects made in Studio
or with `create_from_plan` set it false, so hands-off never pauses). After that,
no checkpoints: the song with the best lyric coverage, the
identity edit with the best face match (seed x wording grid), the best-scoring take per shot. A good yolo agent still
checks its own work between steps: `cut_report` for identity drift, takes sheets for extra limbs and text, and re-rolls what
fails before finishing.

## Running unattended

A pass is a night of rendering. The pipeline runs as a background process, so the agent session can end; `pipeline_status`
picks up where it is. The watchdog interrupts and re-queues a stalled or out-of-memory job once, and says so in the log; if
ComfyUI itself goes down, the run stops and waits for a restart (`nightshift watch` resumes).
