import multiprocessing, os, sys, psutil


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
        total_memory_in_mb = int(memory_in_bytes.total / 1024 / 1024)
        return total_memory_in_mb
    except Exception as e:
        print(e, file=sys.stderr)
        print("error getting the number of cpu core")
        os._exit(2)
