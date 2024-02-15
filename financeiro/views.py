from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from vendas.models import Produto, Venda, Cliente, Pedido, Conta, PagamentoVenda, PagamentoPrazo
from .models import CategoriaDespesa, Despesa, Transferencia, ContasPagar, Subcategoria
from datetime import datetime, timedelta
from django.contrib.messages import constants
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
import json
import calendar
import locale
from django.http import JsonResponse
from dateutil.relativedelta import relativedelta
import plotly.express as px
from django.db.models import Max, Min

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')



@login_required(login_url='/')
def visao_geral(request):
    contas = Conta.objects.all()
    clientes = Cliente.objects.all()    
    clientes_devedores = Cliente.objects.filter(valor_receber__gt = 0).order_by('-valor_receber')
    pagamentos_prazo = PagamentoPrazo.objects.all().order_by('-data_prevista')

    clientes_dic = []
    vendas_aberto = Venda.objects.filter(status_pago__in=["A", "RP"]).order_by('data')   
    for venda in vendas_aberto:
        cliente = venda.cliente                  
        dias_venda = datetime.now().date() - venda.data
        dias_venda = dias_venda.days           
        cliente_existente = next((item for item in clientes_dic if item['cliente'] == cliente), None)

        if not cliente_existente:
            novo_cliente_dic = {'cliente': cliente, 'valor_receber': cliente.valor_receber, 'dias': dias_venda}
            clientes_dic.append(novo_cliente_dic)
    clientes_dic = sorted(clientes_dic, key=lambda x: x['valor_receber'], reverse=True)

    total_receber = [ cliente['valor_receber'] for cliente in clientes_dic ]
    total_receber = sum(total_receber)
    total_receber = locale.currency(total_receber, grouping=True)

    for cliente in clientes_dic:
        cliente['valor_receber'] = locale.currency(cliente['valor_receber'], grouping=True)
        
    mes = datetime.now().month
    vendas_mes = Venda.objects.filter(data__month = mes)  
    
    total_mes = 0
    for venda in vendas_mes:
        total_mes += venda.valor_total
    total_mes = locale.currency(total_mes, grouping=True)

    saldo_total = 0
    for conta in contas:
        saldo_total += conta.saldo
    saldo_total = locale.currency(saldo_total, grouping=True)
    
    
    total_cheque_boleto = [ pagamento.valor for pagamento in PagamentoPrazo.objects.all() ]
    total_cheque_boleto = sum(total_cheque_boleto)
    total_cheque_boleto = locale.currency(total_cheque_boleto, grouping=True)

    total_pagar = [ conta.valor for conta in ContasPagar.objects.all() ]
    total_pagar = sum(total_pagar)
    total_pagar = locale.currency(total_pagar, grouping=True)

    despesa_mes = Despesa.objects.filter(data__month = mes )
    total_despesas = [ despesa.valor for despesa in despesa_mes ]
    total_despesas = sum(total_despesas)
    total_despesas = locale.currency(total_despesas, grouping=True)
    
    numero_do_mes = datetime.now().month
    mes_atual = calendar.month_name[numero_do_mes].capitalize()

    nome_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

    contas_pagar_mes = ContasPagar.objects.annotate(
            mes=ExtractMonth('data_parcela'),            
            ano=ExtractYear('data_parcela')
        ).values('ano', 'mes').annotate(valor=Sum('valor'))
    contas_pagar_mes = sorted(contas_pagar_mes, key=lambda x: x['mes'])
    
    for conta in contas_pagar_mes:
        conta['valor'] = locale.currency(conta['valor'], grouping=True)

    for item in contas_pagar_mes:
        numero_mes = item['mes']
        nome_mes = nome_meses[numero_mes-1]          
        item['mes'] = nome_mes

    data = datetime.now().date()
    data_atual = data.strftime('%Y-%m-%d')
    
    
    return render(request, 'visao_geral.html', {'contas': contas, 
                                                'saldo_total': saldo_total, 
                                                'total_receber': total_receber,
                                                'clientes_devedores': clientes_devedores,
                                                'mes_atual': mes_atual,
                                                'total_mes': total_mes,
                                                'total_pagar': total_pagar,
                                                'contas_pagar_mes': contas_pagar_mes,
                                                'total_despesas': total_despesas,
                                                'clientes_dic': clientes_dic,
                                                'data_atual': data_atual,
                                                'total_cheque_boleto': total_cheque_boleto,
                                                'pagamentos_prazo': pagamentos_prazo})

