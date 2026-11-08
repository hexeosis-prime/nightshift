# Picks from the overnight run, Nov 6-7 2026

Every pick with the job that made it: workflow, seed, size, inputs and the full prompt.
Re-run any of these with `promo_tonight.py` (same name, seed and prompt give the same result).

## Aesthetic favorites

### x_yoga_filmic_clip_v_v0
- workflow: vid_ltx_ff (LTX 2.3 first frame, 2-stage x2)
- size 768x1280, seed 9700, 5 s, render 177.0 s
- inputs: x_yoga_filmic_v
- prompt:
  > Slow lateral tracking shot along the row of people as they flow together out of warrior pose and raise their arms overhead, breathing in unison. The instructor smiles and nods. Sunbeams shift gently across the floor. Smooth, steady camera. Moody cinematic film look, high contrast, deep shadows, film grain, anamorphic.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### x_yoga_filmic_v  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 768x1280, seed 6704, render 25.2 s
- prompt:
  > A bright sunlit yoga studio with warm oak floors and tall floor-to-ceiling windows that look out onto lush green trees. A small class of adults on natural-color mats hold warrior two pose, an instructor in front guides them with a warm smile. Hanging plants, golden morning sunbeams across the room. Cinematic film still from an arthouse feature, shot on 35mm Kodak Vision3 500T film with an anamorphic lens. Dramatic low-key contrast lighting: one strong motivated key light, deep shadows, rich blacks, subtle halation, heavy film grain, muted earthy palette with warm highlights. Moody, intimate, quiet. Natural clear healthy skin, real everyday adults. No text, no logos. 
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

### connect_h_v0_ff
- workflow: vid_ltx_ff (LTX 2.3 first frame, 2-stage x2)
- size 1280x768, seed 9100, 5 s, render 182.1 s
- inputs: connect_h_v0
- prompt:
  > Slow orbiting camera around the low table as the friends laugh and talk, one pours tea for another, someone leans in and touches a friend's shoulder. Lively, warm, natural moment. Smooth, steady camera.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### connect_h_v0  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 1280x768, seed 4447, render 25.7 s
- prompt:
  > A warm tea lounge at a wellness center in the late afternoon. Friends sit on floor cushions around a low wooden table with clay teacups and a teapot, laughing together mid-conversation. Big windows with greenery behind them, woven textures, plants, warm golden light. Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

### x_monk_v_v0
- workflow: vid_ltx_t2v (LTX 2.3 text to video)
- size 768x1280, seed 9700, 6 s, render 209.6 s
- prompt:
  > After a profound meditation, a Buddhist monk opens his eyes to a breathtaking world bathed in golden light. Lush hills roll into the distance, covered in vibrant greenery that shimmers with life. Delicate wildflowers bloom in brilliant reds, deep blues and sunny yellows. Crystal-clear waters trickle over smooth stones. Majestic mountains rise in the background, their peaks kissed by clouds, while serene lakes reflect the azure sky. Birds soar overhead and butterflies flit among the blossoms. Each moment feels suspended in beauty and peace. Photoreal, cinematic.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

### x_connect_filmic_clip_v_v0
- workflow: vid_ltx_ff (LTX 2.3 first frame, 2-stage x2)
- size 768x1280, seed 9700, 5 s, render 176.7 s
- inputs: x_connect_filmic_v
- prompt:
  > Slow orbiting camera around the low table as the friends laugh and talk, one pours tea for another, someone leans in and touches a friend's shoulder. Lively, warm, natural moment. Smooth, steady camera. Moody cinematic film look, high contrast, deep shadows, film grain, anamorphic.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### x_connect_filmic_v  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 768x1280, seed 6707, render 25.3 s
- prompt:
  > A warm tea lounge at a wellness center in the late afternoon. Friends sit on floor cushions around a low wooden table with clay teacups and a teapot, laughing together mid-conversation. Big windows with greenery behind them, woven textures, plants, warm golden light. Cinematic film still from an arthouse feature, shot on 35mm Kodak Vision3 500T film with an anamorphic lens. Dramatic low-key contrast lighting: one strong motivated key light, deep shadows, rich blacks, subtle halation, heavy film grain, muted earthy palette with warm highlights. Moody, intimate, quiet. Natural clear healthy skin, real everyday adults. No text, no logos. 
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

