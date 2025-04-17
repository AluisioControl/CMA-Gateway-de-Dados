###############################################################
# main.py
# ------------------------------------------------------------
# Arquivo principaldo Middleware
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
from scadalts import *
from logger import *
from dotenv import load_dotenv

# Carregando as variáveis de ambiente do arquivo .env
load_dotenv()

# Variáveis de configuração de tempos de chacagem
HEALTH_SYSTEM_CHECK_INTERVAL = os.getenv("HEALTH_CHECK_INTERVAL")
STATUS_SERVER_CHECK_INTERVAL = os.getenv("STATUS_SERVER_CHECK_INTERVAL")

# Variáveis da aplicação
stop_event = threading.Event()
STATUS_SCADA = "INICIANDO"
service_status = {"is_running": False}

# Variável global para controle das threads
active_threads = {}



def get_network_info():

    """
    Retorna as informações da placa de rede, como IP, máscara, status e velocidade.

    Retorna um dicionário com as seguintes chaves:
    - Interface: nome da interface de rede
    - IP: endereço IP da interface
    - Máscara: máscara de sub-rede da interface
    - Status: status da interface (Ativo ou Inativo)
    - Velocidade: velocidade da interface em Mbps

    Se nenhuma interface de rede com cabo conectado for encontrada, retorna None.
    """
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


def thr_get_system_info():
    """
    Função que retorna informações do sistema.

    Informações coletadas:
        - Memória RAM (total, usada, percentual)
        - Uso do processador (percentual)
        - Espaço do HD (total, usado, percentual)
        - Tempo de funcionamento (em horas e minutos)
        - Informações da rede (interface, IP, máscara, status e velocidade)

    A função executa em loop infinito e exibe as informações
    a cada 15 segundos.
    """
    print("Iniciando monitoramento de informações do sistema...")
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
            print("\n=====  INFORMAÇÕES DA REDE   =====")
            print(f"Interface: {network_data['Interface']}")
            print(f"IP: {network_data['IP']}")
            print(f"Máscara: {network_data['Máscara']}")
            print(f"Status: {network_data['Status']}")
            print(f"Velocidade: {network_data['Velocidade']}\n")
        else:
            print("\n=====  INFORMAÇÕES DA REDE   =====")
            print("Nenhuma conexão de rede com cabo detectada.\n")


        payload = {
        "sistema": {
                "memoria_ram": {
                    "usada_gb": round(used_ram, 2),
                    "total_gb": round(total_ram, 2),
                    "percentual_uso": f"{ram_percent}%" if ram_percent is not None else ram_percent
                },
                "processador": {
                    "percentual_uso": f"{cpu_usage}%" if cpu_usage is not None else cpu_usage
                },
                "hd": {
                    "usado_gb": round(used_disk, 2),
                    "total_gb": round(total_disk, 2),
                    "percentual_uso": f"{disk_percent}%"
                },
                "tempo_funcionamento": {
                    "tempo_h_min": f"{int(uptime_hours)}:{int(uptime_minutes)}"
                }, 
                "rede": {
                    "interface": network_data["Interface"] if network_data else None,
                    "ip": network_data["IP"] if network_data else None,
                    "mascara": network_data["Máscara"] if network_data else None,
                    "status": network_data["Status"] if network_data else None,
                    "velocidade": network_data["Velocidade"] if network_data  else None
                }
            }
        }
        payload = json.dumps(payload, indent=4, ensure_ascii=False)
        send_data_to_mqtt(payload)
        time.sleep(int(HEALTH_SYSTEM_CHECK_INTERVAL))


def fetch_name_value_pairs(table_class, field_name, xid):

    """
    Busca pares de valores das colunas 'nome' e 'valor' de uma tabela
    e retorna uma estrutura de dados no formato [{"nome": "valor"}, ...].

    Args:
        table_class: Classe ORM que representa a tabela.
        field_name (str): Nome da coluna usada como filtro.
        xid: Valor usado na condição WHERE.

    Returns:
        list[dict]: Lista de dicionários no formato {"nome": "valor"}.
    """

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


