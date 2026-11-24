# Founder story

A narrator tells the founder's story in third person ("This is Toni, and she was a broke college student…") over fast B-roll, then the product, proof, offer and guarantee. Reference: `Reference Ads/This is Toni (Cloud Clip).mp4` (54s, 46 shots). First LuxeLight version: "Founder Xmas Gift" (review app code ALEXXMAS, 2026-11-17; the CapCut projects were first called "This Is Alex Xmas").

## How the work is split
The user cuts the voiceover and B-roll in CapCut themselves, including the pacing, their own collage, crops and blurred review card. Claude then adds the captions, movement, transitions, overlays, sounds and music to that draft, and never changes the user's clips, cuts or voice. Builder: `~/.video-editing-work/luxe-light/eric-vo-1117/scripts/style_draft.py` (rebuilds from a saved copy of the user's draft).

## Captions
- White, lowercase, no punctuation, heavy font (Montserrat Black is the closest we have), soft shadow, no box. One to three words, cut on with the voice, no pop.
- **Move the text where it makes sense, not all the time, and never leave it in one spot for the whole ad (user, 2026-11-17).** The reference's moves, to copy at the matching beats:
  - Hook: "this is [name]" curved round the founder's head, one word at a time.
  - Sideways up the edge of the frame on the travel lines, and either side of the product on "the [product] / was born".
  - A thin curved arrow from the caption to the person it names ("Korean engineers").
  - The debt figure huge and faint, drifting across behind the small caption.
  - A label tilted onto the object ("molds"), a label top and bottom of the product.
  - Offer as a stack that builds line by line, small to huge; "+ free …" slides in; the guarantee as a centred stack.
  - No caption over the review card.
- Bigger size on the words that matter.
- **No sideways text running up or down the frame (user, v3 notes 2026-11-17).** Keep it level; the slide-in animation is liked.
- **Never put text over a face or over the head torch (user, v3 notes).** Move that caption above or below the subject.
- **All text inside the 4:5 safe zone (x 65 to 1015, y 285 to 1635), the hook included.** The hook curve sits just over his head, and follows any zoom on the shot. Montserrat Black is wide: shrink a long line to fit instead of letting it spill.
- Where the reference moves the text (around "she used her life savings, took out loans"), move ours too: either side of the person, then a big pop.

## Transitions and animations
The reference keeps attention with scene transitions and pop-ons: a warm light flash across a cut, emoji flooding the screen and sliding off to reveal the next shot, customer clips popping on as a collage, small cards and pictures popping on, text sliding in. Build these; plain cuts alone are not the style.

## Sound
- **A sound effect only goes where there is a transition or an animation, and it belongs to that move. Never on a plain cut, and never at random (user, 2026-11-17).**
- **Match the sounds the reference uses, not the house defaults (user, 2026-11-17).** Listen first: Parker's `analyze_video_from_url` with audio-only notes, twice, and trust only what both listens agree on. For the reference: shutter on the first flash, whoosh on the travel cards, bass thud on the debt figure, pops on the emoji flood and the collage, shimmer on the flash into the product, soft ding on the guarantee.
- **Music matches the reference (upbeat electronic pop, about 126–128 bpm, one steady level). Not Christmas music just because the ad is a Christmas ad (user, 2026-11-17).**

- **A sound lands bang on the frame its picture appears** (the cash sound on the cut to the cash, not at the start of the sentence) (user, v3 notes).
- **Each kind of move gets its own sound; don't reuse one everywhere.** The user asked for sounds "we've not used so far": a pencil scribble as the arrow draws on, a card flick as the review card pops in, a stamp for the guarantee. No leftover sound in the middle of a stack.
- When the library has no match, generate it (Higgsfield `mirelo_text_to_audio`, half a credit each), trim the leading silence, level it, and tell the user which ones were generated.
- Animations the user asked for: the arrow scribbles on; the review card pops in; guarantee lines stamp down.

- **The user's own picks on ALEXXMAS V1 (2026-11-17), all from CapCut's sound library. Use these before generating anything:**
  - Arrow scribbling on: `Pencil pencil write circle add circle`, 0.53s, level 1.0 (replaced the generated pencil).
  - Flash into the product reveal: `Magic reveal`, level 1.0 (replaced the generated shimmer).
  - Review card popping in: `It is a decision sound called picon.`, level 0.45 (replaced the generated card flick).
  - Guarantee stack landing: `Wow`, level 0.23 (replaced the generated stamp).
  - "Click shop now": `Click_Mouse_Click_02`, level 0.59. The user put this back after I removed it, so the house click on the call to action stays.
  - Music level 0.06.
- They also put a black-and-white filter (`BW 3`, 0.72) on the "another bottle of aftershave" shot: the unwanted-gift beat goes grey (standards 6.36).

## Preview
`preview_project.py` layers every video track with crops, blur, keyframes and overlays. A preview that shows one strip of the timeline is wrong (user's notes on v2: missing crop, collage and blurred background).
