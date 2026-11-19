# Component banks: building prompts from parts

_hexe's ComfyUI component banks (Nov 18): one entry per line, ready to paste into ComfyUI's multi-line selector nodes, and
each entry holding only its own kind of detail so any line combines with any other. This is the public set: hexe's own
characters, band outfits and brand lines stay in his private banks._

How the parts become a prompt: [flux3-images.md](flux3-images.md) (the image slots) and
[ltx-2.3-video.md](ltx-2.3-video.md) section 4 (the eight video categories, joined in screenplay order). The legacy
connector chain (`A {1} — featuring {2}. {3} — set in a {4}. ...`) still works in hexe's graphs, but joining
complete sentences in screenplay order (location before subject, sound last) reads better and was preferred in testing.

## Image slots (FLUX 3)

### Person: identity only (no clothes, pose, light or place)

```text
young East Asian woman in her early 20s, long straight silky black hair with soft curtain bangs, fair porcelain skin with natural soft makeup, glossy plump lips with a subtle pink tint, light blue-gray eyes
glamorous Japanese woman in her early 20s with long voluminous silky dark hair, natural glowing skin, soft fox-eye makeup, long lashes, glossy pink lips, and delicate feminine features
young woman in her early 20s with black hair featuring subtle colored streaks, realistic skin texture, edgy expressive facial features
young woman with brown hair styled in a messy elegant bun with loose face-framing strands, soft natural complexion, natural brows, and subtle natural makeup
woman in her late 20s with tied-back auburn hair, warm expressive eyes, natural skin texture with light freckles
woman with long flowing black hair and pale skin, serene delicate facial features
woman with loose dark braids, warm natural complexion, relaxed athletic build
strikingly handsome young man in his early 20s with thick slightly tousled jet-black hair, strong well-defined eyebrows, deep expressive dark-brown eyes, straight sculpted nose, prominent cheekbones, defined masculine jawline, and subtle natural stubble
rugged male construction worker in his 40s, weathered tan skin, strong build, focused expression
younger male construction worker in his late 20s with a neatly trimmed short beard, athletic build, attentive expression
focused surgeon in their mid-30s, natural skin texture with subtle fatigue around the eyes, athletic posture
male news anchor in his mid-20s with short neatly styled brown hair, clean-shaven, professional posture
female news anchor in her mid-20s with sleek blonde hair, poised posture, bright expressive eyes
big bald man with a thick full beard and warm weathered complexion
a soaked young courier with damp hair clinging to their forehead
an older quiet librarian with silver-streaked hair and gentle eyes
a restless teenage musician with tousled hair and lean build
a hooded street vendor with weathered features and alert eyes
a tired office analyst with slight dark circles under their eyes
a lone wanderer with sun-weathered skin and windblown hair
a chrome female android with a cracked glowing visor and delicate mechanical joints
a rusty oversized gentle male robot with weathered steel plating and warm optical sensors
```

### Outfit: head to toe, fabrics and exact placement (no body, pose or place)

