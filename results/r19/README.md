# R19 full-development pitch-specialist artifact archive

This folder records the original user-supplied Kaggle dataset ZIP `tourism-puffin-r19-m2par-full-pitch-specialist-v1.zip`, SHA256 `674f53da5fdf65901f81cdaea80d2d18b4c3db16462e7c21fa1386c17db6d3b6`. ZIP CRC validation passed and it contains 23 regular file entries (79,139,123 total uncompressed bytes). Original archive: https://www.kaggle.com/datasets/caolitong/tourism-puffin-r19-m2par-full-pitch-specialist-v1

## What this private GitHub folder actually contains

- [`originals/`](originals/R19_protocol.json) stores the **17 original small text entries** from that ZIP, with unchanged paths and bytes, including `R19_protocol.json`, `R19_final_model_lock.json`, `R19_critical_sha256.json`, the three epoch summaries/configs and checksum lists, `train_history.csv`, and the original model-card placeholders.
- [`ORIGINAL_R19_SHA256.json`](ORIGINAL_R19_SHA256.json) gives the size and SHA256 for every one of the 23 source ZIP entries, including the six binary files.
- The **six binary files (three adapters and three optimizer-resume .pt files)** remain in the exact original Kaggle ZIP; they are **not currently present on GitHub** because the linked GitHub file upload cannot reliably transfer the multi-megabyte binary payload. See [`BINARY_ARTIFACTS.md`](BINARY_ARTIFACTS.md). The ZIP uploaded by the project owner is our source for this audit, not a reconstructed model.
- The original executed R19 source cell is archived separately at [`reproduction/executed_notebook_cells/R19_training_cell261_EXACT_SOURCE.py`](../../reproduction/executed_notebook_cells/R19_training_cell261_EXACT_SOURCE.py).

## Integrity checks

The original `R19_critical_sha256.json` contains five critical-entry digests and each matches the source ZIP; the three epoch-specific `sha256.json` files contain three digests each, with 9/9 matching. The total is **14/14**. The original `R19_final_model_lock.json` points to Epoch 3 adapter SHA256 `1dc8afa37c4947d30f58e9ae3aa260c76730dd7201a042f98fcbfd97ae0da8b0`, which matches both the actual source adapter and the R20 V3 protocol reference. It also agrees with the R19 protocol signature `f83708c4201d3af5e02b2b4623f4723799f3dcdaa6230111473173e5028013f7`. Checksum matches audit the submitted dataset; they do not independently fetch live Kaggle.

## Frozen training configuration and recorded outcome

The recorded R19 run used 526 primary + 216 auxiliary training rows (742 total), three epochs, frozen Puffin-Base projector/RADIO features, and Qwen q/k/v/o LoRA (rank 8, alpha 16, dropout 0.05). Training history has 47 optimizer steps in each epoch, with weighted CE 1.712793, 1.350010, and 1.037182 respectively. Epoch 3 was **prelocked**, not selected after calculating development MAE. `R19_final_model_lock.json` records `Stable101_used=false` and `test239_used=false`; R20 V3 is a separate downstream evaluation. The `qwen_lora/README.md` files are automatically generated PEFT template model cards with placeholders; their content is archived faithfully but is not a complete project-specific model card.

## Distribution and use

Repository remains Private. The original `adapter_config.json` contains a Kaggle-local base-model path, so the unmodified adapter is not an independent standalone checkpoint; point it to the properly licensed foundation model when setting up a separate deployment. Do not deserialize untrusted `optimizer_resume.pt` files. Check model, data, and third-party license permissions before any public distribution. No test239 tuning or rerun is authorized by this archive.
