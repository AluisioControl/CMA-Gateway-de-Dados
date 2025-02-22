import requests
import time

# Configurações
login = "http://localhost:8080/Scada-LTS/api/auth/admin/admin"
url = "http://localhost:8080/Scada-LTS/api/point_value/getValue/DP_480034"
#url = "http://localhost:8080/Scada-LTS/api/datasource/getAll"

flag = False

def reads_json_data(json_data, value):
    parsed_data = json_data.json()
    return parsed_data[value]

def get_new_cookie(url):

    try:
        # Faz a requisição POST para autenticação
        response = requests.get(url)        
        # Verifica se a autenticação foi bem-sucedida
        if response.status_code == 200:
            # Obtém o cookie do cabeçalho 'Set-Cookie'
            #cookie = response.cookies.get_dict()
            session_id = response.cookies.get('JSESSIONID')
            #print("Novo cookie obtido:", cookie)
            print("Novo cookie obtido:", session_id)
            return session_id
        else:
            print(f"Falha na autenticação. Status code: {response.status_code}")
            return 1
    except requests.RequestException as e:
        print("Erro ao obter o cookie:", e)
        return 1


def try_auth():
    response = requests.get(login)
    # Verifica o status e exibe o resultado
    try:
        if response.status_code == 200:
            print("Auth response: ", response.json())
        else:
            print(f"Erro {response.status_code}: {response.text}")
    except requests.RequestException as e:
        print("Erro ao estabelecer conexão:", e)
        return None

def get_point_Value(xid, cookie):
        
        headers = {
        "Accept": "application/json",
        "Cookie": "JSESSIONID=" + str(cookie)
        }
        
        url = "http://localhost:8080/Scada-LTS/api/point_value/getValue/"+ str(xid)
        print(url)
        response = requests.get(url, headers=headers)

        try:
            if response.status_code == 200:
                #print("GET response: ", response.json())
                print("Value:",reads_json_data(response, "value"))
            else:
                print(f"Erro {response.status_code}: {response.text}")
        except requests.RequestException as e:
                print("Erro ao estabelecer conexão:", e)
                return None


Cookie = get_new_cookie("http://localhost:8080/Scada-LTS/api/auth/admin/admin")

try:    
    if Cookie != 1:  
        headers = {
        "Accept": "application/json",
        "Cookie": "JSESSIONID=" + str(Cookie)
        }
        auth = requests.get(login, headers=headers)
        print(auth)
        flag = True
    else:
        print("Erro na autenticação")
        flag = False
except requests.exceptions:
    print("erro")
"""
if flag == True:
    try_auth()
else:
    print("Erro de autencicação")
"""


while True:
        get_point_Value("DP_319182", Cookie)
        time.sleep(10)


