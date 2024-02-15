from django.contrib import admin
from .models import Produto, Cliente, Pedido, Venda, PagamentoVenda, Freezer, PagamentoPrazo, Embalagem

admin.site.register(Produto)
admin.site.register(Cliente)
admin.site.register(Pedido)
admin.site.register(Venda)
admin.site.register(PagamentoVenda)
admin.site.register(Freezer)
admin.site.register(PagamentoPrazo)
admin.site.register(Embalagem)



