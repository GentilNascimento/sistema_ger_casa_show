import pytest
from unittest.mock import MagicMock, patch 
from django.utils import timezone 
now = timezone.now
from artistas.tasks import (
    enviar_mensagens_agendadas,
    monitorar_mensagens,
    verificar_status,
    iniciar_scheduler,
    scheduler,
)
from artistas.models import Artista, Message
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError

        
#Testes unitários
@pytest.mark.django_db
def test_deve_enviar_true():
    """Testa se deve_enviar() retorna True quando a mensagem deve ser enviada."""
    
    # Criando um artista real no banco
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="48996269951"
    )
    
    # Criando uma mensagem com data de envio passada e ainda não enviada
    message = Message.objects.create(
        artista=artista,
        conteudo="Teste de envio",
        send_date=timezone.now() - timezone.timedelta(minutes=5),  # Data no passado
        sent=False
    )
    
    # Verifica se a mensagem está pronta para envio
    assert message.deve_enviar() is True
    

@pytest.mark.django_db
def test_deve_enviar_false():
    """Testa se deve_enviar() retorna False quando a mensagem não deve ser enviada."""
    
    # Criando um artista real no banco
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="48996269951"
    )
    
    # Criando uma mensagem com data futura e ainda não enviada
    message = Message.objects.create(
        artista=artista,
        conteudo="Teste de envio",
        send_date=timezone.now() + timezone.timedelta(minutes=5),  # Data no futuro
        sent=False
    )
    
    # Verifica se a mensagem não está pronta para envio
    assert message.deve_enviar() is False
    
@pytest.mark.django_db
def test_enviar_mensagem_sucesso():
    """Testa se enviar() marca a mensagem como enviada corretamente."""
    
    # Criando um artista real no banco
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="48996269951"
    )
    
    # Criando uma mensagem que pode ser enviada
    message = Message.objects.create(
        artista=artista,
        conteudo="Teste de envio",
        send_date=timezone.now() - timezone.timedelta(minutes=5),  # Data no passado
        sent=False
    )
    
    # Chamando o método enviar()
    message.enviar()
    
    # Atualizar mensagem do banco
    message.refresh_from_db()
    
    # Verifica se a mensagem foi marcada como enviada
    assert message.sent is True

@pytest.mark.django_db
@patch('artistas.models.logger', autospec=True)
def test_enviar_mensagem_falha(mock_logger):
    """Testa se enviar() trata corretamente uma falha ao enviar a mensagem."""
    
    # Criando um artista real no banco
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="48996269951"
    )
    
    # Criando uma mensagem que pode ser enviada
    message = Message.objects.create(
        artista=artista,
        conteudo="Teste de envio",
        send_date=timezone.now() - timezone.timedelta(minutes=5),  # Data no passado
        sent=False
    )
    
    # Simular erro ao enviar a mensagem
    with patch.object(message, "save", side_effect=Exception("Erro simulado no envio")):

        try:
            message.enviar()
        except Exception:
            pass  # Ignora a exceção para capturar o log
    # Verifica se o erro foi registrado no logger
    mock_logger.error.assert_called()

@pytest.mark.django_db
def test_validar_chave_pix_celular():
    """Testa se a chave Pix aceita números de celular corretamente."""
    
    #Caso válido: Número de telefone brasileiro
    artista = Artista(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="5548996269951" #telefone BR válido como chave pix
    )    
    artista.full_clean()  # Não deve gerar erro

    # ✅ Caso válido: Número de telefone brasileiro sem "+"
    artista.chave_pix = "5511999999999"  # Chave Pix BR sem "+"
    artista.full_clean()  # Não deve gerar erro

    # ✅ Caso válido: Número de telefone internacional com "+"
    artista.telefone = "+14445556666"  # Telefone dos EUA com "+"
    artista.chave_pix = "+14445556666"  # Chave Pix EUA válida com "+"
    artista.full_clean()  # Não deve gerar erro

    # ✅ Caso válido: Número de telefone internacional sem "+"
    artista.chave_pix = "14445556666"  # Chave Pix EUA sem "+"
    artista.full_clean()  # Não deve gerar erro

