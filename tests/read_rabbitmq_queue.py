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
        try:
            mensagem_obj = json.loads(body.decode())
            mensagens.append(mensagem_obj)
            print(f",{json.dumps(mensagem_obj, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao decodificar mensagem: {e}")
    else:
        break

connection.close()

# Salvando no arquivo como JSON puro (sem strings escapadas)
with open('mensagens_gateway.json', 'w', encoding='utf-8') as f:
    json.dump(mensagens, f, indent=4, ensure_ascii=False)

print(f"\n📁 {len(mensagens)} mensagens salvas em 'mensagens_gateway.json'")

