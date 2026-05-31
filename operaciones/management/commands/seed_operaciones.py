from django.core.management.base import BaseCommand
from django.db import transaction

from operaciones.models import InventoryLevel, Item, Warehouse
from prediction.catalog import ALMACENES, PRODUCTOS


class Command(BaseCommand):
    help = "Crea Items/Almacenes/Niveles de inventario base para operaciones."

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
            w, _ = Warehouse.objects.get_or_create(name=name)
            warehouses.append(w)

        items = []
        for name in PRODUCTOS:
            i, _ = Item.objects.get_or_create(name=name)
            items.append(i)

        created_levels = 0
        for w in warehouses:
            for i in items:
                _, created = InventoryLevel.objects.get_or_create(
                    warehouse=w,
                    item=i,
                    defaults={"quantity": 0, "low_stock_threshold": threshold},
                )
                if created:
                    created_levels += 1

        self.stdout.write(self.style.SUCCESS("Seed completado."))
        self.stdout.write(f"- Almacenes: {len(warehouses)}")
        self.stdout.write(f"- Items: {len(items)}")
        self.stdout.write(f"- Niveles de inventario creados: {created_levels}")

