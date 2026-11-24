"""Word-level timings for the tightened voiceover. Writes work/words.json and prints the text with times.

Usage: python -I transcribe.py <project>
Transcribing AFTER tightening matters: on raw audio the model stretches words across pauses, which makes captions start early.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # -I leaves the script folder off the path
import json

from faster_whisper import WhisperModel

from common import project

project()
model = WhisperModel("small.en", device="cpu", compute_type="int8", cpu_threads=4)
segs, _ = model.transcribe("work/vo_tight.wav", word_timestamps=True)
words = [dict(w=x.word.strip(), s=round(x.start, 3), e=round(x.end, 3)) for s in segs for x in s.words]
json.dump(words, open("work/words.json", "w"), indent=0)
print(" ".join(f"{w['w']}[{w['s']:.2f}]" for w in words))
