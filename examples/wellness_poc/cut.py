"""Edit picked clips into one silent picture (crossfades), then lay a music track under it.
  python3 cut.py picture <out.mp4> <W> <H> clip1[:cut] clip2[:xf] ...   (":cut" = hard cut into this clip, default 0.5 s crossfade)
  python3 cut.py music <picture.mp4> <track> <out.mp4>"""
import json, subprocess, sys

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]))

def picture(out, W, H, specs, xf=0.5):
    # spec: file[:cut][@seconds]  (@ trims the clip to that length)
    trims = [float(s.split("@")[1]) if "@" in s else None for s in specs]
    specs = [s.split("@")[0] for s in specs]
    clips = [s.split(":")[0] for s in specs]
    joins = [(s.split(":")[1] if ":" in s else "xf") for s in specs]
    D = [trims[i] or dur(c) for i, c in enumerate(clips)]
    W, H = int(W), int(H)
    f, ins = [], []
    for i, c in enumerate(clips):
        ins += ["-i", c]
        tr = f"trim=0:{trims[i]},setpts=PTS-STARTPTS," if trims[i] else ""
        f.append(f"[{i}:v]{tr}scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},fps=24,format=yuv420p,setsar=1,settb=1/24[v{i}]")
    cur, t = "v0", D[0]
    for i in range(1, len(clips)):
        o = f"j{i}"
        if joins[i] == "cut":
            f.append(f"[{cur}][v{i}]concat=n=2:v=1:a=0,settb=1/24[{o}]"); t += D[i]
        else:
            f.append(f"[{cur}][v{i}]xfade=transition=fade:duration={xf}:offset={t - xf:.3f}[{o}]"); t += D[i] - xf
        cur = o
    f.append(f"[{cur}]fade=t=in:st=0:d=0.4,fade=t=out:st={t - 0.8:.3f}:d=0.8[out]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", ";".join(f), "-map", "[out]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
    print(out, round(dur(out), 2))

def music(pic, track, out):
    d = dur(pic)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", track, "-map", "0:v", "-map", "1:a",
                    "-af", f"atrim=0:{d},afade=t=in:st=0:d=0.3,afade=t=out:st={d - 1.5}:d=1.5", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out], check=True)
    print(out, round(dur(out), 2))

if __name__ == "__main__":
    a = sys.argv[1:]
    picture(a[1], a[2], a[3], a[4:]) if a[0] == "picture" else music(*a[1:4])
