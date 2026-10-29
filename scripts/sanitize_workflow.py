"""Blank out personal defaults in an API workflow before sharing it: file names in LoadImage / LoadAudio nodes and save
prefixes. Prompts are left alone (read them yourself). Usage: python scripts/sanitize_workflow.py workflows/*.json"""
import json
import sys

for path in sys.argv[1:]:
    if path.endswith((".map.json", ".meta.json")):
        continue
    d = json.load(open(path, encoding="utf-8"))
    n = 0
    for node in d.values():
        ins = node.get("inputs", {})
        for k, v in list(ins.items()):
            if not isinstance(v, str):
                continue
            if k == "image" and v.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                ins[k] = "example.png"; n += 1
            elif k == "audio" and v.lower().endswith((".mp3", ".wav", ".flac")):
                ins[k] = "example.mp3"; n += 1
            elif k == "filename_prefix":
                ins[k] = "nightshift/example"; n += 1
    json.dump(d, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"{path}: {n} field(s) reset")
