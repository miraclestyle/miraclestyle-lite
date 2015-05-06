# -*- coding: utf-8 -*-
'''
Created on May 6, 2015

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import time
import util

def compute(start):
    return round((time.time() - start) * 1000, 3)

class Profile():

    def __init__(self):
        self.start = time.time()

    @property
    def miliseconds(self):
        return compute(self.start)


def profile(message=None):
    def decorator(fn):
        def inner(*args, **kwargs):
            start = time.time()
            result = fn(*args, **kwargs)
            initial_message = None
            if message is None:
                initial_message = '%s executed in %s'
            else:
                initial_message = message
            util.log.debug(message % (fn.__name__, compute(start)))
            return result
        return inner
    return decorator