def parse_json_response(json_response, key):

    """
    Faz o parse de um JSON e retorna o valor associado a uma chave fornecida.

    Args:
        json_response (dict): O JSON retornado da função `get_with_cookie`.
        key (str): A chave cujo valor o usuário deseja extrair.

    Returns:
        Any: O valor associado à chave, ou uma mensagem de erro se a chave
        não existir ou se ocorrer um erro durante o processamento.
    """

    try:
        if key in json_response:
            return json_response[key]
        else:
            logger.error(f"Chave '{key}' não encontrada no JSON.")
            return f"Chave '{key}' não encontrada no JSON."
    except Exception as e:
        logger.error(f"Erro ao processar o JSON: {e}")
        return f"Erro ao processar o JSON: {e}"


def process_json_datapoints(xid_sensor_param: str, protocol: str):

    """
    Função para geração de um Payload (arquivo JSON) de múltiplas
    Tabelas do banco de dados

    Args:
        xid_sensor_param (str): Valor do xid_sensor.
        protocol (str): "modbus" ou "dnp3".

    Returns:
        json: payload Json com os dados para ser enviados para Scada-LTS
    """
    session = SessionLocal()

    try:
        no_data = "sem dados"
        if protocol == "DNP3":
            
            # Montando query datapoints dnp3
            query_datapoints = select(datapoints_dnp3).where(datapoints_dnp3.xid_sensor == xid_sensor_param)
            result_datapoints = session.execute(query_datapoints).scalars().first()
            xid_eqp = no_data if not result_datapoints else result_datapoints.xid_equip
            
            # Montando query datasources dnp3
            query_datasources = select(datasource_dnp3).where(datasource_dnp3.xid_equip == xid_eqp)
            result_datasources = session.execute(query_datasources).scalars().first()
            xid_gtw = no_data if not result_datasources else result_datasources.xid_gateway
         
            #Montando queries 
            query_cma_gateway = select(cma_gateway).where(cma_gateway.xid_gateway == xid_gtw)
            query_datasource_dnp3 = select(datasource_dnp3).where(datasource_dnp3.xid_equip == xid_eqp)
            query_eqp_tags = select(eqp_tags).where(eqp_tags.xid_equip == xid_eqp)
            query_dp_tags = select(dp_tags).where(dp_tags.xid_sensor == xid_sensor_param)

            # resultado das queries
            result_cma_gateway = session.execute(query_cma_gateway).scalars().first()
            result_datasource_dnp3 = session.execute(query_datasource_dnp3).scalars().first()
            result_eqp_tags = session.execute(query_eqp_tags).scalars().first()
            result_dp_tags = session.execute(query_dp_tags).scalars().first()

            # Coletando variáveis de interesse DATA GATEWAY
            gateway_id = no_data if not result_cma_gateway else result_cma_gateway.xid_gateway
            subestacao = no_data if not result_cma_gateway else result_cma_gateway.subestacao
            regional = no_data if not result_cma_gateway else result_cma_gateway.regional
            host_gateway = no_data if not result_cma_gateway else result_cma_gateway.host
            status_gateway = no_data if not result_cma_gateway else result_cma_gateway.status

            # Coletando variáveis de interesse DATASOURCE DNP 3
            xid_equip = no_data if not result_datasource_dnp3 else result_datasource_dnp3.xid_equip
            fabricante = no_data if not result_datasource_dnp3 else result_datasource_dnp3.fabricante
            marca = no_data if not result_datasource_dnp3 else result_datasource_dnp3.marca
            modelo = no_data if not result_datasource_dnp3 else result_datasource_dnp3.modelo
            type_ = no_data if not result_datasource_dnp3 else result_datasource_dnp3.type
            sap_id = no_data if not result_datasource_dnp3 else result_datasource_dnp3.sap_id
            status_datasource = no_data if not result_datasource_dnp3 else result_datasource_dnp3.enabled
            host_datasource = no_data if not result_datasource_dnp3 else result_datasource_dnp3.host
            
            # Coletando variáveis de interesse DATAPOINTS DNP3 IP
            xid_sensor = no_data if not result_datapoints else result_datapoints.xid_sensor
            registrador = no_data if not result_datapoints else result_datapoints.index
            nome = no_data if not result_datapoints else result_datapoints.nome
            tipo = no_data if not result_datapoints else result_datapoints.tipo
            classificacao = no_data if not result_datapoints else result_datapoints.classificacao
            status_datapoints = no_data if not result_datapoints else result_datapoints.enabled
            

        elif protocol == "MODBUS":
            
           # Montando query datapoints modbus
            query_datapoints = select(datapoints_modbus_ip).where(datapoints_modbus_ip.xid_sensor == xid_sensor_param)
            result_datapoints = session.execute(query_datapoints).scalars().first()
            xid_eqp = no_data if not result_datapoints else result_datapoints.xid_equip

            # Montando query datasources modbus
            query_datasources = select(datasource_modbus_ip).where(datasource_modbus_ip.xid_equip == xid_eqp)
            result_datasources = session.execute(query_datasources).scalars().first()
            xid_gtw = no_data if not result_datasources else result_datasources.xid_gateway

            # Montando queries
            query_cma_gateway = select(cma_gateway).where(cma_gateway.xid_gateway == xid_gtw)
            query_datasource_modbus_ip = select(datasource_modbus_ip).where(datasource_modbus_ip.xid_equip == xid_eqp)
            query_eqp_tags = select(eqp_tags).where(eqp_tags.xid_equip == xid_eqp)
            query_dp_tags = select(dp_tags).where(dp_tags.xid_sensor == xid_sensor_param)

            # Resultado das queries
            result_cma_gateway = session.execute(query_cma_gateway).scalars().first()
            result_datasource_modbus_ip = session.execute(query_datasource_modbus_ip).scalars().first()
            result_eqp_tags = session.execute(query_eqp_tags).scalars().first()
            result_dp_tags = session.execute(query_dp_tags).scalars().first()

            # Coletando variáveis de interesse DATA GATEWAY
            gateway_id = no_data if not result_cma_gateway else result_cma_gateway.xid_gateway
            subestacao = no_data if not result_cma_gateway else result_cma_gateway.subestacao
            regional = no_data if not result_cma_gateway else result_cma_gateway.regional
            host_gateway = no_data if not result_cma_gateway else result_cma_gateway.host
            gtw_id = no_data if not result_cma_gateway else result_cma_gateway.id_gtw
            sub_id = no_data if not result_cma_gateway else result_cma_gateway.id_sub 
            

            # Coletando variáveis de interesse DATASOURCE MODBUS IP
            xid_equip = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.xid_equip
            fabricante = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.fabricante
            sap_id = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.sap_id
            host_datasource = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.host
            id_hdw_id = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.id_hdw
            name_hdw_name = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.name_hdw
            type_sen_type = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.type
            model_sen_model = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.model_sen
            name_sen_name = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.name_sen
            id_man_id = no_data if not result_datasource_modbus_ip else result_datasource_modbus_ip.id_man

            # Coletando variáveis de interesse DATAPOINTS MODBUS IP
            xid_sensor = no_data if not result_datapoints else result_datapoints.xid_sensor
            registrador = no_data if not result_datapoints else result_datapoints.offset
            nome = no_data if not result_datapoints else result_datapoints.nome
            phase_reg= no_data if not result_datapoints else result_datapoints.phase
            circuitBreakerManeuverType_reg = no_data if not result_datapoints else result_datapoints.circuitBreakerManeuverType_reg_mod
            bushingSide_reg = no_data if not result_datapoints else result_datapoints.bushingSide
            register_type_id_reg = no_data if not result_datapoints else result_datapoints.id_reg_reg_mod
            register_type_reg = no_data if not result_datapoints else result_datapoints.classificacao
            sensor_type_id_reg = no_data if not result_datapoints else result_datapoints.id_sen_reg_mod
            sensor_type_reg = no_data if not result_datapoints else result_datapoints.tipo
          
       
        if xid_sensor != no_data:
            #print("Entrando no if xid_sensor\n")
            extracted_value = get_json_data(xid_sensor) #retorne o payload da api para extrair o value ou retorna none            
            extracted_value = parse_json_response(extracted_value, 'value') 
            print("Extracted value: ", extracted_value)

            if extracted_value != None:
                #print("Entrando no get_json_data(xid_sensor)\n")    
                tags_equipamento = no_data if not result_eqp_tags else result_eqp_tags.xid_equip
                xid_eqp_tags = fetch_name_value_pairs(eqp_tags, 'xid_equip', tags_equipamento)
                tag_sensor = no_data if not result_dp_tags else result_dp_tags.xid_sensor
                xid_dp_tags = fetch_name_value_pairs(dp_tags, 'xid_sensor', tag_sensor)
                timestamp = datetime.now().timestamp()
                #result=None #Se result é atribuído como None após primeiro resultado válido como os demais procederão corretamente?
 
                try:
                        response_data = {
                            "gateways": [  
                                {
                                    "timestamp":timestamp,
                                    "gateway_id": gtw_id,
                                    "gateway_name":gateway_id,
                                    "gateway_ip":host_gateway,
                                    "SE_id":sub_id,
                                    "SE":subestacao,
                                    "SE_Region":regional
                                }
                            ],
                            "sensors": [
                                {
                                    "hardware_id": id_hdw_id,
                                    "hardware_name": name_hdw_name,
                                    "sap_id": sap_id,
                                    "type": type_sen_type,
                                    "model": model_sen_model,
                                    "sensor_id":xid_equip,
                                    "sensor_name": name_sen_name,
                                    "sensor_ip":host_datasource,
                                    "sensor_protocol": protocol,
                                    "manufacturer_id": id_man_id,
                                    "manufacturer_name": fabricante,
                                    "sensor_tags": xid_eqp_tags
                                }
                            ],
                            "registers": [
                                {
                                    "register_id": xid_sensor,
                                    "register_name": nome,
                                    "register": registrador,
                                    "phase":phase_reg,
                                    "circuitBreakerManeuverType":circuitBreakerManeuverType_reg,
                                    "bushingSide":bushingSide_reg,
                                    "register_type_id":register_type_id_reg,
                                    "register_type":register_type_reg,
                                    "sensor_type_id":sensor_type_id_reg,
                                    "sensor_type":sensor_type_reg,                                
                                    "register_tags": xid_dp_tags,
                                    "register_value": extracted_value,
                                }
                            ]
                        }
                        result = json.dumps(response_data, indent=4, ensure_ascii=False)
                        return result
                        #print("result = ", result)
                except:
                        print("Erro ao gerar JSON com dados do xid_sensor", xid_sensor)
                        logger.error(f"Erro ao gerar JSON com dados do xid_sensor {xid_sensor}")
                        payload = {
                        "xid_erro": {
                            "xid_sensor": "Json Error value"
                        }
                    }

                result = json.dumps(payload, indent=4, ensure_ascii=False)
                return result
                
            elif extracted_value == None:
                    print(f"Valor de xid_sensor: {xid_sensor} = None. Um report será enviado.")
                    logger.warning(f"Valor de xid_sensor: {xid_sensor} = None. Um report será enviado.")
                    payload = {
                        "xid_erro": {
                            "xid_sensor_none": xid_sensor
                        }
                    }

                    result = json.dumps(payload, indent=4, ensure_ascii=False)
                    return result

                    #send_data_to_mqtt(payload)   #send_data_to_mqtt(payload) é chamado logo após obter resultado dessa função               
                    #return result
            else:
                print("Erro ao obter dados do xid_sensor", xid_sensor, "no Sacada-LTS!")
                logger.error(f"Erro ao obter dados do xid_sensor {xid_sensor} no Sacada-LTS!")
                payload = {
                        "xid_erro": {
                            "xid_sensor": xid_sensor,
                            "descricao": "Json Error extratecd value"
                        }
                    }

                result = json.dumps(payload, indent=4, ensure_ascii=False)
                return result

    except Exception as e:
        logger.error(f"Erro ao gerar um Payload (JSON) de múltiplas Tabelas do banco de dados: {e}")
        payload = {
                        "xid_erro": {
                            "xid_sensor": xid_sensor,
                            "descricao": "Json Error no data"
                        }
                    }

        result = json.dumps(payload, indent=4, ensure_ascii=False)
        return result

    finally:
        session.close()