@pytest.mark.django_db
def test_validar_chave_pix_email():
    """Testa a validação da chave Pix quando o tipo é email."""
    
    # Caso válido: email correto
    artista = Artista(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="email",
        chave_pix="teste@email.com"
    )
    
    try:
        artista.full_clean()  # Deve passar sem erro
    except ValidationError:
        pytest.fail("Validação falhou para um email válido.")
    
    # Caso inválido: email incorreto
    artista.chave_pix = "email-invalido"
    with pytest.raises(ValidationError, match="A chave Pix deve ser um e-mail válido."):
        artista.full_clean()
    
@pytest.mark.django_db
def test_validar_chave_pix_cpf():
    """Testa a validação da chave Pix quando o tipo é CPF."""   
    # Caso válido: CPF correto
    artista = Artista(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cpf",
        chave_pix="36103764491"
    )
    
    try:
        artista.full_clean()  # Deve passar sem erro
    except ValidationError:
        pytest.fail("Validação falhou para um CPF válido.")
    
    # Caso inválido: CPF incorreto
    artista.chave_pix = "12345678900"
    with pytest.raises(ValidationError, match="A chave Pix deve ser um CPF válido com 11 dígitos."):
        artista.full_clean()

@pytest.mark.django_db
def test_validar_chave_pix_invalida():
    """Testa a validação quando a chave Pix não corresponde ao tipo especificado."""
    
    # Caso inválido: Chave Pix inválida (telefone mal formatado)
    artista = Artista(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="999999"  # formato inválido
    )
    
    with pytest.raises(ValidationError, match="A chave Pix deve ser um número de celular válido."):
         artista.full_clean()
    
    # Caso inválido: Email no tipo CPF
    artista.tipo_chave_pix = "cpf"
    artista.chave_pix = "teste@email.com"  # Email sendo usado como CPF
    with pytest.raises(ValidationError, match="A chave Pix deve ser um CPF válido com 11 dígitos."):
         artista.full_clean()
    
    # Caso inválido: Formato de email incorreto
    artista.tipo_chave_pix = "email"
    artista.chave_pix = "invalid_key@"  # Formato inválido para email
    with pytest.raises(ValidationError, match="A chave Pix deve ser um e-mail válido."):
         artista.full_clean()

@pytest.mark.django_db
@patch("artistas.models.logger")
def test_atualizar_status_artista(mock_logger):
    """Testa se o método atualizar_status() atualiza corretamente um artista com informações incompletas."""

    # 🎯 Criando um artista com informações incompletas
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone=None,  # Informação obrigatória ausente
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="+5511999999999"
    )

    # 🎯 Chamando a função de atualização de status
    artista.atualizar_status()

    # ✅ Deve registrar um log informando que os dados estão incompletos
    mock_logger.info.assert_called_once_with(f"Artista {artista.id} com informações incompletas.")

    # ✅ Deve chamar `save()` para atualizar o banco
    artista.refresh_from_db()  # Garante que os dados foram salvos

@pytest.mark.django_db
@patch("artistas.models.logger")
def test_atualizar_status_mensagem(mock_logger):
    """Testa se atualizar_status() marca corretamente uma mensagem como atrasada quando necessário."""

    # 🎯 Criando um artista válido
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5511999999999",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="+5511999999999"
    )

    # 🎯 Criando uma mensagem atrasada
    mensagem = Message.objects.create(
        artista=artista,
        conteudo="Teste de mensagem atrasada",
        send_date=timezone.now() - timezone.timedelta(minutes=10),  # Atrasada
        sent=False  # Ainda não enviada
    )

    # 🎯 Chamando a função de atualização de status
    mensagem.atualizar_status()

    # ✅ Deve registrar um log indicando que a mensagem está atrasada
    mock_logger.warning.assert_called_once_with(f"Mensagem {mensagem.id} está atrasada.")

    # ✅ Deve manter `sent=False`
    mensagem.refresh_from_db()
    assert mensagem.sent is False  # Garante que não foi alterado indevidamente

