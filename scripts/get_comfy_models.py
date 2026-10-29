"""Download the model files Nightshift's workflows load into your ComfyUI models folder (skips files you already have).

    python scripts/get_comfy_models.py --comfy-dir <ComfyUI folder> [--set core flux3] [--list]

Sets: core (Flux 2 Klein 9B, LTX 2.3, MiniMax Music 3, ~120 GB), flux3 (FLUX 3 Image Klein, optional). Gated repos (Black Forest
Labs) need you to accept the license on Hugging Face first and a token in HF_TOKEN. These are the sources we know carry
the exact file names the graphs load; any copy with the same name works.
"""
import argparse
import os
import shutil
import sys
import urllib.request

HF = "https://huggingface.co/{}/resolve/main/{}"
# (set, models/<folder>, file name, repo, path in repo)
FILES = [
    ("core", "diffusion_models", "flux-2-klein-base-9b-fp8.safetensors", "black-forest-labs/FLUX.2-klein-base-9b-fp8", "flux-2-klein-base-9b-fp8.safetensors"),
    ("core", "text_encoders", "qwen_3_8b_fp8mixed.safetensors", "Comfy-Org/Flux-2-Klein-9B", "split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors"),
    ("core", "vae", "full_encoder_small_decoder.safetensors", "black-forest-labs/FLUX.2-small-decoder", "full_encoder_small_decoder.safetensors"),
    ("core", "loras", "lenovo_flux_klein9b.safetensors", "Danrisi/Lenovo_FluxKlein9b_base", "lenovo_flux_klein9b.safetensors"),
    ("core", "diffusion_models", "ltx-2.3-22b-distilled-1.1-int8-ConvRot.safetensors", "obsxrver/ComfyUI-Native-INT8_ConvRot", "checkpoints/ltx-2.3-22b-distilled-1.1-int8-ConvRot.safetensors"),
    ("core", "unet", "ltx-2.3-22b-dev-Q4_K_M.gguf", "unsloth/LTX-2.3-GGUF", "ltx-2.3-22b-dev-Q4_K_M.gguf"),
    ("core", "text_encoders", "gemma_3_12B_it_fp4_mixed.safetensors", "Comfy-Org/ltx-2", "split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors"),
    ("core", "text_encoders", "ltx-2.3_text_projection_bf16.safetensors", "Kijai/LTX2.3_comfy", "text_encoders/ltx-2.3_text_projection_bf16.safetensors"),
    ("core", "text_encoders", "gemma-3-12b-it-qat-UD-Q4_K_XL.gguf", "unsloth/gemma-3-12b-it-qat-GGUF", "gemma-3-12b-it-qat-UD-Q4_K_XL.gguf"),
    ("core", "text_encoders", "ltx-2.3-22b-dev_embeddings_connectors.safetensors", "unsloth/LTX-2.3-GGUF", "text_encoders/ltx-2.3-22b-dev_embeddings_connectors.safetensors"),
    ("core", "vae", "ltx-2.3-22b-dev_video_vae.safetensors", "unsloth/LTX-2.3-GGUF", "vae/ltx-2.3-22b-dev_video_vae.safetensors"),
    ("core", "vae", "ltx-2.3-22b-dev_audio_vae.safetensors", "unsloth/LTX-2.3-GGUF", "vae/ltx-2.3-22b-dev_audio_vae.safetensors"),
    ("core", "vae", "taeltx2_3.safetensors", "Kijai/LTX2.3_comfy", "vae/taeltx2_3.safetensors"),
    ("core", "latent_upscale_models", "ltx-2.3-spatial-upscaler-x2-1.1.safetensors", "Lightricks/LTX-2.3", "ltx-2.3-spatial-upscaler-x2-1.1.safetensors"),
    ("core", "loras", "ltx-2.3-22b-distilled-lora-384.safetensors", "Lightricks/LTX-2.3", "ltx-2.3-22b-distilled-lora-384.safetensors"),
    ("core", "loras", "ltx-2.3-22b-distilled-1.1_lora-dynamic_fro09_avg_rank_111_bf16.safetensors", "Kijai/LTX2.3_comfy", "loras/ltx-2.3-22b-distilled-1.1_lora-dynamic_fro09_avg_rank_111_bf16.safetensors"),
    ("core", "loras", "LTX2.3_Crisp_Enhance.safetensors", "vrgamedevgirl84/LTX_2.3_Crisp_Enhance_Style_LoRa", "LTX2.3_Crisp_Enhance.safetensors"),
    ("core", "loras", "LTX2.3_Soft_Enhance.safetensors", "vrgamedevgirl84/LTX_2.3_Soft_Enhance_Style_LoRa", "LTX2.3_Soft_Enhance.safetensors"),
    ("core", "loras/LTX2", "LTX-2.3-OmniNFT-RL-Lora_bf16.safetensors", "Kijai/LTX2.3_comfy", "loras/LTX-2.3-OmniNFT-RL-Lora_bf16.safetensors"),
    ("core", "loras", "ltx-2-19b-ic-lora-detailer.safetensors", "Lightricks/LTX-2-19b-IC-LoRA-Detailer", "ltx-2-19b-ic-lora-detailer.safetensors"),
    ("core", "diffusion_models", "MelBandRoformer_fp32.safetensors", "Kijai/MelBandRoFormer_comfy", "MelBandRoformer_fp32.safetensors"),
    ("core", "diffusion_models", "minimax_music3_dit_fp16.safetensors", "Comfy-Org/MiniMax-Music-3", "diffusion_models/minimax_music3_dit_fp16.safetensors"),
    ("core", "text_encoders", "minimax_music3_text_encoder_pruned_int8_convrot.safetensors", "Comfy-Org/MiniMax-Music-3", "text_encoders/minimax_music3_text_encoder_pruned_int8_convrot.safetensors"),
    ("core", "vae", "minimax_music3_dav.safetensors", "Comfy-Org/MiniMax-Music-3", "vae/minimax_music3_dav.safetensors"),
    ("flux3", "diffusion_models", "flux3-image-klein-int8-convrot.safetensors", "black-forest-labs/flux-3-image-klein-comfy", "diffusion_models/flux3-image-klein-int8-convrot.safetensors"),
    ("flux3", "text_encoders", "qwen3vl_4b_int8_convrot.safetensors", "black-forest-labs/flux-3-image-klein-comfy", "text_encoders/qwen3vl_4b_int8_convrot.safetensors"),
    ("flux3", "vae", "flux2-vae.safetensors", "black-forest-labs/flux-3-image-klein-comfy", "vae/flux2-vae.safetensors"),
]