def send_data_to_mqtt(content_data):

    """
    Função que armazena e envia um JSON para o RabbitMQ.

    Parameters
    ----------
    content_data : str
        Conteúdo do JSON a ser armazenado e enviado ao RabbitMQ.

    Returns
    -------
    dict
        Dicionário com chave "error" caso haja erro. Caso contrário, 
        retorna None.

    Notes
    -----
    1. Armazena o JSON no campo content_data e False no campo sended
    2. Percorre a tabela e envia o JSON onde sended = False.
       Se o envio for sucesso altera o campo sended = True
    """
    print("send_data_to_mqtt -> content_data = ", content_data)
    if  content_data == "":
        print("Nenhum conteúdo para enviar ao MQTT!")
        return

    session = SessionLocal()
    try:
        send_success = False
        # 1 - Armazena o JSON no campo content_data
        # e atribui False no campo sended
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

            ntries = 3
            current_try = 1
            while (ntries + 1 > current_try):
                print("Tentativa de envio", current_try, "de", ntries)

                if check_rabbitmq_connection(): # Verifica se o RabbitMg está online antes de enviar
                    print("Servidor RabbitMQ está acessível!")
                    status = send_rabbitmq(content_data)
                    if status:
                        send_success = True
                        break

                else:
                    send_success = False
                    print("Não foi possível conectar ao servidor RabbitMQ.")
                    logger.error("Não foi possível conectar ao servidor RabbitMQ.")
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
                    print("Exclusão de registro temporário concluído com sucesso!\n\n\n")
                else:
                    print("Falha ao excluir registro temporário!")

            else:
                print("Falha ao enviar mensagem para o MQTT. A mensagem foi guardada em fila e será enviada posteriormente!")

    except SQLAlchemyError as e:
        session.rollback()  # Desfaz transações em caso de erro
        logger.error(f"Erro no banco de dados: {str(e)}")
        return {"error": f"Erro no banco de dados: {str(e)}"}

    finally:
        session.close()


