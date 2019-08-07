# it's offical so i'm using it + alpine so damn small
FROM python:3.7.4-alpine3.10

# copy the codebase
COPY . /worker

# install required packages - requires build-base due to psutil GCC complier requirements
RUN apk add --no-cache build-base python3-dev linux-headers
RUN pip install -r /worker/requirements.txt

#set python to be unbuffered
ENV PYTHONUNBUFFERED=1

# run the worker-manger
WORKDIR /worker
CMD [ "python", "/worker/worker.py" ]