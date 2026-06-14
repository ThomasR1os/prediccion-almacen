from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from desercion_escolar.quality import normalize_email
from .models import Customer, Item, Sale, SaleLine, Warehouse

SALELINE_PREFIX = "lines"


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "email", "phone", "active"]

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise ValidationError("El nombre es obligatorio.")
        qs = Customer.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ya existe un cliente con este nombre.")
        return name

    def clean_email(self):
        email = normalize_email(self.cleaned_data.get("email"))
        if not email:
            return None
        qs = Customer.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ya existe un cliente con este correo.")
        return email


class InventoryAdjustForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all())
    item = forms.ModelChoiceField(queryset=Item.objects.all())
    delta = forms.IntegerField(
        help_text="Cantidad a sumar (+) o restar (-). Usa 0 si solo actualizas el umbral."
    )
    low_stock_threshold = forms.IntegerField(required=False, min_value=0)

    def clean(self):
        cleaned = super().clean()
        delta = cleaned.get("delta")
        threshold = cleaned.get("low_stock_threshold")
        if delta is None:
            return cleaned
        if delta == 0 and threshold is None:
            raise ValidationError(
                "Indica un ajuste distinto de 0 o un umbral de bajo stock."
            )
        return cleaned


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["customer", "warehouse"]
        error_messages = {
            "customer": {"required": "Selecciona un cliente."},
            "warehouse": {"required": "Selecciona un almacén."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.filter(active=True).order_by("name")


class SaleLineForm(forms.ModelForm):
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        required=False,
        error_messages={
            "invalid_choice": "Selecciona un item válido.",
        },
    )
    quantity = forms.IntegerField(
        required=False,
        min_value=1,
        error_messages={
            "min_value": "La cantidad debe ser al menos 1.",
            "invalid": "Indica una cantidad válida.",
        },
    )

    class Meta:
        model = SaleLine
        fields = ["item", "quantity"]

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("DELETE"):
            return cleaned
        item = cleaned.get("item")
        quantity = cleaned.get("quantity")
        if not item and quantity in (None, ""):
            return cleaned
        if not item:
            raise ValidationError({"item": "Selecciona un item."})
        if quantity in (None, ""):
            raise ValidationError({"quantity": "Indica la cantidad."})
        return cleaned


class BaseSaleLineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        seen_items = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            item = form.cleaned_data.get("item")
            quantity = form.cleaned_data.get("quantity")
            if not item or not quantity:
                continue
            if item.pk in seen_items:
                raise ValidationError(
                    f'El item "{item.name}" está repetido. Usa una sola fila con la cantidad total.'
                )
            seen_items.add(item.pk)


SaleLineFormSet = inlineformset_factory(
    Sale,
    SaleLine,
    form=SaleLineForm,
    formset=BaseSaleLineFormSet,
    fields=["item", "quantity"],
    extra=1,
    can_delete=True,
)
