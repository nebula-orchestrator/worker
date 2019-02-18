import multiprocessing, os, sys, psutil, socket


# return numbers of cores
def get_number_of_cpu_cores():
    try:
        cpu_number = multiprocessing.cpu_count()
        return cpu_number
    except Exception as e:
        print(e, file=sys.stderr)
        print("error getting the number of cpu core")
        os._exit(2)


# return numbers of cores
def get_total_memory_size_in_mb():
    try:
        memory_in_bytes = psutil.virtual_memory()
        total_memory_in_mb = int(memory_in_bytes.total // 1024 // 1024)
        return total_memory_in_mb
    except Exception as e:
        print(e, file=sys.stderr)
        print("error getting the memory size")
        os._exit(2)


# return CPU usage percentage
def get_cpu_use_percentage():
    try:
        cpu_use_percentage = psutil.cpu_percent(interval=None)
        return cpu_use_percentage
    except Exception as e:
        print(e, file=sys.stderr)
        print("error getting cpu usage")
        os._exit(2)


# return root HD usage
def get_root_disk_usage():
    try:
        root_disk_usage = psutil.disk_usage('/')
        root_disk_usage_dict = {
            "total": int(root_disk_usage.total // 1024 // 1024),
            "used": int(root_disk_usage.used // 1024 // 1024),
            "free": int(root_disk_usage.free // 1024 // 1024)
        }
        return root_disk_usage_dict
    except Exception as e:
        print(e, file=sys.stderr)
        print("error getting the root disk usage")
        os._exit(2)


# return memory usage
def get_memory_usage():
    try:
        memory_in_bytes = psutil.virtual_memory()
        memory_usage_dict = {
            "total": int(memory_in_bytes.total // 1024 // 1024),
            "used": int(memory_in_bytes.used // 1024 // 1024),
            "free": int(memory_in_bytes.free // 1024 // 1024),
            "available": int(memory_in_bytes.available // 1024 // 1024)
        }
        return memory_usage_dict
    except Exception as e:
        print(e, file=sys.stderr)
        print("error getting memory usage")
        os._exit(2)


# return host fqdn
def get_fqdn():
    return socket.getfqdn()
