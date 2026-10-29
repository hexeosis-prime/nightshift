"""Beat map for a song: tempo, beats, downbeats (4/4 assumed), sections, energy, loop-seam check."""
import json

import numpy as np


def beatmap(src, dst, prompted_bpm=None):
    import librosa
    y, sr = librosa.load(src, sr=22050, mono=True)
    dur = len(y) / sr
    hop = 512

    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr, hop_length=hop, units="frames")
    tempo = float(np.atleast_1d(tempo)[0])
    beat_t = librosa.frames_to_time(beats, sr=sr, hop_length=hop)

    # Downbeats: the beat phase (0-3) whose beats carry the most low-end onset energy.
    S = np.abs(librosa.stft(y, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr)
    low = librosa.onset.onset_strength(S=librosa.amplitude_to_db(S[freqs < 200]), sr=sr, hop_length=hop)
    scores = [float(np.mean(low[beats[p::4]])) if len(beats[p::4]) else 0 for p in range(4)]
    phase = int(np.argmax(scores))
    down_t = beat_t[phase::4]

    # Sections: agglomerative segmentation on beat-synced chroma + MFCC, snapped to downbeats.
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop, n_mfcc=13)
    feat = np.vstack([librosa.util.normalize(chroma, axis=1), librosa.util.normalize(mfcc, axis=1)])
    sync = librosa.util.sync(feat, beats, aggregate=np.median)
    k = int(np.clip(round(dur / 25), 4, 10))
    bounds = librosa.segment.agglomerative(sync, k)
    bound_t = sorted(set([0.0] + [float(beat_t[min(b, len(beat_t) - 1)]) for b in bounds if b > 0]))
    if len(down_t):
        bound_t = sorted(set([0.0] + [float(down_t[np.argmin(np.abs(down_t - t))]) for t in bound_t[1:]]))

    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rms_t = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    sections = []
    edges = bound_t + [dur]
    for i in range(len(edges) - 1):
        a, b = edges[i], edges[i + 1]
        m = (rms_t >= a) & (rms_t < b)
        sections.append({"start": round(a, 3), "end": round(b, 3), "seconds": round(b - a, 2),
                         "energy": round(float(np.mean(rms[m])) if m.any() else 0.0, 4)})
    emax = max(s["energy"] for s in sections) or 1
    for s in sections:
        s["energy_rel"] = round(s["energy"] / emax, 2)

    # Loop seam: how similar the last 4 s are to the first 4 s (chroma cosine, 1 = identical harmony).
    n = int(4 * sr / hop)
    c = librosa.util.normalize(chroma, axis=0)
    head, tail = c[:, :n].mean(axis=1), c[:, -n:].mean(axis=1)
    seam = float(np.dot(head, tail) / (np.linalg.norm(head) * np.linalg.norm(tail) + 1e-9))

    nz = np.where(rms > 0.02 * rms.max())[0]
    lead, trail = (float(rms_t[nz[0]]), float(dur - rms_t[nz[-1]])) if len(nz) else (0.0, 0.0)

    out = {
        "file": str(src).replace("\\", "/").split("/")[-1],
        "duration_s": round(dur, 3),
        "tempo_bpm_detected": round(tempo, 2),
        "tempo_bpm_prompted": prompted_bpm,
        "beat_seconds": round(60 / tempo, 4) if tempo else None,
        "shot_lengths_at_tempo": {"2_bars_s": round(8 * 60 / tempo, 3), "4_bars_s": round(16 * 60 / tempo, 3)} if tempo else None,
        "beats": [round(float(t), 3) for t in beat_t],
        "downbeats": [round(float(t), 3) for t in down_t],
        "sections": sections,
        "loop_seam_chroma_similarity": round(seam, 3),
        "leading_silence_s": round(lead, 2),
        "trailing_silence_s": round(trail, 2),
        "notes": "Downbeats assume 4/4. Sections are automatic boundaries, not labels; check by ear.",
    }
    with open(dst, "w") as f:
        json.dump(out, f, indent=1)
    return out
