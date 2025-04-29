import pika

credentials = pika.PlainCredentials('cma_gateway', 'cm@GTW')
connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost', 5672, '/', credentials)
)
channel = connection.channel()

channel.queue_declare(queue='Gateway', durable=True)
mensagem = '{"sensor": 23, "valor": 7.8, "data": "2025-04-29T09:15:00"}'
channel.basic_publish(
    exchange='',
    routing_key='Gateway',
    body=mensagem,
    properties=pika.BasicProperties(delivery_mode=2)  # mensagem persistente
)
print("📤 Mensagem enviada para a fila 'Gateway'")
connection.close()
