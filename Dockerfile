# it's offical so i'm using it + alpine so damn small
FROM python:2.7.15-alpine3.8

# copy the codebase
COPY . /worker-manager

# install docker-py and rabbitmq required packages
RUN pip install -r /worker-manager/requirements.txt

#set python to be unbuffered
ENV PYTHONUNBUFFERED=1

# run the worker-manger
WORKDIR /worker-manager
CMD [ "python", "/worker-manager/worker-manager.py" ]