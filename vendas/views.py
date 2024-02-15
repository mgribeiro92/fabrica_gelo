from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Produto, Venda, Cliente, Pedido, PagamentoVenda, Conta, Freezer, PagamentoPrazo
from datetime import datetime, timedelta
from django.contrib.messages import constants
from django.contrib import messages
from django.utils import timezone
import locale
import json
from django.db.models import Max

@login_required(login_url='/')
def pedidos(request):
    produtos = Produto.objects.all()
    cliente = Cliente.objects.all().order_by('nome')

    data = datetime.now().date()
    data_atual = data.strftime('%Y-%m-%d')     

    if request.method == "GET":
        return render(request, "pedidos.html", {'produtos': produtos, 'clientes': cliente, 'data_atual': data_atual})
    
    elif request.method == "POST":
        produtos_id = request.POST.getlist('produtos')
        produto_selecionados = Produto.objects.filter(id__in = produtos_id)
     
        cliente = request.POST.get('cliente')
        cliente_selecionado = Cliente.objects.filter(nome = cliente).first()
        quantidade_produto = request.POST.getlist('quantidade_produto')
        valor_unitario = request.POST.getlist('valor_unitario')
        data = request.POST.get('data')
        
        quantidade_preenchidas = [indice for indice, item in enumerate(quantidade_produto) if item != ""]       
        indice_produtos = [int(item) - 1 for item in produtos_id]

        if indice_produtos != quantidade_preenchidas:
            messages.add_message(request, constants.ERROR, 'A quantidade preenchida não corresponde ao produto selecionado!')     
            return redirect('pedidos')

        itens_vazios = [indice for indice, item in enumerate(quantidade_produto) if item == ""]
        for indice in reversed(itens_vazios):
            del quantidade_produto[indice]
            del valor_unitario[indice]

        quantidade_produto = [int(i) for i in quantidade_produto]
        valor_unitario = [float(i.replace(',', '.')) for i in valor_unitario]            
        valores_pedidos = [a * b for a, b in zip(quantidade_produto, valor_unitario)]
        total_venda = sum(valores_pedidos)     
      
        if not produto_selecionados:
            messages.add_message(request, constants.ERROR, 'Produto nao foi preenchido!')     
            return redirect('pedidos')
            
        try:
            venda = Venda(
                usuario = request.user,
                cliente = cliente_selecionado,
                data = data,        
                valor_total = total_venda,
                valor_receber = total_venda,
                valor_recebido = 0,                     
            )    
            venda.save()

            venda.cliente.valor_receber += total_venda
            venda.cliente.save()      
        
            index = 0
            for produto in produto_selecionados:
                solicitacao_pedido_temp = Pedido(
                    produto = produto,
                    quantidade = quantidade_produto[index],
                    valor_unitario = valor_unitario[index],
                    valor_pedido = valores_pedidos[index],
                )
                solicitacao_pedido_temp.save()
                produto.estoque -= quantidade_produto[index]
                produto.save()
                venda.produto.add(solicitacao_pedido_temp)
                index += 1        
            venda.save()

            nfe_vista = request.POST.get('nfe_vista')
            nfe_prazo = request.POST.get('nfe_prazo')

            if nfe_prazo == "on":
                pagamento_prazo = PagamentoPrazo(
                    tipo_pagamento = "Boleto",
                    prazo = True,
                    usuario = request.user,
                    venda = venda,
                    data_prevista = datetime.now() + timedelta(days=7),
                    valor = total_venda,
                )
                pagamento_prazo.save()
                venda.prazo = "Boleto"
                venda.boleto = True
                venda.nfe = True
                venda.save()

            elif nfe_vista == "on":                
                venda.nfe = True
                venda.save()

            messages.add_message(request, constants.SUCCESS, 'Venda registrada com sucesso!')       
            return redirect('ultima_venda')
        except:
            messages.add_message(request, constants.ERROR, 'Venda não registrada')
            return redirect('pedidos')
     
@login_required
def ultima_venda(request):
    if request.method == "GET":
        ultima_venda =  Venda.objects.last()
        ultimo_pedido = Venda.objects.filter(id= ultima_venda.id)

        return render(request, 'resumo_pedido.html', {'ultima_venda': ultima_venda,
                                            'ultimo_pedido': ultimo_pedido} )

