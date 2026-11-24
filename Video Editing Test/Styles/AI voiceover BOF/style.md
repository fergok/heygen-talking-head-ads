# AI voiceover, bottom of funnel

Short deal-focused ads for people who already know the product: an AI voiceover over B-roll, with no creator on camera.

**The main rulebook always wins.** It holds the newest rules, from the Red Light Skit reviews. Everything in `Old setup/` comes from before those reviews, so it adds detail but never overrides them. The old scripts haven't been run since the move, and they still use the old text and caption behaviour.

## What's in this folder
- `Old setup/references/bottom-of-funnel.md`: how to write and cut this style. Read it before any script or edit. It records the user's earlier corrections.
- `Old setup/workflow.md`, `references/config.md` and `scripts/`: how the old ads were built.
- `Reference Ads/`: example ads to watch first.
- `Finished Ads/Luxe Light/`: Camo New Drop, Camo Triple Discount, Orange BOF, Pink BOF and Red Light BOF, with their older rounds.
- `Past ad settings/`: the hooks, shots and timings for each of those ads, plus sample frames of the colour footage in `footage-survey/`.
- Full working files for those ads stay in `~/.video-editing-work/luxe-light/`. They're large and out of iCloud on purpose.

## Where old and new rules differ, use the main rulebook
| Topic | Old setup | Use now |
|---|---|---|
| Captions during the hook | Shown under the hook text | Hidden until the hook leaves |
| Caption and text position | Inside the 4:5 box | Main rulebook positions |
| Music | Quiet bed on every ad | Only when asked, on some versions |
| End box | None | End box with bounce and click, where the references have one |
| Delivery | Sent as files | Review app, plus sent as files |
| Text style | CapCut System font, Bold | Same font; use the main rulebook's exact settings |

The red box over white box hook text in this style's reference ads differs from the skit's single box. It's the style's own look, so keep it unless the user says otherwise.

## Scrolling sale banner (user, 2026-11-17, BFCOLOURS)
- For a seasonal sale (Black Friday) the user wants a thin ticker banner that scrolls right to left in a loop for the whole ad, placed like their reference frame: a full-width band near the top of the 4:5 zone (top at y 345, 72px tall at 1080x1920, 150px a second). Full width is deliberate here.
- Their banner artwork is in `Assets/banners/` (1 yellow "FREE CASES / BLACK FRIDAY SPECIAL / UP TO 50% OFF", 2 "BIGGEST SALE OF THE YEAR", 3 "BLACK FRIDAY SALE", 4 "FREE CARRY CASES / UP TO 50% OFF / BLACK FRIDAY OFFER"). `Edits/BFCOLOURS/scripts/banner.py` makes a seamless strip from one and burns it onto a finished MP4.
- During the hook the banner runs in the lower third (top at y 1540) and the hook box keeps the top (y 300), so the text never covers the head torches. On the cut into the body the banner moves up to the top third (y 345) and stays to the end (user notes on BFCOLOURS v1: the first build put the banner on top throughout, which pushed the hook text down onto the product). Move the hook box lower only when the top would cover the product. Hook and end box lines must measure under 950px wide (`story_hooks.box_extent`), or they run off the sides.
- `video-qa` misreads the moving banner as hook text and captions, so its "captions missing", "captions under hook" and side safe-zone flags on a banner ad need checking by eye before acting on them.
- The build is `story_hooks.py` (hook shots and boxes) from `Edits/BFCOLOURS/scripts/edit_v1.py`; the old BOF scripts were not used.
- The hook text always sits in the top third. When the product is up there, change or reframe the clip so the text clears it; never move the text down (user, BFCOLOURS v2 notes, said twice).
- No per-light bundle prices anywhere in a hook, hook text or script ("under $23 each", "from $17.40"): the site shows $36 for one, so it reads as deceptive and people complain (user, BFCOLOURS v3, 2026-11-17). This overrides the "state a simple price such as under $23 each" advice in `Old setup/references/bottom-of-funnel.md`.

## Uploading to the OK App (user, 2026-11-24: "build this into the BOF workflow")
- When the user approves a BOF ad and asks for it to be uploaded, put it in the OK App queue with `tools/ok_app/upload.py <spec.json>` (try `--dry-run` first). It lands in Deliverables > Luxelight > Queue > Ready for Upload, created by Ferg. Never upload before the user asks: approval in the review app is not the go-ahead.
- One deliverable per concept, holding that concept's hook versions (the free-case ad is one deliverable with its three videos).
- File naming: `[CLAUDE] <ad name> - V1 - Ferg`, `- V2 -`, `- V3 -` (for example `[CLAUDE] BF All colours - V1 - Ferg`, `[CLAUDE] BF Free Case - V2 - Ferg`). The deliverable takes the first file's name, as the app does.
- Fields: Run Under Page "Luxelight"; primary text in the brand's hook / ✅ lines / 👇 offer format; a headline; description "Risk-free for 60 days" unless told otherwise; landing page PDP Luxelight (https://tryluxelight.com/products/headtorch-test); call to action "Shop Now".
- The browser route does not work for the files: the built-in browser can't attach local files and Chrome's upload tool stops at 10 MB. The script writes to the app's own Supabase project instead (settings in `~/.video-editing-work/ok_app.json`), and refuses to upload a title that is already there.
- After uploading, open https://ok-app-tasks.vercel.app/deliverables/luxelight/queue and check the card. The user signs in as Ferg themselves; never type the PIN.