```text
blue denim jacket over a white rib-knit tank-top, black straight-leg denim jeans, white canvas sneakers, small silver stud earrings
oversized pastel hoodie and matching loose sweatpants, barefoot
white fitted crop top and grey tight high-waisted yoga pants, barefoot
oversized plain red t-shirt, relaxed black cargo pants, clean white high-top sneakers, delicate stud earrings
pale blush-pink button-up blouse with sleeves casually rolled to the forearms, high-waisted wide-leg cream trousers with pleats, clean white sneakers, small stud earrings
oversized luxury streetwear hoodie and patterned designer pants, multiple silver rings and statement jewelry on fingers
white long-sleeve knit cardigan over a fitted black top, thin red oval metal-frame glasses, small red hair clip on the left side
crisp off-white button-up shirt with sleeves rolled to the forearms, black suspenders, tailored black trousers, polished dress shoes
deep-purple one-shoulder party dress with a small leather shoulder bag and strappy sandals
simple dark green flowing dress made of soft matte linen
smudged canvas florist apron over a casual rolled-sleeve work shirt and dark jeans
neatly pressed navy blue tailored broadcast suit, crisp white dress shirt, and satin tie
high-visibility neon orange safety vest over a grey cotton t-shirt, faded blue heavy-duty denim jeans, scuffed brown leather work boots, and a bright yellow hard hat
premium dark charcoal structured thermal medical scrubs with a tailored fit
standard light-blue hospital surgical scrubs with surgical cap and mask
weathered travel cloak, layered linen tunic, scuffed leather boots, and a worn leather crossbody satchel
polished silver-and-cobalt medieval plate armor with subtle engravings
white lightweight summer linen shirt and shorts, damp from water
worn yellow waterproof raincoat and scuffed rubber boots
soft cable-knit cardigan over a collared shirt and wire-rimmed reading glasses
loose faded pullover hoodie, distressed jeans, and worn canvas sneakers
matte black techwear jacket, cargo trousers, and fingerless gloves
plain wrinkled white button-up office shirt, dark slacks, and a loosened silk tie
```

### Action: a frozen pose, hands, gaze, the prop in use (no movement over time, no background)

```text
standing facing forward in a full-body front view, upright in a neutral standing pose with arms hanging naturally at the sides, head level looking straight into the lens like a casting photo
standing in a relaxed, stylish full-body pose with both hands tucked naturally inside pants pockets, body facing the camera while head is turned slightly to the side
walking forward in a confident full-body stride on the left-center of the frame, one hand resting in a trouser pocket while the other hangs naturally, calm neutral expression looking toward the camera
sitting on the floor indoors holding a red electric guitar, dramatic candid pose with head tilted back and tongue playfully out toward the guitar neck
close-up selfie pose resting right cheek on hand with fingers gently curled under the chin, looking directly into the camera with a calm, slightly pouty expression
glamorous over-the-shoulder pose, body turned away while looking back into the camera lens with voluminous hair crossing part of the face
seated beside a green-felt billiards table, holding a wooden pool cue naturally with both hands, looking slightly off to the side with a calm, serious, thoughtful expression
standing under a flickering streetlight, looking down at a glowing smartphone screen held in one hand
sitting quietly by a window, fingers resting on the corner of an open hardcover book
leaning casually against a metal rooftop railing, holding an acoustic guitar across the chest
standing behind a wooden street cart, hands arranging small goods while watching the passing crowd
sitting hunched at a desk, staring intently at a glowing laptop screen
standing centered in a relaxed athletic posture, mid-dance pose with one hip isolated and a playful wink directed at the lens
standing near a stack of plywood, pointing right index finger firmly at an unfurled set of white and blue blueprints
leaning forward with both hands resting on knees, looking intently down at blueprints on a wooden stack
standing upright holding a bright yellow metal tape measure extended flat against a vertical wooden stud, looking back over the left shoulder with an affirming nod
standing in a cold room with shoulders slightly tense, mid-exhale with a focused, determined gaze
standing naturally in dappled shade, holding a fresh slice of red watermelon in both hands with a candid summer smile
holding a clear glass tequila shot up toward the camera with a bold, warm grin
```

### Light: the sources, which side, their color, how much shadow (Nightshift's fifth slot)

Added Nov 19: the backlot locations leave light out on purpose, and the Nov 18 tests showed the light needs a sentence of
its own to reach the person. Write where the light comes from, not just its mood.

