import os
import re
from collections import defaultdict


def normalize_email(email):
    return (email or "").strip().lower()


def safe_filename(value, fallback="archivo", max_len=60):
    safe = re.sub(r"[^\w\-_.]", "_", str(value or ""))
    safe = safe.strip("_") or fallback
    return safe[:max_len]


def aggregate_quantities_by_item(lines):
    totals = defaultdict(int)
    items = {}
    for line in lines:
        totals[line.item_id] += line.quantity
        items[line.item_id] = line.item
    return totals, items


def clamp_prediction_values(raw_values):
    cantidad, bultos, precio, lead_time, stock = raw_values
    return {
        "cantidad_unitaria": max(0, int(cantidad)),
        "bultos": max(0, int(bultos)),
        "precio_unidad": max(0.0, float(precio)),
        "lead_time_dias": max(0, int(lead_time)),
        "stock_almacen": max(0, int(stock)),
    }


def model_file_available(model_path):
    return bool(model_path) and os.path.isfile(model_path)
