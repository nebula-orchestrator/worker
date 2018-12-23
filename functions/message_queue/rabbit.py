import pika


# connect to rabbit function
def rabbit_connect(rabbit_user, rabbit_pass, rabbit_host, rabbit_port, rabbit_virtual_host, rabbit_heartbeat):
    credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbit_host, rabbit_port, rabbit_virtual_host,
                                                                   credentials, heartbeat=rabbit_heartbeat))
    return connection


# close connection to rabbit function
def rabbit_close(rabbit_connection):
    rabbit_connection.close()
    return None


# create channel
def rabbit_create_channel(rabbit_connection):
    channel = rabbit_connection.channel()
    return channel


# create exchange
def rabbit_create_exchange(rabbit_channel, exchange_name):
    rabbit_channel.exchange_declare(exchange=exchange_name, exchange_type='fanout', durable=True)
    return None


# send message
def rabbit_send(rabbit_channel, exchange_name, rabbit_send_message):
    rabbit_channel.basic_publish(exchange=exchange_name, routing_key='', body=rabbit_send_message)
    return None


# receive message
def rabbit_receive(rabbit_receive_channel, rabbit_work_function, rabbit_receive_queue):
    rabbit_receive_channel.basic_consume(rabbit_work_function, queue=rabbit_receive_queue)
    rabbit_receive_channel.start_consuming()
    return None


# ack message
def rabbit_ack(rabbit_ack_channel, rabbit_ack_method):
    rabbit_ack_channel.basic_ack(delivery_tag=rabbit_ack_method.delivery_tag)
    return None


# create queue
def rabbit_create_queue(rabbit_queue_name, rabbit_channel):
    created_queue = rabbit_channel.queue_declare(queue=rabbit_queue_name, arguments={"x-expires": 300000})
    return created_queue


# bind queue to exchange
def rabbit_bind_queue(rabbit_bind_queue_name, rabbit_bind_channel, rabbit_bind_exchange):
    rabbit_bind_channel.queue_bind(exchange=rabbit_bind_exchange, queue=rabbit_bind_queue_name)
    return None


# get the current app config via RabbitMQ direct reply to at boot, also creates it's own connection & closes it
def rabbit_connect_get_app_data_disconnect(app_name, rabbit_user, rabbit_pass, rabbit_host, rabbit_port,
                                           rabbit_virtual_host, rabbit_heartbeat, rpc_queue, intial_start):
    rpc_connection = rabbit_connect(rabbit_user, rabbit_pass, rabbit_host, rabbit_port, rabbit_virtual_host,
                                    rabbit_heartbeat)
    rpc_channel = rabbit_create_channel(rpc_connection)
    rpc_channel.basic_consume(intial_start, queue='amq.rabbitmq.reply-to', no_ack=True)
    rpc_channel.basic_publish(exchange='', routing_key=rpc_queue, body=app_name,
                              properties=pika.BasicProperties(reply_to='amq.rabbitmq.reply-to'))
    rpc_channel.start_consuming()
    rabbit_close(rpc_connection)
