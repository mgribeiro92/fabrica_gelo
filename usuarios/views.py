from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.messages import constants
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.conf import settings

def cadastro(request):
    if request.method == "GET":
        return render(request, 'cadastro.html')
    elif request.method == "POST":
        primeiro_nome = request.POST.get('primeiro_nome')
        ultimo_nome = request.POST.get('ultimo_nome')
        username = request.POST.get('username')
        senha = request.POST.get('senha')
        confirmar_senha = request.POST.get('confirmar_senha')
        email = request.POST.get('email')
            
    if not senha == confirmar_senha:
        messages.add_message(request, constants.ERROR, "As senhas não são iguais" )
        return redirect ('/cadastro')

    try:
        user = User.objects.create_user(
            first_name = primeiro_nome,
            last_name = ultimo_nome,
            username = username,
            password = senha,
            email = email,
        )
        user.save()
        messages.add_message(request, constants.SUCCESS, "Usuario cadastrado com sucesso" )
        return redirect ('/')
    except:
        messages.add_message(request, constants.ERROR, "Usuario não cadastrado" )
        return redirect ('/cadastro')
    
def logar(request):
    if request.method == "GET":
        return render(request, 'login.html')
    elif request.method == "POST":
        username = request.POST.get('username')
        senha = request.POST.get('senha')
        continuar_conectado = request.POST.get('continuar_conectado')
        print(continuar_conectado)
        
        user = authenticate(username = username, password = senha) 
       
        if user:
            login(request, user)

            if not continuar_conectado:
                request.session.set_expiry(0)  # Sessão de navegador
            else:
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)

            return redirect('/vendas')
        else:
            messages.add_message(request, constants.ERROR, "Usuario ou senha não é valido" )
            return redirect('/')

def sair(request):
    logout(request)
    return redirect('/')