def get_periods_eqp(table_class, protocol):

    """
    Coleta os períodos de atualização de equipamentos Modbus ou DNP3.

    Args:
        table_class: Classe ORM que representa a tabela de equipamentos.
        protocol (str): Protocolo dos equipamentos, pode ser "modbus" ou "dnp3".

    Returns:
        list: Lista de tuplas contendo xid_equip e os períodos correspondentes.

    Raises:
        ValueError: Se o protocolo fornecido não for "modbus" ou "dnp3".

    Notes:
        - Para Modbus, são retornados os campos "updatePeriods" e "updatePeriodType".
        - Para DNP3, são retornados os campos "rbePollPeriods" e "eventsPeriodType".
    """

    session = SessionLocal()
    try:
        if protocol == "modbus": 
            query = select(table_class.__table__.c["xid_equip", "updatePeriods", "updatePeriodType"])
        elif protocol == "dnp3": 
            query = select(table_class.__table__.c["xid_equip", "rbePollPeriods", "eventsPeriodType"])
        else:
            raise ValueError("Protocolo inválido")
        items = session.execute(query).fetchall()
        return items
    except Exception as e:
        logger.error(f"Erro ao capturar os períodos da tabela {protocol}: {e}")
    finally:
        session.close()
            

def convert_to_seconds(time_value, unit):

    """
    Converte um valor de tempo em segundos.

    Args:
        time_value (float): Valor de tempo a ser convertido.
        unit (str): Unidade do valor de tempo. Pode ser "MILLISECONDS", "SECONDS", "MINUTES" ou "HOURS".

    Returns:
        float: O valor de tempo convertido em segundos.
    """

    conversion_factors = {
        'MILLISECONDS': 1 / 1000,
        'SECONDS': 1,
        'MINUTES': 60,
        'HOURS': 3600
    }
    return time_value * conversion_factors.get(unit, 1)


