import json, os, time, sys, docker


class DockerFunctions:

    def __init__(self):
        self.cli = docker.APIClient(base_url='unix://var/run/docker.sock', version="auto")

    # check network exists:
    def check_network_exists(self, net_name):
        if len(self.cli.networks(names=net_name)) > 0:
            return True
        else:
            return False

    # create a network if it doesn't exist
    def create_docker_network(self, net_name, net_driver):
        if self.check_network_exists(net_name) is False:
            self.cli.create_network(net_name, driver=net_driver, check_duplicate=True)
            print("created a " + net_driver + " type network named " + net_name)

    # list containers based on said image, if no app_name provided gets all of nebula managed apps
    def list_containers(self, app_name=""):
        if app_name == "":
            try:
                return self.cli.containers(filters={"label": "orchestrator=nebula"})
            except Exception as e:
                print(e, file=sys.stderr)
                print("failed getting list of all containers")
                os._exit(2)
        else:
            try:
                app_label = "app_name=" + app_name
                return self.cli.containers(filters={"label": [app_label, "orchestrator=nebula"]}, all=True)
            except Exception as e:
                print(e, file=sys.stderr)
                print("failed getting list of containers where label is app_name=" + app_name)
                os._exit(2)

    # list containers stats on said image, if no app_name provided gets all of nebula managed apps
    def list_containers_stats(self, app_name=""):
        try:
            containers_list = self.list_containers(app_name)
            containers_stats = []
            for container in containers_list:
                containers_stats.append(self.cli.stats(container['Id'], stream=False))
            return containers_stats
        except Exception as e:
            print(e, file=sys.stderr)
            print("failed getting stats of containers where label is app_name=" + app_name)
            os._exit(2)

    # check if a container is healthy by examining the result of the dockerfile healthcheck, if no healthcheck is
    # configured assumes the container to always be healthy.
    def check_container_healthy(self, container_id):
        try:
            container_inspection = self.cli.inspect_container(container_id)
            if "Health" in container_inspection["State"]:
                # check if the container is unhealthy and for a bunch of edge cases so it won't try to restart a
                # container that's in the process of being removed\replaced
                if container_inspection["State"]["Health"]["Status"] == "unhealthy" and \
                        container_inspection["State"]["Running"] is True and \
                        container_inspection["State"]["Restarting"] is False and \
                        container_inspection["State"]["Paused"] is False and \
                        container_inspection["State"]["Dead"] is False:
                    container_healthy = False
                else:
                    container_healthy = True
            else:
                container_healthy = True
        # if the container doesn't exist it's because it was removed and it means we no longer have to worry about
        # it's health as a non existing container who's status is non existing is in the require state and therefor
        # can be considered healthy.
        except Exception as e:
            print(e, file=sys.stderr)
            print("failed getting health status of container " + container_id)
            container_healthy = True
        return container_healthy

    # login to docker registry
    def registry_login(self, registry_user=None, registry_pass=None, registry_host=""):
        if registry_user is not None and registry_user != "skip" and registry_pass is not None and \
                registry_pass != "skip":
            print("logging in to registry")
            try:
                print(self.cli.login(username=registry_user, password=registry_pass, registry=registry_host))
            except Exception as e:
                print(e, file=sys.stderr)
                print("problem logging into registry")
                os._exit(2)
        else:
            print("no registry user pass combo defined, skipping registry login")

    # pull image with optional version tag and registry auth
    def pull_image(self, image_name, version_tag="latest"):
        print("pulling image " + image_name + ":" + str(version_tag))
        try:
            print(image_name)
            for line in self.cli.pull(image_name, str(version_tag), stream=True):
                print(json.dumps(json.loads(line), indent=4))
        except Exception as e:
            print(e, file=sys.stderr)
            print("problem pulling image " + image_name + ":" + str(version_tag))
            os._exit(2)

    # prune unused images
    def prune_images(self):
        print("pruning unused images")
        try:
            print(self.cli.prune_images())
        except Exception as e:
            print(e, file=sys.stderr)
            print("problem pruning unused image")
            os._exit(2)

    # create container
    def create_container(self, app_name, container_name, image_name, host_configuration, container_ports=[],
                         env_vars=[], volume_mounts=[], default_network="nebula"):
        print("creating container " + container_name)
        try:
            container_created = self.cli.create_container(image=image_name, name=container_name, ports=container_ports,
                                                          environment=env_vars, host_config=host_configuration,
                                                          volumes=volume_mounts, labels={"app_name": app_name,
                                                                                         "orchestrator": "nebula"},
                                                          networking_config=self.create_networking_config(
                                                              default_network))
            print(("successfully created container " + container_name))
            return container_created
        except Exception as e:
            print(e, file=sys.stderr)
            print("failed creating container " + container_name)
            os._exit(2)

    # stop container, default timeout set to 5 seconds, will try to kill if stop failed
    def stop_container(self, container_name, stop_timout=5):
        print(("stopping container " + container_name))
        try:
            reply = self.cli.stop(container_name, stop_timout)
            return reply
        except:
            try:
                reply = self.cli.kill(container_name, 9)
                time.sleep(3)
                return reply
            except Exception as e:
                print(e, file=sys.stderr)
                print("problem stopping container " + container_name)
                os._exit(2)

    # start container
    def start_container(self, container_name):
        print(("starting container " + container_name))
        try:
            return self.cli.start(container_name)
        except "APIError" as e:
            print(e, file=sys.stderr)
            print("problem starting container - most likely port bind already taken")
        except not "APIError" as e:
            print(e, file=sys.stderr)
            print("problem starting container " + container_name)
            os._exit(2)

    # restart container, default timeout set to 2 seconds
    def restart_container(self, container_name, stop_timout=2):
        print(("restarting container " + container_name))
        try:
            return self.cli.restart(container_name, stop_timout)
        except "APIError" as e:
            print(e, file=sys.stderr)
            print("problem starting container - most likely port bind already taken")
        except not "APIError" as e:
            print(e, file=sys.stderr)
            print("problem restarting container " + container_name)
            os._exit(2)

    # remove container
    def remove_container(self, container_name):
        print(("removing container " + container_name))
        try:
            return self.cli.remove_container(container_name)
        except:
            try:
                return self.cli.remove_container(container_name, force=True)
            except Exception as e:
                print(e, file=sys.stderr)
                print("problem removing container " + container_name)
            os._exit(2)

    # create host_config
    # TODO - change the restart_policy to be default unless-stopped but allow to have a never restart policy too
    def create_container_host_config(self, port_binds, volumes, devices, privileged, network_mode):
        try:
            return self.cli.create_host_config(port_bindings=port_binds, restart_policy={'Name': 'unless-stopped'},
                                               binds=volumes, devices=devices, privileged=privileged,
                                               network_mode=network_mode)
        except Exception as e:
            print(e, file=sys.stderr)
            print("problem creating host config")
            os._exit(2)

    # create networking_config
    def create_networking_config(self, starting_network=""):
        try:
            networking_config = self.cli.create_networking_config(
                {
                    starting_network: self.cli.create_endpoint_config()
                }
            )
            return networking_config
        except Exception as e:
            print(e, file=sys.stderr)
            print("problem creating network config")
            os._exit(2)

    # connect a container to a network
    def connect_to_network(self, container, net_id):
        try:
            self.cli.connect_container_to_network(container, net_id)
        except Exception as e:
            print(e, file=sys.stderr)
            print("problem connecting to network " + net_id)
            os._exit(2)

    # get net_id
    def get_net_id(self, network):
        requested_net_id = self.cli.networks(names=network)
        return requested_net_id[0]["Id"]

    # return what the default net needs to be
    def default_net(self, networks):
        if len(networks) > 0 and networks[0] == "host":
            return "host"
        elif len(networks) > 0 and networks[0] == "none":
            return "none"
        else:
            return "nebula"

    # pull image, create hostconfig, create and start the container and bind to networks all in one simple function
    def run_container(self, app_name, container_name, image_name, bind_port, ports, env_vars, version_tag="latest",
                      volumes=[], devices=[], privileged=False, networks=[]):
        volume_mounts = []
        for volume in volumes:
            splitted_volume = volume.split(":")
            volume_mounts.append(splitted_volume[1])
        if networks[0] == "host":
            network_mode = "host"
        elif networks[0] == "none":
            network_mode = "none"
        else:
            network_mode = "bridge"
        self.create_container(app_name, container_name, image_name + ":" + version_tag,
                              self.create_container_host_config(bind_port, volumes, devices, privileged, network_mode),
                              ports, env_vars, volume_mounts, default_network=self.default_net(networks))
        self.start_container(container_name)
        for network in networks:
            # special networks which are created from the container creation as they have to be first
            if network != "nebula" and network != "host" and network != "none":
                try:
                    self.connect_to_network(container_name, self.get_net_id(network))
                except Exception as e:
                    print(e, file=sys.stderr)
                    print("problem connecting to network " + network)
                    os._exit(2)

    # stop and remove container
    def stop_and_remove_container(self, container_name):
        self.stop_container(container_name)
        self.remove_container(container_name)

    # TODO - add functions that return if the exit of a container is OK (if 0 then True all else False)

    # TODO - add run cron_job container function which removes the logs/data/container of previous runs and starts a new
    # TODO - container without the restart_policy flag
