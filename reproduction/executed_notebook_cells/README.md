# Original Kaggle Notebook source-cell archive — R18 / R19 / R20 V3

These three `.py` files are the exact UTF-8 **source text of three executed code cells** extracted from the user-uploaded `notebook2aa6f4bd81 (1).ipynb` with no header inserted or code edited. They are archival snippets from a larger Notebook, **not independent one-click programs**, and must not be rerun to change the frozen test239 outcome. These source-cell excerpts do not include the other 275 cells inline; the two complete original Notebook snapshots are stored separately in `reproduction/notebooks/notebook2aa6f4bd81_original_snapshots.zip`.

Full source notebook SHA256: `2e4ed571902122423ed626d57d6af7e659f40a7aaf20871142b239595736b929`; 278 total cells.

| File | Notebook cell (0-indexed) | execution_count | Source byte count | Source SHA256 | Saved output evidence |
|---|---:|---:|---:|---|---|
| [R18 freeze](R18_freeze_cell260_EXACT_SOURCE.py) | 260 | 2 | 35849 | `19eb27b73214ae71664e14fb8f555e08fe2a4e2f7b184b7c9be59d3361ae9c1e` | `R18_ALL_REMOTE_SHA256_VERIFIED`, `R18_M2PAR_FREEZE_COMPLETE`; no saved exception. |
| [R19 full training](R19_training_cell261_EXACT_SOURCE.py) | 261 | 1 | 54859 | `aa29de302907c0e7ea1ca89cd8e9c17322becd320797765d6ad986b490521225` | `R19_FINAL_REMOTE_LOCK_VERIFIED`, `R19_FINAL_FULL_DEVELOPMENT_TRAINING_COMPLETE`; no saved exception. |
| [R20 final V3](R20_V3_final_cell276_EXACT_SOURCE.py) | 276 | 26 | 31091 | `d831faa267b4f11c0e71abc2c72b3202b8aa78709f2ec0d4f1ffe2fcfab7bcb9` | Final remote SHA256 verification; original V3 verdict printed; no saved exception. |

The R20 V3 cell's printed final verdict was parsed and compared field-for-field with the original user-uploaded Kaggle `results/r20_v3/originals/R20_V3_final_verdict.json`: **identical**. Original results are at [`results/r20_v3/originals/`](../../results/r20_v3/originals/R20_V3_protocol.json).

Historical earlier attempts and diagnostic cells remain part of the original 278-cell Notebook. Notably, the preceding V2 cell stopped on an implementation-only prompt-length assertion before V3. **R18 freezes the post-hoc pitch-routing rule; R19 trains the frozen LoRA specialist; R20 V3 evaluates it without any training or reuse of Stable101.** The earlier R14 original primary endpoint is still recorded as failed.

There is **no trained adapter weight bundled in this code folder**. The original R19 final Epoch-3 adapter is recorded under Kaggle dataset `caolitong/tourism-puffin-r19-m2par-full-pitch-specialist-v1` with SHA256 `1dc8afa37c4947d30f58e9ae3aa260c76730dd7201a042f98fcbfd97ae0da8b0`. Confirm rights before public release; the project repository remains Private.
