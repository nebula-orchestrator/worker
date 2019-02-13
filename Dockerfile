# it's offical so i'm using it + alpine so damn small
FROM python:2.7.15-alpine3.9

# copy the codebase
COPY . /worker

# install required packages - requires build-base due to psutil GCC complier requirements
RUN apk add --no-cache build-base python2-dev linux-headers
RUN pip install -r /worker/requirements.txt

#set python to be unbuffered
ENV PYTHONUNBUFFERED=1

# run the worker-manger
WORKDIR /worker
CMD [ "python", "/worker/worker.py" ]