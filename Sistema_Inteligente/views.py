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
from django.contrib.auth.decorators import login_required

# PDF e Modelos
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from .models import Cliente, Chamado
from .forms import ClienteForm, ChamadoForm


import mercadopago
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.db.models import Sum
from django.db.models import Q 
from django.contrib.auth.models import User





@login_required
def chamados_registrados(request):
    busca = request.GET.get('q')
    
    chamados_list = Chamado.objects.all().order_by('-data_criacao')

    if busca:
        chamados_list = chamados_list.filter(
            Q(cliente__nome__icontains=busca) | 
            Q(descricao__icontains=busca)
        )

    return render(request, 'chamadas/chamados_registrados.html', {
        'chamados': chamados_list,
        'busca': busca
    })


def pagamento_sucesso(request):
    return render(request, 'chamadas/pagamento_sucesso.html')



@csrf_exempt
def mercadopago_webhook(request):
    import json
    
    # 1. Tentar capturar o ID e o Tópico de várias formas (GET, POST ou Body JSON)
    topic = request.GET.get('topic') or request.GET.get('type')
    resource_id = request.GET.get('id')
    
    if not resource_id and request.body:
        try:
            data = json.loads(request.body)
            topic = data.get('type') or topic
            resource_id = data.get('data', {}).get('id')
        except:
            pass

    # 2. Processar apenas se for um pagamento aprovado
    if topic in ['payment', 'payment.updated'] and resource_id:
        sdk = mercadopago.SDK("APP_USR-805107443493899-022520-5a39746b4773f8a8776ec2c51d1160fd-215251480")
        payment_info = sdk.payment().get(resource_id)
        
        if payment_info["status"] in [200, 201]:
            payment_data = payment_info["response"]
            chamado_id = payment_data.get('external_reference')
            status_pagamento = payment_data.get('status')

            # 3. Se o pagamento foi aprovado, atualizamos o banco
            if chamado_id and status_pagamento == 'approved':
                chamado = Chamado.objects.filter(id=chamado_id).first()
                
                # Só executa se o chamado existir e ainda não estiver como 'pago'
                if chamado and chamado.status != 'pago':
                    chamado.status = 'pago'
                    chamado.save()
                    
                    # 4. Enviar e-mail de confirmação bonitão
                    try:
                        assunto = f"✅ Pagamento Confirmado - OS #{chamado.id}"
                        html_confirma = f"""
                        <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
                            <div style="text-align: center; background-color: #28a745; color: white; padding: 10px; border-radius: 8px;">
                                <h2>Pagamento Recebido!</h2>
                            </div>
                            <p>Olá, <strong>{chamado.cliente.nome}</strong>,</p>
                            <p>Confirmamos o recebimento do pagamento referente à <strong>OS #{chamado.id}</strong>.</p>
                            <p>Obrigado por confiar na <strong>SmartFlow</strong>!</p>
                            <hr style="border: 0; border-top: 1px solid #eee;">
                            <p style="font-size: 12px; color: #888; text-align: center;">SmartFlow - Sistema Inteligente</p>
                        </div>
                        """
                        text_confirma = strip_tags(html_confirma)
                        
                        email = EmailMultiAlternatives(assunto, text_confirma, settings.EMAIL_HOST_USER, [chamado.cliente.email])
                        email.attach_alternative(html_confirma, "text/html")
                        email.send()
                    except Exception as e:
                        print(f"Erro ao enviar confirmação: {e}")

    # 5. IMPORTANTE: Retornar sempre 200 para o Mercado Pago não reenviar a mesma coisa
    return HttpResponse(status=200)


def gerar_link_pagamento(chamado):
    sdk = mercadopago.SDK("APP_USR-805107443493899-022520-5a39746b4773f8a8776ec2c51d1160fd-215251480")
    
    preference_data = {
        "items": [
            {
                "title": f"Serviço SmartFlow - OS #{chamado.id}",
                "quantity": 1,
                "unit_price": float(chamado.valor),
            }
        ],
        "external_reference": str(chamado.id),
    }
    
    preference_response = sdk.preference().create(preference_data)
    return preference_response["response"]["init_point"]


