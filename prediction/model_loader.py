"""Load and cache the ML model once at application startup."""
from __future__ import annotations

import warnings

import joblib
from django.conf import settings

from .model_storage import model_file_available

_model = None
_init_error: Exception | None = None
_warmed_up = False


class ModelNotReadyError(Exception):
    """Raised when the prediction model is unavailable."""


def warmup_prediction_model() -> None:
    """Download (if needed) and load the model. Call only at startup."""
    global _model, _init_error, _warmed_up

    if _warmed_up and _model is not None:
        return
    if _init_error is not None:
        raise ModelNotReadyError(str(_init_error)) from _init_error

    try:
        if not model_file_available(settings.MODEL_PATH):
            raise FileNotFoundError(
                f"Model file missing or incomplete at {settings.MODEL_PATH}. "
                "El servidor debe descargarlo al iniciar con scripts/ensure_model.py."
            )
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Trying to unpickle estimator*",
                category=UserWarning,
            )
            _model = joblib.load(settings.MODEL_PATH)
        _warmed_up = True
        print(f"Prediction model loaded from {settings.MODEL_PATH}.")
    except Exception as exc:
        _init_error = exc
        raise ModelNotReadyError(
            "No se pudo cargar el modelo de predicción al iniciar la aplicación. "
            f"Detalle: {exc}"
        ) from exc


def get_prediction_model():
    """Return the cached model. Never downloads during HTTP requests."""
    if _model is not None:
        return _model
    if _init_error is not None:
        raise ModelNotReadyError(str(_init_error)) from _init_error
    raise ModelNotReadyError(
        "El modelo aún no está listo. Espera 2-3 minutos a que termine "
        "el despliegue y vuelve a intentar."
    )
