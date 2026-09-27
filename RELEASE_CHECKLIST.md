# Before clicking GitHub Publish

- [ ] Confirm names, author order, institution and coauthors' consent; update the project author/citation fields.
- [x] Recover and SHA256-verify the exact executed R18, R19, and R20 V3 source cells from the uploaded 278-cell Kaggle Notebook; R20 V3's saved verdict agrees exactly with the original result JSON.
- [ ] Audit the recovered source code and full historical notebook for third-party redistribution rights before publishing; the earlier archived historical R20 script is a different source artifact.
- [ ] Inspect paths, image/location metadata, repository history and notebook outputs for personal information, tokens or unauthorized private content.
- [ ] Read and include Puffin's latest relevant S-Lab license notice if any Puffin-derived file is being redistributed.
- [ ] Confirm rights for any external result CSV or data manifest before adding it. Raw tourist photographs, original weights, adapters and private caches stay excluded by default.
- [x] Obtain and cross-check the ten original **R20 V3** JSON/CSV files from the user-provided dataset ZIP, including `R20_V3_protocol.json`, `R20_V3_final_verdict.json`, original predictions and SHA256 manifest. The nine manifest-listed files match their original SHA256; see `results/r20_v3/ORIGINALS_SHA256_AUDIT.md`.
- [ ] Before public release, independently review permission to redistribute the original R20 V3 prediction text, image IDs and location metadata, and if possible compare the imported ZIP's checksums with a fresh download from the original Kaggle dataset.
- [x] Obtain and audit the original R19 dataset ZIP and its 23 entries; 14/14 embedded checksum comparisons passed and the frozen Epoch-3 adapter hash matches R20 V3. The 17 original small text entries and all hashes are included in `results/r19/`.
- [ ] Transfer and reverify the six R19 binary checkpoint files to a suitable controlled large-file distribution if necessary, or retain the original Kaggle dataset as their canonical archive; confirm licensing and data rights.
- [ ] Verify the full pipeline against original Kaggle environment if claiming full reproducibility. The CPU tests in this package cover independent utility functions only.
- [ ] Freeze/tag R20. Implement M3 on a separate branch, development folds only, without post-reveal test239 tuning.
- [ ] Decide whether the archived historical R20 script should be publicly distributed or retained privately until permissions are confirmed. If not cleared, remove it and its checksum and say the public version is a method-code release, not a complete R20 code release.
