# Workflows

`workflows/` holds the ComfyUI graphs the first video was made with, exported in **API format**, each with a **map**
(`<name>.map.json`) that names the inputs Nightshift fills in. `project.json` `workflows` says which graph does which job, so
you can point any job at your own graph.

| job | file | what it does |
|---|---|---|
| `still` | `still_flux` | Flux 2 Klein 9B text to image. One structured prompt (person / outfit / action / location + style switches for framing, photo look, indoor/outdoor, day/night, atmosphere) assembled inside the graph; image size follows the project's `work_size` |
| `sheet_text` | `sheet_from_text` | Flux 2 Klein 9B character reference sheet from a written description (front view with the face covered by a white circle, back view, macro face close-up, on grey) |
| `sheet_image` | `sheet_from_image` | the same layout made from a picture of the character |
| `edit2` | `edit_flux_2image` | Flux 2 Klein 9B edit with two images (identity edits, relights, environment changes) |
| `edit3` | `edit_flux_3image` | the same with a third image (a second character) |
| `ff` | `vid_ltx_ff` | LTX 2.3 image to video from a first frame, two-stage with x2 spatial upscale |
| `fflf` | `vid_ltx_fflf` | LTX 2.3 first + last frame with song audio, guide strengths and an arrive frame |
| `lipsync` | `vid_ltx_lipsync` | LTX 2.3 image to video driven by a song section (vocal separated with MelBand RoFormer inside the graph) |
| `t2v` | `vid_ltx_t2v` | LTX 2.3 text to video |
| `song` | `song_minimax_m3` | MiniMax Music 3 text to song |

With `"image_model": "flux3"` in `project.json` (the FLUX 3 Klein button in the app) these jobs switch to FLUX 3 Image Klein
graphs, all core ComfyUI nodes (0.41+), no custom node packs:

