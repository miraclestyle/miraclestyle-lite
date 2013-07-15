# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import db

class Workflow():
      def new_state(self, **kwargs): pass
      def new_event(self, **kwargs): pass

class User(db.Model, Workflow):
    state = db.IntegerProperty(required=True)

class ObjectLog(db.Model):
    
    reference = db.ReferenceProperty(None, collection_name='reference', required=True)
    agent = db.ReferenceProperty(User, collection_name='agents', required=True)
    logged = db.DateTimeProperty(auto_now_add=True, required=True)
    event = db.IntegerProperty(required=True)
    state = db.IntegerProperty(required=True)
    message = db.TextProperty(required=True)
    note = db.TextProperty(required=True)
    log = db.BlobProperty(required=True) # ne znam da li bi i ovde trebalo TextProperty umesto BlobProperty