@login_required(login_url='/')
def pedidos_pagos(request):
    vendas = Venda.objects.filter(valor_receber = 0)
    data = request.GET.get('data')

    if data:
        vendas = vendas.filter(data__contains= data)

    return render(request, 'pedidos_pagos.html', {'vendas': vendas})

@login_required(login_url='/')
def registro_despesa(request):       
    if request.method == "GET":
        categorias = CategoriaDespesa.objects.all().order_by('nome_categoria')
        caixas = Conta.objects.all()
        tipo_pagamento = ['Dinheiro', 'Pix', 'Cheque', 'Cartão Crédito', 'Debito Automatico', 'Boleto']       

        data = datetime.now().date()
        data_atual = data.strftime('%Y-%m-%d')

        return render(request, 'registro_despesa.html', {'categorias': categorias,
                                                         'caixas': caixas,
                                                         'tipo_pagamento': tipo_pagamento,
                                                         'data_atual': data_atual})

    elif request.method == "POST":
        data = request.POST.get('data')        
        valor = request.POST.get('valor')       
        categoria = request.POST.get('categoria')        
        subcategoria = request.POST.get('subcategoria')               
        caixa = request.POST.get('caixa')
        tipo_pagamento = request.POST.get('tipo_pagamento')
        obs = request.POST.get('observacao')

        if len(valor) == 0:
            messages.add_message(request, constants.ERROR, 'Valor não preenchido')
            return redirect('registro_despesa')

        if subcategoria == None:
            messages.add_message(request, constants.ERROR, 'Subcategoria não preenchida')
            return redirect('registro_despesa')
        
        try:
            valor = float(valor)
            caixa_selecionado = Conta.objects.filter(nome= caixa).first()            
            caixa_selecionado.saldo -= valor
            caixa_selecionado.save()
    
            despesa = Despesa(
                data = data,
                valor = valor,
                categoria = categoria,
                tipo_pagamento = tipo_pagamento,
                caixa = caixa_selecionado,
                subcategoria = subcategoria,
                obs = obs          
            )
            despesa.save()
            messages.add_message(request, constants.SUCCESS, 'Despesa Registrada Com Sucesso')
            return redirect('registro_despesa')
        except:
            messages.add_message(request, constants.ERROR, 'Erro interno do sistema')
            return render(request, 'registro_despesa.html')

@login_required(login_url='/')
def historico_caixas(request):    
    pagamentos = PagamentoVenda.objects.all().order_by('-data')
    caixas = Conta.objects.all()
    despesas = Despesa.objects.all()
    transferencias = Transferencia.objects.all()

    caixa = request.GET.get('caixa')           
    if caixa:
        caixa = Conta.objects.get(nome = caixa)
        caixas = caixas.filter(nome = caixa)
        pagamentos = pagamentos.filter(caixa = caixa)
        despesas = despesas.filter(caixa = caixa)
        transferencias = transferencias.filter(caixa = caixa)
    
    limpar = request.GET.get('limpar')
    if limpar:
        caixas = Conta.objects.all()
        despesas = Despesa.objects.all()
        transferencias = Transferencia.objects.all()

    for despesa in despesas:
        despesa.valor = -despesa.valor

    transacoes = sorted(
        list(pagamentos) + list(despesas) + list(transferencias),
        key=lambda x: x.data,
        reverse=True
    )

    data = datetime.now().date()
    data_atual = data.strftime('%Y-%m-%d')
    
    return render(request, 'historico_caixas.html', {'pagamentos': pagamentos, 
                                                     'caixas': caixas, 
                                                     'transacoes': transacoes,
                                                     'data_atual': data_atual})

@login_required(login_url='/')
def entrada_saida(request):
     if request.method == "POST":        
        data = request.POST.get('data_es')
        caixa = request.POST.get('caixa_es')
        tipo = request.POST.get('tipo_es')
        valor = request.POST.get('valor_es')
        es = request.POST.get('es')

        if len(valor) == 0:
            messages.add_message(request, constants.ERROR, 'Valor não preeechido!')
            return redirect('visao_geral')

        try:
            valor = float(valor)
            caixa_obj = Conta.objects.filter(nome = caixa).first()       

            if es == "Saida":
                caixa_obj.saldo -= valor
                valor = -valor                
            else:
                caixa_obj.saldo += valor            
            caixa_obj.save()

            entrada_saida = Transferencia(
                data = data,            
                valor = valor,
                categoria_transferencia = es,
                caixa = caixa_obj,
                tipo_transferencia = tipo
            )
            entrada_saida.save()

            messages.add_message(request, constants.SUCCESS, 'Entrada/Saida realizada com sucesso!')
            return redirect('historico_caixas')
        
        except:
            messages.add_message(request, constants.ERROR, 'Entrda/Saida não realizada!')
            return redirect('historico_caixas')

