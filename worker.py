from NebulaPythonSDK import Nebula
from functions.reporting.reporting import *
from functions.reporting.kafka import *
from functions.docker_engine.docker_engine import *
from functions.misc.server import *
from functions.misc.cron_schedule import *
from threading import Thread
from random import randint
from retrying import retry
from parse_it import ParseIt
import os, sys, time


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


# update\release\restart function
def restart_containers(app_json, force_pull=True):
    image_registry_name, image_name, version_name = split_container_name_version(app_json["docker_image"])
    # wait between zero to max_restart_wait_in_seconds seconds before rolling - avoids roaring horde of the registry
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
    # wait between zero to max_restart_wait_in_seconds seconds before rolling - avoids roaring horde of the registry
    time.sleep(randint(0, max_restart_wait_in_seconds))
    # pull image to speed up downtime between stop & start
    if force_pull is True:
        docker_socket.pull_image(image_name, version_tag=version_name)
    # list current containers
    containers_list = docker_socket.list_containers(app_json["app_name"], container_type="app")
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
                    for host_port, container_port in x.items():
                        port_binds[int(container_port)] = int(host_port) + idx
                        port_list.append(container_port)
                else:
                    print("starting ports can only a list containing intgers or dicts - dropping worker")
                    os._exit(2)
            docker_socket.run_container(app_json["app_name"], app_json["app_name"] + "-" + str(idx + 1), image_name,
                                        port_binds, port_list, app_json["env_vars"], version_name, app_json["volumes"],
                                        app_json["devices"], app_json["privileged"], app_json["networks"],
                                        "unless-stopped")
            # wait 5 seconds between container rolls to give each container time to start fully
            time.sleep(5)


# stop app function
def stop_containers(app_json, container_type="app"):
    # list current containers
    containers_list = docker_socket.list_containers(app_json["app_name"], container_type=container_type,
                                                    show_all_containers=True)
    # stop running containers
    threads = []
    for container in containers_list:
        t = Thread(target=docker_socket.stop_and_remove_container, args=(container["Id"],))
        threads.append(t)
        t.start()
    for z in threads:
        z.join()
    return


# start cron container function
def start_cron_job_container(cron_job_json, force_pull=True, container_type="cron_job"):
    # list current containers
    if cron_job_json["running"] is True:
        image_registry_name, image_name, version_name = split_container_name_version(cron_job_json["docker_image"])
        containers_needed = 1
        # pull required image
        if force_pull is True:
            docker_socket.pull_image(image_name, version_tag=version_name)
        # start new containers
        container_number = 1
        threads = []
        while container_number <= containers_needed:
            t = Thread(target=docker_socket.run_container, args=(cron_job_json["cron_job_name"],
                                                                 cron_job_json["cron_job_name"] + "-" +
                                                                 str(int(time.time())) + "-" + str(container_number),
                                                                 image_name, {}, [], cron_job_json["env_vars"],
                                                                 version_name, cron_job_json["volumes"],
                                                                 cron_job_json["devices"], cron_job_json["privileged"],
                                                                 cron_job_json["networks"], None),
                       kwargs={"container_type": container_type})
            threads.append(t)
            t.start()
            container_number = container_number + 1
        for y in threads:
            y.join()
        return


# start app function
def start_containers(app_json, force_pull=True):
    # list current containers
    containers_list = docker_socket.list_containers(app_json["app_name"], container_type="app")
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
                    for host_port, container_port in x.items():
                        port_binds[int(container_port)] = int(host_port) + container_number - 1
                        port_list.append(container_port)
                else:
                    print("starting ports can only a list containing intgers or dicts - dropping worker")
                    os._exit(2)
            t = Thread(target=docker_socket.run_container, args=(app_json["app_name"], app_json["app_name"] + "-" +
                                                                 str(container_number), image_name, port_binds,
                                                                 port_list, app_json["env_vars"], version_name,
                                                                 app_json["volumes"], app_json["devices"],
                                                                 app_json["privileged"], app_json["networks"],
                                                                 "unless-stopped"))
            threads.append(t)
            t.start()
            container_number = container_number + 1
        for y in threads:
            y.join()
        return