def get_xid_sensor_from_eqp_modbus(xid_equip_modbus):

    """
    Retorna o xid_sensor da tabela datapoints_modbus_ip com base no xid_equip_modbus.

    Args:
        xid_equip_modbus (str): Xid do equipamento Modbus IP.

    Returns:
        str: Xid do sensor Modbus IP.
    """
    try:
        session = SessionLocal()
        
        query = select(datapoints_modbus_ip.xid_sensor).where(
            datapoints_modbus_ip.xid_equip == xid_equip_modbus)
        result = session.execute(query).scalars().all()
        print("xid_sensor modbus: ", result)
        return result
    except Exception as e:
        logger.error(
            f"Erro ao capturar o xid_sensor da tabela xid_equip_modbus_ip: {e}")
    finally:
        session.close()


def get_xid_sensor_from_eqp_dnp3(xid_equip_dnp3):

    """
    Retorna o xid_sensor da tabela datapoints_dnp3 com base no xid_equip.

    Args:
        xid_equip_dnp3 (str): Xid do equipamento DNP3.

    Returns:
        str: Xid do sensor DNP3.
    """

    try:
        session = SessionLocal()
        query = select(datapoints_dnp3.xid_sensor).where(
            datapoints_dnp3.xid_equip == xid_equip_dnp3)
        result = session.execute(query).scalars().all()

        return result
    except Exception as e:
        logger.error(
            f"Erro ao capturar o xid_sensor da tabela datapoints_dnp3: {e}")
    finally:
        session.close()


