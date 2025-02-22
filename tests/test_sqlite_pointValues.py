import sqlite3
import requests
import time

# Configurações da API
base_url = "http://192.168.0.66:8080//Scada-LTS/api"  # Substitua pelo URL do SCADA-LTS
endpoint = "/point_value/getValue/:point-values"  # Endpoint para buscar valores dos pontos
api_token = "seu_token_aqui"  # Substitua pelo seu token de autenticação

# Configuração do banco de dados SQLite
db_path = "seu_banco.sqlite"  # Substitua pelo caminho do seu arquivo SQLite

def fetch_xids_from_db():
    """
    Busca todos os XIDs na tabela `points` do banco de dados SQLite.
    
    :return: Lista de XIDs.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT xid FROM points")
        xids = [row[0] for row in cursor.fetchall()]
        conn.close()
        return xids
    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}")
        return []

def get_point_values(xid):
    """
    Faz uma requisição GET para obter os valores de um ponto no SCADA-LTS e exibe apenas o campo `value`.
    
    :param xid: XID do ponto que deseja buscar os valores.
    """
    headers = {
        "Authorization": f"Bearer {api_token}"
    }
    url = f"{base_url}{endpoint}/{xid}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lança uma exceção para códigos de erro HTTP
        data = response.json()  # Parse do JSON retornado
        
        # Busca o campo `value` no JSON retornado
        if "value" in data:
            value = data["value"]
            print(f"Valor do ponto {xid}: {value}")
        else:
            print(f"O campo `value` não foi encontrado no ponto {xid}. Dados recebidos: {data}")
    
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter dados do ponto {xid}: {e}")

if __name__ == "__main__":
    interval = float(input("Digite o intervalo de tempo entre as requisições (em segundos): "))

    if interval <= 0:
        print("O intervalo deve ser maior que zero. Tente novamente.")
    else:
        print(f"Iniciando monitoramento com intervalo de {interval} segundos...")
        try:
            while True:
                xids = fetch_xids_from_db()
                if not xids:
                    print("Nenhum XID encontrado no banco de dados. Encerrando monitoramento.")
                    break
                for xid in xids:
                    get_point_values(xid)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoramento encerrado pelo usuário.")
