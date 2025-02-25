import pytest
from unittest import mock
import configparser
import pika
from src.rabbitmq import (
    load_rabbitmq_config,
    get_rabbitmq_var,
    check_rabbitmq_connection,
    send_rabbitmq
)

@pytest.fixture
def mock_config_parser():
    """Fixture para simular o ConfigParser."""
    with mock.patch('configparser.ConfigParser') as mock_parser:
        config_mock = mock.MagicMock()
        mock_parser.return_value = config_mock
        yield config_mock

@pytest.fixture
def mock_rabbitmq_connection():
    """Fixture para simular a conexão com o RabbitMQ."""
    with mock.patch('pika.BlockingConnection') as mock_conn:
        connection = mock.MagicMock()
        mock_conn.return_value = connection
        channel = mock.MagicMock()
        connection.channel.return_value = channel
        yield connection, channel

@pytest.mark.unit
def test_load_rabbitmq_config(mock_config_parser):
    """Testa a função load_rabbitmq_config."""
    # Configurando o comportamento do mock
    mock_config_parser.get.side_effect = [
        "localhost", "5672", "guest", "guest", "/", "topic", "key"
    ]
    
    # Chamando a função
    result = load_rabbitmq_config()
    
    # Verificando se o método read foi chamado com o arquivo correto
    mock_config_parser.read.assert_called_once_with("config.ini")
    
    # Verificando se o resultado é o esperado
    expected_result = {
        "host": "localhost",
        "port": "5672",
        "username": "guest",
        "password": "guest",
        "caminho": "/",
        "topico": "topic",
        "chave": "key"
    }
    assert result == expected_result

@pytest.mark.unit
def test_get_rabbitmq_var():
    """Testa a função get_rabbitmq_var."""
    # Mockando a função load_rabbitmq_config
    with mock.patch('src.rabbitmq.load_rabbitmq_config') as mock_load:
        mock_load.return_value = {
            "host": "localhost",
            "port": "5672"
        }
        
        # Testando uma variável existente
        assert get_rabbitmq_var("host") == "localhost"
        
        # Testando uma variável inexistente
        assert get_rabbitmq_var("nonexistent") is None

@pytest.mark.unit
def test_check_rabbitmq_connection_success():
    """Testa a função check_rabbitmq_connection quando a conexão é bem-sucedida."""
    # Mockando as funções necessárias
    with mock.patch('src.rabbitmq.get_rabbitmq_var') as mock_get_var, \
         mock.patch('pika.PlainCredentials') as mock_credentials, \
         mock.patch('pika.ConnectionParameters') as mock_params, \
         mock.patch('pika.BlockingConnection') as mock_connection, \
         mock.patch('builtins.print') as mock_print:
        
        # Configurando os mocks
        mock_get_var.side_effect = ["user", "pass", "host", "5672"]
        mock_connection_instance = mock.MagicMock()
        mock_connection.return_value = mock_connection_instance
        
        # Chamando a função
        result = check_rabbitmq_connection()
        
        # Verificando se a função retornou True
        assert result is True
        
        # Verificando se os mocks foram chamados corretamente
        mock_credentials.assert_called_once_with("user", "pass")
        mock_params.assert_called_once()
        mock_connection.assert_called_once()
        mock_connection_instance.close.assert_called_once()

@pytest.mark.unit
def test_check_rabbitmq_connection_failure():
    """Testa a função check_rabbitmq_connection quando a conexão falha."""
    # Mockando as funções necessárias
    with mock.patch('src.rabbitmq.get_rabbitmq_var') as mock_get_var, \
         mock.patch('pika.PlainCredentials') as mock_credentials, \
         mock.patch('pika.ConnectionParameters') as mock_params, \
         mock.patch('pika.BlockingConnection') as mock_connection, \
         mock.patch('builtins.print') as mock_print, \
         mock.patch('src.rabbitmq.logger', create=True) as mock_logger:
        
        # Configurando os mocks
        mock_get_var.side_effect = ["user", "pass", "host", "5672"]
        mock_connection.side_effect = pika.exceptions.AMQPConnectionError("Connection error")
        
        # Chamando a função
        result = check_rabbitmq_connection()
        
        # Verificando se a função retornou False
        assert result is False
        
        # Verificando se o logger foi chamado
        mock_logger.error.assert_called_once()

@pytest.mark.unit
def test_send_rabbitmq_success(mock_rabbitmq_connection):
    """Testa a função send_rabbitmq quando o envio é bem-sucedido."""
    connection, channel = mock_rabbitmq_connection
    
    # Chamando a função
    result = send_rabbitmq(
        caminho="exchange",
        topico="queue",
        chave="routing_key",
        payload="test message"
    )
    
    # Verificando se a função retornou True
    assert result is True
    
    # Verificando se os métodos foram chamados corretamente
    channel.queue_declare.assert_called_once_with(queue="queue")
    channel.basic_publish.assert_called_once_with(
        exchange="exchange",
        routing_key="routing_key",
        body="test message"
    )
    connection.close.assert_called_once()

@pytest.mark.unit
def test_send_rabbitmq_failure():
    """Testa a função send_rabbitmq quando ocorre um erro de conexão."""
    # Mockando a conexão para lançar um erro
    with mock.patch('pika.BlockingConnection') as mock_connection, \
         mock.patch('builtins.print') as mock_print, \
         mock.patch('src.rabbitmq.logger', create=True) as mock_logger:
        
        mock_connection.side_effect = pika.exceptions.AMQPConnectionError("Connection error")
        
        # Chamando a função
        result = send_rabbitmq(
            caminho="exchange",
            topico="queue",
            chave="routing_key",
            payload="test message"
        )
        
        # Verificando se a função retornou False
        assert result is False
        
        # Verificando se o logger foi chamado
        mock_logger.error.assert_called_once()