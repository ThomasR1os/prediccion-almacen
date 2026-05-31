from django.contrib import admin

from .models import Customer, InventoryLevel, Item, Sale, SaleLine, Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name"]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    list_display = ["name"]


@admin.register(InventoryLevel)
class InventoryLevelAdmin(admin.ModelAdmin):
    search_fields = ["warehouse__name", "item__name"]
    list_filter = ["warehouse"]
    list_display = ["warehouse", "item", "quantity", "low_stock_threshold"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    search_fields = ["name", "email", "phone"]
    list_filter = ["active"]
    list_display = ["name", "email", "phone", "active"]


class SaleLineInline(admin.TabularInline):
    model = SaleLine
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_filter = ["warehouse", "created_at"]
    search_fields = ["customer__name", "created_by__username"]
    list_display = ["id", "created_at", "customer", "warehouse", "created_by"]
    inlines = [SaleLineInline]
