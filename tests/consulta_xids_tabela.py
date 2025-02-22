from sqlalchemy import create_engine, select, inspect
from sqlalchemy.exc import SQLAlchemyError

def consultar_chaves_e_valores_com_select(nome_tabela, nome_chave, caminho_banco='sqlite:///banco.sqlite'):
    """
    Consulta e imprime todas as chaves únicas de uma coluna específica de uma tabela 
    e seus valores, iterando por todas as entradas da tabela, usando `select`.

    Parâmetros:
        nome_tabela (str): Nome da tabela no banco de dados.
        nome_chave (str): Nome da coluna que será usada como chave.
        caminho_banco (str): URI de conexão com o banco de dados SQLite. 
                             Padrão é 'sqlite:///banco.sqlite'.
    """
    try:
        # Criar o engine e conectar ao banco de dados
        engine = create_engine(caminho_banco)
        conexao = engine.connect()

        # Usar o inspetor para verificar as colunas da tabela
        inspetor = inspect(engine)
        colunas = [col['name'] for col in inspetor.get_columns(nome_tabela)]

        if nome_chave not in colunas:
            raise ValueError(f"A coluna '{nome_chave}' não existe na tabela '{nome_tabela}'.")

        # Consultar todas as chaves únicas da coluna
        consulta_chaves = select(nome_chave).distinct().select_from(nome_tabela)
        chaves = conexao.execute(consulta_chaves).fetchall()

        # Contar e imprimir as chaves
        print(f"A tabela '{nome_tabela}' possui {len(chaves)} chaves únicas na coluna '{nome_chave}':")
        for chave in chaves:
            print(f"Chave: {chave[0]}")

        # Iterar por toda a tabela e imprimir valores linha a linha
        consulta_todos = select("*").select_from(nome_tabela)
        resultados = conexao.execute(consulta_todos)

        print("\nValores de todas as linhas na tabela:")
        for linha in resultados:
            print(dict(linha))

    except SQLAlchemyError as e:
        print(f"Erro ao acessar o banco de dados: {e}")
    except ValueError as e:
        print(e)
    finally:
        # Fechar a conexão com o banco de dados
        if 'conexao' in locals():
            conexao.close()
