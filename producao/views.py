from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from vendas.models import Produto, Venda, Cliente, Pedido, Conta, PagamentoVenda, Embalagem
from financeiro.models import CategoriaDespesa, Despesa
from .models import ProdutoProducao, Producao
from datetime import datetime
from django.contrib.messages import constants
from django.contrib import messages
import locale
import plotly.express as px

@login_required(login_url='/')
def historico_producao(request):
    producoes = Producao.objects.all().order_by('-data')    
    
    return render(request, 'historico_producao.html', {'producoes': producoes})

@login_required(login_url='/')
def producao(request):
    producoes = Producao.objects.all().order_by('-data')  
    produtos = Produto.objects.all()
    embalagens = Embalagem.objects.all()

    return render(request, 'producao.html', {'producoes': producoes, 
                                             'produtos': produtos,
                                             'embalagens': embalagens})

@login_required(login_url='/')
def cadastrar_producao(request):
    if request.method == "GET":
        producoes = Producao.objects.all().order_by('-data')
        produtos = Produto.objects.all()       

        return render(request, 'cadastrar_producao.html', {'producoes': producoes, 'produtos': produtos})
    
    elif request.method == "POST":    
        
        locale.setlocale(locale.LC_TIME, 'pt_BR.utf-8')        
        data = request.POST.get('data')
        
        if data == "":     
            messages.add_message(request, constants.ERROR, 'Data não preenchida!')     
            return redirect('cadastrar_producao')
        else:
            data = datetime.strptime(data, '%Y-%m-%d')
            dia_semana = data.strftime("%A").capitalize()
             
        funcionario1 = request.POST.get('funcionario1')
        funcionario2 = request.POST.get('funcionario2')
        funcionario3 = request.POST.get('funcionario3')

        # Dados dos produtos do formulario 1
        produtos_id1 = request.POST.getlist('produtos1')
        produto_selecionados1 = Produto.objects.filter(id__in = produtos_id1)
        quantidade1 = request.POST.getlist('quantidade1')
        quantidade_preenchidas1 = [indice for indice, item in enumerate(quantidade1) if item != ""]       
        indice_produtos1 = [int(item) - 1 for item in produtos_id1]

        quantidade1 = [item for item in quantidade1 if item != ""]
        quantidade1 = [int(i) for i in quantidade1]

        produtos_kg1 = []
        for produto in produto_selecionados1:
            produtos_kg1.append(produto.kg)

        producao_kg1 = [a * b for a, b in zip(produtos_kg1, quantidade1)]
        total_producao1 = sum(producao_kg1)

        if indice_produtos1 != quantidade_preenchidas1:
            messages.add_message(request, constants.ERROR, 'A quantidade preenchida não corresponde ao produto selecionado!')     
            return redirect('cadastrar_producao')

        if not produto_selecionados1:
            messages.add_message(request, constants.ERROR, 'Produto nao foi preenchido!')     
            return redirect('cadastrar_producao')    

        # Dados do formulario 2, se existir
        produtos_id2 = request.POST.getlist('produtos2')
        produto_selecionados2 = Produto.objects.filter(id__in = produtos_id2)
  
        if produto_selecionados2:
            quantidade2 = request.POST.getlist('quantidade2')
            quantidade_preenchidas2 = [indice for indice, item in enumerate(quantidade2) if item != ""]       
            indice_produtos2 = [int(item) - 1 for item in produtos_id2]

            quantidade2 = [item for item in quantidade2 if item != ""]
            quantidade2 = [int(i) for i in quantidade2]

            produtos_kg2 = []
            for produto in produto_selecionados2:
                produtos_kg2.append(produto.kg)

            producao_kg2 = [a * b for a, b in zip(produtos_kg2, quantidade2)]
            total_producao2 = sum(producao_kg2)

            if indice_produtos2 != quantidade_preenchidas2:
                messages.add_message(request, constants.ERROR, 'A quantidade preenchida não corresponde ao produto selecionado!')     
                return redirect('cadastrar_producao')

        #Dados do formulario 3, se existir
        produtos_id3 = request.POST.getlist('produtos3')
        produto_selecionados3 = Produto.objects.filter(id__in = produtos_id3)

        if produto_selecionados3:
            quantidade3 = request.POST.getlist('quantidade3')
            quantidade_preenchidas3 = [indice for indice, item in enumerate(quantidade3) if item != ""]       
            indice_produtos3 = [int(item) - 1 for item in produtos_id3]

            quantidade3 = [item for item in quantidade3 if item != ""]
            quantidade3 = [int(i) for i in quantidade3]

            produtos_kg3 = []
            for produto in produto_selecionados3:
                produtos_kg3.append(produto.kg)

            producao_kg3 = [a * b for a, b in zip(produtos_kg3, quantidade3)]
            total_producao3 = sum(producao_kg3)

            if indice_produtos3 != quantidade_preenchidas3:
                messages.add_message(request, constants.ERROR, 'A quantidade preenchida não corresponde ao produto selecionado!')     
                return redirect('cadastrar_producao')

        try:
            producao = Producao(
                data = data,
                dia_semana = dia_semana,                     
            )
            producao.save()

            index = 0
            for produto in produto_selecionados1:            
                produtos_producao = ProdutoProducao(
                    produto = produto,
                    quantidade = quantidade1[index],
                    quantidade_kg = producao_kg1[index],
                    funcionario = funcionario1,
                )
                produtos_producao.save()
                producao.produto.add(produtos_producao)
                
                produto.estoque += quantidade1[index]                
                produto.embalagem.estoque -= quantidade1[index]                
                produto.embalagem.save()
                produto.save()
                index += 1

                producao.total_kg += total_producao1
                producao.save()

            if produto_selecionados2:
                index = 0
                for produto in produto_selecionados2:            
                    produtos_producao = ProdutoProducao(
                        produto = produto,
                        quantidade = quantidade2[index],
                        quantidade_kg = producao_kg2[index],
                        funcionario = funcionario2,
                    )
                    produtos_producao.save()
                    producao.produto.add(produtos_producao)
                    
                    produto.estoque += quantidade2[index]
                    produto.embalagem.estoque -= quantidade2[index]
                    produto.embalagem.save()
                    produto.save()
                    index += 1

                    producao.total_kg += total_producao2
                    producao.save()

            if produto_selecionados3:
                index = 0
                for produto in produto_selecionados3:            
                    produtos_producao = ProdutoProducao(
                        produto = produto,
                        quantidade = quantidade3[index],
                        quantidade_kg = producao_kg3[index],
                        funcionario = funcionario3,
                    )
                    produtos_producao.save()
                    producao.produto.add(produtos_producao)
                    
                    produto.estoque += quantidade3[index]
                    produto.embalagem.estoque -= quantidade3[index]
                    produto.embalagem.save()
                    produto.save()
                    index += 1

                    producao.total_kg += total_producao3
                    producao.save()                    
            
            messages.add_message(request, constants.SUCCESS, 'Produção registrada com sucesso')
            return redirect('historico_producao')
            
        except:
            messages.add_message(request, constants.ERROR, 'Produção não registrada!')
            return render(request, 'cadastrar_producao.html')

@login_required(login_url='/')       
def historico_produtos(request):
    vendas = Venda.objects.all()
    producoes = Producao.objects.all()
    produtos = Produto.objects.all()

    transacoes = sorted(
        list(vendas) + list(producoes),
        key=lambda x: x.data,
        reverse=True
    )

    return render(request, 'historico_produtos.html', {'transacoes': transacoes,
                                                       'produtos': produtos})