@login_required(login_url='/')
def gerenciar_vendas(request):
    if request.method == "GET":
        data_hoje = datetime.now()
        data_15_dias_atras = data_hoje - timedelta(days=15)
        vendas = Venda.objects.filter(data__gte=data_15_dias_atras, data__lte=data_hoje).order_by("-id")
        #vendas = Venda.objects.all().exclude(valor_receber = 0).order_by("-id")
    
        data = request.GET.get('data')
        # if data:
        #     vendas = vendas.filter(data__contains= data)
        # elif data == "":
        #     vendas = []

        status_pagamento = request.GET.get('status')        
        
        if status_pagamento and data == "":
            if status_pagamento == "Em aberto":
                status_pagamento = "A"
                vendas = vendas.filter(status_pago = status_pagamento)
            elif status_pagamento == "Recebido":
                status_pagamento = "R"
                vendas = vendas.filter(status_pago = status_pagamento)
            elif status_pagamento == "Cancelado":
                status_pagamento = "C"
                vendas = vendas.filter(status_pago= status_pagamento)
            elif status_pagamento == "Todos os pedidos":
                vendas = Venda.objects.filter(data__gte=data_15_dias_atras, data__lte=data_hoje).order_by("-id")
            
        if data != "" and status_pagamento:
            if status_pagamento == "Em aberto":
                status_pagamento = "A"
                vendas = vendas.filter(status_pago= status_pagamento).filter(data__contains = data)
            elif status_pagamento == "Recebido":
                status_pagamento = "R"
                vendas = vendas.filter(status_pago= status_pagamento).filter(data__contains = data)
            elif status_pagamento == "Cancelado":
                status_pagamento = "C"
                vendas = vendas.filter(status_pago= status_pagamento).filter(data__contains = data)
            elif status_pagamento == "Todos os pedidos":
                vendas = vendas.filter(data__contains = data)
        
        limpar = request.GET.get('limpar')
        if limpar:
            vendas = Venda.objects.filter(data__gte=data_15_dias_atras, data__lte=data_hoje).order_by("-id")

        valores_vendas = [venda.valor_total for venda in vendas]
        valores_vendas = sum(valores_vendas)
        valores_vendas = locale.currency(valores_vendas, grouping=True, symbol=None)

        valor_receber_vendas = [venda.valor_receber for venda in vendas]
        valor_receber_vendas = sum(valor_receber_vendas)
        valor_receber_vendas = locale.currency(valor_receber_vendas, grouping=True, symbol=None)

        valor_recebido_vendas = [venda.valor_recebido for venda in vendas]
        valor_recebido_vendas = sum(valor_recebido_vendas)
        valor_recebido_vendas = locale.currency(valor_recebido_vendas, grouping=True, symbol=None)

        data_atual = datetime.now().date()
        data_atual = data_atual.strftime('%Y-%m-%d')

        if data:
            data = datetime.strptime(data, "%Y-%m-%d")
            data = data.strftime("%d de %B")

        return render(request, 'gerenciar_vendas.html', {'vendas': vendas,
                                                         'data_atual': data_atual,
                                                         'data_hoje': data_hoje.date,
                                                         'data_15': data_15_dias_atras.date,
                                                         'valor_total': valores_vendas,
                                                         'valor_receber': valor_receber_vendas,
                                                         'valor_recebido': valor_recebido_vendas,
                                                         'data_pesquisa': data})

