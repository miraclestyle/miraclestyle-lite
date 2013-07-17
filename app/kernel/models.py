# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import logging
import webapp2
from webapp2_extras.i18n import _
from webapp2_extras import sessions

from app import settings
from app import ndb

class Workflow():
    
      OBJECT_TYPE = 0
      OBJECT_STATES = {}
      OBJECT_EVENTS = {}
      OBJECT_DEFAULT_STATE = 1
      OBJECT_TRANSITIONS = {}
      
      def new_state(self, state, **kwargs):
          return ObjectLog(state=state, reference=self.key, reference_type=self.OBJECT_TYPE, **kwargs).put()
          
      def new_event(self, event, **kwargs):
          return ObjectLog(event=event, reference=self.key, reference_type=self.OBJECT_TYPE, **kwargs).put()

class User(ndb.Model, Workflow):
    
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
    
    state = ndb.IntegerProperty(default=1)
    
    @classmethod
    @webapp2.cached_property
    def get_current_user(cls):
        logging.info('get_current_user')
        sess = sessions.get_store().get_session(backend=settings.SESSION_STORAGE)
        if sess.has_key(settings.USER_SESSION_KEY):
           return sess[settings.USER_SESSION_KEY].get()
        return None
    
    
    
    def new_state(self, state, **kwargs):
        return super(User, self).new_state(state, agent=self.key, **kwargs)
        
    def new_event(self, event, **kwargs):
        return super(User, self).new_event(event, agent=self.key, **kwargs)    
    
     
class ObjectLog(ndb.Model):
    
    reference = ndb.KeyProperty()
    reference_type = ndb.IntegerProperty(default=0)
    agent = ndb.KeyProperty(kind=User)
    logged = ndb.DateTimeProperty(auto_now_add=True, required=True)
    event = ndb.IntegerProperty(required=True)
    state = ndb.IntegerProperty(required=True)
    message = ndb.TextProperty(default=None) # stavljam u none, jer nema smisla da bude ovo required, bezze se bloata informacijama object log
    note = ndb.TextProperty(default=None) # stavljam u none, jer nema smisla da bude ovo required, bezze se bloata informacijama object log
    log = ndb.JsonProperty(default={})


class UserConfig(ndb.Model):
    
    #user = ndb.KeyProperty(kind=User)
    code = ndb.StringProperty(required=True)
    data = ndb.TextProperty(required=True) # ne znam da li bi i ovde trebalo nesto drugo umesto TextProperty


class UserEmail(ndb.Model):
    
    user = ndb.KeyProperty(kind=User)
    email = ndb.StringProperty()
    primary = ndb.BooleanProperty(default=False) 


class UserIdentity(ndb.Model):
    
    user = ndb.KeyProperty(kind=User)
    user_email = ndb.KeyProperty(kind=UserEmail)
    identity = ndb.StringProperty(required=True)
    provider = ndb.IntegerProperty(default=0)
    associated = ndb.BooleanProperty(default=True)


class UserIPAddress(ndb.Model):
    
    user = ndb.KeyProperty(kind=User)
    ip_address = ndb.StringProperty(required=True)
    logged = ndb.DateTimeProperty(auto_now_add=True)


class Role(ndb.Model):
    
    name = ndb.StringProperty(required=True)
    readonly = ndb.BooleanProperty(default=True)


class UserRole(ndb.Model):
    
    user = ndb.KeyProperty(kind=User)
    role = ndb.KeyProperty(kind=Role)
    