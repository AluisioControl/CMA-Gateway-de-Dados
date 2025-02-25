import pytest
import os
import sys
import time
import json
import threading
import socket
from unittest.mock import patch, MagicMock
from datetime import datetime

# Adiciona o diretório raiz ao path para importação de módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importações do módulo principal
from models import *
from rabbitmq import *
from scadalts import *
from logger import *

# Importando as funções do script principal
from main import (
    get_network_info,
    fetch_name_value_pairs,
    process_json_datapoints,
    send_data_to_mqtt,
    get_periods_eqp,
    send_to_mqtt_broker,
    convert_to_seconds,
    get_xid_sensor_from_eqp_modbus,
    get_xid_sensor_from_eqp_dnp3,
    start_main_threads
)

# Configurações para testes
@pytest.fixture
def setup_environment():
    """Configura o ambiente para os testes"""
    # Backup das variáveis globais originais
    original_status = {
        'STATUS_CMA': getattr(sys.modules['main'], 'STATUS_CMA'),
        'STATUS_SCADA': getattr(sys.modules['main'], 'STATUS_SCADA'),
        'service_status': getattr(sys.modules['main'], 'service_status').copy()
    }
    
    # Mock das variáveis de ambiente
    os.environ['HEALTH_CHECK_INTERVAL'] = '5'
    os.environ['STATUS_SERVER_CHECK_INTERVAL'] = '5'
    
    yield
    
    # Restaura as variáveis globais após o teste
    sys.modules['main'].STATUS_CMA = original_status['STATUS_CMA']
    sys.modules['main'].STATUS_SCADA = original_status['STATUS_SCADA']
    sys.modules['main'].service_status = original_status['service_status']

# Mocks para banco de dados
class MockSession:
    def __init__(self, mock_data=None):
        self.mock_data = mock_data or {}
        
    def execute(self, query):
        return MockQueryResult(self.mock_data)
    
    def commit(self):
        pass
    
    def rollback(self):
        pass
    
    def close(self):
        pass
    
    def scalars(self):
        return self

class MockQueryResult:
    def __init__(self, mock_data):
        self.mock_data = mock_data
        
    def fetchall(self):
        return self.mock_data.get('fetchall', [])
    
    def first(self):
        return self.mock_data.get('first')
    
    def all(self):
        return self.mock_data.get('all', [])

