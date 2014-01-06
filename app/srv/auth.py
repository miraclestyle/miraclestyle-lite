# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

class Context():
  
  def __init__(self):
    self.user = ndb.get_current_user()