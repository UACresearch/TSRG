# ==========================================================================================
# Tourism-Puffin
# R19 | FINAL FULL-DEVELOPMENT M1-v4 PITCH-SPECIALIST TRAINING
#
# Frozen by R18.
#
# PURPOSE
# -------
# Train ONE final full-development M1-v4 component for M2-PAR.
#
# Data:
#   526 primary
#   216 aux
#   742 total
#
# Model:
#   Puffin-Base RADIO       frozen
#   Puffin-Base Projector   frozen
#   Puffin-Base Qwen        frozen
#   q/k/v/o LoRA            trainable
#
# Exact R13-v4 configuration:
#   LoRA r=8
#   alpha=16
#   dropout=.05
#   LR=1e-5
#   weight decay=.01
#   grad accumulation=16
#   grad clip=1
#   primary weight=1.0
#   aux weight=.4
#   caption CE=.25
#   camera CE=1.0
#   corrected roll/pitch/square-vFoV target text
#   missing primary parameter -> M0 in text only
#   NO geometry head
#   NO geometry loss
#   3 epochs
#   Epoch 3 PRELOCKED
#
# IMPORTANT
# ---------
# NO Stable101.
# NO test239.
# NO MAE evaluation.
# NO epoch selection.
#
# This component will later be used ONLY for:
#   pitch of event / heritage images
#
# roll and square-vFoV remain M0 in M2-PAR.
# ==========================================================================================


# ==========================================================================================
# 0. IMPORTS
# ==========================================================================================

import re
import gc
import json
import math
import time
import random
import hashlib
import inspect
import importlib
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
import torch.nn.functional as F

from tqdm.auto import tqdm

import kagglehub


# ==========================================================================================
# 1. FROZEN CONFIG
# ==========================================================================================

SEED = 20260908

EPOCHS = 3

GRAD_ACCUM = 16

GRAD_CLIP = 1.0

LR_LORA = 1e-5

WEIGHT_DECAY = 0.01

PRIMARY_WEIGHT = 1.0

AUX_WEIGHT = 0.4

CAPTION_TOKEN_WEIGHT = 0.25

CAMERA_TOKEN_WEIGHT = 1.0

DTYPE = torch.bfloat16


# ----------------------------------------------------------
# Need dual T4
# ----------------------------------------------------------

assert torch.cuda.is_available(), (
    "GPU is required for R19."
)

assert (
    torch.cuda.device_count()
    >=
    2
), (
    "R19 expects 2 GPUs. "
    "Use Kaggle 2xT4."
)


VIS_DEV = torch.device(
    "cuda:0"
)

LLM_DEV = torch.device(
    "cuda:1"
)


PROMPT = (
    "Describe the image in detail. "
    "Then reason its spatial distribution and estimate "
    "its camera parameters (roll, pitch, and field-of-view)."
)


# ==========================================================================================
# 2. DATA / ARTIFACT PATHS
# ==========================================================================================

DATA_ROOT = Path(
    "/kaggle/input/datasets/caolitong/"
    "tourism-puffin-geometry-training"
)


GEO_JSONL = (
    DATA_ROOT
    /
    "geometry_training"
    /
    "geometry_train_combined.jsonl"
)


M0_PATH = Path(
    "/kaggle/input/datasets/caolitong/"
    "tourism-puffin-m0-train742-merged-v1/"
    "m0_train742_predictions_merged.csv"
)


RADIO_CACHE_HANDLE = (
    "caolitong/"
    "tourism-puffin-m1-v3-radio-cache-742"
)


R18_HANDLE = (
    "caolitong/"
    "tourism-puffin-r18-m2-par-freeze-v1"
)


SAVE_HANDLE = (
    "caolitong/"
    "tourism-puffin-r19-m2par-full-pitch-specialist-v1"
)


WORK = Path(
    "/kaggle/working/"
    "tourism_puffin_r19_full_pitch_specialist"
)


STAGE = (
    WORK
    /
    "persistent_stage"
)


STAGE.mkdir(
    parents=True,
    exist_ok=True
)


EXPECTED_RADIO_SHA256 = (
    "efe3b25e4a955782aa8bf614358b32be0"
    "bf8e8dd63281fd6d5ced9bb56e0ddc4"
)


EXPECTED_PRIMARY = 526

EXPECTED_AUX = 216

EXPECTED_TOTAL = 742

EXPECTED_OPT_STEPS = math.ceil(
    EXPECTED_TOTAL
    /
    GRAD_ACCUM
)


assert EXPECTED_OPT_STEPS == 47


print(
    "=" * 108
)

print(
    "R19 | FINAL FULL-DEVELOPMENT "
    "M1-v4 PITCH SPECIALIST"
)

print(
    "=" * 108
)


print(
    "GPUs:",
    [
        torch.cuda.get_device_name(i)
        for i in range(
            torch.cuda.device_count()
        )
    ]
)


print(
    "VIS_DEV:",
    VIS_DEV
)

print(
    "LLM_DEV:",
    LLM_DEV
)

print(
    "Stable101 used: False"
)

print(
    "test239 used: False"
)


# ==========================================================================================
# 3. REPRODUCIBILITY
# ==========================================================================================

random.seed(
    SEED
)

np.random.seed(
    SEED
)

torch.manual_seed(
    SEED
)

torch.cuda.manual_seed_all(
    SEED
)


# ==========================================================================================
# 4. HELPERS
# ==========================================================================================

def sha256_file(path):

    path = Path(
        path
    )

    h = hashlib.sha256()

    with path.open(
        "rb"
    ) as f:

        while True:

            block = f.read(
                8 * 1024 * 1024
            )

            if not block:
                break

            h.update(
                block
            )

    return h.hexdigest()


def sha256_text(text):

    return hashlib.sha256(
        str(text).encode(
            "utf-8"
        )
    ).hexdigest()


def find_file(
    root,
    filename,
):

    root = Path(
        root
    )

    direct = (
        root /
        filename
    )

    if direct.is_file():
        return direct

    hits = list(
        root.rglob(
            filename
        )
    )

    assert hits, (
        f"Could not find {filename} "
        f"under {root}"
    )

    return hits[0]


def dataset_download_fresh(
    handle
):

    fn = kagglehub.dataset_download

    sig = inspect.signature(
        fn
    )

    kwargs = {}

    if (
        "force_download"
        in sig.parameters
    ):
        kwargs[
            "force_download"
        ] = True

    return Path(
        fn(
            handle,
            **kwargs
        )
    )


