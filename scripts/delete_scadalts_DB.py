import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Carrega variáveis do .env
load_dotenv()

def delete_all_rows(table_name: str):
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
            delete_query = f"DELETE FROM `{table_name}`"
            cursor.execute(delete_query)
            connection.commit()
            print(f"[INFO] Todos os registros da tabela '{table_name}' foram removidos com sucesso.")

    except Error as e:
        print(f"[ERRO] Falha ao conectar ou executar comando no MySQL: {e}")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("[INFO] Conexão com o MySQL encerrada.")

# Execução
if __name__ == "__main__":
    #tabela = input("Informe o nome da tabela a ser limpa: ").strip()
    delete_all_rows("datapoints")
    delete_all_rows("datasources")
