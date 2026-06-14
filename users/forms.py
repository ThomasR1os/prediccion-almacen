from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from desercion_escolar.quality import normalize_email

User = get_user_model()

EMAIL_WIDGET = forms.TextInput(
    attrs={
        "autocomplete": "email",
        "inputmode": "email",
        "placeholder": "usuario@correo.com",
    }
)


def clean_email_value(raw_email, *, required=True, check_unique=False):
    value = (raw_email or "").strip()
    if not value:
        if required:
            raise ValidationError("El correo es obligatorio.")
        return None
    if "@" not in value:
        raise ValidationError(
            'El correo debe incluir el símbolo "@". Ejemplo: usuario@correo.com.'
        )
    try:
        validate_email(value)
    except ValidationError as exc:
        raise ValidationError(
            "Ingresa un correo válido. Ejemplo: usuario@correo.com."
        ) from exc
    email = normalize_email(value)
    if check_unique and User.objects.filter(email__iexact=email).exists():
        raise ValidationError(
            "Este correo ya está registrado. Si olvidaste tu contraseña, contacta al administrador."
        )
    return email


def _translate_password_error(message):
    lower = message.lower()
    if "too short" in lower:
        return "La contraseña es demasiado corta. Debe tener al menos 8 caracteres."
    if "too similar" in lower:
        return "La contraseña es demasiado parecida a tu información personal."
    if "too common" in lower:
        return "La contraseña es demasiado común. Elige una más segura."
    if "entirely numeric" in lower:
        return "La contraseña no puede ser solo números."
    return message


def validate_password_es(password, user=None):
    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        raise ValidationError([_translate_password_error(msg) for msg in exc.messages]) from exc


class UserRegisterForm(forms.ModelForm):
    username = forms.CharField(
        label='Usuario',
        required=True,
        help_text='Puedes ingresar cualquier combinación de caracteres.',
        widget=forms.TextInput,
        error_messages={'required': 'El nombre de usuario es obligatorio.'},
    )
    email = forms.CharField(
        label='Correo electrónico',
        required=True,
        widget=EMAIL_WIDGET,
        help_text='Debe ser único. No podrás registrar el mismo correo dos veces.',
        error_messages={'required': 'El correo es obligatorio.'},
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text="Mínimo 8 caracteres. Debe cumplir las reglas de seguridad del sistema.",
        error_messages={'required': 'La contraseña es obligatoria.'},
    )
    password_confirm = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput,
        help_text="Confirma la contraseña.",
        error_messages={'required': 'Debes confirmar la contraseña.'},
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].validators = [
            validator
            for validator in self.fields['username'].validators
            if validator.__class__.__name__ != 'UniqueValidator'
        ]

    def validate_unique(self):
        # Username and email uniqueness are validated in clean_* with Spanish messages.
        return

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise ValidationError('El nombre de usuario es obligatorio.')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('El nombre de usuario ya está registrado.')
        return username

    def clean_email(self):
        return clean_email_value(self.cleaned_data.get('email'), check_unique=True)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password:
            validate_password_es(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Las contraseñas no coinciden.')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class EmailLoginForm(forms.Form):
    email = forms.CharField(
        label="Correo electrónico",
        widget=EMAIL_WIDGET,
        error_messages={"required": "El correo es obligatorio."},
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput,
        error_messages={"required": "La contraseña es obligatoria."},
    )

    def clean_email(self):
        return clean_email_value(self.cleaned_data.get("email"))