```text
a warm sodium street lamp high on her left, cool shop-window glow on the right, half her face in shadow
one bare tungsten bulb overhead, hard light on the top of the head and shoulders, the eyes in shadow
the green glow of a laundromat window on one side, a warm street lamp behind, steam catching both colors
low golden-hour sun from behind her left shoulder, a warm rim on the hair, the face in soft open shade
cool blue light from the low clouds and the city glow behind, the front of the body mostly in shadow
flickering fluorescent tubes overhead, flat greenish light, hard shadows under the brows
a phone screen held in her hand, cold blue light from below on the chin and cheeks, the room dark around her
a single candle on the table in front of her, warm low light from below, deep falloff into darkness
soft overcast daylight from a window on her right, gentle falloff across the face into the room
passing headlights sweeping from left to right across her face, otherwise dark
red and blue neon signs on either side, colored spill on each cheek, deep shadow between
hard midday sun from high above, short shadows, squinting eyes, bright bounce from the pavement
```

## The backlot: 36 locations

The five-part formula: `[scale/material] [place], [surface/structure], [furniture/object], [small prop] and [small detail]`.
No people and no light in these lines; add the light slot. A location plate (one rendered image of each place) can go in a
reference slot so the place stays the same from shot to shot.

```text
narrow rain-slicked city alley, wet brick walls and fire escapes, metal dumpsters, glowing shop signs, puddles and crumpled paper
crowded neon-lit street market, hanging cables and steam vents, food carts and plastic stools, glowing lanterns, plastic bags and rain puddles
wind-blown urban rooftop, concrete floor and rusted railings, industrial AC units and vents, potted plants, coiled cables and LED floor strips
stone marina quay flanked by moored luxury yachts, tall white fiberglass hulls and rigging masts, deck railings and hull fenders, thick dark mooring poles, yellow mooring lines and rippling water
suburban ranch-style living room, plastered walls and sisal rug over hardwood floor, beige fabric couch with square pillows and coffee table, potted plants and modern art paintings, window overlooking city lights
quiet high-ceilinged library study, tall wooden bookshelves and dark paneling, worn leather armchair and reading desk, brass desk lamp, stacked books and steaming ceramic mug
cramped apartment kitchen, checkered linoleum floor and tiled backsplash counter, vintage gas stove and wooden cabinets, ceramic coffee mugs, hanging dried herbs and dish towels
tidy modern bedroom, soft pastel walls and hardwood floor, built-in white wooden shelves and half-closed window, neatly folded clothes, plush throw pillows and wall mirror
suburban backyard patio, wooden deck and lush perimeter fencing, tall swaying palm trees and lounge chairs, overhead string lights, scattered glass bottles and garden planters
open-plan 1963 midcentury office, exposed red brick walls and geometric carpet, orange chairs with blue desks and yellow dividers, ceramic potted palms, vintage rotary phones and stacked papers
sterile modern corporate office, floor-to-ceiling glass walls and polished concrete floor, long brushed-metal conference table and ergonomic chairs, open laptop, ceramic coffee cup and scattered documents
narrow neighborhood florist shop, glass storefront window and wooden floorboards, rustic wooden workbench and display tiers, colorful flower bouquets in metal buckets, kraft wrapping paper and sharp trimming scissors
sterile modern hospital operating room, pale walls and seamless linoleum floor, surgical table and overhead articulated equipment arms, stainless steel instrument trays, digital vital monitors and wall clock
luxurious old-world billiards hall, dark polished wood paneling and burgundy velvet curtains, classic green-felt pool table and leather club chairs, warm brass table lamps, wooden cue sticks and colorful billiard balls
concrete basement workshop, cinderblock walls and oil-stained concrete floor, heavy wooden workbench and metal tool shelves, vintage vise grip, dented oil cans and scattered scrap metal
windswept coastal cliffside overlooking a sandy beach, weathered grey basalt rocks and narrow dirt path, twisted pine trees and driftwood logs, wild coastal daisies, crashing white-foam waves and wet pebbles
overgrown forest clearing, dense tree canopy and damp mossy ground, twisted tree roots and fallen decaying logs, lush green ferns, scattered autumn leaves and smooth stones
infinitely extending opulent palace-spaceship corridor, black lacquered walls and colorful geometric floor tiles, symmetrical archways and mirrored columns, gilded copper and gold sacred-geometry inlays, glowing neon accent tubes and crystal sconces
narrow metallic commuter train interior, ribbed aluminum walls and scuffed rubber aisle floor, rows of molded plastic seats and stainless steel grab poles, overhead hand straps, scratched plexiglass windows and route maps
narrow vintage laundromat, checkered linoleum floor and wood-paneled walls, long rows of chrome front-loading washing machines, plastic laundry baskets and rolling wire carts, detergent boxes and spinning clothes behind glass doors
cavernous underground concrete parking garage, raw poured-concrete pillars and oil-stained asphalt lanes, yellow painted parking stalls and speed bumps, concrete wheel stops, overhead ventilation ducts and convex safety mirrors
weathered desert service station forecourt, cracked asphalt pavement and corrugated metal canopy, vintage analog fuel pumps and concrete island bollards, battered metal trash cans, coiled air hoses and faded price signs
retro 1950s roadside diner interior, black-and-white checkerboard floor and stainless steel wall panels, red vinyl booths and laminate counter with chrome barstools, glass pie display case, napkin dispensers and ceramic coffee mugs
cavernous industrial warehouse nightclub, raw concrete walls and steel truss ceiling, raised DJ booth and metal mezzanine catwalks, towering matte-black speaker stacks, coiled XLR cables and scuffed dancefloor grates
acoustically treated recording studio control room, cedar wood diffuser panels and dark charcoal foam walls, wide analog mixing console and leather studio chair, studio monitor speakers on stands, patch-bay cables and condenser microphone behind glass
long symmetrical luxury hotel hallway, plush geometric-patterned carpet and silk-wallpapered walls, recessed mahogany doorways and wainscoting panels, ornate brass wall sconces, gilded room-number plaques and marble console table
cramped neighborhood convenience store, fluorescent ceiling tiles and scuffed linoleum floor, densely packed metal gondola shelves and glass-door beverage coolers, checkout counter with cash register, cardboard boxes and plastic shopping baskets
minimalist brutalist art gallery, towering board-formed concrete walls and polished terrazzo floor, monolithic stone display pedestals and long wooden bench, large abstract canvases, brass stanchions and recessed floor tracks
narrow timber-framed ramen stall, weathered cedar counter and wet cobblestone floor, open steaming noodle kitchen and low wooden stools, hanging fabric noren curtains, bamboo chopstick holders and stacked ceramic bowls
high-tech robotics assembly laboratory, white epoxy floor and cleanroom glass partitions, articulated yellow industrial robot arms and steel workbenches, diagnostic oscilloscope monitors, braided wire harnesses and precision torque tools
tranquil wooden temple courtyard, raked white gravel garden and mossy stone stairway, weathered cedar timber pavilions and sliding shoji screens, carved stone lanterns, bamboo water fountain and flowering camellia bushes
ornate Victorian iron-and-glass conservatory, oxidized green wrought-iron ribs and wet flagstone walkway, tiered wooden plant benches and towering tropical palms, terracotta pots, hanging ferns and brass watering cans
arid red-rock desert canyon, towering striated sandstone cliffs and cracked clay ground, wind-carved rock arches and dry washbed boulders, desert sagebrush and saguaro cacti, rusted classic car fender and sun-bleached driftwood
isolated brutalist concrete cliffside observation deck, raw geometric concrete cantilevers and glass safety barriers, recessed concrete seating alcoves and steel railings, astronomical brass telescope, shallow reflecting pool and wet slate tiles
expansive commercial photography studio, seamless curved white cyclorama wall and polished reflective studio floor, C-stands with sandbags and rolling equipment carts, large octagonal softbox diffusers, coiled power cables and gaffer tape marks
spacious sunlit dance rehearsal studio, sprung blonde-hardwood floor and floor-to-ceiling mirror wall, brass ballet barre and acoustic wall panels, portable boombox speaker on a stool, gym duffel bag and stainless steel water bottle
```

