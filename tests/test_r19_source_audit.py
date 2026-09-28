"""Small synthetic tests; never need the original private photos or source CSVs."""
import csv
import json
from pathlib import Path

import pytest

from tools.audit_r19_training_sources import audit, kind_of_license


@pytest.mark.parametrize(("value", "expected"), [
    ("CC BY 4.0", "cc_by"),
    ("CC-BY-SA 3.0", "cc_by_sa"),
    ("CC BY-SA 4.0", "cc_by_sa"),
    ("CC0 1.0", "public_domain_or_cc0"),
    ("Public domain", "public_domain_or_cc0"),
    ("PD-old", "public_domain_or_cc0"),
    ("CC BY-NC-SA 4.0", "outside_documented_inclusion_list"),
    ("CC BY-ND 4.0", "outside_documented_inclusion_list"),
    ("unknown", "requires_manual_review"),
])
def test_license_label_classifier(value, expected):
    assert kind_of_license(value) == expected


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def test_minimal_fixture_surfaces_expected_count_flags_and_matches_source(tmp_path):
    root = tmp_path / "data"
    mfields = ("sha1", "split", "location_id", "file_page", "license",
               "license_url", "artist", "license_audit", "local_sha256")
    write_csv(root / "metadata/trainable_manifest_final.csv", mfields, [
        {"sha1": "a" * 40, "split": "train", "location_id": "site_A",
         "file_page": "https://commons.wikimedia.org/wiki/File:A.jpg",
         "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
         "artist": "Author", "license_audit": "pass", "local_sha256": "1" * 64},
    ])
    pfields = ("id", "source_page", "source_sha1", "artist", "license",
               "license_url", "source_file", "split")
    write_csv(root / "panorama_truth/manifest.csv", pfields, [
        {"id": "aux1", "source_page": "https://commons.wikimedia.org/wiki/File:Pan.jpg",
         "source_sha1": "z" * 40, "artist": "Author", "license": "CC BY-SA 3.0",
         "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
         "source_file": "pano.jpg", "split": "train_aux"},
    ])
    f = root / "geometry_training/geometry_train_combined.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("\n".join(json.dumps(x) for x in [
        {"id": "a" * 40, "label_provenance": "geocalib_pseudo_parameter_filtered"},
        {"id": "aux1", "label_provenance": "projection_truth"},
    ]) + "\n", encoding="utf-8")
    write_csv(root / "ATTRIBUTION.csv", ["sha1", "artist"], [{"sha1": "a" * 40, "artist": "Author"}])
    result = audit(root, tmp_path / "out")
    assert result["primary_manifest_sha1_matches"] == 1
    assert result["primary_license_counts"] == {"CC BY 4.0": 1}
    assert result["attribution_inventory"]["file_count"] == 1
    assert result["redistribution_rights"] == "not_determined_by_this_script"
    assert result["flag_count"] > 0  # small fixture intentionally differs from 1425/742
    assert (tmp_path / "out/r19_source_rights_flags.csv").is_file()


def test_missing_dataset_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        audit(tmp_path / "absent", tmp_path / "out")
