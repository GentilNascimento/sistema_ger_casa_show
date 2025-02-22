from django.test import TestCase
from django.urls import reverse
from artistas.models import Artista
from eventos.models import Evento
from datetime import date




class HomeViewTests(TestCase):
    
    def setUp(self):
        #cria um artista para teste
        self.artista = Artista.objects.create(
            nome="Artista Teste",
            cpf="12345678900",
            banco="Banco Teste",
            tipo_chave_pix="cel",
            chave_pix="11987654321"
        )
            
    def test_home_view_status_code(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
    def test_home_view_template_used(self):
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'base.html')
        
    def test_home_view_contains_eventos_proximos(self):
        response = self.client.get(reverse('home'))
        self.assertIn('eventos_proximos', response.context)
        self.assertEqual(response.context['eventos_proximos'].count(), 0)
                
    def test_home_view_contains_evento_descricao(self):
        #cria um evento associado ao artista criado
        Evento.objects.create(
            artista=self.artista,
            data='2024-12-18', 
            horario='18:00', 
            descricao='Evento Teste'
        )
        response = self.client.get(reverse('home'))
        
        # Verifica se o evento aparece no contexto
        self.assertIn('eventos_proximos', response.context)
        eventos_proximos = response.context['eventos_proximos']
        print(eventos_proximos)  # Depuração
        self.assertEqual(eventos_proximos.count(), 1)  # Certifica-se de que um evento está no queryset
    
        # Verifica se a descrição do evento está no HTML
        self.assertContains(response, 'Evento Teste') # Verifica se a descrição do evento está na resposta
        
        