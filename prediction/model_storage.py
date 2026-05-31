"""
Download and validate the ML model file for local dev and Railway deploys.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from pathlib import Path

LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1"
GITHUB_LFS_REPO = os.environ.get(
    "GITHUB_LFS_REPO",
    "https://github.com/ThomasR1os/prediccion-almacen.git",
)
MODEL_LFS_OID = "ca2f359502ead12d69c496626f6b116dd59287768b2638ad03aff874be0ba722"
MODEL_LFS_SIZE = 314638129
DOWNLOAD_CHUNK_SIZE = 8 * 1024 * 1024


def is_git_lfs_pointer(path: Path | str) -> bool:
    model_path = Path(path)
    if not model_path.is_file():
        return False
    with model_path.open("rb") as handle:
        return handle.read(len(LFS_PREFIX)) == LFS_PREFIX


def _file_size(path: Path | str) -> int:
    return Path(path).stat().st_size


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(DOWNLOAD_CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def model_file_available(model_path: Path | str) -> bool:
    model_path = Path(model_path)
    if not model_path.is_file() or is_git_lfs_pointer(model_path):
        return False
    return _file_size(model_path) == MODEL_LFS_SIZE


def invalidate_model(model_path: Path | str) -> None:
    model_path = Path(model_path)
    if model_path.is_file():
        print(f"Removing invalid model file: {model_path}")
        model_path.unlink()


def _download_stream(dest: Path, url: str, expected_size: int | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest.with_suffix(dest.suffix + ".part")
    if temp_path.exists():
        temp_path.unlink()

    print(f"Downloading model ({expected_size or 'unknown'} bytes expected) ...")
    request = urllib.request.Request(url, headers={"User-Agent": "git-lfs/3.0.0"})
    with urllib.request.urlopen(request, timeout=300) as response:
        content_length = response.headers.get("Content-Length")
        if expected_size and content_length and int(content_length) != expected_size:
            raise RuntimeError(
                f"Unexpected Content-Length {content_length}; expected {expected_size}."
            )

        written = 0
        with temp_path.open("wb") as handle:
            while True:
                chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                handle.write(chunk)
                written += len(chunk)

    if expected_size and written != expected_size:
        temp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Incomplete download: got {written} bytes, expected {expected_size}."
        )

    temp_path.replace(dest)
    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"Model downloaded ({size_mb:.1f} MB).")


def _download_from_github_lfs(dest: Path) -> None:
    batch_url = f"{GITHUB_LFS_REPO.rstrip('/')}/info/lfs/objects/batch"
    payload = json.dumps(
        {
            "operation": "download",
            "transfers": ["basic"],
            "objects": [{"oid": MODEL_LFS_OID, "size": MODEL_LFS_SIZE}],
        }
    ).encode()
    request = urllib.request.Request(
        batch_url,
        data=payload,
        headers={
            "Accept": "application/vnd.git-lfs+json",
            "Content-Type": "application/vnd.git-lfs+json",
            "User-Agent": "git-lfs/3.0.0",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read())

    obj = data["objects"][0]
    error = obj.get("error")
    if error:
        raise RuntimeError(f"GitHub LFS error: {error}")

    download_url = obj["actions"]["download"]["href"]
    _download_stream(dest, download_url, expected_size=MODEL_LFS_SIZE)

    if _sha256(dest) != MODEL_LFS_OID:
        dest.unlink(missing_ok=True)
        raise RuntimeError("Downloaded model failed SHA-256 checksum verification.")


def ensure_model(
    model_path: Path | str,
    model_url: str | None = None,
    *,
    force: bool = False,
) -> None:
    model_path = Path(model_path)
    model_url = (model_url or os.environ.get("MODEL_URL", "")).strip()

    if not force and model_file_available(model_path):
        print(f"Model OK: {model_path}")
        return

    if model_path.is_file():
        invalidate_model(model_path)

    print(f"Model missing or invalid at {model_path}.")

    if model_url:
        _download_stream(model_path, model_url, expected_size=MODEL_LFS_SIZE)
    else:
        print("Fetching model from GitHub LFS ...")
        _download_from_github_lfs(model_path)

    if not model_file_available(model_path):
        raise RuntimeError(
            f"Model at {model_path} is invalid after download "
            f"(size {_file_size(model_path) if model_path.is_file() else 0}, "
            f"expected {MODEL_LFS_SIZE}). "
            "Set MODEL_URL in Railway to a direct download link."
        )
