from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from desercion_escolar.quality import normalize_email

User = get_user_model()


class UserRegisterForm(forms.ModelForm):
    username = forms.CharField(
        label='Usuario',
        required=True,
        help_text='Puedes ingresar cualquier combinación de caracteres.',
        widget=forms.TextInput,
    )
    email = forms.EmailField(
        label='Correo electrónico',
        required=True,
        help_text='Debe ser único. No podrás registrar el mismo correo dos veces.',
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text="Mínimo 8 caracteres. Debe cumplir las reglas de seguridad del sistema.",
    )
    password_confirm = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput,
        help_text="Confirma la contraseña.",
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise ValidationError('El nombre de usuario es obligatorio.')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('El nombre de usuario ya está registrado.')
        return username

    def clean_email(self):
        email = normalize_email(self.cleaned_data.get('email'))
        if not email:
            raise ValidationError('El correo es obligatorio.')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Este correo ya está registrado. Si olvidaste tu contraseña, contacta al administrador.')
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password')
        validate_password(password)
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
    email = forms.EmailField(label="Correo electrónico")
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
