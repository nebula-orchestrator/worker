import json, os, time, random, string, uuid, sys
from functions.rabbit_functions import *
from functions.docker_functions import *
from functions.server_functions import *
from threading import Thread
from random import randint


# get setting from envvar with failover from conf.json file if envvar not set
# using skip rather then None so passing a None type will still pass a None value rather then assuming there should be
# default value thus allowing to have No value set where needed (like in the case of registry user\pass)
def get_conf_setting(setting, settings_json, default_value="skip"):
    try:
        setting_value = os.getenv(setting.upper(), settings_json.get(setting, default_value))
    except Exception as e:
        print >> sys.stderr, "missing " + setting + " config setting"
        print "missing " + setting + " config setting"
        os._exit(2)
    if setting_value == "skip":
        print >> sys.stderr, "missing " + setting + " config setting"
        print "missing " + setting + " config setting"
        os._exit(2)
    return setting_value


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
def rabbit_login(rabbit_login_user, rabbit_login_password, rabbit_login_host, rabbit_login_port, rabbit_login_vhost,
                 rabbit_login_heartbeat):
    rabbit_connection = rabbit_connect(rabbit_login_user, rabbit_login_password, rabbit_login_host, rabbit_login_port,
                                       rabbit_login_vhost, rabbit_login_heartbeat)
    rabbit_connection_channel = rabbit_create_channel(rabbit_connection)
    return rabbit_connection_channel


# update\release\restart function
def restart_containers(app_json, registry_auth_user="skip", registry_auth_password="skip", registry_host=""):
    image_registry_name, image_name, version_name = split_container_name_version(app_json["docker_image"])
    # wait between zero to max_restart_wait_in_seconds seconds before rolling - avoids overloading backend
    time.sleep(randint(0, max_restart_wait_in_seconds))
    # pull image to speed up downtime between stop & start
    docker_socket.pull_image(image_name, version_tag=version_name, registry_user=registry_auth_user,
                             registry_pass=registry_auth_password, registry_host=registry_host)
    # stop running containers
    stop_containers(app_json)
    # start new containers
    start_containers(app_json, True, registry_auth_user, registry_auth_password, registry_host)
    return


# roll app function
def roll_containers(app_json, registry_auth_user="skip", registry_auth_password="skip", registry_host=""):
    image_registry_name, image_name, version_name = split_container_name_version(app_json["docker_image"])
    # wait between zero to max_restart_wait_in_seconds seconds before rolling - avoids overloading backend
    time.sleep(randint(0, max_restart_wait_in_seconds))
    # pull image to speed up downtime between stop & start
    docker_socket.pull_image(image_name, version_tag=version_name, registry_user=registry_auth_user,
                             registry_pass=registry_auth_password, registry_host=registry_host)
    # list current containers
    containers_list = docker_socket.list_containers(app_json["app_name"])
    # roll each container in turn - not threaded as the order is important when rolling
    containers_needed = containers_required(app_json)
    for idx, container in enumerate(sorted(containers_list, key=lambda k: k['Names'][0])):
        docker_socket.stop_and_remove_container(container["Id"])
        if idx < containers_needed:
            port_binds = dict()
            port_list = []
            for x in app_json["starting_ports"]:
                if isinstance(x, int):
                    port_binds[x] = x + idx
                    port_list.append(x)
                elif isinstance(x, dict):
                    for host_port, container_port in x.iteritems():
                        port_binds[int(container_port)] = int(host_port) + idx
                        port_list.append(container_port)
                else:
                    print "starting ports can only a list containing intgers or dicts - dropping worker-manager"
                    os._exit(2)
            docker_socket.run_container(app_json["app_name"], app_json["app_name"] + "-" + str(idx + 1), image_name,
                                        port_binds, port_list, app_json["env_vars"], version_name,
                                        app_json["volumes"], app_json["devices"], app_json["privileged"],
                                        app_json["networks"])
            # wait 5 seconds between container rolls to give each container time to start fully
            time.sleep(5)
    return


# stop app function
def stop_containers(app_json):
    # list current containers
    containers_list = docker_socket.list_containers(app_json["app_name"])
    # stop running containers
    threads = []
    for container in containers_list:
        t = Thread(target=docker_socket.stop_and_remove_container, args=(container["Id"],))
        threads.append(t)
        t.start()
    for z in threads:
        z.join()
    return


