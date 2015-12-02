import threading

lock = threading.Lock()
thing = None

def getstuff():
    global thing
    with lock:
        if not thing:
            thing = {1: 2, 2: 2, 3: 3}
    return thing

print(getstuff().iteritems())
print(getstuff().iteritems())