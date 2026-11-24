# Benefit Stack

A 16.3s music-only ad: a hook box, then six feature chips over two clips, the product name over a demo, and the close box. Built from the winning Stitchers ads (CapCut projects `1023 (2)`, `1023 (2)-copy`, `1023 (2)-copy-copy`) with Hunters V3 (`1023 (2)-copy-copy (1)`) as a style reference. Reference videos are in the user's Drive folder "benefit stack ads". The first ad made with this template is the camping one, `Edits/CAMPSTACK` (approved at v4, 2026-11-03). This adds to the main rulebook and overrides it where they differ.

## How a request looks
"Make a Benefit Stack ad for [persona] from [static or ad]". The source is usually a static or video that has already performed well, now being tested in this format: a Parker link, an ad ID, an ad name or an image. One ad per session. Several sessions can run at once (see "Running several at once").

## The process, in order
1. **Read the rules.** The main rulebook, this file, the LuxeLight brand notes (`~/Documents/LuxeLight Claude/CLAUDE.md`) and `product-summary.md`.
2. **Pull the source ad from Parker.** Use `search_facebook_ads_sql` with `adIds` and `include: ["extended", "ad_analysis"]`. Note its headline, `value_props`, spend, ROAS and audience (age and gender). Leave out offer value props (discounts); the offer goes in the close.
3. **Write the copy and show it to the user before building any video.** That means three hooks, six chips, the product name and the close. Say where each chip came from. Wait for their OK.
   - **Chips name features,** something you could point to on the product or its spec sheet. Fit claims count ("works with your glasses", "fits over a beanie"). Benefits and use cases ("reading in the tent", "late-night toilet trips") never go on chips; the footage shows those.
   - **Order of sources:** the source's value props first (in its own wording), then the persona's Parker reviews and comments turned into the feature that enables them, then our own reasoning. There are six chips, three per clip. If the source has fewer than six, add the most logical features for the persona. No chip has a fixed position; battery and free case are not compulsory. Keep each chip to about 20 characters: the tilted slots push longer ones ("rechargeable, no batteries", 26) past the side of the safe zone.
   - **Hooks:** A is locked to the source ad's headline where there is one ("A MUST HAVE FOR CAMPERS", "RED FOR THE STARS. WHITE FOR THE WALK BACK."). B and C are the variables: take bigger swings, rather than defaulting to "obsessed" and "perfect gift" every time (user, 2026-11-04). Build them from the frameworks of Benefit Stack ads that have spent over £100 with a hook rate above 30%. Re-check Parker for each new ad (`search_facebook_ads_sql`, keywords "benefit stack", lifetime, sorted by spend). As of 2026-11-04 those are: "WHY [PERSONA] WANT THE RED LIGHT" (Hunters V1, 47.9%), "WHY [PERSONA] ARE OBSESSED WITH THIS" (Stitchers V2, 45.8%) and "THE PERFECT GIFT FOR [PERSONA]" (Stitchers V1, 38.2%). Few ads qualify, so push the mechanism further: name the persona, name the one feature they care about, and create curiosity, a problem or a callout. Hooks are uppercase, never more than two lines in the box, at `"size": 12` or larger (CapCut size 12), with one key phrase in colour and a persona emoji at the end (user, 2026-11-04). The box must sit inside the safe zone (x 65 to 1015, so at most 950 px wide). If the words won't fit on two lines at 12, shorten the copy, even the locked headline ("RED FOR THE STARS. / WHITE TO GET BACK 🔭"), and drop an emoji before going smaller. Measure each option with `box_img(...).getbbox()` before showing the copy. The phrase is green (`"green"` in `ad.json`), except a phrase about red light, which is red (`"red"`), because green text saying "red" contradicts itself (user, 2026-11-04).
   - **Close:** "CLICK SHOP NOW / [offer] / + FREE TRAVEL CASE". Ask for the current offer if it hasn't been given (the camping ad used "30% OFF").
