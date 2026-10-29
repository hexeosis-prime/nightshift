# Pass notes (as written during production)

Shot numbers are as burned into each pass's numbered review copy. Kept as written.


## Pass 04 — what changed (shot numbers as burned into pass04_review_numbered.mp4)

Files: roughcut_full_pass04.mp4 (master, 1080p) · pass04_review_numbered.mp4 · pass04_review_sm.mp4
Cut: roughcut_v4.json · grade A+ (tools/grade.py A2_portra_dusk_plus) · overlay tools/overlay/overlay_deluxe_v6.html

All      Grade A+ on footage; graphics desaturated, lyric type at full colour. Shot 40 (the rapper) gets a small shadow/mid lift (LIFT env in finish.py).
03       New take; illustrations animated (robot sparks/jaw, lotus, server flames, DNA, ring).
10       Gradient line grows from a short stub to edge-to-edge on "draw"; bounce settles after 3 beats; both lines same height.
13 v04   Rescue FFLF: closed-mouth first frame, younger face (take p42; alt p41 reads older).
15 v06   Rescue FFLF: wet-hair angry close-up -> pull back through the fence, plain shirt (take p41; alts p40, p42).
19 p04   New still + take (p40); merge orb now dissolves inside 19.
20/22/27/45  Lyric corners per notes.
25 c01   Red fill on the left of her face, camera rush, dance language (p41; alt p43 = tighter face match, less energy).
26 c02   Dance take with red fill (p42; alts p40 = push to a coy close-up, p41).
28 c04   Pyramid fly-up to the peak (FFLF, p40).
30/31    "We're the pattern".
34 r03   New whip-pan take, lip sync carries through.
44 e02   One consistent singer, no longer two slightly different faces.
45 e03   New lip-sync take from the closed-mouth smile still, ends looking into the lens (L41).
         FLAG: a small white emblem appears on her shirt in the last ~3 s. Alt L40 has none but turns to profile at the end.
         The rescue FFLF version stalls ComfyUI at 225 frames (3 tries) - not viable at this length without changes.
46       Alpine meadow (e04f1).
48       Bioluminescent street (e04g4), slowed 6% to fill the slot instead of a frozen tail.
49 e05   Loop seam lands on the first frame (in 0.583).
Not done: 12 skin re-roll (low priority).
Alt takes are all in clips/; swapping one = edit roughcut_v4.json, move its seg out of roughcut_v4_segs, re-run segs + join + the two finish chunks it touches.


## Pass 05 — changes from pass 04 (shot numbers as burned into pass05_review_numbered.mp4; 52 shots now)

Files: pass05.mp4 (master, 1080p, grade A+) · pass05_review_numbered.mp4 · pass05_review_sm.mp4
Cut: roughcut_v5.json (= roughcut_v4.json) · overlay tools/overlay/overlay_deluxe_v6 + pass05 edits (scratch copy in the cloud session) · data_p5.json

03 o03   Erik's face edit + new gesture prompt (take p52): looks at her raised right hand, then faces the lens and shrugs.
         Illustrations timed to her head: robot/servers land on the beat while she looks left; flower/DNA/ring as she turns back.
         Illustrations 90% (flower 80%).
15 v06   Same seed, last frame taken from the take itself (frame 136) -> no hair/face pop at the end.
19 p04   Merge bubble pops 10 frames earlier.
20 p05   "The edges sanded down" lifted 130 px into the dark sky.
26 c02   Alternate take p40 (red key holds into the close-up); its "What do you want" forced to lower left.
36 r05   "Smaller now / Truer now" kept (lyric sheet) and retimed to the vocal (both words were ~0.4 s late).
41 k05   "Is the answer" lifted 95 px above the rapper.
46-51    Ending rebuilt: six one-bar cuts on the downbeats, all at ~2x:
         46 meadow · 47 coral reef revival (new, b/w -> color) · 48 green city · 49 open-air workshop (new) ·
         50 bioluminescent street · 51 tree winter -> blossom (new, into the loop). 52 = loop shot, unchanged.
