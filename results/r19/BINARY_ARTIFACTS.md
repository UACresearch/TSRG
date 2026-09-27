# R19 original binary checkpoints — provenance and access

All six binaries are present in the **original user-uploaded Kaggle ZIP**, which passed CRC and all embedded critical/epoch SHA256 checks. Their exact bytes have **not** been copied into GitHub: this connector failed to transfer the 8.7 MB final adapter as one Git blob. They remain available from the original [Kaggle R19 dataset](https://www.kaggle.com/datasets/caolitong/tourism-puffin-r19-m2par-full-pitch-specialist-v1), and are recorded in [`ORIGINAL_R19_SHA256.json`](ORIGINAL_R19_SHA256.json). No substitute model was fabricated.

| Original relative path | Bytes | SHA256 |
|---|---:|---|
| `epoch_1/optimizer_resume.pt` | 17625749 | `7517af677e4e122563fba5356d7b8ed4ed24fb7badb2357231a0e640818f900f` |
| `epoch_1/qwen_lora/adapter_model.safetensors` | 8745704 | `8095560bc5d2d819b386413b94c20eb75ccd15a428613de37ee12dfca15a1261` |
| `epoch_2/optimizer_resume.pt` | 17625749 | `b17eaf54242b33570935dcc5de3f65b35844c0374f8fa74ce48e953064b96030` |
| `epoch_2/qwen_lora/adapter_model.safetensors` | 8745704 | `2c25a25852676be97bdaaf065f9e47e5fe74fcceb0ae34a3fabd04bfbad2714e` |
| `epoch_3/optimizer_resume.pt` | 17625749 | `73ddb9b88f12c5953eecad2f8500265c75379d9cb842bb75dc59f50f34613e73` |
| **`epoch_3/qwen_lora/adapter_model.safetensors`** | **8745704** | **`1dc8afa37c4947d30f58e9ae3aa260c76730dd7201a042f98fcbfd97ae0da8b0`** |

The Epoch 3 adapter is the frozen component referenced by R20 V3; the optimizer resume files serve training-resume provenance and are not needed for forward inference. If uploaded in the future, keep them byte-identical and re-check all source digests. The currently linked original Kaggle dataset is the canonical large-file archive.
