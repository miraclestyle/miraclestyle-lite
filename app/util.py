# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import sys
import logging
import string
import random

from app import settings
 
def random_chars(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))
 
def logger(msg, t=None):
    if t == None:
       t = 'info'
       
    if settings.DO_LOGS:
       getattr(logging, t)(msg)