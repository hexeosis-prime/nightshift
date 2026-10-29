"""ComfyUI API workflows addressed by role instead of node id.

Every workflow in workflows/ is a ComfyUI API-format export (<name>.json) plus a map (<name>.map.json) that names
the inputs Nightshift fills in:

    {"kind": "ff",
     "roles":   {"image":  {"node": "149", "input": "image"},
                 "seed":   [{"node": "257:218", "input": "noise_seed"}, {"node": "257:228", "input": "noise_seed", "offset": 1}],
                 "frames": [{"node": "257:255", "input": "length"}, {"node": "257:254", "input": "frames_number"}]},
     "outputs": {"video": {"node": "75", "input": "filename_prefix"}},
     "defaults": [{"node": "5258", "input": "switch", "value": true}]}

A role is one target or a list of targets (all get the value). "offset" adds to numeric values (seeds),
"type" casts (int / float / str). A role may instead be a text concat hook:
    "negative": {"concat_from": ["152:549", 0], "into": [{"node": "1026:1031", "input": "source"}]}
which makes append("negative", text) splice a StringConcatenate node into the graph.

No map? Title nodes in ComfyUI "ns:<role>" (for example "ns:prompt", "ns:seed", "ns:output:video") and the role
is found by title. Swapping in your own workflow = export it in API format, drop it in workflows/ (or a project's
workflows/ folder), and write its map or title its nodes.
"""
import copy
import json
import re
import os

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_WORKFLOWS = os.path.abspath(os.path.join(PKG_DIR, "..", "workflows"))
TITLE_INPUTS = ("text", "value", "prompts", "image", "audio", "seed", "noise_seed", "filename_prefix", "caption", "switch")


class WorkflowError(Exception):
    pass


def search_dirs(extra=()):
    dirs = [d for d in extra if d] + [os.environ.get("NIGHTSHIFT_WORKFLOWS", ""), REPO_WORKFLOWS]
    return [d for d in dirs if d and os.path.isdir(d)]


def find(name, extra_dirs=()):
    base = name[:-5] if name.endswith(".json") else name
    for d in search_dirs(extra_dirs):
        p = os.path.join(d, base + ".json")
        if os.path.exists(p):
            return p
    raise WorkflowError(f"workflow '{name}' not found in {search_dirs(extra_dirs)}")


def available(extra_dirs=()):
    out = {}
    for d in reversed(search_dirs(extra_dirs)):
        for f in sorted(os.listdir(d)):
            if f.endswith(".json") and not f.endswith(".map.json") and not f.endswith(".meta.json"):
                out[f[:-5]] = os.path.join(d, f)
    return out


def flux3_refs(text):
    """Reference names for FLUX 3 edits: "[reference_image2]" / "image 2" -> "<ref_image_1>" (FLUX 3 counts from 0)."""
    text = re.sub(r"\[reference_image(\d)\]", lambda m: f"<ref_image_{int(m.group(1)) - 1}>", text)
    return re.sub(r"\b[Ii]mage (\d)\b", lambda m: f"<ref_image_{int(m.group(1)) - 1}>", text)


