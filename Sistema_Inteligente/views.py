import os
import calendar
from datetime import datetime
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse
from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.contrib.auth.forms import UserCreationForm

# PDF e Modelos
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from .models import Cliente, Chamado
from .forms import ClienteForm, ChamadoForm

# --- 1. DASHBOARD ---
@login_required
def dashboard(request):
    filtro_prioridade = request.GET.get('prioridade')
    context = {
        'total': Chamado.objects.count(),
        'alta': Chamado.objects.filter(prioridade='alta').count(),
        'media': Chamado.objects.filter(prioridade='media').count(),
        'baixa': Chamado.objects.filter(prioridade='baixa').count(),
        'filtro_ativo': filtro_prioridade,
    }
    
    chamados_query = Chamado.objects.all().order_by('-data_criacao')
    if filtro_prioridade and filtro_prioridade != 'None':
        chamados_query = chamados_query.filter(prioridade=filtro_prioridade)

    context['chamados'] = chamados_query[:15]
    context['lista_atividades'] = chamados_query[:15]
    
    return render(request, 'chamadas/dashboard.html', context)

# --- 2. CLIENTES ---
@login_required
def lista_clientes(request):
    termo_busca = request.GET.get('q', '')
    clientes = Cliente.objects.filter(nome__icontains=termo_busca) if termo_busca else Cliente.objects.all()
    return render(request, 'clientes/lista.html', {'clientes': clientes, 'termo_busca': termo_busca})

@login_required
def criar_cliente(request):
    form = ClienteForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('lista_clientes')
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
    get_object_or_404(Cliente, id=id).delete()
    return redirect('lista_clientes')

# --- 3. CHAMADOS ---
@login_required 
def lista_chamados(request):
    chamados = Chamado.objects.all().order_by('-data_criacao')
    dia, mes, ano = request.GET.get('dia'), request.GET.get('mes'), request.GET.get('ano')

    if dia and mes and ano:
        chamados = chamados.filter(data_criacao__day=dia, data_criacao__month=mes, data_criacao__year=ano)
    elif mes and ano:
        chamados = chamados.filter(data_criacao__month=mes, data_criacao__year=ano)
    elif ano:
        chamados = chamados.filter(data_criacao__year=ano)

    return render(request, 'chamadas/lista_chamados.html', {
        'chamados': chamados,
        'filtros': {'dia': dia, 'mes': mes, 'ano': ano}
    })

@login_required
def criar_chamado(request):
    if request.method == 'POST':
        form = ChamadoForm(request.POST)
        if form.is_valid():
            chamado = form.save(commit=False)
            chamado.responsavel = request.user
            chamado.save()
            return redirect('dashboard')
    else:
        form = ChamadoForm()
    
    return render(request, 'chamadas/criar_chamado.html', {
        'form': form,
        'clientes': Cliente.objects.all()
    })

@login_required
def detalhe_chamado(request, chamado_id):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    return render(request, 'chamadas/detalhe_chamado.html', {'chamado': chamado})

@login_required
def finalizar_chamado(request, chamado_id):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    if request.method == 'POST':
        chamado.solucao = request.POST.get('solucao')
        chamado.status = 'finalizado'
        chamado.data_finalizacao = timezone.now()
        chamado.save()
        return redirect('dashboard')
    return render(request, 'chamadas/encerrar_chamado.html', {'chamado': chamado})

@login_required
def mudar_status(request, chamado_id, novo_status):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    chamado.status = novo_status
    chamado.save()
    return redirect('dashboard')

@login_required
def excluir_chamado(request, chamado_id):
    get_object_or_404(Chamado, id=chamado_id).delete()
    return redirect('lista_chamados')

# --- 4. RELATÓRIOS E PDF ---
@login_required
def relatorio_chamados(request):
    relatorio_mensal = Chamado.objects.annotate(mes=TruncMonth('data_criacao')).values('mes').annotate(total=Count('id')).order_by('-mes')
    estatisticas_clientes = Chamado.objects.values('cliente__nome').annotate(total=Count('id')).order_by('-total')[:5]
    return render(request, 'chamadas/relatorio.html', {
        'relatorio_mensal': relatorio_mensal,
        'estatisticas_clientes': estatisticas_clientes
    })

