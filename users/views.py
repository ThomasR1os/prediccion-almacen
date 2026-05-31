from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from desercion_escolar.quality import normalize_email
from .forms import UserRegisterForm, EmailLoginForm

User = get_user_model()


def _add_form_errors_to_messages(request, form):
    for field, errors in form.errors.items():
        label = field if field == '__all__' else field.capitalize()
        for error in errors:
            messages.error(request, f"{label}: {error}")


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                messages.error(
                    request,
                    'Este correo ya está registrado. Ejecuta dedupe_user_emails si ves duplicados antiguos.',
                )
            else:
                messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
                return redirect('login')
        _add_form_errors_to_messages(request, form)
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = normalize_email(form.cleaned_data['email'])
            password = form.cleaned_data['password']
            users = User.objects.filter(email__iexact=email)

            if not users.exists():
                messages.error(request, 'Correo o contraseña incorrectos.')
            else:
                if users.count() > 1:
                    messages.warning(
                        request,
                        'Hay cuentas duplicadas con este correo. Un administrador debe ejecutar: '
                        'python manage.py dedupe_user_emails --merge',
                    )

                authenticated_user = None
                for candidate in users:
                    authenticated_user = authenticate(
                        request,
                        username=candidate.username,
                        password=password,
                    )
                    if authenticated_user is not None:
                        break

                if authenticated_user is not None:
                    login(request, authenticated_user)
                    messages.success(request, f'¡Bienvenido {authenticated_user.username}!')
                    return redirect('home')
                else:
                    messages.error(request, 'Correo o contraseña incorrectos.')
        else:
            _add_form_errors_to_messages(request, form)
    else:
        form = EmailLoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')
