import requests
import time
import BytesIO
import pycurl

# Configurações da API
base_url = "http://127.0.0.1:8080/Scada-LTS/api"  # Substitua pelo URL do SCADA-LTS
endpoint = "/point_value/getValue"  # Endpoint para buscar valores dos pontos
#api_token = "seu_token_aqui"  # Substitua pelo seu token de autenticação

def auth_ScadaLTS():
    base_url = "http://127.0.0.1:8080/Scada-LTS/api"  # Substitua pelo URL do SCADA-LTS
    endpoint = "/auth/admin/admin"  # Endpoint para buscar valores dos pontos

    url = f"{base_url}{endpoint}"
    print(url)

    try:
        response = requests.get(url)
        response.raise_for_status()  # Lança uma exceção para códigos de erro HTTP
        data = response.json()  # Parse do JSON retornado
        print(f"Autenticando usuario:")
        print(data)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao autenticar: {e}\n")

def auth2_ScadaLTS():
    
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'http://localhost:8080/Scada-LTS/login.htm')
    c.setopt(c.POST, 1)
    c.setopt(c.POSTFIELDS, 'username=admin&password=admin&submit=Login')
    c.setopt(c.COOKIEFILE, '')
    c.setopt(c.COOKIEJAR, 'cookies')
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    response = buffer.getvalue().decode('utf-8')
    print(response)
    
    print("AUTH SCADA")



def get_point_values(point_id):
    """
    Faz uma requisição GET para obter os valores de um ponto no SCADA-LTS.
    
    :param point_id: ID do ponto que deseja buscar os valores.
    """
    """
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    """

    headers = {
                "Accept": "application/json",
                #"Cookie": "JSESSIONID=28C962A6275969F5EAE13DD7C1AD4173"
                "Cookie": "JSESSIONID=8680F0F61FB48136DFCBA612A61B9ABD"
            }
    http_proxy  = "http://127.0.0.1:8080"
    https_proxy = "http://127.0.0.1:8080"

    proxyDict = {
                "http"  : http_proxy,
                "https" : https_proxy
                }

    url = f"{base_url}{endpoint}/{point_id}"
    print(url)
    
    try:
        response = requests.get(url, headers=headers, proxies=proxyDict)
        #response = requests.get(url).decode('utf-8')
        response.raise_for_status()  # Lança uma exceção para códigos de erro HTTP
        data = response.json()  # Parse do JSON retornado
        print(f"Dados do ponto {point_id}:")
        print(data + "\n")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter dados do ponto {point_id}: {e}\n")

        """"
        Erro ao autenticar: 
        HTTPConnectionPool(host='localhost', port=8080): Max retries exceeded with 
        url: /Scada-LTS/api/auth/:admin/:admin 
        (Caused by NewConnectionError('<urllib3.connection.HTTPConnection 
        object at 0x000002454311CD70>: 
        Failed to establish a new connection: 
        [WinError 10061] Nenhuma conexão pôde ser feita porque a máquina de destino as recusou ativamente'))
        Erro ao obter dados do ponto ggsdfg: 
        HTTPConnectionPool(host='localhost', port=8080): 
        Max retries exceeded with url: /Scada-LTS/api/point_value/getValue/point-values/:ggsdfg 
        (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x0000024543138690>: 
        Failed to establish a new connection: 
        [WinError 10061] Nenhuma conexão pôde ser feita porque a máquina de destino as recusou ativamente'))

        Scada-LTS online mas com usuario incorreto
        Autenticando usuario:
        False

        Autenticando usuario corretamente:
        True
        Erro ao obter dados do ponto DP_319182: 404 Client 
        Error:  for url: http://localhost:8080/Scada-LTS/api/point_value/getValue/point-values/:DP_319182

        No erro acima o data point está correto, porém o equipamento não está online.
        Testar agora no linux onde tem um equipamento onlne.
        
        """

if __name__ == "__main__":
    # ID do ponto que você deseja buscar (substitua pelo ID real)
    point_id = input("Digite o ID do ponto que deseja monitorar: ")
    interval = float(input("Digite o intervalo de tempo entre as requisições (em segundos): "))

    if interval <= 0:
        print("O intervalo deve ser maior que zero. Tente novamente.")
    else:
        print(f"Iniciando monitoramento do ponto {point_id} com intervalo de {interval} segundos...")
        try:
            while True:
                auth_ScadaLTS()
                get_point_values(point_id)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoramento encerrado pelo usuário.")
