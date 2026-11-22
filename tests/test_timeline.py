"""Timeline pacing (Nov 21, from the Nov 20 upbeat run): squeezed shots get a minimum slot before the rest is shared, and a
long character slot is split into shots of at most the tone's split_seconds, cutting to the other framing."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nightshift import studio as S
from nightshift import timeline as T


def main():
    ch = S.character({"noun": "woman", "look": "late twenties, dark wavy hair", "outfit": "a cream knit sweater"})
    plan = S.shots(["seaside-dawn"], S.DEFAULT_LYRICS, 10, ch, shot_seed=7, tone="upbeat", vertical=True)["shots"]
    sing = [s for s in plan if s["mode"] == "lipsync"]
    assert sing and all(s.get("split", {}).get("framing") in ("close", "medium") for s in sing)
    assert all(s["split"]["framing"] != s["framing"] for s in sing), [(s["framing"], s["split"]["framing"]) for s in sing]
    assert all("Her hands stay empty, fingers relaxed." in s["split"]["video"] or s["split"]["framing"] == "wide" for s in sing)
    print("ok   studio: every singing shot carries a second framing for the timeline to cut to")

    # an 11.8 s singing slot at the upbeat tone's 4.5 s: three shots, close / medium / close, cuts inside the slot
    s08 = dict(next(s for s in sing if s["framing"] == "close"), id="s08", start=16.11, seconds=11.8)
    out = T.split([dict(s08)], 4.5)
    assert [x["id"] for x in out] == ["s08", "s08b", "s08c"], [x["id"] for x in out]
    assert [x["framing"] for x in out] == ["close", "medium", "close"]
    assert out[1]["setup"] == s08["split"]["setup"] and out[2]["setup"] == s08["setup"]
    assert len({x["seed"] for x in out}) == 3 and all("split" not in x and "anchor" not in x for x in out[1:])
    assert abs(sum(x["seconds"] for x in out) - 11.8) < 1e-3 and out[1]["start"] == round(16.11 + out[0]["seconds"], 4)
    # beat snapping never starves a piece; empty-place and short shots are left alone
    out = T.split([dict(s08, seconds=9.2)], 4.5, snap=lambda t: round(t), lo=1.5)
    assert all(x["seconds"] >= 1.5 for x in out) and len(out) == 3
    assert len(T.split([dict(s08, seconds=4.4)], 4.5)) == 1
    assert len(T.split([{"id": "s10", "mode": "fflf", "chars": [], "start": 30, "seconds": 9}], 4.5)) == 1
    print("ok   split: 11.8 s becomes three shots of ~3.9 s, alternating framings, new seeds")
    # the last piece falls in the instrumental after the last line: a moving shot, not a silent lip-sync
    out = T.split([dict(s08)], 4.5, sung=lambda a, b: a < 23.0)
    assert [x["mode"] for x in out] == ["lipsync", "lipsync", "ff"] and out[2]["setup"] == s08["split_quiet"]["setup"]
    assert "no_lyric" not in out[2] and out[2]["framing"] == "medium"
    print("ok   a wordless piece of a singing slot becomes a moving shot")
    assert {t: S.TONES[t]["split_seconds"] for t in S.TONES} == {"upbeat": 4.5, "builds": 7.0, "mellow": 10.0}

    # song takes: the one that sings the sheet AND runs long enough wins over a clearer short one (Nov 21: 26.5 s of 40)
    from nightshift import pipeline as PL
    rows = [{"file": "a", "lyric_coverage": 1.0, "clarity": .95, "seconds": 26.6},
            {"file": "b", "lyric_coverage": 1.0, "clarity": .91, "seconds": 23.7},
            {"file": "c", "lyric_coverage": .964, "clarity": .92, "seconds": 34.3}]
    assert [r["file"] for r in sorted(rows, key=PL.song_rank(40))] == ["c", "a", "b"]
    assert [r["file"] for r in sorted(rows, key=PL.song_rank(None))] == ["a", "b", "c"]
    assert sorted(rows + [{"file": "d", "lyric_coverage": .7, "clarity": .99, "seconds": 40}], key=PL.song_rank(40))[0]["file"] == "c"
    print("ok   song takes: long enough and fully sung first, then coverage, then clarity")
    print("timeline ok")


if __name__ == "__main__":
    main()
