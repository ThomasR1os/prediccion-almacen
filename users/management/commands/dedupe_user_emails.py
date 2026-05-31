from collections import defaultdict

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import Lower

from operaciones.models import Sale
from prediction.models import PrediccionAlmacen


class Command(BaseCommand):
    help = (
        "Lista o fusiona usuarios con el mismo correo electrónico. "
        "Conserva la cuenta con actividad más reciente y reasigna datos relacionados."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--merge",
            action="store_true",
            help="Fusiona duplicados (sin este flag solo lista).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra qué haría --merge sin modificar la base de datos.",
        )
        parser.add_argument(
            "--email",
            type=str,
            help="Procesar solo un correo concreto (útil para pruebas).",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        merge = options["merge"]
        dry_run = options["dry_run"]
        email_filter = (options.get("email") or "").strip()

        duplicates = self._find_duplicate_groups(User, email_filter)
        if not duplicates:
            self.stdout.write(self.style.SUCCESS("No hay correos duplicados."))
            return

        self.stdout.write(f"Correos duplicados encontrados: {len(duplicates)}")
        for normalized_email, users in duplicates.items():
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(f"Correo: {normalized_email} ({len(users)} cuentas)"))
            for user in users:
                self.stdout.write(
                    f"  - id={user.id} username={user.username!r} "
                    f"last_login={user.last_login} is_active={user.is_active}"
                )

        if not merge:
            self.stdout.write("")
            self.stdout.write("Ejecuta con --merge para fusionar, o --merge --dry-run para simular.")
            return

        if dry_run:
            self.stdout.write("")
            self.stdout.write(self.style.NOTICE("Modo simulación (--dry-run): no se guardarán cambios."))

        merged_groups = 0
        deleted_users = 0

        for normalized_email, users in duplicates.items():
            keeper = self._choose_keeper(users)
            to_remove = [user for user in users if user.id != keeper.id]

            self.stdout.write("")
            self.stdout.write(
                f"Fusionando {normalized_email}: conservar id={keeper.id} "
                f"({keeper.username}), eliminar {[user.id for user in to_remove]}"
            )

            if dry_run:
                for user in to_remove:
                    sales_count = Sale.objects.filter(created_by=user).count()
                    pred_count = PrediccionAlmacen.objects.filter(usuario=user.username).count()
                    self.stdout.write(
                        f"  - id={user.id}: reasignar {sales_count} venta(s), "
                        f"{pred_count} predicción(es) por username"
                    )
                merged_groups += 1
                deleted_users += len(to_remove)
                continue

            with transaction.atomic():
                for user in to_remove:
                    Sale.objects.filter(created_by=user).update(created_by=keeper)
                    PrediccionAlmacen.objects.filter(usuario=user.username).update(
                        usuario=keeper.username
                    )
                    user.delete()
                    deleted_users += 1
                merged_groups += 1

        suffix = " (simulación)" if dry_run else ""
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Listo{suffix}: {merged_groups} grupo(s) procesado(s), "
                f"{deleted_users} cuenta(s) eliminada(s)."
            )
        )

    def _find_duplicate_groups(self, User, email_filter):
        qs = (
            User.objects.exclude(email__isnull=True)
            .exclude(email="")
            .annotate(normalized_email=Lower("email"))
            .values("normalized_email")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
            .order_by("normalized_email")
        )

        if email_filter:
            qs = qs.filter(normalized_email=email_filter.lower())

        duplicate_emails = [row["normalized_email"] for row in qs]
        if not duplicate_emails:
            return {}

        users = (
            User.objects.annotate(normalized_email=Lower("email"))
            .filter(normalized_email__in=duplicate_emails)
            .order_by("normalized_email", "id")
        )

        groups = defaultdict(list)
        for user in users:
            groups[user.normalized_email].append(user)
        return dict(groups)

    def _choose_keeper(self, users):
        def sort_key(user):
            last_login = user.last_login
            return (
                1 if user.is_superuser else 0,
                1 if user.is_staff else 0,
                last_login or user.date_joined,
                -user.id,
            )

        return max(users, key=sort_key)
