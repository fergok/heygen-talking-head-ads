---
name: ugc-skit
description: Edit a UGC skit video ad, where creators act out a scene together and we add B-roll, house text, a hook box and the end box, as in the Red Light and Obsession skits. Use whenever the user has skit or UGC footage of creators acting a scene and asks for it to be edited, cut, hooked or turned into an ad ("I've got this UGC content, edit it").
---

# UGC skit

The whole process lives in the style folder, so this skill only sets the order. Read these in full before starting:

1. `~/Video Editing Test/.claude/skills/ve-video-edit-general/references/video-editing-standards.md`, the main rulebook for every video. Section 11a is the house look learned on the skits.
2. The brand's files in `~/Video Editing Test/Brands/<brand>/`. For LuxeLight these are `brand-notes.md`, `product-summary.md` and `footage.md` (clip notes), which link to the master copies in `~/Documents/LuxeLight Claude/`. They hold the product, offer and footage rules.
3. `~/Video Editing Test/Styles/UGC skit/style.md`, the skit's editing rules, hook wording and workflow. Follow its workflow in order, starting from `edit_template.py` in that folder.

Finished examples: `~/Video Editing Test/Edits/REDSKIT` and `~/Video Editing Test/Edits/OBSKIT`. Use the `ve-video-edit-general`, `apply-notes` and `video-qa` skills for the shared steps. Save new rules where the user's notes belong: general ones in the rulebook, skit ones in the style's `style.md`, brand ones in the brand notes.
