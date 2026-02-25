from django.db import models
from django.contrib.auth.models import User


class Cliente(models.Model):  
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.nome

class Chamado(models.Model):
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='baixa')
    responsavel = models.CharField(max_length=50) 
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_alteracao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.titulo} - {self.cliente.nome}"


class Chamado(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título")
    prioridade = models.CharField(
        max_length=10, 
        choices=[('baixa', 'Baixa'), ('media', 'Média'), ('alta', 'Alta')],
        default='media'
    )
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Selecione o Cliente")
    descricao = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    descricao = models.TextField()
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
    max_length=20,
    choices=[
        ('aberto', 'Aberto'),
        ('em_andamento', 'Em Atendimento'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado')
    ],
    default='aberto'
)
    
    def __str__(self):
        return self.titulo