def url(repo, path):
    return HF.format(repo, path)


def find_existing(models, name):
    for dirpath, _, files in os.walk(models):
        if name in files:
            return os.path.join(dirpath, name)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--comfy-dir", help="your ComfyUI folder (the one with models/)")
    ap.add_argument("--set", nargs="+", default=["core"], choices=["core", "flux3"])
    ap.add_argument("--list", action="store_true", help="print the files and links, download nothing")
    a = ap.parse_args(argv)
    rows = [r for r in FILES if r[0] in a.set]
    if a.list or not a.comfy_dir:
        for s, folder, name, repo, path in rows:
            print(f"{s:6} models/{folder:22} {name}\n       {url(repo, path)}")
        return 0
    models = os.path.join(os.path.abspath(os.path.expanduser(a.comfy_dir)), "models")
    if not os.path.isdir(models):
        sys.exit(f"no models/ folder in {a.comfy_dir}")
    token = os.environ.get("HF_TOKEN")
    for s, folder, name, repo, path in rows:
        have = find_existing(models, name)
        if have:
            print(f"have  {os.path.relpath(have, models)}")
            continue
        dst = os.path.join(models, *folder.split("/"), name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        print(f"get   models/{folder}/{name}  <- {repo}")
        req = urllib.request.Request(url(repo, path), headers={"Authorization": f"Bearer {token}"} if token else {})
        try:
            with urllib.request.urlopen(req, timeout=60) as r, open(dst + ".part", "wb") as f:
                total, done = int(r.headers.get("Content-Length") or 0), 0
                while True:
                    chunk = r.read(8 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        print(f"\r      {done / 2**30:.1f} / {total / 2**30:.1f} GB", end="", flush=True)
            print()
            shutil.move(dst + ".part", dst)
        except Exception as e:
            print(f"\n  !!  {name}: {e}" + ("  (gated: accept the license on Hugging Face and set HF_TOKEN)" if "401" in str(e) or "403" in str(e) else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
