"""End-to-end test without a GPU: a fake ComfyUI folder, a synthetic song, placeholder stills and clips.

    python -m pytest tests/        or        python tests/test_offline.py

Covers: workflow maps, project init, song jobs, timeline resolve, job building for every mode, takes, assembly, review copy,
finish. ComfyUI itself is not called (see tests/smoke_comfy.py for that).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from nightshift import workflows as W
from nightshift.project import init


def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def make_env():
    tmp = tempfile.mkdtemp(prefix="ns_test_")
    comfy = os.path.join(tmp, "ComfyUI")
    for d in ("input", "output", "user"):
        os.makedirs(os.path.join(comfy, d))
    root = os.path.join(comfy, "output", "nightshift", "demo")
    p = init(root, "demo", comfy_dir=comfy)
    return tmp, comfy, p


def fake_song(p, seconds=40):
    """Kick on every beat at 120 bpm under a tone, so librosa finds beats."""
    song = p.path("songs", "take_101_00001_.mp3")
    ff("-f", "lavfi", "-i", f"sine=frequency=220:duration={seconds}", "-f", "lavfi",
       "-i", f"aevalsrc='0.9*sin(2*PI*60*t)*exp(-30*mod(t,0.5))':d={seconds}", "-filter_complex", "amix=inputs=2", song)
    return song


def fake_words(p):
    """Pretend transcript: every lyric line sung in order, one word every 0.4 s, 2 s between lines."""
    from nightshift.lyrics import sheet_lines, align
    lines = sheet_lines(open(p.path("song", "lyrics.txt")).read())
    words, t = [], 1.0
    for l in lines:
        for w in l.split():
            words.append({"word": w, "start": round(t, 2), "end": round(t + 0.35, 2), "p": 0.9})
            t += 0.4
        t += 0.6
    p.save("song/words.json", {"words": words})
    p.save("song/lines.json", {"lines": align(lines, words)})
    return t


def test_all():
    tmp, comfy, p = make_env()
    try:
        # workflows
        for name in W.available():
            assert not W.Workflow.load(name).check(), name
        assert p.renders_in_place and p.output_subdir == "nightshift/demo"

        # song jobs
        from nightshift import song
        jobs = song.build_jobs(p, [7, 8])
        j = json.load(open(jobs[0]))
        assert j["37:38"]["inputs"]["seed"] == 7 and "Tell me what you're chasing" in j["37:13"]["inputs"]["lyrics"]
        assert j["35"]["inputs"]["filename_prefix"] == "nightshift/demo/songs/take_7"
        assert "<!--" not in j["37:13"]["inputs"]["caption"]

        # song + analysis
        src = fake_song(p, 40)
        song.choose(p, src)
        from nightshift.beatmap import beatmap
        bm = beatmap(p.path("song", "song.mp3"), p.path("song", "beatmap.json"))
        assert 100 < bm["tempo_bpm_detected"] < 140, bm["tempo_bpm_detected"]
        fake_words(p)

        # timeline
        from nightshift import timeline
        print(timeline.resolve(p))
        rs = {s["id"]: s for s in p.shots("shots_resolved.json")}
        assert rs["s02"].get("t") is not None and rs["s02"]["audio"].startswith("nightshift/demo/")
        assert all((s["frames"] - 1) % 8 == 0 for s in rs.values())
        assert os.path.exists(os.path.join(comfy, "input", "nightshift", "demo", "song.mp3"))

        # stills
        from nightshift import build
        r = build.build(p, "stills")
        assert r["written"], r
        sj = json.load(open(p.path("jobs", "s02_still.json")))
        assert sj["1366"]["inputs"]["value"].startswith("woman in her late twenties")
        assert sj["1363"]["inputs"]["filename_prefix"] == "nightshift/demo/stills/s02_flux"
        assert sj["ns_negative_concat"]["inputs"]["string_b"].startswith("blonde hair")
        assert sj["1362:1327"]["inputs"]["source"] == ["ns_negative_concat", 0]
        assert sj["1362:1314"]["inputs"]["value"] is False and sj["1362:1317"]["inputs"]["value"] == 1280   # landscape 1280x768
        assert sj["1362:1312"]["inputs"]["value"] == rs["s02"]["seed"] and sj["1362:1313"]["inputs"]["value"] is True

        # fake renders of stills + sheets
        # character sheets: jobs for the first world from the description, the second world as an outfit edit of the first
        from nightshift import sheets
        assert sheets.worlds(p) == {"lead": ["real", "stage"]}, sheets.worlds(p)
        assert sheets.source(p, "lead") == "text"
        sj1 = json.load(open(sheets.build(p, "lead", "real", 2)[1]))
        assert sj1["1375"]["inputs"]["value"].startswith("The character is woman in her late twenties")
        assert "charcoal crew-neck sweater, dark green wide-leg trousers, white canvas sneakers" in sj1["1375"]["inputs"]["value"]
        assert sj1["1312:791"]["inputs"]["value"] == 7001 + 1000 and sj1["9"]["inputs"]["filename_prefix"] == "nightshift/demo/sheets/lead_real_c1"
        assert "blonde hair" in sj1["1368"]["inputs"]["value"]
        os.makedirs(p.path("refs"), exist_ok=True)
        for f in ("lead_real.png", "lead_stage.png"):
            ff("-f", "lavfi", "-i", "color=c=gray:s=1024x768", "-frames:v", "1", p.path("refs", f))
        assert sheets.pick(p, "lead", "real", p.path("refs", "lead_real.png")) == "refs/sheets/lead_real.png"
        oj = json.load(open(sheets.build(p, "lead", "stage", 1, primary=p.path("refs/sheets/lead_real.png"))[0]))
        assert "plain white crew-neck sweater, black wide-leg trousers" in oj["92:113"]["inputs"]["text"]
        assert oj["76"]["inputs"]["image"] == oj["81"]["inputs"]["image"] == "nightshift/demo/sheet_lead_primary.png"
        sheets.pick(p, "lead", "stage", p.path("refs", "lead_stage.png"))
        assert all(r["sheet"] for r in sheets.status(p))
        for s in rs.values():
            for lab in ("flux", "edit"):
                ff("-f", "lavfi", "-i", "testsrc2=s=1280x768", "-frames:v", "1", p.path("stills", f"{s['id']}_{lab}_00001_.png"))

        r = build.build(p, "sheetedits")
        assert "jobs/s02_edit.json" in r["written"], r
        ej = json.load(open(p.path("jobs", "s02_edit.json")))
        assert ej["76"]["inputs"]["image"] == "nightshift/demo/s02_flux.png" and ej["81"]["inputs"]["image"] == "nightshift/demo/lead_real.png"
        assert "film character sheet" in ej["92:113"]["inputs"]["text"]
        vs = build.variants(p, ["s06"], "AC", 2)
        assert len(vs) == 4 and json.load(open(p.path(vs[3])))["94"]["inputs"]["filename_prefix"].endswith("s06_vC1")

        # videos
        r = build.build(p, "videos")
        assert not r["skipped"], r
        lj = json.load(open(p.path("jobs", "s02_video.json")))
        assert lj["60"]["inputs"]["start_time"] == rs["s02"]["audio_start"]
        assert '"Every light on the avenue' in lj["36"]["inputs"]["text"] and "{lead}" not in lj["36"]["inputs"]["text"]
        assert "straight black shoulder-length hair" in lj["36"]["inputs"]["text"]
        assert lj["47"]["inputs"]["filename_prefix"] == "nightshift/demo/clips/s02_lipsync_edit"
        fj = json.load(open(p.path("jobs", "s08_video.json")))
        # s01 is too short in this 40 s song and gets dropped, so the loop shot ends on the first live shot's still
        assert rs["s01"].get("dropped") and fj["5052"]["inputs"]["image"] == fj["5075"]["inputs"]["image"] == "nightshift/demo/s02_edit.png"
        assert rs["s02"]["start"] == 0.0
        assert isinstance(fj["5110"]["inputs"]["Xi"], int) and fj["5258"]["inputs"]["switch"] is True
        tj = json.load(open(p.path("jobs", "s04_video.json")))
        assert tj["7"]["inputs"]["width"] == 1280 and tj["10"]["inputs"]["value"] == rs["s04"]["frames"]
        fj = json.load(open(p.path("jobs", "s03_video.json")))
        assert fj["257:255"]["inputs"]["length"] == fj["257:254"]["inputs"]["frames_number"] == rs["s03"]["frames"]
        assert fj["257:228"]["inputs"]["noise_seed"] == fj["257:218"]["inputs"]["noise_seed"] + 1

        # takes
        from nightshift import takes
        tk = takes.takes(p, "jobs/s06_video.json", 3)
        t2 = json.load(open(p.path(tk[2])))
        assert t2["32"]["inputs"]["noise_seed"] == rs["s06"]["seed"] + 2000
        assert t2["47"]["inputs"]["filename_prefix"].endswith("s06_lipsync_edit_t2")

        # fake clips -> cut -> review -> finish
        live = [s for s in rs.values() if not s.get("dropped")]
        for s in live:
            n = s["frames"]
            ff("-f", "lavfi", "-i", f"testsrc2=s=1280x768:r=24", "-frames:v", str(n), "-pix_fmt", "yuv420p", p.path("clips", f"{s['id']}_x_00001.mp4"))
        print(timeline.fill(p))
        from nightshift.assemble import assemble
        res = assemble(p.path("cut.json"), p.path("out", "pass01_cut.mp4"))
        print(res)
        from nightshift.assemble import duration
        assert abs(duration(p.path("out", "pass01_cut.mp4")) - 40) < 0.3
        # change one shot: only it re-encodes
        timeline.pick(p, "s03", "clips/s03_x_00001.mp4", **{"in": 0.5})
        res2 = assemble(p.path("cut.json"), p.path("out", "pass01_cut.mp4"), on_event=lambda m: print("  ", m))
        from nightshift import review, finish
        review.numbered(p.path("out", "pass01_cut.mp4"), p.path("out", "pass01_cut_edl.csv"), p.path("review", "pass01_numbered.mp4"), parts=2)
        ht = finish.make_halftone(p.path("overlay", "halftone.png"))
        finish.finish(p.path("out", "pass01_cut.mp4"), p.path("out", "pass01.mp4"), halftone=ht, chunk_s=15)
        assert abs(duration(p.path("out", "pass01.mp4")) - 40) < 0.3
        print("ok", tmp)
        return tmp, p
    except Exception:
        print("left test folder for inspection:", tmp)
        raise


if __name__ == "__main__":
    test_all()
