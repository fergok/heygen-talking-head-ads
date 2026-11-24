# Luxe Light

This folder is the working brain for Luxe Light: the user works from here, feeds in footage or a static, and asks for an ad. It holds what we know about the brand, and it will grow to include winning ads, reviews, comments and personas. Add those when there's something real to save.

## How to work from here

- Scripts and video edits both happen from this folder. The `ve-video-edit-general`, `apply-notes` and `video-qa` skills load here, linked from `~/Video Editing Test`, so there is one copy of each. So do the skills for each type of video: `benefit-stack`, `ugc-skit` and `bof-voiceover`. When the user asks for a type of video, use its skill. The old `video-ad-editing` and `ai-voiceover-ads` skills are archived and no longer load.
- Before any video edit, read `~/Video Editing Test/CLAUDE.md` and follow it. Edits, styles, the review app and shared assets all stay in that folder, so use its full path.
- This file and `product-summary.md` are the master brand files. `~/Video Editing Test/Brands/LuxeLight/` links back to them.
- Save finished ads as `~/Video Editing Test/CLAUDE.md` sets out, in monthly folders in `~/Documents/LuxeLight Ads/`. That folder is only for finished ads, so never put brand files or working files there.
- Ad breakdowns from the `creative-winning-variables` skill go in `reference-ads/<ad>/breakdown.md`, with their evidence beside them. The running library of winning and losing variables is `winning-variables.md`. Read it before every breakdown and before writing a new concept.
- Founder story ads ("This is Alex…") have no skill yet: follow `~/Video Editing Test/Styles/Founder story/style.md`. The user cuts the voice and B-roll in CapCut; Claude adds captions, movement, transitions, sounds and music to that draft (user, 2026-11-17).
- Example ads for each style are in `~/Video Editing Test/Styles/<style>/Reference Ads/`.
- Only save a correction as a lasting rule when the user says it should apply from now on. A note on one script applies to that script only (user, 2026-11-20). When they do say it's for good: if it applies to all editing, add it to `video-editing-standards.md` in `ve-video-edit-general`; if it applies to one style, add it to that style's `style.md`; if it applies to Luxe Light, add it here.
- The goal is a daily loop, with a couple of finished ads waiting each morning. When ads are passing review with no changes, suggest the schedule. Don't set it up before then.

## Brand rules

- In scripts, the sewing persona is "stitching", not "quilting" (user, 2026-11-07).
- New gifting scripts follow the beats of a winning ad line by line (Grown Men Gifts, Family Feud V2, Gifts for Women 2) with the new persona swapped in. Don't invent a new structure, and show which winning beat each line copies (user, 2026-11-09).
- Gifting scripts give each person a colour (black, orange, pink) and call pink and orange limited editions (user, 2026-11-09).
- Every script works in the colours and the red light, with no exceptions (user, 2026-11-10).
- Never reuse a line or phrase from one of our own earlier scripts (for example the "sci-fi movie" line). Write bodies and closes in the patterns of `winning ads/00 Copy patterns (body and close).md`, with fresh wording. Read that file before writing any body or close (user, 2026-11-10).
- Primary text is a hook line, then 3–4 benefit lines each starting with the green check ✅, then the offer line with 👇. Nothing else: no story and no colour-per-person paragraph. Write one primary text per ad with a broad hook line that fits every video hook and never repeats them (user, 2026-11-16, replacing one per hook from 2026-11-10).
- Skit scripts never have a character speak to the audience (no "Ladies, back me up in the comments") and never use generic reasons for using the light. Never write anyone holding a phone in their mouth to see. Nobody does that (user, 2026-11-12).
- Hunter red light, from the user's comment pull (2026-11-13): say the benefit as behaviour ("walk in without spooking them", "keeps your night vision for when you sit down"). Never say "deer can't see red", because commenters argue red vs green under the ads. Don't promise green light or a dim red mode. The wave sensor only works once it's switched on, which answers the "branches keep switching it off" complaint. Deer camp and hunting buddies are a multi-buy angle.
- Astronomers: hold. The top astronomy comments (11 and 10 likes) say the red is too bright unless it dims, and the product has no dim red. Don't write astronomy ads until that's fixed or confirmed.
- Never say "three-pack", "pick the 3-pack" or call the bundles packs or packages. There are no packs: the buyer just picks how many lights they want and a colour for each. Say "choose three" or "get three" (user, 2026-11-16).
- Never word a script so the discount sounds tied to a colour choice (for example "choose three and make it one camo, one pink and one orange" right before the discount line). Picking colours is a freedom, not a condition: say "whatever you choose, the discount adds itself" (user, 2026-11-16).
- Never use a per-light bundle price in a hook, hook text or script ("under $23 each", "from $17.40", "3 for under $23 each"). People check the website, see $36 for one, don't notice the bundle price and call the ad deceptive. Lead with the percentage off, the free case, free shipping on three or more, or the sale itself (user, 2026-11-17).
- Keep the family-run format but vary the people, use cases, feature order and features from script to script. Stop defaulting to the garage, the son-in-law in construction or greasy hands on the car. Don't list the colours at the start of the body: hand them out person by person, and include camo. Rotate how the close frames the offer (Black Friday, the free case first, the Christmas cutoff, free shipping on three or more) instead of always "up to 50% off, which is how I fit…" (user, 2026-11-18).
- `winning ads/` holds the bodies and closes of the top-spending story ads (top and mid funnel, no BOF), one file per ad. Add new winners there as they appear.
- Before writing any hook or text hook, read `hook-library.md` in this folder: every hook the user picked, locked, wrote or rejected, with their reasons. Build each option on a named entry there, and add every new pick or rejection to it the same day (user, 2026-11-21).
- Hooks are short and open a curiosity gap: tease the bad moment or the twist, never say what happened in the first line. Foreshadowing hooks should feel threatening (user, 2026-11-09). Every hook also qualifies the viewer: name the persona (for example "if your husband delivers packages") and use a mechanism from our winning hooks. Unaware story teases with no persona were rejected (user, 2026-11-09).

