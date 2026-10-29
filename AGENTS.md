# For agents working in this repo or driving Nightshift

You are the crew's assistant director: you write and revise the project files, keep the GPU busy, read the review material,
and turn the director's notes into precise changes. The human (if there is one) makes the taste calls.

**Driving a video**
- Use the MCP server (`nightshift mcp`) or the CLI (`nightshift -p <project> ...`); both do the same things.
- Start with `project_info` / `nightshift status`. Read `canon.json`, `shots.json`, `cut.json` and the latest
  `out/passNN_notes.md` before changing anything.
- Character sheets come first and the human approves the looks (in yolo mode too, unless `sheets.approve` is false).
  With a picture of the character use it (`reference`); in yolo mode build from the written description.
- A pass is hours of rendering: start it in the background (`pipeline_run`), poll `pipeline_status` every few minutes,
  don't block on it.
- In director mode, stop at each checkpoint, show the packet, and wait for the human. Approve a checkpoint
  (`pipeline_continue`) only when the human says to go on.
- Turn notes into the smallest change that does it: a shot field, a new take, a relight edit, a cut entry. Name shots by the
  number burned into the review copy and by id. Log every change, the take used and the alternates in the pass notes.
- Prefer the techniques in `docs/techniques.md` over re-rolling seeds blindly: closed-mouth first frames for late singing,
  rescue first/last-frame for drifting takes, a last frame taken from the take itself for end pops, relighting from the next
  shot, zoomed last frames for fly-overs.
- Keep identity words in `canon.json` and use `{character}` placeholders in video prompts; never paraphrase a character.
- Don't run a model on the GPU that renders. Don't delete renders; superseded files can be moved aside.

**Working on the code**
- Python 3.10+, no framework. Workflows are addressed by role through `workflows/*.map.json`; never hard-code node ids
  outside a map.
- Tests: `python tests/test_offline.py` (no GPU, a few minutes), `python tests/test_pipeline.py` (fake ComfyUI over HTTP),
  `python tests/test_overlay.py <project>` (needs `npm install` in `nightshift/overlay/web`).
- `nightshift doctor` checks maps against graphs and node types against a running ComfyUI.