### Studio and editorial sets

```text
a sunlit Mediterranean tiled courtyard, whitewashed stone walls and an ancient olive tree, carved stone bench, terracotta clay pots and a rustic wooden chair
a warm and inviting architectural living room with a soffited ceiling and large light-stone fireplace, plush rust-colored L-shaped sectional sofa with cream and rust pillows, circular textured coffee table holding stacked books and a gray vase with dried grasses, two matching rust-velvet armless chairs on slender black metal legs, and floor-to-ceiling windows with light drapery
a dark professional photography studio, deep black-gray seamless backdrop and a polished reflective black floor, billowing clouds of vivid red and dense dark charcoal smoke spreading across the lower background
a gray misty editorial studio, smoky gray textured backdrop and floor, with low white fog drifting gently across the floor around the subject's feet
a bright ivory-to-warm-white luxury editorial studio background with abundant negative space, subtle floor reflections, and soft diffused shadows
a clean neutral-toned modern room filled with blurred ghost-like silhouettes of moving people creating long-exposure motion blur and light trails
a seamless neutral grey #B8B8B8 commercial studio background with soft even studio lighting and smooth floor falloff
a bustling residential construction site at golden hour, exposed vertical wooden wall framing and raw dirt ground, stacks of fresh plywood and cast long afternoon shadows
```

