import pytest
import os
import time
import json
from unittest import mock
import pycurl
from io import BytesIO

# Importando as funções do módulo a ser testado
from src.scadalts import (
    get_cookie_from_url,
    get_with_cookie,
    get_valid_cookie,
    get_json_data,
    auth_ScadaLTS,
    send_data_to_scada,
    cookie_cache
)

@pytest.fixture
def mock_env_variables():
    """Fixture para configurar as variáveis de ambiente corretas para os testes."""
    with mock.patch.dict(os.environ, {
        "username": "admin",
        "password": "admin",
        "URL_BASE": "http://localhost:8080"
    }):
        yield

@pytest.fixture
def reset_cookie_cache():
    """Fixture para resetar o cache de cookie entre os testes."""
    global cookie_cache
    original_cache = cookie_cache.copy()
    cookie_cache = {"value": None, "expires_at": 0}
    yield
    cookie_cache = original_cache

class MockBuffer:
    """Classe para simular um buffer que captura dados escritos."""
    def __init__(self, data=None):
        self.buffer = BytesIO()
        if data:
            self.buffer.write(data)
            self.buffer.seek(0)
    
    def write(self, data):
        self.buffer.write(data)
        return len(data)
    
    def getvalue(self):
        current_pos = self.buffer.tell()
        self.buffer.seek(0)
        value = self.buffer.read()
        self.buffer.seek(current_pos)
        return value

@pytest.fixture
def mock_curl():
    """Fixture para mockar a instância do pycurl.Curl."""
    with mock.patch('pycurl.Curl') as mock_curl_class:
        mock_curl = mock.MagicMock()
        mock_curl_class.return_value = mock_curl
        yield mock_curl

def setup_mock_curl_response(mock_curl, status_code, headers=None, body=None):
    """Configura a resposta simulada do pycurl.Curl."""
    if headers is None:
        headers = b'HTTP/1.1 200 OK\r\n\r\n'
    if body is None:
        body = b''
    
    header_buffer = MockBuffer(headers)
    body_buffer = MockBuffer(body)
    
    def mock_setopt(option, callback):
        if option == pycurl.WRITEFUNCTION:
            mock_curl.write_callback = callback
        elif option == pycurl.HEADERFUNCTION:
            mock_curl.header_callback = callback
        mock_curl.options[option] = callback
    
    mock_curl.options = {}
    mock_curl.setopt.side_effect = mock_setopt
    
    def mock_perform():
        mock_curl.header_callback(header_buffer.getvalue())
        mock_curl.write_callback(body_buffer.getvalue())
    
    mock_curl.perform.side_effect = mock_perform
    mock_curl.getinfo.return_value = status_code

@pytest.mark.integration
def test_get_cookie_from_url_success(mock_env_variables, reset_cookie_cache, mock_curl):
    """Testa a obtenção de cookie com sucesso usando um mock mais preciso."""
    setup_mock_curl_response(
        mock_curl,
        status_code=200,
        headers=b'HTTP/1.1 200 OK\r\nSet-Cookie: JSESSIONID=abc123; Path=/; HttpOnly\r\n\r\n'
    )
    
    result = get_cookie_from_url("http://localhost:8080/Scada-LTS/api/auth/admin/admin")
    
    assert result == "JSESSIONID=abc123"
    assert cookie_cache["value"] == "JSESSIONID=abc123"
    assert cookie_cache["expires_at"] > time.time()
    
    mock_curl.setopt.assert_any_call(pycurl.URL, "http://localhost:8080/Scada-LTS/api/auth/admin/admin")
    mock_curl.perform.assert_called_once()
    mock_curl.close.assert_called_once()

