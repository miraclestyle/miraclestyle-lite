# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import sys
import logging
import string
import random

from app import settings

class Meaning(object):
  '''
    Class used to make meaning to variables. E.g.
    
    Nonexistent = Meaning('Represents something that does not exist in either list, dict or whatever')
    
    if value is Nonexistent:
       do stuff
  '''
  def __init__(self, docstring=None):
    self.__doc__ = docstring
    
  def __repr__(self):
    return '<Meaning() => %s>' % self.__doc__
  
Nonexistent = Meaning('Represents something that does not exist when built-in None cannot be used.')

def random_chars(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
  return ''.join(random.choice(chars) for x in range(size))

def logger(msg, t=None):
  if t == None:
    t = 'info'
  if settings.DO_LOGS:
    getattr(logging, t)(msg)