### x_connect_empty_h
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 1280x768, seed 6807, render 24.2 s
- prompt:
  > A warm tea lounge at a wellness center in late afternoon, floor cushions around a low wooden table with clay teacups and a steaming teapot, big windows with greenery, woven textures and plants, golden light. Completely empty, no people anywhere in the scene. Photoreal cinematic photograph, soft natural light, gentle film grain, full-frame cinema camera, 35mm lens, shallow depth of field. No text, no logos, no signage. 
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

## Technical merit

### phone_in_v_fflf_v0
- workflow: vid_ltx_fflf (LTX 2.3 first+last frame, silent audio)
- size 768x1280, seed 9300, 5 s, render 141.0 s
- inputs: phone_in_v, cave_v_v0
- prompt:
  > The camera pushes slowly forward toward the phone screen and passes through it, the glowing salt cave on the screen grows until it fills the whole frame and becomes the real salt cave room. Smooth, continuous, magical push-in, no cut.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### phone_in_v  (input)
- workflow: edit_flux3_2image (FLUX 3 Klein edit, 50 steps, cfg 1)
- size 768x1280, seed 7770, render 45.0 s
- inputs: phone_in_v_base, cave_v_v0
- prompt:
  > Keep <ref_image_0> exactly: the same person, hand, phone, room and light. Replace only the phone's screen content with the picture from <ref_image_1>, fitted edge to edge inside the screen, bright and sharp. No text, no app icons, no status bar.

#### cave_v_v0  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 768x1280, seed 4444, render 25.3 s
- prompt:
  > Inside a Himalayan salt cave relaxation room at a modern wellness center. The walls and arched ceiling are built from glowing amber and rose salt bricks lit from behind, the floor is a bed of fine white salt crystals. People recline on cushioned zero-gravity loungers wrapped in soft cream blankets, eyes closed, peaceful. Warm low glow, a faint haze in the air. Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

### x_phone_in_more_h_v1
- workflow: vid_ltx_fflf (LTX 2.3 first+last frame, silent audio)
- size 1280x768, seed 9701, 5 s, render 145.5 s
- inputs: phone_in_h, cave_h_v0
- prompt:
  > The camera pushes slowly forward toward the phone screen and passes through it, the glowing salt cave on the screen grows until it fills the whole frame and becomes the real salt cave room. Smooth, continuous, magical push-in, no cut.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### phone_in_h  (input)
- workflow: edit_flux3_2image (FLUX 3 Klein edit, 50 steps, cfg 1)
- size 1280x768, seed 7770, render 46.3 s
- inputs: phone_in_h_base, cave_h_v0
- prompt:
  > Keep <ref_image_0> exactly: the same person, hand, phone, room and light. Replace only the phone's screen content with the picture from <ref_image_1>, fitted edge to edge inside the screen, bright and sharp. No text, no app icons, no status bar.

#### cave_h_v0  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 1280x768, seed 4444, render 30.6 s
- prompt:
  > Inside a Himalayan salt cave relaxation room at a modern wellness center. The walls and arched ceiling are built from glowing amber and rose salt bricks lit from behind, the floor is a bed of fine white salt crystals. People recline on cushioned zero-gravity loungers wrapped in soft cream blankets, eyes closed, peaceful. Warm low glow, a faint haze in the air. Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

### phone_in_v_base
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 768x1280, seed 5550, render 25.4 s
- prompt:
  > A close-up photograph of a woman's hand holding a modern black smartphone in a bright, cozy living room with plants, a sofa softly out of focus behind. The phone faces straight on to the camera, centered, filling the middle of the frame, its screen lit plain soft white. Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin, text on screen, app icons

### phone_in_h_base
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 1280x768, seed 5550, render 25.8 s
- prompt:
  > A close-up photograph of a woman's hand holding a modern black smartphone in a bright, cozy living room with plants, a sofa softly out of focus behind. The phone faces straight on to the camera, centered, filling the middle of the frame, its screen lit plain soft white. Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin, text on screen, app icons