@login_required(login_url='/')
def venda_filtro(request, venda_id):
    if request.method == "GET":
        venda = Venda.objects.get(id= venda_id)       
        pagamentos = venda.pagamento.all()        
        venda_lista = Venda.objects.filter(id = venda_id)

        valor_receber = str(venda.valor_receber)        
        data = datetime.now().date()
        data_atual = data.strftime('%Y-%m-%d')       
        
        url_venda_filtro = reverse('venda_filtro', kwargs={'venda_id': venda_id})        
        pagamentos_prazo = PagamentoPrazo.objects.filter(venda = venda)
        
        cancelar_venda = request.GET.get('cancelar')
        if cancelar_venda:
            dias_venda = datetime.now().date() - venda.data
            try:
                if venda.status_pago == 'R':
                    messages.add_message(request, constants.ERROR, 'O pedido não foi cancelado porque tem recebimentos realizados!')
                    return redirect(url_venda_filtro)
                elif venda.status_pago == 'C':
                    messages.add_message(request, constants.ERROR, 'O pedido ja foi cancelado!')
                    return redirect(url_venda_filtro)                        
                elif dias_venda.days >= 3:
                    messages.add_message(request, constants.ERROR, 'A venda nao pode ser cancelada depois de 3 dias!')     
                    return redirect(url_venda_filtro)
                else:
                    venda.cliente.valor_receber -= venda.valor_total
                    venda.cliente.save()
                    venda.status_pago = "C"
                    venda.valor_receber = 0
                    venda.valor_total = 0                                      
                    venda.save()                  
                    messages.add_message(request, constants.SUCCESS, 'Pedido cancelado!')
                    return redirect(url_venda_filtro)
            except:
                messages.add_message(request, constants.ERROR, 'O pedido não cancelado: erro no sistema!')
                return redirect(url_venda_filtro)

        return render(request, 'venda_filtro.html', {'venda': venda,
                                                     'valor_receber': valor_receber, 
                                                     'pagamentos': pagamentos, 
                                                     'venda_lista': venda_lista,
                                                     'pagamentos_prazo': pagamentos_prazo,
                                                     'data_atual': data_atual})
    
    elif request.method == "POST":
        valor_recebido_pagamento = request.POST.get('valor_recebido')
        data_recebimento = request.POST.get('data_recebimento')
        desconto = request.POST.get('desconto')        
        caixa = request.POST.get('caixa')
        tipo_pagamento = request.POST.get('tipo_pagamento')
        status_pagamento = "R"

        data_cheque = request.POST.get('data_cheque')
        valor_cheque = request.POST.get('valor_cheque')
        desconto_cheque = request.POST.get('desconto_cheque')     

        venda_paga = Venda.objects.get(id = venda_id)

        if valor_recebido_pagamento:
            valor_recebido_pagamento = float(valor_recebido_pagamento)
            desconto = float(desconto)
            caixa_selecionado = Conta.objects.filter(nome= caixa).first()
            # juros  = float(juros)
            # juros_desconto = desconto - juros            

            valor_recebimento_total = valor_recebido_pagamento + venda_paga.valor_recebido        
            if valor_recebido_pagamento > venda_paga.valor_total or valor_recebimento_total > venda_paga.valor_total:
                messages.add_message(request, constants.ERROR, 'Valor de pagamento maior que o pedido')
            else:
                pagamento = PagamentoVenda(
                    data = data_recebimento,
                    usuario = request.user,
                    valor_recebido_pagamento = valor_recebido_pagamento,
                    desconto = desconto,                    
                    tipo_pagamento = tipo_pagamento,
                    caixa = caixa_selecionado,
                    cliente = venda_paga.cliente
                )
                pagamento.save()
                venda_paga.pagamento.add(pagamento)
                
                venda_paga.status_pago = status_pagamento        
                venda_paga.valor_recebido += valor_recebido_pagamento
                venda_paga.valor_receber = (venda_paga.valor_total - venda_paga.valor_recebido) - desconto
               
                if venda_paga.valor_receber != 0:
                    venda_paga.status_pago = "RP"
                else:
                    venda_paga.status_pago = "R"
                venda_paga.cliente.valor_receber -= valor_recebido_pagamento + desconto

            
            caixa_selecionado.saldo += valor_recebido_pagamento
            caixa_selecionado.save()
            
            venda_paga.cliente.save()
            venda_paga.save()
            messages.add_message(request, constants.SUCCESS, 'Valor recebido com sucesso')      

        #RECEBIMENTO CHEQUE
        elif data_cheque and valor_cheque:            
            data_cheque = datetime.strptime(data_cheque, "%Y-%m-%d")
            desconto_cheque = float(desconto_cheque)            
            if data_cheque.date() == datetime.now().date():
                prazo = False
            else:
                prazo = True       
            valor_cheque = float(valor_cheque)

            if valor_cheque <= 0:                
                messages.add_message(request, constants.ERROR, 'Valor do cheque inserido incorretamente')
            else:           
                valor_recebimento_total = valor_cheque + venda_paga.valor_recebido        
                if valor_cheque > venda_paga.valor_total or valor_recebimento_total > venda_paga.valor_total:
                    messages.add_message(request, constants.ERROR, 'Valor de pagamento maior que o pedido')
                
                pagamento_prazo = PagamentoPrazo(
                    tipo_pagamento = "Cheque",
                    prazo = prazo,
                    usuario = request.user,
                    venda = venda_paga,
                    data_prevista = data_cheque,
                    valor = valor_cheque,
                    desconto = desconto_cheque
                )
                pagamento_prazo.save()
                
                venda_paga.valor_recebido += valor_cheque
                venda_paga.valor_receber = (venda_paga.valor_total - venda_paga.valor_recebido) - desconto_cheque
                if venda_paga.valor_receber != 0:
                    venda_paga.status_pago = "RP"
                else:
                    venda_paga.status_pago = "R"
                venda_paga.cliente.valor_receber -= valor_cheque + desconto_cheque

                if prazo == True:
                    venda_paga.prazo = "Cheque a Prazo"
                else:
                    venda_paga.prazo = "Cheque a Vista"
                venda_paga.save()
                venda_paga.cliente.save()            
                messages.add_message(request, constants.SUCCESS, 'Cheque cadastrado com sucesso')
        else:
            messages.add_message(request, constants.ERROR, 'Favor preencher os dados corretamente')
            
        return redirect('gerenciar_vendas')

