import configparser

CONFIG_FILE = "config.ini"

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

# ******************** RABBIT MQ *************************
# host, port, username, password, caminho, tópico, chave
# ********************************************************

host = config.get("config_rabbitmq", "host")
port = config.get("config_rabbitmq", "port")
user = config.get("config_rabbitmq", "user")
password = config.get("config_rabbitmq", "password")
caminho = config.get("config_rabbitmq", "caminho")
topico = config.get("config_rabbitmq", "topico")
chave = config.get("config_rabbitmq", "chave")

# DEBUG
print("******************** RABBIT MQ *************************")
print(f"host: {host}")
print(f"port: {port}")
print(f"user: {user}")
print(f"password: {password}")
print(f"topico: {topico}")
print(f"chave: {chave}")



# ******************* PLACA DE REDE**********************
# IP estático, Máscara, Gateway
# ********************************************************

ip = config.get("config_rede", "ip")
mascara = config.get("config_rede", "mascara")
gateway = config.get("config_rede", "gateway")

# DEBUG
print("******************** REDE *************************")
print(f"ip: {ip}")
print(f"mascara: {mascara}")
print(f"gateway: {gateway}")



# ******************* CMA GATEWAY **********************
# ID do CMA Gateway
# ********************************************************

cma_gtw_nome = config.get("config_cma_gateway", "nome")
addr_cma_web = config.get("config_cma_gateway", "addr_cma_web")

# DEBUG
print("******************** CMA GATEWAY *************************")
print(f"nome: {cma_gtw_nome}")
print(f"host: {addr_cma_web}")
