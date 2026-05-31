from calendar import monthrange
from datetime import datetime

from django import forms

from .catalog import ALMACENES, PRODUCTOS, PROVEEDORES, TURNOS


class PrediccionForm(forms.Form):
    TIPO_PREDICCION_CHOICES = [
        ("unitario", "Predicción del día"),
        ("mes_completo", "Predicción del mes"),
    ]
    TIPO_CHOICES = [("Entrada", "Entrada"), ("Salida", "Salida")]
    FESTIVO_CHOICES = [(0, "No"), (1, "Sí")]
    MES_CHOICES = [(i, str(i)) for i in range(1, 13)]

    tipo_prediccion = forms.ChoiceField(
        choices=TIPO_PREDICCION_CHOICES,
        error_messages={"required": "Selecciona un modo de predicción (día o mes)."},
    )
    tipo = forms.ChoiceField(choices=TIPO_CHOICES)
    almacen = forms.ChoiceField(choices=[(a, a) for a in ALMACENES])
    turno = forms.ChoiceField(choices=[(t, t) for t in TURNOS])
    producto = forms.ChoiceField(choices=[(p, p) for p in PRODUCTOS])
    origen = forms.ChoiceField(choices=[(o, o) for o in PROVEEDORES])
    mes = forms.TypedChoiceField(choices=MES_CHOICES, coerce=int)
    festivo = forms.TypedChoiceField(choices=FESTIVO_CHOICES, coerce=int)
    dia_mes = forms.IntegerField(required=False, min_value=1, max_value=31)

    def clean(self):
        cleaned = super().clean()
        tipo_prediccion = cleaned.get("tipo_prediccion")
        mes = cleaned.get("mes")
        dia_mes = cleaned.get("dia_mes")

        if tipo_prediccion == "unitario":
            if not dia_mes:
                self.add_error("dia_mes", "Indica el día del mes para la predicción diaria.")
            elif mes:
                year = datetime.now().year
                max_day = monthrange(year, mes)[1]
                if dia_mes > max_day:
                    self.add_error("dia_mes", f"El mes seleccionado solo tiene {max_day} días.")
                else:
                    try:
                        datetime(year, mes, dia_mes)
                    except ValueError:
                        self.add_error("dia_mes", "Fecha inválida.")
        return cleaned
