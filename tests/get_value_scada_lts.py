import requests
import json


def reads_json_data(json_data):
    parsed_data = json_data.json()
    return parsed_data["value"]

# Configurações
login = "http://localhost:8080/Scada-LTS/api/auth/admin/admin"
url = "http://localhost:8080/Scada-LTS/api/point_value/getValue/DP_480034"
#url = "http://localhost:8080/Scada-LTS/api/datasource/getAll"

headers = {
    "Accept": "application/json",
    "Cookie": "JSESSIONID=43A10CD6F83295BA01B7798BA87C9D93"
    #"Cookie": "JSESSIONID=8680F0F61FB48136DFCBA612A61B9ABD"
}

# Requisição GET
auth = requests.get(login, headers=headers)

if auth.status_code == 200:
    print("Resposta JSON:", auth.json())
else:
    print(f"Erro {auth.status_code}: {auth.text}")

response = requests.get(url, headers=headers)

# Verifica o status e exibe o resultado
if response.status_code == 200:
    #print("Resposta JSON:", response.json())
    value = reads_json_data(response)
    print("Value: " + str(value))
else:
    print(f"Erro {response.status_code}: {response.text}")
