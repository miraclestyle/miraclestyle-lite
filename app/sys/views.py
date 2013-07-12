# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.core import HttpResponse

# index page view
def index(request):
    return HttpResponse('Hello World 2.0v')