## Video categories (LTX 2.3)

Joined in this order: genre, location, subject, action, camera, lighting, continuation, sound (last). Each line is a
complete clause for its slot.

### 1. Genre / scene type

```text
strictly empty landscape scene focusing purely on environment and atmosphere
cinematic medical drama with clinical precision and quiet tension
sunny tropical travel vlog with bright, relaxed pacing
cinematic, realistic dramatic film scene
realistic, nature documentary field recording
realistic, entertainment news TV broadcast
realistic, local television news broadcast with split-screen graphics
realistic, nature documentary sequence
vertical social media street-dance video
vertical homemade selfie TikTok video
opulent sci-fi palace documentary POV exploration blending classical grandeur with futuristic design
quiet nighttime backyard documentary with intimate, observant framing
moody coastal landscape film emphasizing isolation and natural rhythm
abstract digital tech visualization focused on sacred geometry and data flow
handheld raw vertical phone video with spontaneous night-out UGC energy
gritty first-person POV disaster survival recording
experimental arthouse film thought piece about existential longing
psychedelic Saturday morning cartoon motion-graphics sequence
tactile handcrafted felt stop-motion animation
high-end luxury commercial product cinematography
```

### 2. Subject: appearance and wardrobe only

```text
no visible human subjects, focusing entirely on the architectural and natural environment
a dedicated medical team in sterile surgical scrubs, caps, and focused masks
a focused surgeon in their mid-thirties wearing premium dark charcoal structured thermal scrubs
a professional male news anchor in his mid-twenties with short brown hair wearing a neatly pressed navy blue suit
a professional female news anchor in her mid-twenties with blonde hair wearing a neatly pressed navy blue suit
two dancers in their early twenties dressed in oversized streetwear and reflective sneakers
a lone wanderer in weathered travel gear carrying a worn leather satchel
a pair of street musicians holding acoustic instruments with open instrument cases at their feet
a silent guardian figure in polished silver armor
a woman in her late twenties with tied-back auburn hair wearing a smudged canvas florist apron
a woman with long flowing black hair and pale skin wearing a simple dark green linen dress
a woman with loose braids wearing an oversized pastel hoodie and matching sweatpants
a woman wearing a fitted white crop top and tight grey yoga pants
a young woman with long dark hair in a deep-purple one-shoulder party dress accompanied by three female friends in evening dresses
two male construction workers wearing high-visibility neon orange vests over grey cotton t-shirts, faded blue heavy-duty denim jeans, scuffed brown leather boots, and bright yellow hard hats
a black cat with sleek fur and bright green eyes
a towering faceted crystal sculpture with precision-cut beveled prism edges
a glowing crystalline rainbow geometric cube hovering mid-air
```