@pytest.mark.integration
def test_get_cookie_from_url_failure(mock_env_variables, reset_cookie_cache, mock_curl):
    """Testa a falha na obtenção de cookie."""
    setup_mock_curl_response(
        mock_curl,
        status_code=401,
        headers=b'HTTP/1.1 401 Unauthorized\r\n\r\n'
    )
    
    result = get_cookie_from_url("http://localhost:8080/Scada-LTS/api/auth/admin/admin")
    
    assert result is None
    assert cookie_cache["value"] is None
    
    mock_curl.perform.assert_called_once()
    mock_curl.close.assert_called_once()

@pytest.mark.integration
def test_get_with_cookie_success(mock_env_variables, mock_curl):
    """Testa a função get_with_cookie com sucesso."""
    response_json = {
        "value": "42.5",
        "ts": 1613035200000,
        "name": "DP_123",
        "type": "NumericValue"
    }
    response_bytes = json.dumps(response_json).encode('utf-8')
    
    setup_mock_curl_response(
        mock_curl,
        status_code=200,
        body=response_bytes
    )
    
    result = get_with_cookie(
        "http://localhost:8080/Scada-LTS/api/point_value/getValue/DP_123",
        "JSESSIONID=abc123",
        "DP_123"
    )
    
    assert result == response_json
    
    mock_curl.setopt.assert_any_call(pycurl.URL, "http://localhost:8080/Scada-LTS/api/point_value/getValue/DP_123")
    mock_curl.setopt.assert_any_call(pycurl.COOKIE, "JSESSIONID=abc123")
    mock_curl.perform.assert_called_once()
    mock_curl.close.assert_called_once()

@pytest.mark.integration
def test_get_with_cookie_error(mock_env_variables, mock_curl):
    """Testa a função get_with_cookie quando o status HTTP não é 200."""
    setup_mock_curl_response(
        mock_curl,
        status_code=404
    )
    
    result = get_with_cookie(
        "http://localhost:8080/Scada-LTS/api/point_value/getValue/DP_123",
        "JSESSIONID=abc123",
        "DP_123"
    )
    
    assert result is None
    
    mock_curl.perform.assert_called_once()
    mock_curl.close.assert_called_once()

@pytest.mark.integration
def test_get_valid_cookie_cached(mock_env_variables, reset_cookie_cache):
    """Testa o uso de um cookie em cache ainda válido."""
    global cookie_cache
    cookie_cache["value"] = "JSESSIONID=valid123"
    cookie_cache["expires_at"] = time.time() + 3600
    
    result = get_valid_cookie()
    
    assert result == "JSESSIONID=valid123"

@pytest.mark.integration
def test_get_valid_cookie_expired(mock_env_variables, reset_cookie_cache, mock_curl):
    """Testa a renovação de um cookie expirado."""
    global cookie_cache
    cookie_cache["value"] = "JSESSIONID=expired123"
    cookie_cache["expires_at"] = time.time() - 1
    
    setup_mock_curl_response(
        mock_curl,
        status_code=200,
        headers=b'HTTP/1.1 200 OK\r\nSet-Cookie: JSESSIONID=new123; Path=/; HttpOnly\r\n\r\n'
    )
    
    result = get_valid_cookie()
    
    assert result == "JSESSIONID=new123"
    mock_curl.perform.assert_called_once()
    mock_curl.close.assert_called_once()

@pytest.mark.integration
def test_get_json_data_with_valid_cookie(mock_env_variables, mock_curl):
    """Testa a obtenção de dados JSON com um cookie válido."""
    response_data = {
        "value": "42.5",
        "ts": 1613035200000,
        "name": "DP_123",
        "type": "NumericValue"
    }
    
    with mock.patch('src.scada.get_valid_cookie') as mock_get_cookie, \
         mock.patch('src.scada.get_with_cookie') as mock_get_with_cookie:
        
        mock_get_cookie.return_value = "JSESSIONID=valid123"
        mock_get_with_cookie.return_value = response_data
        
        result = get_json_data("DP_123")
        
        assert result == response_data
        mock_get_cookie.assert_called_once()
        mock_get_with_cookie.assert_called_once_with(
            "http://localhost:8080/Scada-LTS/api/point_value/getValue/DP_123",
            "JSESSIONID=valid123",
            "DP_123"
        )