@login_required
def gerar_os_pdf(request, chamado_id):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="OS_{chamado.id}.pdf"'

    # Configuração de margens e página
    doc = SimpleDocTemplate(response, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Cores personalizadas
    cor_primaria = colors.HexColor('#2C3E50')
    cor_fundo = colors.HexColor('#F4F7F6')

    # --- CABEÇALHO COM LOGO ---
    logo_path = find('img/logo.png')
    if not logo_path:
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')

    dados_header = []
    col_widths = [480] # Largura total se não houver logo

    if os.path.exists(logo_path):
        img = Image(logo_path, width=80, height=45)
        col_widths = [100, 380]
        texto_header = [
            Paragraph(f"<b>SMARTFLOW - SISTEMA DE GESTÃO</b>", styles['Title']),
            Paragraph(f"Ordem de Serviço Individual #{chamado.id}", styles['Normal'])
        ]
        dados_header = [[img, texto_header]]
    else:
        dados_header = [[Paragraph(f"<b>SMARTFLOW - ORDEM DE SERVIÇO #{chamado.id}</b>", styles['Title'])]]

    header_tab = Table(dados_header, colWidths=col_widths)
    header_tab.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(header_tab)

    # Linha divisória elegante
    line = Table([['']], colWidths=[530], rowHeights=[2])
    line.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 2, cor_primaria)]))
    elements.append(line)
    elements.append(Spacer(1, 20))

    # --- QUADRO DE INFORMAÇÕES ---
    def estilo_celula(titulo, valor):
        return [Paragraph(f"<b>{titulo}</b>", styles['Normal']), Paragraph(str(valor), styles['Normal'])]

    dados_info = [
        [estilo_celula("CLIENTE:", chamado.cliente.nome), estilo_celula("DATA ABERTURA:", chamado.data_criacao.strftime('%d/%m/%Y %H:%M'))],
        [estilo_celula("TÉCNICO:", chamado.responsavel.username), estilo_celula("STATUS:", chamado.get_status_display().upper())],
        [estilo_celula("PRIORIDADE:", chamado.prioridade.upper()), estilo_celula("FORMA PAG.:", getattr(chamado, 'meio_pagamento', 'A definir'))]
    ]

    info_tab = Table(dados_info, colWidths=[265, 265])
    info_tab.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,-1), cor_fundo),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(info_tab)
    elements.append(Spacer(1, 25))

    # --- DESCRIÇÃO E SOLUÇÃO ---
    elements.append(Paragraph("<b>DETALHAMENTO DOS SERVIÇOS</b>", styles['Heading3']))
    
    # Caixa de Descrição
    desc_tab = Table([[Paragraph(f"<b>Problema Relatado:</b><br/>{chamado.descricao}", styles['Normal'])]], colWidths=[530])
    desc_tab.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(desc_tab)
    elements.append(Spacer(1, 15))

    if chamado.solucao:
        sol_tab = Table([[Paragraph(f"<b>Solução Técnica:</b><br/>{chamado.solucao}", styles['Normal'])]], colWidths=[530])
        sol_tab.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, cor_primaria),
            ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
            ('PADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(sol_tab)

    # --- RODAPÉ DE ASSINATURAS ---
    elements.append(Spacer(1, 80))
    ass_data = [
        ["_________________________________", "_________________________________"],
        ["Assinatura do Técnico", "Assinatura do Cliente"]
    ]
    ass_tab = Table(ass_data, colWidths=[265, 265])
    ass_tab.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTSIZE', (0,1), (-1,-1), 8)]))
    elements.append(ass_tab)

    doc.build(elements)
    return response

@login_required
def gerar_pdf_chamados(request):
    """Gera um relatório PDF profissional com a listagem de todos os chamados."""
    chamados = Chamado.objects.all().order_by('-data_criacao')
    
    # Captura filtros de data da URL para o relatório ser dinâmico
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    if mes: chamados = chamados.filter(data_criacao__month=mes)
    if ano: chamados = chamados.filter(data_criacao__year=ano)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Relatorio_SmartFlow_{datetime.now().strftime("%d%m%Y")}.pdf"'

    # Configuração do Documento
    doc = SimpleDocTemplate(response, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    cor_primaria = colors.HexColor('#2C3E50')

    # --- CABEÇALHO ---
    logo_path = find('img/logo.png')
    if not logo_path:
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo.png')

    if os.path.exists(logo_path):
        img = Image(logo_path, width=70, height=40)
        header_data = [[img, Paragraph("<b>SMARTFLOW - RELATÓRIO GERAL</b>", styles['Title'])]]
        header_tab = Table(header_data, colWidths=[80, 420])
    else:
        header_tab = Table([[Paragraph("<b>SMARTFLOW - RELATÓRIO GERAL</b>", styles['Title'])]], colWidths=[500])
    
    header_tab.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elements.append(header_tab)
    
    # Linha Divisória
    line = Table([['']], colWidths=[530], rowHeights=[2])
    line.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 2, cor_primaria)]))
    elements.append(line)
    elements.append(Spacer(1, 10))

    # Informações do Filtro
    texto_filtro = f"Período: {mes if mes else 'Todos'}/{ano if ano else 'Todos os anos'}"
    elements.append(Paragraph(f"<i>{texto_filtro}</i>", styles['Normal']))
    elements.append(Paragraph(f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # --- TABELA DE DADOS ---
    # Cabeçalho da Tabela
    dados = [['ID', 'Cliente', 'Data', 'Prioridade', 'Status']]
    
    for c in chamados:
        dados.append([
            f"#{c.id}",
            c.cliente.nome[:25], # Limita o nome para não quebrar a tabela
            c.data_criacao.strftime('%d/%m/%Y'),
            c.prioridade.upper(),
            c.status.upper()
        ])

    # Estilização da Tabela
    tabela = Table(dados, colWidths=[40, 180, 80, 100, 100])
    tabela.setStyle(TableStyle([
        # Estilo do Cabeçalho da Tabela
        ('BACKGROUND', (0, 0), (-1, 0), cor_primaria),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        
        # Estilo das Linhas (Efeito Zebrado)
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(tabela)

    # --- RESUMO FINAL ---
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"<b>Total de Chamados no Relatório:</b> {chamados.count()}", styles['Normal']))
    
    doc.build(elements)
    return response

# --- 5. USUÁRIOS ---
def registrar_responsavel(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('login')
    return render(request, 'chamadas/registrar.html', {'form': form})