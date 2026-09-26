# R20 V3 final one-time evaluation — evidence archive

This folder records the **executed R20 V3** test239 evaluation evidence. It is separate from the earlier historical R20 script in `/reproduction`.

## Provenance and file scope

- `executed_console_log_exact.md` is a byte-identical copy of the saved Kaggle console log from the research archive. It includes the complete visible execution trace and final verdict. Its original SHA256 is `f2a6d3eb48685f0c52f165e6e1b5a2fed5f1b5dc34a24467ce2694aa79f7a4d3` (39,508 bytes); Git blob SHA1 is `0ddee7625caefb19acfc5234116b6bc188b32bf5`.
- `verdict_extracted_from_console.json` is a verbatim JSON object extracted from the saved log, **not** the original Kaggle `R20_V3_final_verdict.json` file.
- `category_results_extracted_from_console.csv` transcribes only the printed four-category table (six-decimal display precision), **not** the original Kaggle `R20_V3_category_summary.csv`.
- `artifact_inventory.md` records the original Kaggle dataset and its file names, as visible in the log.

Original Kaggle artifact location: `caolitong/tourism-puffin-r20-one-time-batch1-r11-v3` (access and original file bytes are not provided by this GitHub repository). The log reports remote SHA256 verification of those Kaggle files; those remote originals have **not** been independently downloaded or compared against GitHub extracts in this archival upload. The original full execution code/notebook was also not present among the available saved files, so do not identify the older R20 script as the exact V3 execution script.

## Results and interpretation

The test covered 239 images from 16 locations. The pitch quality policy selected 84 examples at 15 locations for the paired endpoint. M0 pitch MAE was 1.1041807334510654° and M2-PAR pitch MAE was 1.084518827231383°, a descriptive 1.780678255291592% relative MAE decrease. Location-cluster bootstrap (10,000 draws) gave a 95% interval of [−0.06167604083244341°, 0.02339181905185608°] for M2-PAR minus M0: **the interval contains zero**, so this does not establish a statistically significant overall advantage. The four frozen procedural checks passed according to the saved log. This is a **post-hoc pitch-only endpoint after R18**; the log explicitly says the earlier R14 original primary endpoint remains FAILED. There was no training or Stable101 reuse in V3, and no post-reveal tuning is permitted.

The source record uses a strict corrected R11 prompt; its protocol signature is `469d53cb01b21869002a814c4420c5b9c3ac78ed5e505f5335ecf70f4b19111b`. The previously archived `docs/R20_PROTOCOL.md` is historical and should be read with this V3 evidence archive, not substituted for it.

## Exclusions

No Puffin/GeoCalib weights, LoRA adapters, original tourism photographs, raw predictions, source dataset manifests, protected test examples, original Kaggle protocol JSON or original remote checksum manifest are redistributed here. The saved console log and derivative transcription must be reviewed for authorship, third-party rights and data-disclosure scope **before making this private repository public**.