4. **Find the clips** in the persona's Playbook folder (camping: board `ViaoryfauPW5feNpqpfRYBS3`). Anything in that folder counts, not only literal scenes. Download candidates into the working folder, run `tools/contact_sheets.py <workdir> <clips...>`, read the pages, then check in-points on timed strips. Pick clips using the rules below.
5. **Write `ad.json`** in the working folder (format: `example_ad.json`). Each hook has its own opening clip, song and position. The body clips are shared. Run `benefit_stack.py ad.json preview` to check the text.
6. **Render hook A**, look at frames at every shot, then render B and C. The user may ask for all three at once.
7. **Deliver:** copy to `Edits/<CODE>/Exports/<CODE>_Hook<X>_v<N>.mp4` (path from `notes.py next`), with `<stem>.plan.json` beside each (written by the render) so QA uses its `benefit-stack` profile. Save `ad.json` and the template as `Edits/<CODE>/scripts/edit_v<N>.py`. Run `/video-qa --post` and answer expected flags. Send the videos and end with the review app link.
8. **Notes:** `/apply-notes <CODE>`. Change only what each note names. Body fixes go on every hook. Reply on every note, and move the old version to the Trash.
9. **Approval:** the user approves in the review app, or says "Approved". Check `notes.py status`; don't post to the app's approve API (without `"value": true` it removes approvals). Then copy the latest hooks to `~/Documents/LuxeLight Ads/<Month YY> Ads/` as `<Persona> Benefit Stack - V1 - Ferg.mp4` (A), `V2` (B) and `V3` (C), never overwriting.

10. **Write the Facebook primary text and headline** once the final ads are saved. Follow the user's template below line for line, and reword only the persona-specific parts (user, 2026-11-03): the opening problem and its emoji, where the light lands, and the four ticked benefits. The benefits here can be benefits, unlike the chips. Use only claims from `product-summary.md` (water-resistant, never waterproof) and the current offer. The headline is the offer line. Show both in chat and save them as `Edits/<CODE>/ad-copy.md`.

   Primary text template (the Stitchers version):
   ```
   Sewing after dark shouldn't mean squinting. 🪡

   The LuxeLight headlamp puts bright, even light right where you're looking: on the needle, the seam, the hoop.

   ✅ Both hands free
   ✅ Wide light with no shadow from a lamp
   ✅ Rechargeable by USB-C, no batteries
   ✅ Turn it on with a wave

   50% off + a free carry case today 👇
   ```
   Headline template: `50% off + a free carry case today 👇`

## Choosing clips: what the user likes and doesn't
Likes:
- **Feature shots:** the head torch on someone's head, lit, with the wide strip beam showing and the person facing camera.
- **Hook clips:** clips that say the persona at a glance (a campsite, a campfire), each hook on a different clip.
- **Variety:** different people across the shots.
- **Close placement:** the close box in the lower third, under the person's face and the product, still inside the feed safe zone.
- **Real footage in the body:** use real clips after the hook wherever real ones exist; the user can spot AI clips, so keep AI (`hf_…`) to the hooks unless nothing real shows it (user, 2026-11-04).
- **Comment-reply hook:** for one-off ideas the user may swap the hook box for a TikTok "Reply to … comment" bubble (Astronomers hook E). Give the hook `"image"` (a PNG, path relative to `ad.json`) instead of `"lines"`; `Edits/ASTROSTACK/scripts/tiktok/make_reply.py "<comment>" reply.png` rebuilds the bubble from the user's screenshot. Only when asked: it's not part of the standard set or a schedule.
- **Hook matches the chips:** a product-aware hook that promises a reason ("WHY ASTRONOMERS LOVE THIS RED LIGHT") needs benefit chips that answer it. Don't put it on a feature-chip ad (user, 2026-11-04, Astronomers: hook moved from V1 to V2).
- **Show the feature clearly:** when a chip clip shows a feature in action (white switching to red), the whole lamp and the change must be visible and clear of the chips. Prefer it worn on the head, high in frame (zoom with `"anchor": 1`), over a hand-held lamp that sits where the chips go. White light in use means the wide beam out in the open, never the spotlight (user, 2026-11-04).
- **Never zoom the lamp out of frame:** after any `zoom` with `"anchor": 1`, check that the lit lamp and its beam sit well inside the frame, not cut off at the top edge. If a clip only clears the chips by pushing the lamp to the edge, it's the wrong clip: pick one where the face and lamp already sit above the chips (user, 2026-11-08, Fishermen: "you can't even see the beam").
- **Persona clips first:** for a chip clip, a persona clip with the light on (a fisherman with the beam on) beats a generic feature demo from another setting. Features the next clip already shows don't need their own demo (user, 2026-11-08).
- **No clip twice in one version:** a hook's opening clip can't appear again in that version's body, and neither can a near-identical clip of the same scene (two AI boat-driving clips count as one). Before rendering, list each version's five clips and check they're all different (user, 2026-11-08, Fishermen).
- **Template sameness:** every ad identical to the template, with only copy, clips and song changing.

