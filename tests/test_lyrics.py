"""Lyric timing without Whisper: cleaning invented words, the first-word lead-in, coverage and clarity (Nov 19 fix for
'2 of 6 lyric lines timed')."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nightshift import lyrics

SHEET = ["Every light is burning for someone", "Tell me what you're chasing", "Only the night knows"]


def w(word, s, e, p=0.95):
    return {"word": word, "start": s, "end": e, "p": p}


def main():
    # the lyric prompt echoed back: a burst of sheet words at one instant is dropped, the real singing kept
    echo = [w(x, 13.91, 13.91) for x in "Every road is open. Only the night knows.".split()]
    sung = [w("Tell", 16.49, 16.7), w("me", 16.77, 16.9), w("what", 16.93, 17.1), w("you're", 17.11, 17.3),
            w("chasing.", 17.35, 18.0)]
    tail = [w("night", 38.2, 38.25), w("night", 38.28, 38.3), w("knows", 39.0, 39.5, p=0.0)]
    got = lyrics.clean(echo + sung + tail)
    assert [x["word"] for x in got] == ["Tell", "me", "what", "you're", "chasing.", "night"], got
    print("ok   clean: prompt echo, back-to-back repeats and 0-probability words dropped")

    # without a voice filter the first word of a line soaks up the pause before it: the line starts 0.5 s before it ends
    words = [w("Only", 23.44, 26.5), w("the", 26.5, 27.04), w("night", 27.04, 27.78), w("knows", 27.78, 28.78)]
    al = lyrics.align(SHEET, words)
    assert len(al) == 1 and al[0]["start"] == 26.0 and al[0]["words"][0]["s"] == 26.0, al
    print("ok   align: a 3 s first word starts the line at 26.0 s, not 23.44 s")

    full = [w(x, 1 + i * 0.4, 1.3 + i * 0.4, p=0.9) for i, x in enumerate(" ".join(SHEET).split())]
    mumbled = [dict(x, p=0.5) for x in full]
    assert lyrics.coverage(SHEET, full) == lyrics.coverage(SHEET, mumbled) == 1.0
    assert lyrics.clarity(SHEET, full) > lyrics.clarity(SHEET, mumbled)
    print("ok   coverage ties are broken by clarity")
    print("lyrics ok")


if __name__ == "__main__":
    main()
