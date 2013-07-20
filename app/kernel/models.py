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
          return ObjectLog(state=state, parent=self.key, **kwargs).put()
          
      def new_event(self, event, **kwargs):
          return ObjectLog(event=event, parent=self.key, **kwargs).put()
      
      @property
      def logs(self):
          return ObjectLog.query(ancestor=self.key)

class User(ndb.BaseModel, Workflow):
    
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
    
    state = ndb.IntegerProperty('1', required=True)
    _default_indexed = False
  
    @staticmethod
    def is_guest():
        return User.get_current_user() == 2
    
    @staticmethod
    def is_logged():
        return User.is_guest() == False
         
    @staticmethod
    def get_current_user():
        u = getattr(webapp2._local, 'user', 1)
        if u == 1:
            logging.info('get_current_user')
            sess = sessions.get_store().get_session(backend=settings.SESSION_STORAGE)
            if sess.has_key(settings.USER_SESSION_KEY):
               u = sess[settings.USER_SESSION_KEY].get()
               if not u:
                  u = 2
            else:
               u = 2
            webapp2._local.user = u
             
        return u
     
    def new_state(self, state, **kwargs):
        return super(User, self).new_state(state, agent=self.key, **kwargs)
        
    def new_event(self, event, **kwargs):
        return super(User, self).new_event(event, agent=self.key, **kwargs)    
    
     
class ObjectLog(ndb.BaseModel):
    
    # ancestor Any
    # kind izvlacimo iz kljuca pomocu key.kind() funkcije
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    agent = ndb.KeyProperty('2', kind=User, required=True)
    event = ndb.IntegerProperty('3', required=True)
    state = ndb.IntegerProperty('4', required=True)
    message = ndb.TextProperty('5') # nema potrebe da bude ovo required
    note = ndb.TextProperty('6') # nema potrebe da bude ovo required
    log = ndb.TextProperty('7') # nema potrebe da bude ovo required
    
    # ovako se smanjuje storage u Datastore, i trebalo bi sprovesti to isto na sve modele
    @classmethod
    def _get_kind(cls):
      return '1'
 

class UserEmail(ndb.BaseModel):
    
    # ancestor User
    email = ndb.StringProperty('1', required=True)
    primary = ndb.BooleanProperty('2', default=True)


class UserIdentity(ndb.BaseModel):
    
    # ancestor User
    user_email = ndb.KeyProperty('1', kind=UserEmail, required=True)
    identity = ndb.StringProperty('2', required=True)
    provider = ndb.StringProperty('3', required=True)
    associated = ndb.BooleanProperty('4', default=True)

# moze li ovo snimati GAE log ?
class UserIPAddress(ndb.BaseModel):
    
    # ancestor User
    ip_address = ndb.StringProperty('1', required=True)
    logged = ndb.DateTimeProperty('2', auto_now_add=True, required=True)

# ovo je pojednostavljena verzija permisija, ispod ovog modela je skalabilna verzija koja se moze prilagoditi i upotrebiti umesto ove 
class Role(ndb.BaseModel):
    
    # ancestor Store (Any?)
    name = ndb.StringProperty('1', required=True)
    permissions = ndb.StringProperty('2', indexed=False, repeated=True)
    readonly = ndb.BooleanProperty('3', default=True)

class UserRole(ndb.BaseModel):
    
    # splice
    user = ndb.KeyProperty('1', kind=User, required=True)
    role = ndb.KeyProperty('2', kind=Role, required=True)



    