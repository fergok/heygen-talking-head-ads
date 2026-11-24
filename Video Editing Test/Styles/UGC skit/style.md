# UGC skit

Creators act out a scene together, and we add B-roll and text. Example: `Edits/REDSKIT` (the Red Light Skit). This adds to the main rulebook, and overrides it where they differ.

## Editing
- **Leave the skit's own cut and audio alone.** Don't trim pauses, chop lines or speed it up unless asked. This overrides the pacing, filler and pause rules in the main rulebook.
- **Length follows the skit.** 1:44 is fine. This overrides the length limit.
- B-roll covers about a quarter of the video, on lines naming a feature. Keep reveals, jokes and personal lines on the couple.
- On lines about the sale, let each clip breathe, with no quick-fire stacks. Example: one clip of someone doing an activity that sells the torch across "they're doing a sale right now" (such as walking the dog, varied between ads), one of someone using it on the discount, then the carry case. Then return to the speaker.
- When the light goes off and on with the wave sensor, add a quick punch-in and back out, for retention. Don't punch in on mode switches (white, red, spotlight): it doesn't amplify anything (reviewer, WHOSKIT v1).
- Zoom onto the speaker's face on the big lines for retention: the reveal ("you bought her for me") and the hero claim ("best present you've ever got me"). Ramp in over a few frames, hold through the line, and zoom back out after the joke lands or snap out on the cut (reviewer, WHOSKIT v1).
- The end box comes in early enough for the script to finish under it, such as on the last short reply. Never freeze the picture to make room for it.
- Finished edit script to start from: `edit_template.py` in this folder.

## Workflow
1. Read the main rulebook and this file. Download the brief, the raw video and any reference videos from the user's link. If a reference has a CapCut project, take its settings from there.
2. Work in the session's scratchpad. Copy in `edit_template.py`, `voice_read.py` and `check_alignment.py` from this folder, and the click and any song from `Assets/`. Save the video as `raw/skit.mov` and its audio as `audio/skit.wav` (16k mono).
3. Transcribe with word timings, run `voice_read.py` (it writes `qa/spk.npz`), and find the skit's camera cuts for `RAW_CUTS`.
4. Choose B-roll from the whole Playbook workspace, looking at the frames first. Save clips as `pb/<clip>.mov`, and check `ffmpeg -i` for HDR clips (`arib-std-b67`) to list in `HDR_CLIPS`.
5. Fill in the template's settings, then run `edit.py base`, then `edit.py A` and so on for each hook. When each hook renders its own full video (as in WHOSKIT), run the hooks at the same time, not one after another: a round of three takes about 5 minutes instead of 10. Check frames, and run `check_alignment.py`. It can flag a false alarm when a caption changes just before the shot, so look at any flagged frames.
6. Copy each render to `Edits/<CODE>/Exports/` using the path from `notes.py next`, and copy `edit.py` to `Edits/<CODE>/`. Run QA with `--post`, send the videos, and point the user at the review app.
7. Apply notes with `/apply-notes`. When the user says it's completed, save to the monthly folder as set out in `CLAUDE.md`.

## Text hooks
- Winning ads are first person or point at a relationship conflict, promise fallout and don't repeat the voice:
  - "Divorce papers are being drafted 🤣"
  - "Ranking my wife of 10 year's xmas gifts 🎁 (this didn't go well)"
  - "EXPOSING MY WIFE'S XMAS GIFTS 🚨 (we argued after this)"
- Hooks chosen for REDSKIT, results not known yet:
  - "Marriage counselling is booked 🤣"
  - "He owes her an apology after this one 😳"
  - "Meltdown pending 👀⏳ (wait for it....)"
  - "Jealous husband unlocked 👀 (over this of all things)"
  - "Christmas gift drama 😳🎄 (he's not happy)", in the red box
- Use the reviewer's wording exactly, including punctuation.
- **What the data says** (Parker, "Skit Couple" ads, lifetime to 2026-11-03; about 93% of spend reaches women, 78% of it aged 55+, so the viewer is the wife buying the gift):
  - "Ranking my wife of 10 year's xmas gifts 🎁 (this didn't go well)": £68k spend across its two copies, hook rate 67 to 69%, ROAS 1.8 to 1.9. The big winner.
  - "Divorce papers are being drafted 🤣 ranking every Christmas gift": £9.8k, hook rate 69%, the best ROAS at 2.0 and CPA £21.
  - "EXPOSING MY WIFE'S XMAS GIFTS 🚨 (we argued after this)": about £90, hook rate 44%. Meta didn't scale it.
