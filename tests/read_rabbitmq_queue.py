import pika
import json

# Conexão ao RabbitMQ
credentials = pika.PlainCredentials('cma_gateway', 'cm@GTW')
connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost', 5672, '/', credentials)
)
channel = connection.channel()

# Nome da fila
fila = 'Gateway'
mensagens = []

print(f"🔄 Lendo mensagens da fila: {fila}...")

while True:
    method_frame, header_frame, body = channel.basic_get(queue=fila, auto_ack=True)
    if method_frame:
        mensagens.append(body.decode())
        print(f"✅ Mensagem recebida: {body.decode()}")
    else:
        break

connection.close()

# Salvando no arquivo
with open('mensagens_gateway.json', 'w') as f:
    json.dump(mensagens, f, indent=4)

print(f"\n📁 {len(mensagens)} mensagens salvas em 'mensagens_gateway.json'")
