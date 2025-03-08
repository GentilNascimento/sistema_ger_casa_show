from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (EventoCreateView, 
                    EventoListView, 
                    #EventoDetailView, 
                    EventoUpdateView, 
                    EventoDeleteView
)
from artistas.views import ArtistaViewSet, MessageViewSet


router = DefaultRouter()
router.register(r'artistas', ArtistaViewSet)
router.register(r'mensagens', MessageViewSet)

 


urlpatterns = [
    path('', include(router.urls)),  #urls do router
    path('eventos/list/', EventoListView.as_view(), name='evento_list'),
    path('eventos/create/', EventoCreateView.as_view(), name='evento_create'),
    #path('eventos/<int:pk>/detail/', EventoDetailView.as_view(), name='evento_detail'),
    path('eventos/<int:pk>/update/', EventoUpdateView.as_view(), name='evento_update'),
    path('eventos/<int:pk>/delete/', EventoDeleteView.as_view(), name='evento_delete'),
 ]
