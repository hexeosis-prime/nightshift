"""Studio's non-agent shot plan (Nov 19): tone picks setups by energy and sets the pace; vertical character shots stop at
medium; hands are named empty; the HUD title is the title field, never the folder name."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nightshift import studio as S


def energy(s):
    return next((b[4] for b in S.BANK.get((s["mode"], s["framing"]), []) if b[0] == s.get("setup")), None)


def main():
    ch = S.character({"noun": "woman", "look": "late twenties, auburn hair", "outfit": "a denim jacket"})
    for seed in range(5):
        mellow = S.shots(["night-avenue"], S.DEFAULT_LYRICS, 6, ch, shot_seed=seed, tone="mellow")["shots"]
        assert all(energy(s) in (None, "calm") for s in mellow), [(s.get("setup"), energy(s)) for s in mellow]
        up = S.shots(["night-avenue"], S.DEFAULT_LYRICS, 10, ch, shot_seed=seed, tone="upbeat")["shots"]
        assert all(energy(s) in (None, "medium", "high") for s in up), [(s.get("setup"), energy(s)) for s in up]
        assert any(energy(s) == "high" for s in up)
        vert = S.shots(["night-avenue"], S.DEFAULT_LYRICS, 8, ch, shot_seed=seed, vertical=True)["shots"]
        assert not [s for s in vert if s.get("chars") and s["framing"] == "wide"], "full-body character wide in 9:16"
    assert all("Nothing in her hands." in s["video"] for s in mellow if s.get("chars") and s["framing"] != "wide")
    assert all("slowly and gently" in s["video"] for s in mellow if s.get("chars"))
    print("ok   tone: mellow draws calm setups, upbeat medium/high; vertical has no full-body character wides")
    assert "75 BPM" in S.caption("night-avenue", "", "woman", 40, tone="mellow")
    assert "120 BPM" in S.caption("night-avenue", "", "woman", 40, tone="upbeat")
    print("ok   tone words in the song brief")
    assert S.overlay_cfg(S.DEFAULT_LYRICS, None, True)["style"]["title"] == ""
    assert S.overlay_cfg(S.DEFAULT_LYRICS, "Night knows", True)["style"]["title"] == "NIGHT KNOWS"
    print("ok   HUD title: empty unless given")
    print("studio ok")


if __name__ == "__main__":
    main()