### 3. Action and dialogue: one continuous motion

Dialogue is quoted with who speaks and how; with an existing song, the audio is the authority and the action describes
the performance, not the words.

```text
remains completely still as ambient environmental elements shift naturally around the frame
stands calmly, observing the surroundings with steady focus and subtle natural breathing motion
performs precise, methodical movements with surgical instruments in focused concentration
interacts naturally with the surrounding environment, showing gentle hand gestures and relaxed facial reactions
sits close to the lens and whispers, (woman, southern accent, whispering): "close your eyes and listen", intimate ASMR delivery
looks up thoughtfully and speaks, (man, speaking softly): "I've been thinking about this all day", calm reflective delivery
trims flower stems with sharp scissors, unwraps fresh roses and tulips from kraft paper, looks directly into the camera with a calm expression, and says in a warm slightly husky voice, "Can't beat the smell of fresh cut flowers."
moves purposefully from synchronized stances into rapid footwork, fluid arm waves, and tight body isolations when the beat drops, spinning simultaneously to mirror each other before holding a final pose with a playful shrug
starts from a relaxed posture, launches into tight viral choreography with quick shoulder rolls, synchronized finger snaps, and sharp hip isolations matching the beat, and finishes with a playful wink and quick hair flip as the music cuts
sings expressively while dancing to the rhythm, (woman, singing): "oh, whoa, oh oh. whoa, oh no, oh whoa oh oh, got that? ja ja!", energetic pop vocal delivery
points firmly at an unfurled set of blueprints on a plywood stack, pauses briefly, then gestures toward a vertical wall frame and says in a gruff commanding voice, "The load-bearing beam goes right across this top section."
walks purposefully forward as the structured fabric of the outfit moves naturally with every stride
rotates her head slowly with eyes closed and a serene expression, seemingly listening to the environment itself
pauses mid-stride, looks directly into the lens with an intense gaze, and says in a clear feline voice, "meow meow", before stepping forward onto the porch
sways gently in the coastal breeze as a Voice Over narrator speaks in a measured, authoritative British accent: "Not many have even heard of the ocean before. Most believe it to be merely imaginary. A fable."
pulses and rotates smoothly in a seamless geometric loop, refracting spectrum light across its facets
```

### 4. Location

The backlot above, plus these video sets:

```text
vast empty natural landscape with open terrain and unbroken horizon
sun-drenched tropical coastline with pristine white sand, turquoise ocean waves, and tall swaying palm fronds
misty coastal shoreline with rocky basalt formations, tide pools, and scattered sun-bleached driftwood
high-tech television news studio set with a sleek anchor desk on one side and a large 16x9 video monitor displaying kaleidoscopic hexagonal neon graphics on the other
large outdoor rave festival grounds with massive stage video monitors displaying kaleidoscopic geometric hexagonal patterns
bustling residential construction site with exposed wooden wall framing, raw dirt ground, and stacks of plywood
pure featureless glossy black void with an ultra-clean reflective floor
digital abstract cybernetic space filled with glowing multicolored 3D wireframe structures, vector laser grids, and holographic data locator boxes
```

### 5. Camera: always a framing scale and an explicit behavior

Keep moves small when the shot shows only part of a person or place: whatever comes into view is invented
([ltx-2.3-video.md](ltx-2.3-video.md), "What enters the frame is invented").

