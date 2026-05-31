from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import Lower

from operaciones.models import Customer, Sale


class Command(BaseCommand):
    help = "Lista o fusiona clientes con el mismo correo electrónico."

    def add_arguments(self, parser):
        parser.add_argument("--merge", action="store_true", help="Fusiona duplicados por correo.")
        parser.add_argument("--dry-run", action="store_true", help="Simula la fusión.")
        parser.add_argument("--email", type=str, help="Procesar solo un correo.")

    def handle(self, *args, **options):
        merge = options["merge"]
        dry_run = options["dry_run"]
        email_filter = (options.get("email") or "").strip().lower()

        duplicates = self._find_duplicate_groups(email_filter)
        if not duplicates:
            self.stdout.write(self.style.SUCCESS("No hay clientes con correo duplicado."))
            return

        self.stdout.write(f"Correos duplicados: {len(duplicates)}")
        for email, customers in duplicates.items():
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(f"Correo: {email} ({len(customers)} clientes)"))
            for customer in customers:
                sales_count = Sale.objects.filter(customer=customer).count()
                self.stdout.write(
                    f"  - id={customer.id} name={customer.name!r} active={customer.active} ventas={sales_count}"
                )

        if not merge:
            self.stdout.write("")
            self.stdout.write("Ejecuta con --merge para fusionar duplicados.")
            return

        if dry_run:
            self.stdout.write(self.style.NOTICE("Modo simulación (--dry-run)."))

        merged = 0
        deleted = 0
        for email, customers in duplicates.items():
            keeper = max(customers, key=lambda c: (c.active, -c.id))
            to_remove = [c for c in customers if c.id != keeper.id]
            self.stdout.write(f"Conservar id={keeper.id} ({keeper.name}), eliminar {[c.id for c in to_remove]}")

            if dry_run:
                for customer in to_remove:
                    sales_count = Sale.objects.filter(customer=customer).count()
                    self.stdout.write(f"  - Reasignar {sales_count} venta(s) de id={customer.id}")
                merged += 1
                deleted += len(to_remove)
                continue

            with transaction.atomic():
                for customer in to_remove:
                    Sale.objects.filter(customer=customer).update(customer=keeper)
                    customer.delete()
                    deleted += 1
                merged += 1

        self.stdout.write(self.style.SUCCESS(f"Grupos: {merged}, clientes eliminados: {deleted}"))

    def _find_duplicate_groups(self, email_filter):
        qs = (
            Customer.objects.exclude(email__isnull=True)
            .exclude(email="")
            .annotate(normalized_email=Lower("email"))
            .values("normalized_email")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
            .order_by("normalized_email")
        )
        if email_filter:
            qs = qs.filter(normalized_email=email_filter)

        emails = [row["normalized_email"] for row in qs]
        if not emails:
            return {}

        customers = (
            Customer.objects.annotate(normalized_email=Lower("email"))
            .filter(normalized_email__in=emails)
            .order_by("normalized_email", "id")
        )
        groups = defaultdict(list)
        for customer in customers:
            groups[customer.normalized_email].append(customer)
        return dict(groups)
