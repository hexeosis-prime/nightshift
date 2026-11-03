"""Studio projects with one and three places build every still job for both image models (no ComfyUI needed)."""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
from nightshift import studio, build as B
from nightshift.project import Project


def main():
    for scenes in (["night-avenue"], ["desert-highway", "snow-motel", "living-room"]):
        for model in ("flux3", "flux2"):
            d = tempfile.mkdtemp(); cd = os.path.join(d, "ComfyUI")
            os.makedirs(os.path.join(cd, "input")); os.makedirs(os.path.join(cd, "output"))
            form = {"name": "t", "length": "short", "aspect": "9:16", "image_model": model, "mode": "yolo", "scenes": scenes,
                    "comfy_url": "http://127.0.0.1:1", "comfy_dir": cd, "song": {"source": "generate"},
                    "character": {"noun": "woman", "look": "late twenties, curly red hair", "outfit": "a denim jacket"},
                    "overlay": {"lyrics": True, "hud": False, "color": "contrast"}}
            p = Project(studio.create(os.path.join(cd, "output", "nightshift", "t"), form).root)
            r = B.Builder(p).run("stills")
            assert r["written"] and not r["skipped"], (scenes, model, r)
            print(f"ok {model} {'+'.join(scenes)}: {len(r['written'])} stills")
    print("studio build ok")


if __name__ == "__main__":
    main()