# Testes End-to-End
@pytest.mark.e2e
class TestEndToEnd:
    
    @patch('socket.create_connection')
    @patch('models.SessionLocal')
    @patch('rabbitmq.check_rabbitmq_connection')
    @patch('rabbitmq.send_rabbitmq')
    @patch('scadalts.get_json_data')
    def test_full_data_flow(self, mock_get_json_data, mock_send_rabbitmq, 
                           mock_check_rabbitmq, mock_session, mock_socket, 
                           setup_environment):
        """
        Testa o fluxo completo de dados desde a coleta até o envio para o MQTT
        """
        # Mock das conexões de rede
        mock_socket.return_value = MagicMock()
        
        # Mock das respostas do banco de dados
        mock_session_instance = MockSession({
            'fetchall': [('equip_test', 10, 'SECONDS')],
            'first': MagicMock(
                xid_sensor='XIDSENS',
                xid_equip='XIDEQP',
                xid_gateway='Gateway_01',
                subestacao='For',
                regional='Messejana',
                host='127.0.0.1',
                status='ONLINE',
                fabricante='Fabricante Test',
                marca='Marca Test',
                modelo='Modelo Test',
                type='DNP3_IP',
                sap_id='SAP123',
                enabled=True,
                index=1,
                offset=1,
                nome='Sensor Test',
                tipo='ANALOG',
                classificacao='Classe Test'
            ),
            'all': [MagicMock(
                id=1, 
                content_data='{"test": "data"}', 
                sended=False
            )]
        })
        mock_session.return_value = mock_session_instance
        
        # Mock das respostas do RabbitMQ
        mock_check_rabbitmq.return_value = True
        mock_send_rabbitmq.return_value = True
        
        # Mock da resposta do Scada-LTS
        mock_get_json_data.return_value = {"value": 42.5}
        
        # Configura o status dos servidores
        sys.modules['main'].STATUS_CMA = "ONLINE"
        sys.modules['main'].STATUS_SCADA = "ONLINE"
        sys.modules['main'].service_status["is_running"] = True
        
        # Teste 1: Verificar conversão de tempo
        assert convert_to_seconds(10, 'SECONDS') == 10
        assert convert_to_seconds(1, 'MINUTES') == 60
        assert convert_to_seconds(1, 'HOURS') == 3600
        assert convert_to_seconds(1000, 'MILLISECONDS') == 1
        
        # Teste 2: Verificar processamento de JSON do datapoint
        with patch('main.parse_json_response', return_value=24):
            with patch('main.fetch_name_value_pairs', return_value={"tag1": "value1"}):
                result = process_json_datapoints('XIDSENS', 'DNP3')
                # Verifica se o resultado é um JSON válido
                parsed = json.loads(result)
                assert parsed['dataPoints'][0]['Sensor'] == 'XIDSENS'
                assert parsed['dataPoints'][0]['Valor'] == 24
                assert parsed['data_gateway'][0]['ID'] == 'Gateway_01'
        
        # Teste 3: Verificar envio para MQTT
        with patch('main.process_json_datapoints', return_value='{"test": "data"}'):
            send_to_mqtt_broker('XIDSENS', 'DNP3')
            mock_send_rabbitmq.assert_called_once()
            
    @patch('psutil.net_if_addrs')
    @patch('psutil.net_if_stats')
    def test_network_info(self, mock_stats, mock_addrs, setup_environment):
        """
        Testa a função que obtém informações de rede
        """
        # Configura os mocks para simular uma interface de rede ativa
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = '192.168.1.100'
        mock_addr.netmask = '255.255.255.0'
        
        mock_addrs.return_value = {
            'eth0': [mock_addr]
        }
        
        mock_stats.return_value = {
            'eth0': MagicMock(isup=True, speed=1000)
        }
        
        # Executa a função
        result = get_network_info()
        
        # Verifica os resultados
        assert result is not None
        assert result['Interface'] == 'eth0'
        assert result['IP'] == '192.168.1.100'
        assert result['Status'] == 'Ativo'
        assert result['Velocidade'] == '1000 Mbps'
        
    @patch('models.SessionLocal')
    def test_db_queries(self, mock_session, setup_environment):
        """
        Testa as funções que fazem consultas ao banco de dados
        """
        # Configura o mock para simular respostas do banco
        mock_session_instance = MockSession({
            'first': 'XIDSENS',
            'fetchall': [('nome1', 'valor1'), ('nome2', 'valor2')]
        })
        mock_session.return_value = mock_session_instance
        
        # Teste 1: get_xid_sensor_from_eqp_modbus
        result = get_xid_sensor_from_eqp_modbus('equip_test')
        assert result == 'XIDSENS'
        
        # Teste 2: get_xid_sensor_from_eqp_dnp3
        result = get_xid_sensor_from_eqp_dnp3('equip_test')
        assert result == 'XIDSENS'
        
        # Teste 3: fetch_name_value_pairs
        with patch('main.table_class.__table__.c', {'nome': None, 'valor': None}):
            with patch('sqlalchemy.select', return_value=MagicMock()):
                result = fetch_name_value_pairs(MagicMock(), 'field_name', 'value')
                assert isinstance(result, dict)
    
    @patch('threading.Thread')
    def test_start_main_threads(self, mock_thread, setup_environment):
        """
        Testa a inicialização das threads principais
        """
        # Configura o mock para a criação de threads
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Limpa o dicionário de threads ativas
        sys.modules['main'].active_threads = {}
        
        # Executa a função
        start_main_threads()
        
        # Verifica se as threads foram criadas
        assert 'process_cma' in sys.modules['main'].active_threads
        assert 'process_scada' in sys.modules['main'].active_threads
        assert 'health_checker' in sys.modules['main'].active_threads
        assert 'modbus_thread' in sys.modules['main'].active_threads
        assert 'dnp3_thread' in sys.modules['main'].active_threads
        
        # Verifica se o método start foi chamado para cada thread
        assert mock_thread_instance.start.call_count == 5

    @patch('socket.create_connection')
    def test_server_status_check(self, mock_socket, setup_environment):
        """
        Testa a verificação de status dos servidores
        """
        # Configurar o comportamento do mock para simular servidor online/offline
        def side_effect(*args, **kwargs):
            host, port = args[0]
            if port == 5000:  # CMA
                return MagicMock()
            else:  # SCADA
                raise ConnectionRefusedError()
                
        mock_socket.side_effect = side_effect
        
        # Executa a função (em uma thread separada para não bloquear)
        thread = threading.Thread(
            target=sys.modules['main'].thr_check_server_online,
            args=("127.0.0.1", 5000, "CMA"),
            daemon=True
        )
        thread.start()
        
        # Dá tempo para a thread executar
        time.sleep(2)
        
        # Verifica o status do CMA
        assert sys.modules['main'].STATUS_CMA == "ONLINE"
        
        # Executa a função para o SCADA
        thread = threading.Thread(
            target=sys.modules['main'].thr_check_server_online,
            args=("127.0.0.1", 8080, "SCADA-LTS"),
            daemon=True
        )
        thread.start()
        
        # Dá tempo para a thread executar
        time.sleep(2)
        
        # Verifica o status do SCADA
        assert sys.modules['main'].STATUS_SCADA == "OFFLINE"