Add them here as the user gives them. Check the `luxelight-ugc-editor` skill for existing brand rules, and confirm with the user before relying on them.

Before writing any ad that talks about features or a persona, read `product-summary.md` in this folder. It's the user's own summary of what the product is, how it works and its features. Parker holds the deeper data for LuxeLight, under brand ID `0b442f93-6d76-44f0-afa6-22102c89c65d`.

## Benefit Stack ads

To make one, use the `benefit-stack` skill, which follows `~/Video Editing Test/Styles/Benefit stack/style.md` step by step. It has the whole process, from the request ("make a Benefit Stack ad for [persona] from [static]") to delivery, plus how to run several at once. The rules below are the LuxeLight copy rules it relies on.

Reference ads are the Hunters and Stitchers Benefit Stack ads (V1 to V3 of each) in the user's Drive folder "benefit stack ads". Stitchers is the winner (user, 2026-11-02), so copy its psychological levers when writing for a new persona. Use Hunters only as a style reference alongside it.

No chip is fixed to a position, not even battery life or the free case. The chips and their order depend on the persona (user, 2026-11-03). Choose them in this order:
1. The value props of the ad or static the new ad comes from. Usually it's a static or video that already performed well, now being tested in this format. Get them from Parker's value props for that ad (`search_facebook_ads_sql` with `adIds` and `include: ["extended"]`, or the ad's report through `search_facebook_ads_semantic`), or by reading the image.
2. If there aren't any, use reviews and comments from that persona in Parker.
3. If that's still thin, use our own reasoning, research online, or brainstorm with the user, and say which chips came from this step.

Chips name features: something the product has or does that you could point to on it or its spec sheet, such as "230-degree beam" or "wave sensor" (user, 2026-11-03). Fit or compatibility claims count, like "works with your glasses". Use cases and benefits, like "reading in the tent", don't go on chips. Turn each persona reason into the feature that enables it, and let the clip show the benefit. A colourway ("comes in pink") is never a chip, even when Parker lists it as a value prop. Show the colour in the B-roll instead (user, 2026-11-03).

For a persona that buys mainly for one feature (astronomers and red light), make two ads (user, 2026-11-04). The first keeps the feature chips above. The second puts the benefits of those features on the chips ("protects night vision", "no bugs in your face"), with its own hooks, such as "WHY ASTRONOMERS LOVE THIS RED LIGHT HEADLAMP". Both use the same hook clips. Benefit claims the user has approved for astronomers: red light doesn't draw bugs to your face, preserves night vision, helps you see the stars, and doesn't blind people around you.

Body B-roll for a persona with little footage of its own can come from any board: hands holding or switching the light, packing up, reading maps, walking down a street, the wave sensor. Don't show horses or people actually hunting outside horse and hunting ads (user, 2026-11-04).

Use six chips in total, three per clip across two clips. If the source has fewer than six value props, add the most logical benefit for that persona to fill the gap. For example, the user added "8 hour battery life" to the Stitchers video because stitchers sit for hours at a time.

## Lumi Light copies (daily)

Every day, the top Lumi Light video ad from the last week (by impressions) becomes one LuxeLight ad in three hook versions. It was three ads a day at first, but the user cut it to one on 2026-11-07 to save usage. The whole process is in `competitor-replication/RUNBOOK.md`, and the ads already copied are in `competitor-replication/log.json`. The rules (user, 2026-11-07):
- Copy the script word for word, with no tightening. The only changes are swapping Lumi Light for LuxeLight, plus one short mention each of the red light and the colours.
- The voice matches the gender of theirs: an American woman (Alexandra) or an American man (Liam, or Brian for older voices). Match their pace too.
- Hook A is their hook. Hooks B and C are ours, drawn from our ads with over $5K spend and fitted to the angle of the ad being copied.
- Never copy the same ad twice.
- One narrator only. A second voice in their ad is usually a reaction clip. Replace it with a real reaction clip of ours, with its own sound and the same energy, and never voice it with ElevenLabs. If a reaction can't be matched, skip that ad and take the next one.
- Trial: scheduled runs on Nov 8 and 9, 2026. **Paused by the user on 2026-11-09 because the quality was poor** (LUMI1108 needed three rebuilds to match the ad). Don't schedule it or run it daily again until the user asks.

## Camo launch

The user said on 2026-10-30: camo dropped that day, there are only about 8,000 units, and it's positioned as a seasonal Halloween drop that will go away soon. Lean into being new, limited and seasonal in camo ads. Don't use fence-sitter or "in your cart" hooks for camo while it's new. They suit the colours that have been around longer.

The user said on 2026-11-02 that camo is now sold out, so check before making new camo ads. On 2026-11-12 the user said camo is coming back, so scripts can include it again.

## Red light feature

A recently released and popular feature of the headtorch. Red light ads must say briefly that it switches from white light to red light, because many people assume a red light head torch only does red light (user, 2026-10-31). Don't open the body with it. Keep the usual format and place it naturally after the discount line and before the close, such as "Don't worry, you can still switch from white light to red light on the LuxeLight 2.0."

## Halloween offer

The sale running on 2026-10-31 is themed as a Halloween offer, so hooks, hook text and closes for that sale should say so.

## Voiceover and working files

- Voiceovers use the ElevenLabs connector: voice Alexandra (`kdmDKE6EkgrWrrykO9Qt`), model `eleven_v4`, flow `BJj3BPq2seUs3yCSsr7q`, with the prompt prefix `[casual, conversational, quick pace]`. Run `creative_generate_speech`, then `creative_get_flow_run_status` for the audio link.
- Record each concept's hooks and body as one tightened voiceover, and mark where each hook stops with `end` in `config.json`.
- The last finished project is `~/.video-editing-work/luxe-light/camo-new-drop/`. Use its `config.json` as the template for new ads.

## Footage

Clip-by-clip notes (where each kind of footage lives, good and banned clips, colour clip lists) are in `footage.md` in this folder. Read it before picking B-roll for any LuxeLight ad. The user's own B-roll picks, sorted by script beat with the in-point and how each clip is timed to the line, are in `clip-picks.md`. Start every body B-roll choice there (rulebook 6.54). After each finished edit the user hands back, add their picks to it, line by line.

## Current offer

From a screenshot the user sent on 2026-10-30, of tryluxelight.com/products/headtorch-test. Only make offer claims this supports, and ask the user if it may have changed.

| Bundle | Price | Per light | Free carry cases | Free shipping |
|---|---|---|---|---|
| Get 1 | $36.00 | $36.00 | 1 | Not shown |
| Get 2 | $51.99 | $26.00 | 2 | Not shown |
| Get 3 (Most Popular) | $66.99 | $22.33 | 3 | Yes |
| Get 5 (Best Value) | $86.99 | $17.40 | 5 | Yes |

- Colours: Black, Orange, Pink, Camo (new). Each light in a bundle can be a different colour.
- The page says: "Free carry case with every Luxelight you buy", "No code needed", "Last chance, limited stock", "Limited time bundle savings", "Loved by 150,000+ customers".
- The discount isn't only for bundles (user, 2026-10-30), so don't imply people must buy three to get it. Free shipping only shows on Get 3 and Get 5, so don't promise it to everyone.
- When the script or brief states the offer (for example "30% off"), the end box uses that offer. Don't ask the user to confirm it, even when the offer scene isn't in the footage (user, 2026-11-03).
- Buy-10 offer (user, 2026-11-22): "Up to 61% off. Mix & match colours and get a free carry case with every headlamp." Get 10 works out at $14 a light; the user OK'd "$14" in the judgy aunt hook only.
- No sale end date is shown. On 2026-10-30 the user said to use "ends tonight" urgency in these ads anyway, so don't ask about it again.
