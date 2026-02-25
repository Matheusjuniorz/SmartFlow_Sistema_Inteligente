from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.forms import UserCreationForm
from .models import Cliente, Chamado
from .forms import ClienteForm, ChamadoForm 
from django.contrib.auth.decorators import login_required

def lista_clientes(request):
    termo_busca = request.GET.get('q', '')
    if termo_busca:
        clientes = Cliente.objects.filter(nome__icontains=termo_busca)
    else:
        clientes = Cliente.objects.all()
    return render(request, 'clientes/lista.html', {'clientes': clientes, 'termo_busca': termo_busca})
    
def criar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes') 
    else:
        form = ClienteForm()
    return render(request, 'clientes/form.html', {'form': form})

def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    form = ClienteForm(request.POST or None, instance=cliente)
    if form.is_valid():
        form.save()
        return redirect('lista_clientes')
    return render(request, 'clientes/form.html', {'form': form})

def excluir_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    cliente.delete()
    return redirect('lista_clientes')

@login_required 
def criar_chamado(request):
    if request.method == 'POST':
        form = ChamadoForm(request.POST)
        if form.is_valid():
            chamado = form.save(commit=False)
            o
            chamado.responsavel = request.user
            chamado.save()
            return redirect('lista_chamados')
    else:
        form = ChamadoForm()
    return render(request, 'chamadas/form_chamado.html', {'form': form})


@login_required 
def lista_chamados(request):
    chamados = Chamado.objects.all()
    return render(request, 'chamadas/lista_chamados.html', {'chamados': chamados})



def registrar_responsavel(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('two_factor:login')
    else:
        form = UserCreationForm()
    return render(request, 'chamadas/registrar.html', {'form': form})