###############################################################
# functions.py
# ------------------------------------------------------------
# Arquivo com as funções auxiliares do Middleware
# Author: Aluisio Cavalcante <aluisio@controlengenharia.eng.br>
# novembro de 2024
# TODOS OS DIREITOS RESERVADOS A CONTROL ENGENHARIA
# #############################################################
from datetime import datetime
import threading 
import socket
from io import BytesIO
import pycurl
import json
import os
import psutil
from models import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, Column, Integer, String, Float, select
import logging
import logging.handlers
import signal
import time
import sys
import multiprocessing
from rabbitmq import *
from dotenv import load_dotenv

# Carregando as variáveis de ambiente do arquivo .env
load_dotenv()

# Localização do arquivo de log 
LOG_LINUX   = os.getenv("LOG_LINUX")
LOG_WINDOWS = os.getenv("LOG_WINDOWS")

# Configuração do logging
log_formatter = logging.Formatter('[MIDDLEWARE] %(asctime)s - %(levelname)s - %(funcName)s - %(message)s')

# Para salvar no arquivo em vez de usar SysLogHandler
log_handler = logging.FileHandler(LOG_LINUX)
log_handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.addHandler(log_handler)
logger.setLevel(logging.WARNING)  # Configura o nível mínimo para WARNING

# Teste de log
# logger.error("TESTE DE ERRO")
# logger.warning("TESTE DE WARNING")
# logger.error(f"Erro ao criar item: {e}")

# -------------------------------------------------------------
# Variáveis da aplicação
# -------------------------------------------------------------
stop_event = threading.Event()
STATUS_CMA   = ""
STATUS_SCADA = ""
service_status = {"is_running": False}
# Variável global para controle das threads
active_threads = {}

# -------------------------------------------------------------
# Funções que retorna o estado atual dos servidores CMA e SCADA
# "ONLINE" ou "OFFLINE" (API - DELETAR DEPOIS)
# -------------------------------------------------------------
def get_server_status_cma():
    return STATUS_CMA

# Retorna o estado atual do servidor SCADA
def get_server_status_scada():
    return STATUS_SCADA

# -------------------------------------------------------------
# Função que retorna informações da placa de rede
# -------------------------------------------------------------
def get_network_info():
    net_info = psutil.net_if_addrs()
    net_status = psutil.net_if_stats()

    for interface, stats in net_status.items():
        if stats.isup and stats.speed > 0:  # Verifica se a interface está ativa e tem velocidade > 0
            for addr in net_info.get(interface, []):
                if addr.family == socket.AF_INET:  # Apenas IPv4
                    return {
                        "Interface": interface,
                        "IP": addr.address,
                        "Máscara": addr.netmask,
                        "Status": "Ativo",
                        "Velocidade": f"{stats.speed} Mbps"
                    }

    return None  # Nenhuma interface de rede com cabo conectado encontrada

# -------------------------------------------------------------
# Função que retorna informações do sistema (HEALTH CHECK)
# -------------------------------------------------------------
def thr_get_system_info():
    while True:
        # Memória RAM
        ram = psutil.virtual_memory()
        total_ram = ram.total / (1024 ** 3)  # Convertendo para GB
        used_ram = ram.used / (1024 ** 3)
        ram_percent = ram.percent

        # Processador
        cpu_usage = psutil.cpu_percent(interval=1)

        # Espaço do HD
        disk = psutil.disk_usage('/')
        total_disk = disk.total / (1024 ** 3)
        used_disk = disk.used / (1024 ** 3)
        free_disk = disk.free / (1024 ** 3)
        disk_percent = disk.percent

        # Tempo de funcionamento (uptime)
        uptime_seconds = time.time() - psutil.boot_time()
        uptime_hours = uptime_seconds // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60

        # Informações da rede
        network_data = get_network_info()

        # Exibir informações formatadas
        print("\n===== INFORMAÇÕES DO SISTEMA =====")
        print(
            f"Memória RAM: {used_ram:.2f} GB / {total_ram:.2f} GB ({ram_percent}%)")
        print(f"Uso do Processador: {cpu_usage}%")
        print(
            f"Espaço do HD: {used_disk:.2f} GB usados / {total_disk:.2f} GB ({disk_percent}%)")
        print(
            f"Tempo de Funcionamento: {int(uptime_hours)}h {int(uptime_minutes)}min")

        if network_data:
            print("\n===== INFORMAÇÕES DA REDE =====")
            print(f"Interface: {network_data['Interface']}")
            print(f"  IP: {network_data['IP']}")
            print(f"  Máscara: {network_data['Máscara']}")
            print(f"  Status: {network_data['Status']}")
            print(f"  Velocidade: {network_data['Velocidade']}\n")
        else:
            print("\n===== INFORMAÇÕES DA REDE =====")
            print("Nenhuma conexão de rede com cabo detectada.\n")
        time.sleep(15)