## Demo edit, horizontal

### x_phone_in_more_h_v1
- workflow: vid_ltx_fflf (LTX 2.3 first+last frame, silent audio)
- size 1280x768, seed 9701, 5 s, render 145.5 s
- inputs: phone_in_h, cave_h_v0
- prompt:
  > The camera pushes slowly forward toward the phone screen and passes through it, the glowing salt cave on the screen grows until it fills the whole frame and becomes the real salt cave room. Smooth, continuous, magical push-in, no cut.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### phone_in_h  (input)
- workflow: edit_flux3_2image (FLUX 3 Klein edit, 50 steps, cfg 1)
- size 1280x768, seed 7770, render 46.3 s
- inputs: phone_in_h_base, cave_h_v0
- prompt:
  > Keep <ref_image_0> exactly: the same person, hand, phone, room and light. Replace only the phone's screen content with the picture from <ref_image_1>, fitted edge to edge inside the screen, bright and sharp. No text, no app icons, no status bar.

#### cave_h_v0  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 1280x768, seed 4444, render 30.6 s
- prompt:
  > Inside a Himalayan salt cave relaxation room at a modern wellness center. The walls and arched ceiling are built from glowing amber and rose salt bricks lit from behind, the floor is a bed of fine white salt crystals. People recline on cushioned zero-gravity loungers wrapped in soft cream blankets, eyes closed, peaceful. Warm low glow, a faint haze in the air. Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

### cave_h_v0_ff
- workflow: vid_ltx_ff (LTX 2.3 first frame, 2-stage x2)
- size 1280x768, seed 9100, 5 s, render 229.2 s
- inputs: cave_h_v0
- prompt:
  > Slow smooth dolly forward through the glowing salt cave between the loungers. The people breathe slowly and rest, one woman pulls her blanket a little higher and smiles with her eyes closed. Warm light flickers softly across the salt walls. Calm, steady camera.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### cave_h_v0  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 1280x768, seed 4444, render 30.6 s
- prompt:
  > Inside a Himalayan salt cave relaxation room at a modern wellness center. The walls and arched ceiling are built from glowing amber and rose salt bricks lit from behind, the floor is a bed of fine white salt crystals. People recline on cushioned zero-gravity loungers wrapped in soft cream blankets, eyes closed, peaceful. Warm low glow, a faint haze in the air. Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

### x_land_zen_h_v0
- workflow: vid_ltx_t2v (LTX 2.3 text to video)
- size 1280x768, seed 9700, 6 s, render 256.6 s
- prompt:
  > A slow dolly across a Japanese rock garden at dawn, raked gravel patterns, moss-covered stones, a single red maple, soft fog and the first warm light. No people anywhere. Photoreal, cinematic, smooth steady camera.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

### x_land_waterfall_h_v0
- workflow: vid_ltx_t2v (LTX 2.3 text to video)
- size 1280x768, seed 9700, 6 s, render 256.7 s
- prompt:
  > A slow cinematic glide toward a tall waterfall in a lush tropical jungle, mist rising from a turquoise pool, ferns and vines, god rays through the canopy. No people anywhere. Photoreal, cinematic, smooth steady camera.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

### x_land_valley_h_v0
- workflow: vid_ltx_t2v (LTX 2.3 text to video)
- size 1280x768, seed 9700, 6 s, render 255.7 s
- prompt:
  > A slow aerial drone shot over a breathtaking mountain valley at sunrise, snow-capped peaks, lush green forested hills, clouds rolling slowly through the valley, sunlight casting long shadows, a vast serene untouched landscape. No people anywhere. Photoreal, cinematic, smooth steady camera.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

