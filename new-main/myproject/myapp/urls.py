
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('afficher-donnees/', views.afficher_donnees, name='afficher_donnees'),
    path('actualiser-donnees/', views.actualiser_donnees, name='actualiser_donnees'),
    path('filtrer-donnees/', views.filtrer_donnees, name='filtrer_donnees'),
    path('exporter-donnees/', views.exporter_donnees, name='exporter_donnees'),
    path('graph/', views.graph_view, name='graph_view'),
    path('update-piece/<int:capteur_id>/', views.update_piece, name='update_piece'),
]
