import timeit
import sys
import time

sys.setrecursionlimit(200000)

def recurse():
    recurse()

recurse()

STACK = 10000

class Increaser:

    def __init__(self):
        self.n = 0

    def incr(self):
        self.n += 1
        return self.n

n1 = Increaser()
n2 = Increaser()

def test_recursion2():
    while True:
        try:
            if n1.incr() == STACK:
                raise Exception('stop')
        except:
            break

def test_recursion():
    try:
        if n2.incr() == STACK:
            raise Exception('stop')
        test_recursion()
    except:
        pass

print 'Test recursion'
start = time.time()
test_recursion()
print 'in %sms' % ((time.time() - start) * 1000)

print 'Test While'
start = time.time()
test_recursion2()
print 'in %sms' % ((time.time() - start) * 1000)


setup = """
class Increaser:

    def __init__(self):
        self.n = 0

    def incr(self):
        self.n += 1
        return self.n

n1 = Increaser()
n2 = Increaser()

def test_recursion2():
    while True:
        try:
            if n1.incr() == STACK:
                raise Exception('stop')
        except:
            break

"""

print timeit.timeit('test_recursion2()', setup=setup, number=1)

exit()