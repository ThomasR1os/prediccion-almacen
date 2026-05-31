from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class PrediccionAlmacen(models.Model):
    id_carga = models.IntegerField()
    fecha_carga = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=255, null=True, blank=True)
    tipo = models.CharField(max_length=20)
    almacen = models.CharField(max_length=100)
    turno = models.CharField(max_length=20)
    producto = models.CharField(max_length=100)
    proveedor = models.CharField(max_length=100)
    mes = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    dia_mes = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)], default=1)
    dia_semana = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(6)])
    festivo = models.BooleanField()
    cantidad_unitaria = models.IntegerField(validators=[MinValueValidator(0)])
    bultos = models.IntegerField(validators=[MinValueValidator(0)])
    precio_unidad = models.FloatField(validators=[MinValueValidator(0)])
    lead_time_dias = models.IntegerField(validators=[MinValueValidator(0)])
    stock_almacen = models.IntegerField(validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["id_carga", "usuario", "mes", "dia_mes", "producto", "tipo"],
                name="uniq_prediccion_carga_dia",
            ),
        ]

    def clean(self):
        super().clean()
        if self.mes and self.dia_mes:
            from calendar import monthrange
            from datetime import datetime
            year = datetime.now().year
            if self.dia_mes > monthrange(year, self.mes)[1]:
                raise ValidationError({"dia_mes": "Día inválido para el mes seleccionado."})

    def __str__(self):
        return f"ID_CARGA {self.id_carga} | {self.producto} ({self.tipo}) | {self.fecha_carga.strftime('%Y-%m-%d')}"