| job | file | what it does |
|---|---|---|
| `still` | `still_flux3` | text to image from one caption the builder writes (shot, person, outfit, action, setting, the world's `style`) |
| `sheet_text` / `sheet_image` | `sheet_from_text_flux3` / `sheet_from_image_flux3` | the same three-view character sheet, from the description or from a picture |
| `edit2` / `edit3` | `edit_flux3_2image` / `edit_flux3_3image` | multi-reference edits through `Set Reference Multi Latent`; prompts written for Flux 2's "[reference_image2]" / "image 2" are rewritten to `<ref_image_1>` automatically |

They load the step-distilled int8 checkpoint (16 steps, cfg 1). For the 50-step base checkpoint set the roles `model`,
`steps` and `cfg` (e.g. in a project-level copy of the graph, or by editing the defaults in the `.json`).

Video-to-video and an image glitch utility were tried during the first video and left out for now (see ROADMAP.md).

## Custom nodes

A recent ComfyUI has the LTX 2.3, MiniMax Music 3, seed and switch nodes in core. On top of that:

| pack | used by |
|---|---|
| [ComfyUI-KJNodes](https://github.com/kijai/ComfyUI-KJNodes) | all LTX graphs (VAE loader, resize, NAG, preview override, calculator, constants) |
| [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) | `vid_ltx_ff`, `vid_ltx_t2v` (GGUF model and text encoder) |
| [ComfyUI-INT8-Fast](https://github.com/BobJohnson24/ComfyUI-INT8-Fast) | `vid_ltx_fflf`, `vid_ltx_lipsync` (int8 ConvRot model loader) |
| [ComfyUI-MelBandRoFormer](https://github.com/kijai/ComfyUI-MelBandRoFormer) | `vid_ltx_lipsync` |
| [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) | `vid_ltx_fflf`, `vid_ltx_lipsync` |
| [rgthree-comfy](https://github.com/rgthree/rgthree-comfy) | `vid_ltx_fflf`, `still_flux`, `sheet_from_text` (Power Lora Loader, Any Switch) |
| [ComfyUI_essentials](https://github.com/cubiq/ComfyUI_essentials) | edits, `sheet_from_image` (image resize) |
| [ComfyUI-Custom-Scripts](https://github.com/pythongosssss/ComfyUI-Custom-Scripts) | `vid_ltx_lipsync` |
| [ComfyUI-mxToolkit](https://github.com/Smirnov75/ComfyUI-mxToolkit) | `vid_ltx_fflf` (sliders) |
| [ComfyUI-MediaMixer](https://github.com/DoctorDiffusion/ComfyUI-MediaMixer) | `vid_ltx_fflf`, `still_flux` (PromptJournal) |
| [WhatDreamsCost-ComfyUI](https://github.com/WhatDreamscost/WhatDreamsCost-ComfyUI) | `vid_ltx_fflf` (LoadAudioUI) |
| [ComfyUI-Easy-Use](https://github.com/yolain/ComfyUI-Easy-Use) | `still_flux` (prompt replace) |

`nightshift doctor` asks your ComfyUI for every node type each configured graph uses and lists anything missing.

## Model files

File names as the graphs load them (`nightshift workflows --models` prints this from the graphs themselves).
`python scripts/get_comfy_models.py --comfy-dir <ComfyUI>` downloads every missing one into the right `models/` folder
(`--set core flux3` adds FLUX 3 Klein; `--list` prints the files with their Hugging Face links). Black Forest Labs' repos are
gated: accept the license on Hugging Face and set `HF_TOKEN` first. Any copy with the same file name works.

**Flux 2 Klein 9B** (stills, edits): `flux-2-klein-base-9b-fp8.safetensors` (diffusion model), `qwen_3_8b_fp8mixed.safetensors`
(text encoder), `full_encoder_small_decoder.safetensors` (VAE); still graph also `lenovo_flux_klein9b.safetensors` (LoRA).

**LTX 2.3** (video):
- `ltx-2.3-22b-distilled-1.1-int8-ConvRot.safetensors` (fflf, lipsync) or `ltx-2.3-22b-dev-Q4_K_M.gguf` (ff, t2v)
- `gemma_3_12B_it_fp4_mixed.safetensors` + `ltx-2.3_text_projection_bf16.safetensors` (text encoder; t2v uses
  `gemma-3-12b-it-qat-UD-Q4_K_XL.gguf` + `ltx-2.3-22b-dev_embeddings_connectors.safetensors`)
- `ltx-2.3-22b-dev_video_vae.safetensors`, `ltx-2.3-22b-dev_audio_vae.safetensors`, `taeltx2_3.safetensors` (preview VAE)
- `ltx-2.3-spatial-upscaler-x2-1.1.safetensors`
- LoRAs: `ltx-2.3-22b-distilled-lora-384.safetensors`, `ltx-2.3-22b-distilled-1.1_lora-dynamic_fro09_avg_rank_111_bf16.safetensors`,
  `LTX2.3_Crisp_Enhance.safetensors`, `LTX2.3_Soft_Enhance.safetensors`, `LTX-2.3-OmniNFT-RL-Lora_bf16.safetensors`,
  `ltx-2-19b-ic-lora-detailer.safetensors`
- `MelBandRoformer_fp32.safetensors` (vocal separation for lip-sync)

**FLUX 3 Image Klein** (optional, `image_model: flux3`), from
[black-forest-labs/flux-3-image-klein-comfy](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy) (gated: accept the
license first): `diffusion_models/flux3-image-klein-int8-convrot.safetensors` (or `flux3-image-klein-base-int8-convrot.safetensors`),
`text_encoders/qwen3vl_4b_int8_convrot.safetensors`, `vae/flux2-vae.safetensors`.

**MiniMax Music 3** (song): `minimax_music3_dit_fp16.safetensors`, `minimax_music3_text_encoder_pruned_int8_convrot.safetensors`,
`minimax_music3_dav.safetensors`.

## Maps

```json
{
 "workflow": "vid_ltx_ff.json",
 "kind": "ff",
 "roles": {
  "image":    {"node": "149", "input": "image"},
  "prompt":   {"node": "257:220", "input": "text"},
  "negative": {"node": "257:204", "input": "value"},
  "frames":   [{"node": "257:255", "input": "length"}, {"node": "257:254", "input": "frames_number"}],
  "seed":     [{"node": "257:218", "input": "noise_seed"}, {"node": "257:228", "input": "noise_seed", "offset": 1}]
 },
 "outputs":  {"video": {"node": "75", "input": "filename_prefix"}}
}
```

- A role is one target or a list (all get the value). `offset` adds to numbers (two samplers, two seeds); `type` casts
  (`int`, `float`, `str`) for nodes that are picky (a seconds slider wants an int, an expression wants a string).
- `outputs` are the save nodes, by name. A graph may have several (say a photoreal and an illustrated model side by side);
  the shot's `still` picks which one is kept and the others are pruned before the job is queued.
- `defaults` (`[{"node": "5258", "input": "switch", "value": true}]`) are set on every job: switches that must be on,
  fixed-seed toggles.
- A negative that is wired from another node (not typed into a box) gets a concat hook:
  `"negative": {"concat_from": ["152:549", 0], "into": [{"node": "1362:1327", "input": "source"}]}`. The builder splices a
  StringConcatenate node in and appends each shot's never-list.

**Roles the builder uses**, by job: `still`: `person outfit action location female_count male_count switch.<name> long_edge short_edge
vertical seed negative` (or just `prompt seed negative` for a plain text-to-image graph); `sheet_text`: `description negative seed`; `sheet_image`: `image1 prompt seed`; `edit2`/`edit3`: `image1 image2 [image3] prompt
width height seed`; `ff`: `image prompt negative frames width height seed`; `fflf`: `image last_image prompt negative seconds audio audio_start
audio_end audio_seconds first_strength last_strength arrive_frame width height seed`; `lipsync`: `image prompt negative audio audio_start
audio_seconds width height long_edge seed`; `t2v`: `prompt negative frames width height seed`; `song`: `caption lyrics max_seconds seed`.

**No map?** Title the nodes in ComfyUI `ns:prompt`, `ns:seed`, `ns:image`, `ns:output:video` ... and the roles are found by
title. **Using your own graph:** Workflow menu > Export (API), save it as `workflows/<name>.json` (or in the project's own
`workflows/` folder), write its map or title its nodes, set `project.json` `"workflows": {"ff": "<name>"}`, run
`nightshift doctor`.
