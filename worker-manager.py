import json, os, time, random, string, uuid
from functions.db_functions import *
from functions.rabbit_functions import *
from functions.docker_functions import *
from functions.server_functions import *
from bson.json_util import dumps, loads
from threading import Thread
from random import randint


# get setting from envvar with failover from conf.json file if envvar not set
def get_conf_setting(setting, settings_json):
    try:
        setting_value = os.getenv(setting.upper(), settings_json[setting])
        return setting_value
    except:
        print "missing " + setting + " config setting"
        os._exit(2)


# split container image name to the registry, image & version used with default of docker hub if registry not set.
def split_container_name_version(image_name):
    try:
        image_registry_name, image_name = image_name.rsplit("/", 1)
    except:
        image_registry_name = "registry.hub.docker.com/library"
    try:
        image_name, version_name = image_name.split(":")
    except:
        version_name = "latest"
    try:
        image_name = image_registry_name + "/" + image_name
    except:
        pass
    return image_registry_name, image_name, version_name


# used in rabbitmq queue name as it's partly random
def randomword():
    return str(uuid.uuid4()).replace('-', '')


# login to rabbit function
def rabbit_login():
    rabbit_connection = rabbit_connect(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                       rabbit_heartbeat)
    rabbit_connection_channel = rabbit_create_channel(rabbit_connection)
    return rabbit_connection_channel


# update\release\restart function
def restart_containers(app_json, registry_auth_user="", registry_auth_password="", registry_host=""):
    image_registry_name, image_name, version_name = split_container_name_version(app_json["docker_image"])
    # wait between zero to max_restart_wait_in_seconds seconds before rolling - avoids overloading backend
    time.sleep(randint(0, max_restart_wait_in_seconds))
    # pull image to speed up downtime between stop & start
    pull_image(image_name, version_tag=version_name, registry_user=registry_auth_user,
               registry_pass=registry_auth_password, registry_host=registry_host)
    # stop running containers
    stop_containers(app_json)
    # start new containers
    start_containers(app_json, True, registry_auth_user, registry_auth_password, registry_host)
    return


# roll app function
def roll_containers(app_json, registry_auth_user="", registry_auth_password="", registry_host=""):
    # TODO - get rolling restart module to work
    print "not yet implemented, do not use - will restart for the time being"
    restart_containers(app_json, registry_auth_user=registry_auth_user, registry_auth_password=registry_auth_password,
                       registry_host=registry_host)
    return


# stop app function
def stop_containers(app_json):
    # list current containers
    containers_list = list_containers(app_json["app_name"])
    # stop running containers
    threads = []
    for container in containers_list:
        t = Thread(target=stop_and_remove_container, args=(container["Id"],))
        threads.append(t)
        t.start()
    for z in threads:
        z.join()
    return


# start app function
def start_containers(app_json, no_pull=False, registry_auth_user="", registry_auth_password="", registry_host=""):
    # list current containers
    split_container_name_version(app_json["docker_image"])
    containers_list = list_containers(app_json["app_name"])
    if len(containers_list) > 0:
        print "app already running so restarting rather then starting containers"
        restart_containers(app_json)
    else:
        # find out how many containers needed
        image_registry_name, image_name, version_name = split_container_name_version(app_json["docker_image"])
        for scale_type, scale_amount in app_json["containers_per"].iteritems():
            if scale_type == "cpu":
                containers_needed = int(cpu_cores * scale_amount)
            elif scale_type == "server" or scale_type == "instance":
                containers_needed = int(scale_amount)
        # pull latest image
        if no_pull is False:
            pull_image(image_name, version_tag=version_name, registry_user=registry_auth_user,
                       registry_pass=registry_auth_password, registry_host=registry_host)
        # start new containers
        container_number = 1
        threads = []
        while container_number <= containers_needed:
            port_binds = dict()
            port_list = []
            for x in app_json["starting_ports"]:
                if isinstance(x, int):
                    port_binds[x] = x + container_number - 1
                    port_list.append(x)
                elif isinstance(x, dict):
                    for host_port, container_port in x.iteritems():
                        port_binds[int(container_port)] = int(host_port) + container_number - 1
                        port_list.append(container_port)
                else:
                    print "starting ports can only a list containing intgers or dicts - dropping worker-manager"
                    os._exit(2)
            t = Thread(target=run_container, args=(app_json["app_name"], app_json["app_name"] + str(container_number),
                                                   image_name, port_binds, port_list, app_json["env_vars"],
                                                   app_json["network_mode"], version_name, registry_auth_user,
                                                   registry_auth_password))
            threads.append(t)
            t.start()
            container_number = container_number + 1
        for y in threads:
            y.join()
        return


