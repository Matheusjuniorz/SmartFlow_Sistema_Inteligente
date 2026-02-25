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
from Sistema_Inteligente import views 
from django.contrib.auth.views import LogoutView # Importação necessária para o Logout
from two_factor.views import (
    LoginView, SetupView, QRGeneratorView, SetupCompleteView, 
    BackupTokensView, ProfileView, DisableView
)

# 1. Lista de URLs da autenticação incluindo o Logout
auth_patterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'), # Rota de saída adicionada
    path('setup/', SetupView.as_view(), name='setup'),
    path('qrcode/', QRGeneratorView.as_view(), name='qr'),
    path('setup/complete/', SetupCompleteView.as_view(), name='setup_complete'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('backup/tokens/', BackupTokensView.as_view(), name='backup_tokens'),
    path('disable/', DisableView.as_view(), name='disable'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 2. Incluindo as rotas manuais no namespace exigido pelo pacote
    path('account/', include((auth_patterns, 'two_factor'), namespace='two_factor')),

    # Suas rotas do Sistema SmartFlow
    path('dashboard/', views.dashboard, name='dashboard'),
    path('chamado/<int:chamado_id>/', views.detalhe_chamado, name='detalhe_chamado'),
    path('chamado/excluir/<int:chamado_id>/', views.excluir_chamado, name='excluir_chamado'),
    path('chamado/status/<int:chamado_id>/<str:novo_status>/', views.mudar_status, name='mudar_status'),
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/novo/', views.criar_cliente, name='criar_cliente'),
    path('clientes/editar/<int:id>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/excluir/<int:id>/', views.excluir_cliente, name='excluir_cliente'),
    path('chamados/novo/', views.criar_chamado, name='criar_chamado'),
    path('chamados/', views.lista_chamados, name='lista_chamados'),
    path('registrar/', views.registrar_responsavel, name='registrar_responsavel'),
]