# -------------------------------------------------------------
# Rotina de autenticação no SCADA-LTS
# -------------------------------------------------------------
def auth_ScadaLTS():
    username = os.getenv("username")
    password = os.getenv("password")

    if not username or not password:
        print("Erro: Credenciais de acesso ao SCADA-LTS não encontradas no arquivo .env")
        logger.error(
            "Erro: Credenciais de acesso ao SCADA-LTS não encontradas no arquivo .env")
        return
    try:
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, 'http://localhost:8080/Scada-LTS/login.htm')
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS,
                 f'username={username}&password={password}&submit=Login')
        c.setopt(c.COOKIEFILE, '')
        c.setopt(c.COOKIEJAR, 'cookies')
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()
        response = buffer.getvalue().decode('utf-8')
        # print(response)
        print("AUTH SCADA")
    except ConnectionError as e:
        logger.error(f"Erro ao tentar autenticar no SCADA-LTS: {e}")


# -------------------------------------------------------------
# Função para envio de dados para o SCADA-LTS
# -------------------------------------------------------------
def send_data_to_scada(raw_data):
    try:
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(
            c.URL, 'http://localhost:8080/Scada-LTS/dwr/call/plaincall/EmportDwr.importData.dwr')
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS, raw_data)
        c.setopt(c.COOKIEFILE, 'cookies')
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()
        response = buffer.getvalue().decode('utf-8')
        #print(response)
        #print("send_data_to_scada", raw_data)
    except ConnectionError as e:
        logger.error(f"Erro ao enviar dados ao SCADA-LTS: {e}")

# -------------------------------------------------------------
# Rotina de autenticação de usuário no Scada-LTS e
# obter cookie para sessão de acesso à API do Scada-LTS
# -------------------------------------------------------------

def get_cookie_from_url(url):
    buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.URL, url)
    curl.setopt(curl.WRITEFUNCTION, buffer.write)
    curl.setopt(curl.COOKIEFILE, '')  # Habilita cookies
    curl.setopt(curl.HEADER, True)    # Inclui cabeçalhos na resposta

    try:
        curl.perform()
        headers = buffer.getvalue().decode('utf-8').splitlines()
        cookies = [line for line in headers if line.startswith('Set-Cookie')]
        if cookies:
            # Retorna o primeiro cookie encontrado, caso haja múltiplos
            cookie = cookies[0].split(":", 1)[1].strip()
            return cookie
        return None
    except ConnectionError as e:
        logger.error(f"Erro ao obter o cookie para sessão de acesso: {e}")
    finally:
        curl.close()


# -------------------------------------------------------------
# Função para fazer um GET na URL fornecida usando o cookie
# e retorna o JSON da resposta.
# -------------------------------------------------------------
def get_with_cookie(url, cookie):
    if not url or not isinstance(url, str):
        logger.error("URL inválida fornecida.")
        return None

    if not cookie or not isinstance(cookie, str):
        logger.error("Cookie inválido fornecido.")
        return None

    buffer = BytesIO()
    curl = pycurl.Curl()

    try:
        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEFUNCTION, buffer.write)
        curl.setopt(curl.COOKIE, cookie)

        curl.perform()
        status_code = curl.getinfo(pycurl.RESPONSE_CODE)

        if status_code != 200:
            logger.error(f"Erro HTTP {status_code} ao acessar a URL: {url}")
            return None

        response = buffer.getvalue().decode('utf-8')
        return json.loads(response)

    except pycurl.error as e:
        logger.error(f"Erro de conexão com PyCurl: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar a resposta JSON: {e}")
        return None
    finally:
        buffer.close()
        curl.close()


