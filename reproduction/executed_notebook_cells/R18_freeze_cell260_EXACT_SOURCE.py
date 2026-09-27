# ==========================================================================================
# Tourism-Puffin
# R18 | FREEZE M2-PAR PARAMETER-AWARE HYBRID SYSTEM
#
# NEW SYSTEM:
#
#   M2-PAR = Parameter-Aware Routing
#
#   roll:
#       always M0
#
#   square-vFoV:
#       always M0
#
#   pitch:
#       event         -> M1-v4 specialist
#       heritage      -> M1-v4 specialist
#       natural       -> M0
#       purpose_built -> M0
#
# IMPORTANT:
#   - M1-v4 unified adapter branch remains CLOSED.
#   - M1-v4 is NOT promoted as a 3-parameter replacement.
#   - R18 freezes a NEW system architecture.
#   - OOF431 is development evidence, NOT independent confirmation.
#   - NO training.
#   - NO Stable101.
#   - NO test239.
#
# AFTER R18:
#   When GPU quota returns:
#   train ONE final full-development M1-v4 component
#   on all 526 primary + 216 aux, exactly 3 epochs,
#   with the already-frozen R13-v4 configuration.
#
#   Then evaluate test239 ONCE under the frozen M2-PAR rule.
# ==========================================================================================


# ==========================================================================================
# 0. IMPORTS
# ==========================================================================================

import json
import time
import hashlib
import inspect
from pathlib import Path

import numpy as np
import pandas as pd

import kagglehub


# ==========================================================================================
# 1. CONFIG
# ==========================================================================================

SEED = 20260925

BOOTSTRAP_B = 10_000


R14_HANDLE = (
    "caolitong/"
    "tourism-puffin-m1-v4-r14-oof-reveal"
)


R16_HANDLE = (
    "caolitong/"
    "tourism-puffin-m1-v4-r16-category-routing"
)


R17_HANDLE = (
    "caolitong/"
    "tourism-puffin-r17-adapter-branch-closure-v1"
)


SAVE_HANDLE = (
    "caolitong/"
    "tourism-puffin-r18-m2-par-freeze-v1"
)


WORK = Path(
    "/kaggle/working/"
    "tourism_puffin_r18_m2_par"
)


OUT = (
    WORK /
    "archive"
)


OUT.mkdir(
    parents=True,
    exist_ok=True
)


EXPECTED_ROWS = 431

EXPECTED_LOCATIONS = 57


ACTIVE_PITCH_CATEGORIES = [
    "event",
    "heritage",
]


M0_PITCH_CATEGORIES = [
    "natural",
    "purpose_built",
]


EXPECTED_PITCH_ROUTE = {

    "event":
        "M1-v4",

    "heritage":
        "M1-v4",

    "natural":
        "M0",

    "purpose_built":
        "M0",
}


PARAMS = {

    "roll": {

        "target":
            "target_roll_deg",

        "m0":
            "m0_roll_deg",

        "m1":
            "m1v4_roll_deg",
    },

    "pitch": {

        "target":
            "target_pitch_deg",

        "m0":
            "m0_pitch_deg",

        "m1":
            "m1v4_pitch_deg",
    },

    "vfov": {

        "target":
            "target_square_vfov_deg",

        "m0":
            "m0_square_vfov_deg",

        "m1":
            "m1v4_square_vfov_deg",
    },
}


print(
    "=" * 108
)

print(
    "R18 | FREEZE M2-PAR PARAMETER-AWARE HYBRID SYSTEM"
)

print(
    "=" * 108
)


print(
    "\nSYSTEM STATUS:"
)


print(
    "M0 reference: FROZEN"
)


print(
    "M1-v4 unified adapter: CLOSED"
)


print(
    "M2-PAR: NEW SYSTEM CANDIDATE"
)


print(
    "Training in R18: False"
)


print(
    "Stable101 used: False"
)


print(
    "test239 used: False"
)


# ==========================================================================================
# 2. HELPERS
# ==========================================================================================

def sha256_file(
    path
):

    path = Path(
        path
    )


    h = hashlib.sha256()


    with path.open(
        "rb"
    ) as f:

        while True:

            block = f.read(
                8
                *
                1024
                *
                1024
            )


            if not block:
                break


            h.update(
                block
            )


    return h.hexdigest()


