from django.urls import path

from . import views

app_name = "operaciones"

urlpatterns = [
    # Clientes
    path("clientes/", views.clientes_list, name="clientes_list"),
    path("clientes/nuevo/", views.clientes_create, name="clientes_create"),
    # Inventario
    path("inventario/", views.inventario_list, name="inventario_list"),
    path("inventario/ajustar/", views.inventario_adjust, name="inventario_adjust"),
    path("inventario/alertas/", views.inventario_alertas, name="inventario_alertas"),
    # Ventas
    path("ventas/", views.ventas_list, name="ventas_list"),
    path("ventas/nueva/", views.ventas_create, name="ventas_create"),
    path("ventas/<int:sale_id>/", views.ventas_detail, name="ventas_detail"),
    # Peso (mockup UI)
    path("peso/mockup/", views.peso_mockup, name="peso_mockup"),
]

