import pycurl
import json
from io import BytesIO
import time
import re
from dotenv import load_dotenv
import os
from logger import *
# Carregando as variáveis de ambiente do arquivo .env
load_dotenv()

username = os.getenv("username")
password = os.getenv("password")
URL_BASE = os.getenv("URL_BASE")

AUTH_URL = f"{URL_BASE}/Scada-LTS/api/auth/admin/admin"

# Cache do cookie e tempo de expiração
cookie_cache = {
    "value": None,
    "expires_at": 0
}

def get_cookie_from_url(url):
    """Obtém um novo cookie de autenticação da URL fornecida."""
    global cookie_cache

    buffer = BytesIO()
    header_buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.URL, url)
    curl.setopt(curl.WRITEFUNCTION, buffer.write)
    curl.setopt(curl.HEADERFUNCTION, header_buffer.write)
    curl.setopt(curl.COOKIEFILE, '')

    try:
        curl.perform()
        status_code = curl.getinfo(pycurl.RESPONSE_CODE)
        headers = header_buffer.getvalue().decode('utf-8').splitlines()

        print(f"Status Code ao obter cookie: {status_code}")
        #print(f"Cabeçalhos recebidos:\n{headers}")

        cookies = [line for line in headers if 'Set-Cookie' in line]
        
        if status_code == 200 and cookies:
            #print(f"Cookies brutos encontrados: {cookies}")

            match = re.search(r"Set-Cookie:\s*([^;]+)", cookies[0], re.IGNORECASE)
            if match:
                cookie = match.group(1)
                cookie_cache["value"] = cookie
                cookie_cache["expires_at"] = time.time() + 3600  # 1 hora

                print(f"Novo cookie armazenado: {cookie_cache['value']}, expira em {time.ctime(cookie_cache['expires_at'])}")
                logger.warning(f"Novo cookie armazenado: {cookie_cache['value']}, expira em {time.ctime(cookie_cache['expires_at'])}")
                return cookie
            else:
                print("Erro ao extrair o cookie do cabeçalho.")
                logger.error("Erro ao extrair o cookie do cabeçalho.")
        else:
            print("Nenhum Set-Cookie encontrado ou falha na autenticação.")
            logger.error("Nenhum Set-Cookie encontrado ou falha na autenticação.")
            return None
    except Exception as e:
        #print(f"Erro ao obter cookie: {e}")
        logger.error(f"Erro ao obter cookie: {e}")
        return None
    finally:
        curl.close()

def get_with_cookie(url, cookie, xid_sensor):
    """Realiza uma requisição GET usando o cookie de autenticação."""
    buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.URL, url)
    curl.setopt(curl.WRITEFUNCTION, buffer.write)
    curl.setopt(curl.COOKIE, cookie)

    try:
        curl.perform()
        status_code = curl.getinfo(pycurl.RESPONSE_CODE)
        response_data = buffer.getvalue().decode('utf-8')

        print(f"Status Code GET: {status_code}")
        #print(f"Resposta bruta: {response_data}")

        if status_code != 200:
            print(f"Erro ao buscar dados do xid_sensor {xid_sensor}. Status: {status_code}")
            return None

        return json.loads(response_data) if response_data else None
    except json.JSONDecodeError:
        print("Erro ao decodificar JSON. Resposta vazia ou inválida.")
        return None
    except Exception as e:
        print(f"Erro na requisição GET: {e}")
        return None
    finally:
        curl.close()

def get_valid_cookie():
    """Verifica se o cookie armazenado ainda é válido, senão obtém um novo."""
    current_time = time.time()
    print(f"Tempo atual: {current_time} ({time.ctime(current_time)})")
    print(f"Tempo de expiração do cookie: {cookie_cache['expires_at']} ({time.ctime(cookie_cache['expires_at'])})")

    if cookie_cache["value"] and current_time < cookie_cache["expires_at"]:
        print(f"Usando cookie armazenado: {cookie_cache['value']}")
        return cookie_cache["value"]
    
    print("Cookie expirado ou inexistente. Renovando...")
    return get_cookie_from_url(AUTH_URL)

