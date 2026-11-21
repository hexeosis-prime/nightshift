"""Resolve a song-agnostic shot list against the chosen song.

Every shot gets a slot in the edit and is rendered at exactly that length (no freeze frames, no wasted frames).
  - A shot with "anchor": "<first words of a lyric line>" starts just before that line is sung ("lead" seconds earlier
    if the singer needs a run-up), using the line times in song/lines.json. Anchors are matched in order with a small dynamic program, so a repeated chorus
    line lands on the right repetition.
  - Shots between two anchors share the gap (lip-sync shots weigh 2, others 1); cut points snap to nearby beats.
  - Slots under min_seconds are dropped (their time goes to the neighbour). Every clip renders its whole slot, up to
    render_max_seconds (12 s), so a long gap in the song doesn't end on a frozen frame.
  - Lip-sync and first/last-frame shots get the song as audio from their slot start, and the words sung in the slot.
  - "voice" shots (e.g. a rapper) fall back to "fallback_mode" when the chosen song has no such voice
    (project.json "song_voices").
"""
import glob
import json
import math
import os
import re

norm = lambda t: re.sub(r"[^a-z0-9']", "", t.lower())


def frames_for(sec, fps=24):
    """LTX wants 8n+1 frames; render at least the slot (minimum 9)."""
    n = math.ceil(sec * fps - 1e-6)
    return 8 * math.ceil(max(n - 1, 8) / 8) + 1


SPLIT_MODES = ("lipsync", "ff")


