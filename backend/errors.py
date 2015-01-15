# -*- coding: utf-8 -*-
'''
Created on Sep 22, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

class BaseKeyValueError(Exception):

    LOG = False # log this exception if possible

    def __init__(self, message):
        self.message = {}
        if hasattr(self, 'KEY'):
            key = self.KEY
        else:
            key = self.__class__.__name__.lower()
        self.message[key] = message