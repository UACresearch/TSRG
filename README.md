# TSRG — Tourism-aware Spatial Reasoning and Geometry

**R20 release candidate (research code; not an official Puffin release).**

TSRG investigates tourism-domain camera geometry prediction using [Puffin](https://github.com/KangLiao929/Puffin) as the foundation model and [GeoCalib](https://github.com/cvg/GeoCalib) for selected pseudo-reference labels. This archive documents the *frozen* R20 evaluation protocol and provides independently authored, CPU-testable geometry conversion, routing and evaluation utilities. It **does not** contain Puffin model weights, LoRA weights, copyrighted tourism photographs, original manifests, or the formal R20 output data.

> **Status:** release candidate prepared from the project's saved R20 script. Do not describe this archive as an end-to-end independently reproduced model: a full Kaggle reproduction requires the original external data, checkpoints, prior R18/R19 artifacts and permissions. Do not rerun R20 to select, adjust or re-rank models after its one-time test reveal.

## What is frozen in R20

- Test set: 239 images from 16 test locations (four per tourism category), kept separate from development/model selection.
- M2-PAR chooses the R19 M1-v4 pitch specialist for `event` and `heritage`; M0 predicts pitch for `natural` and `purpose_built`.
- Roll and square-view vertical FoV (`square-vFoV`) are copied from M0 for every image.
- Reference pitch uses an audited GeoCalib pseudo-label when `status == 'ok'`, pitch is finite, and pitch uncertainty is at most 3.0 degrees. These pseudo-labels are *not* a physical ground-truth claim.
- The protocol checks a pre-existing 234/526 primary-training pitch supervision mask before test evaluation. One-time test exposure and no post-reveal adjustment are essential.

The core routing implementation is in [`tsrg/routing.py`](tsrg/routing.py); independent conversion and paired location-bootstrap utilities are in [`tsrg/camera.py`](tsrg/camera.py) and [`tsrg/evaluation.py`](tsrg/evaluation.py). The complete saved **R20 source script** is archived at [`reproduction/r20_saved_source_exact.txt`](reproduction/r20_saved_source_exact.txt), with its original bytes and hash preserved. A separate [`syntax-repaired copy`](reproduction/r20_syntax_repaired_UNVERIFIED.py) fixes **one apparent bracket omission in the saved transcription** but has not been run on Kaggle; neither is a standalone demo. The script imports Puffin modules and references project artifacts.

## Quick checks (no GPU or private data needed)

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

This validates our general-purpose code only. It does not measure the released model's accuracy or redo test239. To perform a historical audit, compare the archived script hash in [`reproduction/SOURCE_SHA256.txt`](reproduction/SOURCE_SHA256.txt), check the upstream source licenses and inspect the original persisted `R20_protocol.json`, `R20_final_verdict.json`, predictions and SHA256 manifest in the project's Kaggle dataset. These output files are not bundled here.

## Camera target schema

The historical source text once encoded *original-image horizontal FoV (radians)*; Puffin's center-square evaluation uses *square-view vertical FoV*. The conversion is

`vfov_square = 2 * atan(min(width, height) / width * tan(hfov_original / 2))`

with conversion from radians to degrees for the square-vFoV supervision target. Do not train using the old hFoV string as though it were official square-vFoV. See [`docs/TARGET_SCHEMA.md`](docs/TARGET_SCHEMA.md).

## Licensing, data and reproducibility

This is an independent research adaptation and is **not affiliated with or endorsed by the Puffin authors**. Puffin is licensed under the **S-Lab License 1.0** with a non-commercial restriction. This project does not relicense Puffin or any other third-party dependency. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and [`LICENSE`](LICENSE) for precise file scope and release checks. Review rights to the archived historical script, model adapters, image metadata and all coauthor contributions before publishing.

No new R20 test-set tuning is intended. M3 work, if any, needs separate location-disjoint development validation and a new independent test for a new formal generalization claim.

## Upstream citation

Kang Liao and colleagues, *Thinking with Camera: A Unified Multimodal Model for Camera-Centric Understanding and Generation*, ICLR 2026, arXiv:2510.08673. Please also cite the GeoCalib authors and their work when using its method or outputs.

## Release readiness

This draft includes the archived original R20 evaluation source and independent testing utilities, but **not** the historical training notebooks, complete data, trained models or authoritative numerical output artifacts. Add those only after source integrity, attribution and distribution rights have been checked. Do not fill missing benchmark tables using remembered or approximated numbers.
