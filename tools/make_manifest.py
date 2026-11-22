"""Writes data/MANIFEST.json: SHA-256 and size of every data file the experiments read. Run only when data changes."""
import hashlib, json, os
out = {}
for root in ("data/raw", "data/processed"):
    for f in sorted(os.listdir(root)):
        p = f"{root}/{f}"
        out[p] = dict(sha256=hashlib.sha256(open(p, "rb").read()).hexdigest(), bytes=os.path.getsize(p))
json.dump(out, open("data/MANIFEST.json", "w"), indent=1)
print(len(out), "files")
