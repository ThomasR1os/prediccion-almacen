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
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
from html import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def _chart_day(record):
    return record.get('dia_mes') or record.get('dia_semana') or record.get('id')


PDF_COLUMN_LABELS = {
    "tipo": "Tipo",
    "almacen": "Almacén",
    "turno": "Turno",
    "producto": "Producto",
    "proveedor": "Proveedor",
    "mes": "Mes",
    "dia_mes": "Día del mes",
    "dia_semana": "Día de la semana",
    "festivo": "Festivo",
    "cantidad_unitaria": "Cantidad unitaria",
    "bultos": "Bultos",
    "precio_unidad": "Precio unitario",
    "lead_time_dias": "Lead time (días)",
    "stock_almacen": "Stock almacén",
}

DIAS_SEMANA_PDF = (
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
)


def _pdf_column_label(key):
    return PDF_COLUMN_LABELS.get(key, key.replace("_", " ").capitalize())


def _format_dia_semana(record):
    dia_semana = record.get("dia_semana")
    if dia_semana is not None:
        try:
            idx = int(dia_semana)
            if 0 <= idx <= 6:
                return DIAS_SEMANA_PDF[idx]
        except (TypeError, ValueError):
            pass
    mes = record.get("mes")
    dia_mes = record.get("dia_mes")
    if mes and dia_mes:
        from datetime import datetime
        try:
            return DIAS_SEMANA_PDF[datetime(datetime.now().year, int(mes), int(dia_mes)).weekday()]
        except ValueError:
            pass
    return str(dia_semana) if dia_semana is not None else ""


def _pdf_cell_value(key, value, record=None):
    if value is None:
        return ""
    if key == "precio_unidad":
        return f"S/ {float(value):.2f}"
    if key == "festivo":
        return "Sí" if value else "No"
    if key == "dia_semana":
        return _format_dia_semana(record or {})
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


PDF_MARGIN = 0.4 * inch
PORTRAIT_PAGE = letter
LANDSCAPE_PAGE = landscape(letter)


def _pdf_doc_with_mixed_orientation(buffer):
    doc = BaseDocTemplate(buffer, pagesize=PORTRAIT_PAGE)

    landscape_width = LANDSCAPE_PAGE[0] - 2 * PDF_MARGIN
    landscape_height = LANDSCAPE_PAGE[1] - 2 * PDF_MARGIN
    portrait_width = PORTRAIT_PAGE[0] - 2 * PDF_MARGIN
    portrait_height = PORTRAIT_PAGE[1] - 2 * PDF_MARGIN

    doc.addPageTemplates([
        PageTemplate(
            id="landscape",
            frames=[Frame(PDF_MARGIN, PDF_MARGIN, landscape_width, landscape_height, id="landscape_frame")],
            pagesize=LANDSCAPE_PAGE,
        ),
        PageTemplate(
            id="portrait",
            frames=[Frame(PDF_MARGIN, PDF_MARGIN, portrait_width, portrait_height, id="portrait_frame")],
            pagesize=PORTRAIT_PAGE,
        ),
    ])
    return doc, landscape_width, portrait_width


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
    doc, landscape_width, portrait_width = _pdf_doc_with_mixed_orientation(buffer)
    elements = []

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        "pdfHeader",
        parent=styles["Normal"],
        fontSize=7,
        leading=8,
        textColor=colors.black,
    )
    cell_style = ParagraphStyle(
        "pdfCell",
        parent=styles["Normal"],
        fontSize=6,
        leading=7,
    )
    elements.append(Paragraph(f"<b>Reporte: {proveedor} - {producto} (Mes: {mes})</b>", styles["Title"]))
    elements.append(Spacer(1, 0.2 * inch))

    columnas = [k for k in registros[0].keys() if k not in ("id_carga", "fecha_carga", "id", "usuario")]
    table_data = [[Paragraph(_pdf_column_label(col), header_style) for col in columnas]]
    for r in registros:
        row = [
            Paragraph(escape(_pdf_cell_value(col, r[col], r)), cell_style)
            for col in columnas
        ]
        table_data.append(row)

    col_width = landscape_width / len(columnas)
    t = Table(table_data, repeatRows=1, colWidths=[col_width] * len(columnas))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(t)

    elements.append(NextPageTemplate("portrait"))
    elements.append(PageBreak())

    chart_width = min(6 * inch, portrait_width)
    chart_height = chart_width / 2

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

    elements.append(Image(
        grafico(cantidad, f"Cantidad Unitaria – {producto} (Mes {mes})", 'Cantidad'),
        chart_width,
        chart_height,
    ))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Image(
        grafico(lead_time, f"Lead‑Time (d) – {producto} (Mes {mes})", 'Lead‑Time (días)'),
        chart_width,
        chart_height,
    ))
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(Image(
        grafico(stock, f"Stock Almacén – {producto} (Mes {mes})", 'Stock'),
        chart_width,
        chart_height,
    ))

    doc.build(elements)
    buffer.seek(0)
    filename = safe_filename(f'reporte_{producto}_{proveedor}_{mes}', fallback='reporte')
    return FileResponse(buffer, as_attachment=True, filename=f'{filename}.pdf')
