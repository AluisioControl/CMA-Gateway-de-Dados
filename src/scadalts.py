###############################################################
# scadalts.py
# ------------------------------------------------------------
# Arquivo de funções do Scada-LTS
# Author: Aluisio Cavalcante <aluisio@controlengenharia.eng.br>
# novembro de 2025
# TODOS OS DIREITOS RESERVADOS A CONTROL ENGENHARIA
# #############################################################

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

        #print(f"Status Code GET: {status_code}")
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




# -------------------------------------------------------------
# Rotina de autenticação no SCADA-LTS
# -------------------------------------------------------------
def auth_ScadaLTS():

    """
    Realiza a autenticação no SCADA-LTS com as credenciais definidas no arquivo .env.

    Caso as credenciais estejam vazias, não realiza a autenticação e retorna None.
    Caso haja um erro na conexão, registra o erro no log e retorna None.

    Caso a autenticação seja bem-sucedida, grava o cookie de sessão no arquivo 'cookies' e
    retorna None.
    """

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




def send_data_to_scada(raw_data):

    """
    Envia dados brutos para o SCADA-LTS via POST.

    Parâmetros:
    raw_data (str): dados brutos a serem enviados.

    Retorna None.

    Caso haja um erro na conexão, registra o erro no log e retorna None.
    """

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