def get_json_data(xid_sensor):
    """Obtém os dados JSON apenas se o cookie for válido."""
    cookie = get_valid_cookie()
    if cookie:
        url_get_value = f"{URL_BASE}/Scada-LTS/api/point_value/getValue/{xid_sensor}"
        print(f"Requisição GET para: {url_get_value} com cookie {cookie}")
        response_json = get_with_cookie(url_get_value, cookie, xid_sensor)
        #print("response=", response_json)
        return response_json
    else:
        print("Falha ao buscar os dados do xid_sensor:", xid_sensor)
        logger.error(f"Falha ao buscar os dados do xid_sensor: {xid_sensor}")
        return None

# TESTE: 
'''
get_json_data("XIDSENS")
time.sleep(5)  # Espera 5 segundos
print("-------------------------------------------------------------------------")
get_json_data("XIDSENS2")  # Deve reutilizar o cookie
time.sleep(3605)  # Espera 1 hora + 5 segundos
print("-------------------------------------------------------------------------")
get_json_data("XIDSENS")  # Deve renovar o cookie

'''
# -------------------------------------------------------------
# Rotina de autenticação no SCADA-LTS
# -------------------------------------------------------------
def auth_ScadaLTS():
    if not username or not password:
        print("Erro: Credenciais de acesso ao SCADA-LTS não encontradas no arquivo .env")
        logger.error("Erro: Credenciais de acesso ao SCADA-LTS não encontradas no arquivo .env")
        return
    try:
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, f"{URL_BASE}/Scada-LTS/login.htm")
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
            c.URL, f"{URL_BASE}/Scada-LTS/dwr/call/plaincall/EmportDwr.importData.dwr")
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS, raw_data)
        c.setopt(c.COOKIEFILE, 'cookies')
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        c.close()
        response = buffer.getvalue().decode('utf-8')
        #print(response)
        print("send_data_to_scada", raw_data)
    except ConnectionError as e:
        logger.error(f"Erro ao enviar dados ao SCADA-LTS: {e}")

# -------------------------------------------------------------
# Função para importação de Datasources Modbus no SCADA-LTS
# -------------------------------------------------------------
def import_datasource_modbus(xid_equip, updatePeriodType, enabled, host, 
                          maxReadBitCount, maxReadRegisterCount, 
                          maxWriteRegisterCount, port, retries, timeout, updatePeriods):
    try:
        raw_data = (
                'callCount=1\n'
                'page=/Scada-LTS/import_project.htm\n'
                'httpSessionId=\n'
                'scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n'
                'c0-scriptName=EmportDwr\n'
                'c0-methodName=importData\n'
                'c0-id=0\n'
                'c0-param0=string:{"dataSources":[{"xid":"' +
                str(xid_equip) + '", '
                '"type":"MODBUS_IP", "alarmLevels":{"POINT_WRITE_EXCEPTION":"URGENT", '
                '"DATA_SOURCE_EXCEPTION":"URGENT", "POINT_READ_EXCEPTION":"URGENT"}, '
                '"updatePeriodType":"' + str(updatePeriodType) + '", '
                '"transportType":"TCP", '
                '"contiguousBatches":false, "createSlaveMonitorPoints":false, '
                '"createSocketMonitorPoint":false, '
                '"enabled":' + str(enabled).lower() + ', '
                '"encapsulated":false, '
                '"host":"' + str(host) + '", '
                f'"maxReadBitCount":{maxReadBitCount}, '
                f'"maxReadRegisterCount":{maxReadRegisterCount}, '
                f'"maxWriteRegisterCount":{maxWriteRegisterCount}, '
                '"name":"' + str(xid_equip) + '", '
                f'"port":{port}, '
                '"quantize":false, '
                f'"retries":{retries}, '
                f'"timeout":{timeout}, '
                f'"updatePeriods":{updatePeriods}'
                '}]}\n'
                'batchId=8\n'
            )
        return raw_data
    except ConnectionError as e:
        logger.error(f"Erro no import de datasource Modbus para SCADA-LTS")
        return None
    
