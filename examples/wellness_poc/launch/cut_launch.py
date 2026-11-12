"""Cut the two launch demos from the picked takes.  python3 cut_launch.py A|B   (picks in PICKS below)
Picture: 1920x1080, H.264. Music: the look's MiniMax track, faded. End line on the last shot. Then an email-size copy."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
OUT, CUT = os.path.join(HERE, "out"), os.path.join(HERE, "cut")
FONT = "/usr/share/fonts/truetype/lato/Lato-Medium.ttf"
LINE = "A wellness center in your pocket."
# shot, take, seconds used, join into this shot ("cut" = straight cut, "xf" = dissolve)
PICKS = {
    "A": [("s1_push_in", 1, 5.04, None), ("s2_cave", 0, 3.0, "cut"), ("s3_yoga", 0, 3.5, "cut"),
          ("s4_session", 0, 3.0, "cut"), ("s5_connect", 1, 3.5, "cut"), ("s6_retreat", 0, 3.5, "cut"),
          ("s7_pull_out", 0, 5.04, "xf"), ("s8_end", 1, 3.5, "cut")],
    # B: the push-in eases out as it lands and the cave shot eases in, so the join pauses. Cut on motion instead:
    # end the push-in while it still moves (4.0 s), start the cave shot after its ease-in (0.6 s).
    "B": [("s1_push_in", 0, 4.0, None), ("s2_cave", 1, 4.5, "cut", 0.6), ("s3_yoga", 1, 4.5, "xf"),
          ("s4_session", 1, 4.5, "xf"), ("s5_connect", 0, 4.5, "xf"), ("s6_retreat", 0, 4.5, "xf"),
          ("s7_pull_out", 0, 5.04, "xf"), ("s8_end", 0, 4.5, "cut")],
}
XF = {"A": 0.35, "B": 0.75}
# the filmic retreat still came out letterboxed (FLUX drew cinema bars): crop them off those shots
LETTERBOX = {("B", "s6_retreat"): "crop=1280:604:0:62,", ("B", "s7_pull_out"): "crop=1280:604:0:62,"}
GRADE = {"A": "", "B": ""}


def run(cmd):
    subprocess.run(cmd, check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))


def cut(look, picks=None):
    picks = picks or PICKS[look]
    os.makedirs(CUT, exist_ok=True)
    ins, f, xf = [], [], XF[look]
    for i, pick in enumerate(picks):
        shot, take, secs = pick[:3]
        start = pick[4] if len(pick) > 4 else 0      # optional: skip the first seconds (cut on motion)
        ins += ["-ss", str(start), "-i", os.path.join(OUT, f"{look}_{shot}_t{take}.mp4")]
        lb = LETTERBOX.get((look, shot), "")
        f.append(f"[{i}:v]trim=0:{secs},setpts=PTS-STARTPTS,{lb}scale=1920:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=1920:1080,fps=24,"
                 f"format=yuv420p,setsar=1,settb=1/24[v{i}]")
    cur, t = "v0", picks[0][2]
    for i in range(1, len(picks)):
        o, join, secs = f"j{i}", picks[i][3], picks[i][2]
        if join == "xf":
            f.append(f"[{cur}][v{i}]xfade=transition=fade:duration={xf}:offset={t - xf:.3f}[{o}]"); t += secs - xf
        else:
            f.append(f"[{cur}][v{i}]concat=n=2:v=1:a=0,settb=1/24[{o}]"); t += secs
        cur = o
    last = picks[-1][2]
    txt = (f"drawtext=fontfile={FONT}:text='{LINE}':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=h*0.86:"
           f"shadowcolor=black@0.75:shadowx=3:shadowy=3:alpha='if(lt(t,{t - last + 0.4}),0,min(1,(t-{t - last + 0.4})/0.6))'")
    f.append(f"[{cur}]{txt},fade=t=in:st=0:d=0.3,fade=t=out:st={t - 0.7:.3f}:d=0.7[out]")
    tag = os.environ.get("CUT_TAG", "")
    pic = os.path.join(CUT, f"launch_{look}{tag}_picture.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(f), "-map", "[out]", "-c:v", "libx264",
         "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", pic])
    d = dur(pic)
    music = [os.path.join(OUT, x) for x in os.listdir(OUT) if x.startswith(f"{look}_music")][0]
    full = os.path.join(CUT, f"launch_{look}{tag}.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", music, "-map", "0:v", "-map", "1:a",
         "-af", f"atrim=0:{d},afade=t=in:st=0:d=0.2,afade=t=out:st={d - 2}:d=2,alimiter=limit=0.89",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", full])
    small = os.path.join(CUT, f"launch_{look}{tag}_email.mp4")
    rate = int(8.5 * 8 * 1000 / d) - 128      # about 8.5 MB, so both looks fit one email
    for p in (1, 2):
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", full, "-c:v", "libx264", "-preset", "medium", "-b:v", f"{rate}k",
             "-pass", str(p), "-passlogfile", f"/tmp/launch_{look}"] +
            (["-an", "-f", "mp4", "/dev/null"] if p == 1 else ["-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", small]))
    print(full, round(d, 2), "s;", small, round(os.path.getsize(small) / 1e6, 1), "MB")


if __name__ == "__main__":
    cut(sys.argv[1])
