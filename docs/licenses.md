# Licenses

Nightshift's own code is under the Apache License 2.0 (copyright hexeosis inc.). The models it drives are not covered by that, and their terms differ. This is a summary as of
October 2026, not legal advice: read the license files themselves before you make anything commercial.

| model | license | weights for commercial use | outputs |
|---|---|---|---|
| FLUX.2 [klein] 9B (Black Forest Labs) | FLUX Non-Commercial License v2.1 | no, a commercial license is sold by BFL | section 2(d) allows commercial use of outputs, but section 4(a) restricts "data produced by" the model for commercial purposes; the text is inconsistent, so check with BFL |
| FLUX 3 Image Klein (Black Forest Labs), optional | FLUX Kommunity License v1.0 | non-commercial use; outputs may be used commercially by a "Qualifying User" (under US$5M annual revenue, with the license's content-review and AI-disclosure conditions) | BFL claims no ownership of outputs |
| LTX-2 / LTX 2.3 (Lightricks) | LTX-2 Community License | yes for organisations under US$10M annual revenue; above that a paid license | Lightricks claims no rights in outputs |
| MiniMax Music 3 (MiniMax) | open weights under CC BY-NC 4.0 | no; commercial use through MiniMax's API, or (since August 2026) a commercial license sold through Comfy | non-commercial when self-hosted |
| YuNet, SFace (OpenCV Zoo) | MIT / Apache 2.0 | yes | |

Sources: [FLUX 3 Image Klein LICENSE](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy/blob/main/LICENSE.md),
[FLUX.2-klein-base-9B LICENSE](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9B/blob/main/LICENSE.md),
[LTX-2.3 LICENSE](https://huggingface.co/Lightricks/LTX-2.3/blob/main/LICENSE),
[MiniMax Music 3 open weights, CC BY-NC 4.0](https://mer.vin/news/minimax-music-3-is-open-weight-but-not-open-for-business/),
[Comfy as MiniMax's commercial reseller](https://blog.comfy.org/p/comfy-is-now-the-only-official-reseller).

Several of these require accepting terms on Hugging Face before download.
