import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Carrega variáveis do ambiente
load_dotenv()

def listar_coluna_xid(table_name: str):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )

        if connection.is_connected():
            cursor = connection.cursor()
            query = f"SELECT xid FROM `{table_name}`"
            cursor.execute(query)
            resultados = cursor.fetchall()

            print(f"\n[INFO] {len(resultados)} registro(s) encontrados na coluna 'xid' da tabela '{table_name}':\n")
            print("-" * 40)
            for row in resultados:
                print(row[0])

    except Error as e:
        if "Unknown column 'xid'" in str(e):
            print(f"[ERRO] A tabela '{table_name}' não possui a coluna 'xid'.")
        else:
            print(f"[ERRO] Falha ao acessar o MySQL: {e}")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n[INFO] Conexão com o banco encerrada.")

# Execução
if __name__ == "__main__":
    #abela = input("Informe o nome da tabela a ser consultada: ").strip()
    listar_coluna_xid("datasources")    
    listar_coluna_xid("datapoints")