# figure out how many containers are needed
def containers_required(app_json):
    for scale_type, scale_amount in app_json["containers_per"].items():
        if scale_type == "cpu":
            containers_needed = int(cpu_cores * scale_amount)
        elif scale_type == "memory" or scale_type == "mem":
            containers_needed = int(total_memory_size_in_mb / scale_amount)
        elif scale_type == "server" or scale_type == "instance":
            containers_needed = int(scale_amount)
    return containers_needed


# prune unused images
def prune_images():
    docker_socket.prune_images()


# prune exited containers
def prune_exited_containers(filters=None):
    return docker_socket.prune_exited_containers(filters=filters)


# loop forever and in any case where a container healthcheck shows a container as unhealthy restart it
def restart_unhealthy_containers():
    try:
        while True:
            time.sleep(10)
            nebula_containers = docker_socket.list_containers(container_type="app")
            for nebula_container in nebula_containers:
                if docker_socket.check_container_healthy(nebula_container["Id"]) is False:
                    docker_socket.restart_container(nebula_container["Id"])
    except Exception as e:
        print(e, file=sys.stderr)
        print("failed checking containers health")
        os._exit(2)


# retry getting the device_group info
@retry(wait_exponential_multiplier=200, wait_exponential_max=1000, stop_max_attempt_number=10)
def get_device_group_info(nebula_connection_object, device_group_to_get_info):
    return nebula_connection_object.list_device_group_info(device_group_to_get_info)


