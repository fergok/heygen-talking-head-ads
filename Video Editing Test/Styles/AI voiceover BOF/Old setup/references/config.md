# config.json

One file in the project folder drives the render. Clip names are filenames in `src/` without the extension.

```json
{
  "name": "Brand_Product_Concept",
  "voiceover": "drive/vo.mp3",
  "music": "music/bed.mp3",
  "music_volume": 0.09,
  "fixes": { "wrong transcription": "Right Spelling.", "omega -3": "omega-3" },
  "proper_nouns": ["USA", "D3"],
  "caption_max_words": 4,
  "body": {
    "shots": [
      ["first words of the body", "clip_a", 0.0],
      ["next sentence starts here", "clip_b", 6.0]
    ]
  },
  "versions": [
    {
      "name": "Version1",
      "hook": ["First line of the hook card", "SECOND LINE 🚫"],
      "shots": [
        ["first words of this hook", "clip_c", 14.0],
        ["second sentence of this hook", "clip_d", 26.3]
      ]
    },
    {
      "name": "Version2",
      "hook": ["Another hook card", "second line 😩"],
      "shots": [["first words of the second hook", "clip_e", 0.0]],
      "end": "first words after this hook"
    }
  ]
}
```

## Fields

- **shots**: `[cue, clip, in-point seconds]`. A shot starts when the cue is spoken and runs until the next cue, so cuts stay locked to the voiceover. Cues are the first few words of the sentence, matched against `work/words.json`, ignoring case and punctuation.
- **body.shots**: the first cue marks where the body starts. Every version plays its own hook and then this same body.
- **end**: where a hook stops, if the voiceover has several hooks recorded back to back. Leave it out when the hook runs straight into the body.
- **fixes**: exact words (as in `work/words.json`, with their punctuation) to replace. Use it for brand names and numbers the transcriber gets wrong. Several words can become one, such as `"2 a .m.": "2am."`. An empty value deletes them.
- **proper_nouns**: words kept in this exact case. Other caption text is lowercase, apart from "I".
- **captions**: optional list of exact caption lines, used to copy a reference ad's captions. Together they must match every spoken word in order, and the render stops if they don't. Without it, captions are split automatically.
- **captions_in_hook**: optional, default false. Shows captions under the hook card during the hook, as bottom-of-funnel ads do.
- **hook_y**, **hook_styles**, **hook_font_size**: optional. The top of the hook card in pixels, the `[text, box]` colours per line, such as `[["white", [238, 45, 66]], ["black", "white"]]`, and the text size.
- **hook_y** and **hook_font_size** on a version: override the position or text size for that version only, for when the hook text would land on a head or the product, or is short enough to go bigger.
- **caption_wrap**, **caption_bottom**: optional. The share of the frame width a caption can fill before it wraps onto two lines, and the pixel position of its bottom edge.
- **music**: optional. Omit it for no bed.
- **width/height/fps**: optional, default 1080×1920 at 30fps. The 4:5 safe box is worked out from these.

## Hook card

Two boxes: white on red, then black on white, with any emoji on the line drawn in colour. The text matches CapCut's System font with Bold on. This is a default, so change `hook_png` in `render.py` if the reference ads for the project use a different look.