### x_drone_open_h_v1
- workflow: vid_ltx_fflf (LTX 2.3 first+last frame, silent audio)
- size 1280x768, seed 9701, 7 s, render 199.1 s
- first strength 0.8, last strength 1.0
- inputs: x_drone_wide_h, x_drone_cu_h
- prompt:
  > A drone shot flies smoothly over a quiet leafy neighborhood at golden hour, high above the rooftops and palm trees, then the camera banks and does a graceful twisting barrel roll as it descends in a spiral, swooping down into one backyard and landing on a close-up of a woman on her patio looking at her phone with a calm smile. One continuous stylish move, warm golden light, soft haze, cinematic, no cut.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### x_drone_wide_h  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 1280x768, seed 6661, render 31.6 s
- prompt:
  > An overhead high-angle aerial drone photograph of a quiet leafy Southern California neighborhood at golden hour: rows of houses with gardens, backyards and tall palm trees, long warm shadows, soft golden haze, low sun from the left. Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

#### x_drone_cu_h  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 1280x768, seed 6662, render 25.4 s
- prompt:
  > A close-up portrait of a woman in her thirties sitting on her backyard patio at golden hour, looking down at her smartphone with a calm soft smile, the phone glowing in her hands. Palm trees and rooftops softly blurred behind her. The same warm low sun from the left as an aerial view of the neighborhood, golden rim light on her hair, soft haze. Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

## Demo edit, vertical

### x_phone_in_more_v_v0
- workflow: vid_ltx_fflf (LTX 2.3 first+last frame, silent audio)
- size 768x1280, seed 9700, 5 s, render 138.5 s
- inputs: phone_in_v, cave_v_v0
- prompt:
  > The camera pushes slowly forward toward the phone screen and passes through it, the glowing salt cave on the screen grows until it fills the whole frame and becomes the real salt cave room. Smooth, continuous, magical push-in, no cut.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### phone_in_v  (input)
- workflow: edit_flux3_2image (FLUX 3 Klein edit, 50 steps, cfg 1)
- size 768x1280, seed 7770, render 45.0 s
- inputs: phone_in_v_base, cave_v_v0
- prompt:
  > Keep <ref_image_0> exactly: the same person, hand, phone, room and light. Replace only the phone's screen content with the picture from <ref_image_1>, fitted edge to edge inside the screen, bright and sharp. No text, no app icons, no status bar.

#### cave_v_v0  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 768x1280, seed 4444, render 25.3 s
- prompt:
  > Inside a Himalayan salt cave relaxation room at a modern wellness center. The walls and arched ceiling are built from glowing amber and rose salt bricks lit from behind, the floor is a bed of fine white salt crystals. People recline on cushioned zero-gravity loungers wrapped in soft cream blankets, eyes closed, peaceful. Warm low glow, a faint haze in the air. Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

### x_session_empty_clip_v_v0
- workflow: vid_ltx_ff (LTX 2.3 first frame, 2-stage x2)
- size 768x1280, seed 9700, 5 s, render 176.6 s
- inputs: x_session_empty_v
- prompt:
  > Slow gentle push in toward the crystal singing bowls, candle flames flickering, a curtain moving softly in the breeze. Completely empty, no people anywhere in the scene. Calm, steady camera.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### x_session_empty_v  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 768x1280, seed 6807, render 25.3 s
- prompt:
  > A softly lit sound healing room with linen curtains, a cushioned mat with a folded blanket, frosted crystal singing bowls of different sizes, dried flowers and glowing candles. Completely empty, no people anywhere in the scene. Photoreal cinematic photograph, soft natural light, gentle film grain, full-frame cinema camera, 35mm lens, shallow depth of field. No text, no logos, no signage. 
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

### x_yoga_filmic_clip_v_v0
- workflow: vid_ltx_ff (LTX 2.3 first frame, 2-stage x2)
- size 768x1280, seed 9700, 5 s, render 177.0 s
- inputs: x_yoga_filmic_v
- prompt:
  > Slow lateral tracking shot along the row of people as they flow together out of warrior pose and raise their arms overhead, breathing in unison. The instructor smiles and nods. Sunbeams shift gently across the floor. Smooth, steady camera. Moody cinematic film look, high contrast, deep shadows, film grain, anamorphic.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### x_yoga_filmic_v  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 768x1280, seed 6704, render 25.2 s
