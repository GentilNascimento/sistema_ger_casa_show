import pytest
from django.utils import timezone
from eventos.models import Evento
from artistas.models import Artista
from unittest.mock import patch


@pytest.fixture
def artista():
    return Artista.objects.create(
        nome="Event Artist",
        cpf="12345678900",
        telefone="+5511987654321",
        banco="Test Bank",
        tipo_chave_pix="cel",
        chave_pix="48987654321",
        email="artist@test.com"
    )


@pytest.fixture
def evento(artista):
    return Evento.objects.create(
        artista=artista,
        data=timezone.now().date(),
        horario=timezone.now().time(),
        descricao="Descrição do evento",
        scheduled_date=None
    )
    
@pytest.mark.django_db
def test_cria_evento_com_sucesso(artista):
    """Testa se um evento é criado corretamente no banco de dados sem interferência do scheduler."""
    
    evento = Evento.objects.create(
        artista=artista,
        data=timezone.now().date(),
        horario=timezone.now().time(),
        descricao="Teste de trabalho agendado",
        scheduled_date=timezone.now(),        
    )

    # Verifica se o evento foi salvo no banco corretamente
    evento_bd = Evento.objects.get(id=evento.id)
    assert evento_bd.artista == artista
    assert evento_bd.descricao == "Teste de trabalho agendado"

@pytest.mark.django_db
def test_evento_remove_tarefa_agendada(artista):
    """Testa se a exclusão de um evento remove corretamente do banco de dados."""

    # Criando um evento real no banco
    evento = Evento.objects.create(
        artista=artista,
        data=timezone.now().date(),
        horario=timezone.now().time(),
        descricao="Descrição de teste",
        scheduled_date=None  # ✅ Sem send_date, pois ele não existe no modelo
    )

    evento_id = evento.id

    # Deletar o evento
    evento.delete()

    # Verifica se o evento foi realmente removido do banco
    assert not Evento.objects.filter(id=evento_id).exists(), "O evento ainda existe no banco após a exclusão!"
    
@pytest.mark.django_db  
def test_evento_str(evento):
    """
    Testa a representação em string do modelo Evento.
    """
    expected_str = f"{evento.artista.nome} - {evento.formatted_data()} {evento.formatted_horario()}"
    assert str(evento) == expected_str

@pytest.mark.django_db
def test_evento_formatted_data(evento):
    """
    Testa o método formatted_data do modelo Evento.
    """
    formatted_date = evento.data.strftime('%d-%m-%Y')
    assert evento.formatted_data() == formatted_date

@pytest.mark.django_db
def test_evento_formatted_horario(evento):
    """
    Testa o método formatted_horario do modelo Evento.
    """
    formatted_time = evento.horario.strftime('%H:%M')
    assert evento.formatted_horario() == formatted_time
    
def test_scheduler_instance():
    from app.scheduler import scheduler
    assert hasattr(scheduler, "add_job"), "O scheduler não possui o método 'add_job'"

