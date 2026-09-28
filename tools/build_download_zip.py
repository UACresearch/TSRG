"""Build a lean, allowlisted, reproducible TSRG private download candidate.

No historical notebooks, personal data, test prediction rows, raw photographs or
model binaries are included. This is intentionally not a whole-repository zip.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "TSRG-inference-v0.1.0-rc1"
FIXED_ZIP_TIME = (2026, 9, 28, 0, 0, 0)

# archive relative path => source repository relative path
ALLOWLIST = {
    "README.md": "DOWNLOAD_README_CN.md",
    "LICENSE": "LICENSE",
    "THIRD_PARTY_NOTICES.md": "THIRD_PARTY_NOTICES.md",
    "requirements-inference.txt": "requirements-inference.txt",
    "requirements-dev.txt": "requirements-dev.txt",
    "tsrg/__init__.py": "tsrg/__init__.py",
    "tsrg/inference.py": "tsrg/inference.py",
    "tsrg/routing.py": "tsrg/routing.py",
    "tsrg/camera.py": "tsrg/camera.py",
    "tsrg/evaluation.py": "tsrg/evaluation.py",
    "tests/test_inference.py": "tests/test_inference.py",
    "tests/test_routing.py": "tests/test_routing.py",
    "tests/test_camera.py": "tests/test_camera.py",
    "tests/test_evaluation.py": "tests/test_evaluation.py",
}
MANIFEST = "MANIFEST_SHA256.txt"


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _add(z: zipfile.ZipFile, path: str, content: bytes) -> None:
    info = zipfile.ZipInfo(f"{PACKAGE_NAME}/{path}", date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    z.writestr(info, content)


def build_archive(output_dir: Path, source_root: Path = ROOT) -> Path:
    """Write the curated ZIP with hashes; reject missing files and symlinks."""
    members = {}
    source_root = source_root.resolve()
    for dest, src in sorted(ALLOWLIST.items()):
        file = source_root / src
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(source_root):
            raise FileNotFoundError(f"Missing, linked or unsafe required source: {src}")
        members[dest] = file.read_bytes()
    manifest = "".join(f"{_digest(members[name])}  {name}\n" for name in sorted(members))
    members[MANIFEST] = manifest.encode("utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{PACKAGE_NAME}.zip"
    with zipfile.ZipFile(target, "w") as z:
        for name, content in sorted(members.items()):
            _add(z, name, content)
    verify_archive(target)
    return target


def verify_archive(target: Path) -> None:
    """Check exact member set, names and every recorded SHA256."""
    expected = {f"{PACKAGE_NAME}/{name}" for name in (*ALLOWLIST, MANIFEST)}
    with zipfile.ZipFile(target) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or set(names) != expected:
            raise ValueError("Download ZIP member list differs from allowlist")
        if z.testzip() is not None:
            raise ValueError("Download ZIP CRC error")
        manifest = z.read(f"{PACKAGE_NAME}/{MANIFEST}").decode("utf-8").splitlines()
        digests = {}
        for entry in manifest:
            digest, name = entry.split("  ", 1)
            if len(digest) != 64 or name in digests:
                raise ValueError("Invalid manifest")
            digests[name] = digest
        if set(digests) != set(ALLOWLIST):
            raise ValueError("Manifest differs from allowlist")
        for name, expected_digest in digests.items():
            if _digest(z.read(f"{PACKAGE_NAME}/{name}")) != expected_digest:
                raise ValueError(f"SHA256 mismatch in ZIP: {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or verify TSRG private inference download ZIP")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--verify", type=Path, help="Verify an existing package instead of building")
    args = parser.parse_args()
    if args.verify is not None:
        verify_archive(args.verify)
        print(f"Verified: {args.verify}")
    else:
        path = build_archive(args.output_dir)
        print(f"Built and SHA256-verified: {path}")
        print(f"ZIP SHA256: {_digest(path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
