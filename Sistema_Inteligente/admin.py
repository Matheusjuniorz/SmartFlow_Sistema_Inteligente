from django.contrib import admin
from .models import Clientes, Chamadas, Notificacoes, Relatorios

admin.site.register(Clientes)
admin.site.register(Chamadas)
admin.site.register(Notificacoes)
admin.site.register(Relatorios)
