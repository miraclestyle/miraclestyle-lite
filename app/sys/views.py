# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.core import HttpResponse

def index(request):
    return HttpResponse('Hello World')