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
      
      def new_state(self, **kwargs): pass
      def new_event(self, **kwargs): pass

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
    
    @staticmethod
    def get_google_authorization_url(redirect_to):
        return '%s' % webapp2.uri_for('login', segment='exchange', provider='google')
    
    @staticmethod
    def get_facebook_authorization_url(redirect_to):
        return '%s' % webapp2.uri_for('login', segment='exchange', provider='facebook')
    
    def login(self):
        pass
    
     
class ObjectLog(db.Model):
    reference = db.ReferenceProperty(None, collection_name='reference', required=True)
    agent = db.ReferenceProperty(User, collection_name='agents', required=True)
    logged = db.DateTimeProperty(auto_now_add=True, required=True)
    event = db.IntegerProperty(required=True)
    state = db.IntegerProperty(required=True)
    message = db.TextProperty(required=True)
    note = db.TextProperty(required=True)
    log = db.BlobProperty(required=True) # ne znam da li bi i ovde trebalo TextProperty umesto BlobProperty
    

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
    provider = db.StringProperty(multiline=False, required=True)
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
    