def dataset_download_fresh(
    handle
):

    fn = (
        kagglehub
        .dataset_download
    )


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


def find_file(
    root,
    filename
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
        f"Cannot find "
        f"{filename}"
    )


    return hits[
        0
    ]


def verify_manifest(
    root,
    source_name
):

    manifest_path = (
        find_file(
            root,
            "sha256_manifest.json"
        )
    )


    manifest = json.loads(
        manifest_path
        .read_text(
            encoding="utf-8"
        )
    )


    rows = []


    for (
        filename,
        expected_sha
    ) in manifest.items():

        path = find_file(
            root,
            filename
        )


        actual_sha = (
            sha256_file(
                path
            )
        )


        assert (
            actual_sha
            ==
            expected_sha
        ), (
            f"{source_name}: "
            f"SHA mismatch: "
            f"{filename}"
        )


        rows.append(
            {

                "source":
                    source_name,

                "filename":
                    filename,

                "expected_sha256":
                    expected_sha,

                "actual_sha256":
                    actual_sha,

                "verified":
                    True,
            }
        )


    return rows


# ==========================================================================================
# 3. DOWNLOAD FROZEN R14 / R16 / R17
# ==========================================================================================

print(
    "\nDownloading R14..."
)


R14_ROOT = (
    dataset_download_fresh(
        R14_HANDLE
    )
)


print(
    "Downloading R16..."
)


R16_ROOT = (
    dataset_download_fresh(
        R16_HANDLE
    )
)


print(
    "Downloading R17..."
)


R17_ROOT = (
    dataset_download_fresh(
        R17_HANDLE
    )
)


# ==========================================================================================
# 4. VERIFY ALL SOURCE HASHES
# ==========================================================================================

integrity_rows = []


integrity_rows.extend(
    verify_manifest(
        R14_ROOT,
        "R14",
    )
)


print(
    "R14_SHA256_VERIFIED: PASSED"
)


integrity_rows.extend(
    verify_manifest(
        R16_ROOT,
        "R16",
    )
)


print(
    "R16_SHA256_VERIFIED: PASSED"
)


integrity_rows.extend(
    verify_manifest(
        R17_ROOT,
        "R17",
    )
)


print(
    "R17_SHA256_VERIFIED: PASSED"
)


# ==========================================================================================
# 5. VERIFY R17 BRANCH CLOSURE
# ==========================================================================================

R17_DECISION_PATH = (
    find_file(
        R17_ROOT,
        "R17_decision_record.json",
    )
)


r17 = json.loads(
    R17_DECISION_PATH
    .read_text(
        encoding="utf-8"
    )
)


assert (
    r17[
        "decision"
    ][
        "current_reference_system"
    ]
    ==
    "M0"
)


assert (
    r17[
        "decision"
    ][
        "unified_M1_adapter_branch"
    ]
    ==
    "CLOSED"
)


assert (
    r17[
        "decision"
    ][
        "category_expert_branch"
    ]
    ==
    "NOT_SUPPORTED_AND_CLOSED"
)


assert (
    r17[
        "decision"
    ][
        "test239_status"
    ]
    ==
    "PRISTINE_UNTOUCHED"
)


print(
    "\nR17 CLOSURE LOCK VERIFIED"
)


# ==========================================================================================
# 6. VERIFY R16 CROSS-FITTED ROUTING RESULT
# ==========================================================================================

R16_DECISION_PATH = (
    find_file(
        R16_ROOT,
        "R16_decision.json",
    )
)


R16_RULES_PATH = (
    find_file(
        R16_ROOT,
        "R16_crossfit_routing_rules.csv",
    )
)


R16_SUMMARY_PATH = (
    find_file(
        R16_ROOT,
        "R16_pooled_summary.csv",
    )
)


R16_ROUTED_PATH = (
    find_file(
        R16_ROOT,
        "R16_crossfit_routed_predictions.csv",
    )
)


r16_decision = json.loads(
    R16_DECISION_PATH
    .read_text(
        encoding="utf-8"
    )
)


rules = pd.read_csv(
    R16_RULES_PATH
)


r16_summary = pd.read_csv(
    R16_SUMMARY_PATH
)


r16_routed = pd.read_csv(
    R16_ROUTED_PATH
)


assert (
    r16_decision[
        "CATEGORY_EXPERT_EVIDENCE_PASS"
    ]
    is False
)


