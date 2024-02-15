from django.db import models
from vendas.models import Produto

class ProdutoProducao(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    quantidade_kg = models.IntegerField(default=0)
    funcionario = models.CharField(max_length = 20)

    def __str__(self):
        return str(self.produto)

class Producao(models.Model):
    data = models.DateField()
    dia_semana = models.CharField(max_length=20)
    produto = models.ManyToManyField(ProdutoProducao)
    total_kg = models.IntegerField(default=0)    

    def __str__(self):
        return str(self.id)