Doesn't like:
- **Text over faces:** any text box or chip over a face or the product. Eyes go to faces, then to the torch.
- **Hidden torch:** backs turned or hands-only shots where you can't see the torch working.
- **The spotlight:** single bright point or lens flare, unless the copy mentions it.
- **Negative clips:** clips like the bug clip (`hf_20261022_104022`), unless the script is negative about white light.
- **Banned clip:** `IMG_2929`, never.
- **One creator throughout:** the same creator in every shot. Neighbouring shots, above all the two chip clips, must differ in person and setting; the same person in the same room twice reads as recycled (user, 2026-11-03, Quilters).
- **Single emoji:** the user disliked a lone emoji on Quilters hook A and asked for a second ("QUILTERS LOVE 🧵🪡", 2026-11-03). Lean towards two emojis on hooks.
- **Unrequested changes:** changing clips or text that no note asked about.

Tools for faces:
- **Face behind a chip slot:** reframe with `"zoom"` and `"anchor": 1.0`.
- **Face behind the hook or close box:** move it with the hook's `"cy"` (1140 sits below the face) or the ad's `"cta_cy"` (1100 for the close). Stitchers V1 moved its hook lower for the same reason.

## What stays the same in every ad
`benefit_stack.py` holds all of it, taken from the CapCut projects rather than by eye:
- **Shots:** hook 0 to 3.03s, first chip clip to 6.6s, second chip clip to 10.0s, product demo to 12.57s, close to 16.3s.
- **Chips:** three per clip, 0.6s apart, in fixed positions and tilts, with CapCut's Pop Up. CapCut size 11, black on white, with ✅.
- **Hook:** the white box, CapCut size 12 to 14 bold, one green phrase (`#00b209`), ending in an emoji. No animation.
- **Product demo:** "✅ The LuxeLight 2.0" chip with Bounce In.
- **Close:** the white box with Bounce In and 🚨 above it.
- **Sound:** the "correct answer" sound on the first three chips, a ding on the next three, a whoosh on the demo and the click on the close (`sfx/`). A song from `music/` runs under everything at about -23.5 LUFS, with a different song per hook. Don't keep reusing the same four: test a new track that fits the persona in at least one hook (user, 2026-11-04). `space (Astro, start 5s).mp3` is an Interstellar-style track made with ElevenLabs Music v2.5 through Higgsfield (`generate_audio`, model `elevenlabs_music_v2_5`, instrumental, about 9 credits for two takes). Clips' own sound is muted.

## Running several at once
- **Separate folders:** each ad gets its own code (persona + STACK, such as `CAMPSTACK`, `FISHSTACK`), its own working folder `~/.video-editing-work/luxe-light/<code>/` and its own `Edits/<CODE>/`. Never write into another ad's folders.
- **One review app:** it serves every ad. Start it only if http://localhost:8765 doesn't answer.
- **Shared files:** `benefit_stack.py`, `sfx/`, `music/`, the rulebook and the brand notes. Don't change the template while other ads may be rendering. If it needs a fix, tell the user, make it once, and say that open ads should re-render. When saving a rule to a shared file, re-read the file first and make one small edit, so another session's rule isn't lost.

## Expected QA warnings
A flash cut right after 10s can be the light flaring into the lens as the demo shot opens. Look at the frames before answering it, and remember the spotlight rule above.

## Technical notes
- This ffprobe build always prints JSON, and ffmpeg's drawtext can't read a font path with spaces (the helpers copy the font into the working folder).
- iPhone clips carry a rotation flag that the base video inherits; the render ignores it. Check the first frames after any change.
- The template outputs 30fps, 489 frames, 16.3s. Chips change on the cut frame, and the next shot's text appears on the frame after.
