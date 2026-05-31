"""CLI wrapper to ensure the ML model file exists before serving traffic."""
from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from prediction.model_storage import ensure_model  # noqa: E402


def main() -> int:
    model_path = Path(
        os.environ.get(
            "MODEL_PATH",
            BASE_DIR / "prediction" / "modelo_random_forest_new.pkl",
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