def remote_candidate(
    root,
    relative_path,
):

    root = Path(
        root
    )

    relative_path = Path(
        relative_path
    )

    direct = (
        root /
        relative_path
    )

    if direct.is_file():
        return direct

    suffix = str(
        relative_path
    ).replace(
        "\\",
        "/"
    )

    hits = []

    for p in root.rglob(
        relative_path.name
    ):

        if (
            p.is_file()
            and
            str(p)
            .replace(
                "\\",
                "/"
            )
            .endswith(
                suffix
            )
        ):

            hits.append(
                p
            )

    if len(
        hits
    ) == 1:

        return hits[0]

    return None


def try_get_remote():

    try:

        return dataset_download_fresh(
            SAVE_HANDLE
        )

    except Exception:

        return None


def upload_stage(
    note
):

    kagglehub.dataset_upload(
        SAVE_HANDLE,
        str(
            STAGE
        ),
        version_notes=note,
    )


def verify_remote_hashes(
    hash_map,
    max_tries=20,
    sleep_seconds=10,
):

    last_error = None

    for attempt in range(
        1,
        max_tries + 1,
    ):

        try:

            root = dataset_download_fresh(
                SAVE_HANDLE
            )

            okay = True

            for (
                rel,
                expected_sha,
            ) in hash_map.items():

                p = remote_candidate(
                    root,
                    rel
                )

                if p is None:

                    okay = False

                    last_error = (
                        "missing remote file: "
                        +
                        rel
                    )

                    break

                actual_sha = sha256_file(
                    p
                )

                if (
                    actual_sha
                    !=
                    expected_sha
                ):

                    okay = False

                    last_error = (
                        "SHA mismatch: "
                        +
                        rel
                    )

                    break

            if okay:

                for rel in hash_map:

                    print(
                        "REMOTE_SHA256_VERIFIED:",
                        rel
                    )

                return True

        except Exception as e:

            last_error = repr(
                e
            )

        print(
            "Waiting for Dataset "
            f"processing {attempt}/"
            f"{max_tries} | "
            f"{last_error}"
        )

        time.sleep(
            sleep_seconds
        )

    raise RuntimeError(
        "Remote SHA verification failed: "
        +
        str(
            last_error
        )
    )


# ==========================================================================================
# 5. VERIFY R18 FREEZE BEFORE ANY TRAINING
# ==========================================================================================

print(
    "\nDOWNLOADING AND VERIFYING R18 FREEZE..."
)


R18_ROOT = dataset_download_fresh(
    R18_HANDLE
)


R18_MANIFEST_PATH = find_file(
    R18_ROOT,
    "sha256_manifest.json"
)


r18_manifest = json.loads(
    R18_MANIFEST_PATH.read_text(
        encoding="utf-8"
    )
)


for (
    filename,
    expected_sha,
) in r18_manifest.items():

    p = find_file(
        R18_ROOT,
        filename,
    )

    actual_sha = sha256_file(
        p
    )

    assert (
        actual_sha
        ==
        expected_sha
    ), (
        f"R18 SHA mismatch: "
        f"{filename}"
    )


print(
    "R18_SHA256_MANIFEST_VERIFIED: PASSED"
)


R18_PLAN_PATH = find_file(
    R18_ROOT,
    "R18_final_training_plan.json"
)


R18_SYSTEM_PATH = find_file(
    R18_ROOT,
    "R18_M2PAR_system_definition.json"
)


R18_TEST_PATH = find_file(
    R18_ROOT,
    "R18_test239_precommit.json"
)


r18_plan = json.loads(
    R18_PLAN_PATH.read_text(
        encoding="utf-8"
    )
)


r18_system = json.loads(
    R18_SYSTEM_PATH.read_text(
        encoding="utf-8"
    )
)


r18_test = json.loads(
    R18_TEST_PATH.read_text(
        encoding="utf-8"
    )
)


assert (
    r18_plan[
        "training_data"
    ][
        "primary"
    ]
    ==
    526
)

assert (
    r18_plan[
        "training_data"
    ][
        "aux"
    ]
    ==
    216
)

assert (
    r18_plan[
        "training_data"
    ][
        "total"
    ]
    ==
    742
)

assert (
    r18_plan[
        "LoRA_r"
    ]
    ==
    8
)

assert (
    r18_plan[
        "LoRA_alpha"
    ]
    ==
    16
)

assert (
    float(
        r18_plan[
            "LoRA_dropout"
        ]
    )
    ==
    0.05
)

assert (
    float(
        r18_plan[
            "learning_rate"
        ]
    )
    ==
    LR_LORA
)

assert (
    int(
        r18_plan[
            "epochs"
        ]
    )
    ==
    3
)

assert (
    r18_plan[
        "epoch_selection"
    ]
    ==
    "epoch 3 prelocked"
)

assert (
    r18_plan[
        "geometry_head"
    ]
    is False
)

assert (
    r18_plan[
        "geometry_loss"
    ]
    is False
)

assert (
    r18_plan[
        "Stable101_for_selection"
    ]
    is False
)

assert (
    r18_plan[
        "test239_for_training"
    ]
    is False
)


assert (
    r18_system[
        "status"
    ]
    ==
    "FROZEN_CANDIDATE_BEFORE_FINAL_TEST"
)


assert (
    r18_system[
        "pitch"
    ][
        "event"
    ]
    ==
    "M1-v4 specialist"
)

assert (
    r18_system[
        "pitch"
    ][
        "heritage"
    ]
    ==
    "M1-v4 specialist"
)

assert (
    r18_system[
        "pitch"
    ][
        "natural"
    ]
    ==
    "M0"
)

assert (
    r18_system[
        "pitch"
    ][
        "purpose_built"
    ]
    ==
    "M0"
)


assert (
    r18_test[
        "status_at_R18"
    ]
    ==
    "PRISTINE_UNTOUCHED"
)


R18_PLAN_SHA = sha256_file(
    R18_PLAN_PATH
)

R18_SYSTEM_SHA = sha256_file(
    R18_SYSTEM_PATH
)

R18_TEST_SHA = sha256_file(
    R18_TEST_PATH
)


print(
    "R18 TRAINING PLAN LOCK VERIFIED"
)

print(
    "R18 M2-PAR SYSTEM LOCK VERIFIED"
)

print(
    "R18 test239 precommit verified"
)


# ==========================================================================================
# 6. LOAD 742 MASTER DATA
# ==========================================================================================

assert GEO_JSONL.is_file()

assert M0_PATH.is_file()