@login_required(login_url='/')
def cliente_filtro(request, cliente_id):
    if request.method == "GET":
        cliente = Cliente.objects.get(id= cliente_id)   
        vendas_cliente = Venda.objects.filter(cliente = cliente).order_by("-id")
        freezers = Freezer.objects.all().order_by('tamanho')

        pedidos_abertos = request.GET.get('pedidos_abertos')
        if pedidos_abertos:
            vendas_cliente = vendas_cliente.filter(status_pago__in=["A", "RP"]).order_by('-data')

        return render(request, 'cliente_filtro.html', {'vendas_cliente': vendas_cliente, 
                                                       'cliente': cliente,
                                                       'freezers': freezers})
    elif request.method == "POST":
        return redirect()

@login_required(login_url='/')
def home(request):    
    return render(request, 'home.html')

@login_required(login_url='/')
def editar_venda(request, venda_id):    
    venda = Venda.objects.filter(id=venda_id).first()

    if request.method == "GET":       
        url_venda_filtro = reverse('venda_filtro', kwargs={'venda_id': venda_id})
        dias_venda = datetime.now().date() - venda.data        
        # if dias_venda.days >= 3:
        #     messages.add_message(request, constants.ERROR, 'A venda nao pode ser editada depois de 3 dias!')     
        #     return redirect(url_venda_filtro)
        
        if venda.status_pago == "R" or venda.status_pago == "RP":
            messages.add_message(request, constants.ERROR, 'A venda com recebimentos não pode ser editada!')     
            return redirect(url_venda_filtro)
        
        venda = Venda.objects.filter(id=venda_id).first()
        clientes = Cliente.objects.all()
        produtos = Produto.objects.all()
    
        produtos_selecionados = [ pedido.produto.nome for pedido in venda.produto.all() ]
        quantidade_produtos = [ pedido.quantidade for pedido in venda.produto.all() ]
        valor_unitario = [ pedido.valor_unitario for pedido in venda.produto.all() ]        

        produtos_nome = [ produto.nome for produto in produtos]
        indices_produtos = [produtos_nome.index(item) for item in produtos_selecionados]

        valor_unitario_produtos = [ produto.valor_unitario for produto in Produto.objects.all() ]       

        for indice, valor in zip(indices_produtos, valor_unitario):
            valor_unitario_produtos[indice] = valor

        i = 0
        quantidade_preencher = [""] * 4
        for quantidade in quantidade_produtos:
            quantidade_preencher[indices_produtos[i]] = quantidade
            i += 1

        return render(request, 'editar_venda.html', {'venda': venda,
                                                    'clientes': clientes,
                                                    'produtos': produtos,
                                                    'produtos_selecionados': produtos_selecionados,
                                                    'quantidade_preencher': quantidade_preencher,
                                                    'valor_unitario_produtos': valor_unitario_produtos})

    if request.method == "POST":
        #Retornando o valor que o cliente deve        
        cliente_anterior = Cliente.objects.get(id = venda.cliente.id)        
        cliente_anterior.valor_receber -= venda.valor_total        
        cliente_anterior.save()

        produtos_id = request.POST.getlist('produtos')
        produto_selecionados = Produto.objects.filter(id__in = produtos_id)
     
        cliente = request.POST.get('cliente')
        cliente_selecionado = Cliente.objects.filter(nome = cliente).first()
        quantidade_produto = request.POST.getlist('quantidade_produto')
        valor_unitario = request.POST.getlist('valor_unitario')
        
        quantidade_preenchidas = [indice for indice, item in enumerate(quantidade_produto) if item != ""]       
        indice_produtos = [int(item) - 1 for item in produtos_id]

        if indice_produtos != quantidade_preenchidas:
            messages.add_message(request, constants.ERROR, 'A quantidade preenchida não corresponde ao produto selecionado!')     
            return redirect('pedidos')

        itens_vazios = [indice for indice, item in enumerate(quantidade_produto) if item == ""]
        for indice in reversed(itens_vazios):
            del quantidade_produto[indice]
            del valor_unitario[indice]

        quantidade_produto = [int(i) for i in quantidade_produto]
        valor_unitario = [float(i.replace(',', '.')) for i in valor_unitario]            
        valores_pedidos = [a * b for a, b in zip(quantidade_produto, valor_unitario)]
        total_venda = sum(valores_pedidos)     

        
        if not produto_selecionados:
            messages.add_message(request, constants.ERROR, 'Produto nao foi preenchido!')     
            return redirect('pedidos')        

        venda.cliente = cliente_selecionado        
        venda.valor_total = total_venda
        venda.valor_receber = total_venda
        venda.save()        
        venda.cliente.valor_receber += venda.valor_total
        venda.cliente.save()

        for pedido in venda.produto.all():
            pedido.delete()
            pedido.save()

        index = 0
        for produto in produto_selecionados:
            solicitacao_pedido_temp = Pedido(
                produto = produto,
                quantidade = quantidade_produto[index],
                valor_unitario = valor_unitario[index],
                valor_pedido = valores_pedidos[index],
            )
            solicitacao_pedido_temp.save()
            venda.produto.add(solicitacao_pedido_temp)
            index += 1        
        venda.save()

        nfe_vista = request.POST.get('nfe_vista')
        nfe_prazo = request.POST.get('nfe_prazo')

        if nfe_prazo == "on":
            pagamento_prazo = PagamentoPrazo(
                tipo_pagamento = "Boleto",
                prazo = True,
                usuario = request.user,
                venda = venda,
                data_prevista = datetime.now() + timedelta(days=7),
                valor = total_venda,
            )
            pagamento_prazo.save()
            venda.prazo = "Boleto"
            venda.boleto = True
            venda.nfe = True
            venda.save()

        elif nfe_vista == "on":                
            venda.nfe = True
            venda.save()
        
        messages.add_message(request, constants.SUCCESS, 'Venda editada com sucesso!')       
        return redirect('gerenciar_vendas')
        # except:
        #     messages.add_message(request, constants.ERROR, 'Venda não registrada')
        #     return redirect('pedidos')

        return render(request, 'editar_venda.html')
    