def execute_sensors_modbus(xid_modbus, interval, stop_event):
    """ 
    Executa a rotina de coleta dos tempos para envio dos dados dos 
    sensores Modbus periodicamente enquanto o evento de parada não 
    for acionado. 

    Args:
        xid_modbus (str): Xid do equipamento Modbus.
        interval (float): Intervalo de envio dos dados em segundos.
        stop_event (Event): Evento de parada.

    returns:
        None
    """
    print("entrou no execute_sensors_modbus...")
    while not stop_event.is_set():
        for _ in range(int(interval * 10)):  # delay de 0.1s
            if stop_event.is_set():
                print(f"Thread de envio xid_sensor modbus:{xid_modbus} finalizada.")
                return  # Sai imediatamente se o evento foi acionado
            time.sleep(0.1)
        if STATUS_SCADA == "ONLINE":
            print(f"\nEnviando para MQTT dados xid_sensor mdbus:{xid_modbus} a cada {interval/60} minuto(s)")
            list_xid_sensor_modbus = get_xid_sensor_from_eqp_modbus(xid_modbus)
            
            agora = datetime.now()
            print(agora.strftime("%Y-%m-%d %H:%M:%S"))  # Exemplo: 2025-03-16 14:32:15
            for xid_sensor_modbus in list_xid_sensor_modbus:
                print("Enviando para mqtt dados do sensor modbus: ", xid_sensor_modbus)
                payload = process_json_datapoints(xid_sensor_modbus, "MODBUS")
                print("PAYLOAD A SER ENVIADO PARA MQTT=", payload)
                send_data_to_mqtt(payload)

        else:
            print(f"Comunicação com SCADA perdida ao enviar dados xid_sensor modbus:{xid_modbus}!")
            logger.error(f"Comunicação com SCADA perdida ao enviar dados xid_sensor modbus:{xid_modbus}!")
        time.sleep(1)