- **The formula:** every high hook-rate hook opens a loop with a strong human trigger, keeps it obviously playful, and never names the product. Account-wide, the hooks with the best hook rate (£1k+ spend) used these frameworks:
  - **Fight forecast:** "babe yeah walk the dogs you never do it ARGUMENT INCOMING..." (80%), "Divorce papers are being drafted 🤣" (69%), "(this didn't go well)". Viewers stay to see the row.
  - **Warning to a group:** "HUSBANDS: NEVER TRUST A RANDOM GIFT BEFORE BED 😂" (84%). A callout and a rule that begs "why?"
  - **Broken expectation:** 'I told my wife "I wanted nothing" and found the one gift' (82%, £171k spend), "They said DON'T buy anything for Christmas" (73%, £179k).
  - **Blame or accusation, with an angry emoji:** "She kept stealing it 🤬" (70%), "THIS MISTAKE COST US $$$ 😡" (71%, ROAS 2.5).
  - **Quote plus a universal truth:** "'IT'S YOUR TURN.' - THE BEGINNING OF EVERY MARRIED COUPLE'S ARGUMENT." (75%).
  - **Outsized claim:** "THE $30 GIFT THAT TOOK OVER XMAS 🎄" (77%).
  - **Self-doubt mystery:** "I thought it was just me being PARANOID 💀" (77%).
  - **Meme unlock:** "Jealous husband unlocked 👀 (over this of all things)", REDSKIT's best performer (user, 2026-11-03).
- **Box size and fit:** hook boxes are CapCut size 12, which is the house 75px (from the reference CapCut project), and never smaller. They never run to more than two lines. If the wording won't fit, shorten it ("Xmas" for "Christmas", drop a phrase) rather than shrink the text or add a third line.
- **Box placement:** the hook box must fit inside the centred 4:5 box (y 285 to 1635 at 1080x1920), because outside it the text is hidden in the feed. Within that, there's no fixed spot: place it for the footage underneath, clear of faces and the product, and check every frame it's on screen, B-roll included. If one spot can't clear the whole opening, move the box at the cut (user, 2026-11-03).
- **Always draw boxes with the template's `box_layer`.** It's the CapCut look. A home-made multi-line version gave jagged, glitchy edges (OBSKIT v4 and v5).
- Take big swings across these frameworks, not variations of one gift line, and give each hook of an ad a different framework.
- **Avoid left-field drama hooks** (cheating, affairs, "is my husband hiding something"). They pull in the wrong viewers, who switch off once they see it's a head torch (user, 2026-11-03). Hooks follow the story and the gift, not the brief's dramatic premise.

## QA warnings to expect
Filler, pause and length warnings are normal for this style, because of the rules above. Reply to them in the review app rather than changing the edit.
- Two-line house box hooks: word them so the lines differ clearly in width, the shorter line on top. Near-equal lines merge into a flat block that doesn't look like CapCut, and unmerged they leave a notch (user, CRAZYGF and HEADSKIT C, 2026-11-11).
- End CTA boxes sit well inside the 4:5 box, not touching its edges: LOW STOCK's bottom edge at least 80px above the box's bottom (y 1555 or higher at 1080x1920). At top 1500 it read as "too close to the bottom" (user, PRANK700, 2026-11-18).
- Skit text hooks go in the top third of the 4:5 box when the faces are in the middle of the frame, sized so they don't cover a face. A bracketed second line ("(wait for the end)", "(over this of all things)") is white text with a dark outline and NO box, under the white box (user, PRANK700, 2026-11-18).
- Counting gags ("$1, $2, $3") get one caption per number. When a feature B-roll sits before a joke, cut back to the creators for the joke (user, PRANK700).
- B-roll must be at least as long as its slot: check the source clip has enough footage left after the in-point, or the last frames flash back to the creator (user, HONEST, 2026-11-19: `Bulky Headtorches/ege.mov` from 5.6s only has 4.0s left).
