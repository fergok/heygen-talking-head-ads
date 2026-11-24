---
name: heygen-talking-head
description: Make a HeyGen talking-head video ad, where an AI character made from a real room screenshot and a Pinterest face talks to camera (lip-synced in HeyGen to an ElevenLabs voiceover) between B-roll, as in Red Light TOF V2. Use whenever the user asks for a HeyGen ad, a talking-head or AI-creator ad, an "AI UGC" ad, or to remake a competitor's talking-head ad with our own character.
---

# HeyGen talking head

The whole process lives in the style folder, so this skill only sets the order. Read these in full before starting:

1. `~/Video Editing Test/.claude/skills/ve-video-edit-general/references/video-editing-standards.md`, the main rulebook for every video.
2. The brand's files in `~/Video Editing Test/Brands/<brand>/`. For LuxeLight these are `brand-notes.md`, `product-summary.md` and `footage.md`, plus `~/Documents/LuxeLight Claude/clip-picks.md` and `hook-library.md`.
3. `~/Video Editing Test/Styles/AI voiceover story/style.md`, for cutting the voiceover, B-roll and the CapCut hand-off.
4. `~/Video Editing Test/Styles/HeyGen talking head/style.md`, the pipeline from script to HeyGen render and how the character is used in the edit. Follow its steps in order.

Tools: Sume (`google/nano-banana-pro`) for the character image, ElevenLabs for the voiceover, HeyGen for the avatar and the lip-synced render, `tools/capcut/story_ad.py` for the edit, `tools/captions/reply_bubble/make_reply.py` for comment-reply hooks. Use the `ve-video-edit-general`, `apply-notes` and `video-qa` skills for the shared steps. Save new rules where the user's notes belong: general ones in the rulebook, this style's in its `style.md`, brand ones in the brand notes.
