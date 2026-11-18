# FLUX 3 all-in-one graph: speed, references, identity (Nov 18)

Tests on the RTX 3090 with hexe's `img_flux3` (padded references) and `vid_ltx` (Nov 17). Scripts: `scripts/wf_test.py`;
identity edits through the builder on a copy of the gpu-a project (`runs/gpu-f3`, 9:16, the red-haired lead).

**Model files.** `flux3-image-klein-int8-convrot` (hyphens, ComfyUI's templates) is the distilled model; the older
underscore mirror `flux3_image_klein_int8_convrot` is the base. The distilled file at 15 steps cfg 1 (er_sde) matches its
50-step cfg 3.5 still in 5 s instead of 35 s; the base file at 15 steps breaks poses. Cfg 1 is "no guidance".

**Scene edits** (relight, compose from 2-4 references) work on the distilled model at 16 steps cfg 1: the dusk relight was
the same at 16 steps (12 s) as at 50 steps cfg 3.5 (58 s); four references composed as asked. The prompt upsampler helped
put a second reference's person into the scene (off: she did not clearly appear).

**Identity edits don't carry the sheet's face on FLUX 3.** Face match to the character sheet (SFace cosine), 3 shots:

| | s02 | s04 | s05 |
| --- | --- | --- | --- |
| FLUX 3 base still (before the edit) | 0.25 | 0.13 | 0.27 |
| distilled, 16 steps cfg 1 | 0.23 | 0.12 | 0.27 |
| distilled, 16 steps + upsampler | 0.32 | 0.11 | 0.40 |
| distilled, 50 steps cfg 3.5 | 0.23 | 0.16 | 0.28 |
| distilled, raw references at 1 MP (no pad) | 0.22 | | 0.25 |
| base file, 50 steps cfg 1, raw references | 0.25 | | 0.22 |
| Flux 2 Klein identity edit (gpu-a, its own base still) | 0.68 | 0.41 | 0.55 |

The FLUX 3 edits keep the base still almost unchanged (pose, light, face); the upsampler carries the clothing (white
T-shirt) and a little of the face. Reference size and padding make no difference. Flux 2 edits replace the face with the
sheet's (freckles, eye shape) but recompose more. So identity stays on Flux 2 (`image_model` flux2, the default) until a
FLUX 3 wording or setting carries the face; FLUX 3 is the faster, cleaner choice for stills and scene edits.
