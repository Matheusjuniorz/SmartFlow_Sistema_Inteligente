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
# Adicionado ParagraphStyle aqui para evitar o NameError
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

from .models import Cliente, Chamado
from .forms import ClienteForm, ChamadoForm




@login_required
@login_required
def gerar_os_pdf(request, chamado_id):
    chamado = get_object_or_404(Chamado, id=chamado_id)
    
    response = HttpResponse(content_type='application/pdf')
    nome_arquivo = f"OS_{chamado.id}_{chamado.cliente.nome[:15].replace(' ', '_')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'

    # Configuração básica do documento
    doc = SimpleDocTemplate(response, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()

    # --- 1. DEFINIÇÃO DE ESTILOS (Para corrigir o espaçamento/encavalamento) ---
    style_titulo = ParagraphStyle('TituloOS', parent=styles['Normal'], fontSize=16, leading=20, fontName='Helvetica-Bold')
    style_subtitulo = ParagraphStyle('SubtituloOS', parent=styles['Normal'], fontSize=12, leading=15)
    style_id = ParagraphStyle('IdOS', parent=styles['Normal'], fontSize=10, leading=12, fontName='Helvetica-Bold')

    # --- 2. CABEÇALHO ---
    logo_path = find('img/logo.png')
    
    titulo_empresa = Paragraph("SmartFlow - Sistema de Gestão", style_titulo)
    subtitulo_doc = Paragraph("Relatório Técnico de Chamados", style_subtitulo)
    info_os = Paragraph(f"Ordem de Serviço #{chamado.id}", style_id)

    # Criamos uma lista de elementos para a célula de texto
    coluna_texto = [titulo_empresa, Spacer(1, 3), subtitulo_doc, Spacer(1, 3), info_os]

    if logo_path and os.path.exists(logo_path):
        img = Image(logo_path, width=70, height=35)
        header_tab = Table([[img, coluna_texto]], colWidths=[90, 390])
    else:
        header_tab = Table([[coluna_texto]], colWidths=[480])

    header_tab.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(header_tab)
    
    # Linha divisória
    elements.append(Spacer(1, 5))
    line = Table([['']], colWidths=[480], rowHeights=[1])
    line.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(line)
    elements.append(Spacer(1, 20))

    # --- 3. DADOS DO CLIENTE E CHAMADO ---
    telefone = getattr(chamado.cliente, 'telefone', 'Não informado')
    dados_info = [
        [Paragraph("<b>DADOS DO CLIENTE</b>", styles['Normal']), Paragraph("<b>INFORMAÇÕES TÉCNICAS</b>", styles['Normal'])],
        [f"Nome: {chamado.cliente.nome}", f"Responsável: {chamado.responsavel.get_full_name() or chamado.responsavel.username}"],
        [f"Contato: {telefone}", f"Data de Abertura: {chamado.data_criacao.strftime('%d/%m/%Y %H:%M')}"],
        ["", f"Status Atual: {chamado.get_status_display().upper()}"]
    ]
    
    info_tab = Table(dados_info, colWidths=[240, 240])
    info_tab.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, colors.grey),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('FONTSIZE', (0,1), (-1,-1), 10),
    ]))
    elements.append(info_tab)
    elements.append(Spacer(1, 20))

    # --- 4. DESCRIÇÃO E SOLUÇÃO ---
    elements.append(Paragraph("<b>DESCRIÇÃO DO PROBLEMA / SOLICITAÇÃO</b>", styles['Normal']))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(chamado.descricao, styles['Normal']))
    elements.append(Spacer(1, 15))

    solucao_texto = getattr(chamado, 'solucao', None)
    if solucao_texto:
        elements.append(Paragraph("<b>SOLUÇÃO APLICADA / OBSERVAÇÕES</b>", styles['Normal']))
        elements.append(Spacer(1, 5))
        sol_tab = Table([[Paragraph(solucao_texto, styles['Normal'])]], colWidths=[480])
        sol_tab.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
            ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
            ('PADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(sol_tab)
        elements.append(Spacer(1, 20))

    # --- 5. FINANCEIRO ---
    valor = getattr(chamado, 'valor', 0.00)
    try:
        meio_pag = chamado.get_meio_pagamento_display()
    except:
        meio_pag = getattr(chamado, 'meio_pagamento', 'A definir')

    pagamento_dados = [
        [Paragraph("<b>RESUMO FINANCEIRO</b>", styles['Normal']), ""],
        ["Valor Total do Serviço:", f"R$ {valor:.2f}"],
        ["Forma de Pagamento:", str(meio_pag)]
    ]
    
    pag_tab = Table(pagamento_dados, colWidths=[150, 330])
    pag_tab.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,1), (-1,-1), 0.5, colors.lightgrey),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(pag_tab)

    # --- 6. ASSINATURAS E RODAPÉ ---
    elements.append(Spacer(1, 60))
    tab_ass = Table([
        ["___________________________", "___________________________"],
        ["Assinatura do Responsável", "Assinatura do Cliente"]
    ], colWidths=[240, 240])
    tab_ass.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTSIZE', (0,1), (-1,-1), 9)]))
    elements.append(tab_ass)

    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"<center><font size='8'>Gerado por SmartFlow em {datetime.now().strftime('%d/%m/%Y %H:%M')}</font></center>", styles['Normal']))

    doc.build(elements)
    return response

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