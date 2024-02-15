from django.urls import path
from . import views

urlpatterns = [
    path('', views.producao, name='producao'),
    path('historico_producao', views.historico_producao, name='historico_producao'),
    path('cadastrar_producao', views.cadastrar_producao, name='cadastrar_producao'),
    path('historico_produtos', views.historico_produtos, name='historico_produtos'),  
]