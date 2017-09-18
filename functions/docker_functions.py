import docker
import json, os, time


class DockerFunctions:

    def __init__(self):
        self.cli = docker.APIClient(base_url='unix://var/run/docker.sock', version="auto")

    # check network exists:
    def check_network_exists(self, net_name):
        if len(self.cli.networks(names=net_name)) > 0:
            return True
        else:
            return False

    # create default network if doesn't exist
    def create_default_nebula_network(self):
        if self.check_network_exists("nebula") is False:
            self.cli.create_network("nebula", driver="bridge", check_duplicate=True)

    # list containers based on said image, if no app_name provided gets all
    def list_containers(self, app_name=""):
        if app_name == "":
            try:
                return self.cli.containers(filters={})
            except:
                print "failed getting list of all containers"
                os._exit(2)
        else:
            try:
                app_label = "app_name=" + app_name
                return self.cli.containers(filters={"label": app_label}, all=True)
            except:
                print "failed getting list of containers where label is app_name=" + app_name
                os._exit(2)

    # pull image with optional version tag and registry auth
    def pull_image(self, image_name, version_tag="latest", registry_user="", registry_pass="", registry_host=""):
        print "logging in to registry"
        try:
            print self.cli.login(registry_user, password=registry_pass, registry=registry_host)
        except:
            print "problem logging into registry"
            os._exit(2)
        print "pulling " + image_name + ":" + str(version_tag)
        try:
            print image_name
            for line in self.cli.pull(image_name, str(version_tag), stream=True):
                print(json.dumps(json.loads(line), indent=4))
        except:
            print "problem pulling " + image_name + ":" + str(version_tag)
            os._exit(2)

    # create container
    def create_container(self, app_name, container_name, image_name, host_configuration, container_ports=[],
                         env_vars=[], volume_mounts=[]):
        print "creating container " + container_name
        try:
            container_created = self.cli.create_container(image=image_name, name=container_name, ports=container_ports,
                                                          environment=env_vars, host_config=host_configuration,
                                                          volumes=volume_mounts, labels={"app_name": app_name})
            print "successfully created container " + container_name
            return container_created
        except:
            print "failed creating container " + container_name
            os._exit(2)

    # stop container, default timeout set to 5 seconds, will try to kill if stop failed
    def stop_container(self, container_name, stop_timout=5):
        print "stopping " + container_name
        try:
            reply = self.cli.stop(container_name, stop_timout)
        except:
            try:
                reply = self.cli.kill(container_name, 9)
                time.sleep(3)
            except:
                print "problem stopping " + container_name
                os._exit(2)
        return reply

    # start container
    def start_container(self, container_name):
        print "starting " + container_name
        try:
            return self.cli.start(container_name)
        except "APIError":
            print "problem starting container - most likely port bind already taken"
        except not "APIError":
            print "problem starting " + container_name
            os._exit(2)

    # restart container, default timeout set to 2 seconds
    def restart_container(self, container_name, stop_timout=2):
        print "restarting " + container_name
        try:
            return self.cli.restart(container_name, stop_timout)
        except "APIError":
            print "problem starting container - most likely port bind already taken"
        except not "APIError":
            print "problem restarting " + container_name
            os._exit(2)

    # remove container
    def remove_container(self, container_name):
        print "removing " + container_name
        try:
            return self.cli.remove_container(container_name)
        except:
            try:
                return self.cli.remove_container(container_name, force=True)
            except:
                print "problem removing " + container_name
            os._exit(2)

    # create host_config
    def create_container_host_config(self, port_binds, net_mode, volumes, devices, privileged):
        try:
            return self.cli.create_host_config(port_bindings=port_binds, restart_policy={'Name': 'unless-stopped'},
                                          network_mode=net_mode, binds=volumes, devices=devices, privileged=privileged)
        except:
            print "problem creating host config"
            os._exit(2)

    # create networking_config
    def create_networking_config(self, starting_network):
        try:
            networking_config = self.cli.create_networking_config(
                {
                    starting_network: self.cli.create_endpoint_config()
                }
            )
            return networking_config
        except:
            print "problem creating network config"
            os._exit(2)

    # connect a container to a network
    def connect_to_network(self, container, net_id):
        try:
            self.cli.connect_container_to_network(container, net_id)
        except:
            print "problem connecting to network " + net_id + ", does the net your trying to connect to exist?"
            os._exit(2)

    # pull image, create hostconfig, create and start the container all in one simple function
    def run_container(self, app_name, container_name, image_name, bind_port, ports, env_vars, net_mode,
                      version_tag="latest", docker_registry_user="", docker_registry_pass="", volumes=[], devices=[],
                      privileged=False):
        volume_mounts = []
        for volume in volumes:
            splitted_volume = volume.split(":")
            volume_mounts.append(splitted_volume[1])
        self.create_container(app_name, container_name, image_name + ":" + version_tag,
                              self.create_container_host_config(bind_port, net_mode, volumes, devices, privileged),
                              ports, env_vars, volume_mounts)
        self.start_container(container_name)

    # stop and remove container
    def stop_and_remove_container(self, container_name):
        self.stop_container(container_name)
        self.remove_container(container_name)
