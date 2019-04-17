from functions.docker_engine.docker_engine import *
from functions.misc.server import *
import time


class ReportingDocument:

    def __init__(self, docker_connection_object, device_group):
        self.docker_connection = docker_connection_object
        self.server_number_of_cores = get_number_of_cpu_cores()
        self.device_group = device_group

    # TODO - add cron_jobs containers status of each run and time it started & completed (if not still running)
    def current_status_report(self, device_group_config):
        report = {
            "memory_usage": get_memory_usage(),
            "root_disk_usage": get_root_disk_usage(),
            "cpu_usage": {
                "cores": self.server_number_of_cores,
                "used_percent": get_cpu_use_percentage()
            },
            "apps_containers": self.docker_connection.list_containers_stats(),
            "current_device_group_config": device_group_config,
            "device_group": self.device_group,
            "report_creation_time": int(time.time()),
            "hostname": get_fqdn()
        }
        return report
