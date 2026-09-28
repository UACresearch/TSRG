"""Ensure the distributable ZIP excludes research archives and verifies all hashes."""
from pathlib import Path
import zipfile

import pytest

from tools.build_download_zip import (
    ALLOWLIST, MANIFEST, PACKAGE_NAME, build_archive, verify_archive,
)


def test_curated_zip_only_contains_allowlisted_files(tmp_path):
    target = build_archive(tmp_path)
    verify_archive(target)
    with zipfile.ZipFile(target) as archive:
        names = archive.namelist()
        assert len(names) == len(ALLOWLIST) + 1
        assert f"{PACKAGE_NAME}/README.md" in names
        assert f"{PACKAGE_NAME}/tsrg/inference.py" in names
        assert f"{PACKAGE_NAME}/{MANIFEST}" in names
        for forbidden in (
            "/reproduction/", "/results/", "/artifacts/", "/.github/",
            "adapter_model.safetensors", "Puffin-Base.pth", ".ipynb",
        ):
            assert not any(forbidden in "/" + name for name in names)


def test_download_zip_is_deterministic(tmp_path):
    first = build_archive(tmp_path / "one")
    second = build_archive(tmp_path / "two")
    assert first.read_bytes() == second.read_bytes()


def test_missing_file_fails_closed(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_archive(tmp_path / "out", source_root=tmp_path)