# -------------------------------------------------------------
# Função para fazer o parse de um JSON e retorna o valor
# associado a uma chave fornecida pelo usuário.
#
#   :param json_response: O JSON retornado da função `get_with_cookie`.
#   :param key: A chave cujo valor o usuário deseja extrair.
#   :return: O valor associado à chave, ou uma mensagem de erro
#    se a chave não existir.
# -------------------------------------------------------------
def parse_json_response(json_response, key):
    #print("parse_json_response=", json_response, key)
    try:
        if key in json_response:
            return json_response[key]
        else:
            return f"Chave '{key}' não encontrada no JSON."
    except Exception as e:
        logger.error(f"Erro ao processar o JSON: {e}")
        return f"Erro ao processar o JSON: {e}"




# -------------------------------------------------------------
# Rotina de captura de todos os xid_equip e xid_sensor
# idênticos encontrados nas tabelas tags_eqp e tags_sensor
# -------------------------------------------------------------

def get_tags_from_table(table_class, field_name, xid):

    session = SessionLocal()
    try:
        query = select(table_class.__table__.c.nome).where(
            table_class.__table__.c[field_name] == xid)
        items = session.execute(query).fetchall()
        valid_xid_sensors = [item[0] for item in items if item[0]]

        if not valid_xid_sensors:
            print("Nenhuma tag correspondente da tabela {}".format(
                table_class.__table__), "foi encontrada!")
            valid_xid_sensors = ["null"]

        return valid_xid_sensors
    except Exception as e:
        logger.error(
            f"Erro ao capturar os xid_equip e xid_sensor idênticos encontrados nas tabelas tags_eqp e tags_sensor: {e}")

    finally:
        session.close()


# -----------------------------------------------------------------------
# Busca pares de valores das colunas 'nome' e 'valor' de uma tabela
# e retorna uma estrutura de dados no formato [{"nome": "valor"}, ...].
#
#    Args:
#       session (Session): Sessão do banco de dados SQLAlchemy.
#       table_class: Classe ORM que representa a tabela.
#       field_name (str): Nome da coluna usada como filtro.
#       xid: Valor usado na condição WHERE.
#
#    Returns:
#       list[dict]: Lista de dicionários no formato {"nome": "valor"}.
# ----------------------------------------------------------------------
def fetch_name_value_pairs(table_class, field_name, xid):

    # Montar a consulta para buscar 'nome' e 'valor'
    session = SessionLocal()
    try:
        query = (
            select(table_class.__table__.c.nome, table_class.__table__.c.valor)
            .where(table_class.__table__.c[field_name] == xid)
        )

        # Executar a consulta e obter todos os resultados
        items = session.execute(query).fetchall()

        # Montar a estrutura de saída como lista de dicionários
        result = {item[0]: item[1] for item in items if item[0] and item[1]}

        return result
    except Exception as e:
        logger.error(
            f"Erro ao buscar pares de valores das colunas 'nome' e 'valor' de uma tabela: {e}")
    finally:
        session.close()