class Workflow:
    def __init__(self, name, graph, spec, path=None):
        self.name, self.graph, self.spec, self.path = name, graph, spec or {}, path
        self.kind = self.spec.get("kind")

    @classmethod
    def load(cls, name, extra_dirs=()):
        path = find(name, extra_dirs)
        graph = json.load(open(path, encoding="utf-8"))
        if "nodes" in graph and "links" in graph:
            raise WorkflowError(f"{path} is a UI workflow; export it with 'Export (API)' in ComfyUI")
        mp = path[:-5] + ".map.json"
        spec = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
        wf = cls(os.path.basename(path)[:-5], graph, spec, path)
        wf._titles()
        return wf

    def copy(self):
        return Workflow(self.name, copy.deepcopy(self.graph), self.spec, self.path)

    # ---- role lookup -------------------------------------------------------------------------------
    def _titles(self):
        """Merge "ns:<role>" node titles into the role table (the map file wins)."""
        roles = self.spec.setdefault("roles", {})
        outs = self.spec.setdefault("outputs", {})
        for nid, node in self.graph.items():
            title = (node.get("_meta") or {}).get("title", "")
            if not title.lower().startswith("ns:"):
                continue
            role = title[3:].strip()
            inp = next((k for k in TITLE_INPUTS if k in node.get("inputs", {})), None)
            if not inp:
                continue
            if role.startswith("output"):
                outs.setdefault(role.split(":", 1)[1] if ":" in role else "main", {"node": nid, "input": "filename_prefix"})
            else:
                roles.setdefault(role, {"node": nid, "input": inp})

    def roles(self):
        return sorted(self.spec.get("roles", {}))

    def outputs(self):
        return list(self.spec.get("outputs", {}))

    def has(self, role):
        return role in self.spec.get("roles", {})

    def _targets(self, role):
        spec = self.spec.get("roles", {}).get(role)
        if spec is None:
            raise WorkflowError(f"{self.name}: no role '{role}' (has {self.roles()})")
        return spec if isinstance(spec, list) else [spec]

    def _node(self, nid):
        if nid not in self.graph:
            raise WorkflowError(f"{self.name}: node {nid} is missing (map out of date?)")
        return self.graph[nid]

    # ---- setters -------------------------------------------------------------------------------
    @staticmethod
    def _cast(v, t):
        return {"int": lambda x: int(round(float(x))), "float": float, "str": str, "bool": bool}.get(t, lambda x: x)(v)

    def set(self, role, value, required=True):
        if role == "prompt" and isinstance(value, str) and self.spec.get("ref_syntax") == "flux3":
            value = flux3_refs(value)
        if not self.has(role):
            if required:
                raise WorkflowError(f"{self.name}: no role '{role}'")
            return False
        for t in self._targets(role):
            if "concat_from" in t:
                raise WorkflowError(f"{self.name}: role '{role}' is a concat hook, use append()")
            v = value
            if t.get("offset") and isinstance(v, (int, float)) and not isinstance(v, bool):
                v = v + t["offset"]
            self._node(t["node"])["inputs"][t["input"]] = self._cast(v, t.get("type"))
        return True

    def try_set(self, role, value):
        return self.set(role, value, required=False)

    def get(self, role):
        t = self._targets(role)[0]
        return self._node(t["node"])["inputs"].get(t["input"])

    def append(self, role, text, sep=""):
        """Add text to a prompt input (negative lists, lighting notes). Works on plain inputs and concat hooks."""
        if not text or not self.has(role):
            return False
        for t in self._targets(role):
            if "concat_from" in t:
                nid = f"ns_{role}_concat"
                self.graph[nid] = {"class_type": "StringConcatenate", "_meta": {"title": f"nightshift: {role} + extra"},
                                   "inputs": {"string_a": list(t["concat_from"]), "string_b": text.lstrip(", "), "delimiter": ", "}}
                for tgt in t["into"]:
                    self._node(tgt["node"])["inputs"][tgt["input"]] = [nid, 0]
            else:
                inputs = self._node(t["node"])["inputs"]
                cur = inputs.get(t["input"], "")
                if isinstance(cur, list):
                    raise WorkflowError(f"{self.name}: {role} is wired from another node; give it a concat hook in the map")
                inputs[t["input"]] = (cur or "") + sep + text
        return True

    def seed(self, base):
        self.set("seed", int(base))

    def output(self, prefix, which=None):
        outs = self.spec.get("outputs", {})
        if not outs:
            raise WorkflowError(f"{self.name}: map has no outputs")
        names = [which] if which else list(outs)
        for n in names:
            t = outs[n]
            p = prefix if len(outs) == 1 or which else f"{prefix}_{n}"
            self._node(t["node"])["inputs"][t["input"]] = p

    def output_prefix(self, which=None):
        outs = self.spec.get("outputs", {})
        t = outs[which] if which else next(iter(outs.values()))
        return self._node(t["node"])["inputs"].get(t["input"])

    def prune_outputs(self, keep):
        """Drop the save nodes of the other outputs so ComfyUI only computes the branch that is used."""
        for n, t in self.spec.get("outputs", {}).items():
            if n != keep:
                self.graph.pop(t["node"], None)

    def apply_defaults(self):
        for d in self.spec.get("defaults", []):
            self._node(d["node"])["inputs"][d["input"]] = d["value"]

    # ---- io -------------------------------------------------------------------------------
    def to_api(self):
        return self.graph

    def save(self, path, meta=None):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.graph, f, indent=1)
        m = {"workflow": self.name, "kind": self.kind, **(meta or {})}
        with open(path[:-5] + ".meta.json", "w", encoding="utf-8") as f:
            json.dump(m, f, indent=1)
        return path

    # ---- checks -------------------------------------------------------------------------------
    def check(self):
        """Every mapped node/input exists. Returns a list of problems (empty = fine)."""
        bad = []
        for role in self.roles():
            for t in self._targets(role):
                if "concat_from" in t:
                    if t["concat_from"][0] not in self.graph:
                        bad.append(f"{role}: concat source {t['concat_from'][0]} missing")
                    for tgt in t["into"]:
                        if tgt["node"] not in self.graph:
                            bad.append(f"{role}: node {tgt['node']} missing")
                    continue
                n = self.graph.get(t["node"])
                if n is None:
                    bad.append(f"{role}: node {t['node']} missing")
                elif t["input"] not in n.get("inputs", {}):
                    bad.append(f"{role}: node {t['node']} ({n['class_type']}) has no input '{t['input']}'")
        for n, t in self.spec.get("outputs", {}).items():
            if t["node"] not in self.graph:
                bad.append(f"output {n}: node {t['node']} missing")
        for d in self.spec.get("defaults", []):
            if d["node"] not in self.graph:
                bad.append(f"default: node {d['node']} missing")
        return bad

    def models(self):
        """Model files the graph loads (for the install checklist)."""
        out = set()
        for node in self.graph.values():
            for v in node.get("inputs", {}).values():
                if isinstance(v, str) and v.lower().endswith((".safetensors", ".gguf", ".ckpt", ".pth", ".onnx", ".bin", ".pt")):
                    out.add((node["class_type"], v))
                if isinstance(v, dict) and v.get("lora"):
                    out.add((node["class_type"], v["lora"]))
        return sorted(out)

    def node_classes(self):
        return sorted({n["class_type"] for n in self.graph.values()})


def load_job_meta(job_path):
    mp = job_path[:-5] + ".meta.json"
    return json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}


def job_workflow(job_path, extra_dirs=()):
    """Re-open a built job with its workflow's map, so takes/variants can re-seed it by role."""
    meta = load_job_meta(job_path)
    if not meta.get("workflow"):
        raise WorkflowError(f"{job_path}: no .meta.json next to it; build jobs with nightshift so they carry their workflow name")
    wf = Workflow.load(meta["workflow"], extra_dirs)
    wf.graph = json.load(open(job_path, encoding="utf-8"))
    return wf, meta
