from django.db import models
import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

class Conta(models.Model):
    nome = models.CharField(max_length = 20)
    saldo = models.FloatField()

    def __str__(self):
        return self.nome

    def saldo_cor(self):
        saldo_formatado = locale.currency(self.saldo, grouping=True)
        color = 'red' if self.saldo < 0 else 'green'
        return f'<span style="color: {color};">{saldo_formatado}</span>'
    
    def saldo_brasil(self):
        return locale.currency(self.saldo, grouping=True, symbol=None)
    
class CategoriaDespesa(models.Model):
    nome_categoria = models.CharField(max_length = 22)    

    def __str__(self):
        return self.nome_categoria
    
class Subcategoria(models.Model):
    categoria = models.ForeignKey(CategoriaDespesa, on_delete=models.CASCADE)
    nome_subcategoria = models.CharField(max_length=30)

    def __str__(self):
        return self.nome_subcategoria

class Despesa(models.Model):
    tipo = models.CharField(max_length=10, default="Saida")
    data = models.DateField()
    categoria = models.CharField(max_length=30)
    subcategoria = models.CharField(max_length=30, null=True)
    valor = models.FloatField()
    caixa = models.ForeignKey(Conta, on_delete = models.DO_NOTHING)
    tipo_pagamento = models.CharField(max_length=20)
    obs = models.CharField(max_length=100, null=True)

class Transferencia(models.Model):
    data = models.DateField()
    categoria_transferencia = models.CharField(max_length=30, default="Transferencia")
    valor = models.FloatField()
    caixa = models.ForeignKey(Conta, on_delete= models.DO_NOTHING)
    tipo_transferencia = models.CharField(max_length=20)

class ContasPagar(models.Model):
    data_compra = models.DateField()
    data_parcela = models.DateField()
    parcela = models.IntegerField(default=1)
    quantidade_parcelas = models.IntegerField(default=1)
    loja = models.CharField(max_length=30)
    produto = models.CharField(max_length=20)
    valor = models.FloatField(default=0)
    tipo_conta = models.CharField(max_length=100, null=True)

    def __str__(self):
        return f"{self.loja} - {self.valor}"

    def valor_brasil(self):
        return locale.currency(self.valor, grouping=True, symbol=None)
    


   