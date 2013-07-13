# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

from django.db.models import *

# Override Django manager 
class DBManager(Manager):
      pass
  
# Override Django Model
class Model(Model):
      objects = DBManager()
      
      class Meta:
         abstract = True
          