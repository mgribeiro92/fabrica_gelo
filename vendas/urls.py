from django.urls import path
from . import views

urlpatterns = [    
    path('pedidos/', views.pedidos, name='pedidos'),    
    path('gerenciar_vendas', views.gerenciar_vendas, name='gerenciar_vendas'),
    path('editar_venda/<int:venda_id>', views.editar_venda, name='editar_venda'),    
    path('venda_filtro/<int:venda_id>', views.venda_filtro, name='venda_filtro'),
    path('cliente_filtro/<int:cliente_id>', views.cliente_filtro, name='cliente_filtro'),
    path('clientes', views.clientes, name='clientes'),    
    path('ultima_venda', views.ultima_venda, name='ultima_venda'),
    path('pedidos_abertos', views.pedidos_abertos, name='pedidos_abertos'),
    path('', views.home, name='home')
]