def split(shots, most, snap=lambda t: t, lo=1.0, sung=None):
    """A character shot whose slot is longer than `most` seconds becomes several shots of about equal length (cuts on
    beats), each a render of its own: s08, s08b, s08c. The pieces after the first take the shot's "split" fields (the
    other framing and a setup of its own, written by Studio), alternating with the original, so a long held line plays as
    close, medium, close instead of one 12-second take (Nov 20 upbeat run). Shots without "split" repeat themselves with
    a new seed. sung(t0, t1): whether any word is sung in that span; a lip-sync piece with no words (the instrumental after
    the last line) becomes a moving shot from the shot's "split_quiet" fields, when it has them."""
    out = []
    for s in shots:
        out.append(s)
        n = int(-(-s.get("seconds", 0) // most)) if not s.get("dropped") else 1
        if s["mode"] not in SPLIT_MODES or not s.get("chars") or n < 2:
            continue
        t0, t1 = s["start"], s["start"] + s["seconds"]
        cuts = [t0]
        for k in range(1, n):
            c = snap(t0 + (t1 - t0) * k / n)
            cuts.append(c if c - cuts[-1] >= lo and t1 - c >= lo else t0 + (t1 - t0) * k / n)
        cuts.append(t1)
        s["seconds"] = round(cuts[1] - cuts[0], 4)
        alt, quiet = s.get("split") or {}, s.get("split_quiet")
        for k in range(1, n):
            piece = {kk: v for kk, v in s.items() if kk not in ("split", "split_quiet", "anchor", "anchor_note", "lead")}
            if k % 2 == 1:
                piece.update(alt)
            if s["mode"] == "lipsync" and quiet and sung and not sung(cuts[k], cuts[k + 1]):
                piece.update(quiet, mode="ff")
                piece.pop("no_lyric", None)
            piece.update(id=f"{s['id']}{'bcdefgh'[k - 1]}", part_of=s["id"], start=round(cuts[k], 4),
                         seconds=round(cuts[k + 1] - cuts[k], 4), seed=int(s.get("seed", 0)) + 7919 * k)
            out.append(piece)
    return out


def resolve(project, shots_name="shots.json", out_shots="shots_resolved.json", out_cut="cut.json", song_input=None):
    from .song import song_path
    fps = project.cfg["fps"]
    tl = project.cfg["timeline"]
    shots = project.shots(shots_name)
    words = project.load("song/words.json")["words"]
    bm = project.load("song/beatmap.json")
    beats, end = bm["beats"], bm["duration_s"]
    voices = project.cfg.get("song_voices")
    song = song_path(project)
    song_in = song_input or project.stage_input(song)   # the name ComfyUI's audio loaders use
    nw = [norm(w["word"]) for w in words]

    # Anchors match the lyric sheet's lines as timed by the analysis (song/lines.json): the sheet's words are exact, so a
    # line whose first words the recogniser missed still anchors, and "Every light is ..." can't land on "Every road is
    # ..." (Nov 19, video-6: two of three anchors went to the wrong lines and four shots were squeezed out). Without
    # timed lines, the heard words are matched as before.
    lines = [l for l in (project.load("song/lines.json", {"lines": []}) or {}).get("lines", []) if l.get("text")]
    lw = [[norm(x) for x in l["text"].split()] for l in lines]

    def cands(a):
        key = [norm(x) for x in a.split()][:3]
        if lines:
            return [i for i, ws in enumerate(lw) if ws[:len(key)] == key[:len(ws)] and key]
        need = len(key) - (1 if len(key) >= 3 else 0)
        return [i for i in range(len(nw) - len(key) + 1)
                if nw[i] == key[0] and sum(nw[i + j] == key[j] for j in range(len(key))) >= need]

    def when(i):
        return lines[i]["start"] if lines else words[i]["start"]

    todo = []
    for s in shots:
        for k in ("t", "start", "seconds", "frames", "dropped", "warn", "anchor_note", "lyric", "audio", "audio_start"):
            s.pop(k, None)
        if s.get("voice") and voices is not None and s["voice"] not in voices:
            s["mode"] = s.get("fallback_mode", "ff")
            s["anchor_note"] = f"no {s['voice']} voice in this song"
            continue
        if s.get("anchor"):
            todo.append((s, cands(s["anchor"])))
    # ordered alignment: increasing word positions matching as many anchors as possible
    states = {-1: (0, [])}
    for s, cs in todo:
        new_states = dict(states)
        for last, (cnt, path) in states.items():
            for i in cs:
                if i > last and (i not in new_states or new_states[i][0] < cnt + 1):
                    new_states[i] = (cnt + 1, path + [(s, i)])
        states = new_states
    best = max(states.values(), key=lambda v: (v[0], -sum(i for _, i in v[1])))
    chosen = {id(s): i for s, i in best[1]}
    for s, cs in todo:
        if id(s) in chosen:
            s["t"] = max(0.0, when(chosen[id(s)]) - s.get("lead", 0.0) - 0.15)
            if lines and lines[chosen[id(s)]].get("end"):
                s["_line_end"] = lines[chosen[id(s)]]["end"]      # a singing shot is given its whole line when it fits
        else:
            s["anchor_note"] = "anchor not found" if not cs else "anchor out of order, unanchored"
    last = -1
    for s in shots:
        if "t" in s:
            if s["t"] <= last + tl["min_seconds"]:
                s.pop("t")
                s["anchor_note"] = "anchor too close to the previous one, unanchored"
            else:
                last = s["t"]
    idx = [i for i, s in enumerate(shots) if "t" in s]
    bounds = [(0, 0.0)] + [(i, shots[i]["t"]) for i in idx] + [(len(shots), end)]

    def snap(t):
        if not beats:
            return t
        b = min(beats, key=lambda x: abs(x - t))
        return b if abs(b - t) < tl["snap"] else t

    lo = tl["min_seconds"]
    for (i0, t0), (i1, t1) in zip(bounds, bounds[1:]):
        run = shots[i0:i1]
        if not run:
            continue
        # every shot first gets the shortest slot it can live with, then the rest is shared (lip-sync shots twice as
        # much): the Nov 20 upbeat run dropped two shots squeezed to 1.0 and 1.3 s by plain 2:1 shares
        w = [2 if s["mode"] == "lipsync" else 1 for s in run]
        mins = [lo * 1.1] * len(run)
        if run[0].get("_line_end") and "t" in run[0]:
            mins[0] = max(mins[0], run[0]["_line_end"] + 0.2 - t0)      # the singer finishes the line on camera
        fits = sum(mins) <= (t1 - t0)
        if not fits:
            mins = [0.0] * len(run)                         # too tight for everyone: plain shares, the shortest drop out
        spare, tot = (t1 - t0) - sum(mins), sum(w)
        t, acc, base = t0, 0, t0
        for k, (s, wi) in enumerate(zip(run, w)):
            acc += wi
            base += mins[k]
            raw = base + spare * acc / tot
            nxt = t1 if k == len(run) - 1 else snap(raw)
            if fits and (nxt - t < mins[k] or t1 - nxt < sum(mins[k + 1:])):
                nxt = raw                                    # a beat snap that would starve a shot: keep the exact cut
            s["start"], s["seconds"] = round(t, 4), round(nxt - t, 4)
            t = nxt

    cap = lambda s: tl["max_fit_seconds"] if s.get("fit") else tl["max_seconds"]
    for s in shots:
        if s["seconds"] < tl["min_seconds"]:
            s["dropped"] = True
        if s["seconds"] > cap(s):
            s["warn"] = f"slot {s['seconds']:.1f}s is over the {cap(s)}s cap"
    live = [s for s in shots if not s.get("dropped")]
    if live and live[0]["start"] > 0:          # a dropped opening shot: its time goes to the first live shot
        live[0]["seconds"] = round(live[0]["seconds"] + live[0]["start"], 4)
        live[0]["start"] = 0.0
    for a, b in zip(live, live[1:]):
        a["seconds"] = round(b["start"] - a["start"], 4)
    if live:
        live[-1]["seconds"] = round(end - live[-1]["start"], 4)
    for s in shots:
        s.pop("_line_end", None)
    if tl.get("split_seconds"):
        shots = split(shots, tl["split_seconds"], snap, lo,
                      sung=lambda a, b: any(a - 0.1 <= w["start"] < b - 0.3 for w in words))
        live = [s for s in shots if not s.get("dropped")]
    # Render every shot at its full slot so nothing freezes: the caps above only steer how time is shared; a clip may run to
    # render_max_seconds (LTX 2.3 holds up well to 12 s and beyond). Only a slot longer than that holds its last frame.
    hard = lambda s: max(cap(s), tl.get("render_max_seconds", 12.0))
    for s in shots:
        if s["seconds"] > hard(s):
            s["warn"] = f"slot {s['seconds']:.1f}s is over the {hard(s)}s render limit: the last frame holds"
        elif s.get("warn"):
            s.pop("warn")
        s["frames"] = frames_for(min(s["seconds"], hard(s)) + 0.05, fps)
        if s["mode"] in ("lipsync", "fflf"):
            s["audio"], s["audio_start"] = song_in, round(s["start"], 3)
            s["lyric"] = " ".join(w["word"] for w in words if s["start"] - 0.1 <= w["start"] < s["start"] + s["seconds"] - 0.1).strip()
    project.save(out_shots, {"note": f"resolved from {shots_name} against {project.rel(song)}", "shots": shots})

    old = {c["id"]: c for c in project.load(out_cut, {"shots": []})["shots"]}
    cut = {"note": "generated by nightshift timeline; edit freely (src, beats, seconds, in, speed)",
           "song": project.rel(song), "beatmap": "song/beatmap.json", "fps": fps,
           "work_size": project.cfg["work_size"], "crop": project.cfg["crop"], "crop_y": None,
           "final_size": project.cfg["final_size"], "start": 0.0, "until": round(end, 3),
           "shots": [{"id": s["id"], "src": (old.get(s["id"]) or {}).get("src", s.get("src", "")), "seconds": s["seconds"]} for s in live]}
    if cut["shots"]:
        cut["shots"][-1].pop("seconds")
    project.save(out_cut, cut)
    rows = []
    for s in shots:
        rows.append(f'{s["id"]:6} {s["mode"]:8} {s["start"]:7.2f} {s["seconds"]:6.2f}s {s["frames"]:4}f '
                    f'{"DROP " if s.get("dropped") else ""}{s.get("anchor_note", "")} {s.get("warn", "")} {s.get("lyric", "")[:50]}')
    rows.append(f"live shots {len(live)}, render seconds {round(sum(s['frames'] for s in live if s['mode'] != 'reuse') / fps, 1)}")
    return "\n".join(rows)


def fill(project, cut_name="cut.json", only_empty=True):
    """Point each cut entry at the newest rendered clip for its shot."""
    cut = project.load(cut_name)
    missing = []
    for s in cut["shots"]:
        if s.get("src") and only_empty:
            continue
        hits = project.renders("clips", f'{s["id"]}_*.mp4')
        if not hits:
            missing.append(s["id"])
            continue
        s["src"] = project.rel(hits[-1])
    project.save(cut_name, cut)
    return {"filled": len(cut["shots"]) - len(missing), "missing": missing}


def pick(project, sid, src, cut_name="cut.json", **fields):
    """Use a specific take for a shot (and optionally set in / speed / beats / seconds)."""
    cut = project.load(cut_name)
    for s in cut["shots"]:
        if s["id"] == sid:
            s["src"] = project.rel(src) if os.path.isabs(src) else src
            s["picked"] = True     # a human (or agent) choice: auto-ranking leaves it alone from now on
            for k, v in fields.items():
                if v is None:
                    s.pop(k, None)
                else:
                    s[k] = v
            project.save(cut_name, cut)
            project.log("pick", shot=sid, src=s["src"], **fields)
            return s
    raise KeyError(f"no shot {sid} in {cut_name}")
