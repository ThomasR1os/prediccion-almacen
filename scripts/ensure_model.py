"""
Ensure the ML model file is present and is not a Git LFS pointer.

Railway (and other CI) often clone the repo without pulling LFS objects.
The pointer text starts with 'version https://git-lfs...' which causes
KeyError: 118 when joblib tries to unpickle it.
"""
from __future__ import annotations

import os
import subprocess
import sys
import urllib.request
from pathlib import Path

LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1"
MIN_MODEL_BYTES = 1_000_000


def is_git_lfs_pointer(path: Path) -> bool:
    if not path.is_file():
        return False
    with path.open("rb") as handle:
        return handle.read(len(LFS_PREFIX)) == LFS_PREFIX


def pull_lfs_objects() -> bool:
    try:
        subprocess.run(["git", "lfs", "install"], check=False, capture_output=True)
        result = subprocess.run(
            ["git", "lfs", "pull", "--include", "prediction/modelo_random_forest_new.pkl"],
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


def download_model(dest: Path, url: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading model from {url} ...")
    urllib.request.urlretrieve(url, dest)
    size_mb = dest.stat().st_size / (1024 * 1024)
    print(f"Model downloaded ({size_mb:.1f} MB).")


def ensure_model(model_path: Path, model_url: str | None = None) -> None:
    model_url = model_url or os.environ.get("MODEL_URL", "").strip()

    if model_path.is_file() and not is_git_lfs_pointer(model_path):
        if model_path.stat().st_size >= MIN_MODEL_BYTES:
            print(f"Model OK: {model_path}")
            return
        print(f"Model file too small ({model_path.stat().st_size} bytes), re-fetching.")

    if is_git_lfs_pointer(model_path):
        print(f"Detected Git LFS pointer at {model_path}.")

    if pull_lfs_objects() and model_path.is_file() and not is_git_lfs_pointer(model_path):
        if model_path.stat().st_size >= MIN_MODEL_BYTES:
            print(f"Model fetched via git lfs: {model_path}")
            return

    if model_url:
        download_model(model_path, model_url)
    else:
        raise RuntimeError(
            f"Model at {model_path} is missing or still a Git LFS pointer. "
            "Run 'git lfs pull' locally before deploy, or set MODEL_URL in Railway "
            "to a direct download link for modelo_random_forest_new.pkl."
        )

    if is_git_lfs_pointer(model_path) or model_path.stat().st_size < MIN_MODEL_BYTES:
        raise RuntimeError(
            f"Model at {model_path} is invalid after download. "
            "Check MODEL_URL or upload the .pkl to Railway as a volume."
        )


def main() -> int:
    base_dir = Path(__file__).resolve().parent.parent
    model_path = Path(
        os.environ.get(
            "MODEL_PATH",
            base_dir / "prediction" / "modelo_random_forest_new.pkl",
        )
    )
    try:
        ensure_model(model_path)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
