"""Lyric timing.

transcribe(): word timestamps with faster-whisper (CPU is fine; a separated vocal stem transcribes better than the mix).
heard(): the best of two transcriptions (with and without the lyric sheet as a prompt), cleaned of prompt echoes.
align(): the transcript is noisy, the lyric sheet is right. Align the sheet's words to the heard words and keep
         the sheet's text with the measured timing. Words the recogniser missed are spread across their line.
voice_pitch(): median pitch of a stretch of vocal, to check that a second singer really is a different voice.
"""
import difflib
import json
import re

import numpy as np

norm = lambda t: re.sub(r"[^a-z0-9']", "", t.lower())
LEAD_MAX, LEAD_KEEP = 1.0, 0.5   # a line's first word longer than 1 s starts 0.5 s before it ends


def sheet_lines(lyrics_text):
    """Lyric lines from lyrics.txt: section tags ([Verse]) and blank lines dropped."""
    out = []
    for line in lyrics_text.splitlines():
        line = line.strip()
        if not line or (line.startswith("[") and line.endswith("]")) or line.startswith("#"):
            continue
        out.append(re.sub(r"\s+", " ", line))
    return out


INSTRUMENTAL = "[Intro]\n[Instrumental]\n\n[Verse]\n[Instrumental]\n\n[Chorus]\n[Instrumental]\n\n[Outro]\n[Instrumental]\n"


def instrumental(project):
    """True for a song with no words: project.json "instrumental": true, or a lyrics.txt with only section tags."""
    import os
    if project.cfg.get("instrumental") is not None:
        return bool(project.cfg["instrumental"])
    path = project.path("song", "lyrics.txt")
    return not os.path.exists(path) or not sheet_lines(open(path, encoding="utf-8").read())


def whisper_model(model="small.en"):
    """A local copy in models/faster-whisper-<name> (next to the face models) wins over a Hugging Face download."""
    import os
    local = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", f"faster-whisper-{model}")
    return local if os.path.exists(os.path.join(local, "model.bin")) else model


_MODELS = {}


def _whisper(model):
    if model not in _MODELS:
        from faster_whisper import WhisperModel
        _MODELS[model] = WhisperModel(whisper_model(model), device="cpu", compute_type="int8")
    return _MODELS[model]


def _run(audio, prompt=None, model="small.en", language="en", vad=False):
    import librosa
    a16, _ = librosa.load(audio, sr=16000, mono=True)
    segs, _ = _whisper(model).transcribe(a16.astype(np.float32), word_timestamps=True, vad_filter=vad, language=language,
                                         initial_prompt=prompt)
    return [{"word": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2), "p": round(w.probability, 2)}
            for s in segs for w in s.words]


def clean(words):
    """Drop what Whisper invents rather than hears: a run of 3+ words stamped at the same instant (the lyric prompt echoed
    back, seen Nov 18: ten sheet words 'sung' at 13.91 s), words Whisper gives a probability under 0.1, and a word repeated
    back to back within 0.15 s ('night night night' over a fade-out)."""
    out, i = [], 0
    while i < len(words):
        j = i
        while j + 1 < len(words) and abs(words[j + 1]["start"] - words[i]["start"]) < 0.02:
            j += 1
        if j - i + 1 >= 3:
            i = j + 1
            continue
        w = words[i]
        if w.get("p", 1) < 0.1:         # guessed, not heard (a fade-out "sung" at probability 0.0)
            i += 1
            continue
        if out and norm(out[-1]["word"]) == norm(w["word"]) and w["start"] - out[-1]["end"] < 0.15:
            i += 1
            continue
        out.append(w)
        i += 1
    return out


def _score(lines, words):
    al = align(lines, words)
    return len(al), coverage(lines, words)


def heard(audio, lines, model="small.en", language="en"):
    """Words actually sung in audio, timed: the better of two passes, scored by lyric lines timed, then coverage.
    No voice-activity filter (it cut whole sung lines on some mixes). One pass without a prompt (on a vocal stem the
    lyric prompt made Whisper skip ahead and repeat the last line: 2 of 6 lines timed, Nov 18), one with the sheet's first
    lines as the prompt (it helps on a full mix). Returns (words, which)."""
    best = None
    for name, prompt in (("no prompt", None), ("lyric prompt", ". ".join(lines[:6]) or None)):
        words = clean(_run(audio, prompt, model, language))
        sc = _score(lines, words)
        if best is None or sc > best[0]:
            best = (sc, words, name)
        if sc[0] == len(lines) and sc[1] >= 0.95:
            break
    return best[1], best[2]


def transcribe(audio, out, prompt=None, model="small.en", language="en", lines=None):
    """Word timestamps into out (json). With the lyric sheet's lines: heard() picks the better of two passes."""
    if lines:
        words, which = heard(audio, lines, model, language)
    else:
        words, which = clean(_run(audio, prompt, model, language)), "prompt" if prompt else "no prompt"
    with open(out, "w") as f:
        json.dump({"source": str(audio).replace("\\", "/").split("/")[-1], "pass": which, "words": words}, f, indent=1)
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
        if hits[0]["end"] - t0 > LEAD_MAX:      # without a voice filter a line's first word soaks up the pause before it
            t0 = round(hits[0]["end"] - LEAD_KEEP, 2)
        if until is not None and t0 >= until:
            break
        ws = []
        for k, i in enumerate(idx):
            if i in tmap:
                ws.append({"w": cw[i][1], "s": max(t0, tmap[i]["start"]), "e": tmap[i]["end"]})
            else:
                frac = k / max(1, len(idx) - 1)
                ws.append({"w": cw[i][1], "s": round(t0 + frac * (t1 - t0), 3), "e": round(t0 + frac * (t1 - t0) + 0.2, 3)})
        out.append({"start": t0, "end": t1, "text": text, "words": ws, "matched": len(hits), "of": len(idx)})
    return out


def clarity(lines, words):
    """Mean recogniser confidence over the sheet words that were heard: breaks ties between takes that sing every line."""
    vocab = {norm(w) for l in lines for w in l.split()}
    ps = [w.get("p", 1) for w in words if norm(w["word"]) in vocab]
    return round(float(np.mean(ps)), 3) if ps else 0.0


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
    if instrumental(project):        # no words to time: the beats alone place the cuts
        project.save("song/words.json", {"words": []})
        project.save("song/lines.json", {"lines": []})
        return {"duration_s": bm["duration_s"], "bpm": bm["tempo_bpm_detected"], "beats": len(bm["beats"]), "words_heard": 0,
                "lines_timed": 0, "lines_on_sheet": 0, "coverage": 1.0, "instrumental": True,
                "loop_seam": bm["loop_seam_chroma_similarity"]}
    sheet = sheet_lines(open(project.path("song", "lyrics.txt"), encoding="utf-8").read())
    words = transcribe(stem or song, project.path("song", "words.json"), model=model, lines=sheet)
    lines = align(sheet, words)
    project.save("song/lines.json", {"lines": lines})
    return {"duration_s": bm["duration_s"], "bpm": bm["tempo_bpm_detected"], "beats": len(bm["beats"]),
            "words_heard": len(words), "lines_timed": len(lines), "lines_on_sheet": len(sheet),
            "coverage": coverage(sheet, words), "loop_seam": bm["loop_seam_chroma_similarity"]}
