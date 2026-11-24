# HeyGen talking head

An AI voiceover + B-roll ad where the A-roll is a HeyGen character talking to camera, so it looks like a real creator's TikTok. It's the `AI voiceover story` style with a face. Set up 2026-11-24 from the user's own winner `Reference Ads/Red Light TOF V2 - Ferg.mp4` (HeyGen man, "What's the red light for?") and the competitor ad it copies from (`Reference Ads/Lumi Christmas cutoff (competitor).mp4`, a real creator).

**Order of authority:** the main rulebook (`.claude/skills/ve-video-edit-general/references/video-editing-standards.md`) first, then `Styles/AI voiceover story/style.md` (voiceover cutting, B-roll, captions, the CapCut hand-off), then this file. Captions use the house rules and the house engine as they are: the user said not to restyle them for this format (2026-11-24). Treat this file as a draft until the first ad passes review.

## The pipeline (user, 2026-11-24). It runs without the user, apart from the checkpoints marked ✋

1. **Script.** A competitor's ad rewritten close to word for word, with our differentiators (red light, limited colours) and the brand rules. One body and three big-swing hooks, built on `~/Documents/LuxeLight Claude/hook-library.md`. ✋ Until ads pass review with no changes, show the user the script before spending credits.
2. **Background.** A real screenshot of a UGC creator's room (TikTok, in the built-in browser), matched to the persona: a lived-in kitchen or living room for a mum, a garage or office for a man. Never a generated background, because the user says they look fake. Avoid rooms with readable brand names, other people or kids.
3. **Character face.** A Pinterest photo of the persona (for example "American mum", "American dad 50s"). Pick a natural phone-camera look, not a studio shot.
4. **Composite, Nano Banana Pro on Sume** (`google/nano-banana-pro`, never Higgsfield). Image 1 is the background, image 2 the face. The prompt: put the person from image 2 into the room from image 1, in the same position and pose as the creator there, filmed on a phone in 9:16, natural light, no beauty filter. Change her enough that she's a different person: hair colour, glasses, age by a few years, different clothes. Make 3–4 variations and pick the most real one: natural skin, believable hands, eyes to camera, nothing warped.
   - **Wearing the light:** in the user's winner the character wears the LuxeLight switched on (red), which keeps the product on screen during every talking beat. When the script's speaker would plausibly have one on (a man who uses it, a woman showing hers), follow the `luxelight-headtorch-wearing-reference` skill's reference set so the headtorch is drawn accurately. A wife talking about a gift for her husband doesn't have to wear it. Say which way you went.
5. **HeyGen character.** Upload the picked image and make a photo avatar (`create_photo_avatar`). One avatar per ad; reuse it for every version.
6. **Voiceover.** ElevenLabs, the user's room-echo "TikTok-recorded" voices: woman `XUzgF7wZopcRt48OPrgJ`, man `x3ACEVziwiA6flKIqmpo`. Match the voice to the character. One file: hook 1, hook 2, hook 3, then the body. Mark where each hook ends with `end` in `config.json`, as in the other voiceover ads.
7. **Speed up to 1.05x** with ffmpeg (`atempo=1.05`). Never faster: the lip sync starts to look off (user).
8. **HeyGen render.** Upload the sped-up audio (`create_asset_upload_batch`), then `create_video_from_avatar` with the avatar, the audio asset, `aspectRatio: "9:16"` and 1080p. One render of the whole voiceover. Wait for it with `get_video`, then download it.
9. **Cut into versions,** like every hook set: V1 = hook 1 + body, V2 = hook 2 + body, V3 = hook 3 + body. The body is the same render in all three (rulebook 5.4a).
10. **Edit** as below, through `tools/capcut/story_ad.py`, to a CapCut project plus a review-app render. Then `video-qa`, the review app and a notification, as in every style.

Before the first paid call each time (Sume, ElevenLabs, HeyGen), the run must already have the script approved or the user's go-ahead for unattended runs.

## How the edit looks (from Red Light TOF V2)

**Hook (0 to about 4.5s).** The character on screen, talking, with a TikTok **"Reply to … comment" bubble** over her chest, in the middle of the frame, as the text hook. The comment is the viewer's question the voice is answering ("What's the red light for, and why would anyone want it on their head torch?"). No captions while it's up (rulebook 3.2). The bubble comes from `tools/captions/reply_bubble/make_reply.py "<comment>" out.png`, rebuilt from the user's screenshot. For hooks that aren't a reply, use the house hook box with the script's text hook instead. The hook ends on a fast blur zoom into the body (at 3.5s in the winner).

