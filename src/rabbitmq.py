###############################################################
# rabbitmq.py
# ------------------------------------------------------------
# Arquivo de funções do RabbitMQ
# Author: Aluisio Cavalcante <aluisio@controlengenharia.eng.br>
# novembro de 2025
# TODOS OS DIREITOS RESERVADOS A CONTROL ENGENHARIA
# #############################################################
import pika


from dotenv import load_dotenv
import os
from logger import *
# Carregando as variáveis de ambiente do arquivo .env
load_dotenv()

# Variáveis de configuração do rabbitmq
RABBIT_HOST=os.getenv("RABBIT_HOST")
RABBIT_PORT=os.getenv("RABBIT_PORT")
RABBIT_USER=os.getenv("RABBIT_USER")
RABBIT_PASS=os.getenv("RABBIT_PASS")
RABBIT_CAMINHO=os.getenv("RABBIT_CAMINHO")
RABBIT_TOPICO=os.getenv("RABBIT_TOPICO")
RABBIT_CHAVE=os.getenv("RABBIT_CHAVE")


def check_rabbitmq_connection():

    """
    Verifica se a conexão com o Broker RabbitMQ pode ser estabelecida.

    Esta função lê as variáveis de configuração do RabbitMQ e tenta
    estabelecer uma conexão com o Broker. Se a conexão for bem-sucedida,
    a função retorna True, caso contrário retorna False.

    Returns:
        bool: True se a conexão foi bem-sucedida, False caso contrário.
    """

    try:
        # Configurando as credenciais
        credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)

        # Configurando os parâmetros de conexão
        connection_params = pika.ConnectionParameters(
            host=RABBIT_HOST, port=RABBIT_PORT, credentials=credentials)

        # Tentando estabelecer a conexão
        connection = pika.BlockingConnection(connection_params)
        logger.info("Conexão com RabbitMQ foi bem-sucedida!")

        # Se chegou aqui, a conexão foi bem-sucedida
        print("Conexão com RabbitMQ foi bem-sucedida!")
        #connection.close()  # Fechando a conexão
        return connection

    except pika.exceptions.AMQPConnectionError as e:
        print(f"Erro ao checar conexão com RabbitMQ: {e}")
        logger.error(f"Erro ao checar conexão como RabbitMQ: {e}")
        
        return False



def send_rabbitmq(payload=str):

    """
    Envia uma mensagem ao RabbitMQ.

    Parameter
    ----------
    payload : str
        Conteúdo da mensagem.

    Returns
    -------
        bool: True se a mensagem foi enviada com sucesso, False caso contrário.
    """
    if payload == None:
        logger.warning("Tentativa de envio de payload vazio ao RabbitMQ.")
        print("Nenhum conteúdo para enviar ao RabbitMQ!")
        return False    
    try:
        credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
        # Configurando os parâmetros de conexão
        connection_params = pika.ConnectionParameters(
            host=RABBIT_HOST, port=RABBIT_PORT, credentials=credentials)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.queue_declare(queue=RABBIT_TOPICO)

        channel.basic_publish(
            exchange=RABBIT_CAMINHO, routing_key=RABBIT_CHAVE, body=payload)

        connection.close()
        logger.info(f"Payload enviado com sucesso para fila '{RABBIT_TOPICO}'.")
        return True

    except pika.exceptions.AMQPConnectionError as e:
        print(f"Erro ao enviar dados para ao RabbitMQ: {e}")
        logger.error(f"Erro ao enviar dados para ao RabbitMQ: {e}")
        return False
