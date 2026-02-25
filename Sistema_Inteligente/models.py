from django.db import models

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
