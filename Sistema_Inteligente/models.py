from django.db import models
from django.contrib.auth.models import User

class Cliente(models.Model):  
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.nome

class Chamado(models.Model):
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
    ]

    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('atendimento', 'Em Atendimento'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]

    MEIO_PAGAMENTO_CHOICES = [
        ('dinheiro', 'Dinheiro'),
        ('pix', 'PIX'),
        ('cartao', 'Cartão de Crédito/Débito'),
        ('boleto', 'Boleto'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Responsável")
    
    descricao = models.TextField(verbose_name="Descrição do Problema", default="") 
    solucao = models.TextField(blank=True, null=True, verbose_name="Solução") 
    
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='media')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')

    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_alteracao = models.DateTimeField(auto_now=True) # Mantive este que é útil
    data_finalizacao = models.DateTimeField(blank=True, null=True)

    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    meio_pagamento = models.CharField(max_length=50, choices=MEIO_PAGAMENTO_CHOICES, default='pix')
    
    def __str__(self):
        return f"#{self.id} - {self.titulo}"