```text
captures a wide static locked-off frame with zero camera movement, allowing the internal scene motion to dominate
frames a medium shot that executes a slow, steady push-in toward the subject while maintaining sharp focus
holds a close-up handheld frame that weaves intimately between foreground details and the subject's hands
executes a smooth pull-back from a close-up to a wide shot, gradually revealing the full scale of the surrounding environment
pans gently from left to right in a wide establishing frame, following the natural contour of the space
tilts slowly downward from an eye-level wide view toward the foreground details while maintaining crisp focus
tracks smoothly alongside the subject at a consistent walking pace in a medium Steadicam framing
drifts with subtle handheld breathing in a medium-close framing for an authentic documentary feel
remains fixed in a chest-up vertical phone framing with slight natural handheld sway mimicking a casual mirror recording
tracks backward at a low angle ahead of the subject, gliding smoothly across the floor
executes a slow, controlled 360-degree orbital rotation around the centered subject in a medium-full framing
moves forward slowly at a steady linear pace along a centered single-point perspective axis for a geometrically seamless z-space loop
flies forward through 3D space while executing a smooth barrel roll and panning left to right
jolts, whips, and reels reactively in a continuous first-person handheld POV, snapping toward each physical impact with natural motion blur
```

### 6. Lighting

```text
soft overcast daylight filling the space evenly without harsh shadows or extreme contrast
warm golden-hour sunlight streaming at a low angle, casting long dramatic shadows and warm rim highlights
warm sunset light blending with cool artificial neon tones, casting sharp rhythmic shadows across the floor
cool silvery moonlight filtering through the darkness, establishing a quiet, mysterious ambiance
high-contrast directional studio key lighting with deep shadows and crisp edge highlights
soft studio-style three-point broadcast lighting, producing a clean, polished, even illumination
vibrant triadic neon glow in electric cyan, magenta, and yellow casting shimmering colorful reflections across polished surfaces
strong backlighting outlining the subject in a bright golden rim halo with subtle optical bloom
volumetric light shafts and crepuscular rays cutting through thin atmospheric mist and suspended dust motes
soft morning sunlight streaming through front glass, illuminating dancing dust motes in the air
flat, even natural room daylight streaming through a half-closed window without harsh shadows
prismatic chromatic light source casting dynamic rainbow caustics and spectral dispersion across faceted surfaces
```

### 7. Continuation and rendering notes

```text
The scene remains tranquil with gentle natural movement throughout, rendered in photorealistic 4K cinema quality with subtle film grain
The sequence maintains consistent pacing as environmental textures and skin pores remain in crisp focus with shallow depth of field
The visual treatment emphasizes tactile material realism, subsurface scattering, and polished reflections as the camera settles on the final pose
Motion remains smooth and continuous, with creamy optical bokeh isolating the focal plane from the softly blurred background
Visual tone holds steady as vertical faceted crystal prism stripes briefly occupy parts of the frame, refracting the scene with chromatic aberration and rainbow caustics
Subtle digital glitch overlays, scanlines, and pixel sorting appear intermittently, adding a retro-tech cybernetic aesthetic without breaking temporal continuity
Optical lens flare and warm light halation evolve naturally as the light source shifts slightly across the lens
The composition holds steady on the subject's final laughing expression for one full second before the clip naturally concludes
First and last frames align in exact geometric symmetry to form a continuous, infinitely repeating seamless loop
```

### 8. Sound (always last)

Sound words can turn into pictures: "distant birdsong" puts birds in wide shots about a third of the time. Leave out
anything you don't want to see.

