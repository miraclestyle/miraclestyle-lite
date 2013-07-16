# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import webapp2
from webapp2_extras.i18n import _
from app import db

class Workflow():
    
      OBJECT_TYPE = 0
      OBJECT_STATES = {}
      OBJECT_EVENTS = {}
      OBJECT_DEFAULT_STATE = 1
      OBJECT_TRANSITIONS = {}
      
      def new_state(self, state, **kwargs):
          return ObjectLog(state=state, reference=self, reference_type=self.OBJECT_TYPE, **kwargs).put()
          
      def new_event(self, event, **kwargs):
          return ObjectLog(event=event, reference=self, reference_type=self.OBJECT_TYPE, **kwargs).put()

class User(db.Model, Workflow):
    
    OBJECT_TYPE = 1
    OBJECT_STATES = {
        1 : _('Active'),
        2 : _('Banned'),
    }
    OBJECT_EVENTS = {
        1 : _('Registered'),
        2 : _('Logged in'),
        3 : _('Logged out'),

    }
    
    state = db.IntegerProperty(default=1, required=True)
    
    def new_state(self, state, **kwargs):
        return super(User, self).new_state(state, agent=self, **kwargs)
        
    def new_event(self, event, **kwargs):
        return super(User, self).new_event(event, agent=self, **kwargs)    
    
     
class ObjectLog(db.Model):
    
    reference = db.ReferenceProperty(None, collection_name='reference', required=True)
    reference_type = db.IntegerProperty(default=0)
    agent = db.ReferenceProperty(User, collection_name='agents', required=True)
    logged = db.DateTimeProperty(auto_now_add=True, required=True)
    event = db.IntegerProperty(required=True)
    state = db.IntegerProperty(required=True)
    message = db.TextProperty(default=None) # stavljam u none, jer nema smisla da bude ovo required, bezze se bloata informacijama object log
    note = db.TextProperty(default=None) # stavljam u none, jer nema smisla da bude ovo required, bezze se bloata informacijama object log
    log = db.JSONProperty(default={})


class UserConfig(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='user_configs', required=True)
    code = db.StringProperty(multiline=False, required=True)
    data = db.TextProperty(required=True) # ne znam da li bi i ovde trebalo nesto drugo umesto TextProperty


class UserEmail(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='user_emails', required=True)
    email = db.EmailProperty(required=True)
    primary = db.BooleanProperty(default=False, required=True) 


class UserIdentity(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='user_identities', required=True)
    user_email = db.ReferenceProperty(UserEmail, required=True)
    identity = db.StringProperty(multiline=False, required=True)
    provider = db.IntegerProperty(default=0, required=True)
    associated = db.BooleanProperty(default=True, required=True)


class UserIPAddress(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='user_ips', required=True)
    ip_address = db.StringProperty(multiline=False, required=True)
    logged = db.DateTimeProperty(auto_now_add=True, required=True)


class Role(db.Model):
    
    name = db.StringProperty(multiline=False, required=True)
    readonly = db.BooleanProperty(default=True, required=True)


class UserRole(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    role = db.ReferenceProperty(Role, collection_name='roles', required=True)
    