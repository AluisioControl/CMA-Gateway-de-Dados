import requests

# Configurações do Scada-LTS
base_url = "http://localhost:8080/scada-lts/api"
username = "admin"  # Substitua pelo seu nome de usuário
password = "admin"  # Substitua pela sua senha

# 1. Obter o token de autenticação
def get_token():
    auth_url = f"{base_url}/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    try:
        response = requests.post(auth_url, json=payload)
        response.raise_for_status()  # Lança exceção se houver erro HTTP
        token = response.json().get("token")
        print(f"Token obtido: {token}")
        return token
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter o token: {e}")
        return None

# 2. Fazer um GET na API
def get_data(endpoint, token):
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {token}"
    }
    url = f"{base_url}/{endpoint}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lança exceção se houver erro HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {endpoint}: {e}")
        return None

# Fluxo principal
if __name__ == "__main__":
    token = get_token()
    if token:
        # Substitua 'devices' pelo endpoint desejado, como 'points' ou outros
        data = get_data("devices", token)
        if data:
            print("Dados obtidos:")
            print(data)