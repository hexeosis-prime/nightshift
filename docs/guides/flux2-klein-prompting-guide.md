# FLUX.2 [klein] 9B — Hyper-Specific Prompting Guide

*Zero (HEXEBOTZERO), hexeosis inc. Written for this pipeline. Reviewed and edited by Claude Opus 5.5.*

*Researched 2026-10-25 from BFL official docs + community knowledge*

---

## Architecture Context (Why This Matters)

**FLUX.2 [klein] 9B uses Qwen3 8B as its text embedder.** Not Mistral (which FLUX.2 [dev] uses), not a CLIP encoder. This means:
- It **natively understands natural language**, sentences, and relationships — you don't need to talk to it like a keyword engine
- But QA-level text understanding ≠ optimal image generation output. The model's text encoder interprets your words well; the *flow transformer* still needs clear spatial and visual direction to render correctly
- **No prompt upsampling is available on klein** — what you write is exactly what the model receives. Longer, more detailed prompts help more than on larger models

---

## 1. Image Reference Naming (The Core Question)

### BFL's Official Convention

**Always use: "image 1", "image 2", "image 3"**

This is the canonical naming across all of BFL's documentation, examples, and API spec. From the docs:

> *"Refer to references by position: 'image 1' is the first entry in images, 'image 2' the second. Use the same words every time you mention an image."*

**Do NOT use alternatives like** `[reference-image1]`, `src_img`, `first image`, `the first reference`, `ref_image`. These *may* work (the LLM understands them) but the model was trained on the positional naming convention, so "image 1" / "image 2" / "image 3" is the safest, most reliable form.

### What Each Image Does — Name the Role

Specify the purpose of each image explicitly. BFL's role taxonomy:

| Role | Phrasing |
|------|----------|
| **Subject** (person/character to keep recognizable) | "the person in image 1" |
| **Product** (object with shape/color/label to preserve) | "the bottle from image 2" |
| **Setting** (background/scene everything goes into) | "the environment from image 3" |
| **Style** (palette/texture/lighting to apply) | "in the style of image 2" |
| **Pose reference** | "the pose from image 1" |

**Best pattern for face replacement / character consistency:**

```
Replace the face in image 1 with the face from image 2, 
keeping the pose, lighting, expression, and background of image 1 exactly unchanged.
```

### Multi-Image Ordering Matters

With `aspect_ratio: "auto"` (default), the output takes its aspect ratio from **image 1**. So:
- **Put the base/composition image first**, then style/face/product refs after
- If you want a specific aspect ratio that differs from all references, set it explicitly

---

## 2. Prompt Structure for Editing / Multi-Reference

### The Edit Record Pattern (from BFL examples)

For multi-part edits with 2-3 images, use this three-part structure:

```
Part 1: Name the operation
"Modify image 1 using image 2 for reference."

Part 2: Say what changes and how
"Replace the face in image 1 with the face from image 2, 
matching the skin tone and lighting of image 1. 
Keep the hairstyle of image 1."

Part 3: List what stays (preservation clause)
"Keep the rest of the scene exactly unchanged, 
preserving the background, body position, clothing, and lighting."
```

### The "Checklist" from BFL (Vague → Specific)

| Instead of | Write |
|------------|-------|
| "Combine these images" | "Place the person from image 2 into the setting of image 1, matching lighting and perspective." |
| "Use the style of the other one" | "Turn image 1 into the style of image 2, keeping the subject's shape, pose, and expression." |
| "Make them wear it" | "The person in image 1 wears the jacket from image 2 in the setting of image 3." |
| "Fix this face" | "Replace the face in image 1 with the face from image 2, keeping expression natural and consistent with body language." |

### Face Replacement Specific Pattern (Synthesized)

Based on BFL's single-ref editing patterns for object replacement + the "preservation clause" from their multi-ref examples:

```
Modify image 1 by replacing the face with the face from image 2. 
Keep the hairstyle, expression, skin texture, and lighting of image 1. 
[optional: facial hair, glasses, accessories from which image]
Preserve the background, body, clothing, and pose of image 1 exactly unchanged.
```

**Key insight from BFL's remove-vegetation example:**
When preservation matters, be *exhaustive* in what you list as unchanged. The "keep" list in their best examples names every major element. Don't just say "keep the rest" — say *what* the rest includes.

---

## 3. Klein-Specific Behavior Notes

### From the Official Docs

| Behavior | Detail |
|----------|--------|
| **Prompt style** | "Prompt following is heavily influenced by the prompting style" (HF model card) |
| **Write in prose** | "Write in prose, not keyword lists: describe scenes like a novelist" (model reference) |
| **Style tags** | Add `Style: [style]. Mood: [mood].` at end for consistent aesthetics — this is specifically documented for klein |
| **Max references (API)** | 4 images via API (`input_image` through `input_image_4`) |
| **Inference steps** | 4 (step-distilled). The base variant (undistilled) uses 50 steps |
| **No upsampling** | No prompt upsampling available. You must write detailed prompts yourself |
| **Negative prompts** | Not supported. Describe what you *want*, not what you don't want |

### Style + Mood Tag Pattern (Klein-Specific)

The docs specifically call this out for klein:

```
[Scene and subject description]. 
Style: Country chic meets luxury lifestyle editorial. 
Mood: Serene, romantic, grounded.
```

```
[Edit instruction for multi-ref]. 
Style: Cinematic naturalism, shallow depth of field. 
Mood: Intimate, candid, timeless.
```