@login_required(login_url='/')
def transferencia(request):
    if request.method == "POST":        
        data = request.POST.get('data_transferencia')
        caixa_entrada = request.POST.get('caixa_entrada')
        caixa_saida = request.POST.get('caixa_saida')
        tipo = request.POST.get('tipo_transferencia')
        valor = request.POST.get('valor_transferencia')

        if len(valor) == 0:
            messages.add_message(request, constants.ERROR, 'Valor não preeechido!')
            return redirect('visao_geral')

        try:
            valor = float(valor)
            caixa_saida_obj = Conta.objects.filter(nome = caixa_saida).first()       
            caixa_saida_obj.saldo -= valor
            caixa_saida_obj.save()

            caixa_entrada_obj = Conta.objects.filter(nome = caixa_entrada).first()
            caixa_entrada_obj.saldo += valor
            caixa_entrada_obj.save()

            transferencia_entrada = Transferencia(
                data = data,            
                valor = valor,
                caixa = caixa_entrada_obj,
                tipo_transferencia = tipo
            )
            transferencia_entrada.save()

            transferencia_saida = Transferencia(
                data = data,            
                valor = -valor,
                caixa = caixa_saida_obj,
                tipo_transferencia = tipo
            )
            transferencia_saida.save()
            messages.add_message(request, constants.SUCCESS, 'Transferencia realizada com sucesso!')
            return redirect('visao_geral')
        
        except:
            messages.add_message(request, constants.ERROR, 'Transferencia não realizada!')
            return redirect('visao_geral')

@login_required(login_url='/')  
def contas_pagar(request):
    if request.method == "GET":
        contas_pagar = ContasPagar.objects.all().order_by('data_parcela')
        nome_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        lojas_pagar = [ conta.loja for conta in ContasPagar.objects.all() ]
        lojas_pagar = list(set(lojas_pagar))        
        
        mes_filtro = request.GET.get('mes')
        if mes_filtro:
            numero_mes = nome_meses.index(mes_filtro) + 1
            contas_pagar = ContasPagar.objects.filter(data_parcela__month=numero_mes).order_by('data_parcela')

        loja_filtro = request.GET.get('loja')
        if loja_filtro:
            contas_pagar = ContasPagar.objects.filter(loja = loja_filtro).order_by('data_parcela')
        
        limpar = request.GET.get('limpar')
        if limpar:
            contas_pagar = ContasPagar.objects.all().order_by('data_parcela')

        total_pagar = [conta.valor for conta in contas_pagar]
        total_pagar = sum(total_pagar)
        total_pagar = locale.currency(total_pagar, grouping=True, symbol=None)

        contas_pagar_mes = ContasPagar.objects.annotate(
            mes=ExtractMonth('data_parcela'),            
            ano=ExtractYear('data_parcela')
        ).values('ano', 'mes').annotate(valor=Sum('valor'))
        contas_pagar_mes = sorted(contas_pagar_mes, key=lambda x: x['mes'])
        
        for item in contas_pagar_mes:
            numero_mes = item['mes']
            nome_mes = nome_meses[numero_mes-1]          
            item['mes'] = nome_mes

        for item in contas_pagar_mes:
            valor = item['valor']
            item['valor'] = locale.currency(valor, grouping=True)
        
        return render(request, 'contas_pagar.html', {'contas_pagar': contas_pagar,
                                                     'nome_meses': nome_meses,                                                     
                                                     'total_pagar': total_pagar,
                                                     'contas_pagar_mes': contas_pagar_mes,
                                                     'lojas_pagar': lojas_pagar})
                                                     
    elif request.method == "POST":
            
        if request.content_type == 'application/json':            
            dados = json.loads(request.body)
            conta_pagar_id = dados.get('conta_pagar')
            try:
                conta_pagar = ContasPagar.objects.get(id = conta_pagar_id)                
                conta_pagar.delete()
                messages.add_message(request, constants.SUCCESS, 'Conta a pagar excluida com sucesso')
                return JsonResponse({'status': 'success'})
            except:
                messages.add_message(request, constants.ERROR, 'Conta a pagar não foi excluida')
                return redirect('contas_pagar')
                                  
        elif 'loja' in request.POST:
            data_atual = datetime.now()
            data_parcela = request.POST.get('data_parcela')        
            quantidade_parcelas = request.POST.get('quantidade_parcelas')
            dias_parcelas = request.POST.get('dias_parcela')
            loja = request.POST.get('loja')
            produto = request.POST.get('produto')
            valor = request.POST.get('valor')
            tipo_conta = request.POST.get('tipo_conta')

            if quantidade_parcelas == "":
                quantidade_parcelas = 1               
            else:
                quantidade_parcelas = int(quantidade_parcelas)

            if dias_parcelas == "":
                dias_parcelas = 0                         
            else:
                dias_parcelas = int(dias_parcelas)
            
            if not data_parcela or not valor or not loja or not produto:
                messages.add_message(request, constants.ERROR, 'Dados não preenchidos corretamente')
                return redirect('contas_pagar')

            try:
                valor = float(valor)
                data_parcela = datetime.strptime(data_parcela, "%Y-%m-%d")

                for i in range(quantidade_parcelas):            
                    conta_pagar = ContasPagar(
                    data_compra = data_atual,
                    data_parcela = data_parcela,
                    parcela = i + 1,
                    quantidade_parcelas = quantidade_parcelas,
                    loja = loja,
                    produto = produto,
                    valor = valor,
                    tipo_conta = tipo_conta
                    )
                    conta_pagar.save()
                    if dias_parcelas == 0:
                        data_parcela += relativedelta(months=1)                    
                    else:
                        data_parcela += timedelta(days=dias_parcelas)                    
                        
                messages.add_message(request, constants.SUCCESS, 'Conta a Pagar Registrado com Sucesso')
                return redirect('contas_pagar')            
            
            except:
                messages.add_message(request, constants.ERROR, 'Erro no Sistema')
                return redirect('contas_pagar')
        

    return render(request, 'contas_pagar.html')  

