"""
URL configuration for SmartFlow_Sistema_Inteligente project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from Sistema_Inteligente import views 
from django.contrib.auth.views import LogoutView 
from two_factor.views import (
    LoginView, SetupView, QRGeneratorView, SetupCompleteView, 
    BackupTokensView, ProfileView, DisableView
)
from django.conf import settings  
from django.conf.urls.static import static


# 1. Lista de URLs da autenticação
auth_patterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('setup/', SetupView.as_view(), name='setup'),
    path('qrcode/', QRGeneratorView.as_view(), name='qr'),
    path('setup/complete/', SetupCompleteView.as_view(), name='setup_complete'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('backup/tokens/', BackupTokensView.as_view(), name='backup_tokens'),
    path('disable/', DisableView.as_view(), name='disable'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    
    #login
    path('login/', LoginView.as_view(template_name='two_factor/core/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # 2. Autenticação Two-Factor
    path('account/', include((auth_patterns, 'two_factor'), namespace='two_factor')),

    # --- Suas rotas do Sistema SmartFlow ---
    
    # Dashboard e Filtros
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Gestão de Chamados (Ajustadas para bater com seu HTML)
    path('chamados/novo/', views.criar_chamado, name='criar_chamado'),
    path('chamados/pdf/', views.gerar_pdf_chamados, name='gerar_pdf_chamados'),
    path('chamados/', views.lista_chamados, name='lista_chamados'),
    path('chamados/detalhe/<int:chamado_id>/', views.detalhe_chamado, name='detalhe_chamado'), 
    path('chamados/finalizar/<int:chamado_id>/', views.finalizar_chamado, name='finalizar_chamado'),
    path('chamados/excluir/<int:chamado_id>/', views.excluir_chamado, name='excluir_chamado'),
    path('chamados/status/<int:chamado_id>/<str:novo_status>/', views.mudar_status, name='mudar_status'),
    path('relatorios/', views.relatorio_chamados, name='relatorios'),
    path('chamado/pagar/<int:chamado_id>/', views.finalizar_chamado, name='finalizar_chamado'),
    path('chamados/finalizar/<int:chamado_id>/', views.finalizar_chamado, name='finalizar_chamado'),
    path('webhooks/mercadopago/', views.mercadopago_webhook, name='mp_webhook'),
    path('pagamento/sucesso/', views.pagamento_sucesso, name='pagamento_sucesso'),
    path('chamados/registrados/', views.chamados_registrados, name='chamados_registrados'),

    # Gestão de Clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/novo/', views.criar_cliente, name='criar_cliente'),
    path('clientes/editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/excluir/<int:id>/', views.excluir_cliente, name='excluir_cliente'),
    path('chamados/os/<int:chamado_id>/', views.gerar_os_pdf, name='gerar_os_pdf'),
    

    # Usuários
    path('registrar/', views.registrar_responsavel, name='registrar_responsavel'),
        
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])