assert (
    r16_decision[
        "R14_gate_reopened"
    ]
    is False
)


assert (
    r16_decision[
        "Stable101_used"
    ]
    is False
)


assert (
    r16_decision[
        "test239_used"
    ]
    is False
)


print(
    "R16 STATUS VERIFIED:"
)


print(
    "Category-expert whole-system gate: False"
)


# ==========================================================================================
# 7. TEST WHETHER PITCH ROUTING RULE IS EXACTLY STABLE ACROSS ALL 4 FOLDS
# ==========================================================================================

pitch_rules = (
    rules[
        rules[
            "parameter"
        ]
        ==
        "pitch"
    ]
    .copy()
)


assert (
    pitch_rules[
        "heldout_fold"
    ].nunique()
    ==
    4
)


assert (
    len(
        pitch_rules
    )
    ==
    16
)


stability_rows = []


for fold in [
    0,
    1,
    2,
    3,
]:

    fold_rules = (
        pitch_rules[
            pitch_rules[
                "heldout_fold"
            ]
            ==
            fold
        ]
    )


    assert (
        len(
            fold_rules
        )
        ==
        4
    )


    for category, expected_route in (
        EXPECTED_PITCH_ROUTE.items()
    ):

        row = (
            fold_rules[
                fold_rules[
                    "category"
                ]
                ==
                category
            ]
        )


        assert (
            len(
                row
            )
            ==
            1
        )


        actual_route = str(
            row[
                "route"
            ]
            .iloc[
                0
            ]
        )


        assert (
            actual_route
            ==
            expected_route
        ), (
            f"Pitch rule instability: "
            f"fold={fold}, "
            f"category={category}, "
            f"actual={actual_route}, "
            f"expected={expected_route}"
        )


        stability_rows.append(
            {

                "heldout_fold":
                    fold,

                "category":
                    category,

                "route":
                    actual_route,

                "expected_route":
                    expected_route,

                "stable":
                    True,
            }
        )


routing_stability = pd.DataFrame(
    stability_rows
)


print(
    "\nPITCH ROUTING STABILITY:"
)


print(
    "event: M1-v4 in 4/4 folds"
)


print(
    "heritage: M1-v4 in 4/4 folds"
)


print(
    "natural: M0 in 4/4 folds"
)


print(
    "purpose_built: M0 in 4/4 folds"
)


print(
    "PITCH_ROUTING_RULE_FULLY_STABLE: TRUE"
)


# ==========================================================================================
# 8. LOAD ORIGINAL R14 OOF431
# ==========================================================================================

R14_OOF_PATH = (
    find_file(
        R14_ROOT,
        "R14_OOF431_merged_predictions.csv",
    )
)


oof = pd.read_csv(
    R14_OOF_PATH
)


oof[
    "id"
] = (
    oof[
        "id"
    ]
    .astype(str)
)


assert (
    len(
        oof
    )
    ==
    EXPECTED_ROWS
)


assert (
    oof[
        "id"
    ].nunique()
    ==
    EXPECTED_ROWS
)


assert (
    oof[
        "location_id"
    ].nunique()
    ==
    EXPECTED_LOCATIONS
)


# ==========================================================================================
# 9. CONSTRUCT FIXED M2-PAR OOF OUTPUTS
#
# roll -> always M0
# vfov -> always M0
#
# pitch:
#   event / heritage -> M1-v4
#   natural / purpose_built -> M0
# ==========================================================================================

hybrid = oof.copy()


hybrid[
    "m2par_roll_deg"
] = (
    hybrid[
        "m0_roll_deg"
    ]
)


hybrid[
    "m2par_square_vfov_deg"
] = (
    hybrid[
        "m0_square_vfov_deg"
    ]
)


pitch_use_m1 = (
    hybrid[
        "category"
    ]
    .isin(
        ACTIVE_PITCH_CATEGORIES
    )
)


hybrid[
    "pitch_route"
] = np.where(

    pitch_use_m1,

    "M1-v4",

    "M0",
)


hybrid[
    "m2par_pitch_deg"
] = np.where(

    pitch_use_m1,

    hybrid[
        "m1v4_pitch_deg"
    ],

    hybrid[
        "m0_pitch_deg"
    ],
)


