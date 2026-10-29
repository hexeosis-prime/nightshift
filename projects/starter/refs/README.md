# refs/

Reference images for this project.

**Character sheets are made for you** as the first step of a pass (`nightshift run`, or `nightshift sheets build <character>
<world>`): a front full-body view with the face covered by a white circle, a back view and a macro close-up of the face, on
seamless grey. The one you approve (`nightshift sheets pick ...`, or the best-scoring one if you don't pick) is saved as
`refs/sheets/<character>_<world>.png` and written into `canon.json`, and every identity edit and face score uses it from then
on.

- **Have a picture of the character?** Put it here and set `"reference": "refs/<file>.png"` on the character in `canon.json`.
  The sheet is then made from the picture, reformatted into the sheet layout.
- **Only a description?** Leave `reference` empty: the sheet is made from the character's `person` words and outfit.
- **Already have a finished sheet?** Put it here and set `"sheet": {"real": "refs/<file>.png"}`: nothing is generated.

One sheet per character and world when the outfit changes between worlds; the second world's sheet is an outfit edit of the
first, so the face stays the same person. A close-up face portrait (`"sheet_ref"` on a shot) and a smiling sheet for upbeat
shots are worth adding by hand.

Lock the sheets before anything else. Every later fix gets cheaper when the faces are settled first.