@login_required(login_url='/')
def cheque_boleto(request):
    if request.method == "GET":
        pagamentos_prazo = PagamentoPrazo.objects.all().order_by('data_prevista')
        caixas = Conta.objects.all()

        total_cheque = pagamentos_prazo.filter(tipo_pagamento = "Cheque")
        total_cheque = [ valor_cheque.valor for valor_cheque in total_cheque ]
        total_cheque = sum(total_cheque)
        total_cheque = locale.currency(total_cheque, grouping=True, symbol=None)
        
        total_boleto = pagamentos_prazo.filter(tipo_pagamento = "Boleto")
        total_boleto = [ valor_boleto.valor for valor_boleto in total_boleto ]
        total_boleto = sum(total_boleto)
        locale.currency(total_boleto, grouping=True, symbol=None)
    
        filtro = request.GET.get('cheque_boleto')
        if filtro:
            pagamentos_prazo = PagamentoPrazo.objects.filter(tipo_pagamento = filtro)

        data = datetime.now().date()
        data_atual = data.strftime('%Y-%m-%d')

        return render(request, 'cheque_boleto.html', {'pagamentos_prazo': pagamentos_prazo,
                                                    'total_cheque': total_cheque,
                                                    'total_boleto': total_boleto,
                                                    'data_atual': data,
                                                    'caixas': caixas})
    
    elif request.method == "POST":                       
        try:    
            dados = json.loads(request.body)
            venda = dados.get('venda')   
            request.session['venda'] = venda
            pagamento = dados.get('pagamento')   
            request.session['pagamento'] = pagamento             
        except json.JSONDecodeError:
            pass      
            
        if 'caixa' in request.POST:
            caixa = request.POST.get('caixa')       
            venda = request.session.get('venda')           
            pagamento = request.session.get('pagamento')
            # desconto = request.POST.get('desconto')
            juros = request.POST.get('juros')

            # desconto = float(desconto)
            juros = float(juros)

            pagamento_prazo = PagamentoPrazo.objects.filter(id=pagamento).first()
            caixa = Conta.objects.filter(nome=caixa).first()
            venda = Venda.objects.filter(id=venda).first()

            valor_pagamento = pagamento_prazo.valor + juros

            try:
                pagamento_venda = PagamentoVenda(
                    data = datetime.now(),
                    usuario = request.user,
                    valor_recebido_pagamento = valor_pagamento,
                    desconto = pagamento_prazo.desconto,
                    juros = juros,                    
                    caixa = caixa,
                    cliente = venda.cliente,
                    tipo_pagamento = pagamento_prazo.tipo_pagamento
                )
                pagamento_venda.save()
                venda.pagamento.add(pagamento_venda)
                
                venda.cliente.valor_receber -= pagamento_prazo.valor                                                 
                venda.save()

                caixa.saldo += valor_pagamento
                caixa.save()
                pagamento_prazo.delete()
                messages.add_message(request, constants.SUCCESS, 'Recebimento confirmado!')
                  
            
                if pagamento_prazo.tipo_pagamento == "Boleto":
                    venda.status_pago = "R"                                       
                    venda.valor_recebido = valor_pagamento
                    venda.valor_receber -= (valor_pagamento - juros)
                    venda.save()
                    venda.cliente.save()                    
                    pagamento_prazo.delete()                    
            except:
                pass

        elif 'observacao' in request.POST:
            observacao = request.POST.get('observacao') 
            pagamento = request.session.get('pagamento')
            pagamento_prazo = PagamentoPrazo.objects.filter(id=pagamento).first()

            pagamento_prazo.obs = observacao
            pagamento_prazo.save()

        return redirect('cheque_boleto')

