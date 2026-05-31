# views.py
from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from prediction import models
from django.db.models.functions import TruncDate
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_GET

from desercion_escolar.quality import safe_filename
from .auth_utils import exigir_carga_propia, registros_carga_del_usuario
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def _chart_day(record):
    return record.get('dia_mes') or record.get('dia_semana') or record.get('id')


def obtener_cargas_unicas(request):
    if not request.user.is_authenticated:
        return []

    cargas = (
        models.PrediccionAlmacen.objects
        .filter(usuario=request.user.username)
        .annotate(fecha_solo_dia=TruncDate('fecha_carga'))
        .values('id_carga', 'fecha_solo_dia')
        .distinct()
        .order_by('-fecha_solo_dia')
    )
    return [
        {'id_carga': c['id_carga'], 'fecha_carga': c['fecha_solo_dia'].strftime('%Y-%m-%d')}
        for c in cargas
    ]


@login_required
def dashboard_view(request):
    cargas = obtener_cargas_unicas(request)
    return render(request, 'dashboard.html', {'cargas': cargas})


@login_required
@require_GET
def dashboard_data(request):
    id_carga_raw = request.GET.get('id_carga')
    fecha_raw = request.GET.get('fecha')

    fecha = parse_date(fecha_raw)
    if not fecha:
        return JsonResponse({'error': 'Formato de fecha inválido. Use AAAA-MM-DD.'}, status=400)

    try:
        id_carga = exigir_carga_propia(request.user, id_carga_raw, fecha)
    except PermissionDenied:
        return JsonResponse({'error': 'Carga no encontrada o no autorizada.'}, status=403)

    registros = list(
        registros_carga_del_usuario(request.user, id_carga, fecha).values()
    )
    registros.sort(key=_chart_day)

    if registros:
        producto = registros[0].get('producto', 'Desconocido')
        mes = registros[0].get('mes', 'N/A')
    else:
        producto = 'Desconocido'
        mes = 'N/A'

    return JsonResponse({
        'data': registros,
        'producto': producto,
        'mes': mes
    })


@login_required
@require_GET
def descargar_pdf(request):
    id_carga_raw = request.GET.get('id_carga')
    fecha_raw = request.GET.get('fecha')
    fecha = parse_date(fecha_raw)

    if not fecha:
        return JsonResponse({'error': 'Fecha inválida. Use AAAA-MM-DD.'}, status=400)

    try:
        id_carga = exigir_carga_propia(request.user, id_carga_raw, fecha)
    except PermissionDenied:
        return JsonResponse({'error': 'Carga no encontrada o no autorizada.'}, status=403)

    registros = list(
        registros_carga_del_usuario(request.user, id_carga, fecha).values()
    )
    registros.sort(key=_chart_day)

    if not registros:
        return JsonResponse({'error': 'No hay datos para esta carga.'}, status=404)

    producto = registros[0]['producto']
    mes = registros[0]['mes']
    proveedor = registros[0]['proveedor']
    dias = [_chart_day(r) for r in registros]
    cantidad = [r['cantidad_unitaria'] for r in registros]
    lead_time = [r['lead_time_dias'] for r in registros]
    stock = [r['stock_almacen'] for r in registros]

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"<b>Reporte: {proveedor} - {producto} (Mes: {mes})</b>", styles['Title']))
    elements.append(Spacer(1, 0.2 * inch))

    columnas = [k for k in registros[0].keys() if k not in ('id_carga', 'fecha_carga', 'id', 'usuario')]
    table_data = [columnas]
    for r in registros:
        table_data.append([r[col] for col in columnas])

    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.3 * inch))

    def grafico(y_data, titulo, ylabel):
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(dias, y_data, marker='o')
        ax.set_title(titulo)
        ax.set_xlabel('Día del Mes')
        ax.set_ylabel(ylabel)
        fig.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        return buf

    elements.append(Image(grafico(cantidad, f"Cantidad Unitaria – {producto} (Mes {mes})", 'Cantidad'), 6*inch, 3*inch))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Image(grafico(lead_time, f"Lead‑Time (d) – {producto} (Mes {mes})", 'Lead‑Time (días)'), 6*inch, 3*inch))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Image(grafico(stock, f"Stock Almacén – {producto} (Mes {mes})", 'Stock'), 6*inch, 3*inch))

    doc.build(elements)
    buffer.seek(0)
    filename = safe_filename(f'reporte_{producto}_{proveedor}_{mes}', fallback='reporte')
    return FileResponse(buffer, as_attachment=True, filename=f'{filename}.pdf')
