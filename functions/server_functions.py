import multiprocessing, os


# return numbers of cores
def get_number_of_cpu_cores():
    try:
        cpu_number = multiprocessing.cpu_count()
    except:
        print "error getting the number of cpu core"
        os._exit(2)
    return cpu_number