with GEO_JSONL.open(
    "r",
    encoding="utf-8",
) as f:

    raw_rows = [

        json.loads(
            line
        )

        for line in f

        if line.strip()
    ]


df = pd.DataFrame(
    raw_rows
).reset_index(
    drop=True
)


df[
    "id"
] = (
    df[
        "id"
    ]
    .astype(str)
)


df[
    "global_index"
] = np.arange(
    len(df),
    dtype=int,
)


m0 = pd.read_csv(
    M0_PATH
).reset_index(
    drop=True
)


assert len(df) == 742

assert len(m0) == 742

assert df["id"].is_unique


if (
    "id"
    in
    m0.columns
):

    m0[
        "id"
    ] = (
        m0[
            "id"
        ]
        .astype(str)
    )

    assert (
        m0[
            "id"
        ].tolist()
        ==
        df[
            "id"
        ].tolist()
    )


TARGET_COLS = [

    "target_roll_deg",

    "target_pitch_deg",

    "target_square_vfov_deg",
]


M0_COLS = [

    "m0_roll_deg",

    "m0_pitch_deg",

    "m0_square_vfov_deg",
]


for col in (
    TARGET_COLS
    +
    M0_COLS
    +
    [
        "output_text"
    ]
):

    assert col in m0.columns, (
        f"Missing column: {col}"
    )


primary = (
    df[
        df[
            "label_provenance"
        ]
        ==
        "geocalib_pseudo_parameter_filtered"
    ]
    .copy()
)


aux = (
    df[
        df[
            "label_provenance"
        ]
        ==
        "projection_truth"
    ]
    .copy()
)


assert len(primary) == 526

assert len(aux) == 216


primary_indices = (
    primary[
        "global_index"
    ]
    .astype(int)
    .tolist()
)


aux_indices = (
    aux[
        "global_index"
    ]
    .astype(int)
    .tolist()
)


train_indices = (
    primary_indices
    +
    aux_indices
)


assert len(
    train_indices
) == 742


assert len(
    set(
        train_indices
    )
) == 742


print(
    "\nFULL DEVELOPMENT DATA:"
)

print(
    "primary =",
    len(
        primary_indices
    )
)

print(
    "aux     =",
    len(
        aux_indices
    )
)

print(
    "total   =",
    len(
        train_indices
    )
)

print(
    "optimizer steps / epoch =",
    EXPECTED_OPT_STEPS
)

print(
    "final partial accumulation group =",
    EXPECTED_TOTAL
    %
    GRAD_ACCUM,
    "samples"
)

print(
    "R13-compatible /16 scaling preserved:",
    True
)


# ==========================================================================================
# 7. LOCK R19 PROTOCOL
# ==========================================================================================

LOCKED_PROTOCOL = {

    "run":
        "R19",

    "system":
        "M2-PAR",

    "component":
        (
            "full-development "
            "M1-v4 pitch specialist"
        ),

    "role":
        (
            "pitch candidate only for "
            "event and heritage"
        ),

    "R18_handle":
        R18_HANDLE,

    "R18_training_plan_sha256":
        R18_PLAN_SHA,

    "R18_system_definition_sha256":
        R18_SYSTEM_SHA,

    "R18_test_precommit_sha256":
        R18_TEST_SHA,

    "seed":
        SEED,

    "train_primary":
        526,

    "train_aux":
        216,

    "train_total":
        742,

    "radio":
        (
            "Puffin-Base exact "
            "persistent RADIO cache; frozen"
        ),

    "projector":
        (
            "Puffin-Base projector; "
            "frozen from first step"
        ),

    "qwen":
        "Puffin-Base Qwen2.5-1.5B",

    "trainable":
        "q/k/v/o LoRA only",

    "lora_r":
        8,

    "lora_alpha":
        16,

    "lora_dropout":
        0.05,

    "learning_rate":
        LR_LORA,

    "weight_decay":
        WEIGHT_DECAY,

    "gradient_accumulation":
        GRAD_ACCUM,

    "partial_accumulation_behavior":
        (
            "preserve R13 implementation: "
            "final partial group loss still "
            "divided by 16"
        ),

    "gradient_clip":
        GRAD_CLIP,

    "primary_weight":
        PRIMARY_WEIGHT,

    "aux_weight":
        AUX_WEIGHT,

    "caption_token_weight":
        CAPTION_TOKEN_WEIGHT,

    "camera_token_weight":
        CAMERA_TOKEN_WEIGHT,

    "geometry_head":
        False,

    "geometry_loss":
        False,

    "epochs":
        3,

    "epoch_selection":
        "epoch 3 prelocked",

    "prompt":
        PROMPT,

    "corrected_square_vfov_target":
        True,

    "missing_parameter_policy":
        (
            "M0 self-distillation "
            "in text only"
        ),

    "development_MAE_calculated":
        False,

    "Stable101_used":
        False,

    "test239_used":
        False,
}


PROTOCOL_SIGNATURE = sha256_text(
    json.dumps(
        LOCKED_PROTOCOL,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    )
)


LOCKED_PROTOCOL[
    "protocol_signature_sha256"
] = PROTOCOL_SIGNATURE


PROTOCOL_PATH = (
    STAGE /
    "R19_protocol.json"
)


PROTOCOL_PATH.write_text(
    json.dumps(
        LOCKED_PROTOCOL,
        indent=2,
    ),
    encoding="utf-8",
)


print(
    "\nR19 PROTOCOL SIGNATURE:",
    PROTOCOL_SIGNATURE
)


# ==========================================================================================
# 8. CHECK FOR COMPATIBLE REMOTE RESUME
# ==========================================================================================

remote_existing = (
    try_get_remote()
)


resume_epoch = 0

resume_root = None