# -------------------------------------------------------------
# Função para geração de um Payload (arquivo JSON) de múltiplas
# Tabelas do banco de dados
# -------------------------------------------------------------
def process_json_datapoints(xid_sensor_param: str, protocol: str):
    session = SessionLocal()
    #print(f"RECEBIDO XID_SENSOR {xid_sensor_param} E PROTOCOLO {protocol}")
    try:
        no_data = "sem dados"
        if protocol == "DNP3":
            #print("Entrou no DNP3 com xid_sensor_param=", xid_sensor_param)
            # Criando a consulta síncrona
            query_datapoints = select(datapoints_dnp3).where(
                datapoints_dnp3.xid_sensor == xid_sensor_param)
            result_datapoints = session.execute(
                query_datapoints).scalars().first()
            # xid_eqp = result_datapoints.xid_equip
            xid_eqp = no_data if not result_datapoints else result_datapoints.xid_equip
            
            query_datasources = select(datasource_dnp3).where(
                datasource_dnp3.xid_equip == xid_eqp)
            result_datasources = session.execute(
                query_datasources).scalars().first()
            # xid_gtw = result_datasources.xid_gateway
            xid_gtw = no_data if not result_datasources else result_datasources.xid_gateway
         
            query_cma_gateway = select(cma_gateway).where(
                cma_gateway.xid_gateway == xid_gtw)
            query_datasource_dnp3 = select(datasource_dnp3).where(
                datasource_dnp3.xid_equip == xid_eqp)
            query_eqp_tags = select(eqp_tags).where(
                eqp_tags.xid_equip == xid_eqp)
            query_dp_tags = select(dp_tags).where(
                dp_tags.xid_sensor == xid_sensor_param)

            # Executando a consulta
            result_cma_gateway = session.execute(
                query_cma_gateway).scalars().first()
            result_datasource_dnp3 = session.execute(
                query_datasource_dnp3).scalars().first()
            result_eqp_tags = session.execute(query_eqp_tags).scalars().first()
            result_dp_tags = session.execute(query_dp_tags).scalars().first()

            # DATA GATEWAY
            gateway_id = no_data if not result_cma_gateway else result_cma_gateway.xid_gateway
            subestacao = no_data if not result_cma_gateway else result_cma_gateway.subestacao
            regional = no_data if not result_cma_gateway else result_cma_gateway.regional
            host_gateway = no_data if not result_cma_gateway else result_cma_gateway.host
            status_gateway = no_data if not result_cma_gateway else result_cma_gateway.status

            # DATASOURCE DNP 3
            xid_equip = no_data if not result_datasource_dnp3 else result_datasource_dnp3.xid_equip
            fabricante = no_data if not result_datasource_dnp3 else result_datasource_dnp3.fabricante
            marca = no_data if not result_datasource_dnp3 else result_datasource_dnp3.marca
            modelo = no_data if not result_datasource_dnp3 else result_datasource_dnp3.modelo
            type_ = no_data if not result_datasource_dnp3 else result_datasource_dnp3.type
            sap_id = no_data if not result_datasource_dnp3 else result_datasource_dnp3.sap_id
            status_datasource = no_data if not result_datasource_dnp3 else result_datasource_dnp3.enabled
            host_datasource = no_data if not result_datasource_dnp3 else result_datasource_dnp3.host
            #tags_equipamento = no_data if not result_eqp_tags else result_eqp_tags.valor

            # DATAPOINTS DNP3 IP
            xid_sensor = no_data if not result_datapoints else result_datapoints.xid_sensor
            # value = no_data if not result_datapoints else result_datapoints.value
            registrador = no_data if not result_datapoints else result_datapoints.index
            nome = no_data if not result_datapoints else result_datapoints.nome
            tipo = no_data if not result_datapoints else result_datapoints.tipo
            classificacao = no_data if not result_datapoints else result_datapoints.classificacao
            status_datapoints = no_data if not result_datapoints else result_datapoints.enabled
            #tag_sensor = no_data if not result_dp_tags else result_dp_tags.xid_sensor

        elif protocol == "MODBUS":
            
           # Criando a consulta síncrona
            query_datapoints = select(datapoints_modbus_ip).where(
                datapoints_modbus_ip.xid_sensor == xid_sensor_param)
            result_datapoints = session.execute(
                query_datapoints).scalars().first()
            # xid_eqp = result_datapoints.xid_equip
            xid_eqp = no_data if not result_datapoints else result_datapoints.xid_equip

            query_datasources = select(datasource_modbus_ip).where(
                datasource_modbus_ip.xid_equip == xid_eqp)
            result_datasources = session.execute(
                query_datasources).scalars().first()
            # xid_gtw = result_datasources.xid_gateway
            xid_gtw = no_data if not result_datasources else result_datasources.xid_gateway

            query_cma_gateway = select(cma_gateway).where(
                cma_gateway.xid_gateway == xid_gtw)
            query_datasource_modbus_ip = select(datasource_modbus_ip).where(
                datasource_modbus_ip.xid_equip == xid_eqp)
            query_eqp_tags = select(eqp_tags).where(
                eqp_tags.xid_equip == xid_eqp)
            query_dp_tags = select(dp_tags).where(
                dp_tags.xid_sensor == xid_sensor_param)

            # Executando a consulta
            result_cma_gateway = session.execute(
                query_cma_gateway).scalars().first()
            result_datasource_modbus_ip = session.execute(
                query_datasource_modbus_ip).scalars().first()
            result_eqp_tags = session.execute(query_eqp_tags).scalars().first()
            result_dp_tags = session.execute(query_dp_tags).scalars().first()

            # DATA GATEWAY
            gateway_id = no_data if not result_cma_gateway else result_cma_gateway.xid_gateway
            subestacao = no_data if not result_cma_gateway else result_cma_gateway.subestacao
            regional = no_data if not result_cma_gateway else result_cma_gateway.regional
            host_gateway = no_data if not result_cma_gateway else result_cma_gateway.host
            status_gateway = no_data if not result_cma_gateway else result_cma_gateway.status

            # DATASOURCE MODBUS IP
            xid_equip = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.xid_equip
            fabricante = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.fabricante
            marca = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.marca
            modelo = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.modelo
            type_ = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.type
            sap_id = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.sap_id
            status_datasource = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.enabled
            host_datasource = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.host
            #tags_equipamento = no_data if not result_eqp_tags else result_eqp_tags.valor

            # DATAPOINTS MODBUS IP
            xid_sensor = no_data if not result_datapoints else result_datapoints.xid_sensor
            # value = no_data if not result_datapoints else result_datapoints.value
            registrador = no_data if not result_datapoints else result_datapoints.offset
            nome = no_data if not result_datapoints else result_datapoints.nome
            tipo = no_data if not result_datapoints else result_datapoints.tipo
            classificacao = no_data if not result_datapoints else result_datapoints.classificacao
            status_datapoints = no_data if not result_datapoints else result_datapoints.enabled
            #tag_sensor = no_data if not result_dp_tags else result_dp_tags.xid_sensor    
       


        if xid_sensor != no_data:

            test_url = "http://localhost:8080/Scada-LTS/api/auth/admin/admin"
            cookie = get_cookie_from_url(test_url)

            url_get_value = "http://localhost:8080/Scada-LTS/api/point_value/getValue/" + \
                str(xid_sensor)

            if cookie != "":

                response_json = get_with_cookie(url_get_value, cookie)
                #print("response_json =", response_json)

                extracted_value = parse_json_response(response_json, "value")
                #print("extracted_value = ", extracted_value)

                tags_equipamento = no_data if not result_eqp_tags else result_eqp_tags.xid_equip
                # xid_eqp_tags = get_tags_from_table(eqp_tags, 'xid_equip', tags_equipamento)
                xid_eqp_tags = fetch_name_value_pairs(eqp_tags, 'xid_equip', tags_equipamento)
                #print("tags_equipamento: ", tags_equipamento)
                #print("TAGS ENCONTRADAS:", xid_eqp_tags)

                tag_sensor = no_data if not result_dp_tags else result_dp_tags.xid_sensor
                # xid_dp_tags = get_tags_from_table(dp_tags, 'xid_sensor', tag_sensor)
                xid_dp_tags = fetch_name_value_pairs(dp_tags, 'xid_sensor', tag_sensor)
                # print("Datapoints: ", tag_sensor)
                # print("TAGS ENCONTRADAS:", xid_dp_tags)
                timestamp = datetime.now().timestamp()

                try:
                    response_data = {
                        "data_gateway": [  # CMA_GD
                            {
                                "ID": gateway_id,
                                "Subestacao": subestacao,
                                "Regional": regional,
                                "IP": host_gateway,
                                "Status": status_gateway
                            }
                        ],
                        "dataSources": [
                            {
                                "Equipamento": xid_equip,
                                "Fabricante": fabricante,
                                "Marca": marca,
                                "Modelo": modelo,
                                "Protocolo": type_,
                                "SAP_id": sap_id,
                                "IP": host_datasource,
                                "Status": status_datasource,
                                "tags_equipamento": xid_eqp_tags
                            }
                        ],
                        "dataPoints": [
                            {
                                "timestamp": timestamp,
                                "Sensor": xid_sensor,
                                "Valor": extracted_value,
                                "Registrador": registrador,
                                "Nome": nome,
                                "Tipo": tipo,
                                "Classificacao": classificacao,
                                "Status": status_datapoints,
                                "tags_sensor": xid_dp_tags
                            }
                        ]
                    }
                    result = json.dumps(response_data, indent=4, ensure_ascii=False)
                    #print("result = ", result)
                except:
                    print("ERRO AO GERAR O JSON PARA O XID_SENSOR=", xid_sensor)
                    result = "Erro ao gerar JSON!"

                return result

            else:
                print("Erro ao obter cookie")

    except Exception as e:

        logger.error(f"Erro ao gerar um Payload (JSON) de múltiplas Tabelas do banco de dados: {e}")

    finally:
        session.close()


