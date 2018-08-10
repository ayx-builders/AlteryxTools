import sys, time

sys.stdout = open("c:\Logs\debut.txt", 'w')
startTime = time.perf_counter()
logLabel: str = ''


def print_start(label: str):
    global startTime
    global logLabel
    startTime = time.perf_counter()
    logLabel = label


def print_end():
    global startTime
    global logLabel
    delta = time.perf_counter() - startTime
    print(logLabel + "|" + repr(delta))


