import docker
import json, os, time

# work against docker socket
cli = docker.APIClient(base_url='unix://var/run/docker.sock', version="auto")


# list containers based on said image, if no app_name provided gets all
def list_containers(app_name=""):
    if app_name == "":
        try:
            return cli.containers(filters={})
        except:
            print "failed getting list of all containers"
            os._exit(2)
    else:
        try:
            app_label = "app_name=" + app_name
            return cli.containers(filters={"label": app_label}, all=True)
        except:
            print "failed getting list of containers where label is app_name=" + app_name
            os._exit(2)


# pull image with optional version tag and registry auth
def pull_image(image_name, version_tag="latest", registry_user="", registry_pass="", registry_host=""):
    print "logging in to registry"
    try:
        print cli.login(registry_user, password=registry_pass, registry=registry_host)
    except:
        print "problem logging into registry"
        os._exit(2)
    print "pulling " + image_name + ":" + str(version_tag)
    try:
        print image_name
        for line in cli.pull(image_name, str(version_tag), stream=True):
            print(json.dumps(json.loads(line), indent=4))
    except:
        print "problem pulling " + image_name + ":" + str(version_tag)
        os._exit(2)


# create container
def create_container(app_name, container_name, image_name, host_configuration, container_ports=[], env_vars=[],
                     volume_mounts=[]):
    print "creating container " + container_name
    try:
        container_created = cli.create_container(image=image_name, name=container_name, ports=container_ports,
                                                 environment=env_vars, host_config=host_configuration,
                                                 volumes=volume_mounts, labels={"app_name": app_name})
        print "successfully created container " + container_name
        return container_created
    except:
        print "failed creating container " + container_name
        os._exit(2)


# stop container, default timeout set to 5 seconds, will try to kill if stop failed
def stop_container(container_name, stop_timout=5):
    print "stopping " + container_name
    try:
        reply = cli.stop(container_name, stop_timout)
    except:
        try:
            reply = cli.kill(container_name, 9)
            time.sleep(3)
        except:
            print "problem stopping " + container_name
            os._exit(2)
    return reply


# start container
def start_container(container_name):
    print "starting " + container_name
    try:
        return cli.start(container_name)
    except "APIError":
        print "problem starting container - most likely port bind already taken"
    except not "APIError":
        print "problem starting " + container_name
        os._exit(2)


# restart container, default timeout set to 2 seconds
def restart_container(container_name, stop_timout=2):
    print "restarting " + container_name
    try:
        return cli.restart(container_name, stop_timout)
    except "APIError":
        print "problem starting container - most likely port bind already taken"
    except not "APIError":
        print "problem restarting " + container_name
        os._exit(2)


# remove container
def remove_container(container_name):
    print "removing " + container_name
    try:
        return cli.remove_container(container_name)
    except:
        try:
            return cli.remove_container(container_name, force=True)
        except:
            print "problem removing " + container_name
        os._exit(2)


# create host_config
def create_container_host_config(port_binds, net_mode, volumes):
    try:
        return cli.create_host_config(port_bindings=port_binds, restart_policy={'Name': 'unless-stopped'},
                                      network_mode=net_mode, binds=volumes)
    except:
        print "problem creating host config"
        os._exit(2)


# pull image, create hostconfig, create and start the container all in one simple function
def run_container(app_name, container_name, image_name, bind_port, ports, env_vars, net_mode, version_tag="latest",
                  docker_registry_user="", docker_registry_pass="", volumes=[]):
    volume_mounts = []
    for volume in volumes:
        splitted_volume = volume.split(":")
        volume_mounts.append(splitted_volume[1])
    create_container(app_name, container_name, image_name + ":" + version_tag,
                     create_container_host_config(bind_port, net_mode, volumes), ports, env_vars, volume_mounts)
    start_container(container_name)


# stop and remove container
def stop_and_remove_container(container_name):
    stop_container(container_name)
    remove_container(container_name)
