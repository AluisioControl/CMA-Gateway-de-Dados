from datetime import datetime

timestamp = datetime.now().timestamp()
print(timestamp)

data_hora = datetime.fromtimestamp(timestamp)

# Formatando
formatado = data_hora.strftime("%d/%m/%Y %H:%M:%S")
print(formatado)

print("Nível subestação")

def fetch_name_value_pairs(table_class, field_name, xid):
    """
    Busca pares de valores das colunas 'nome' e 'valor' de uma tabela
    e retorna uma estrutura de dados no formato [{"nome": "valor"}, ...].

    Args:
        session (Session): Sessão do banco de dados SQLAlchemy.
        table_class: Classe ORM que representa a tabela.
        field_name (str): Nome da coluna usada como filtro.
        xid: Valor usado na condição WHERE.

    Returns:
        list[dict]: Lista de dicionários no formato {"nome": "valor"}.
    """
    # Montar a consulta para buscar 'nome' e 'valor'
    query = (
        select(table_class.__table__.c.nome, table_class.__table__.c.valor)
        .where(table_class.__table__.c[field_name] == xid)
    )
    
    # Executar a consulta e obter todos os resultados
    items = session.execute(query).fetchall()
    
    # Montar a estrutura de saída como lista de dicionários
    result = [item[0], item[1] for item in items if item[0] and item[1]]
    
    return result