from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'nombre', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'nombre')
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('nombre',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('nombre',)}),
    )
