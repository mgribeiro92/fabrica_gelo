from django.contrib import admin
from .models import Conta, Despesa, CategoriaDespesa, Transferencia, ContasPagar, Subcategoria

admin.site.register(Conta)
admin.site.register(Despesa)
admin.site.register(CategoriaDespesa)
admin.site.register(Subcategoria)
admin.site.register(Transferencia)
admin.site.register(ContasPagar)