def import_datapoint_modbus(xid_sensor, range, modbusDataType, additive, 
                            bit, multiplier, offset, slaveId,
                            xid_equip, enabled, nome):
        try:
            raw_data = (
                'callCount=1\n'
                'page=/Scada-LTS/import_project.htm\n'
                'httpSessionId=\n'
                'scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n'
                'c0-scriptName=EmportDwr\n'
                'c0-methodName=importData\n'
                'c0-id=0\n'
                'c0-param0=string:{"dataPoints":[{"xid":"' +
                str(xid_sensor) + '",'
                '"loggingType":"ON_CHANGE",'
                '"intervalLoggingPeriodType":"MINUTES",'
                '"intervalLoggingType":"INSTANT",'
                '"purgeType":"YEARS",'
                '"pointLocator":{"range":"' + str(range) + '",'
                '"modbusDataType":"' + str(modbusDataType) + '",'
                f'"additive":{additive},'
                f'"bit":{bit},'
                '"charset":"ASCII",'
                f'"multiplier":{multiplier},'
                f'"offset":{offset},'
                '"registerCount":0,"settableOverride":false,'
                f'"slaveId":{slaveId},'
                '"slaveMonitor":false,"socketMonitor":false},'
                '"eventDetectors":[],"engineeringUnits":"","purgeStrategy":"PERIOD",'
                '"chartColour":null,"chartRenderer":null,"dataSourceXid":"' +
                str(xid_equip) + '",'
                '"defaultCacheSize":1,"description":null,"deviceName":"' +
                str(xid_sensor) + '",'
                '"discardExtremeValues":false,"discardHighLimit":1.7976931348623157,'
                '"discardLowLimit":-1.7976931348623157,'
                '"enabled":' + str(enabled).lower() + ', '
                '"eventTextRenderer"'
                ':{"type":"EVENT_NONE"},"intervalLoggingPeriod":15,"name":"' +
                str(nome) + '","purgePeriod":1,'
                '"purgeValuesLimit":100,"textRenderer":{"type":"PLAIN","suffix":""},"tolerance":0}]}\n'
                'batchId=8\n'
            )
            return raw_data
        except ConnectionError as e:
            logger.error(f"Erro no import de datasource Modbus para SCADA-LTS")
            return None
        
def import_datapoint_modbus(xid_equip, eventsPeriodType, enabled, host, port,
                            rbePollPeriods, retries, slaveAddress, sourceAddress,
                            staticPollPeriods):
    try:
        raw_data = (
                'callCount=1\n'
                'page=/Scada-LTS/import_project.htm\n'
                'httpSessionId=\n'
                'scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n'
                'c0-scriptName=EmportDwr\n'
                'c0-methodName=importData\n'
                'c0-id=0\n'
                'c0-param0=string:{"dataSources":[{"xid":"' +
                str(xid_equip) + '",'
                '"type":"DNP3_IP",'
                '"alarmLevels":{"DATA_SOURCE_EXCEPTION":"URGENT","POINT_READ_EXCEPTION":"URGENT"},'
                '"eventsPeriodType":"' + str(eventsPeriodType) + '",'
                '"enabled":' + str(enabled).lower() +','
                '"host":"' + str(host) + '","name":"' +
                str(xid_equip) + '",'
                f'"port":{port},'
                '"quantize":false,'
                f'"rbePollPeriods":{rbePollPeriods},'
                f'"retries":{retries},'
                f'"slaveAddress":{slaveAddress},'
                f'"sourceAddress":{sourceAddress},'
                f'"staticPollPeriods":{staticPollPeriods},'
                f'"synchPeriods":30,'
                '"timeout":800}]}\n'
                'batchId=8\n'
            )
        return raw_data
    except ConnectionError as e:
        logger.error(f"Erro no import de datasource Modbus para SCADA-LTS")
        return None