from django.core.management.base import BaseCommand
from django.db import transaction

from operaciones.models import Customer, InventoryLevel, Item, Warehouse
from prediction.catalog import (
    ALMACENES,
    DEFAULT_CUSTOMERS,
    PRODUCTOS,
    STOCK_BASE_POR_ALMACEN,
)


def _initial_quantity(warehouse_name: str, item_index: int) -> int:
    base = STOCK_BASE_POR_ALMACEN.get(warehouse_name, 50)
    return base + (item_index % 7) * 10


class Command(BaseCommand):
    help = "Inicializa almacenes, productos, inventario y clientes en la BD local."

    def add_arguments(self, parser):
        parser.add_argument(
            "--threshold",
            type=int,
            default=10,
            help="Umbral por defecto para alerta de bajo stock.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        threshold = int(options["threshold"])

        warehouses = []
        for name in ALMACENES:
            warehouse, _ = Warehouse.objects.get_or_create(name=name)
            warehouses.append(warehouse)

        items = []
        for name in PRODUCTOS:
            item, _ = Item.objects.get_or_create(name=name)
            items.append(item)

        created_levels = 0
        for warehouse in warehouses:
            for index, item in enumerate(items):
                _, created = InventoryLevel.objects.get_or_create(
                    warehouse=warehouse,
                    item=item,
                    defaults={
                        "quantity": _initial_quantity(warehouse.name, index),
                        "low_stock_threshold": threshold,
                    },
                )
                if created:
                    created_levels += 1

        created_customers = 0
        for data in DEFAULT_CUSTOMERS:
            email = data.get("email")
            if email:
                _, created = Customer.objects.get_or_create(
                    email=email,
                    defaults={
                        "name": data["name"],
                        "phone": data.get("phone"),
                        "active": True,
                    },
                )
            elif Customer.objects.filter(name=data["name"]).exists():
                created = False
            else:
                Customer.objects.create(
                    name=data["name"],
                    phone=data.get("phone"),
                    active=True,
                )
                created = True
            if created:
                created_customers += 1

        self.stdout.write(self.style.SUCCESS("Seed completado."))
        self.stdout.write(f"- Almacenes: {len(warehouses)}")
        self.stdout.write(f"- Productos: {len(items)}")
        self.stdout.write(f"- Niveles de inventario creados: {created_levels}")
        self.stdout.write(f"- Clientes creados: {created_customers}")
