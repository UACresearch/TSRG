"""Audit original R19 training-source provenance, without copying photographs.

For owner's private Kaggle dataset caolitong/tourism-puffin-geometry-training.
Structural/metadata checks only: these cannot grant or prove legal permission to
redistribute images, their derivatives, or model weights.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
import re

EXPECTED = {"master": 742, "primary": 526, "aux": 216, "manifest": 1425}
SPLITS = {"train": 1018, "validation": 168, "test": 239}
NEEDED_MANIFEST = ("sha1", "split", "file_page", "license", "license_url", "artist", "license_audit", "local_sha256")
NEEDED_AUX = ("id", "source_page", "source_sha1", "artist", "license", "license_url", "source_file", "split")
OUTPUT_FIELDS = ("set", "id", "source_page", "license", "artist", "issue")


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as h:
        rd = csv.DictReader(h)
        fields = rd.fieldnames or []
        data = [{str(k): ("" if v is None else str(v).strip()) for k, v in row.items()}
                for row in rd]
    return fields, data


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as h:
        return [json.loads(line) for line in h if line.strip()]


def kind_of_license(value: str) -> str:
    s = re.sub(r"[-_ ]+", " ", str(value).upper()).strip()
    if re.search(r"\bCC\s*BY\s*NC\b|\bCC\s*BY\s*ND\b", s):
        return "outside_documented_inclusion_list"
    if "CC0" in s or "PUBLIC DOMAIN" in s or s.startswith("PD ") or s == "PD":
        return "public_domain_or_cc0"
    if re.search(r"\bCC\s*BY\s*SA\b", s):
        return "cc_by_sa"
    if re.search(r"\bCC\s*BY\b", s):
        return "cc_by"
    return "requires_manual_review"


def audit(root: Path, output: Path) -> dict:
    manifest_file = root / "metadata" / "trainable_manifest_final.csv"
    combined_file = root / "geometry_training" / "geometry_train_combined.jsonl"
    panorama_file = root / "panorama_truth" / "manifest.csv"
    for p in (manifest_file, combined_file, panorama_file):
        if not p.is_file():
            raise FileNotFoundError(f"Required original source missing: {p}")

    mcols, manifest = read_csv(manifest_file)
    acols, pano = read_csv(panorama_file)
    combined = read_jsonl(combined_file)
    for name, fields, expected in (("main manifest", mcols, NEEDED_MANIFEST),
                                    ("panorama manifest", acols, NEEDED_AUX)):
        missing = set(expected) - set(fields)
        if missing:
            raise ValueError(f"{name}: missing columns: {sorted(missing)}")

    primary = [x for x in combined if x.get("label_provenance") == "geocalib_pseudo_parameter_filtered"]
    aux = [x for x in combined if x.get("label_provenance") == "projection_truth"]
    counts = {"manifest": len(manifest), "master": len(combined),
              "primary": len(primary), "aux": len(aux), "panorama_manifest": len(pano)}
    flags = []

    def issue(group, item_id, page, lic, artist, why):
        flags.append(dict(set=group, id=item_id, source_page=page,
                          license=lic, artist=artist, issue=why))

    for k, n in EXPECTED.items():
        if counts[k] != n:
            issue("global", k, "", "", "", f"expected_count={n}; actual={counts[k]}")
    if counts["panorama_manifest"] != 216:
        issue("global", "panorama_manifest", "", "", "", f"expected_count=216; actual={len(pano)}")

    for group, vals in (("master", [x.get("id", "") for x in combined]),
                        ("master image metadata", [x["sha1"] for x in manifest]),
                        ("panorama", [x["id"] for x in pano])):
        if len(vals) != len(set(vals)):
            issue("global", group, "", "", "", "duplicate_id_or_sha1")

    splits = Counter(x.get("split", "") for x in manifest)
    if dict(splits) != SPLITS:
        issue("global", "manifest_split_counts", "", "", "", f"expected={SPLITS}; actual={dict(splits)}")
    location_sets = {}
    for split in SPLITS:
        location_sets[split] = {x.get("location_id", "") for x in manifest if x.get("split") == split}
    for a, b in (("train", "validation"), ("train", "test"), ("validation", "test")):
        overlap = location_sets[a] & location_sets[b]
        if overlap:
            issue("global", "location_disjoint", "", "", "", f"{a}/{b} overlap: {len(overlap)}")

    index = {x["sha1"]: x for x in manifest}
    primary_matched = 0
    primary_license = Counter()
    primary_audit = Counter()
    primary_resolutions = Counter()
    for x in primary:
        ident = str(x.get("id", ""))
        row = index.get(ident)
        if row is None:
            # The original JSONL IDs are normally image SHA1; report any mismatch
            # rather than silently matching on an unproven alternative key.
            issue("primary", ident, "", "", "", "id_not_found_in_original_manifest_sha1")
            continue
        primary_matched += 1
        page, lic, author = (row.get("file_page", ""), row.get("license", ""), row.get("artist", ""))
        lic_kind = kind_of_license(lic)
        primary_license[lic] += 1
        primary_audit[row.get("license_audit", "")] += 1
        primary_resolutions[row.get("source_resolution_tier", "")] += 1
        if row.get("split") != "train":
            issue("primary", ident, page, lic, author, "manifest_split_not_train")
        if not page.startswith("https://commons.wikimedia.org/wiki/"):
            issue("primary", ident, page, lic, author, "missing_or_unexpected_source_page")
        if lic_kind in ("outside_documented_inclusion_list", "requires_manual_review"):
            issue("primary", ident, page, lic, author, "license_outside_or_unknown_in_original_inclusion_list")
        if lic_kind in ("cc_by", "cc_by_sa") and not author.strip():
            issue("primary", ident, page, lic, author, "attribution_author_missing")
        if lic_kind in ("cc_by", "cc_by_sa") and not row.get("license_url", "").startswith("https://"):
            issue("primary", ident, page, lic, author, "attribution_license_url_missing")
        if not row.get("local_sha256", "").strip():
            issue("primary", ident, page, lic, author, "source_image_sha256_missing")
        if not row.get("license_audit", "").strip():
            issue("primary", ident, page, lic, author, "license_audit_record_missing")

    sources = defaultdict(list)
    for row in pano:
        sources[row.get("source_page", "")].append(row)
    aux_source_summary = []
    for page, rows in sorted(sources.items()):
        sample = rows[0]
        licenses = sorted({r.get("license", "") for r in rows})
        authors = sorted({r.get("artist", "") for r in rows})
        urls = sorted({r.get("license_url", "") for r in rows})
        source_hashes = sorted({r.get("source_sha1", "") for r in rows})
        aux_source_summary.append({"page": page, "rows": len(rows), "licenses": licenses,
                                   "authors": authors, "license_urls": urls,
                                   "distinct_source_sha1": len(source_hashes)})
        lic = sample.get("license", "")
        if not page.startswith("https://commons.wikimedia.org/wiki/"):
            issue("aux_source", "", page, lic, sample.get("artist", ""), "missing_commons_source_page")
        if len(rows) != 108:
            issue("aux_source", "", page, lic, sample.get("artist", ""), f"unexpected_projection_count={len(rows)}")
        if len(licenses) != 1 or len(authors) != 1 or len(urls) != 1 or len(source_hashes) != 1:
            issue("aux_source", "", page, lic, sample.get("artist", ""), "inconsistent_source_metadata")
        if kind_of_license(lic) != "cc_by_sa":
            issue("aux_source", "", page, lic, sample.get("artist", ""), "auxiliary_license_needs_review")
        if not sample.get("artist", "").strip() or not sample.get("license_url", "").startswith("https://"):
            issue("aux_source", "", page, lic, sample.get("artist", ""), "author_or_license_url_missing")
        if {r.get("split", "") for r in rows} != {"train_aux"}:
            issue("aux_source", "", page, lic, sample.get("artist", ""), "unexpected_split")

    if len(sources) != 2:
        issue("global", "aux_source_count", "", "", "", f"expected=2; actual={len(sources)}")
    if len({x.get("id", "") for x in aux}) != len(aux):
        issue("global", "aux_training_ids", "", "", "", "duplicated_training_id")
    pano_ids = {x["id"] for x in pano}
    unmatched_aux = {str(x.get("id", "")) for x in aux} - pano_ids
    if unmatched_aux:
        issue("global", "aux_not_in_panorama_manifest", "", "", "", f"count={len(unmatched_aux)}")
    if len(primary) and primary_matched != len(primary):
        issue("global", "primary_match_coverage", "", "", "", f"matched={primary_matched}/{len(primary)}")

    # Detect the existence and schema of the separate attribution inventory;
    # do not silently assume its key or that its license fields match the master.
    attr_files = list(root.rglob("ATTRIBUTION.csv"))
    attribution = {"file_count": len(attr_files), "files": []}
    if not attr_files:
        issue("global", "ATTRIBUTION.csv", "", "", "", "attribution_inventory_not_found")
    for p in attr_files:
        cols, rows = read_csv(p)
        attribution["files"].append({"path": str(p.relative_to(root)),
                                     "rows": len(rows), "columns": cols})

    summary = {
        "audit_type": "metadata_and_provenance_structural_check_only",
        "redistribution_rights": "not_determined_by_this_script",
        "original_dataset": "caolitong/tourism-puffin-geometry-training",
        "counts": counts,
        "split_counts": dict(splits),
        "locations_per_split": {k: len(v) for k, v in location_sets.items()},
        "primary_manifest_sha1_matches": primary_matched,
        "primary_license_counts": dict(sorted(primary_license.items())),
        "primary_license_audit_counts": dict(sorted(primary_audit.items())),
        "primary_source_resolution_tiers": dict(sorted(primary_resolutions.items())),
        "auxiliary_source_summary": aux_source_summary,
        "attribution_inventory": attribution,
        "flag_count": len(flags),
        "flag_counts_by_issue": dict(sorted(Counter(x["issue"] for x in flags).items())),
        "manual_steps": [
            "Review every flagged record against the actual Wikimedia source page.",
            "Review attribution inventory and all licensing/credit terms for intended publication.",
            "Confirm R19 LoRA redistribution permission with project contributors and applicable upstream terms.",
            "Do not equate metadata screening or zero flags with legal authorization.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "r19_source_rights_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (output / "r19_source_rights_flags.csv").open("w", encoding="utf-8-sig", newline="") as h:
        wr = csv.DictWriter(h, fieldnames=OUTPUT_FIELDS)
        wr.writeheader()
        wr.writerows(flags)
    return summary


def main() -> None:
    p = argparse.ArgumentParser(description="Private R19 original-data provenance metadata audit")
    p.add_argument("--dataset-root", type=Path, default=Path(
        "/kaggle/input/datasets/caolitong/tourism-puffin-geometry-training"))
    p.add_argument("--output-dir", type=Path, default=Path("/kaggle/working/r19_rights_audit"))
    a = p.parse_args()
    result = audit(a.dataset_root, a.output_dir)
    print("R19 source metadata audit complete")
    print("Counts:", result["counts"])
    print("Primary match:", result["primary_manifest_sha1_matches"])
    print("Primary licenses:", result["primary_license_counts"])
    print("Panorama source count:", len(result["auxiliary_source_summary"]))
    print("Attribution inventory:", result["attribution_inventory"]["file_count"])
    print("Flags:", result["flag_count"])
    print("Saved summary:", a.output_dir / "r19_source_rights_summary.json")
    print("Saved flags:", a.output_dir / "r19_source_rights_flags.csv")
    print("IMPORTANT: This is not a declaration of redistribution permission.")


if __name__ == "__main__":
    main()