@pytest.mark.integration
def test_get_json_data_with_invalid_cookie(mock_env_variables):
    """Testa a falha na obtenção de dados JSON com um cookie inválido."""
    with mock.patch('src.scada.get_valid_cookie') as mock_get_cookie:
        mock_get_cookie.return_value = None
        
        result = get_json_data("DP_123")
        
        assert result is None
        mock_get_cookie.assert_called_once()

@pytest.mark.integration
def test_auth_ScadaLTS_success(mock_env_variables, mock_curl):
    """Testa a autenticação bem-sucedida no SCADA-LTS."""
    setup_mock_curl_response(
        mock_curl,
        status_code=200,
        body=b"<html><body>Login successful</body></html>"
    )
    
    with mock.patch('builtins.print') as mock_print:
        auth_ScadaLTS()
        
        mock_curl.setopt.assert_any_call(pycurl.URL, "http://localhost:8080/Scada-LTS/login.htm")
        mock_curl.setopt.assert_any_call(pycurl.POST, 1)
        mock_curl.setopt.assert_any_call(pycurl.POSTFIELDS, "username=admin&password=admin&submit=Login")
        mock_curl.setopt.assert_any_call(pycurl.COOKIEJAR, 'cookies')
        mock_curl.perform.assert_called_once()
        mock_curl.close.assert_called_once()
        mock_print.assert_called_with("AUTH SCADA")

@pytest.mark.integration
def test_auth_ScadaLTS_missing_credentials():
    """Testa a falha na autenticação por falta de credenciais."""
    with mock.patch.dict(os.environ, {"username": "", "password": ""}), \
         mock.patch('builtins.print') as mock_print, \
         mock.patch('src.scada.logger') as mock_logger:
        
        auth_ScadaLTS()
        
        mock_print.assert_called_with("Erro: Credenciais de acesso ao SCADA-LTS não encontradas no arquivo .env")
        mock_logger.error.assert_called_with("Erro: Credenciais de acesso ao SCADA-LTS não encontradas no arquivo .env")

@pytest.mark.integration
def test_send_data_to_scada(mock_env_variables, mock_curl):
    """Testa o envio de dados para o SCADA-LTS."""
    test_data = (
        "callCount=1\n"
        "page=/Scada-LTS/emport.htm\n"
        "httpSessionId=123\n"
        "scriptSessionId=456\n"
        "c0-scriptName=EmportDwr\n"
        "c0-methodName=importData\n"
        "c0-id=0\n"
        "c0-param0=string:<dataPoint xid='DP_TEST' type='NUMERIC'></dataPoint>"
    )
    
    setup_mock_curl_response(
        mock_curl,
        status_code=200,
        body=b"//OK"
    )
    
    with mock.patch('builtins.print') as mock_print:
        send_data_to_scada(test_data)
        
        mock_curl.setopt.assert_any_call(
            pycurl.URL, 
            "http://localhost:8080/Scada-LTS/dwr/call/plaincall/EmportDwr.importData.dwr"
        )
        mock_curl.setopt.assert_any_call(pycurl.POST, 1)
        mock_curl.setopt.assert_any_call(pycurl.POSTFIELDS, test_data)
        mock_curl.setopt.assert_any_call(pycurl.COOKIEFILE, 'cookies')
        mock_curl.perform.assert_called_once()
        mock_curl.close.assert_called_once()
        mock_print.assert_called_with("send_data_to_scada", test_data)

@pytest.mark.integration
def test_send_data_to_scada_error(mock_env_variables, mock_curl):
    """Testa o erro ao enviar dados para o SCADA-LTS."""
    mock_curl.perform.side_effect = pycurl.error("Connection error")
    
    test_data = "test_data"
    
    with mock.patch('src.scada.logger') as mock_logger:
        send_data_to_scada(test_data)
        
        mock_logger.error.assert_called()