HUD      "FULL PASS 0X" removed (lower left now "<SCENE> · WHAT DO YOU WANT"); "HX-02" removed (upper right).
Alts     o03 p50/p51/p53 · v06S s1/s2 · c02 p41/p42 · e06c p50 · e06t p51 (if it rendered) · e06w p51.


## Pass 06 — overnight changes from pass 05 (52 shots; numbers as burned into pass06_review_numbered.mp4)

Files: pass06.mp4 (master) · pass06_review_numbered.mp4 · pass06_review_sm.mp4 · cut roughcut_v6.json · overlay data data_p6.json

03 o03   New first frame: my face fix, using shot 02's still as the reference (same face, darker/straighter hair; face match
         to shot 02 0.41 vs 0.28 in pass 05). Take n6q60: glance right, look left at her raised hand, face the lens, shrug.
         Wink added to the negative prompt. Illustrations re-timed: flower + DNA first, robot + servers as she looks left, ring as she turns back.
         Alternates: n6q61, m6q60 (one long look left), m6q61 (push-in close-up).
21 p06   New first frame matched to the singer in shot 22; take q60 uses the original seed, so the same camera move
         (face match to shot 22 0.56 vs 0.35). Alternates q61-q63.
26 c02   First and last frames relit from shot 27 (face in shadow, strong red key from the left); rescue FFLF lands on the
         relit close-up, so the cut into 27 matches. Take q62 (most dancing). Alternates q60, q61, q63.
47 reef  New end frame = 60% crop of the living reef, so the camera flies forward over it while the colour returns (take p60).
50 street  Pedestrians removed from the still; forward flight between the glowing trees, still at 2x (take q60).
Tree (51) unchanged (static, as you liked). Everything else identical to pass 05 (unchanged chunks reused byte for byte).


## Pass 07 — changes from pass 06

Files: pass07.mp4 (master; NOTE it is joined from pass07_parts + pass06_parts, keep both folders) · pass07_review_numbered.mp4 · pass07_review_sm.mp4
Cut: roughcut_v7.json · overlay data data_p7.json · overlay chunks overlay/f7/

16-18    Face box removed in the laundry sequence (faces still steer the lyric layout, so the type doesn't move).
26 c02   Swapped to take c02R q61 (no extra-arm glitch).
49 e06w  Workshop plays at normal speed (seconds 1.0-3.1 of the take) so people move naturally.
50 e04c  New street: open boulevard to the horizon, no T-intersection, healthy trees, people on the sidewalks,
         stars + Milky Way overhead. Fast forward flight through z-space, rendered at normal speed (take e04s1 v70;
         alt e04s1 v71 drifts violet to blue, alt e04s3 v70 bigger trees). Stills e04s1-4 in stills/.
Shots 3 and 21: unchanged, waiting on your replacement renders.

To drop in your renders for 3 and 21: tell me the file names; I'll trim/retime, re-track the face boxes,
re-time the shot 3 illustrations to her head turns, and re-finish only chunks 0-1 (shot 3) and 7 (shot 21).


## Pass 09 — final candidate

pass09.mp4      master, 1080p, H.264 CRF 17, 930 MB (self-contained)
pass09_web.mp4  posting copy, 1080p, 14 Mbps, AAC 320k, faststart, 305 MB (fits X's 512 MB limit)
Cut: roughcut_v9.json · overlay data data_p8.json (cloud) · grade A+ (tools/grade.py A2_portra_dusk_plus) + rapper lift on shot 40

Since pass 07:
03 o03   Erik's FF + LF, FFLF with song audio (take e73): sings, looks over at her raised hand while the robot and
         servers land beside her, turns to the lens and opens into Erik's shrug frame as flower / DNA / ring arrive.
         Erik's 1280x720 stills were mirror-padded to 1280x768 for generation; the edit crops exactly that back off.
21 p06   Erik's FF, original seed / camera move (take e70).
50 e04c  Residential street: arching bioluminescent canopy, warm houses, dog walkers, kid on a bike, Milky Way;
         forward glide through z-space via a zoomed last frame, at normal speed (take e04rF z80; z81 nearly identical).
Lesson logged: re-committing a file to the same PC path can deliver a stale copy; always commit fixes under a new path.