if (
    remote_existing
    is not None
):

    remote_protocol = remote_candidate(
        remote_existing,
        "R19_protocol.json",
    )

    if (
        remote_protocol
        is not None
    ):

        old = json.loads(
            remote_protocol.read_text(
                encoding="utf-8"
            )
        )

        assert (
            old.get(
                "protocol_signature_sha256"
            )
            ==
            PROTOCOL_SIGNATURE
        ), (
            "Existing R19 Dataset "
            "has a DIFFERENT protocol. "
            "Refusing to overwrite."
        )

        print(
            "EXISTING_R19_PROTOCOL_MATCHED"
        )

        # --------------------------------------------------
        # Verify each complete epoch.
        # Also copy verified prior epoch directories into
        # local STAGE so future dataset_upload preserves them.
        # --------------------------------------------------

        for ep in (
            1,
            2,
            3,
        ):

            sha_path = remote_candidate(
                remote_existing,
                f"epoch_{ep}/sha256.json",
            )

            if (
                sha_path
                is None
            ):
                break

            hashes = json.loads(
                sha_path.read_text(
                    encoding="utf-8"
                )
            )

            epoch_ok = True

            for (
                rel,
                expected_sha,
            ) in hashes.items():

                p = remote_candidate(
                    remote_existing,
                    rel
                )

                if (
                    p is None
                    or
                    sha256_file(p)
                    !=
                    expected_sha
                ):

                    epoch_ok = False
                    break

            if not epoch_ok:
                break

            remote_epoch_dir = (
                sha_path.parent
            )

            local_epoch_dir = (
                STAGE /
                f"epoch_{ep}"
            )

            shutil.copytree(
                remote_epoch_dir,
                local_epoch_dir,
                dirs_exist_ok=True,
            )

            resume_epoch = ep
            resume_root = remote_existing

        remote_history = remote_candidate(
            remote_existing,
            "train_history.csv",
        )

        if (
            remote_history
            is not None
        ):

            shutil.copy2(
                remote_history,
                STAGE /
                "train_history.csv",
            )

        print(
            "REMOTE RESUME EPOCH:",
            resume_epoch
        )


# ==========================================================================================
# 9. PERSISTENCE PREFLIGHT
# ==========================================================================================

if (
    remote_existing
    is None
):

    (
        STAGE /
        "upload_probe.txt"
    ).write_text(
        "R19 persistence preflight",
        encoding="utf-8",
    )

    print(
        "\nTESTING PERSISTENT STORAGE..."
    )

    upload_stage(
        (
            "R19 protocol freeze "
            "and persistence preflight"
        )
    )

    verify_remote_hashes(
        {
            "R19_protocol.json":
                sha256_file(
                    PROTOCOL_PATH
                )
        }
    )

    print(
        "PERSISTENT_BACKUP_PREFLIGHT_PASSED"
    )

else:

    print(
        "EXISTING PERSISTENT R19 "
        "DATASET DETECTED"
    )


# ==========================================================================================
# 10. LOAD EXACT PUFFIN RADIO CACHE
# ==========================================================================================

cache_hits = list(
    Path(
        "/kaggle/input"
    ).rglob(
        "radio_tokens_742_float32.npy"
    )
)


if cache_hits:

    CACHE_PATH = (
        cache_hits[0]
    )

else:

    cache_root = Path(
        kagglehub.dataset_download(
            RADIO_CACHE_HANDLE
        )
    )

    CACHE_PATH = find_file(
        cache_root,
        "radio_tokens_742_float32.npy",
    )


cache = np.load(
    CACHE_PATH,
    mmap_mode="r",
)


assert (
    cache.shape
    ==
    (
        742,
        256,
        5120,
    )
)


assert (
    cache.dtype
    ==
    np.float32
)


print(
    "\nCALCULATING RADIO SHA256..."
)


cache_sha = sha256_file(
    CACHE_PATH
)


assert (
    cache_sha
    ==
    EXPECTED_RADIO_SHA256
)


print(
    "VERIFIED_PUFFIN_BASE_RADIO_CACHE:",
    cache.shape
)


# ==========================================================================================
# 11. GET PUFFIN-BASE + QWEN TEXT ASSETS
# ==========================================================================================

from huggingface_hub import (
    hf_hub_download,
    snapshot_download,
)


print(
    "\nRESTORING PUFFIN-BASE..."
)


CKPT = Path(
    hf_hub_download(
        repo_id="KangLiao/Puffin",
        filename="Puffin-Base.pth",
    )
)


assert CKPT.is_file()


print(
    "PUFFIN_BASE_READY:",
    round(
        CKPT.stat().st_size
        /
        1024**3,
        3,
    ),
    "GiB"
)


QDIR = (
    WORK /
    "qwen_text_assets"
)


QDIR.mkdir(
    parents=True,
    exist_ok=True,
)


snapshot_download(

    repo_id=(
        "Qwen/"
        "Qwen2.5-1.5B-Instruct"
    ),

    local_dir=str(
        QDIR
    ),

    allow_patterns=[
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
    ],

    max_workers=3,
)


for f in [
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
]:

    assert (
        QDIR /
        f
    ).is_file()


print(
    "QWEN_TEXT_ASSETS_READY"
)


# ==========================================================================================
# 12. PEFT / TORCHAO PATCH
# ==========================================================================================

import peft.import_utils as peft_utils


peft_utils.is_torchao_available = (
    lambda: False
)


try:

    importlib.import_module(
        "peft.tuners.lora.torchao"
    ).is_torchao_available = (
        lambda: False
    )

except Exception:

    pass


from peft import (
    LoraConfig,
    get_peft_model,
    set_peft_model_state_dict,
)


from safetensors.torch import (
    load_file as load_safetensors,
)


# ==========================================================================================
# 13. BUILD TOKENIZER / BASE PROJECTOR / BASE QWEN
# ==========================================================================================

from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModelForCausalLM,
)


tok = (
    AutoTokenizer
    .from_pretrained(
        str(
            QDIR
        ),
        use_fast=True,
        local_files_only=True,
    )
)


config = (
    AutoConfig
    .from_pretrained(
        str(
            QDIR
        ),
        local_files_only=True,
    )
)


config._attn_implementation = (
    "sdpa"
)


assert (
    tok.eos_token_id
    is not None
)


print(
    "\nRESTORING ORIGINAL "
    "PUFFIN-BASE QWEN + PROJECTOR..."
)


puffin = torch.load(
    str(
        CKPT
    ),
    map_location="cpu",
    mmap=True,
    weights_only=True,
)


state = (
    puffin.get(
        "state_dict",
        puffin,
    )
    if isinstance(
        puffin,
        dict,
    )
    else
    puffin
)


assert isinstance(
    state,
    dict,
)


# ==========================================================================================
# 13A. FROZEN PROJECTOR
# ==========================================================================================

projector = nn.Sequential(

    nn.Linear(
        5120,
        1536,
    ),

    nn.SiLU(),

    nn.Linear(
        1536,
        1536,
    ),
)


proj_state = {

    k[
        len(
            "projector."
        ):
    ]:
        v

    for k, v
    in state.items()

    if k.startswith(
        "projector."
    )
}


assert (
    set(
        proj_state.keys()
    )
    ==
    set(
        projector
        .state_dict()
        .keys()
    )
)