# start app function
def start_containers(app_json, no_pull=False, registry_auth_user=None, registry_auth_password=None, registry_host=""):
    # list current containers
    split_container_name_version(app_json["docker_image"])
    containers_list = docker_socket.list_containers(app_json["app_name"])
    if len(containers_list) > 0:
        print "app already running so restarting rather then starting containers"
        restart_containers(app_json, registry_auth_user, registry_auth_password, registry_host)
    elif app_json["running"] is True:
        image_registry_name, image_name, version_name = split_container_name_version(app_json["docker_image"])
        containers_needed = containers_required(app_json)
        # pull latest image
        if no_pull is False:
            docker_socket.pull_image(image_name, version_tag=version_name, registry_user=registry_auth_user,
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
            t = Thread(target=docker_socket.run_container, args=(app_json["app_name"], app_json["app_name"] + "-" +
                                                                 str(container_number), image_name, port_binds,
                                                                 port_list, app_json["env_vars"], version_name,
                                                                 app_json["volumes"], app_json["devices"],
                                                                 app_json["privileged"], app_json["networks"]))
            threads.append(t)
            t.start()
            container_number = container_number + 1
        for y in threads:
            y.join()
        return


# figure out how many containers are needed
def containers_required(app_json):
    for scale_type, scale_amount in app_json["containers_per"].iteritems():
        if scale_type == "cpu":
            containers_needed = int(cpu_cores * scale_amount)
        elif scale_type == "server" or scale_type == "instance":
            containers_needed = int(scale_amount)
    return containers_needed


def rabbit_work_function(ch, method, properties, body):
    try:
        # check the message body to get the needed order
        app_json = json.loads(body)
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
    except pika.exceptions.ConnectionClosed as e:
        print >> sys.stderr, e
        print "lost rabbitmq connection mid transfer - dropping container to be on the safe side"
        os._exit(2)


# recursive so it will always keep trying to reconnect to rabbit in case of any connection issues, this avoids killing
# the worker-manager container on every tiny network hiccup that on distributed systems at scale is common, the
# worker-manager container will be killed if enough time has passed for it's RabbitMQ queue has deleted itself which
# by default happens after 5 minutes without connection
def rabbit_recursive_connect(rabbit_channel, rabbit_work_function, rabbit_queue_name):
    try:
        rabbit_receive(rabbit_channel, rabbit_work_function, rabbit_queue_name)
    except pika.exceptions.ConnectionClosed:
        print "lost rabbitmq connection - reconnecting"
        rabbit_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                      rabbit_heartbeat)
        try:
            rabbit_create_exchange(rabbit_channel, app_name + "_fanout")
            rabbit_bind_queue(rabbit_queue_name, rabbit_channel, str(app_name) + "_fanout")
            time.sleep(1)
        except pika.exceptions.ChannelClosed as e:
            print >> sys.stderr, e
            print "queue no longer exists - can't guarantee order so dropping container"
            os._exit(2)
        rabbit_recursive_connect(rabbit_channel, rabbit_work_function, rabbit_queue_name)


# loop forever and in any case where a container healthcheck shows a container as unhealthy restart it
def restart_unhealthy_containers():
    try:
        while True:
            time.sleep(5)
            nebula_containers = docker_socket.list_containers()
            for nebula_container in nebula_containers:
                if docker_socket.check_container_healthy(nebula_container["Id"]) is False:
                    docker_socket.restart_container(nebula_container["Id"])
    except Exception as e:
        print >> sys.stderr, e
        print "failed checking containers health"
        os._exit(2)


