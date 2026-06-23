import os
from functools import wraps

from django.conf import settings
from django.http import JsonResponse


def require_iot_api_key(view_func):
    """Autentica dispositivos IoT mediante cabecera X-API-Key."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        expected = getattr(settings, "IOT_API_KEY", "") or os.environ.get("IOT_API_KEY", "")
        if not expected:
            return JsonResponse(
                {"success": False, "error": "API IoT no configurada en el servidor."},
                status=503,
            )

        provided = request.headers.get("X-API-Key", "")
        if provided != expected:
            return JsonResponse(
                {"success": False, "error": "API key inválida o ausente."},
                status=401,
            )

        return view_func(request, *args, **kwargs)

    return wrapper
