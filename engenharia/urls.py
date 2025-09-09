# Seu_projeto/urls.py

from django.urls import path
from engenharia import views

urlpatterns = [
    path('/', views.listar_urls_api, name='painel-urls'),
]