**Body: the character carries the talking, B-roll carries every claim.**
- The character comes back for the beats that are the creator talking: the start of each new point ("reason #1", "two"), asides and attitude ("friends don't let friends use white light", "now I know what you're thinking", "trust me"), and setting up the turn to the product. These run about 1.5–4s each.
- Every line that claims something you could see goes to B-roll, by the rulebook's B-roll rules: features, problems, other people, the product, proof. In the winner, the character is on screen about 35% of the time up to the product reveal, then not at all through features and the close.
- Each return to the character alternates the framing, a wide shot then a punch-in (about 1.0x then 1.15x), so the face never comes back looking identical. HeyGen keeps the hands moving, so no extra movement is needed on her.
- Never put the character on two lines in a row that make different claims: cut to B-roll on the claim.

**Overlays the winner used** (use only where the line calls for them):
- A marketplace line shows the blurred listing scroll with the Amazon logo popping on, and a red "$15" price pop (rulebook 6.37).
- A fake or cheap product gets the red "amazon fake" label.
- "Thousands of five-star reviews" shows our real review screenshots, scrolling.
- One playful sticker on a payoff clip ("wait for it…😂" on the bugs swarming a white light).

**Close.** B-roll only: features, then the colours or the line-up of lights and cases, then the case in hand. In the winner the captions run to the last word with no end box. The house rule (rulebook 10) is an end box on every ad, so use the house end box unless the user says this style drops it.

**Captions.** House captions throughout (rulebook 7 and 11a), the same on the character as on B-roll.

## Open questions for the first ad
- Does this style keep the house end box, or end on captions like the winner?
- Should the speaker wear the light in gift-for-him scripts?

## How the build works (first ad, XMASCUTOFF, 2026-11-24)
- Edit file: `Edits/XMASCUTOFF/scripts/edit_v1.py` writes the edit JSON; use it as the template. Build with `tools/capcut/story_hooks.py <edit.json> --hook A --mp4 --capcut`.
- The voiceover given to the builder is the audio taken out of the HeyGen render, so voice and picture share one clock.
- A shot with `"talk": true` (clip = the HeyGen render) is the character. The builder splits it at every voice cut and plays her from that piece's own second, so her lips stay in sync after pauses are cut, and each cut alternates wide and 1.12x (`expand_talk` in `story_ad.py`). Hooks take `"talk": true` in `hook_shots`.
- `hook_image` puts a PNG over the hook (the comment-reply bubble, 640 wide, top y 1010, over her chest). No hook box with it: one text element at a time.
- `"bw": true` on a shot makes it black and white (fake-product shots). `"blur": 9` blurs it (the marketplace scroll). Both are in the MP4 only: add the filter by hand in CapCut.
- Not built yet: the blur zoom out of the hook, sound effects in the MP4, and the Amazon logo and price pops.
- Checked on this ad: the website recording shows prices in pounds, so it isn't used for US ads.

## From the user's notes on XMASCUTOFF v1 (2026-11-24, "this is actually really good")
- **Hooks take big swings in the picture too.** Three hooks that all open on the same talking head may be grouped as one ad. Keep one hook on the character (the comment-reply one) and open the others on B-roll: the LuxeLight shown on the words that mean it ("one of these for your husband", "gave my husband a fake"), then either cut to the character for the second half ("please don't make the mistake I nearly did") or to the script's distinguishing feature in use (red light, on "one tiny detail").
- Keep the product clear of the hook box in those B-roll openers: move the clip, not the box.

## From the user's own CapCut edit of XMASCUTOFF V1 (2026-11-24)
- **Versions:** the user finishes V1 in CapCut and tweaks the hooks of the other projects. Then `tools/capcut/graft_hook.py "<V1>" "<project with their hook>" "<new name>" <body_from>` puts V1's body under each hook they edited, keeping their hook clips, text and song. `check_bodies.py` must pass. Projects are named "[CLAUDE] <AD NAME> - V1 - FERG", V2, V3.
- **Effects in CapCut:** `tools/capcut/heygen_effects.py <Edits/CODE/assets> --bubble "<V1>" "<V2>" "<V3>"` swaps the fake clips for black-and-white copies and the marketplace scroll for a blurred copy, and lays the comment bubble over V1's hook. Run it on every project before hand-off, so the export has what the MP4 preview had.
- **Their body changes to copy next time:** the first body line ("so I've had a few of these") is covered by the LuxeLight box held up (`Packaging/IMG_2731` from 4.83s), so the product is on screen straight after the hook instead of her again. "The official LuxeLight store" is the website recording after all (from 1.5s). "Pink and orange" is one clip of both colours (`Colour Swatches/IMG_8586` from 2.93s), not a 0.4s shot each. The marketplace scroll is zoomed to 1.49. The guarantee end box sits lower (y -0.44).
- **Hook text** in their versions is plain white capitals with no box, size 13 to 14, at y 0.55.
- **Music:** a different Christmas song per version, at 0.02 to 0.03 under the body (up to 0.09 under a hook).