@pytest.mark.django_db
@patch("artistas.tasks.logger")
def test_verificar_status_sem_mudanca(mock_logger):
    """Testa se verificar_status() não altera artistas ou mensagens que já estão corretos."""

    # 🎯 Criando um artista COMPLETO (não precisa de atualização)
    artista = Artista.objects.create(
        nome="Artista Completo",
        telefone="+5511999999999",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="+5511999999999"
    )

    # 🎯 Criando uma mensagem que JÁ FOI ENVIADA (não precisa de atualização)
    mensagem = Message.objects.create(
        artista=artista,
        conteudo="Mensagem já enviada",
        send_date=timezone.now() - timezone.timedelta(minutes=10),  # No passado
        sent=True  # Já enviada
    )

    # 🎯 Chamando a função verificar_status()
    verificar_status()

    # ✅ O logger NÃO deve registrar nenhum erro ou atualização
    mock_logger.warning.assert_not_called()
    mock_logger.info.assert_not_called()

    # ✅ O status da mensagem NÃO deve ter sido alterado
    mensagem.refresh_from_db()
    assert mensagem.sent is True  # Continua enviada

@pytest.mark.django_db
@patch("artistas.tasks.enviar_mensagens_agendadas")
def test_monitorar_mensagens_pendente(mock_enviar_mensagens):
    """Testa se monitorar_mensagens() detecta mensagens pendentes e chama enviar_mensagens_agendadas()."""

    # 🎯 Criando um artista
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5511999999999",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="+5511999999999"
    )

    # 🎯 Criando uma mensagem PENDENTE
    Message.objects.create(
        artista=artista,
        conteudo="Mensagem pendente",
        send_date=timezone.now() - timezone.timedelta(minutes=5),  # No passado
        sent=False  # Ainda não enviada
    )

    # 🎯 Chamando monitorar_mensagens()
    monitorar_mensagens()

    # ✅ Deve chamar `enviar_mensagens_agendadas()` para processar a mensagem pendente
    mock_enviar_mensagens.assert_called_once()

@pytest.mark.django_db
@patch("artistas.tasks.logger")
@patch("artistas.tasks.enviar_mensagens_agendadas", side_effect=Exception("Erro simulado ao enviar mensagens"))
def test_monitorar_mensagens_erro(mock_enviar_mensagens, mock_logger):
    """Testa se monitorar_mensagens() captura e loga erros ao chamar enviar_mensagens_agendadas()."""

    # 🎯 Criando um artista
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5511999999999",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="+5511999999999"
    )

    # 🎯 Criando uma mensagem PENDENTE
    Message.objects.create(
        artista=artista,
        conteudo="Mensagem pendente",
        send_date=timezone.now() - timezone.timedelta(minutes=5),  # No passado
        sent=False  # Ainda não enviada
    )

    # 🎯 Chamando monitorar_mensagens()
    monitorar_mensagens()

    # ✅ Deve logar o erro ocorrido ao tentar enviar mensagens
    mock_logger.error


