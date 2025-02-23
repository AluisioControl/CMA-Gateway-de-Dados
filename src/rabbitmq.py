
import pika
import configparser
from logger import *

CONFIG_FILE = "config.ini"

# ********************************************************
# Variáveis oriundas do arquivo config.ini
# ********************************************************
def load_rabbitmq_config():
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
    config_vars = load_rabbitmq_config()
    return config_vars.get(var_name, None)

# -------------------------------------------------------------
# Função para verificação de conexão estabelecida com
# Broker rabbitmq
# -------------------------------------------------------------
def check_rabbitmq_connection():
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

# -------------------------------------------------------------
# Função para envio de mensagem MQTT
# Broker rabbitmq
#    Exchange = gateway.to.mqtt
#    |    Queues        |    Routing Keys   |
#    |    Sensor        |       sensor      |
#    |    Alarm         |       alarm       |
#    |    Diagnosis     |        auto       |
# -------------------------------------------------------------

def send_rabbitmq(caminho=str, topico=str, chave=str, payload=str):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        # print(connection)
        # print(connection)
        channel = connection.channel()
        # print("Queue: "+str(channel)+"\n")
        channel.queue_declare(queue=topico)
        # print("Topic: "+str(channel)+"\n")
        channel.basic_publish(
            exchange=caminho, routing_key=chave, body=payload)
        # print("Publish: "+str(channel)+"\n")
        connection.close()
        return True

    except pika.exceptions.AMQPConnectionError as e:
        print(f"Erro ao conectar ao RabbitMQ: {e}")
        logger.error(f"Erro ao conectar ao RabbitMQ: {e}")
        return False
