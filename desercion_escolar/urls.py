"""
URL configuration for desercion_escolar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from users import views as login_views
from prediction import views_2 as prediction_views
from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', login_views.register_view, name='register'),  # Ruta para el registro
    path('',login_views.login_view,name='login'),
    path('home/',prediction_views.home,name='home'),
    path('prediction/',prediction_views.predecir,name='prediction'),
    path('health/', prediction_views.health, name='health'),
    path('acerca/',prediction_views.acerca,name='acerca'),
    ## Aquí defines directamente las rutas del dashboard sin usar include()
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    path('dashboard/data/', dashboard_views.dashboard_data, name='dashboard_data'),
    path('dashboard/pdf/', dashboard_views.descargar_pdf, name='descargar_pdf'),
    path('operaciones/', include('operaciones.urls')),
    path('logout/', login_views.logout_view, name='logout'),
   # path('resultados/', prediction_views.mostrar_resultados, name='mostrar_resultados'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)