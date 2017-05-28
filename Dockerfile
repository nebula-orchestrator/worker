# it's offical so i'm using it + alpine so damn small
FROM python:2.7.12-alpine

# install docker-py and rabbitmq required packages
RUN pip install docker-py pika pymongo[tls]

# copy the codebase
COPY . /worker-manager

#set python to be unbuffered
ENV PYTHONUNBUFFERED=1

# run the worker-manger
WORKDIR /worker-manager
CMD [ "python", "/worker-manager/worker-manager.py" ]