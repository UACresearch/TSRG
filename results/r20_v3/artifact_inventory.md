# Original R20 V3 Kaggle artifact inventory

The saved log identifies these original Kaggle files and reports `REMOTE_SHA256_VERIFIED` for them. The user-provided dataset ZIP now supplies all ten files; each has been copied unchanged to [`originals/`](originals/R20_V3_protocol.json). All nine files named by the embedded original SHA256 manifest pass checksum validation; the manifest's own SHA256 is listed in [`ORIGINALS_SHA256_AUDIT.md`](ORIGINALS_SHA256_AUDIT.md).

| Kaggle file | Evidence |
|---|---|
| `R20_V3_protocol.json` | Pre-reveal frozen protocol, signature `469d53cb01b21869002a814c4420c5b9c3ac78ed5e505f5335ecf70f4b19111b` |
| `M0_predictions.csv` | 239 frozen parsed base predictions |
| `M0_status.json` | M0 status |
| `R19_predictions.csv` | 121 specialist predictions |
| `R19_status.json` | R19 status |
| `R20_V3_summary.csv` | Outcome summary |
| `R20_V3_final_verdict.json` | Formal original verdict |
| `R20_V3_final_predictions_reference.csv` | Full predictions/reference output |
| `R20_V3_category_summary.csv` | Full category results |
| `R20_V3_sha256_manifest.json` | Checksums of original remote artifacts |

Source dataset URL: https://www.kaggle.com/datasets/caolitong/tourism-puffin-r20-one-time-batch1-r11-v3

This private GitHub repository now includes both the saved console log/log-derived excerpts and the ten original source files from the uploaded Kaggle dataset ZIP. The originals remain distinguished by their unmodified filenames in `results/r20_v3/originals/`.
