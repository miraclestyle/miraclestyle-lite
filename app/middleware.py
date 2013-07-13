# -*- coding: utf-8 -*-
'''
Created on Jul 13, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import thread

class Current(object):
    """
    Always have access to the current request
    """
    _request = {}

    def process_request(self, request):
        """
        Store request
        """
        self.__class__.set_request(request)

    def process_response(self, request, response):
        """
        Delete request
        """
        self.__class__.del_request()
        return response

    def process_exception(self, request, exception):
        """
        Delete request
        """
        self.__class__.del_request()

    @classmethod
    def get_request(cls, default=None):
        """
        Retrieve request
        """
        return cls._request.get(thread.get_ident(), default)

    @classmethod
    def set_request(cls, request):
        """
        Store request
        """
        cls._request[thread.get_ident()] = request

    @classmethod
    def del_request(cls):
        """
        Delete request
        """
        cls._request.pop(thread.get_ident(), None)