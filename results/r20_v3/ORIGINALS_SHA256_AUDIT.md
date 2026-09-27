# Original R20 V3 file-integrity audit

Source: user-uploaded file `tourism-puffin-r20-one-time-batch1-r11-v3.zip` (72,213 bytes). Its SHA256 was computed from the supplied ZIP bytes: `0b7c2f35c9bdc2b21dadb0228d43ea3f7107d95a46c3bf1367a7dd092b1faf3e`. ZIP CRC integrity test passed. Its 10 entries are stored byte-identically at `results/r20_v3/originals/`; Git blob hashes were checked against independently computed hashes of the original archive bytes.

The original `R20_V3_sha256_manifest.json` contains checksums for all **nine other** dataset files. All nine match. It does not list/checksum itself; the SHA256 for the manifest is computed separately below.

| Original Kaggle filename | Bytes | SHA256 from supplied ZIP |
|---|---:|---|
| [`M0_predictions.csv`](originals/M0_predictions.csv) | 100868 | `48c32971b4fe454fa0465a3e1c0d0bf6599630ba87fa64b3ec0abc30fb4d88d8` |
| [`M0_status.json`](originals/M0_status.json) | 293 | `210d03138ea0852747c919597eba2a8baf75fe68a280600e5fe84ba2200df0cd` |
| [`R19_predictions.csv`](originals/R19_predictions.csv) | 51728 | `e1023171dc9ad33c2212a50ee972fbee7d4ba7e4790b14a1a7f4a3a941e0abdc` |
| [`R19_status.json`](originals/R19_status.json) | 294 | `3832be2edb1408921255316ee4df1d2a80d4285d9307d94a7a9d2e323ad213de` |
| [`R20_V3_category_summary.csv`](originals/R20_V3_category_summary.csv) | 317 | `00789f36e7e124958a074d94534e938376f36ac21490287ef6faa5f62ec5e4f0` |
| [`R20_V3_final_predictions_reference.csv`](originals/R20_V3_final_predictions_reference.csv) | 55071 | `2630a168dc759d4c9d8529433d05c42bd88d583c8e177cdd01d2356428028616` |
| [`R20_V3_final_verdict.json`](originals/R20_V3_final_verdict.json) | 1293 | `2f37e84775589b1af67a5bbef0829c1514da7f857a7ffc183fa6f1ec776122c9` |
| [`R20_V3_protocol.json`](originals/R20_V3_protocol.json) | 1914 | `fb6207c53df6ea00084e5ef04f43d203babacd64de09bf8f96c05a1aa16f855e` |
| [`R20_V3_sha256_manifest.json`](originals/R20_V3_sha256_manifest.json) | 862 | `32db22f629d33e3030805b55b258029852ffeeffbf9a88232d39faf7c466db9a` |
| [`R20_V3_summary.csv`](originals/R20_V3_summary.csv) | 897 | `fa8e97599b100399f2fdd2b8b9070c506605e5a91230f5e33ce0ccf46180f859` |

The actual source `R20_V3_final_verdict.json` matches the verdict object printed in the saved execution console log. Its protocol signature equals the original `R20_V3_protocol.json` signature. The original `R20_V3_final_predictions_reference.csv` contains 239 data rows, of which 84 are quality-qualified; the four category summary counts sum to 84.

**Scope limitation:** This verifies the user-supplied ZIP against its embedded original manifest and validates Git upload bytes. It is not a fresh independent fetch from live Kaggle. The upload does not assert copyright clearance for changing this repository from Private to Public, and it does not reproduce model inference.
