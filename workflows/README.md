# workflows/

ComfyUI graphs in API format (`<name>.json`) and their maps (`<name>.map.json`). Load a `.json` here into ComfyUI by dragging
it onto the canvas to inspect it; run `nightshift workflows` to list roles and `nightshift doctor` to check them against your
ComfyUI. Full reference: [../docs/workflows.md](../docs/workflows.md).

A project can override any of these with its own `workflows/` folder (same file names win) or by naming other graphs in
`project.json` `"workflows"`.
