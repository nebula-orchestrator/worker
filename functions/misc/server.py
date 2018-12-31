import multiprocessing, os, sys


# return numbers of cores
def get_number_of_cpu_cores():
    try:
        cpu_number = multiprocessing.cpu_count()
        return cpu_number
    except Exception as e:
        print >> sys.stderr, e
        print("error getting the number of cpu core")
        os._exit(2)
