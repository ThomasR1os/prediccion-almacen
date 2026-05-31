from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from desercion_escolar.quality import normalize_email

PHONE_VALIDATOR = RegexValidator(
    regex=r"^[\d\s+\-()]{6,20}$",
    message="Teléfono inválido. Use solo números, espacios, +, - o paréntesis (6-20 caracteres).",
)


class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Almacén"
        verbose_name_plural = "Almacenes"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Item(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class InventoryLevel(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="inventory_levels")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="inventory_levels")
    quantity = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    low_stock_threshold = models.IntegerField(validators=[MinValueValidator(0)], default=0)

    class Meta:
        verbose_name = "Nivel de inventario"
        verbose_name_plural = "Niveles de inventario"
        constraints = [
            models.UniqueConstraint(fields=["warehouse", "item"], name="uniq_inventorylevel_warehouse_item"),
        ]
        ordering = ["warehouse__name", "item__name"]

    def __str__(self) -> str:
        return f"{self.warehouse} - {self.item}: {self.quantity}"


class Customer(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        validators=[PHONE_VALIDATOR],
    )
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(email__isnull=False) & ~models.Q(email=""),
                name="uniq_customer_email",
            ),
        ]

    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.strip()
            if not self.name:
                raise ValidationError({"name": "El nombre no puede estar vacío."})
        if self.email:
            self.email = normalize_email(self.email)

    def save(self, *args, **kwargs):
        if self.email:
            self.email = normalize_email(self.email)
        if self.name:
            self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Sale(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="sales")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="sales")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sales_created")

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Venta #{self.id} - {self.customer}"


class SaleLine(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="sale_lines")
    quantity = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Línea de venta"
        verbose_name_plural = "Líneas de venta"
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["sale", "item"], name="uniq_saleline_sale_item"),
        ]

    def __str__(self) -> str:
        return f"{self.sale_id} - {self.item} x {self.quantity}"
