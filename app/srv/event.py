# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

from app.srv import log, rule, transaction, auth
 
__SYSTEM_ACTIONS = {}

def get_system_action(action_key):
    global __SYSTEM_ACTIONS
    
    action_key = ndb.Key(Action, action_key)
    
    return __SYSTEM_ACTIONS.get(action_key.urlasfe())
 
  
def register_system_action(*args):
    global __SYSTEM_ACTIONS
    
    for action in args:
        __SYSTEM_ACTIONS[action.key.urlsafe()] = action
 
class Context():
  
  def __init__(self):
 
    self.event = None
    self.transaction = transaction.Context()
    self.rule = rule.Context()
  
    self.log = log.Context()
    self.auth = auth.Context()
    self.response = None
    
    
class Argument():
  
  def __init__(self, name, formatter, mapper, value=None):
      self.name = name
      self.formatter = formatter
      self.mapper = mapper
      self.value = value
     
 
 
class Action(ndb.BaseExpando):
  
  KIND_ID = 56
  
  # root (namespace Domain)
  # key.id() = code.code
  
  name = ndb.SuperStringProperty('1', required=True)
  arguments = ndb.SuperPickleProperty('2') # dict
  active = ndb.SuperBooleanProperty('3', default=True)
  operation = ndb.SuperStringProperty('4')
  
  @classmethod
  def get_local_action(cls, action_key):
      action = ndb.Key(urlsafe=action_key).get()
      if action.active:
         return action
      else:
         return None
 
  def run(self, args):
    context = Context()
    context.event = self
    self.args = {}
    for key in self.arguments:
      self.args[key] = args.get(key)
    return transaction.Engine.run(context)
 
  
class Engine:
  
  @classmethod
  def run(cls, action_key, args):
    
    action = get_system_action(action_key)
    if not action:
      action = Action.get_local_action(action_key)
    
    if action:
      action.run(args)