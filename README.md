# HeyGen talking-head ads: the whole workflow

Everything used to make LuxeLight's HeyGen talking-head ads with Claude Code: the skills, the editing rulebook, the style notes, the CapCut tools, the review app and the brand files. You ask Claude Code for an ad and it runs the pipeline: script, character image, voiceover, HeyGen lip-sync, edit, CapCut project, QA, review app.

## What's inside

```
Video Editing Test/                 -> goes to ~/Video Editing Test
  CLAUDE.md                         how Claude works in this folder
  .claude/skills/
    heygen-talking-head/            the HeyGen ad skill (start here)
    ve-video-edit-general/          general editing skill + the main rulebook
                                    (references/video-editing-standards.md)
    apply-notes/                    the review app (notes pinned to the playhead) + applying notes
    video-qa/                       automatic QA pass on every render
    benefit-stack/ ugc-skit/ bof-voiceover/   the other ad styles
  Styles/
    HeyGen talking head/style.md    the HeyGen pipeline, step by step, plus reference ads
    AI voiceover story/style.md     voiceover cutting, B-roll, captions, CapCut hand-off
    (Benefit stack, UGC skit, Founder story, AI voiceover BOF notes)
  tools/capcut/                     story_ad.py / story_hooks.py build the edit as an MP4 AND a real
                                    CapCut project; graft_hook.py, heygen_effects.py, swap_hook.py,
                                    check_bodies.py, capcut_draft.py (read/diff CapCut projects)
  tools/captions/                   house caption engine + TikTok "reply to comment" bubble maker
  Assets/                           end-box click, sound effects, music, banners
  Edits/XMASCUTOFF/scripts/         a real finished HeyGen ad's edit script, to copy from

LuxeLight Claude/                   -> goes to ~/Documents/LuxeLight Claude
  CLAUDE.md                         brand rules (this is where you'd start a session)
  product-summary.md footage.md clip-picks.md hook-library.md winning-variables.md
  winning ads/  reference-ads/  heygen-characters/
```

## The HeyGen pipeline (short version, full one in `Styles/HeyGen talking head/style.md`)

1. Script: a competitor ad rewritten, one body + three big-swing hooks.
2. Background: a real screenshot of a UGC creator's room (never a generated room).
3. Face: a Pinterest photo of the persona.
4. Composite with Nano Banana Pro on **Sume** (`google/nano-banana-pro`): face into the room, same pose, changed enough to be a new person. 3-4 variations, pick the most real.
5. **HeyGen** photo avatar from that image.
6. **ElevenLabs** voiceover: all three hooks then the body, in one file.
7. Speed it to 1.05x with ffmpeg (`atempo=1.05`), no faster or the lip sync looks off.
8. One HeyGen render of the whole voiceover, 9:16, 1080p.
9. Cut into V1/V2/V3 (hook 1/2/3 + the same body).
10. Edit with `tools/capcut/story_hooks.py <edit.json> --hook A --mp4 --capcut` -> MP4 in the review app + CapCut project. Then `heygen_effects.py` for the black-and-white / blur / bubble effects, `graft_hook.py` to put the finished V1 body under the other hooks.

## Setup (Mac, Apple Silicon)

1. Install [Claude Code](https://claude.com/claude-code), [CapCut desktop](https://www.capcut.com) and Python 3.
2. Download this repo, open Terminal in it and run:
   ```bash
   bash setup.sh
   ```
   It copies the two folders into place (it never overwrites files you already have), links the brand files, fixes paths for your Mac and installs the Python tools.
3. Connect these in Claude (claude.ai -> Settings -> Connectors), since the pipeline calls them:
   - **HeyGen** (avatar + lip-synced render)
   - **ElevenLabs** (voiceover)
   - **Sume** (Nano Banana Pro image generation)
   - Optional: Playbook (B-roll library), Parker (ad data, reviews, comments), Google Drive.
4. Voice IDs in `style.md` are from the original ElevenLabs account. Swap in your own voices if they don't show up for you.
5. The `luxelight-headtorch-wearing-reference` skill (drawing the headtorch on the character) lives in a claude.ai plugin, not in this repo. Skip it or recreate it with your own product reference photos.

## Using it

Open Claude Code in `~/Documents/LuxeLight Claude` and say something like:

> Make a HeyGen talking-head ad from this competitor ad: <link>. Persona: American mum, 40s.

Claude follows `heygen-talking-head` -> rulebook -> brand files -> style notes. Every render lands in the review app at http://localhost:8765 (start it with `python3 ~/Video\ Editing\ Test/.claude/skills/apply-notes/scripts/review_server.py`). Leave notes there, then say "apply notes on <CODE>". CapCut projects show up in CapCut's project list, ready to tweak and export.

## Things to know

- B-roll footage isn't included (too big). `footage.md` and `clip-picks.md` reference clips by file name; point Claude at your own B-roll folder and it will build its own notes.
- `tools/capcut/templates/` hold the original editor's CapCut timeline, used for caption look, end stack and click. File paths inside them point at the original Mac and are only used as style references.
- Captions use CapCut's ProximaNova font from CapCut's cache. Open CapCut once and add any caption so it downloads.
- Reference ads over 40 MB were left out to keep the repo light.