projector.load_state_dict(
    proj_state,
    strict=True,
)


projector = (
    projector
    .to(
        VIS_DEV,
        dtype=torch.float32,
    )
)


projector.requires_grad_(
    False
)


projector.eval()


# ==========================================================================================
# 13B. PUFFIN-BASE QWEN
# ==========================================================================================

base_llm = (
    AutoModelForCausalLM
    .from_config(
        config
    )
)


llm_state = {

    k[
        len(
            "llm."
        ):
    ]:
        v

    for k, v
    in state.items()

    if k.startswith(
        "llm."
    )
}


expected_state = (
    base_llm
    .state_dict()
)


assert (
    set(
        llm_state
    )
    ==
    set(
        expected_state
    )
)


for key in expected_state:

    assert (
        tuple(
            expected_state[
                key
            ].shape
        )
        ==
        tuple(
            llm_state[
                key
            ].shape
        )
    )


del expected_state


base_llm.load_state_dict(
    llm_state,
    strict=True,
)


base_llm = (
    base_llm
    .to(
        device=LLM_DEV,
        dtype=DTYPE,
    )
)


del llm_state
del proj_state
del state
del puffin


gc.collect()


base_llm.config.use_cache = False


base_llm.gradient_checkpointing_enable(
    gradient_checkpointing_kwargs={
        "use_reentrant":
            False
    }
)


# ==========================================================================================
# 14. FRESH LoRA
# ==========================================================================================

lora_config = LoraConfig(

    r=8,

    lora_alpha=16,

    lora_dropout=0.05,

    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
    ],

    bias="none",

    task_type="CAUSAL_LM",
)


model = get_peft_model(
    base_llm,
    lora_config,
)


trainable_params = [

    p

    for p
    in model.parameters()

    if p.requires_grad
]


trainable_names = [

    n

    for n, p
    in model.named_parameters()

    if p.requires_grad
]


trainable_n = sum(
    p.numel()
    for p in trainable_params
)


print(
    "\nTRAINABLE LoRA PARAMS:",
    trainable_n
)


print(
    "TRAINABLE PROJECTOR PARAMS:",
    sum(
        p.numel()
        for p in projector.parameters()
        if p.requires_grad
    )
)


assert (
    trainable_n
    ==
    2179072
)


assert all(
    "lora_"
    in n
    for n in trainable_names
)


assert all(
    not p.requires_grad
    for p in projector.parameters()
)


print(
    "TRUE_FROZEN_PROJECTOR_LORA_ONLY_CONFIRMED"
)


optimizer = torch.optim.AdamW(

    trainable_params,

    lr=LR_LORA,

    weight_decay=WEIGHT_DECAY,
)


# ==========================================================================================
# 15. RESTORE VERIFIED RESUME STATE IF NEEDED
# ==========================================================================================

if (
    resume_epoch > 0
    and
    resume_root is not None
):

    adapter_path = remote_candidate(
        resume_root,
        (
            f"epoch_{resume_epoch}/"
            "qwen_lora/"
            "adapter_model.safetensors"
        ),
    )


    optimizer_path = remote_candidate(
        resume_root,
        (
            f"epoch_{resume_epoch}/"
            "optimizer_resume.pt"
        ),
    )


    assert (
        adapter_path
        is not None
    )

    assert (
        optimizer_path
        is not None
    )


    adapter_state = load_safetensors(
        str(
            adapter_path
        )
    )


    set_peft_model_state_dict(
        model,
        adapter_state,
    )


    opt_state = torch.load(
        optimizer_path,
        map_location=LLM_DEV,
        weights_only=False,
    )


    optimizer.load_state_dict(
        opt_state[
            "optimizer"
        ]
    )


    print(
        "RESUMED FROM VERIFIED EPOCH:",
        resume_epoch
    )


else:

    print(
        "STARTING FROM FRESH "
        "PUFFIN-BASE LoRA"
    )


# ==========================================================================================
# 16. STRICT OFFICIAL PROMPT
# ==========================================================================================

PREFIX_IDS = tok.encode(

    (
        "<|im_start|>user\n"
        "<|vision_start|>"
    ),

    add_special_tokens=False,
)


SUFFIX_IDS = tok.encode(

    (
        "<|vision_end|>\n"
        +
        PROMPT
        +
        "<|im_end|>\n"
        +
        "<|im_start|>assistant\n"
    ),

    add_special_tokens=False,
)


assert len(
    PREFIX_IDS
) > 0


assert len(
    SUFFIX_IDS
) > 0


PREFIX_IDS_T = torch.tensor(
    PREFIX_IDS,
    dtype=torch.long,
    device=LLM_DEV,
).unsqueeze(
    0
)


SUFFIX_IDS_T = torch.tensor(
    SUFFIX_IDS,
    dtype=torch.long,
    device=LLM_DEV,
).unsqueeze(
    0
)


print(
    "STRICT_OFFICIAL_PROMPT_READY"
)


# ==========================================================================================
# 17. CORRECTED TEXT SUPERVISION
# ==========================================================================================

CAMERA_MARKER = re.compile(
    (
        r"(?i)"
        r"(?:the\s+)?"
        r"(?:estimated\s+)?"
        r"camera parameters"
        r".{0,120}?"
        r"are\s*:"
    )
)


marker_found = 0


def extract_caption(
    row_idx
):

    global marker_found


    old = str(
        m0.iloc[
            row_idx
        ][
            "output_text"
        ]
    )


    match = CAMERA_MARKER.search(
        old
    )


    if match:

        marker_found += 1

        caption = old[
            :
            match.start()
        ].strip()

    else:

        caption = old.strip()


    caption = re.sub(
        r"\s+",
        " ",
        caption,
    )


    tokenized = tok.encode(
        caption,
        add_special_tokens=False,
    )


    if len(
        tokenized
    ) > 92:

        sentences = re.split(
            r"(?<=[.!?])\s+",
            caption,
        )

        keep = ""

        for sentence in sentences:

            candidate = (
                keep
                +
                " "
                +
                sentence
            ).strip()

            if len(
                tok.encode(
                    candidate,
                    add_special_tokens=False,
                )
            ) > 92:

                break

            keep = candidate

        if keep:

            caption = keep

        else:

            caption = tok.decode(
                tokenized[
                    :88
                ]
            )


    if (
        caption
        and
        caption[-1]
        not in ".!?"
    ):

        caption += "."


    return caption


