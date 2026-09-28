"""CPU-only contract tests for the new-photo inference entrypoint."""
import math
from types import SimpleNamespace
from pathlib import Path

import pytest

from tsrg.inference import (
    PROMPT, R19_ADAPTER_SHA256, choose_compute_dtype, parse_camera_text, sha256_file, validate_assets,
)
from tsrg.routing import CameraPrediction, m2_par_prediction


def test_camera_parse_radians_to_degrees():
    text = "Other text. Camera parameters are: 0.1, -0.2, 0.8"
    value = parse_camera_text(text)
    assert value.roll_deg == pytest.approx(math.degrees(0.1))
    assert value.pitch_deg == pytest.approx(math.degrees(-0.2))
    assert value.square_vfov_deg == pytest.approx(math.degrees(0.8))


def test_last_camera_triple_is_used():
    text = "Camera parameters are: 0,0,1. Camera parameters are: 0.1,0.2,0.9"
    assert parse_camera_text(text).pitch_deg == pytest.approx(math.degrees(0.2))


def test_bad_outputs_do_not_silently_become_numbers():
    with pytest.raises(ValueError, match="not found"):
        parse_camera_text("Camera parameters unknown")
    with pytest.raises(ValueError, match="Non-finite"):
        parse_camera_text("Camera parameters are: 1e999, 0.2, 0.8")


def test_frozen_prompt_and_digest_contract():
    assert PROMPT == ("Describe the image in detail. Then reason its spatial distribution and estimate "
                      "its camera parameters (roll, pitch, and field-of-view).")
    assert len(R19_ADAPTER_SHA256) == 64


def test_preflight_rejects_missing_assets(tmp_path):
    with pytest.raises(FileNotFoundError, match="puffin-source"):
        validate_assets(tmp_path, tmp_path / "Puffin-Base.pth", tmp_path / "adapter")


def test_sha256_file(tmp_path):
    target = tmp_path / "sample.bin"
    target.write_bytes(b"TSRG")
    import hashlib
    assert sha256_file(target) == hashlib.sha256(b"TSRG").hexdigest()


@pytest.mark.parametrize("category,expected_source", [
    ("event", "r19"), ("heritage", "r19"),
    ("natural", "m0"), ("purpose_built", "m0"),
])
def test_frozen_routing_behavior(category, expected_source):
    m0 = CameraPrediction(1.1, -1.2, 50.0)
    specialist = 3.2 if expected_source == "r19" else None
    result = m2_par_prediction(category, m0, specialist)
    assert result.roll_deg == 1.1
    assert result.square_vfov_deg == 50.0
    assert result.pitch_deg == (3.2 if expected_source == "r19" else -1.2)


def test_new_photo_dtype_for_two_t4_cards():
    fake = SimpleNamespace(
        cuda=SimpleNamespace(get_device_capability=lambda i: (7, 5)),
        bfloat16="BF16", float16="FP16",
    )
    assert choose_compute_dtype(fake) == "FP16"


def test_new_photo_dtype_for_two_native_bf16_cards():
    fake = SimpleNamespace(
        cuda=SimpleNamespace(get_device_capability=lambda i: (8, 0)),
        bfloat16="BF16", float16="FP16",
    )
    assert choose_compute_dtype(fake) == "BF16"


def test_mixed_devices_use_fp16():
    fake = SimpleNamespace(
        cuda=SimpleNamespace(get_device_capability=lambda i: (8, 0) if i == 0 else (7, 5)),
        bfloat16="BF16", float16="FP16",
    )
    assert choose_compute_dtype(fake) == "FP16"