# ==========================================================================================
# 10. CALCULATE DEVELOPMENT OOF PERFORMANCE OF FROZEN M2-PAR RULE
#
# NOTE:
#   This is DEVELOPMENT evidence only.
#   It is not an independent validation because M2-PAR was formulated
#   after R16.
# ==========================================================================================

M2_COLS = {

    "roll":
        "m2par_roll_deg",

    "pitch":
        "m2par_pitch_deg",

    "vfov":
        "m2par_square_vfov_deg",
}


summary_rows = []


for param, spec in (
    PARAMS.items()
):

    mask = (
        hybrid[
            spec[
                "target"
            ]
        ].notna()
    )


    d = (
        hybrid[
            mask
        ]
        .copy()
    )


    y = (
        d[
            spec[
                "target"
            ]
        ]
        .to_numpy(
            dtype=float
        )
    )


    p0 = (
        d[
            spec[
                "m0"
            ]
        ]
        .to_numpy(
            dtype=float
        )
    )


    p2 = (
        d[
            M2_COLS[
                param
            ]
        ]
        .to_numpy(
            dtype=float
        )
    )


    e0 = np.abs(
        p0
        -
        y
    )


    e2 = np.abs(
        p2
        -
        y
    )


    m0_mae = float(
        e0.mean()
    )


    m2_mae = float(
        e2.mean()
    )


    summary_rows.append(
        {

            "parameter":
                param,

            "n":
                len(
                    d
                ),

            "locations":
                d[
                    "location_id"
                ].nunique(),

            "M0_MAE":
                m0_mae,

            "M2PAR_MAE":
                m2_mae,

            "delta_M2PAR_minus_M0":
                (
                    m2_mae
                    -
                    m0_mae
                ),

            "relative_change_pct":
                (
                    (
                        m2_mae
                        /
                        m0_mae
                    )
                    -
                    1
                )
                *
                100.0,
        }
    )


m2_summary = pd.DataFrame(
    summary_rows
)


# ==========================================================================================
# 11. VERIFY M2-PAR PITCH EXACTLY MATCHES R16 CROSS-FITTED PITCH ROUTING
#
# Since all 4 held-out folds independently selected the same pitch rule,
# fixed M2-PAR should reproduce the R16 cross-fitted pitch result exactly.
# ==========================================================================================

r16_pitch = (
    r16_summary[
        r16_summary[
            "parameter"
        ]
        ==
        "pitch"
    ]
)


assert (
    len(
        r16_pitch
    )
    ==
    1
)


r16_pitch_mae = float(
    r16_pitch[
        "routed_MAE"
    ]
    .iloc[
        0
    ]
)


m2_pitch_mae = float(
    m2_summary.loc[
        m2_summary[
            "parameter"
        ]
        ==
        "pitch",
        "M2PAR_MAE",
    ]
    .iloc[
        0
    ]
)


assert (
    abs(
        r16_pitch_mae
        -
        m2_pitch_mae
    )
    <
    1e-12
), (
    "Fixed M2-PAR pitch does not "
    "match R16 cross-fitted pitch."
)


print(
    "\nM2-PAR FIXED RULE REPRODUCES "
    "R16 CROSS-FITTED PITCH EXACTLY: PASSED"
)


# ==========================================================================================
# 12. LOCATION-CLUSTER BOOTSTRAP FOR DEVELOPMENT PITCH EFFECT
#
# Descriptive only.
# Not the final test.
# ==========================================================================================

pitch_mask = (
    hybrid[
        "target_pitch_deg"
    ].notna()
)


pitch_df = (
    hybrid[
        pitch_mask
    ]
    .copy()
)


pitch_df[
    "_m0_error"
] = np.abs(
    pitch_df[
        "m0_pitch_deg"
    ]
    -
    pitch_df[
        "target_pitch_deg"
    ]
)


pitch_df[
    "_m2_error"
] = np.abs(
    pitch_df[
        "m2par_pitch_deg"
    ]
    -
    pitch_df[
        "target_pitch_deg"
    ]
)


cluster = (
    pitch_df
    .groupby(
        "location_id",
        sort=True,
    )
    .agg(

        n=(
            "_m0_error",
            "size"
        ),

        sum_m0=(
            "_m0_error",
            "sum"
        ),

        sum_m2=(
            "_m2_error",
            "sum"
        ),
    )
    .reset_index()
)


