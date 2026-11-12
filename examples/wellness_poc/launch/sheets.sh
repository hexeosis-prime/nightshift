#!/bin/bash
# sheets.sh LOOK SHOT...  -> sheet_<LOOK>_<first-shot>.jpg: per shot, t0 and t1 rows of frames at 0, 1.5, 3, 4.5 s
cd "$(dirname "$0")/out"
L=$1; shift
rows=()
for s in "$@"; do
  for t in 0 1; do
    f=${L}_${s}_t${t}.mp4
    [ -f "$f" ] || continue
    ffmpeg -v error -y -i "$f" -vf "select='eq(n\,0)+eq(n\,36)+eq(n\,72)+eq(n\,108)',scale=320:-1,tile=4x1,drawtext=text='${s} t${t}':x=8:y=8:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6" -frames:v 1 "/tmp/r_${s}_${t}.jpg"
    rows+=("-i" "/tmp/r_${s}_${t}.jpg")
  done
done
n=$(( ${#rows[@]} / 2 ))
ffmpeg -v error -y "${rows[@]}" -filter_complex "vstack=inputs=$n" "../sheet_${L}_$1.jpg" && echo "../sheet_${L}_$1.jpg"
