# R20 V3 final one-time evaluation — evidence archive

This folder records the **executed R20 V3 test239 evaluation**, separate from the historical R20 working script under `reproduction/`.

## Source of files

The user supplied the original dataset ZIP `tourism-puffin-r20-one-time-batch1-r11-v3.zip`. Its 10 original entries were added **byte-for-byte**, under their original names in [`originals/`](originals/R20_V3_protocol.json), without rewriting metadata, rounding numerical values, or modifying line endings. The supplied original `R20_V3_sha256_manifest.json` lists nine other files and all nine SHA256 checksums matched. The checksum of the supplied ZIP, every file SHA256 and the manifest's scope are recorded in [`ORIGINALS_SHA256_AUDIT.md`](ORIGINALS_SHA256_AUDIT.md). The Kaggle console log previously recorded remote checksum verification; this GitHub transfer verifies the submitted ZIP against its embedded manifest, and does **not** independently re-download from the current Kaggle API.

- `originals/R20_V3_protocol.json`, `originals/R20_V3_final_verdict.json`, `originals/R20_V3_final_predictions_reference.csv`, `originals/R20_V3_sha256_manifest.json` are the original files as supplied.
- `originals/` also contains the original M0 and R19 prediction/status files, category summary and summary CSV.
- `executed_console_log_exact.md` is a byte-identical copy of the saved console log; SHA256 `f2a6d3eb48685f0c52f165e6e1b5a2fed5f1b5dc34a24467ce2694aa79f7a4d3`.
- `verdict_extracted_from_console.json` and `category_results_extracted_from_console.csv` are **older log-derived excerpts**, retained for provenance and not a replacement for the full original files.
- `artifact_inventory.md` lists the originals. The earlier historical script in `reproduction/` is **not verified as the exact executed V3 notebook**.

Source Kaggle dataset: https://www.kaggle.com/datasets/caolitong/tourism-puffin-r20-one-time-batch1-r11-v3

## Results and interpretation

The original result reports 239 test images from 16 locations; 84 pitch-quality-qualified examples at 15 locations for the paired endpoint. M0 pitch MAE was 1.1041807334510654° and M2-PAR pitch MAE was 1.084518827231383°, a descriptive 1.780678255291592% relative MAE decrease. The location-cluster bootstrap (10,000 draws) 95% interval for M2-PAR minus M0 is [−0.06167604083244341°, 0.02339181905185608°]: **the interval contains zero**, so this does not establish a statistically significant overall advantage. Four frozen procedural checks passed under their recorded criteria. The original final verdict explicitly calls this a **post-hoc R18 pitch-only test** and notes that the original R14 primary endpoint remains FAILED. No training or Stable101 reuse occurred in V3, and post-reveal tuning is not allowed.

The exact executed V3 protocol signature is `469d53cb01b21869002a814c4420c5b9c3ac78ed5e505f5335ecf70f4b19111b`.

## Distribution scope

This remains a **private research archive**. The prediction files include image IDs, destination/location category identifiers, and model output text; assess data rights and whether test output may be public before changing visibility. Model weights, LoRA adapters, underlying tourism photos, protected test imagery, original training data, and the exact executed notebook source are not included.
