import os
import calendar
from datetime import datetime
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.conf import settings
from django.contrib.staticfiles.finders import find

# ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

from .models import Cliente, Chamado
from .forms import ClienteForm, ChamadoForm 

# --- GERAÇÃO DE PDF ---

@login_required
def gerar_pdf_chamados(request):
    dia = request.GET.get('dia')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    
    chamados = Chamado.objects.all().order_by('-data_criacao')

    # Filtros de data
    if dia and mes and ano:
        data_inicio = datetime(int(ano), int(mes), int(dia), 0, 0, 0)
        data_fim = datetime(int(ano), int(mes), int(dia), 23, 59, 59)
        chamados = chamados.filter(data_criacao__range=(data_inicio, data_fim))
    elif mes and ano:
        ultimo_dia = calendar.monthrange(int(ano), int(mes))[1]
        data_inicio = datetime(int(ano), int(mes), 1, 0, 0, 0)
        data_fim = datetime(int(ano), int(mes), ultimo_dia, 23, 59, 59)
        chamados = chamados.filter(data_criacao__range=(data_inicio, data_fim))
    elif ano:
        chamados = chamados.filter(data_criacao__year=ano)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Relatorio_SmartFlow_{datetime.now().strftime("%d%m%Y")}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # --- LOGO (Busca Segura) ---
    logo_path = find('img/logo.png')
    if not logo_path: # Tenta caminho manual se o find falhar
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')

    if os.path.exists(logo_path):
        img = Image(logo_path, width=80, height=40)
        img.hAlign = 'RIGHT' 
        elements.append(img)
    
    elements.append(Paragraph("SmartFlow - Sistema de Gestão", styles['Title']))
    elements.append(Paragraph("Relatório Técnico de Chamados", styles['Heading2']))
    elements.append(Paragraph(f"Filtro aplicado: {dia if dia else '--'}/{mes if mes else '--'}/{ano if ano else '--'}", styles['Normal']))
    elements.append(Paragraph(f"Data de emissão: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Tabela
    dados = [['ID', 'Cliente', 'Data/Hora', 'Assunto', 'Status']]
    for c in chamados:
        dados.append([
            f"#{c.id}",
            c.cliente.nome[:20],
            c.data_criacao.strftime('%d/%m/%Y %H:%M'),
            c.descricao[:35] + '...' if len(c.descricao) > 35 else c.descricao,
            c.status.upper()
        ])

    tabela = Table(dados, colWidths=[40, 110, 100, 200, 80])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f2f2f2')])
    ]))
    elements.append(tabela)
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"Total de registros encontrados: {chamados.count()}", styles['Italic']))

    doc.build(elements)
    return response

def lista_clientes(request):
    termo_busca = request.GET.get('q', '')
    if termo_busca:
        clientes = Cliente.objects.filter(nome__icontains=termo_busca)
    else:
        clientes = Cliente.objects.all()
    return render(request, 'clientes/lista.html', {'clientes': clientes, 'termo_busca': termo_busca})

@login_required
def criar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes') 
    else:
        form = ClienteForm()
    return render(request, 'clientes/form.html', {'form': form})


@login_required 
def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    form = ClienteForm(request.POST or None, instance=cliente)
    if form.is_valid():
        form.save()
        return redirect('lista_clientes')
    return render(request, 'clientes/form.html', {'form': form})

@login_required 
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
            chamado.responsavel = request.user 
            chamado.save()
            return redirect('lista_chamados')
    else:
        form = ChamadoForm()
    return render(request, 'chamadas/form_chamado.html', {'form': form})


@login_required 
def lista_chamados(request):
    chamados = Chamado.objects.all().order_by('-data_criacao')

    dia = request.GET.get('dia')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')

    if dia and mes and ano:
        data_inicio = datetime(int(ano), int(mes), int(dia), 0, 0, 0)
        data_fim = datetime(int(ano), int(mes), int(dia), 23, 59, 59)
        
        chamados = chamados.filter(data_criacao__range=(data_inicio, data_fim))
        
    elif mes and ano:
        ultimo_dia = calendar.monthrange(int(ano), int(mes))[1]
        data_inicio = datetime(int(ano), int(mes), 1, 0, 0, 0)
        data_fim = datetime(int(ano), int(mes), ultimo_dia, 23, 59, 59)
        chamados = chamados.filter(data_criacao__range=(data_inicio, data_fim))
    
    elif ano:
        chamados = chamados.filter(data_criacao__year=ano)

    return render(request, 'chamadas/lista_chamados.html', {
        'chamados': chamados,
        'filtros': {'dia': dia, 'mes': mes, 'ano': ano}
    })

def registrar_responsavel(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('two_factor:login')
    else:
        form = UserCreationForm()
    return render(request, 'chamadas/registrar.html', {'form': form})

@login_required
def dashboard(request):
    filtro_prioridade = request.GET.get('prioridade')

    total = Chamado.objects.count()
    alta = Chamado.objects.filter(prioridade='alta').count()
    media = Chamado.objects.filter(prioridade='media').count()
    baixa = Chamado.objects.filter(prioridade='baixa').count()

    if filtro_prioridade:
        lista_atividades = Chamado.objects.filter(prioridade=filtro_prioridade).order_by('-data_criacao')
    else:
        lista_atividades = Chamado.objects.all().order_by('-data_criacao')[:10]

    context = {
        'total': total,
        'alta': alta,
        'media': media,
        'baixa': baixa,
        'chamados': lista_atividades,
        'filtro_ativo': filtro_prioridade, 
    }
    return render(request, 'chamadas/dashboard.html', context)


@login_required
def mudar_status(request, chamado_id, novo_status):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    
    chamado.status = novo_status
    chamado.save()
    
    return redirect('dashboard')

@login_required
def excluir_chamado(request, chamado_id):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    chamado.delete()
    return redirect('lista_chamados')

def detalhe_chamado(request, chamado_id):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    return render(request, 'chamadas/detalhe_chamado.html', {'chamado': chamado})


def criar_chamado(request):
    if request.method == 'POST':
        # ... sua lógica de salvar ...
        return redirect('dashboard')
    
    clientes = Cliente.objects.all()
    return render(request, 'chamadas/criar_chamado.html', {'clientes': clientes})
        

    Chamado.objects.create(
            cliente=cliente, 
            descricao=descricao,
            responsavel=request.user 
        )
        
    return redirect('lista_chamados')

    clientes = Cliente.objects.all()
    return render(request, 'criar_chamado.html', {'clientes': clientes})


def detalhe_chamado(request, chamado_id):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    return render(request, 'chamadas/detalhe_chamado.html', {'chamado': chamado})


def finalizar_chamado(request, chamado_id):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    
    if request.method == 'POST':
        solucao_tecnica = request.POST.get('solucao')
        
        chamado.solucao = solucao_tecnica
        chamado.status = 'finalizado'
        chamado.data_finalizacao = timezone.now()
        chamado.save()
        
        return redirect('dashboard')
        
    return render(request, 'chamadas/encerrar_chamado.html', {'chamado': chamado})


def relatorio_chamados(request):
    relatorio_mensal = (
        Chamado.objects.annotate(mes=TruncMonth('data_criacao'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('-mes')
    )
    
    estatisticas_clientes = (
        Chamado.objects.values('cliente__nome')
        .annotate(total=Count('id'))
        .order_by('-total')[:5] 
    )

    return render(request, 'chamadas/relatorio.html', {
        'relatorio_mensal': relatorio_mensal,
        'estatisticas_clientes': estatisticas_clientes
    })