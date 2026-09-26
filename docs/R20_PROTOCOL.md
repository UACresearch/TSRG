# Historical R20 evaluation protocol

*This is a summary of the preserved historical source. It must not be revised based on observed test239 results.*

- Design: M0 baseline vs frozen M2-PAR, 239 test images, 16 locations, four locations for each of event / heritage / natural / purpose_built.
- Precommitted routing: `event, heritage` receive R19 M1-v4 specialist **pitch**; all other pitch, and all roll and square-vFoV, come from M0.
- Specialist epoch: R19 epoch 3. Required archived adapter SHA256: `1dc8afa37c4947d30f58e9ae3aa260c76730dd7201a042f98fcbfd97ae0da8b0`.
- R19 protocol signature: `f83708c4201d3af5e02b2b4623f4723799f3dcdaa6230111473173e5028013f7`.
- Reference: GeoCalib pitch if status `ok`, pitch finite and uncertainty ≤ 3 degrees. Before using it on test239, the reconstruction reproduces the already-used training pitch reference mask, 234 of 526 primary rows.
- Exact checks: P1 parse rate 100% for specialist predictions; P2 routed pitch MAE smaller than M0; P3 identical roll; P4 identical square-vFoV. All required for the original primary success definition.
- Cluster bootstrap: 10,000 draws over location IDs, descriptive only.
- No model selection, routing changes, epoch changes, mixing/blending or Stable101 reuse after test reveal.

The R20 final numerical output files were not included in the saved script attachment from which this candidate was assembled. Import the *actual* frozen Kaggle `R20_protocol.json`, `R20_final_verdict.json`, predictions, category summaries and checksum manifest once redistribution rights and provenance have been checked. Avoid manually retyping metrics.
