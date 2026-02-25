from django import forms
from .models import Cliente, Chamado

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'email', 'telefone']

class ChamadoForm(forms.ModelForm):
    class Meta:
        model = Chamado
        fields = ['cliente', 'titulo', 'descricao', 'prioridade', 'responsavel']
        
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control'}),
            'prioridade': forms.Select(attrs={'class': 'form-control'}),
            'responsavel': forms.TextInput(attrs={'class': 'form-control'}),
        }