rng = np.random.default_rng(
    SEED
)


K = len(
    cluster
)


cn = (
    cluster[
        "n"
    ]
    .to_numpy(
        float
    )
)


c0 = (
    cluster[
        "sum_m0"
    ]
    .to_numpy(
        float
    )
)


c2 = (
    cluster[
        "sum_m2"
    ]
    .to_numpy(
        float
    )
)


boot_delta = np.empty(
    BOOTSTRAP_B,
    dtype=float,
)


for b in range(
    BOOTSTRAP_B
):

    s = rng.integers(
        0,
        K,
        size=K,
    )


    N = (
        cn[
            s
        ]
        .sum()
    )


    m0_b = (
        c0[
            s
        ]
        .sum()
        /
        N
    )


    m2_b = (
        c2[
            s
        ]
        .sum()
        /
        N
    )


    boot_delta[
        b
    ] = (
        m2_b
        -
        m0_b
    )


ci_low, ci_high = np.percentile(
    boot_delta,
    [
        2.5,
        97.5,
    ],
)


boot_prob = float(
    np.mean(
        boot_delta
        <
        0
    )
)


bootstrap_record = {

    "parameter":
        "pitch",

    "clusters":
        K,

    "bootstrap_B":
        BOOTSTRAP_B,

    "delta_CI95_low":
        float(
            ci_low
        ),

    "delta_CI95_high":
        float(
            ci_high
        ),

    "bootstrap_probability_M2PAR_better":
        boot_prob,
}


# ==========================================================================================
# 13. PRINT DEVELOPMENT EVIDENCE
# ==========================================================================================

pd.set_option(
    "display.width",
    220
)


pd.set_option(
    "display.max_columns",
    50
)


print(
    "\n"
    +
    "=" * 108
)


print(
    "M2-PAR DEVELOPMENT OOF SUMMARY"
)


print(
    "=" * 108
)


print(
    m2_summary
    .to_string(
        index=False,
        float_format=lambda x:
            f"{x:.6f}",
    )
)


print(
    "\nPITCH DEVELOPMENT CLUSTER BOOTSTRAP:"
)


print(
    json.dumps(
        bootstrap_record,
        indent=2,
    )
)


# ==========================================================================================
# 14. FREEZE M2-PAR SYSTEM DEFINITION
# ==========================================================================================

M2_SYSTEM = {

    "system_name":
        "M2-PAR",

    "full_name":
        (
            "Parameter-Aware Routing "
            "Hybrid System"
        ),

    "status":
        "FROZEN_CANDIDATE_BEFORE_FINAL_TEST",

    "relationship_to_R17":
        {
            "M1_v4_unified_branch_reopened":
                False,

            "category_expert_branch_reopened":
                False,

            "interpretation":
                (
                    "M1-v4 is used only as a "
                    "pitch specialist component "
                    "inside a new system-level "
                    "parameter-aware architecture."
                ),
        },

    "roll":
        {
            "source":
                "M0",

            "routing":
                "none",
        },

    "square_vfov":
        {
            "source":
                "M0",

            "routing":
                "none",
        },

    "pitch":
        {
            "event":
                "M1-v4 specialist",

            "heritage":
                "M1-v4 specialist",

            "natural":
                "M0",

            "purpose_built":
                "M0",
        },

    "pitch_rule_evidence":
        {
            "cross_fitted_rule_stable_across_all_4_folds":
                True,

            "event_route_consistency":
                "4/4 M1-v4",

            "heritage_route_consistency":
                "4/4 M1-v4",

            "natural_route_consistency":
                "4/4 M0",

            "purpose_built_route_consistency":
                "4/4 M0",
        },

    "development_evidence_status":
        (
            "post-hoc model-development evidence; "
            "not independent confirmation"
        ),

    "Stable101_used_for_M2_design":
        False,

    "test239_used_for_M2_design":
        False,
}