# -------------------------------------------------------------
# Rotina de persistencia de envio de dados para MQTT
# -------------------------------------------------------------
def send_data_to_mqtt(content_data):
    if not content_data:
        print("Nenhum conteúdo para enviar ao MQTT.")
        return


    session = SessionLocal()
    try:
        send_success = False
        # 1 - Armazena o JSON no campo content_data
        # e False no campo sended
        query = persistence.__table__.insert().values(
            content_data=content_data,
            sended=False
        )
        session.execute(query)
        session.commit()  # Confirma a transação para inserir no banco
        print("Registro inserido na fila com sucesso!")

        # 2 - Percorre a tabela e envia o JSON onde sended = False.
        # Se o envio for sucesso altera o campo sended = True
        query = select(persistence).where(persistence.sended == False)
        items = session.execute(query).scalars().all()

        for item in items:
            #print(f"Enviando conteúdo: {item.content_data}")
            print("Enviando conteúdo para mqtt...")
            # Simula envio bem-sucedido
            ntries = 3
            current_try = 1
            while (ntries + 1 > current_try):
                print("Tentativa de envio", current_try, "de", ntries)

                if check_rabbitmq_connection(host='localhost', username='cma_gateway', password='cm@GTW'):
                    print("Servidor RabbitMQ está acessível!")
                    status = send_rabbitmq(
                        "amq.topic", "Gateway", "sensor", content_data)
                    if status:
                        send_success = True
                        break

                else:
                    send_success = False
                    print("Não foi possível conectar ao servidor RabbitMQ.")

                    current_try += 1
                    time.sleep(2)

            if send_success:
                # Atualiza o campo sended para True
                query = persistence.__table__.delete().where(
                    persistence.__table__.c.id == item.id
                )
                result = session.execute(query)
                session.commit()
                if result:
                    print("Exclusão de registro temporário concluído com sucesso.")
                else:
                    print("Falha ao excluir registro!")

            else:
                print("Falha ao enviar mensagem. A mensagem foi guardada em fila e será enviada posteriormente!")

    except SQLAlchemyError as e:
        session.rollback()  # Desfaz transações em caso de erro
        logger.error(f"Erro no banco de dados: {str(e)}")
        return {"error": f"Erro no banco de dados: {str(e)}"}

    finally:
        session.close()