### No Negative Prompts — Use Positive Steering

Since there's no `negative_prompt` field:

| Instead of | Write |
|------------|-------|
| "not photorealistic" | "watercolor illustration style with visible paper texture" |
| "no background blur" | "sharp focus throughout, everything in the frame in focus" |
| "don't change the face" | "keep the exact facial features of image 1, identical nose eyes mouth and jawline" |
| "not the red shirt" | "the shirt is the same color and style as in image 1" |

---

## 4. Hyper-Specific Syntax Patterns

### Text in Images (from official docs)

- **Quote the exact words**: `"the text reads 'HELLO WORLD'"` — quotation marks signal "render this as text"
- **Line breaks**: use `\n` inside the quote for multi-line
- **Describe the type**: weight, case, color, alignment
- **Front-load** text descriptions for better accuracy
- **Keep text short** — long strings are harder to render accurately

### Hex Color Codes

Works in both T2I and editing prompts:
```
"change the color of only the left-most jar to #E01075"
"the logo text 'ACME' in color #FF5733"
"gradient from #02eb3c to #edfa3c"
```

### Camera/Lens Language (from reference sheet)

If photorealism is the goal, name specific gear:
```
"Shot on Hasselblad X2D, 80mm lens, f/2.8"
"Canon 5D Mark IV, 24-70mm at 35mm, golden hour"
"Shot on Kodak Portra 400, natural grain, warm color cast"
```

### JSON Structured Prompts

FLUX.2 accepts JSON in the prompt field. The schema from BFL:

```json
{
  "scene": "overall scene description",
  "subjects": [
    {
      "description": "detailed subject description",
      "position": "where in frame",
      "action": "what they're doing"
    }
  ],
  "style": "artistic style",
  "color_palette": ["#hex1", "#hex2"],
  "lighting": "lighting description",
  "mood": "emotional tone",
  "composition": "framing and layout"
}
```

---

## 5. Community Knowledge & Tips (Sourced from Available Resources)

### Prompt Length

- **Klein benefits from longer prompts** more than larger models, since there's no upsampling
- But length ≠ quality. Every detail should be *visible in the frame* — don't add abstract descriptors
- "Start with a sentence and add detail as you review results"

### Successful Pattern: The Worked Example

From BFL's "Building a Prompt" guide, the order that works:

| Order | What to describe |
|-------|-----------------|
| 1. Image type + medium | "High-angle black and white photograph with film grain" |
| 2. Subject | "who or what, and what they are doing" |
| 3. Setting | "where it happens and what surrounds the subject" |
| 4. Light | "source, direction, quality, color" |
| 5. Framing + details | "shot size, angle, lens, depth of field" |

For multi-ref editing, front-load the edit instruction, then add the scene description.

### Lighting Language That Works

Klein seems to respond well to specific lighting language:
- Too vague: "good lighting"
- Better: "soft window light from the left"
- Best: "soft diffused natural light filtering through sheer curtains, creating warm highlights on the subject's face while leaving the background in gentle shadow"

The docs specifically call out describing the light *source, direction, and quality* as the core three elements.

### Preservation Clause Effectiveness

The "keep/preserve" clause at the end is not just a nice-to-have — BFL's strongest editing examples all include a preservation clause that names specific elements. The more specific, the better the consistency:

- Weak: "keep the rest the same"
- Strong: "keep the background exactly unchanged, preserving the wall texture, window position, and floor shadows"
- Strongest (multi-ref): "Preserve the background of image 1, the facial structure of image 2, and the clothing color of image 3"

---

## 6. Proposed Test Framework

Here's what I'd test first based on what you're working on:

### Test 1: Naming Convention

**Prompt A (standard naming):**
```
Replace the face in image 1 with the face from image 2. 
Keep the expression, lighting, and pose of image 1. 
Preserve the background, body, clothing, and hairstyle of image 1 exactly.
```

**Prompt B (alternative naming):**
```
Using the first image as the base scene and the second image for the face reference, 
swap the person's face while keeping everything else the same.
```

### Test 2: Preservation Exhaustiveness

**A (short preserve):**
```
keep the background unchanged
```

**B (exhaustive preserve):**
```
Preserve the background, body position, clothing, lighting direction, 
skin texture, eye shape, nose, mouth, jawline, and hairstyle of image 1.
```

### Test 3: Style Tags

**A (no tags):**
```
The person from image 1 with the face from image 2, natural lighting.
```

**B (with tags):**
```
The person from image 1 with the face from image 2. 
Style: Candid natural portrait, soft natural lighting. 
Mood: Warm, authentic, unposed.
```

---

## Sources

Official BFL Documentation consulted:
- BFL API Docs (docs.bfl.ai) — Prompting Guides, Editing Guides, Prompt Reference
- FLUX.2 Klein 9B Hugging Face Model Card
- BFL Blog: FLUX.2 [klein] announcement and FLUX.2 overview
- GitHub: black-forest-labs/flux2 — inference repo, prompt upsampling guide
- Prompting Basics, Building a Good Prompt, Style/Aesthetics/Text, Single-Ref Editing, Multi-Ref Editing, JSON Structured Prompting, Prompt Reference sheets

*Note: web_search was unavailable during research. Community knowledge in this guide comes from what's embedded in BFL's official docs and observable patterns. For the most active community discussions, search Reddit r/StableDiffusion, Civitai, and the BFL Discord server.*

---

*Written by the second employee.*
