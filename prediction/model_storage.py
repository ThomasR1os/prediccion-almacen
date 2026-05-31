"""
Download and validate the ML model file for local dev and Railway deploys.
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path

LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1"
MIN_MODEL_BYTES = 1_000_000
GITHUB_LFS_REPO = os.environ.get(
    "GITHUB_LFS_REPO",
    "https://github.com/ThomasR1os/prediccion-almacen.git",
)
MODEL_LFS_OID = "ca2f359502ead12d69c496626f6b116dd59287768b2638ad03aff874be0ba722"
MODEL_LFS_SIZE = 314638129


def is_git_lfs_pointer(path: Path | str) -> bool:
    model_path = Path(path)
    if not model_path.is_file():
        return False
    with model_path.open("rb") as handle:
        return handle.read(len(LFS_PREFIX)) == LFS_PREFIX


def model_file_available(model_path: Path | str) -> bool:
    model_path = Path(model_path)
    return (
        model_path.is_file()
        and not is_git_lfs_pointer(model_path)
        and model_path.stat().st_size >= MIN_MODEL_BYTES
    )


def _pull_lfs_objects(relative_path: str) -> bool:
    try:
        subprocess.run(["git", "lfs", "install"], check=False, capture_output=True)
        result = subprocess.run(
            ["git", "lfs", "pull", "--include", relative_path],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 and result.stderr.strip():
            print(result.stderr.strip())
        return result.returncode == 0
    except FileNotFoundError:
        print("git-lfs not available in PATH.")
        return False


def _download_from_url(dest: Path, url: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading model from {url} ...")
    urllib.request.urlretrieve(url, dest)
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
    _download_from_url(dest, download_url)


def ensure_model(model_path: Path | str, model_url: str | None = None) -> None:
    model_path = Path(model_path)
    model_url = (model_url or os.environ.get("MODEL_URL", "")).strip()
    relative_path = model_path.as_posix().lstrip("./")

    if model_file_available(model_path):
        print(f"Model OK: {model_path}")
        return

    if is_git_lfs_pointer(model_path):
        print(f"Detected Git LFS pointer at {model_path}.")
    elif not model_path.is_file():
        print(f"Model missing at {model_path}.")
    else:
        print(f"Model file too small ({model_path.stat().st_size} bytes).")

    if _pull_lfs_objects(relative_path) and model_file_available(model_path):
        print(f"Model fetched via git lfs: {model_path}")
        return

    if model_url:
        _download_from_url(model_path, model_url)
    else:
        print("Fetching model from GitHub LFS ...")
        _download_from_github_lfs(model_path)

    if not model_file_available(model_path):
        raise RuntimeError(
            f"Model at {model_path} is invalid after download. "
            "Set MODEL_URL in Railway to a direct download link."
        )