- prompt:
  > A bright sunlit yoga studio with warm oak floors and tall floor-to-ceiling windows that look out onto lush green trees. A small class of adults on natural-color mats hold warrior two pose, an instructor in front guides them with a warm smile. Hanging plants, golden morning sunbeams across the room. Cinematic film still from an arthouse feature, shot on 35mm Kodak Vision3 500T film with an anamorphic lens. Dramatic low-key contrast lighting: one strong motivated key light, deep shadows, rich blacks, subtle halation, heavy film grain, muted earthy palette with warm highlights. Moody, intimate, quiet. Natural clear healthy skin, real everyday adults. No text, no logos. 
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

### x_land_valley_v_v0
- workflow: vid_ltx_t2v (LTX 2.3 text to video)
- size 768x1280, seed 9700, 6 s, render 207.6 s
- prompt:
  > A slow aerial drone shot over a breathtaking mountain valley at sunrise, snow-capped peaks, lush green forested hills, clouds rolling slowly through the valley, sunlight casting long shadows, a vast serene untouched landscape. No people anywhere. Photoreal, cinematic, smooth steady camera.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

### x_connect_filmic_clip_v_v0
- workflow: vid_ltx_ff (LTX 2.3 first frame, 2-stage x2)
- size 768x1280, seed 9700, 5 s, render 176.7 s
- inputs: x_connect_filmic_v
- prompt:
  > Slow orbiting camera around the low table as the friends laugh and talk, one pours tea for another, someone leans in and touches a friend's shoulder. Lively, warm, natural moment. Smooth, steady camera. Moody cinematic film look, high contrast, deep shadows, film grain, anamorphic.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### x_connect_filmic_v  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 768x1280, seed 6707, render 25.3 s
- prompt:
  > A warm tea lounge at a wellness center in the late afternoon. Friends sit on floor cushions around a low wooden table with clay teacups and a teapot, laughing together mid-conversation. Big windows with greenery behind them, woven textures, plants, warm golden light. Cinematic film still from an arthouse feature, shot on 35mm Kodak Vision3 500T film with an anamorphic lens. Dramatic low-key contrast lighting: one strong motivated key light, deep shadows, rich blacks, subtle halation, heavy film grain, muted earthy palette with warm highlights. Moody, intimate, quiet. Natural clear healthy skin, real everyday adults. No text, no logos. 
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

## Almost (birds in the sky)

### retreat_v_v0_ff
- workflow: vid_ltx_ff (LTX 2.3 first frame, 2-stage x2)
- size 768x1280, seed 9100, 5 s, render 176.8 s
- inputs: retreat_v_v0
- prompt:
  > Slow rising crane shot as the group walks along the boardwalk toward the pavilion, mist drifting through the trees, leaves moving in a light breeze, birds crossing the light. Smooth, steady camera.
  - negative: scene cut, jump cut, text, subtitles, captions, logo, watermark, morphing faces, distorted hands, flicker, fast camera

#### retreat_v_v0  (input)
- workflow: still_flux3 (FLUX 3 Klein base int8, 50 steps, cfg 3.5)
- size 768x1280, seed 4447, render 25.3 s
- prompt:
  > An open-air wooden pavilion retreat surrounded by lush tropical greenery, ferns and tall palms, soft morning mist drifting through the jungle. A small group of people walk along a wooden boardwalk toward the pavilion carrying rolled yoga mats, chatting and smiling. Golden hour light through the leaves. Photoreal cinematic commercial photograph, warm inviting color grade, soft natural light, gentle film grain, shot on a full-frame cinema camera with a 35mm lens, shallow depth of field. Natural clear healthy skin, relaxed genuine expressions, everyday diverse adults of different ages and backgrounds. No text, no logos, no signage.
  - negative: text, letters, watermark, logo, signage, deformed hands, extra fingers, blurry, cartoon, illustration, cgi, plastic skin

## Notes

- Wide shots: people walking and birds flying move oddly.
- hexe has noticed that 'birds chirping' in an LTX prompt puts flying birds in the sky about a third of the time. The retreat move prompt says 'birds crossing the light', which is likely why retreat_v_v0_ff has birds. Next time: leave birds out of the prompt and add 'birds' to the negative.