@login_required(login_url='/')    
def historico_despesa(request):
    despesas = Despesa.objects.all().order_by('-data')
    caixas = Conta.objects.all()

    caixa = request.GET.get('caixa')
    if caixa:
        caixa = Conta.objects.get(nome = caixa)
        despesas = Despesa.objects.filter(caixa = caixa.id).order_by('-id')

    limpar = request.GET.get('limpar')
    if limpar:
        despesas = Despesa.objects.all().order_by('-id')        

    return render(request, 'historico_despesa.html', {'despesas': despesas,
                                                      'caixas': caixas})

@login_required(login_url='/')
def editar_despesa(request, despesa_id):
    despesa = Despesa.objects.get(id = despesa_id)
    if request.method == "GET":
        despesa = Despesa.objects.get(id = despesa_id)
        categorias = CategoriaDespesa.objects.all()
        caixas = Conta.objects.all()              

        dias_despesa = datetime.now().date() - despesa.data
        
        if dias_despesa.days >= 3:
            messages.add_message(request, constants.ERROR, 'Despesa nao pode ser editada depois de 3 dias!')     
            return redirect('historico_despesa')
        
        data = despesa.data
        data_despesa = data.strftime('%Y-%m-%d')      
        valor = despesa.valor
        valor = str(valor)

        tipo_pagamento = ['Dinheiro', 'Pix', 'Cheque', 'Cartão Crédito', 'Debito Automatico', 'Boleto']

        return render(request, 'editar_despesa.html', {'despesa': despesa,
                                                       'categorias': categorias,
                                                       'data_despesa': data_despesa,
                                                       'valor': valor,
                                                       'caixas': caixas,
                                                       'tipo_pagamento': tipo_pagamento})

    elif request.method == "POST":       
        data = request.POST.get('data')      
        valor = request.POST.get('valor')
        valor = float(valor)
        categoria = request.POST.get('categoria')        
        subcategoria = request.POST.get('subcategoria')               
        caixa = request.POST.get('caixa')
        tipo_pagamento = request.POST.get('tipo_pagamento')
        obs = request.POST.get('observacao')
        valor_anterior = despesa.valor
       
        try:
            caixa_selecionado = Conta.objects.filter(nome= caixa).first()                         
            caixa_selecionado.saldo += valor_anterior
            caixa_selecionado.saldo -= valor
            caixa_selecionado.save()
    
            despesa.data = data
            despesa.valor = valor
            despesa.categoria = categoria
            despesa.tipo_pagamento = tipo_pagamento
            despesa.caixa = caixa_selecionado
            despesa.subcategoria = subcategoria
            despesa.obs = obs          
            
            despesa.save()
            messages.add_message(request, constants.SUCCESS, 'Despesa Editada Com Sucesso')
            return redirect('historico_despesa')
        except:
            messages.add_message(request, constants.ERROR, 'Erro interno do sistema')
            return render(request, 'registro_despesa.html')

    
    
