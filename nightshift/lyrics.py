"""Lyric timing.

transcribe(): word timestamps with faster-whisper (CPU is fine; a separated vocal stem transcribes better than the mix).
align(): the transcript is noisy, the lyric sheet is right. Align the sheet's words to the heard words and keep
         the sheet's text with the measured timing. Words the recogniser missed are spread across their line.
voice_pitch(): median pitch of a stretch of vocal, to check that a second singer really is a different voice.
"""
import difflib
import json
import re

import numpy as np

norm = lambda t: re.sub(r"[^a-z0-9']", "", t.lower())


def sheet_lines(lyrics_text):
    """Lyric lines from lyrics.txt: section tags ([Verse]) and blank lines dropped."""
    out = []
    for line in lyrics_text.splitlines():
        line = line.strip()
        if not line or (line.startswith("[") and line.endswith("]")) or line.startswith("#"):
            continue
        out.append(re.sub(r"\s+", " ", line))
    return out


def whisper_model(model="small.en"):
    """A local copy in models/faster-whisper-<name> (next to the face models) wins over a Hugging Face download."""
    import os
    local = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", f"faster-whisper-{model}")
    return local if os.path.exists(os.path.join(local, "model.bin")) else model


def transcribe(audio, out, prompt=None, model="small.en", language="en"):
    import librosa
    from faster_whisper import WhisperModel
    m = WhisperModel(whisper_model(model), device="cpu", compute_type="int8")
    a16, _ = librosa.load(audio, sr=16000, mono=True)
    segs, _ = m.transcribe(a16.astype(np.float32), word_timestamps=True, vad_filter=True, language=language,
                           initial_prompt=prompt)
    words = []
    for s in segs:
        for w in s.words:
            words.append({"word": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2), "p": round(w.probability, 2)})
    with open(out, "w") as f:
        json.dump({"source": str(audio).replace("\\", "/").split("/")[-1], "words": words}, f, indent=1)
    return words


def align(lines, words, until=None):
    """lines: lyric sheet lines. words: transcript words. Returns [{start, end, text, words:[{w, s, e}]}]."""
    cw = [(li, w) for li, l in enumerate(lines) for w in l.split()]
    sm = difflib.SequenceMatcher(None, [norm(w) for _, w in cw], [norm(w["word"]) for w in words], autojunk=False)
    tmap = {}
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            tmap[a + k] = words[b + k]
    out = []
    for li, text in enumerate(lines):
        idx = [i for i, (l, _) in enumerate(cw) if l == li]
        hits = [tmap[i] for i in idx if i in tmap]
        if not hits:
            continue
        t0, t1 = hits[0]["start"], hits[-1]["end"]
        if until is not None and t0 >= until:
            break
        ws = []
        for k, i in enumerate(idx):
            if i in tmap:
                ws.append({"w": cw[i][1], "s": tmap[i]["start"], "e": tmap[i]["end"]})
            else:
                frac = k / max(1, len(idx) - 1)
                ws.append({"w": cw[i][1], "s": round(t0 + frac * (t1 - t0), 3), "e": round(t0 + frac * (t1 - t0) + 0.2, 3)})
        out.append({"start": t0, "end": t1, "text": text, "words": ws, "matched": len(hits), "of": len(idx)})
    return out


def coverage(lines, words):
    """Share of sheet words the recogniser heard in order: a quick 'did the model sing my lyrics' score for picking songs."""
    al = align(lines, words)
    total = sum(len(l.split()) for l in lines) or 1
    return round(sum(l["matched"] for l in al) / total, 3)


def voice_pitch(audio, start, end):
    import librosa
    y, sr = librosa.load(audio, sr=16000, mono=True, offset=max(0, start), duration=max(0.5, end - start))
    f0, vflag, vprob = librosa.pyin(y, fmin=65, fmax=800, sr=sr, frame_length=1024)
    f = f0[(vflag) & (vprob > 0.5)]
    return round(float(np.median(f)), 1) if len(f) else None


def analyze(project, model="small.en", stem=None):
    """song -> song/beatmap.json, song/words.json, song/lines.json"""
    from .beatmap import beatmap
    from .song import song_path
    song = song_path(project)
    bm = beatmap(song, project.path("song", "beatmap.json"), project.cfg.get("bpm"))
    sheet = sheet_lines(open(project.path("song", "lyrics.txt"), encoding="utf-8").read())
    words = transcribe(stem or song, project.path("song", "words.json"), prompt=". ".join(sheet[:6]), model=model)
    lines = align(sheet, words)
    project.save("song/lines.json", {"lines": lines})
    return {"duration_s": bm["duration_s"], "bpm": bm["tempo_bpm_detected"], "beats": len(bm["beats"]),
            "words_heard": len(words), "lines_timed": len(lines), "lines_on_sheet": len(sheet),
            "coverage": coverage(sheet, words), "loop_seam": bm["loop_seam_chroma_similarity"]}