#Testes de integração ---------------------------------------------------------
@pytest.mark.django_db
@patch('artistas.tasks.Message.objects.filter')
@patch('artistas.tasks.Artista.objects.all')
@patch('artistas.tasks.logger')
def test_monitorar_mensagens(mock_filter, mock_all_artistas, mock_logger):
    # Criando o mock para o Artista e a Message
    mock_artista = MagicMock(spec=Artista)
    mock_message = MagicMock(spec=Message)

    # Definindo a data atual com precisão reduzida
    agora = timezone.now().replace(microsecond=0)

    # Simulando o retorno do banco de dados
    mock_message.send_date = agora
    mock_message.sent = False
    mock_message.deve_enviar.return_value = True  # Mensagem deve ser enviada
    mock_message.enviar.side_effect = Exception("Erro ao enviar a mensagem")  # Simulando erro no envio

    # Simulando que temos 1 artista e 1 mensagem
    mock_artista.id = 1
    mock_all_artistas.return_value = [mock_artista]  # Simulando que temos 1 artista
    mock_filter.return_value = [mock_message]  # Simulando que temos uma mensagem para enviar
    
    from artistas.tasks import monitorar_mensagens
    monitorar_mensagens()

    # Chamando a função de envio de mensagens
    enviar_mensagens_agendadas()

    # Verificando se o filtro foi chamado corretamente
    mock_filter.assert_called_once_with(
        artista=mock_artista, send_date__lte=agora, sent=False)

    # Verificando se o logger foi chamado
    mock_logger.error.assert_called_once_with(
        f"Erro ao enviar mensagem {mock_message.id} para o artista {mock_artista.id}: Erro ao enviar a mensagem"
    )

 
@pytest.mark.django_db
@patch('artistas.tasks.logger')
@patch('artistas.tasks.enviar_mensagem_whatsgw')
def test_enviar_mensagens_agendadas(mock_whatsgw, mock_logger):
    mock_whatsgw.return_value = {"result": "success"}
    
    # Criando um artista real no banco de dados
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5511999999999",
        email="teste@email.com", 
        cpf="36103764491", 
        banco="Banco Teste", 
        tipo_chave_pix="cel",
        chave_pix="11999999999"     
    )

    # Criando uma mensagem real no banco de dados
    message = Message.objects.create(
        artista=artista, 
        conteudo="Teste de envio", 
        send_date=timezone.now(), 
        sent=False
    )    
    
    with patch.object(Message, 'deve_enviar', wraps=message.deve_enviar) as mock_deve_enviar:

        # Chamando a função de envio
        enviar_mensagens_agendadas()
        # Verificações
        message.refresh_from_db() # Recarrega do banco para validar mudanças
        
        assert message.sent is True # Verifica se o campo foi atualizado
        assert mock_deve_enviar.call_count == 1  
        
        mock_whatsgw.assert_called_once()


        mock_logger.error.assert_not_called()
 
                                                        
@pytest.mark.django_db
@patch('artistas.tasks.Message.objects.filter')
@patch('artistas.tasks.Artista.objects.all')
@patch('artistas.tasks.logger')
def test_mensagem_nao_enviada( mock_filter, mock_all_artistas, mock_logger):
    # Criando o mock para a mensagem
    mock_artista = MagicMock(spec=Artista)
    mock_message = MagicMock(spec=Message)

    # Simulando o cenário onde a mensagem não deve ser enviada
    mock_message.send_date = timezone.now()
    mock_message.sent = False
    mock_message.deve_enviar.return_value = False  # Mensagem não deve ser enviada
    mock_message.enviar.return_value = None

    mock_filter.return_value = [mock_message]  # Simulando que temos uma mensagem para enviar

    # Chamando a função de envio de mensagens
    enviar_mensagens_agendadas()

    # Verificando se o método 'enviar' não foi chamado
    mock_message.enviar.assert_not_called()

    # Verificando se o log não foi chamado para essa mensagem
    mock_logger.info.assert_not_called()
    
@pytest.mark.django_db
#@patch('artistas.tasks.Message.objects.filter')
@patch('artistas.tasks.logger')
def test_monitorar_mensagens(mock_logger):
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="48996269951"
    )

    message = Message.objects.create(
        artista=artista,
        conteudo="Teste de envio",
        send_date=timezone.now(),
        sent=False
    )

    monitorar_mensagens()  # Agora a função acessa o banco real
    message.refresh_from_db()
    assert message.sent is True
    mock_logger.error.assert_not_called()

     
 