if __name__ == "__main__":

    try:
        # read config file at startup
        print("reading config variables")
        parser = ParseIt(config_folder_location="config")

        print("reading config variables")
        # the following config variables are for configuring Nebula workers
        nebula_manager_auth_user = parser.read_configuration_variable("nebula_manager_auth_user", default_value=None)
        nebula_manager_auth_password = parser.read_configuration_variable("nebula_manager_auth_password",
                                                                          default_value=None)
        nebula_manager_auth_token = parser.read_configuration_variable("nebula_manager_auth_token", default_value=None)
        nebula_manager_host = parser.read_configuration_variable("nebula_manager_host", required=True)
        nebula_manager_port = parser.read_configuration_variable("nebula_manager_port", default_value=80)
        nebula_manager_protocol = parser.read_configuration_variable("nebula_manager_protocol", default_value="http")
        nebula_manager_request_timeout = parser.read_configuration_variable("nebula_manager_request_timeout",
                                                                            default_value=60)
        nebula_manager_check_in_time = parser.read_configuration_variable("nebula_manager_check_in_time",
                                                                          default_value=30)
        registry_auth_user = parser.read_configuration_variable("registry_auth_user", default_value=None)
        registry_auth_password = parser.read_configuration_variable("registry_auth_password", default_value=None)
        registry_host = parser.read_configuration_variable("registry_host", default_value="https://index.docker.io/v1/")
        max_restart_wait_in_seconds = parser.read_configuration_variable("max_restart_wait_in_seconds", default_value=0)
        device_group = parser.read_configuration_variable("device_group", required=True)

        # the following config variables are for configuring Nebula workers optional reporting, being optional non of it
        # is mandatory
        reporting_fail_hard = parser.read_configuration_variable("reporting_fail_hard", default_value=True)
        report_on_update_only = parser.read_configuration_variable("report_on_update_only", default_value=False)
        kafka_bootstrap_servers = parser.read_configuration_variable("kafka_bootstrap_servers", default_value=None)
        kafka_security_protocol = parser.read_configuration_variable("kafka_security_protocol",
                                                                     default_value="PLAINTEXT")
        kafka_sasl_mechanism = parser.read_configuration_variable("kafka_sasl_mechanism", default_value=None)
        kafka_sasl_plain_username = parser.read_configuration_variable("kafka_sasl_plain_username", default_value=None)
        kafka_sasl_plain_password = parser.read_configuration_variable("kafka_sasl_plain_password", default_value=None)
        kafka_ssl_keyfile = parser.read_configuration_variable("kafka_ssl_keyfile", default_value=None)
        kafka_ssl_password = parser.read_configuration_variable("kafka_ssl_password", default_value=None)
        kafka_ssl_certfile = parser.read_configuration_variable("kafka_ssl_certfile", default_value=None)
        kafka_ssl_cafile = parser.read_configuration_variable("kafka_ssl_cafile", default_value=None)
        kafka_ssl_crlfile = parser.read_configuration_variable("kafka_ssl_crlfile", default_value=None)
        kafka_sasl_kerberos_service_name = parser.read_configuration_variable("kafka_sasl_kerberos_service_name",
                                                                              default_value="kafka")
        kafka_sasl_kerberos_domain_name = parser.read_configuration_variable("kafka_sasl_kerberos_domain_name",
                                                                             default_value="kafka")
        kafka_topic = parser.read_configuration_variable("kafka_topic", default_value="nebula-reports")

        # get number of cpu cores on host
        cpu_cores = get_number_of_cpu_cores()

        # get total memory on the host in mb
        total_memory_size_in_mb = get_total_memory_size_in_mb()

        # work against docker socket
        docker_socket = DockerFunctions()

        # ensure default "nebula" named network exists
        docker_socket.create_docker_network("nebula", "bridge")

        # login to the docker registry - if no registry login details are configured will just print a message stating
        # that
        docker_socket.registry_login(registry_host=registry_host, registry_user=registry_auth_user,
                                     registry_pass=registry_auth_password)

        # login to the nebula manager
        nebula_connection = Nebula(username=nebula_manager_auth_user, password=nebula_manager_auth_password,
                                   host=nebula_manager_host, port=nebula_manager_port, protocol=nebula_manager_protocol,
                                   request_timeout=nebula_manager_request_timeout, token=nebula_manager_auth_token)

        # make sure the nebula manager connects properly
        try:
            print("checking nebula manager connection")
            api_check = nebula_connection.check_api()
            if api_check["status_code"] == 200 and api_check["reply"]["api_available"] is True:
                print("nebula manager connection ok")
            else:
                print("nebula manager initial connection check failure, dropping container")
                os._exit(2)
        except Exception as e:
            print(e, file=sys.stderr)
            print("error confirming connection to nebula manager - please check connection & authentication params and "
                  "that the manager is online")
            os._exit(2)

        # stop all nebula managed containers on start to ensure a clean slate to work on
        print("stopping all preexisting nebula managed app containers in order to ensure a clean slate on boot")
        stop_containers({"app_name": ""}, container_type="all")

        # get the initial device_group configuration and store it in memory
        local_device_group_info = get_device_group_info(nebula_connection, device_group)

        # make sure the device_group exists in the nebula cluster
        while local_device_group_info["status_code"] == 403 and \
                local_device_group_info["reply"]["device_group_exists"] is False:
            print(("device_group " + device_group + " doesn't exist in nebula cluster, waiting for it to be created"))
            local_device_group_info = get_device_group_info(nebula_connection, device_group)
            time.sleep(nebula_manager_check_in_time)

        # start all apps that are set to running on boot
        for nebula_app in local_device_group_info["reply"]["apps"]:
            if nebula_app["running"] is True:
                print(("initial start of " + nebula_app["app_name"] + " app"))
                start_containers(nebula_app)
                print(("completed initial start of " + nebula_app["app_name"] + " app"))

        # start the object which will manage cron_jobs
        cron_job_object = CronJobs()
        cron_next_run_dict = {}

        # add all cron_jobs that are included in the device_group to this worker schedule
        for nebula_cron_job in local_device_group_info["reply"]["cron_jobs"]:
            if nebula_cron_job["running"] is True:
                print(("adding cron of " + nebula_cron_job["cron_job_name"] + " cron job"))
                cron_next_run_dict[nebula_cron_job["cron_job_name"]] = cron_job_object.add_cron_job(
                    nebula_cron_job["cron_job_name"], nebula_cron_job["schedule"])
                print(("added initial cron of " + nebula_cron_job["cron_job_name"] + " cron job"))

        # open a thread which is in charge of restarting any containers which health check shows them as unhealthy
        print("starting work container health checking thread")
        Thread(target=restart_unhealthy_containers).start()

        # if the optional reporting system is configured start a kafka connection object that will be used to send the
        # reports to
        if kafka_bootstrap_servers is not None:
            try:
                print("creating reporting kafka connection object")
                kafka_connection = KafkaConnection(kafka_bootstrap_servers,
                                                   security_protocol=kafka_security_protocol,
                                                   sasl_mechanism=kafka_sasl_mechanism,
                                                   sasl_plain_username=kafka_sasl_plain_username,
                                                   sasl_plain_password=kafka_sasl_plain_password,
                                                   ssl_keyfile=kafka_ssl_keyfile,
                                                   ssl_password=kafka_ssl_password,
                                                   ssl_certfile=kafka_ssl_certfile,
                                                   ssl_cafile=kafka_ssl_cafile,
                                                   ssl_crlfile=kafka_ssl_crlfile,
                                                   sasl_kerberos_service_name=kafka_sasl_kerberos_service_name,
                                                   sasl_kerberos_domain_name=kafka_sasl_kerberos_domain_name,
                                                   topic=kafka_topic)
            except Exception as e:
                print(e, file=sys.stderr)
                if reporting_fail_hard is False:
                    print("failed creating reporting kafka connection object")
                    pass
                else:
                    print("failed creating reporting kafka connection object - exiting")
                    os._exit(2)

            try:
                reporting_object = ReportingDocument(docker_socket, device_group)
            except Exception as e:
                print(e, file=sys.stderr)
                if reporting_fail_hard is False:
                    print("failed creating reporting object")
                    pass
                else:
                    print("failed creating reporting object - exiting")
                    os._exit(2)

        # loop forever
        print(("starting device_group " + device_group + " /info check loop, configured to check for changes every "
              + str(nebula_manager_check_in_time) + " seconds"))
        while True:

            # wait the configurable time before checking the device_group info page again
            time.sleep(nebula_manager_check_in_time)

            monotonic_id_increase = False

            # get the device_group configuration
            remote_device_group_info = get_device_group_info(nebula_connection, device_group)

            # logic that checks if each of the app_id was increased and updates the app containers if the answer is yes
            # the logic also starts containers of newly added apps to the device_group
            for remote_nebula_app in remote_device_group_info["reply"]["apps"]:
                if remote_nebula_app["app_name"] in local_device_group_info["reply"]["apps_list"]:
                    local_app_index = local_device_group_info["reply"]["apps_list"].index(remote_nebula_app["app_name"])
                    if remote_nebula_app["app_id"] > local_device_group_info["reply"]["apps"][local_app_index]["app_id"]:
                        monotonic_id_increase = True
                        if remote_nebula_app["running"] is False:
                            print("stopping app " + remote_nebula_app["app_name"] +
                                  " do to changes in the app configuration")
                            stop_containers(remote_nebula_app)
                        elif remote_nebula_app["rolling_restart"] is True and \
                                local_device_group_info["reply"]["apps"][local_app_index]["running"] is True:
                            print("rolling app " + remote_nebula_app["app_name"] +
                                  " do to changes in the app configuration")
                            roll_containers(remote_nebula_app)
                        else:
                            print("restarting app " + remote_nebula_app["app_name"] +
                                  " do to changes in the app configuration")
                            restart_containers(remote_nebula_app)
                else:
                    print(("restarting app " + remote_nebula_app["app_name"] + " do to changes in the app "
                                                                               "configuration"))
                    monotonic_id_increase = True
                    restart_containers(remote_nebula_app)

            # logic that removes containers of apps that was removed from the device_group
            if remote_device_group_info["reply"]["device_group_id"] > local_device_group_info["reply"]["device_group_id"]:
                monotonic_id_increase = True
                for local_nebula_app in local_device_group_info["reply"]["apps"]:
                    if local_nebula_app["app_name"] not in remote_device_group_info["reply"]["apps_list"]:
                        print("removing app " + local_nebula_app["app_name"] +
                              " do to changes in the app configuration")
                        stop_containers(local_nebula_app)

            # logic that checks if each of the cron_job_id was increased and updates the cron_job containers if the
            # answer is yes, the logic also starts containers of newly added cron_jobs to the device_group
            for remote_nebula_cron_job in remote_device_group_info["reply"]["cron_jobs"]:
                if remote_nebula_cron_job["cron_job_name"] in local_device_group_info["reply"]["cron_jobs_list"]:
                    local_cron_job_index = local_device_group_info["reply"]["cron_jobs_list"].index(remote_nebula_cron_job["cron_job_name"])
                    if remote_nebula_cron_job["cron_job_id"] > local_device_group_info["reply"]["cron_jobs"][local_cron_job_index]["cron_job_id"]:
                        monotonic_id_increase = True
                        if remote_nebula_cron_job["running"] is False:
                            print("removing cron_job " + remote_nebula_cron_job["cron_job_name"] +
                                  " schedule do to changes in the app configuration")
                            cron_job_object.remove_cron_job(remote_nebula_cron_job["cron_job_name"])
                            cron_next_run_dict.pop(remote_nebula_cron_job["cron_job_name"], None)
                        else:
                            print("updating cron_job " + remote_nebula_cron_job["cron_job_name"] +
                                  " schedule do to changes in the app configuration")
                            cron_next_run_dict[remote_nebula_cron_job["cron_job_name"]] = \
                                cron_job_object.update_cron_job(remote_nebula_cron_job["cron_job_name"],
                                                                remote_nebula_cron_job["schedule"])
                else:
                    monotonic_id_increase = True
                    print("updating cron_job " + remote_nebula_cron_job["cron_job_name"] +
                          " schedule do to changes in the app configuration")
                    cron_next_run_dict[remote_nebula_cron_job["cron_job_name"]] = cron_job_object.add_cron_job(
                        remote_nebula_cron_job["cron_job_name"], remote_nebula_cron_job["schedule"])

            # logic that removes containers of apps that was removed from the device_group
            if remote_device_group_info["reply"]["device_group_id"] > local_device_group_info["reply"]["device_group_id"]:
                monotonic_id_increase = True
                for local_nebula_cron_job in local_device_group_info["reply"]["cron_jobs"]:
                    if local_nebula_cron_job["cron_job_name"] not in remote_device_group_info["reply"]["cron_jobs_list"]:
                        print("removing cron_job " + local_nebula_cron_job["cron_job_name"] +
                              " schedule do to changes in the app configuration")
                        cron_job_object.remove_cron_job(local_nebula_cron_job["cron_job_name"])
                        cron_next_run_dict.pop(local_nebula_cron_job["cron_job_name"], None)

            # logic that starts cron_jobs according to their next scheduled run time then updates the next runtime
            for cron_job_name, cron_job_next_run in cron_next_run_dict.items():
                if datetime.now() > cron_job_next_run:
                    local_cron_job_index = remote_device_group_info["reply"]["cron_jobs_list"].index(cron_job_name)
                    cron_job_config = remote_device_group_info["reply"]["cron_jobs"][local_cron_job_index]
                    start_cron_job_container(cron_job_config)
                    cron_next_run_dict[cron_job_name] = cron_job_object.return_cron_job_next_runtime(cron_job_name)
                    # clean previous completed cron containers
                    prune_exited_containers(filters={"label": ["orchestrator=nebula", "container_type=cron_job"]})

            # logic that runs image pruning if prune_id increased
            if remote_device_group_info["reply"]["prune_id"] > local_device_group_info["reply"]["prune_id"]:
                print("pruning images do to changes in the app configuration")
                monotonic_id_increase = True
                prune_images()

            # set the in memory device_group info to be the one recently received if any id increased
            if monotonic_id_increase is True:
                local_device_group_info = remote_device_group_info

            # send report to the optional kafka reporting if configured to be used
            if kafka_bootstrap_servers is not None:
                try:
                    # if monotonic_id_increase is true something changed so any case we will want to report on it
                    # otherwise we will report only if report_on_update_only is false
                    if monotonic_id_increase is True or report_on_update_only is False:
                        report = reporting_object.current_status_report(local_device_group_info, monotonic_id_increase)
                        kafka_connection.push_report(report)
                except Exception as e:
                    print(e, file=sys.stderr)
                    if reporting_fail_hard is False:
                        print("failed reporting state to kafka")
                        pass
                    else:
                        print("failed reporting state to kafka - exiting")
                        os._exit(2)

    except Exception as e:
        print(e, file=sys.stderr)
        print("failed main loop - exiting")
        os._exit(2)
