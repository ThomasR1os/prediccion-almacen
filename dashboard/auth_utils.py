from django.core.exceptions import PermissionDenied
from prediction import models


def _parse_id_carga(raw_value):
    if raw_value in (None, ""):
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def registros_carga_del_usuario(user, id_carga, fecha):
    """Registros de una carga solo si pertenecen al usuario autenticado."""
    if not user.is_authenticated:
        return models.PrediccionAlmacen.objects.none()
    return models.PrediccionAlmacen.objects.filter(
        id_carga=id_carga,
        fecha_carga__date=fecha,
        usuario=user.username,
    )


def exigir_carga_propia(user, id_carga, fecha):
    """Lanza PermissionDenied si la carga no existe o no pertenece al usuario."""
    if not user.is_authenticated:
        raise PermissionDenied
    parsed_id = _parse_id_carga(id_carga)
    if parsed_id is None:
        raise PermissionDenied
    if not registros_carga_del_usuario(user, parsed_id, fecha).exists():
        raise PermissionDenied
    return parsed_id
