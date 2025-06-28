import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Carrega variáveis do ambiente
load_dotenv()

def listar_tabelas(cursor):
    cursor.execute("SHOW TABLES")
    return [linha[0] for linha in cursor.fetchall()]

def verificar_coluna(cursor, nome_tabela, coluna):
    cursor.execute(f"SHOW COLUMNS FROM `{nome_tabela}`")
    colunas = [linha[0] for linha in cursor.fetchall()]
    return coluna in colunas

def exibir_coluna_xid(cursor, nome_tabela):
    cursor.execute(f"SELECT xid FROM `{nome_tabela}`")
    resultados = cursor.fetchall()
    print(f"\n[INFO] {len(resultados)} registro(s) encontrados na coluna 'xid' da tabela '{nome_tabela}':\n")
    print("-" * 40)
    for linha in resultados:
        print(linha[0])

def main():
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

            tabelas = listar_tabelas(cursor)
            if not tabelas:
                print("[ERRO] Nenhuma tabela encontrada no banco de dados.")
                return

            print("\nTabelas disponíveis:")
            for i, nome in enumerate(tabelas, 1):
                print(f"{i}. {nome}")

            opcao = int(input("\nSelecione uma tabela pelo número: "))
            tabela_selecionada = tabelas[opcao - 1]

            if verificar_coluna(cursor, tabela_selecionada, 'xid'):
                exibir_coluna_xid(cursor, tabela_selecionada)
            else:
                print(f"[ERRO] A tabela '{tabela_selecionada}' não possui a coluna 'xid'.")

    except Error as e:
        print(f"[ERRO] Falha ao acessar o MySQL: {e}")

    except (ValueError, IndexError):
        print("[ERRO] Opção inválida.")

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n[INFO] Conexão com o banco encerrada.")

if __name__ == "__main__":
    main()