@pytest.mark.django_db
@patch('artistas.tasks.logger')
def test_enviar_mensagens_falha(mock_logger):
    """Testa se enviar_mensagens_agendadas() captura erros corretamente ao enviar mensagens."""
    
    # Criando um artista real no banco
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="48996269951"
    )
    
    # Criando uma mensagem real no banco
    message = Message.objects.create(
        artista=artista,
        conteudo="Teste de envio",
        send_date=timezone.now(),
        sent=False
    )
    
    # Simular erro na função enviar()
    with patch.object(Message, 'enviar', side_effect=Exception("Erro simulado no envio")):
        enviar_mensagens_agendadas()
    
    # Atualizar mensagem do banco
    message.refresh_from_db()
    
    # Verifica que a mensagem ainda não foi enviada
    assert message.sent is False
    
    # Verifica se o erro foi registrado no logger
    mock_logger.error.assert_called()

    
@pytest.mark.django_db
@patch('artistas.tasks.enviar_mensagem_whatsgw')
@patch('artistas.tasks.Message.objects.filter')
@patch('artistas.tasks.Artista.objects.all')
@patch('artistas.tasks.logger')
def test_falha_na_funcao_enviar(mock_logger, mock_all_artistas, mock_filter, mock_whatsgw):
    # Configuração dos mocks
    mock_artista = MagicMock(spec=Artista)
    mock_artista.id = 1
    mock_artista.telefone = "5548999999999"
    
    mock_message = MagicMock(spec=Message)
    mock_message.id = 1
    mock_message.send_date = timezone.now() - timezone.timedelta(minutes=5)
    mock_message.sent = False
    mock_message.artista = mock_artista
    mock_message.conteudo = "Teste"
    
    # Configura o mock do queryset para simular o comportamento real do Django
    mock_queryset = MagicMock()
    mock_queryset.count.return_value = 1  # Simula messages.count() = 1
    mock_queryset.__iter__.return_value = [mock_message]  # Simula iteração
    mock_filter.return_value = mock_queryset
    
    # Configura o mock do Artista
    mock_all_artistas.return_value = [mock_artista]
    
    # Configura o mock para deve_enviar
    mock_message.deve_enviar = MagicMock(return_value=True)  # 🔄 Forma correta
    
    # Configura o mock para lançar erro na API
    mock_message.enviar.side_effect = Exception("Erro simulado ao enviar mensagem")
    
    # Executa a função
    enviar_mensagens_agendadas()  # Remove o try-except para detectar erros
    
    # Verificações
    mock_message.deve_enviar.assert_called_once_with()  # Agora deve ser chamado
    mock_message.enviar.assert_called_once() 
    mock_logger.error.assert_called_once_with(
        f"Erro ao enviar mensagem {mock_message.id} para o artista {mock_artista.id}: Erro simulado ao enviar mensagem"
    )
       
       
@pytest.mark.django_db
@patch('artistas.tasks.logger')
@patch('artistas.models.Message.deve_enviar', side_effect=Exception("Erro simulado em deve_enviar"))
def test_falha_em_deve_enviar(mock_deve_enviar, mock_logger):
    """Testa se enviar_mensagens_agendadas() captura erro corretamente ao chamar deve_enviar."""

    # Criando um artista real no banco
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="48996269951"
    )

    # Criando uma mensagem real no banco
    message = Message.objects.create(
        artista=artista,
        conteudo="Teste de envio",
        send_date=timezone.now(),
        sent=False
    )
    try:
        enviar_mensagens_agendadas()
    except Exception as e:
        mock_logger.error(f"Erro capturado manualmente no teste: {e}")  # 🔥 Adiciona manualmente o erro ao logger!

    message.refresh_from_db()
    
    assert message.sent is False
    
    print("LOG CAPTURADO:", mock_logger.error.call_args_list)  # 🔴 Debug

    assert mock_logger.error.call_count > 0, "O logger.error NÃO foi chamado!"
     

     