def execute_sensors_dnp3(xid_dnp3, interval, stop_event):
    """ 
    Executa a rotina de coleta dos tempos para envio dos dados dos 
    sensores DNP3 periodicamente enquanto o evento de parada não 
    for acionado. 

    Args:
        xid_dnp3 (str): Xid do equipamento DNP3.
        interval (float): Intervalo de envio dos dados em segundos.
        stop_event (Event): Evento de parada.

    returns:
        None
    """
    while not stop_event.is_set():
        for _ in range(int(interval * 10)):  # delay de 0.1s
            if stop_event.is_set():
                print(f"Thread de envio xid_sensor dnp3:{xid_dnp3} finalizada.")
                return  # Sai imediatamente se o evento foi acionado
            time.sleep(0.1)
        if STATUS_SCADA == "ONLINE":
            print(f"\nEnviando para MQTT dados xid_sensor dnp3:{xid_dnp3} a cada {interval} segundo(s)")
            list_xid_sensor_dnp3 = get_xid_sensor_from_eqp_dnp3(xid_dnp3)
            for xid_sensor_dnp3 in list_xid_sensor_dnp3:
                print("Enviando para mqtt dados do sensor dnp3: ", xid_sensor_dnp3)
                payload = process_json_datapoints(xid_sensor_dnp3, "DNP3")
                send_data_to_mqtt(payload)
        else:
            print(f"Comunicação com SCADA perdida ao enviar dados xid_sensor DNP3:{xid_dnp3}!")
            logger.error(f"Comunicação com SCADA perdida ao enviar dados xid_sensor DNP3:{xid_dnp3}!")
        time.sleep(1)
        

def thr_check_server_online(host: str, port: int, servername: str):

    """
    Verifica se o servidor está online ou offline.

    Verifica se o servidor especificado pela variável `host` e `port` está online ou offline.
    Se o servidor estiver online, muda o valor da variável STATUS_SCADA para "ONLINE".
    Se o servidor estiver offline, muda o valor da variável  STATUS_SCADA para "OFFLINE".
    """
    print(f"Iniciando verificação de status do servidor {host}:{port} ...")
    while True:
        try:
            
            global STATUS_SCADA
            global service_status
            with socket.create_connection((host, port), timeout=5):
                if port == 8080:
                    STATUS_SCADA = "ONLINE"
                service_status["is_running"] = True
        except (socket.timeout, ConnectionRefusedError):
            if port == 8080:
                STATUS_SCADA = "OFFLINE"
            service_status["is_running"] = False

        conexao = "ONLINE" if service_status["is_running"] else "OFFLINE"
        if conexao == "OFFLINE":
            logger.error(f"Servidor {servername} está offline!")

        if conexao == "ONLINE":
            STATUS_AUTH_SCADA = auth_ScadaLTS()
    
        print("\n=====   CONEXÃO COM SCADA    =====")
        print("["+servername+"]:", conexao)
        print("Status de autenticação com SCADA:", STATUS_AUTH_SCADA)
        print("\n")

        payload = {
            "scada_lts": {
                "status_conexao": STATUS_SCADA,
                "status_autenticacao": STATUS_AUTH_SCADA
            }
        }

        payload = json.dumps(payload, indent=4, ensure_ascii=False)
        send_data_to_mqtt(payload)
        logger.info("Enviando payload status de conexão SACADA-LTS para RabbitMQ...")
             
        time.sleep(int(STATUS_SERVER_CHECK_INTERVAL))