# --------------------------------------------------------------------
# Função que coleta "xid_equip", "updatePeriods", "updatePeriodType"
# da tabela de sensores Modbus
# --------------------------------------------------------------------
def getPeriods_eqp_modbus(table_class):
    # Modbus (datasource_modbus_ip)
    # updatePeriods
    # updatePeriodType
    session = SessionLocal()
    try:
        query = select(
            table_class.__table__.c["xid_equip", "updatePeriods", "updatePeriodType"])
        items = session.execute(query).fetchall()
        #print("items eqp_modbus", items)
        return items
    except Exception as e:
        logger.error(f"Erro ao capturar os periodos da tabela datasource_modbus_ip: {e}")
    finally:
        session.close()

# --------------------------------------------------------------------
# Função que coleta "xid_equip", "rbePollPeriods", "eventsPeriodType"
# da tabela de sensores DNP3
# --------------------------------------------------------------------
def getPeriods_eqp_dnp3(table_class):
    # DNP3 (datasource_dnp3)
    # rbePollPeriods
    # eventsPeriodType
    session = SessionLocal()
    try:
        query = select(
            table_class.__table__.c["xid_equip", "rbePollPeriods", "eventsPeriodType"])
        items = session.execute(query).fetchall()
        #print("items eqp_dnp3", items)
        return items
    except Exception as e:
        logger.error(f"Erro ao capturar os periodos da tabela datasource_dnp3: {e}")
    finally:
        session.close()


            

# -------------------------------------------------------------
# Função que recebe o vetor de xid_sensor encontrados
# numa tabela de datapoint e envia um a um para o broker
# -------------------------------------------------------------

def send_xid_sensor(valor, protocol):
    if valor != "null":
        payload_mqtt = process_json_datapoints(valor, protocol)
        #print("send_xid_sensor = ", "valor:", valor , "protocol:", protocol, "payload_mqtt:", payload_mqtt)
        send_data_to_mqtt(payload_mqtt)
    


# -------------------------------------------------------------
# Rotinas de conversão de tempo para millisegundos
# ------------------------------------------------------------- 
def convert_to_seconds(time_value, unit):
    conversion_factors = {
        'MILLISECONDS': 1 / 1000,
        'SECONDS': 1,
        'MINUTES': 60,
        'HOURS': 3600
    }
    return time_value * conversion_factors.get(unit, 1)





