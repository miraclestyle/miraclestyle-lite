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
      

class ObjectLog(Model):
    
    id = BigIntegerField(primary_key=True)
    object_id = IntegerField()
    object_type = IntegerField()
    user = ForeignKey('User')
    date = DateTimeField(null=True, blank=True)
    event = IntegerField()
    state = IntegerField()
    message = TextField(blank=True)
    note = TextField(blank=True)
    log = TextField(blank=True)
  
    class Meta:
        db_table = 'object_log'
 
          
# Workflow Class, objectifiying models     
class Workflow():
    
      @property
      def get_state(self):
          return self.OBJECT_STATES[self.state]
      
      def get_last_state(self):
          return ObjectLog.objects.filter(object_id=self.pk, object_type=self.OBJECT_TYPE).order('-pk')[0]
      
      def new_state(self, state, **kwargs):
          return ObjectLog.objects.create(object_id=self.pk, object_type=self.OBJECT_TYPE, state=state, **kwargs)
          