def thr_start_routines_sensor(datasource, protocol):

    """
    Inicia threads individualizadas para cada sensor Modbus ou DNP3,
    com intervalos de envio de dados para o broker MQTT configurados
    dinamicamente.

    A cada loop, verifica se o intervalo de envio de dados mudou
    para algum sensor, e se sim, reinicia a thread com o novo intervalo.
    Se o sensor não estiver mais na lista de sensores ativos, encerra
    a thread.

    Parameters:
        datasource (str): Fonte de dados, pode ser "modbus" ou "dnp3".
        protocol (str): Protocolo do sensor, pode ser "modbus" ou "dnp3".
    """

    proccess_map = {}
    
    # Mapeia funções conforme o protocolo
    execute_sensors_func = execute_sensors_modbus if protocol == "modbus" else execute_sensors_dnp3
    print(f"Iniciando as rotinas do sensor {protocol}...")
    while True:

        time_list = get_periods_eqp(datasource, protocol)
        active_ids = set()

        for id_, time_value, unit in time_list:
            active_ids.add(id_)
            interval = convert_to_seconds(time_value, unit)

            # Verifica se a thread já existe e se o intervalo mudou
            if id_ in proccess_map:
                _, _, old_interval = proccess_map[id_]
                if old_interval == interval:
                    continue

                print(f"Reiniciando {protocol} sensor {id_} com novo intervalo...")
                proccess_map[id_][1].set()  # Aciona o evento de parada
                proccess_map[id_][0].join()  # Aguarda o término da thread
                del proccess_map[id_]

            # Criar nova thread com o intervalo atualizado
            stop_event = threading.Event()
            thread = threading.Thread(target=execute_sensors_func, args=(id_, interval, stop_event), daemon=True)
            thread.start()
            proccess_map[id_] = (thread, stop_event, interval)

        # Verifica se alguma thread precisa ser encerrada
        for id_ in list(proccess_map.keys()):
            if id_ not in active_ids:
                print(f"Encerrando {protocol} sensor {id_}...")
                proccess_map[id_][1].set()  # Aciona o evento de parada
                proccess_map[id_][0].join()  # Aguarda o término da thread
                del proccess_map[id_]
        #print("Processos de sensores rodando no momento: ", len(proccess_map))
        time.sleep(1)


# =======================================================================
# Função principal de inicialização das threads de 
# de envio de dados para MQTT e verificação de conexão com servidores
# =======================================================================
def start_main_threads():
    """Inicia os processos para checar servidores.""" 

    if "process_scada" not in active_threads:
        process_scada = threading.Thread(target=thr_check_server_online, args=("127.0.0.1", 8080, "SCADA-LTS"), daemon=True)
        active_threads["process_scada"] = process_scada  # Armazena a referência da thread
        process_scada.start()
    
    """Inicia os processos para monitorar o sistema (health check)"""
    if "health_checker" not in active_threads:
        health_checker = threading.Thread(target=thr_get_system_info, args=(), daemon = True)
        active_threads["health_checker"] = health_checker  # Armazena a referência da thread
        health_checker.start()

    """Inicia os processos de comunicação com Scada-LTS e envio de dados para MQTT"""
    
    if "modbus_thread" not in active_threads:
        modbus_thread = threading.Thread(target=thr_start_routines_sensor, args=(datasource_modbus_ip,"modbus"), daemon=True)
        active_threads["modbus_thread"] = modbus_thread  # Armazena a referência da thread
        modbus_thread.start()

    if "dnp3_thread" not in active_threads:
        dnp3_thread = threading.Thread(target=thr_start_routines_sensor, args=(datasource_dnp3,"dnp3"), daemon=True)
        active_threads["dnp3_thread"] = dnp3_thread  # Armazena a referência da thread
        dnp3_thread.start()
    

if __name__ == "__main__":
    start_main_threads()

#Garante que todas as threads sejam encerradas
for thread in threading.enumerate():
    if thread is not threading.main_thread():
        thread.join()