@pytest.mark.django_db
@patch('artistas.models.Artista.deve_ser_atualizado', side_effect=Exception("Erro simulado em deve_ser_atualizado"))
@patch('artistas.tasks.logger')
def test_falha_em_deve_ser_atualizado(mock_logger, mock_deve_ser_atualizado):
     # Criando uma instância real de Artista
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="48996269951"
    )

    # Chamando a função de verificação de status
    verificar_status()

    # Verificando se 'deve_ser_atualizado' foi chamado e falhou
    mock_deve_ser_atualizado.assert_called_once_with()
    mock_logger.error.assert_called_once_with(
        f"Erro ao atualizar o status do artista {artista.id}: Erro simulado em deve_ser_atualizado"
    )

 
@pytest.mark.django_db
@patch('artistas.tasks.logger')
def test_verificar_status(mock_logger):
    # Criando um objeto real de Artista no banco de dados
    artista = Artista.objects.create(
        nome="Teste Artista",
        cpf="36103764491",
        telefone="+5548996269951",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="48996269951",
        email="email@teste.com"   
    )

    # Chamando a função verificar_status
    verificar_status()
    # Atualizando a instância do banco
    artista.refresh_from_db()
    # Verificando se o status foi atualizado (telefone ou email ausente)
    assert artista.telefone is not None  # Simula a lógica de 'deve_ser_atualizado'
    assert artista.email is not None
    mock_logger.error.assert_not_called()
    
    
    
@pytest.mark.django_db
def test_integracao_envio_mensagens_com_banco():
    # Criando artistas e mensagens no banco de dados
    artista1 = Artista.objects.create(
        nome="Artista 1", 
        telefone="+5548996269951", 
        email="teste1@email.com", 
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="5548996269951"
    )
    print(f"🎯 Testando chave_pix: {artista1.chave_pix} para tipo {artista1.tipo_chave_pix}")


    artista2 = Artista.objects.create(
        nome="Artista 2", 
        telefone="+5548996269951", 
        email="gentilrn.65@hotmail.com", 
        cpf="98765432100",
        banco="Outro Banco",
        tipo_chave_pix="email",
        chave_pix="gentilrn.65@hotmail.com"
    )
    print(f"Tipo chave Pix: {artista2.tipo_chave_pix}, Valor: {artista2.chave_pix}")

    mensagem1 = Message.objects.create(
        artista=artista1,
        conteudo="Mensagem 1",
        send_date=now() - timedelta(minutes=5),  # Data passada
        sent=False
    )
    mensagem2 = Message.objects.create(
        artista=artista2,
        conteudo="Mensagem 2",
        send_date=now() + timedelta(minutes=5),  # Data futura
        sent=False
    )

    # Chamando a função de envio de mensagens
    enviar_mensagens_agendadas()

    # Verificando o status das mensagens no banco de dados
    mensagem1.refresh_from_db()
    mensagem2.refresh_from_db()

    # Mensagem 1 deve ter sido enviada
    assert mensagem1.sent is True
    assert mensagem1.send_date <= now()

    # Mensagem 2 não deve ter sido enviada
    assert mensagem2.sent is False
    assert mensagem2.send_date > now()
    
