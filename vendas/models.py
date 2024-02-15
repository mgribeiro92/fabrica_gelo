from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import datetime
from financeiro.models import Conta
import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

class Embalagem(models.Model):
    nome = models.CharField(max_length = 20)
    estoque = models.IntegerField()

    def __str__(self):
        return self.nome

class Produto(models.Model):
    tipo_choice = (
        ('C', 'Cubo'),
        ('T', 'Triturado')
    )
    nome = models.CharField(max_length = 10)
    tipo = models.CharField(max_length = 1, choices = tipo_choice)
    valor_unitario = models.FloatField()
    embalagem = models.ForeignKey(Embalagem, on_delete= models.DO_NOTHING)
    estoque = models.IntegerField()
    kg = models.IntegerField(default=0)

    def __str__(self):
        return self.nome
    
class Freezer(models.Model):
    tipo = models.CharField(max_length=20)
    tamanho = models.IntegerField()   
   
    
    def __str__(self):
        return f'{self.tipo} - {self.tamanho} LTS'

class Cliente(models.Model):
    nome = models.CharField(max_length = 30)
    cidade = models.CharField(max_length = 20)
    telefone = models.CharField(max_length= 20, blank=True)
    status = models.BooleanField(default=True) 
    freezer = models.ForeignKey(Freezer, on_delete= models.DO_NOTHING)
    valor_receber = models.FloatField(default=0)    

    def __str__(self):
        return self.nome
    
    def status_cliente(self):
        if self.status == True:
            texto = "Ativo"            
        else:
            texto = "Inativo"         
        return texto
    
    def valor_receber_brasil(self):        
        return locale.currency(self.valor_receber, grouping=True, symbol=None)
        
class Pedido(models.Model):
    produto = models.ForeignKey(Produto, on_delete = models.DO_NOTHING)
    quantidade = models.IntegerField()
    valor_unitario = models.FloatField()
    valor_pedido = models.FloatField(default=0)   
    
    def __str__(self):
        return self.produto.nome

class PagamentoVenda(models.Model):
    tipo = models.CharField(max_length=10, default="Entrada")
    data = models.DateField(default='2023-01-01')
    valor_recebido_pagamento = models.FloatField(default= 0)    
    desconto = models.FloatField()
    juros = models.FloatField(default=0)
    caixa = models.ForeignKey(Conta, on_delete=models.CASCADE)
    tipo_pagamento = models.CharField(max_length=20)
    usuario = models.ForeignKey(User, on_delete = models.DO_NOTHING)
    cliente = models.CharField(max_length=30)

    def __str__(self):
        return str(self.id)

class Venda(models.Model):
    status_pagamento_choice = (
        ('A', 'Em aberto'),        
        ('R', 'Recebido'),
        ('C', 'Cancelado'),
        ('RP', 'Recebido Parcialmente')        
    )
    usuario = models.ForeignKey(User, on_delete = models.DO_NOTHING)
    cliente = models.ForeignKey(Cliente, on_delete = models.DO_NOTHING)
    produto = models.ManyToManyField(Pedido)
    data = models.DateField()
    boleto = models.BooleanField(default=False, null=True, blank=True)
    status_pago = models.CharField(max_length=2, choices=status_pagamento_choice, default="A")
    valor_total = models.FloatField(default=0)
    valor_receber = models.FloatField(default=0)
    valor_recebido = models.FloatField(default=0)
    pagamento =  models.ManyToManyField(PagamentoVenda)
    prazo = models.CharField(max_length=20)
    nfe = models.BooleanField(default=False, null=True, blank=True)    
    
    def __str__(self):
        return str(self.id)
        
    def badge_template_pagamento(self):
        if self.status_pago == "A":
            classes = 'bg-warning'
            texto = "Em aberto"
        elif self.status_pago == "R":
            classes = 'bg-success'
            texto = "Recebido"
        elif self.status_pago == "RP":
            classes = 'bg-info'
            texto = "Recebido Parcialmente"        
        else: 
            classes = 'bg-danger'
            texto = "Cancelado"
        
        return mark_safe(f'<span style="border-radius: 5px; color: white" class="{classes} px-1">{texto}</span>')
    
    def badge_template_prazo(self):
        if self.prazo == "Boleto":
            classes = 'bg-warning'
            texto = "Boleto"   
        elif self.prazo == "Cheque a Vista":
            classes = 'bg-success'
            texto = "Cheque a Vista"
        elif self.prazo == "Cheque a Prazo":
            classes = 'bg-info'
            texto = "Cheque a Prazo"       
        
        return mark_safe(f'<span style="border-radius: 5px" class="{classes} px-1">{texto}</span>')
           
class PagamentoPrazo(models.Model):    
    tipo_pagamento = models.CharField(max_length=20)
    prazo = models.BooleanField()
    venda = models.ForeignKey(Venda, on_delete= models.DO_NOTHING)
    data_prevista = models.DateField()    
    valor = models.FloatField()
    desconto = models.FloatField(default=0, null=True)
    usuario = models.ForeignKey(User, on_delete = models.DO_NOTHING, default=None)
    obs = models.CharField(max_length = 40, null=True)   

    def __str__(self):
        return str(self.id)
    
    def badge_prazo(self):
        if self.prazo == True:
            classes = 'bg-warning'
            texto = "Sim" 
        elif self.prazo == False:
            classes = 'bg-success'
            texto = "Não"

        return mark_safe(f'<span style="border-radius: 5px; color: white" class="{classes} px-1">{texto}</span>')