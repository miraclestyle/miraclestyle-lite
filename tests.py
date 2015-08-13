import threading
lock = threading.Lock()

gc = 0

def init():
    global gc
    with lock:
        print 'initilizing'
        i = 1000
        while i:
            i -= 1
            gc +=1
        print 'finished global counter at %s' % gc

init()