# --- 1. DASHBOARD ---
@login_required
def dashboard(request):
    filtro_prioridade = request.GET.get('prioridade')
    

    is_admin = request.user.is_superuser
    
    if is_admin:
        total_recebido = Chamado.objects.filter(status='pago').aggregate(Sum('valor'))['valor__sum'] or 0.00
        aguardando_pgto = Chamado.objects.filter(status='finalizado').count()
    else:

        total_recebido = 0.00
        aguardando_pgto = 0


    em_aberto = Chamado.objects.filter(status='aberto').count()

    context = {
        'is_admin': is_admin,
        'total_recebido': total_recebido,
        'aguardando_pagamento': aguardando_pgto,
        'pendentes_abertos': em_aberto,
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
            
            responsavel_id = request.POST.get('responsavel')
            
            if responsavel_id:
                chamado.responsavel = User.objects.get(id=responsavel_id)
            else:
                chamado.responsavel = request.user
                
            chamado.save()
            return redirect('dashboard')
    else:
        form = ChamadoForm()
    
    return render(request, 'chamadas/criar_chamado.html', {
        'form': form,
        'clientes': Cliente.objects.all(),
        'usuarios': User.objects.all() 
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
        
        # 1. Garantir valor maior que zero
        valor_os = float(chamado.valor) if chamado.valor and chamado.valor > 0 else 1.0
        
        # 2. Configurar SDK Mercado Pago
        sdk = mercadopago.SDK("APP_USR-805107443493899-022520-5a39746b4773f8a8776ec2c51d1160fd-215251480")
        
        preference_data = {
            "items": [
                {
                    "title": f"Serviço SmartFlow - OS #{chamado.id}",
                    "quantity": 1,
                    "unit_price": valor_os,
                }
            ],
            "external_reference": str(chamado.id),
            "back_urls": {
                "success": "https://SEU-NGROK.ngrok-free.app/pagamento/sucesso/", # Troque pelo seu link Ngrok
                "failure": "https://SEU-NGROK.ngrok-free.app/dashboard/",
                "pending": "https://SEU-NGROK.ngrok-free.app/dashboard/"
            },
            "auto_return": "approved",
        }

        # 3. Criar preferência com tratamento de erro
        preference_response = sdk.preference().create(preference_data)
        
        if preference_response["status"] in [200, 201]:
            link_pagamento = preference_response["response"]["init_point"]
        else:
            link_pagamento = "https://www.mercadopago.com.br"
            print(f"--- ERRO MERCADO PAGO OS {chamado.id} ---")
            print(preference_response["response"])

        chamado.save()

        # 4. Enviar E-mail em HTML com Botão Verde
        assunto = f"✅ OS #{chamado.id} Finalizada - SmartFlow"
        remetente = settings.EMAIL_HOST_USER
        destinatario = [chamado.cliente.email]

        html_content = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="background-color: #2c3e50; padding: 20px; text-align: center; color: white;">
                <h1 style="margin: 0;">SmartFlow</h1>
            </div>
            <div style="padding: 30px; background-color: #ffffff;">
                <h2 style="color: #333;">Olá, {chamado.cliente.nome}!</h2>
                <p>Seu chamado foi finalizado com sucesso. Confira os detalhes abaixo:</p>
                
                <div style="background-color: #f8f9fa; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0;">
                    <p><strong>OS:</strong> #{chamado.id}</p>
                    <p><strong>Solução:</strong> {chamado.solucao}</p>
                    <p style="font-size: 18px;"><strong>Valor: R$ {chamado.valor}</strong></p>
                </div>

                <p style="text-align: center; margin-top: 30px;">
                    <a href="{link_pagamento}" style="background-color: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 18px; display: inline-block;">
                        PAGAR AGORA
                    </a>
                </p>
            </div>
            <div style="background-color: #f1f1f1; padding: 15px; text-align: center; color: #999; font-size: 12px;">
                <p>SmartFlow © 2026 - Este é um e-mail automático.</p>
            </div>
        </div>
        """
        
        text_content = strip_tags(html_content)

        try:
            email = EmailMultiAlternatives(assunto, text_content, remetente, destinatario)
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")

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