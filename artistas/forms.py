from django import forms
from . import models
from .models import Artista, Message

class ArtistaForm(forms.ModelForm):
    def clean_chave_pix(self):
        chave = self.cleaned_data.get('chave_pix')
        print(f"📢 Valor recebido no form: {chave}")  # Depuração
        return chave
    class Meta:
        model = models.Artista
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_chave_pix': forms.Select(attrs={'class': 'form-control'}),
            'chave_pix': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),            
        }
class MessageForm(forms.ModelForm):
    send_date = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M:'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )
    class Meta:
        model = Message
        fields = ['conteudo', 'send_date']
        widgets = {
            'conteudo': forms.Textarea(attrs={'class': 'form-control'}),
        }