def build_supervision(
    row_idx
):

    r = m0.iloc[
        row_idx
    ]


    values_deg = []


    for (
        target_col,
        baseline_col,
    ) in zip(
        TARGET_COLS,
        M0_COLS,
    ):

        if pd.notna(
            r[
                target_col
            ]
        ):

            value = float(
                r[
                    target_col
                ]
            )

        else:

            value = float(
                r[
                    baseline_col
                ]
            )


        assert np.isfinite(
            value
        )

        values_deg.append(
            value
        )


    values_rad = [

        math.radians(
            x
        )

        for x in values_deg
    ]


    caption = extract_caption(
        row_idx
    )


    caption_text = (
        (
            caption
            +
            " "
        )
        if caption
        else ""
    )


    caption_ids = (
        tok.encode(
            caption_text,
            add_special_tokens=False,
        )
        if caption_text
        else []
    )


    camera_text = (
        "The camera parameters "
        "(roll, pitch, and field-of-view) are: "
        f"{values_rad[0]:.6f}, "
        f"{values_rad[1]:.6f}, "
        f"{values_rad[2]:.6f}."
    )


    camera_ids = tok.encode(
        (
            camera_text
            +
            "<|im_end|>"
        ),
        add_special_tokens=False,
    )


    target_ids = (
        caption_ids
        +
        camera_ids
    )


    token_weights = (
        [
            CAPTION_TOKEN_WEIGHT
        ]
        *
        len(
            caption_ids
        )
        +
        [
            CAMERA_TOKEN_WEIGHT
        ]
        *
        len(
            camera_ids
        )
    )


    provenance = (
        df.iloc[
            row_idx
        ][
            "label_provenance"
        ]
    )


    if (
        provenance
        ==
        "geocalib_pseudo_parameter_filtered"
    ):

        row_weight = (
            PRIMARY_WEIGHT
        )

    elif (
        provenance
        ==
        "projection_truth"
    ):

        row_weight = (
            AUX_WEIGHT
        )

    else:

        raise RuntimeError(
            "Unexpected provenance: "
            +
            str(
                provenance
            )
        )


    return {

        "target_ids":
            target_ids,

        "token_weights":
            token_weights,

        "row_weight":
            row_weight,

        "camera_text":
            camera_text,
    }


supervision = {}


for idx in train_indices:

    supervision[
        idx
    ] = build_supervision(
        idx
    )


assert len(
    supervision
) == 742


assert (
    marker_found
    ==
    742
), (
    f"Expected 742 camera markers, "
    f"found {marker_found}"
)


print(
    "CORRECTED_TEXT_TARGETS_READY:",
    len(
        supervision
    )
)


print(
    "Camera-marker extraction count:",
    marker_found,
    "/ 742"
)


# ==========================================================================================
# 18. TRAINING FORWARD
# ==========================================================================================

def forward_training_sample(
    row_idx
):

    # ------------------------------------------------------
    # Exact cached RADIO tokens.
    # copy=True avoids numpy mmap non-writable warning.
    # Values are unchanged.
    # ------------------------------------------------------

    visual_np = np.array(
        cache[
            row_idx
        ],
        dtype=np.float32,
        copy=True,
    )


    visual = (
        torch
        .from_numpy(
            visual_np
        )
        .unsqueeze(
            0
        )
        .to(
            VIS_DEV
        )
    )


    with torch.no_grad():

        image_embeds = projector(
            visual
        )


    del visual
    del visual_np


    image_embeds = (
        image_embeds
        .to(
            LLM_DEV,
            dtype=DTYPE,
        )
    )


    sup = supervision[
        row_idx
    ]


    target_ids = torch.tensor(
        sup[
            "target_ids"
        ],
        dtype=torch.long,
        device=LLM_DEV,
    ).unsqueeze(
        0
    )


    token_weights = torch.tensor(
        sup[
            "token_weights"
        ],
        dtype=torch.float32,
        device=LLM_DEV,
    )


    with torch.no_grad():

        prefix_embeds = (
            model
            .get_input_embeddings()(
                PREFIX_IDS_T
            )
        )


        suffix_embeds = (
            model
            .get_input_embeddings()(
                SUFFIX_IDS_T
            )
        )


        target_embeds = (
            model
            .get_input_embeddings()(
                target_ids
            )
        )


    inputs_embeds = torch.cat(
        [
            prefix_embeds,
            image_embeds,
            suffix_embeds,
            target_embeds,
        ],
        dim=1,
    )


    context_len = (
        prefix_embeds.shape[1]
        +
        image_embeds.shape[1]
        +
        suffix_embeds.shape[1]
    )


    attention_mask = torch.ones(
        inputs_embeds.shape[
            :2
        ],
        dtype=torch.long,
        device=LLM_DEV,
    )


    out = model(
        inputs_embeds=inputs_embeds,
        attention_mask=attention_mask,
        use_cache=False,
        return_dict=True,
    )


    target_logits = out.logits[
        :,
        context_len - 1:
        context_len
        +
        target_ids.shape[1]
        -
        1,
        :
    ]


    assert (
        target_logits.shape[1]
        ==
        target_ids.shape[1]
    )


    per_token_ce = F.cross_entropy(

        target_logits
        .reshape(
            -1,
            target_logits.shape[-1],
        )
        .float(),

        target_ids.reshape(
            -1
        ),

        reduction="none",
    )


    weighted_ce = (
        (
            per_token_ce
            *
            token_weights
        ).sum()
        /
        token_weights.sum()
    )


    loss = (
        weighted_ce
        *
        float(
            sup[
                "row_weight"
            ]
        )
    )


    return loss


# ==========================================================================================
# 19. REAL FORWARD PREFLIGHT
# ==========================================================================================

model.train()


probe_idx = train_indices[
    0
]


probe_loss = forward_training_sample(
    probe_idx
)


assert torch.isfinite(
    probe_loss
)


print(
    "\nREAL_FORWARD_PREFLIGHT_LOSS:",
    float(
        probe_loss
        .detach()
        .cpu()
    )
)


del probe_loss


optimizer.zero_grad(
    set_to_none=True
)


gc.collect()

torch.cuda.empty_cache()


print(
    "REAL_FORWARD_PREFLIGHT_PASSED"
)


# ==========================================================================================
# 20. CHECKPOINT FUNCTION
# ==========================================================================================

