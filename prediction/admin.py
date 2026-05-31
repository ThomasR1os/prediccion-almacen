from django.contrib import admin

from .models import PrediccionAlmacen


@admin.register(PrediccionAlmacen)
class PrediccionAlmacenAdmin(admin.ModelAdmin):
    list_display = (
        'id_carga', 'fecha_carga', 'usuario', 'producto', 'tipo', 'mes', 'dia_mes', 'cantidad_unitaria',
    )
    list_filter = ('id_carga', 'mes', 'producto', 'tipo', 'usuario')
    search_fields = ('producto', 'proveedor', 'usuario', 'id_carga')
    ordering = ('-fecha_carga', '-id_carga', 'dia_mes')