#--------------------------------------------------------------------------
# Retorna o xid_sensor da tabela datapoints_modbus_ip passando-se o xid_equip
#--------------------------------------------------------------------------
def get_xid_sensor_from_eqp_modbus(xid_equip_modbus):
    try:
        session = SessionLocal()
        query = select(datapoints_modbus_ip.xid_sensor).where(
            datapoints_modbus_ip.xid_equip == xid_equip_modbus)
        result = session.execute(query).scalars().first()
        #print("Result sensor modbus:", result)
        return result
    except Exception as e:
        logger.error(
            f"Erro ao capturar o xid_sensor da tabela xid_equip_modbus_ip: {e}")
    finally:
        session.close()


#--------------------------------------------------------------------------
# Retorna o xid_sensor da tabela datapoints_dnp3 passando-se o xid_equip
#--------------------------------------------------------------------------
def get_xid_sensor_from_eqp_dnp3(xid_equip_dnp3):
    try:
        session = SessionLocal()
        query = select(datapoints_dnp3.xid_sensor).where(
            datapoints_dnp3.xid_equip == xid_equip_dnp3)
        result = session.execute(query).scalars().first()
        #print("Result sensor dnp3:", result)
        return result
    except Exception as e:
        logger.error(
            f"Erro ao capturar o xid_sensor da tabela datapoints_dnp3: {e}")
    finally:
        session.close()



# -------------------------------------------------------------
# Rotinas de envio de dados sensor modbus para MQTT
# ------------------------------------------------------------- 
def execute_sensors_modbus(xid_modbus, interval, stop_event):
    """ Executa a rotina periodicamente enquanto o evento de parada não for acionado. """
    while not stop_event.is_set():
        for _ in range(int(interval * 10)):  # delay de 0.1s
            if stop_event.is_set():
                print(f"Thread de envio xid_sensor modbus:{xid_modbus} finalizada.")
                return  # Sai imediatamente se o evento foi acionado
            time.sleep(0.1)
        if STATUS_SCADA == "ONLINE":
            print(f"Enviando para MQTT dados xid_sensor mdbus:{xid_modbus} a cada {interval} segundo(s)")
            xid_sensor_modbus = get_xid_sensor_from_eqp_modbus(xid_modbus)
            send_xid_sensor(xid_sensor_modbus,"MODBUS")
        else:
            print("Comunicação com SCADA perdida!")
        time.sleep(1)



# -------------------------------------------------------------
# Rotinas de envio de dados sensor DNP3 para MQTT
# ------------------------------------------------------------- 
def execute_sensors_dnp3(xid_dnp3, interval, stop_event):
    """ Executa a rotina periodicamente enquanto o evento de parada não for acionado. """
    while not stop_event.is_set():
        for _ in range(int(interval * 10)):  # delay de 0.1s
            if stop_event.is_set():
                print(f"Thread de envio xid_sensor dnp3:{xid_dnp3} finalizada.")
                return  # Sai imediatamente se o evento foi acionado
            time.sleep(0.1)
        if STATUS_SCADA == "ONLINE":
            print(f"Enviando para MQTT dados xid_sensor dnp3:{xid_dnp3} a cada {interval} segundo(s)")
            xid_sensor_dnp3 = get_xid_sensor_from_eqp_dnp3(xid_dnp3)
            send_xid_sensor(xid_sensor_dnp3,"DNP3")
        else:
            print("Comunicação com SCADA perdida!")
        time.sleep(1)
        



# Função de verificação de status do servidor
def thr_check_server_online(host: str, port: int, servername: str):
    while True:
        try:
            global STATUS_CMA
            global STATUS_SCADA
            global service_status
            with socket.create_connection((host, port), timeout=5):
                if port == 5000:
                    STATUS_CMA = "ONLINE"
                if port == 8080:
                    STATUS_SCADA = "ONLINE"
                service_status["is_running"] = True
        except (socket.timeout, ConnectionRefusedError):
            if port == 5000:
                STATUS_CMA = "OFFLINE"
            if port == 8080:
                STATUS_SCADA = "OFFLINE"
            service_status["is_running"] = False

        conexao = "ONLINE" if service_status["is_running"] else "OFFLINE"
        if conexao == "OFFLINE":
            logger.error(f"Servidor {servername} está offline!")

        print("---------------------------------------------------------------")
        print("SERVER STATUS ["+servername+"]:", conexao)
        print("---------------------------------------------------------------\n")
        print("")
        time.sleep(30)


