# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from django.conf import settings
from app import models
from app.middleware import Current

# Workflow Class, objectifiying models     
class Workflow():
    
      OBJECT_STATES = {}
      OBJECT_EVENTS = {}
    
      # Not used currently
      def __save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
          
          new = False
          
          if not self.pk:
             new = True
             
          save = super(Workflow, self).save(force_insert, force_update, using,
             update_fields)
          
          if save:
             if new:
                self.new_state(self.OBJECT_STATES[1], event=self.OBJECT_EVENTS[1])
           
      @property
      def show_state(self):
          return self.OBJECT_STATES[self.state]
      
      def get_last_state(self):
          return ObjectLog.objects.filter(object_id=self.pk, object_type=self.OBJECT_TYPE).order_by('-pk')[0]
      
      def new_state(self, **kwargs):
          get_return = ObjectLog.objects.create(object_id=self.pk, object_type=self.OBJECT_TYPE, **kwargs)
          self.state = get_return.state
          react = 'react_on_state_%s' % get_return.state
          react2 = 'react_on_event_%s' % get_return.event
          
          if hasattr(self, react):
             getattr(self, react)()
             
          if hasattr(self, react2):
             getattr(self, react2)()
          
          return self.save()

class Role(models.Model):
 
    name = models.CharField(max_length=255L, blank=True)
    readonly = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'role'
  
class User(models.Model, Workflow):
    
    OBJECT_TYPE = 1
    OBJECT_STATES = {           
      1 : 'Active',
      2 : 'Disabled',
      3 : 'Banned'
    }
    
    OBJECT_EVENTS = {
        1 : 'Create',
        2 : 'Update',
        3 : 'Logged In',
    }
     
    state = models.IntegerField(null=True, blank=True)
    
    def react_on_event_3(self):
        pass
  
    def login(self):
        req = Current.get_request()
        if not req.session.get(settings.SESSION_USER_KEY):
               req.session[settings.SESSION_USER_KEY] = self.pk
               self.new_state(state=1, event=3, user=self)
 
    def logout(self):
        req = Current.get_request()
        try:
          del req.session[settings.SESSION_USER_KEY]
        except KeyError:
          pass
    
    class Meta:
        db_table = 'user'
        

class ObjectLog(models.Model):
    
    id = models.BigIntegerField(primary_key=True)
    object_id = models.IntegerField()
    object_type = models.IntegerField()
    user = models.ForeignKey(User)
    date = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    event = models.IntegerField()
    state = models.IntegerField()
    message = models.TextField(blank=True)
    note = models.TextField(blank=True)
    log = models.TextField(blank=True)
  
    class Meta:
        db_table = 'object_log'
        
        
class UserConfig(models.Model):
 
    user = models.ForeignKey('User', related_name = 'config')
    key = models.CharField(max_length=255L, blank=True)
    data = models.TextField(blank=True)
    
    class Meta:
        db_table = 'user_config'

class UserEmail(models.Model):
 
    user = models.ForeignKey('User', related_name = 'emails')
    email = models.CharField(max_length=255L, blank=True)
    primary = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_email'
        unique_together = (('user', 'email'),)

class UserIdentity(models.Model):
 
    user = models.ForeignKey('User', related_name = 'identities')
    identity = models.CharField(max_length=255L, blank=True)
    user_email = user = models.ForeignKey('UserEmail', on_delete=models.DO_NOTHING, null=True)
    provider = models.CharField(max_length=255L, blank=True)
    associated = models.BooleanField(default=0)
    
    class Meta:
        db_table = 'user_identity'

class UserIpAddress(models.Model):
 
    user = models.ForeignKey('User', related_name = 'ips')
    ip_address = models.CharField(max_length=255L, blank=True)
    date = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    
    class Meta:
        db_table = 'user_ip_address'

class UserRole(models.Model):
 
    user = user = models.ForeignKey('User', related_name = 'roles')
    role_id = models.IntegerField()
    
    class Meta:
        db_table = 'user_role'
 