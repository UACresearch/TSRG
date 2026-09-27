# Run in ONE Kaggle notebook Python cell after Add Input -> dataset:
# caolitong/tourism-puffin-r20-one-time-batch1-r11-v3
# Does not require a local Python installation, GitHub credentials or rerunning test239.
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json

SLUG = "tourism-puffin-r20-one-time-batch1-r11-v3"
SEARCH_ROOTS = [
    Path("/kaggle/input/datasets/caolitong") / SLUG,
    Path("/kaggle/input") / SLUG,
]
roots = [p for p in SEARCH_ROOTS if p.is_dir()]
if not roots:
    raise FileNotFoundError(
        "First select Add Input in this Kaggle notebook and attach "
        "caolitong/" + SLUG + ". No test inference is required."
    )
required = [
    "R20_V3_protocol.json",
    "R20_V3_final_verdict.json",
    "R20_V3_final_predictions_reference.csv",
    "R20_V3_sha256_manifest.json",
]
additional = [
    "R20_V3_summary.csv",
    "R20_V3_category_summary.csv",
    "M0_predictions.csv",
    "M0_status.json",
    "R19_predictions.csv",
    "R19_status.json",
]
folders = []
for root in roots:
    folders.extend(p.parent for p in root.rglob(required[0]) if p.is_file())
folders = sorted(set(folders))
if len(folders) != 1:
    raise RuntimeError(
        "Expected exactly one V3 protocol in the selected dataset; found: "
        + repr([str(p) for p in folders])
    )
folder = folders[0]
missing = [n for n in required if not (folder / n).is_file()]
if missing:
    raise FileNotFoundError("Required original V3 files missing: " + repr(missing))
names = required + [n for n in additional if (folder / n).is_file()]
out = Path("/kaggle/working/TSRG_R20_V3_Kaggle_ORIGINALS.zip")
out.parent.mkdir(parents=True, exist_ok=True)
audit = {"source_dataset": "caolitong/" + SLUG,
         "source_directory": str(folder), "files": {}}
with ZipFile(out, "w", ZIP_DEFLATED) as z:
    for name in names:
        data = (folder / name).read_bytes()
        audit["files"][name] = {
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        z.writestr("originals/" + name, data)
    z.writestr("EXPORT_LOCAL_SHA256_AUDIT.json",
               json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
with ZipFile(out, "r") as z:
    for name in names:
        original = (folder / name).read_bytes()
        assert z.read("originals/" + name) == original
        assert hashlib.sha256(original).hexdigest() == audit["files"][name]["sha256"]
    assert z.testzip() is None
print("EXPORT VERIFIED:", out)
print("ORIGINAL FILE COUNT:", len(names))
print("FILES:", ", ".join(names))
print("Now download the ZIP from the Kaggle Notebook Output files and upload it to this ChatGPT conversation.")
