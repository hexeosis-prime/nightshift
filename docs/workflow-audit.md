# Workflow audit: how each LTX graph sets size, length and frame rate

_Claude, Nov 7, 2026 (Phase 1 of PLAN.md). The four LTX 2.3 graphs in `workflows/` came from different sources and each
uses its own formulas. hexe fixes them in ComfyUI and re-exports both the UI and API versions; this page is the checklist._

## First: what actually caused Zero's landscape "vertical" renders

Not the graphs. The `.map.json` roles point at the right inputs in all four graphs (the wellness run rendered 768x1280
clips through ff, fflf and t2v). The cause was the **starter project.json**: it carried explicit 16:9 `work_size`, `crop`
and `final_size`, and explicit keys won over `"aspect": "9:16"`. Projects made through `create_from_plan` or the Studio
dropped those keys, which is why they worked; hand-built ones (project_init + write_doc) kept them.

Fixed on `next`: the aspect now owns the three sizes, the starter says `"aspect": "16:9"` instead of sizes, and
`tests/test_config.py` covers it. Same commit: an unknown profile / aspect / image_model no longer locks a project (it
opens with a warning and the default), and `write_doc` refuses a project.json with an unknown value.

The graphs still differ, below. None of it breaks a render today, but every difference is a place a later change can.

## The four graphs today

| | ff (first frame) | fflf (first + last) | lipsync | t2v (text) |
| --- | --- | --- | --- | --- |
| **Size source** | EmptyImage `257:251` (1280x768) → scale 0.5 → GetImageSize → latent | PrimitiveInt Width/Height `5013:5167/5168` (1280x768) → calculator `a/2/2` → latent | ResizeImageMaskNode `33` "scale dimensions" (1280x768) on the input image → GetImageSize → latent | EmptyImage `7` (**1280x720**) → scale 0.5 → GetImageSize → latent |
| **Stages** | 2: half size, then x2 upsample | 3: quarter size (`a/2/2`), then two x2 upsamples | see note 7 | 2: half size, then x2 upsample |
| **Length** | frames, typed in two places (`257:255` length, `257:254` audio frames) | seconds slider `5110` × fps → `1 + 8*round(a*b/8)` | audio duration × fps `(a*b)+1` (MathExpression, pysssss) | frames PrimitiveInt `10` (288) |
| **Frame rate** | ComfyNumberConvert `257:247` (24) | mxSlider `5100` (24) | FloatConstant `65` (24) | PrimitiveInt `11` + PrimitiveFloat `12` (24 twice) |
| **Image conditioning resize** | longer edge 1024 | longer edge 1536 (+ crop to WxH) | longer edge 1280 | none |
| **Audio mask** | none | SolidMask `5047` **768x1280** (portrait) | SolidMask `69` 1024x1024 | none |
| **Custom node packs** | core | KJNodes, mxSlider, rgthree | pysssss, VHS | core |

Things to check when fixing:

1. **fflf is three-stage, the others two.** `a/2/2` plus two x2 upsamplers lands on the same output size, so it is
   consistent, just a different recipe. Worth one A/B (same shot, 2-stage vs 3-stage) to pick one for all graphs.
2. **t2v's default is 1280x720.** 720 / 2 = 360 is not a multiple of 32. Nightshift overrides it with the work size
   (1280x768), but the graph opened by hand is off-grid. Set 1280x768.
3. **Length is three different formulas.** fflf rounds to 8n+1, lipsync does `duration × fps + 1` (not 8n+1 unless
   the duration is a whole number of 1/3 s), ff and t2v take raw frames. LTX wants 8n+1.
4. **The audio SolidMasks** are fixed sizes that don't follow the output (one portrait, one square). If they only mask
   the audio latent, size doesn't matter; worth confirming and labeling.
5. **Conditioning resize** (1024 / 1536 / 1280 / none): pick one rule, e.g. the output's longer edge.
6. **Five custom node packs** across four graphs. Fewer packs = fewer things that break on a ComfyUI update.

## Proposed standard for every LTX graph

One set of inputs, titled `ns_<role>` so Nightshift finds them without a map entry:

| Title | Node | Meaning |
| --- | --- | --- |
| `ns_width`, `ns_height` | PrimitiveInt | final output size (1280x768 or 768x1280) |
| `ns_frames` | PrimitiveInt | length in frames, always 8n+1 (Nightshift computes it) |
| `ns_fps` | PrimitiveFloat | frame rate, fed to every node that needs it |
| `ns_prompt`, `ns_negative`, `ns_seed` | as today | |

Everything else is derived inside the graph the same way in all four: one stage recipe (from the A/B in note 1), conditioning image
resized to the output's longer edge, audio frames from `ns_frames` and `ns_fps`. With that, the maps shrink to almost
nothing, and the graphs behave the same whether Nightshift or a person runs them.

7. **lipsync's stage count** wasn't traced here (it resizes the input image to the full size first); check it when
   re-exporting.

Not covered here: the FLUX 3 still / edit / sheet graphs (those already share one size formula) and the MiniMax song graph.

**Naming rule (hexe, Nov 9):** underscores only, `ns_<kind>_<name>`, e.g. `ns_width`, `ns_fixed_negative`,
`ns_toggle_lighting`, `ns_slot_location`. The same name then works as a node title, a Set/Get name and a file name
(no `:`, which Windows forbids in file names, and no spaces).