(
    OUT /
    "R18_M2PAR_system_definition.json"
).write_text(
    json.dumps(
        M2_SYSTEM,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ==========================================================================================
# 15. FREEZE FINAL FULL-DATA TRAINING PLAN
#
# Only the M1-v4 specialist component must be trained.
#
# IMPORTANT:
#   This is NOT another architecture search.
#   Exact configuration = already-frozen v4 configuration.
# ==========================================================================================

FINAL_TRAINING_PLAN = {

    "component_name":
        "M1-v4-full-development-pitch-specialist",

    "role":
        (
            "Generate pitch candidate only "
            "for event and heritage rows."
        ),

    "training_data":
        {
            "primary":
                526,

            "aux":
                216,

            "total":
                742,
        },

    "RADIO":
        "Puffin-Base exact cache; frozen",

    "Projector":
        "Puffin-Base; frozen",

    "Qwen":
        "Puffin-Base Qwen2.5-1.5B",

    "trainable":
        "q/k/v/o LoRA only",

    "LoRA_r":
        8,

    "LoRA_alpha":
        16,

    "LoRA_dropout":
        0.05,

    "learning_rate":
        1e-5,

    "weight_decay":
        0.01,

    "gradient_accumulation":
        16,

    "gradient_clip":
        1.0,

    "epochs":
        3,

    "epoch_selection":
        "epoch 3 prelocked",

    "primary_row_weight":
        1.0,

    "aux_row_weight":
        0.4,

    "caption_token_weight":
        0.25,

    "camera_token_weight":
        1.0,

    "geometry_head":
        False,

    "geometry_loss":
        False,

    "corrected_square_vfov_target":
        True,

    "missing_primary_parameter":
        "M0 self-distillation in text only",

    "no_hyperparameter_changes_after_R18":
        True,

    "Stable101_for_selection":
        False,

    "test239_for_training":
        False,
}


(
    OUT /
    "R18_final_training_plan.json"
).write_text(
    json.dumps(
        FINAL_TRAINING_PLAN,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ==========================================================================================
# 16. PRECOMMIT FINAL TEST239 PROTOCOL
#
# test239 is still NOT touched here.
#
# Primary confirmation:
#
# P1. M1-v4 specialist camera parsing succeeds for every test row on
#     which M2-PAR requires M1-v4 pitch.
#
# P2. M2-PAR pitch MAE < M0 pitch MAE on test239.
#
# P3. roll output equals M0 exactly by construction.
#
# P4. square-vFoV output equals M0 exactly by construction.
#
# No rule/model/epoch changes after seeing test239.
# ==========================================================================================

FINAL_TEST_PLAN = {

    "dataset":
        "test239",

    "status_at_R18":
        "PRISTINE_UNTOUCHED",

    "evaluation_count":
        "ONE formal evaluation after full model freeze",

    "M2_PAR_rule":
        {
            "roll":
                "M0",

            "square_vfov":
                "M0",

            "pitch_event":
                "M1-v4-full-development",

            "pitch_heritage":
                "M1-v4-full-development",

            "pitch_natural":
                "M0",

            "pitch_purpose_built":
                "M0",
        },

    "primary_confirmation_conditions":
        {

            "P1":
                (
                    "M1-v4 pitch specialist "
                    "parse rate = 1.0 on all "
                    "rows requiring specialist pitch"
                ),

            "P2":
                (
                    "M2-PAR test239 pitch MAE "
                    "< M0 test239 pitch MAE"
                ),

            "P3":
                (
                    "M2-PAR roll predictions "
                    "are exactly M0 predictions"
                ),

            "P4":
                (
                    "M2-PAR square-vFoV predictions "
                    "are exactly M0 predictions"
                ),
        },

    "primary_success":
        "P1 AND P2 AND P3 AND P4",

    "secondary_analysis":
        [
            (
                "paired pitch error delta"
            ),

            (
                "pitch result by category"
            ),

            (
                "bootstrap uncertainty reported "
                "descriptively"
            ),
        ],

    "forbidden_after_test_reveal":
        [
            "change pitch category routes",

            "change LoRA hyperparameters",

            "change epoch",

            "blend M0 and M1-v4",

            "select subsets based on test error",

            "return to Stable101",
        ],
}


(
    OUT /
    "R18_test239_precommit.json"
).write_text(
    json.dumps(
        FINAL_TEST_PLAN,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ==========================================================================================
# 17. SAVE DEVELOPMENT TABLES
# ==========================================================================================

routing_stability.to_csv(
    OUT /
    "R18_pitch_routing_stability.csv",
    index=False,
)


m2_summary.to_csv(
    OUT /
    "R18_M2PAR_development_OOF_summary.csv",
    index=False,
)


hybrid[
    [
        "id",
        "global_index",
        "location_id",
        "category",
        "outer_fold",

        "target_roll_deg",
        "target_pitch_deg",
        "target_square_vfov_deg",

        "m0_roll_deg",
        "m0_pitch_deg",
        "m0_square_vfov_deg",

        "m1v4_roll_deg",
        "m1v4_pitch_deg",
        "m1v4_square_vfov_deg",

        "pitch_route",

        "m2par_roll_deg",
        "m2par_pitch_deg",
        "m2par_square_vfov_deg",
    ]
].to_csv(
    OUT /
    "R18_M2PAR_development_OOF_predictions.csv",
    index=False,
)


(
    OUT /
    "R18_pitch_bootstrap.json"
).write_text(
    json.dumps(
        bootstrap_record,
        indent=2,
    ),
    encoding="utf-8",
)


pd.DataFrame(
    integrity_rows
).to_csv(
    OUT /
    "R18_source_integrity.csv",
    index=False,
)


# ==========================================================================================
# 18. README
# ==========================================================================================

README = """
Tourism-Puffin R18
M2-PAR PARAMETER-AWARE HYBRID FREEZE
================================================

BACKGROUND
----------
R14 showed that unified M1-v4 did not outperform M0
across roll, pitch and square-vFoV.

R16 then tested tourism-category routing cross-fitted.
The whole category-routing system failed because roll
and square-vFoV regressed.

However, the pitch routing rule was identical in all
four held-out folds:

event         -> M1-v4
heritage      -> M1-v4
natural       -> M0
purpose_built -> M0

Pitch routing improved in all four held-out folds.


NEW SYSTEM
----------
M2-PAR is a NEW system architecture.

Roll:
M0 only.

Square-vFoV:
M0 only.

Pitch:
event / heritage -> M1-v4 specialist
natural / purpose_built -> M0


IMPORTANT INTERPRETATION
------------------------
M1-v4 is NOT reinstated as a unified three-parameter model.

The R17 closure remains valid.

M1-v4 is only retained as a specialist component for pitch
inside the newly defined parameter-aware hybrid system.


DEVELOPMENT / CONFIRMATION SEPARATION
-------------------------------------
The 431-row OOF evidence is model-development evidence.
M2-PAR was formulated after inspecting R16.

Therefore the OOF result cannot serve as independent
confirmation of M2-PAR.

test239 remains completely untouched at R18.


NEXT GPU STEP
-------------
Train exactly ONE full-development M1-v4 component:

526 primary + 216 aux
RADIO frozen
Projector frozen
q/k/v/o LoRA only
r=8
alpha=16
dropout=.05
LR=1e-5
3 epochs
Epoch 3 prelocked

No Stable101.
No epoch selection.
No hyperparameter search.


FINAL TEST
----------
After that component is frozen, evaluate test239 ONCE.

Primary M2-PAR confirmation requires:

1. specialist pitch parse rate = 1.0 where needed;
2. M2-PAR pitch MAE < M0 pitch MAE;
3. roll remains exactly M0;
4. square-vFoV remains exactly M0.

No model or routing changes after test reveal.
""".strip()


(
    OUT /
    "README_R18.txt"
).write_text(
    README,
    encoding="utf-8",
)


# ==========================================================================================
# 19. SHA256 MANIFEST
# ==========================================================================================

files = sorted(
    [

        p

        for p in OUT.iterdir()

        if (
            p.is_file()
            and
            p.name
            !=
            "sha256_manifest.json"
        )
    ],

    key=lambda p:
        p.name,
)


manifest_out = {}


for p in files:

    manifest_out[
        p.name
    ] = sha256_file(
        p
    )


MANIFEST_PATH = (
    OUT /
    "sha256_manifest.json"
)


MANIFEST_PATH.write_text(
    json.dumps(
        manifest_out,
        indent=2,
    ),
    encoding="utf-8",
)


manifest_sha = (
    sha256_file(
        MANIFEST_PATH
    )
)


# ==========================================================================================
# 20. FINAL PRE-UPLOAD ASSERTIONS
# ==========================================================================================

roll_delta = float(
    m2_summary.loc[
        m2_summary[
            "parameter"
        ]
        ==
        "roll",
        "delta_M2PAR_minus_M0",
    ]
    .iloc[
        0
    ]
)


pitch_delta = float(
    m2_summary.loc[
        m2_summary[
            "parameter"
        ]
        ==
        "pitch",
        "delta_M2PAR_minus_M0",
    ]
    .iloc[
        0
    ]
)


vfov_delta = float(
    m2_summary.loc[
        m2_summary[
            "parameter"
        ]
        ==
        "vfov",
        "delta_M2PAR_minus_M0",
    ]
    .iloc[
        0
    ]
)


assert (
    abs(
        roll_delta
    )
    <
    1e-15
)


assert (
    pitch_delta
    <
    0
)


assert (
    abs(
        vfov_delta
    )
    <
    1e-15
)


assert (
    FINAL_TEST_PLAN[
        "dataset"
    ]
    ==
    "test239"
)


assert (
    FINAL_TEST_PLAN[
        "status_at_R18"
    ]
    ==
    "PRISTINE_UNTOUCHED"
)


print(
    "\nR18 SYSTEM FREEZE ASSERTIONS: PASSED"
)


# ==========================================================================================
# 21. UPLOAD PERMANENT R18 ARCHIVE
# ==========================================================================================

print(
    "\nUPLOADING R18 PERMANENT ARCHIVE..."
)


kagglehub.dataset_upload(

    SAVE_HANDLE,

    str(
        OUT
    ),

    version_notes=(
        "R18 freeze M2-PAR parameter-aware hybrid; "
        "pitch event/heritage -> M1-v4 specialist; "
        "roll/vFoV remain M0; "
        "test239 untouched"
    ),
)


print(
    "R18_UPLOAD_REQUEST_COMPLETE"
)


# ==========================================================================================
# 22. REMOTE SHA VERIFY
# ==========================================================================================

verify_map = dict(
    manifest_out
)


verify_map[
    "sha256_manifest.json"
] = manifest_sha


verified = False


for attempt in range(
    1,
    21,
):

    try:

        remote = (
            dataset_download_fresh(
                SAVE_HANDLE
            )
        )


        okay = True


        for (
            filename,
            expected_sha
        ) in verify_map.items():

            p = find_file(
                remote,
                filename
            )


            actual_sha = (
                sha256_file(
                    p
                )
            )


            if (
                actual_sha
                !=
                expected_sha
            ):

                okay = False

                print(
                    "Remote SHA mismatch:",
                    filename
                )

                break


        if okay:

            verified = True
            break


    except Exception as e:

        print(
            f"Waiting for R18 Dataset "
            f"{attempt}/20 | "
            f"{repr(e)}"
        )


    time.sleep(
        10
    )


assert (
    verified
)


print(
    "R18_ALL_REMOTE_SHA256_VERIFIED"
)


# ==========================================================================================
# 23. FINAL REPORT
# ==========================================================================================

print(
    "\n"
    +
    "#" * 108
)


print(
    "R18_M2PAR_FREEZE_COMPLETE"
)


print(
    "#" * 108
)


print(
    "System:",
    "M2-PAR"
)


print(
    "Roll:",
    "M0"
)


print(
    "Pitch event:",
    "M1-v4 specialist"
)


print(
    "Pitch heritage:",
    "M1-v4 specialist"
)


print(
    "Pitch natural:",
    "M0"
)


print(
    "Pitch purpose_built:",
    "M0"
)


print(
    "Square-vFoV:",
    "M0"
)


print(
    "\nDevelopment OOF pitch MAE:"
)


print(
    "M0:",
    float(
        m2_summary.loc[
            m2_summary[
                "parameter"
            ]
            ==
            "pitch",
            "M0_MAE",
        ]
        .iloc[
            0
        ]
    )
)


print(
    "M2-PAR:",
    m2_pitch_mae
)


print(
    "Pitch delta:",
    pitch_delta
)


print(
    "Pitch bootstrap CI95:",
    (
        float(
            ci_low
        ),
        float(
            ci_high
        )
    )
)


print(
    "\nM1-v4 unified branch reopened:",
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
    "Final test239 rule frozen:",
    True
)


print(
    "\nNEXT GPU STEP:"
)


print(
    "Train ONE full-development "
    "M1-v4 specialist component "
    "on 526 primary + 216 aux."
)


print(
    "Same frozen R13-v4 configuration."
)


print(
    "Epoch 3 only."
)


print(
    "No Stable101 and no model selection."
)


print(
    "#" * 108
)