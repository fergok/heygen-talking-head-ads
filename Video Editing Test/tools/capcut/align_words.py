"""Forced alignment of a Whisper transcript to its audio (wav2vec2, torchaudio), for caption timing.

Whisper's word times can be 100-300 ms off at word boundaries, which is what made captions switch early or late
(user walkthroughs, XMAS3HOOK 2026-11-06 and CHEAPGENIUS 2026-11-07). This keeps Whisper's words but re-times
each one with a CTC forced alignment, which places word starts on the audio itself.

  align_words.py <audio> <whisper.json> [out.json]     -> writes <whisper>.aligned.json by default

Output: {"words": [{"word", "start", "end", "w_start", "w_end"}...]} where start/end are the aligned times and
w_start/w_end are Whisper's originals. Words the aligner can't place (no letters) keep Whisper's times.
"""
import json, os, re, subprocess, sys
import numpy as np
import torch, torchaudio

SR = 16000
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen " \
       "seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def num_words(n):
    n = int(n)
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000:
        rest = n % 100
        # spoken style for product numbers: 230 -> "two thirty", 150 -> "one fifty"
        return ONES[n // 100] + ("" if rest == 0 else " " + (num_words(rest) if rest >= 10 else "oh " + ONES[rest]))
    return " ".join(ONES[int(d)] for d in str(n))


def spoken(word):
    w = word.lower().replace("%", " percent").replace("&", " and ")
    w = re.sub(r"\$(\d+)", lambda m: num_words(m.group(1)) + " dollars", w)
    w = re.sub(r"(\d+)\s*am\b", lambda m: num_words(m.group(1)) + " a m", w)
    w = re.sub(r"(\d+)\s*pm\b", lambda m: num_words(m.group(1)) + " p m", w)
    w = re.sub(r"\d+", lambda m: " " + num_words(m.group(0)) + " ", w)
    w = re.sub(r"[^a-z' ]", " ", w)
    return [p for p in w.split() if re.search(r"[a-z]", p)]


def load_audio(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return torch.from_numpy(np.frombuffer(raw, np.float32).copy())


def align(audio_path, tx_path, out=None):
    words = [w for s in json.load(open(tx_path))["segments"] for w in s["words"]]
    bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
    model = bundle.get_model().eval()
    labels = bundle.get_labels()                       # ('-', '|', 'E', 'T', ...), '-' is blank
    idx = {c: i for i, c in enumerate(labels)}
    wav = load_audio(audio_path)

    emis = []
    with torch.inference_mode():                       # 30 s chunks keep memory flat
        step = SR * 30
        for a in range(0, len(wav), step):
            e, _ = model(wav[a:a + step].unsqueeze(0))
            emis.append(torch.log_softmax(e, dim=-1)[0])
    emission = torch.cat(emis)
    frame_s = len(wav) / SR / emission.shape[0]

    tokens, owner = [], []                             # one token per character; owner = whisper word index
    for wi, w in enumerate(words):
        for part in spoken(w["word"]):
            if tokens:
                tokens.append(idx["|"]); owner.append(None)
            for ch in part.upper():
                if ch in idx:
                    tokens.append(idx[ch]); owner.append(wi)
    ali, scores = torchaudio.functional.forced_align(emission.unsqueeze(0), torch.tensor([tokens]), blank=0)
    spans = torchaudio.functional.merge_tokens(ali[0], scores[0].exp())    # one span per target token, in order
    assert len(spans) == len(tokens), (len(spans), len(tokens))
    span = {}
    for sp, wi in zip(spans, owner):
        if wi is not None:
            s, e = span.get(wi, (sp.start, sp.end))
            span[wi] = (min(s, sp.start), max(e, sp.end))

    res = []
    for wi, w in enumerate(words):
        s, e = span.get(wi, (None, None))
        res.append(dict(word=w["word"].strip(), w_start=w["start"], w_end=w["end"],
                        start=round(s * frame_s, 3) if s is not None else w["start"],
                        end=round(e * frame_s, 3) if e is not None else w["end"]))
    out = out or re.sub(r"\.json$", "", tx_path) + ".aligned.json"
    json.dump({"audio": audio_path, "model": "WAV2VEC2_ASR_BASE_960H", "words": res}, open(out, "w"), indent=0)
    return out, res


if __name__ == "__main__":
    o, r = align(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    print("aligned %d words -> %s" % (len(r), o))