def save_epoch_checkpoint(
    epoch,
    mean_loss,
    optimizer_steps,
):

    epoch_dir = (
        STAGE /
        f"epoch_{epoch}"
    )


    epoch_dir.mkdir(
        parents=True,
        exist_ok=True,
    )


    model.save_pretrained(
        epoch_dir /
        "qwen_lora",
        safe_serialization=True,
    )


    torch.save(

        {

            "epoch":
                epoch,

            "run":
                "R19",

            "seed":
                SEED,

            "train_rows":
                742,

            "mean_weighted_ce":
                mean_loss,

            "optimizer_steps":
                optimizer_steps,

            "optimizer":
                optimizer.state_dict(),
        },

        epoch_dir /
        "optimizer_resume.pt",
    )


    summary = {

        "epoch":
            epoch,

        "train_primary":
            526,

        "train_aux":
            216,

        "train_total":
            742,

        "mean_weighted_ce":
            mean_loss,

        "optimizer_steps":
            optimizer_steps,

        "projector_trainable":
            False,

        "geometry_head":
            False,

        "geometry_loss":
            False,

        "MAE_calculated":
            False,

        "Stable101_used":
            False,

        "test239_used":
            False,
    }


    summary_path = (
        epoch_dir /
        "epoch_summary.json"
    )


    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )


    adapter_path = (
        epoch_dir /
        "qwen_lora" /
        "adapter_model.safetensors"
    )


    optimizer_path = (
        epoch_dir /
        "optimizer_resume.pt"
    )


    assert adapter_path.is_file()

    assert optimizer_path.is_file()

    assert summary_path.is_file()


    hashes = {

        str(
            adapter_path.relative_to(
                STAGE
            )
        ):
            sha256_file(
                adapter_path
            ),

        str(
            optimizer_path.relative_to(
                STAGE
            )
        ):
            sha256_file(
                optimizer_path
            ),

        str(
            summary_path.relative_to(
                STAGE
            )
        ):
            sha256_file(
                summary_path
            ),
    }


    sha_path = (
        epoch_dir /
        "sha256.json"
    )


    sha_path.write_text(
        json.dumps(
            hashes,
            indent=2,
        ),
        encoding="utf-8",
    )


    print(
        f"EPOCH_{epoch}_LOCAL_CHECKPOINT_COMPLETE"
    )


    print(
        f"UPLOADING_EPOCH_{epoch}_TO_KAGGLE..."
    )


    upload_stage(
        (
            "R19 full-development "
            f"permanent checkpoint epoch {epoch}"
        )
    )


    print(
        f"EPOCH_{epoch}_UPLOAD_REQUEST_COMPLETE"
    )


    verify_remote_hashes(
        hashes
    )


    print(
        f"EPOCH_{epoch}_PERMANENT_BACKUP_VERIFIED"
    )


# ==========================================================================================
# 21. FORMAL FULL-DATA TRAINING
# ==========================================================================================

HISTORY_PATH = (
    STAGE /
    "train_history.csv"
)


if HISTORY_PATH.is_file():

    history = (
        pd.read_csv(
            HISTORY_PATH
        )
        .to_dict(
            "records"
        )
    )

else:

    history = []


start_epoch = (
    resume_epoch
    +
    1
)


print(
    "\n"
    +
    "=" * 108
)


print(
    "START R19 FORMAL FULL-DEVELOPMENT TRAINING"
)


print(
    "=" * 108
)


print(
    "start_epoch:",
    start_epoch
)


if (
    start_epoch
    <=
    EPOCHS
):

    for epoch in range(
        start_epoch,
        EPOCHS + 1,
    ):

        model.train()


        order = list(
            train_indices
        )


        epoch_rng = random.Random(
            SEED
            +
            epoch
        )


        epoch_rng.shuffle(
            order
        )


        optimizer.zero_grad(
            set_to_none=True
        )


        cumulative_loss = 0.0

        optimizer_steps = 0


        iterator = tqdm(

            enumerate(
                order,
                start=1,
            ),

            total=len(
                order
            ),

            desc=(
                f"R19 epoch {epoch}/{EPOCHS}"
            ),
        )


        for (
            step,
            row_idx,
        ) in iterator:

            loss = forward_training_sample(
                row_idx
            )


            assert torch.isfinite(
                loss
            ), (
                f"Non-finite loss "
                f"epoch={epoch}, "
                f"step={step}"
            )


            loss_value = float(
                loss
                .detach()
                .cpu()
            )


            cumulative_loss += (
                loss_value
            )


            # --------------------------------------------------
            # PRESERVE R13 BEHAVIOR:
            # even final partial accumulation group divides by 16.
            # --------------------------------------------------

            (
                loss
                /
                GRAD_ACCUM
            ).backward()


            do_step = (
                (
                    step
                    %
                    GRAD_ACCUM
                    ==
                    0
                )
                or
                (
                    step
                    ==
                    len(
                        order
                    )
                )
            )


            if do_step:

                grad_norm = (
                    torch.nn.utils
                    .clip_grad_norm_(
                        trainable_params,
                        GRAD_CLIP,
                    )
                )


                assert torch.isfinite(
                    grad_norm
                )


                optimizer.step()


                optimizer.zero_grad(
                    set_to_none=True
                )


                optimizer_steps += 1


            if (
                step
                %
                128
                ==
                0
                or
                step
                ==
                len(
                    order
                )
            ):

                print(
                    f"EPOCH {epoch} "
                    f"{step}/{len(order)} | "
                    "weighted CE="
                    f"{cumulative_loss/step:.6f}",
                    flush=True,
                )


        epoch_mean_loss = (
            cumulative_loss
            /
            len(
                order
            )
        )


        assert (
            optimizer_steps
            ==
            EXPECTED_OPT_STEPS
        ), (
            f"Expected "
            f"{EXPECTED_OPT_STEPS} "
            f"optimizer steps, got "
            f"{optimizer_steps}"
        )


        history = [
            x
            for x in history
            if int(
                x[
                    "epoch"
                ]
            )
            !=
            epoch
        ]


        history.append(
            {

                "epoch":
                    epoch,

                "train_rows":
                    742,

                "mean_weighted_ce":
                    epoch_mean_loss,

                "optimizer_steps":
                    optimizer_steps,
            }
        )


        history = sorted(
            history,
            key=lambda x:
                int(
                    x[
                        "epoch"
                    ]
                ),
        )


        pd.DataFrame(
            history
        ).to_csv(
            HISTORY_PATH,
            index=False,
        )


        print(
            f"\nEPOCH {epoch} "
            "TRAINING COMPLETE | "
            "weighted CE="
            f"{epoch_mean_loss:.6f}"
        )


        save_epoch_checkpoint(

            epoch=epoch,

            mean_loss=epoch_mean_loss,

            optimizer_steps=optimizer_steps,
        )