# the thread which manages each individual app
def app_thread(thread_app_name):
    # connect to rabbit and create queue first thing at startup
    try:
        rabbit_channel = rabbit_login(rabbit_user, rabbit_password, rabbit_host, rabbit_port, rabbit_vhost,
                                      rabbit_heartbeat)
        rabbit_queue_name = str(thread_app_name) + "_" + randomword() + "_queue"
        rabbit_queue = rabbit_create_queue(rabbit_queue_name, rabbit_channel)
        rabbit_bind_queue(rabbit_queue_name, rabbit_channel, str(thread_app_name) + "_fanout")
    except Exception as e:
        print >> sys.stderr, e
        print "failed first rabbit connection, dropping container to be on the safe side, check to make sure that " \
              "your rabbit login details are configured correctly and that the rabbit exchange of the tasks this " \
              "nebula worker-manager is set to manage didn't somehow got deleted (or that the nebula app never got " \
              "created in the first place)"
        os._exit(2)

    # at startup get newest app configuration and restart containers if configured to run
    try:
        print "attempting to get initial app config for " + str(thread_app_name) + " from RabbitMQ RPC direct_reply_to"
        rabbit_connect_get_app_data_disconnect(thread_app_name, rabbit_user, rabbit_password, rabbit_host, rabbit_port,
                                               rabbit_vhost, rabbit_heartbeat, RABBIT_RPC_QUEUE, initial_start)
    except Exception as e:
        print >> sys.stderr, e
        print "failed first rabbit connection, dropping container to be on the safe side, check to make sure that " \
              "your rabbit login details are configured correctly and that the rabbit exchange of the tasks this " \
              "nebula worker-manager is set to manage didn't somehow got deleted (or that the nebula app never got " \
              "created in the first place)"
        os._exit(2)

    # start processing rabbit queue, the reasoning behind the create queue -> direct_reply_to-> start processing queue
    # flow is that it ensures that even if a message is sent to the queue changing the app configuration it will be
    # processed at the correct order.
    try:
        rabbit_recursive_connect(rabbit_channel, rabbit_work_function, rabbit_queue_name)
    except Exception as e:
        print >> sys.stderr, e
        print "rabbit connection failure - can't guarantee order so dropping container"
        os._exit(2)


# this function gets the reply from the RabbitMQ direct_reply_to RPC queue upon the worker initial boot & restarts the
# containers if they are configured to be in the running state
def initial_start(ch, method_frame, properties, body):
    try:
        initial_app_name = json.dumps(json.loads(body)["app_name"])
        print "got initial app configuration from RabbitMQ RPC direct_reply_to for app: " + initial_app_name
        initial_app_configuration = json.loads(body)
        # check if app is set to running state
        if initial_app_configuration["running"] is True:
            # if answer is yes start it
            restart_containers(initial_app_configuration, registry_auth_user, registry_auth_password, registry_host)
        else:
            print "app " + initial_app_name + " \"running\" state is false, stopping any existing containers " \
                                              "belonging to " + initial_app_name
            stop_containers(initial_app_configuration)
    except Exception as e:
        print >> sys.stderr, e
        print "failed first rabbit connection, dropping container to be on the safe side, check to make sure that " \
              "your rabbit login details are configured correctly and that the rabbit exchange of the tasks this " \
              "nebula worker-manager is set to manage didn't somehow got deleted (or that the nebula app never got " \
              "created in the first place)"
        os._exit(2)
    ch.close()


if __name__ == "__main__":
    # static variables
    RABBIT_RPC_QUEUE = "rabbit_api_rpc_queue"

    # read config file and config envvars at startup, order preference is envvar>config file>default value (if exists)
    print "reading config variables"
    auth_file = json.load(open("conf.json"))
    registry_auth_user = get_conf_setting("registry_auth_user", auth_file, None)
    registry_auth_password = get_conf_setting("registry_auth_password", auth_file, None)
    registry_host = get_conf_setting("registry_host", auth_file, "https://index.docker.io/v1/")
    rabbit_host = get_conf_setting("rabbit_host", auth_file)
    rabbit_vhost = get_conf_setting("rabbit_vhost", auth_file, "/")
    rabbit_port = int(get_conf_setting("rabbit_port", auth_file, 5672))
    rabbit_user = get_conf_setting("rabbit_user", auth_file)
    rabbit_password = get_conf_setting("rabbit_password", auth_file)
    max_restart_wait_in_seconds = int(get_conf_setting("max_restart_wait_in_seconds", auth_file, 0))
    rabbit_heartbeat = int(get_conf_setting("rabbit_heartbeat", auth_file, 3600))

    # get the app name the worker manages
    app_name_list = os.environ["APP_NAME"].split(",")

    # get number of cpu cores on host
    cpu_cores = get_number_of_cpu_cores()

    # work against docker socket
    docker_socket = DockerFunctions()

    # ensure default "nebula" named network exists
    docker_socket.create_docker_network("nebula", "bridge")

    # opens a thread for each app so they all listen to rabbit side by side for any changes
    for app_name in app_name_list:
        Thread(target=app_thread, args=(app_name,)).start()

    # open a thread which is in charge of restarting any containers which healthcheck shows them as unhealthy
    Thread(target=restart_unhealthy_containers).start()
