import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .iot_auth import require_iot_api_key
from .models import ScaleDeviceState, ScaleReading, WeightRecord

TURNO_VALUES = {"mañana", "tarde", "noche"}
TIPO_VALUES = {"saco", "caja"}


def _parse_weight(value) -> Decimal | None:
    try:
        weight = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if weight < 0:
        return None
    return weight


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"success": False, "error": message}, status=status)


@csrf_exempt
@require_POST
@require_iot_api_key
def iot_peso_lectura(request):
    """Recibe lecturas POST desde dispositivos IoT (balanzas)."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _json_error("JSON inválido.")

    if not isinstance(body, dict):
        return _json_error("El cuerpo debe ser un objeto JSON.")

    device_id = (body.get("deviceId") or "").strip()
    if not device_id:
        return _json_error("Campo deviceId requerido.")

    if len(device_id) > 50:
        return _json_error("deviceId demasiado largo (máx. 50 caracteres).")

    if "weightKg" not in body:
        return _json_error("Campo weightKg requerido.")

    weight_kg = _parse_weight(body.get("weightKg"))
    if weight_kg is None:
        return _json_error("weightKg debe ser un número mayor o igual a 0.")

    with transaction.atomic():
        reading = ScaleReading.objects.create(device_id=device_id, weight_kg=weight_kg)
        state, created = ScaleDeviceState.objects.select_for_update().get_or_create(
            device_id=device_id,
            defaults={"weight_kg": weight_kg, "last_reading": reading},
        )
        if not created:
            state.weight_kg = weight_kg
            state.last_reading = reading
            state.save(update_fields=["weight_kg", "last_reading", "updated_at"])

    return JsonResponse(
        {
            "success": True,
            "deviceId": device_id,
            "weightKg": float(weight_kg),
            "readingId": reading.id,
        },
        status=201,
    )


@login_required
@require_GET
def peso_live(request):
    """Devuelve el estado actual de las balanzas (polling desde la UI)."""
    since_id = request.GET.get("since")
    device_id = (request.GET.get("deviceId") or "").strip()

    states = ScaleDeviceState.objects.select_related("last_reading")
    if device_id:
        states = states.filter(device_id=device_id)

    devices = []
    latest_id = 0
    for state in states:
        reading = state.last_reading
        reading_id = reading.id if reading else 0
        latest_id = max(latest_id, reading_id)
        devices.append(
            {
                "deviceId": state.device_id,
                "weightKg": float(state.weight_kg),
                "readingId": reading_id or None,
                "updatedAt": state.updated_at.isoformat(),
            }
        )

    has_new = False
    if since_id:
        try:
            since_id_int = int(since_id)
            has_new = ScaleReading.objects.filter(id__gt=since_id_int).exists()
        except (TypeError, ValueError):
            has_new = False

    return JsonResponse(
        {
            "success": True,
            "devices": devices,
            "latestReadingId": latest_id,
            "hasNew": has_new,
        }
    )


@login_required
@require_POST
def peso_reiniciar(request):
    """Reinicia el peso mostrado de una balanza."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _json_error("JSON inválido.")

    device_id = (body.get("deviceId") or "").strip()
    if not device_id:
        return _json_error("Campo deviceId requerido.")

    with transaction.atomic():
        state, _ = ScaleDeviceState.objects.select_for_update().get_or_create(
            device_id=device_id,
            defaults={"weight_kg": Decimal("0")},
        )
        state.weight_kg = Decimal("0")
        state.last_reading = None
        state.save(update_fields=["weight_kg", "last_reading", "updated_at"])

    return JsonResponse(
        {
            "success": True,
            "deviceId": device_id,
            "weightKg": 0.0,
        }
    )


def _expected_weight(cantidad: int, tipo_producto: str) -> Decimal:
    peso_por_unidad = Decimal("0.8") if tipo_producto == "caja" else Decimal("1")
    return Decimal(cantidad) * peso_por_unidad


@login_required
@require_POST
def peso_registrar(request):
    """Registra un pesaje completo asociado al usuario autenticado."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _json_error("JSON inválido.")

    device_id = (body.get("deviceId") or "").strip()
    operador = (body.get("operador") or "").strip()
    turno = (body.get("turno") or "").strip()
    tipo_producto = (body.get("tipoProducto") or "").strip()
    cliente = (body.get("cliente") or "").strip()
    producto = (body.get("producto") or "").strip()
    almacen = (body.get("almacen") or "").strip()

    if not device_id:
        return _json_error("Campo deviceId requerido.")
    if not operador:
        return _json_error("Campo operador requerido.")
    if turno not in TURNO_VALUES:
        return _json_error("Turno inválido.")
    if tipo_producto not in TIPO_VALUES:
        return _json_error("Tipo de producto inválido.")
    if not cliente:
        return _json_error("Campo cliente requerido.")
    if not producto:
        return _json_error("Campo producto requerido.")
    if not almacen:
        return _json_error("Campo almacén requerido.")

    try:
        cantidad = int(body.get("cantidad"))
    except (TypeError, ValueError):
        return _json_error("Cantidad inválida.")
    if cantidad < 1:
        return _json_error("La cantidad debe ser al menos 1.")

    peso_esperado = _expected_weight(cantidad, tipo_producto)

    state = ScaleDeviceState.objects.filter(device_id=device_id).select_related("last_reading").first()
    if not state or state.weight_kg <= 0 or not state.last_reading:
        return _json_error(
            "No hay lectura IoT disponible para esta balanza. "
            "Envíe el peso desde el dispositivo antes de registrar."
        )

    peso_real = state.weight_kg
    peso_diferencia = peso_real - peso_esperado

    record = WeightRecord.objects.create(
        created_by=request.user,
        device_id=device_id,
        operador=operador,
        turno=turno,
        tipo_producto=tipo_producto,
        cliente=cliente,
        producto=producto,
        almacen=almacen,
        cantidad=cantidad,
        peso_esperado_kg=peso_esperado,
        peso_real_kg=peso_real,
        peso_diferencia_kg=peso_diferencia,
        scale_reading=state.last_reading,
    )

    return JsonResponse(
        {
            "success": True,
            "recordId": record.id,
            "deviceId": device_id,
            "pesoEsperadoKg": float(peso_esperado),
            "pesoRealKg": float(peso_real),
            "pesoDiferenciaKg": float(peso_diferencia),
            "detailUrl": f"/operaciones/peso/registros/{record.id}/",
        },
        status=201,
    )