# Função de controle para sensores Modbus
def thr_start_routines_sensor_modbus(datasource):
    routines_map = {}

    while True:
        time_list = getPeriods_eqp_modbus(datasource)
        active_ids = set()

        for id_, time_value, unit in time_list:
            active_ids.add(id_)
            interval = convert_to_seconds(time_value, unit)

            # Verifica se a thread já existe
            if id_ in routines_map:
                _, _, old_interval = routines_map[id_]
                if old_interval == interval:
                    continue

                print(f"Reiniciando xid_equip modbus:{id_} com novo intervalo...")
                routines_map[id_][1].set()  # Aciona o evento de parada
                routines_map[id_][0].join()  # Aguarda o término da thread
                del routines_map[id_]

            # Criar nova thread com o intervalo atualizado
            stop_event = threading.Event()
            thread = threading.Thread(target=execute_sensors_modbus, args=(id_, interval, stop_event), daemon=True)
            thread.start()
            routines_map[id_] = (thread, stop_event, interval)

        # Verifica se alguma thread precisa ser encerrada
        for id_ in list(routines_map.keys()):
            if id_ not in active_ids:
                print(f"Encerrando xid_equip modbus:{id_}...")
                routines_map[id_][1].set()  # Aciona o evento de parada
                routines_map[id_][0].join()  # Aguarda o término da thread
                del routines_map[id_]

        time.sleep(1)


# Função de controle para sensores DNP3
def thr_start_routines_sensor_dnp3(datasource):
    routines_map = {}

    while True:
        time_list = getPeriods_eqp_dnp3(datasource)
        active_ids = set()
        #print("time_list_dnp3=", time_list)
        for id_, time_value, unit in time_list:
            active_ids.add(id_)
            interval = convert_to_seconds(time_value, unit)

            # Verifica se a thread já existe
            if id_ in routines_map:
                _, _, old_interval = routines_map[id_]
                if old_interval == interval:
                    continue

                print(f"Reiniciando xid_sensor dnp3:{id_} com novo intervalo...")
                routines_map[id_][1].set()  # Aciona o evento de parada
                routines_map[id_][0].join()  # Aguarda o término da thread
                del routines_map[id_]

            # Criar nova thread com o intervalo atualizado
            stop_event = threading.Event()
            thread = threading.Thread(target=execute_sensors_dnp3, args=(id_, interval, stop_event), daemon=True)
            thread.start()
            routines_map[id_] = (thread, stop_event, interval)

        # Verifica se alguma thread precisa ser encerrada
        for id_ in list(routines_map.keys()):
            if id_ not in active_ids:
                print(f"Encerrando xid_sensor dnp3:{id_}...")
                routines_map[id_][1].set()  # Aciona o evento de parada
                routines_map[id_][0].join()  # Aguarda o término da thread
                del routines_map[id_]

        time.sleep(1)


# Função de inicialização das threads de verificação de servidores
def start_service_checker():
    """Inicia os processos para checar servidores."""
    
    if "process_cma" not in active_threads:
        process_cma = threading.Thread(target=thr_check_server_online, args=("127.0.0.1", 5000, "CMA"), daemon=True)
        active_threads["process_cma"] = process_cma  # Armazena a referência da thread
        process_cma.start()

    if "process_scada" not in active_threads:
        process_scada = threading.Thread(target=thr_check_server_online, args=("127.0.0.1", 8080, "SCADA-LTS"), daemon=True)
        active_threads["process_scada"] = process_scada  # Armazena a referência da thread
        process_scada.start()

    if "health_checker" not in active_threads:
        health_checker = threading.Thread(target=thr_get_system_info, args=(), daemon = True)
        active_threads["health_checker"] = health_checker  # Armazena a referência da thread
        health_checker.start()

    if "modbus_thread" not in active_threads:
        modbus_thread = threading.Thread(target=thr_start_routines_sensor_modbus, args=(datasource_modbus_ip,), daemon=True)
        active_threads["modbus_thread"] = modbus_thread  # Armazena a referência da thread
        modbus_thread.start()
    
    if "dnp3_thread" not in active_threads:
        dnp3_thread = threading.Thread(target=thr_start_routines_sensor_dnp3, args=(datasource_dnp3,), daemon=True)
        active_threads["dnp3_thread"] = dnp3_thread  # Armazena a referência da thread
        dnp3_thread.start()






#-------------------------------------
# TODO: 
# Fazer script shell de configuração geral com menus e submenus (salvar config.ini)
# Pegar as configurações do config.ini
# logger nas mensagens de erro
# Revisão geral do script