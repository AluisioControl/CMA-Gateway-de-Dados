import pycurl
import json
from io import BytesIO
import time
import re

AUTH_URL = "http://localhost:8080/Scada-LTS/api/auth/admin/admin"

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
        print(f"Cabeçalhos recebidos:\n{headers}")

        cookies = [line for line in headers if 'Set-Cookie' in line]
        
        if status_code == 200 and cookies:
            print(f"Cookies brutos encontrados: {cookies}")

            match = re.search(r"Set-Cookie:\s*([^;]+)", cookies[0], re.IGNORECASE)
            if match:
                cookie = match.group(1)
                cookie_cache["value"] = cookie
                cookie_cache["expires_at"] = time.time() + 3600  # 1 hora

                print(f"Novo cookie armazenado: {cookie_cache['value']}, expira em {cookie_cache['expires_at']} ({time.ctime(cookie_cache['expires_at'])})")
                return cookie
            else:
                print("Erro ao extrair o cookie do cabeçalho.")
        else:
            print("Nenhum Set-Cookie encontrado ou falha na autenticação.")
            return None
    except Exception as e:
        print(f"Erro ao obter cookie: {e}")
        return None
    finally:
        curl.close()


def get_with_cookie(url, cookie):
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
            print(f"Erro ao buscar dados. Status: {status_code}")
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
        url_get_value = f"http://localhost:8080/Scada-LTS/api/point_value/getValue/{xid_sensor}"
        print(f"Requisição GET para: {url_get_value} com cookie {cookie}")
        response_json = get_with_cookie(url_get_value, cookie)
        print("response=", response_json)
    else:
        print("Falha ao obter o cookie, não foi possível buscar os dados.")


# TESTE: 
get_json_data("XIDSENS")
time.sleep(5)  # Espera 5 segundos
print("-------------------------------------------------------------------------")
get_json_data("XIDSENS2")  # Deve reutilizar o cookie
time.sleep(3605)  # Espera 1 hora + 5 segundos
print("-------------------------------------------------------------------------")
get_json_data("XIDSENS")  # Deve renovar o cookie

#JSESSIONID=4C62C86BFBE77226CA763EFE164EE56D