###############################################################
# rabbitmq.py
# ------------------------------------------------------------
# Arquivo de funções do RabbitMQ
# Author: Aluisio Cavalcante <aluisio@controlengenharia.eng.br>
# novembro de 2025
# TODOS OS DIREITOS RESERVADOS A CONTROL ENGENHARIA
# #############################################################
import pika
import configparser

CONFIG_FILE = "config.ini"

def load_rabbitmq_config():

    """
    Carrega as variáveis de configuração do RabbitMQ do arquivo config.ini

    Returns:
        Um dicionário com as variáveis de configuração do RabbitMQ
    """

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    
    rabbitmq_vars = {
        "host": config.get("config_rabbitmq", "host", fallback=None),
        "port": config.get("config_rabbitmq", "port", fallback=None),
        "username": config.get("config_rabbitmq", "username", fallback=None),
        "password": config.get("config_rabbitmq", "password", fallback=None),
        "caminho": config.get("config_rabbitmq", "caminho", fallback=None),
        "topico": config.get("config_rabbitmq", "topico", fallback=None),
        "chave": config.get("config_rabbitmq", "chave", fallback=None)
    }
    
    return rabbitmq_vars


def get_rabbitmq_var(var_name):

    """
    Retorna o valor de uma variável de configuração do RabbitMQ.

    Args:
        var_name (str): O nome da variável de configuração do RabbitMQ.

    Returns:
        str: O valor da variável de configuração do RabbitMQ se existir, None caso contrário.
    """

    config_vars = load_rabbitmq_config()
    return config_vars.get(var_name, None)



def check_rabbitmq_connection():

    """
    Verifica se a conexão com o Broker RabbitMQ pode ser estabelecida.

    Esta função lê as variáveis de configuração do RabbitMQ e tenta
    estabelecer uma conexão com o Broker. Se a conexão for bem-sucedida,
    a função retorna True, caso contrário retorna False.

    Returns:
        bool: True se a conexão foi bem-sucedida, False caso contrário.
    """

    username = get_rabbitmq_var("username")
    password = get_rabbitmq_var("password")
    host = get_rabbitmq_var("host")
    port = get_rabbitmq_var("port")

    try:
        # Configurando as credenciais
        credentials = pika.PlainCredentials(username, password)

        # Configurando os parâmetros de conexão
        connection_params = pika.ConnectionParameters(
            host=host, port=port, credentials=credentials)

        # Tentando estabelecer a conexão
        connection = pika.BlockingConnection(connection_params)

        # Se chegou aqui, a conexão foi bem-sucedida
        print("Conexão com RabbitMQ foi bem-sucedida!")
        connection.close()  # Fechando a conexão
        return True

    except pika.exceptions.AMQPConnectionError as e:
        print(f"Erro ao conectar ao RabbitMQ: {e}")
        logger.error(f"Erro ao conectar ao RabbitMQ: {e}")
        return False



def send_rabbitmq(caminho=str, topico=str, chave=str, payload=str):

    """
    Envia uma mensagem ao RabbitMQ.

    Parameters
    ----------
    caminho : str
        Nome da exchange.
    topico : str
        Nome da queue.
    chave : str
        Chave de routing.
    payload : str
        Conteúdo da mensagem.

    Returns
    -------
        bool: True se a mensagem foi enviada com sucesso, False caso contrário.
    """

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue=topico)

        channel.basic_publish(
            exchange=caminho, routing_key=chave, body=payload)

        connection.close()
        return True

    except pika.exceptions.AMQPConnectionError as e:
        print(f"Erro ao conectar ao RabbitMQ: {e}")
        logger.error(f"Erro ao conectar ao RabbitMQ: {e}")
        return False
