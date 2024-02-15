from django.urls import path
from . import views


urlpatterns = [
    path('visao_geral/', views.visao_geral, name='visao_geral'),
    path('pedidos_pagos/', views.pedidos_pagos, name='pedidos_pagos'),
    path('registro_despesa/', views.registro_despesa, name='registro_despesa'),
    path('historico_caixas', views.historico_caixas, name='historico_caixas'),
    path('transferencia', views.transferencia, name='transferencia'),
    path('entrada_saida', views.entrada_saida, name='entrada_saida'),
    path('contas_pagar', views.contas_pagar, name='contas_pagar'),
    path('cheque_boleto', views.cheque_boleto, name='cheque_boleto'),
    path('historico_despesa', views.historico_despesa, name='historico_despesa'),
    path('editar_despesa/<int:despesa_id>', views.editar_despesa, name='editar_despesa'),
]