@login_required(login_url='/')
def clientes(request):
    if request.method == "GET":      
        freezers = Freezer.objects.all().order_by('tamanho')        
        clientes = Cliente.objects.annotate(ultima_venda=Max('venda__data')).order_by('nome')       

        cliente = request.GET.get('cliente')
        print(cliente)
        freezer = request.GET.get('freezer')
        if cliente:
            clientes = clientes.filter(nome__icontains = cliente)
            print(clientes)

        if freezer:            
            clientes = clientes.filter(freezer = freezer)            

        limpar = request.GET.get('limpar')
        if limpar:
            clientes = Cliente.objects.annotate(ultima_venda=Max('venda__data')).order_by('nome')
            

        return render(request, 'clientes.html', {"clientes": clientes, "freezers": freezers})
    
    elif request.method == "POST":
        nome_cliente = request.POST.get('nome')
        cidade = request.POST.get('cidade')
        telefone = request.POST.get('telefone')
        freezer = request.POST.get('freezer')   

        cliente_existente = Cliente.objects.filter(nome = nome_cliente)
        if len(nome_cliente) == 0 or len(cidade) == 0:
            messages.add_message(request, constants.ERROR, 'Preencha os dados corretamente')     
            return redirect('clientes')
        
        if cliente_existente.exists():     
            messages.add_message(request, constants.ERROR, 'Esse cliente ja existe')     
            return redirect('clientes')

        freezer_selecionado = Freezer.objects.filter(id = freezer).first()

        try:
            cliente = Cliente(
                nome = nome_cliente,
                cidade = cidade,
                telefone = telefone,
                freezer = freezer_selecionado,
            )
            cliente.save()
            messages.add_message(request, constants.SUCCESS, 'Cliente cadastrado com sucesso')
            return redirect('clientes')
        except:
            messages.add_message(request, constants.ERROR, 'Erro interno do sistema')
        return redirect('clientes')

@login_required(login_url='/')
def pedidos_abertos(request):
    vendas = Venda.objects.filter(status_pago__in=["A", "RP"]).order_by('-data')
    clientes = [ venda.cliente for venda in vendas ]
    clientes = list(set(clientes))
    
    cliente = request.GET.get('cliente')
    if cliente:
        cliente = Cliente.objects.get(nome = cliente)
        vendas = vendas.filter(cliente = cliente)      

    limpar = request.GET.get('limpar')
    if limpar:
        clientes = Cliente.objects.all().order_by('nome')

    total_receber = [ venda.valor_receber for venda in vendas]
    total_receber = sum(total_receber)

    return render(request, 'pedidos_abertos.html', {'vendas': vendas,
                                                    'clientes': clientes,
                                                    'total_receber': total_receber})