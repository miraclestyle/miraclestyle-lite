# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

from app import models
  
class User(models.Model, models.Workflow):
    
    OBJECT_TYPE = 1
    OBJECT_STATES = {
      1 : 'Active',
      2 : 'Disabled',
      3 : 'Banned'
    }
    
    id = models.IntegerField(primary_key=True)
    state = models.IntegerField()
    
    class Meta:
        db_table = 'user'
 