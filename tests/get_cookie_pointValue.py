import pycurl
from io import BytesIO
import json

def get_cookie_from_url(url):
    """
    Faz um GET na URL fornecida e retorna o valor do cookie obtido.
    """
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
    finally:
        curl.close()

def get_with_cookie(url, cookie):
    """
    Faz um GET na URL fornecida usando o cookie e retorna o JSON da resposta.
    """
    buffer = BytesIO()
    curl = pycurl.Curl()
    curl.setopt(curl.URL, url)
    curl.setopt(curl.WRITEFUNCTION, buffer.write)
    curl.setopt(curl.COOKIE, cookie)  # Define o cookie

    try:
        curl.perform()
        response = buffer.getvalue().decode('utf-8')
        return json.loads(response)
    finally:
        curl.close()

def parse_json_response(json_response, key):
    """
    Faz o parse de um JSON e retorna o valor associado a uma chave fornecida pelo usuário.
    
    :param json_response: O JSON retornado da função `get_with_cookie`.
    :param key: A chave cujo valor o usuário deseja extrair.
    :return: O valor associado à chave, ou uma mensagem de erro se a chave não existir.
    """
    try:
        if key in json_response:
            return json_response[key]
        else:
            return f"Chave '{key}' não encontrada no JSON."
    except Exception as e:
        return f"Erro ao processar o JSON: {e}"

# Exemplo de uso:
if __name__ == "__main__":
    test_url = "http://localhost:8080/Scada-LTS/api/auth/admin/admin"  # URL que define um cookie
    cookie = get_cookie_from_url(test_url)

    print("Cookie obtido:", cookie)

    if cookie:
        response_json = get_with_cookie("http://localhost:8080/Scada-LTS/api/point_value/getValue/DP_319182", cookie)
        #print("Resposta JSON:", response_json)

        # Extrair um valor do JSON
        key = "Value"  # Alterar conforme necessário
        extracted_value = parse_json_response(response_json, key)
        print(f"Valor extraído para a chave '{key}':", extracted_value)