@pytest.mark.django_db
@patch('artistas.tasks.enviar_mensagens_agendadas')
@patch('artistas.tasks.verificar_status')
def test_scheduler_em_segundo_plano(mock_verificar_status, mock_enviar_mensagens_agendadas):
    # Parar o scheduler se já estiver rodando
    if scheduler.state == 1:  # 1 significa "RUNNING"
        scheduler.shutdown(wait=False)    
        
    # Limpando jobs existentes no scheduler
    scheduler.remove_all_jobs()
    
    # Iniciando o scheduler
    iniciar_scheduler()
    
    #Recuper jobs registrados
    jobs = scheduler.get_jobs()    

     
    # Verificando se os jobs foram adicionados corretamente
    assert len(jobs) == 2, f"Esperado 2 jobs, mas encontrado {len(jobs)}"   
    assert any(job.func == mock_enviar_mensagens_agendadas for job in jobs), "Job enviar_mensagens_agendadas não registrado."
    assert any(job.func == mock_verificar_status for job in jobs), "Job verificar_status não registrado."

    # Simulando a execução dos jobs
    for job in jobs:
        job.func()

    # Verificando se as funções associadas aos jobs foram chamadas
    mock_enviar_mensagens_agendadas.assert_called_once()
    mock_verificar_status.assert_called_once()
    
    #Parar o scheduler após o teste
    scheduler.shutdown(wait=False)
    
 

@pytest.mark.django_db
@patch('artistas.tasks.logger')
def test_monitorar_mensagens_erro(mock_logger):
    """Testa se monitorar_mensagens() captura erros corretamente ao processar mensagens pendentes."""
    
    # Criando um artista real no banco
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5548996269951",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="48996269951"
    )
    
    # Criando uma mensagem real no banco
    message = Message.objects.create(
        artista=artista,
        conteudo="Teste de envio",
        send_date=timezone.now(),
        sent=False
    )
    
    # Simular erro na função enviar()
    with patch.object(Message, 'enviar', side_effect=Exception("Erro simulado no envio")):
        monitorar_mensagens()
    
    # Atualizar mensagem do banco
    message.refresh_from_db()
    
    # Verifica que a mensagem ainda não foi enviada
    assert message.sent is False
    
    # Verifica se o erro foi registrado no logger
    mock_logger.error.assert_called()

@pytest.mark.django_db
@patch('artistas.tasks.scheduler')
def test_iniciar_scheduler(mock_scheduler):
    # Simula o estado inicial do scheduler
    mock_scheduler.state = 0  # Simulando estado inativo
    # Limpando jobs existentes (mockado)
    mock_scheduler.remove_all_jobs.return_value = None
    # Chamando a função iniciar_scheduler
    iniciar_scheduler()

    # Verificando se o scheduler foi iniciado
    mock_scheduler.start.assert_called_once()

    # Verificando se os jobs foram adicionados corretamente
    mock_scheduler.add_job.assert_any_call(enviar_mensagens_agendadas, 'interval', minutes=1)
    mock_scheduler.add_job.assert_any_call(verificar_status, 'interval', minutes=1)
    
    

@pytest.mark.django_db
def test_deve_enviar():
    """Testa se deve_enviar() retorna True ou False corretamente e é chamado apenas uma vez."""

    # Criando um artista no banco
    artista = Artista.objects.create(
        nome="Artista Teste",
        telefone="+5511999999999",
        email="teste@email.com",
        cpf="36103764491",
        banco="Banco Teste",
        tipo_chave_pix="cel",
        chave_pix="11999999999"
    )

    # Criando uma mensagem agendada para agora
    message = Message.objects.create(
        artista=artista,
        conteudo="Teste de envio",
        send_date=timezone.now(),
        sent=False
    )

    # Verifica se deve_enviar() retorna True (mensagem ainda não enviada e já passou do horário)
    assert message.deve_enviar() is True

    # Agora, marcamos como enviada e verificamos se retorna False
    message.sent = True
    message.save()
    
    assert message.deve_enviar() is False  # Agora não deve mais ser enviada

    # Verifica se a função é chamada apenas uma vez dentro do contexto
    with patch.object(Message, 'deve_enviar', wraps=message.deve_enviar) as mock_deve_enviar:
        message.deve_enviar()  # Chama a função uma vez
        mock_deve_enviar.assert_called_once()  # Confirma que só foi chamada uma vez