```text
pure ambient foley with strictly no music, featuring subtle environmental sounds, gentle clothing rustles, and quiet natural room tone
natural outdoor ambience featuring rustling leaves, distant birdsong, gentle dripping water, and a faint ethereal hum resonating softly in the background
crisp scissors snipping stems, soft kraft paper crinkling, water gurgling into a bucket, and a faint door chime mingled with distant street noise
crashing ocean wave rhythm, distant seabird calls, and dry coastal leaves rustling in the breeze, with soft ambient harp melodies and sparse xylophone arpeggios layered quietly beneath the natural soundscape without overpowering it
crisp fabric rustles and barefoot floor taps cutting through a quiet room over a faint HVAC hum, while a trending pop-dance track with crisp percussion, synthetic bass, and a repeating vocal hook plays clearly through phone speakers before cutting off abruptly at the end
crisp fabric rustles and rubber sneaker soles squeaking across concrete over distant traffic hums, while a trending trap beat with heavy 808 bass, snapping hi-hats, and chopped vocal samples plays prominently above the ambient noise without muddying the mix
ambient mellow 80 BPM Lo-Fi trap-house featuring syncopated polyrhythms on 808-style drums, a gentle harp melody intertwined with delicate xylophone notes, and very distant computer beeps and dreamlike vocal samples drifting in and out of perception
gritty mid-tempo desert-blues instrumental featuring raw acoustic slide guitar, a steady percussive shaker, and a low atmospheric drone maintaining a flat dynamic profile
rich neoclassical orchestral arrangement with sweeping strings, delicate harp glissandos, and ethereal synth pads at a slow graceful tempo
crisp clinical operating-room ambience featuring metallic surgical tool clinks, muffled background chatter, and a steady ventilation hum
driving IDM electronic music with complex synthesized rhythms, glitchy textures, deep sub-bass rumble, excited crowd cheering, and subtle whooshing digital transition sound effects
sharp terrified gasps, breathless muttering, ragged breathing, and violent structural impacts—strictly diegetic audio coming from the camera operator, with no music allowed
```

## Negative prompts by use

Whether a negative does anything depends on the graph. **LTX 2.3 in Nightshift runs NAG, so video negatives are live. The
FLUX 3 image graph runs at cfg 1, where the negative prompt is skipped entirely**; for images, say what you want instead.
Keep negatives short and aimed at a defect you've seen: the old long lists included "no movement", "static" and
"film grain", which fight shots that want those.

### 5.1 LTX 2.3 Standard Fixed Negative Prompt

```text
worst quality, blurry, jittery, distorted, watermark, low resolution, inconsistent motion
```

### 5.2 LTX 2.3 Extended Narrative Negative Prompt

```text
captions, transition, VR, bad quality, subtitles, text, watermark, overlay effects, cartoon, ugly, blur, logo, static, low quality, noise, mutant, horror, film grain
```

### 5.3 LTX 2.3 Locked-Camera Cinemagraph Loop Negative Prompt

```text
people in shot, person, camera movement, reframing, scene cut, scene transition, no movement, low quality, still frame, frames, watermark, overlay, titles, subtitles, worst quality, lowres, jpeg artifacts, bad anatomy, artist name, stock, signature, bad_quality
```

### 5.4 Crystal, Glass & Studio Logo Ident Negative Prompt

```text
fog, haze, smoke, mist, milky, cloudy glass, matte, plastic, brushed metal, soft focus, painterly, illustration, background gradient, background shapes, glowing aura, particles, text, watermark, logo, deformation, extra letters, cartoon, cheap CGI
```

### 5.5 Luxury Product Advertising Poster Negative Prompt

```text
real brand names, copied original text, aggressive chaotic paint splash, dirty background, heavy black blocks, cheap CGI, plastic-looking bottle, messy layout, oversized typography, random extra props, low-detail liquid, muddy whites, dead blacks, cluttered annotations, human characters
```

### 5.6 Character Sheet & Multi-Panel Portrait Negative Prompt

```text
text, watermark, logo, distortion, warped face, asymmetrical eyes, duplicate features, face variation, blurry facial details, ugly, deformed, low resolution, mutations
```

### 5.7 Early-2000s Retro Video Game CGI Negative Prompt

```text
cartoon, comic book, cel-shaded, hand drawn, outlines, 2d, flat shading, photograph, realistic, 4k, 8k, unreal engine 5, octane render, subsurface scattering, detailed pores, volumetric hair, cinematic lighting, soft shadows, dslr, fujifilm, kodak, pixel art
```

### Nightshift's targeted video negatives (Nov 19)

```text
microphone, object in hand, printed graphic, logo on clothing, birds, flock of birds, scene cut, subtitles, text
```