else:

    print(
        "ALL 3 VERIFIED EPOCHS "
        "ALREADY EXIST"
    )


# ==========================================================================================
# 22. LOCK EPOCH 3 — NO MODEL SELECTION
# ==========================================================================================

FINAL_EPOCH = 3


FINAL_ADAPTER = (
    STAGE /
    "epoch_3" /
    "qwen_lora" /
    "adapter_model.safetensors"
)


FINAL_SUMMARY = (
    STAGE /
    "epoch_3" /
    "epoch_summary.json"
)


assert FINAL_ADAPTER.is_file()

assert FINAL_SUMMARY.is_file()


final_adapter_sha = sha256_file(
    FINAL_ADAPTER
)


epoch3_summary = json.loads(
    FINAL_SUMMARY.read_text(
        encoding="utf-8"
    )
)


assert (
    epoch3_summary[
        "epoch"
    ]
    ==
    3
)


assert (
    epoch3_summary[
        "MAE_calculated"
    ]
    is False
)


assert (
    epoch3_summary[
        "Stable101_used"
    ]
    is False
)


assert (
    epoch3_summary[
        "test239_used"
    ]
    is False
)


print(
    "\n"
    +
    "=" * 108
)


print(
    "R19 FINAL MODEL LOCK"
)


print(
    "=" * 108
)


print(
    "Selected using development metrics: False"
)


print(
    "Prelocked epoch:",
    3
)


print(
    "Epoch-3 adapter SHA256:",
    final_adapter_sha
)


# ==========================================================================================
# 23. CREATE FINAL LOCK RECORD
# ==========================================================================================

FINAL_LOCK = {

    "run":
        "R19",

    "system":
        "M2-PAR",

    "component":
        (
            "M1-v4 full-development "
            "pitch specialist"
        ),

    "status":
        "FROZEN_BEFORE_TEST239",

    "train_primary":
        526,

    "train_aux":
        216,

    "train_total":
        742,

    "training_epochs":
        3,

    "final_epoch":
        3,

    "epoch_selected_using_metrics":
        False,

    "development_MAE_calculated":
        False,

    "final_adapter_relative_path":
        (
            "epoch_3/qwen_lora/"
            "adapter_model.safetensors"
        ),

    "final_adapter_sha256":
        final_adapter_sha,

    "protocol_signature_sha256":
        PROTOCOL_SIGNATURE,

    "R18_training_plan_sha256":
        R18_PLAN_SHA,

    "R18_system_definition_sha256":
        R18_SYSTEM_SHA,

    "R18_test_precommit_sha256":
        R18_TEST_SHA,

    "use_in_M2PAR":
        {
            "roll":
                "DO NOT USE; M0",

            "pitch_event":
                "USE",

            "pitch_heritage":
                "USE",

            "pitch_natural":
                "DO NOT USE; M0",

            "pitch_purpose_built":
                "DO NOT USE; M0",

            "square_vfov":
                "DO NOT USE; M0",
        },

    "Stable101_used":
        False,

    "test239_used":
        False,

    "next_action":
        (
            "ONE formal test239 "
            "evaluation under frozen "
            "R18 M2-PAR protocol"
        ),
}


FINAL_LOCK_PATH = (
    STAGE /
    "R19_final_model_lock.json"
)


FINAL_LOCK_PATH.write_text(
    json.dumps(
        FINAL_LOCK,
        indent=2,
    ),
    encoding="utf-8",
)


# ==========================================================================================
# 24. TOP-LEVEL CRITICAL MANIFEST
# ==========================================================================================

critical_files = {

    "R19_protocol.json":
        sha256_file(
            PROTOCOL_PATH
        ),

    "train_history.csv":
        sha256_file(
            HISTORY_PATH
        ),

    "R19_final_model_lock.json":
        sha256_file(
            FINAL_LOCK_PATH
        ),

    "epoch_3/qwen_lora/adapter_model.safetensors":
        final_adapter_sha,

    "epoch_3/epoch_summary.json":
        sha256_file(
            FINAL_SUMMARY
        ),
}


CRITICAL_MANIFEST_PATH = (
    STAGE /
    "R19_critical_sha256.json"
)


CRITICAL_MANIFEST_PATH.write_text(
    json.dumps(
        critical_files,
        indent=2,
    ),
    encoding="utf-8",
)


critical_files[
    "R19_critical_sha256.json"
] = sha256_file(
    CRITICAL_MANIFEST_PATH
)


# ==========================================================================================
# 25. FINAL PERMANENT UPLOAD
# ==========================================================================================

print(
    "\nUPLOADING FINAL R19 LOCK..."
)


upload_stage(
    (
        "R19 FINAL full-development "
        "M1-v4 pitch specialist; "
        "Epoch3 prelocked; "
        "no development MAE; "
        "test239 untouched"
    )
)


verify_remote_hashes(
    critical_files
)


print(
    "R19_FINAL_REMOTE_LOCK_VERIFIED"
)


# ==========================================================================================
# 26. FINAL REPORT
# ==========================================================================================

history_df = pd.read_csv(
    HISTORY_PATH
)


print(
    "\n"
    +
    "#" * 108
)


print(
    "R19_FINAL_FULL_DEVELOPMENT_TRAINING_COMPLETE"
)


print(
    "#" * 108
)


print(
    "\nTRAINING HISTORY:"
)


print(
    history_df.to_string(
        index=False,
        float_format=lambda x:
            f"{x:.6f}",
    )
)


print(
    "\nTrain primary:",
    526
)


print(
    "Train aux:",
    216
)


print(
    "Train total:",
    742
)


print(
    "Projector frozen:",
    True
)


print(
    "Trainable LoRA params:",
    trainable_n
)


print(
    "Geometry head:",
    False
)


print(
    "Geometry loss:",
    False
)


print(
    "Final epoch:",
    3
)


print(
    "Epoch selected using metrics:",
    False
)


print(
    "Development MAE calculated:",
    False
)


print(
    "Stable101 used:",
    False
)


print(
    "test239 used:",
    False
)


print(
    "Final adapter SHA256:",
    final_adapter_sha
)


print(
    "Permanent Dataset:",
    SAVE_HANDLE
)


print(
    "\nNEXT FIXED ACTION:"
)


print(
    "R20 = ONE formal test239 evaluation "
    "under the frozen R18 M2-PAR rule."
)


print(
    "Do not change model, epoch, "
    "routing, category rule, or hyperparameters."
)


print(
    "#" * 108
)