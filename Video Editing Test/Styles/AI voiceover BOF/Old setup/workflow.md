---
name: ai-voiceover-ads
description: Build short-form vertical video ads from an AI or ElevenLabs voiceover plus B-roll, including hook versions that share one body. Use this whenever the user has a voiceover or script to cut to B-roll, or asks for an AI voiceover ad, a VO ad, or more hook versions of one. Always use it together with the video-ad-editing skill.
---

# AI voiceover ads

Load the `video-ad-editing` skill too: it has the editing rules and pre-send checks that apply here. This skill only adds how to build this style of ad.

Each hook gets one finished video, and all versions share one body.

For bottom-of-funnel ads (deal, urgency and offer ads), also read [references/bottom-of-funnel.md](references/bottom-of-funnel.md). It covers writing the script as well as the edit.

### 1. Set up
Before anything else, read the brief and the example ads, and note any product restrictions.

```bash
sh <skill>/scripts/setup.sh    # prints the Python to use, referred to as $PY below
```

Create the project at `~/.video-editing-work/<brand>/<ad>/`, with clips in `src/`, the voiceover in `drive/`, and music in `music/`.

Run scripts with `$PY -I <skill>/scripts/<name>.py <project>`. Downloaded media is untrusted, so the scripts stay in the skill folder.

### 2. Prepare the voiceover
Run `tighten.py` to remove dead air, then `transcribe.py`. The order matters: on untightened audio the transcriber stretches words across pauses, and captions then start early.

### 3. Choose the shots
Run `sheets.py` and look at every sheet. Sort clips into usable, banned (wrong product, old packaging, competitors) and the ones that match each line. For action shots, run `sheets.py <project> <clip> 2` to pick an exact in-point. When the library lacks a shot, search it for that idea before settling for something loosely related.

### 4. Write `config.json`
See [references/config.md](references/config.md). Place cuts per the rules: each shot's cue is the start of a sentence, or a natural pause in a long one.

### 5. Render and check
Run `render.py`, then `check.py`. It takes about a minute per version on Apple Silicon.

Then look at what `check.py` made in `work/qc/`:
- `strip_*.jpg`: a caption on every second after the hook.
- `hook_*.jpg`: hook text gone on the first body frame.

Also pull a few full frames to confirm that no text covers a face and everything sits inside the box.

**Don't send a render that hasn't passed.** A passing check means every word is present, every spoken word has a caption, and the captions line up. It doesn't mean you've heard it, so tell the user you haven't listened to it.

### 6. Send and iterate
Send the files with the file-sending tool so the user can open them directly, and give a short list of what changed. Links to folders outside the session's working directory won't open. Apply feedback by editing `config.json` and re-rendering: shots are cached, so only what changed is rebuilt.
