"""Load and cache the ML model once at application startup."""
from __future__ import annotations

import warnings

import joblib
from django.conf import settings

from .model_storage import ensure_model, model_file_available

_model = None
_init_error: Exception | None = None


class ModelNotReadyError(Exception):
    """Raised when the prediction model is unavailable."""


def initialize_prediction_model() -> None:
    global _model, _init_error

    if _model is not None:
        return
    if _init_error is not None:
        raise ModelNotReadyError(str(_init_error)) from _init_error

    try:
        ensure_model(settings.MODEL_PATH)
        if not model_file_available(settings.MODEL_PATH):
            raise FileNotFoundError(
                f"Model file missing at {settings.MODEL_PATH}."
            )
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Trying to unpickle estimator*",
                category=UserWarning,
            )
            _model = joblib.load(settings.MODEL_PATH)
        print(f"Prediction model loaded from {settings.MODEL_PATH}.")
    except Exception as exc:
        _init_error = exc
        raise ModelNotReadyError(
            "No se pudo cargar el modelo de predicción al iniciar la aplicación. "
            f"Detalle: {exc}"
        ) from exc


def get_prediction_model():
    if _model is None:
        initialize_prediction_model()
    return _model
