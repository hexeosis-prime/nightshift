"""Going back to the song (Phase 2): the chosen song goes aside and its checkpoint asks again; the same song again keeps
everything, another one sets aside what was timed to the old one (analysis, timeline, every clip). Nothing is deleted."""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nightshift import director as D
from nightshift import song as SONG
from nightshift.project import init


def main():
    tmp = tempfile.mkdtemp(prefix="ns_back_")
    try:
        p = init(os.path.join(tmp, "demo"), "demo")
        os.makedirs(p.path("songs"), exist_ok=True)
        for k, body in (("101", b"song one"), ("202", b"song two")):
            open(p.path("songs", f"take_{k}_00001_.mp3"), "wb").write(body)
        SONG.choose(p, "songs/take_101_00001_.mp3")
        os.makedirs(p.path("clips"), exist_ok=True)
        for f in ("song/lines.json", "song/words.json", "song/beatmap.json", "shots_resolved.json", "cut.json",
                  "clips/s02_lipsync_vC0_00001_.mp4", "clips/s08b_lipsync_vC0_00001_.mp4"):
            open(p.path(f), "w").write("{}")
        st = {"pass": 2, "approved": []}
        msgs = []

        D.reopen(p, st, "song_pick")
        try:
            SONG.song_path(p)
            raise AssertionError("the song should be out of play")
        except FileNotFoundError:
            pass
        assert os.path.exists(p.path(st["reopened"]["song"])), st
        SONG.choose(p, "songs/take_101_00001_.mp3")                 # the same one again
        assert D.settle_song(p, st, msgs.append) is False and "same song" in msgs[-1]
        assert os.path.exists(p.path("song", "lines.json")) and os.path.exists(p.path("clips", "s02_lipsync_vC0_00001_.mp4"))
        print("ok   back to the song, the same one again: everything kept")

        D.reopen(p, st, "song_pick")
        SONG.choose(p, "songs/take_202_00001_.mp3")                 # another one
        assert D.settle_song(p, st, msgs.append) is True and "a new song" in msgs[-1], msgs
        for f in ("song/lines.json", "song/words.json", "song/beatmap.json", "shots_resolved.json", "cut.json"):
            assert not os.path.exists(p.path(f)), f
        assert not os.listdir(p.path("clips")) or os.listdir(p.path("clips")) == ["_aside"], os.listdir(p.path("clips"))
        assert sorted(os.listdir(p.path("clips", "_aside"))) == ["s02_lipsync_vC0_00001_.mp4", "s08b_lipsync_vC0_00001_.mp4"]
        assert os.path.exists(p.path("song", "_aside", "pass02", "lines.json"))
        assert open(SONG.song_path(p), "rb").read() == b"song two"
        print("ok   back to the song, another one: its timing and clips set aside, nothing deleted")
        print("back ok")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
