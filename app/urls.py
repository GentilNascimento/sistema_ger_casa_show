#url principal
from django.contrib import admin
from django.urls import path, include
from accounts.views import login_view, logout_view, register_view
from django.views.generic import TemplateView
from datetime import datetime
from eventos.models import Evento
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from .views import anotacoes_view
 
#Documentação da API
schema_view = get_schema_view(
    openapi.Info(
        title="Gestão de Eventos API",
        default_version='v1',
        description="Documentação da API do sist de envio de msg agendadas",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="gentilrn.65@hotmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,), #ao público
)



class HomeView(TemplateView):
    template_name = 'base.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['eventos_proximos'] = Evento.objects.filter(
            data__gte=datetime.now()).order_by('data')
        context['show_proximos_eventos'] = True
        return context


urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), 
         name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), 
         name='schema-redoc'),
    path('api-auth/', include('rest_framework.urls')),  #Caso esteje usando DRF
    path('admin/', admin.site.urls),  
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('eventos/', include('eventos.urls')),
    path('artistas/', include('artistas.urls')),
    path('', HomeView.as_view(), name='home'),
    path('anotacoes/', anotacoes_view, name='anotacoes'),
]