def rabbit_work_function(ch, method, properties, body):
    try:
        # check the message body to get the needed order
        app_json = loads(body)
        # if it's blank stop containers and kill worker-manger container
        if len(app_json) == 0:
            stop_containers(app_json)
            print "got a blank massage from rabbit - likely app wasn't created in nebula API yet, dropping container"
            os._exit(2)
        # elif it's stopped stop containers
        elif app_json["command"] == "stop":
            stop_containers(app_json)
        # if it's start start containers
        elif app_json["command"] == "start":
            start_containers(app_json, False, registry_auth_user, registry_auth_password, registry_host)
        # if it's roll rolling restart containers
        elif app_json["command"] == "roll":
            roll_containers(app_json, registry_auth_user, registry_auth_password, registry_host)
        # elif restart containers
        else:
            restart_containers(app_json, registry_auth_user, registry_auth_password, registry_host)
        # ack message
        rabbit_ack(ch, method)
    except pika.exceptions.ConnectionClosed:
        print "lost rabbitmq connection mid transfer - dropping container to be on the safe side"
        os._exit(2)


# recursive so it will always keep trying to reconnect to rabbit in case of any connection issues
def rabbit_recursive_connect(rabbit_channel, rabbit_work_function, rabbit_queue_name):
    try:
        rabbit_receive(rabbit_channel, rabbit_work_function, rabbit_queue_name)
    except pika.exceptions.ConnectionClosed:
        print "lost rabbitmq connection - reconnecting"
        rabbit_channel = rabbit_login()
        try:
            rabbit_bind_queue(rabbit_queue_name, rabbit_channel, str(app_name) + "_fanout")
            time.sleep(1)
        except pika.exceptions.ChannelClosed:
            print "queue no longer exists - can't guarantee order so dropping container"
            os._exit(2)
        rabbit_recursive_connect(rabbit_channel, rabbit_work_function, rabbit_queue_name)


def app_theard(theard_app_name):
    # connect to rabbit and create queue first thing at startup
    try:
        rabbit_channel = rabbit_login()
        rabbit_queue_name = str(theard_app_name) + "_" + randomword() + "_queue"
        rabbit_queue = rabbit_create_queue(rabbit_queue_name, rabbit_channel)
        rabbit_bind_queue(rabbit_queue_name, rabbit_channel, str(theard_app_name) + "_fanout")
    except:
        print "failed first rabbit connection, dropping container to be on the safe side"
        os._exit(2)

    # at startup connect to db, load newest app image and restart containers if configured to run
    mongo_collection = mongo_connect_get_app_data_disconnect(mongo_url, theard_app_name, schema_name="nebula")
    # check if app is set to running state
    if mongo_collection["running"] is True:
        # if answer is yes start it
        restart_containers(mongo_collection, registry_auth_user, registry_auth_password, registry_host)
    # start processing rabbit queue
    try:
        rabbit_recursive_connect(rabbit_channel, rabbit_work_function, rabbit_queue_name)
    except:
        print "rabbit connection failure - can't guarantee order so dropping container"
        os._exit(2)


# read config file and config envvars at startup
print "reading config variables"
auth_file = json.load(open("conf.json"))
registry_auth_user = get_conf_setting("registry_auth_user", auth_file)
registry_auth_password = get_conf_setting("registry_auth_password", auth_file)
registry_host = get_conf_setting("registry_host", auth_file)
rabbit_host = get_conf_setting("rabbit_host", auth_file)
rabbit_vhost = get_conf_setting("rabbit_vhost", auth_file)
rabbit_port = int(get_conf_setting("rabbit_port", auth_file))
rabbit_user = get_conf_setting("rabbit_user", auth_file)
rabbit_password = get_conf_setting("rabbit_password", auth_file)
mongo_url = get_conf_setting("mongo_url", auth_file)
schema_name = get_conf_setting("schema_name", auth_file)
max_restart_wait_in_seconds = int(get_conf_setting("max_restart_wait_in_seconds", auth_file))
rabbit_heartbeat = int(get_conf_setting("rabbit_heartbeat", auth_file))

# get the app name the worker manages
app_name_list = os.environ["APP_NAME"].split(",")

# get number of cpu cores on host
cpu_cores = get_number_of_cpu_cores()

# work against docker socket
cli = docker.APIClient(base_url='unix://var/run/docker.sock', version="auto")

# opens a thread for each app so they all listen to rabbit side by side for any changes
for app_name in app_name_list:
    Thread(target=app_theard, args=(app_name,)).start()
