import uuid
from NebulaPythonSDK import Nebula
from functions.docker_engine.docker_engine import *
from functions.misc.server import *
from threading import Thread
from random import randint


# get setting from envvar with failover from config/conf.json file if envvar not set
# using skip rather then None so passing a None type will still pass a None value rather then assuming there should be
# default value thus allowing to have No value set where needed (like in the case of registry user\pass)
def get_conf_setting(setting, settings_json, default_value="skip"):
    try:
        setting_value = os.getenv(setting.upper(), settings_json.get(setting, default_value))
    except Exception as e:
        print >> sys.stderr, e
        print >> sys.stderr, "missing " + setting + " config setting"
        print("missing " + setting + " config setting")
        os._exit(2)
    if setting_value == "skip":
        print >> sys.stderr, "missing " + setting + " config setting"
        print("missing " + setting + " config setting")
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
def random_word():
    return str(uuid.uuid4()).replace('-', '')


# update\release\restart function
def restart_containers(app_json, force_pull=True):
    image_registry_name, image_name, version_name = split_container_name_version(app_json["docker_image"])
    # wait between zero to max_restart_wait_in_seconds seconds before rolling - avoids overloading backend
    time.sleep(randint(0, max_restart_wait_in_seconds))
    # pull image to speed up downtime between stop & start
    if force_pull is True:
        docker_socket.pull_image(image_name, version_tag=version_name)
    # stop running containers
    stop_containers(app_json)
    # start new containers
    start_containers(app_json, force_pull=False)
    return


# roll app function
def roll_containers(app_json, force_pull=True):
    image_registry_name, image_name, version_name = split_container_name_version(app_json["docker_image"])
    # wait between zero to max_restart_wait_in_seconds seconds before rolling - avoids overloading backend
    time.sleep(randint(0, max_restart_wait_in_seconds))
    # pull image to speed up downtime between stop & start
    if force_pull is True:
        docker_socket.pull_image(image_name, version_tag=version_name)
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
                    print("starting ports can only a list containing intgers or dicts - dropping worker")
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
def start_containers(app_json, force_pull=True):
    # list current containers
    split_container_name_version(app_json["docker_image"])
    containers_list = docker_socket.list_containers(app_json["app_name"])
    if len(containers_list) > 0:
        print("app already running so restarting rather then starting containers")
        restart_containers(app_json)
    elif app_json["running"] is True:
        image_registry_name, image_name, version_name = split_container_name_version(app_json["docker_image"])
        containers_needed = containers_required(app_json)
        # pull required image
        if force_pull is True:
            docker_socket.pull_image(image_name, version_tag=version_name)
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
                    print("starting ports can only a list containing intgers or dicts - dropping worker")
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


# prune unused images
def prune_images():
    docker_socket.prune_images()


# loop forever and in any case where a container healthcheck shows a container as unhealthy restart it
def restart_unhealthy_containers():
    try:
        while True:
            time.sleep(10)
            nebula_containers = docker_socket.list_containers()
            for nebula_container in nebula_containers:
                if docker_socket.check_container_healthy(nebula_container["Id"]) is False:
                    docker_socket.restart_container(nebula_container["Id"])
        print("stopping restart_unhealthy_containers thread")
    except Exception as e:
        print >> sys.stderr, e
        print("failed checking containers health")
        os._exit(2)


if __name__ == "__main__":
    # static variables
    RABBIT_RPC_QUEUE = "rabbit_api_rpc_queue"

    # read config file and config envvars at startup, order preference is envvar>config file>default value (if exists)
    if os.path.exists("config/conf.json"):
        print("reading config file")
        auth_file = json.load(open("config/conf.json"))
    else:
        print("config file not found - skipping reading it and checking if needed params are given from envvars")
        auth_file = {}
    print("reading config variables")
    nebula_manager_auth_user = get_conf_setting("nebula_manager_auth_user", auth_file, None)
    nebula_manager_auth_password = get_conf_setting("nebula_manager_auth_password", auth_file, None)
    nebula_manager_host = get_conf_setting("nebula_manager_host", auth_file, "127.0.0.1")
    nebula_manager_port = int(get_conf_setting("nebula_manager_port", auth_file, "80"))
    nebula_manager_protocol = get_conf_setting("nebula_manager_protocol", auth_file, "http")
    nebula_manager_request_timeout = int(get_conf_setting("nebula_manager_request_timeout", auth_file, "60"))
    nebula_manager_check_in_time = int(get_conf_setting("nebula_manager_check_in_time", auth_file, "30"))
    registry_auth_user = get_conf_setting("registry_auth_user", auth_file, None)
    registry_auth_password = get_conf_setting("registry_auth_password", auth_file, None)
    registry_host = get_conf_setting("registry_host", auth_file, "https://index.docker.io/v1/")
    max_restart_wait_in_seconds = int(get_conf_setting("max_restart_wait_in_seconds", auth_file, 0))
    rabbit_heartbeat = int(get_conf_setting("rabbit_heartbeat", auth_file, 3600))
    device_group = get_conf_setting("device_group", auth_file)

    # get number of cpu cores on host
    cpu_cores = get_number_of_cpu_cores()

    # work against docker socket
    docker_socket = DockerFunctions()

    # ensure default "nebula" named network exists
    docker_socket.create_docker_network("nebula", "bridge")

    # login to the docker registry - if no registry login details are configured will just print a message stating that
    docker_socket.registry_login(registry_host=registry_host, registry_user=registry_auth_user,
                                 registry_pass=registry_auth_password)

    # login to the nebula manager
    nebula_connection = Nebula(username=nebula_manager_auth_user, password=nebula_manager_auth_password,
                               host=nebula_manager_host, port=nebula_manager_port, protocol=nebula_manager_protocol,
                               request_timeout=nebula_manager_request_timeout)

    # stop all nebula managed containers on start to ensure a clean slate to work on
    stop_containers({"app_name": ""})

    local_device_group_info = nebula_connection.list_device_group_info(device_group)

    for nebula_app in local_device_group_info["reply"]["apps"]:
        start_containers(nebula_app)

    # open a thread which is in charge of restarting any containers which healthcheck shows them as unhealthy
    Thread(target=restart_unhealthy_containers).start()

    while True:
        time.sleep(nebula_manager_check_in_time)

        remote_device_group_info = nebula_connection.list_device_group_info(device_group)

        # TODO - for each app in the remote_device_group_info:

            # TODO - check if app exists in local_device_group_info:

                # TODO - if yes compare remote_device_group_info app_id to local_device_group_info app_id:

                    # TODO - if the remote is bigger then replace the app containers

                # TODO - if no create app

        # TODO - check if device_group_id in the remote_device_group_info is bigger then the in local_device_group_info:

            # TODO - if yes then check for any app that exists in the local_device_group_info and not in the
            #  remote_device_group_info

                # TODO - for each one found remove all app containers

        if remote_device_group_info["reply"]["prune_id"] > local_device_group_info["reply"]["prune_id"]:
            prune_images()

        local_device_group_info = remote_device_group_info