#!/usr/bin/env python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost::15672'))
channel = connection.channel()

channel.queue_declare(queue='hello')

channel.basic_publish(exchange='',
                      routing_key='hello',
                      body='Hello World!')

print(" [x] Sent 'Hello World!'")

connection.close()

import pika

# Conexão com o broker RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()

# Declara a fila (precisa ser igual à usada no consumidor)
channel.queue_declare(queue="minha_fila")

# Envia uma mensagem
message = "Hello RabbitMQ!"
channel.basic_publish(exchange="", routing_key="minha_fila", body=message)
print(f"[x] Enviado: {message}")

connection.close()