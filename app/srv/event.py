# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

from app.srv import log, rule, transaction, auth
 
__SYSTEM_ACTIONS = {}

def get_system_action(action_key):
    # gets registered system journals
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
  
  KIND_ID = 49
  
  # root (namespace Domain)
  # key.id() = code.code
  
  name = ndb.SuperStringProperty('1', required=True)
  args = ndb.SuperPickleProperty('2', repeated=True) # dict
  active = ndb.SuperBooleanProperty('3', default=True)
  
  @classmethod
  def get_local_action(cls, action_key):
      return ndb.Key(urlsafe=action_key).get()
 
  def run(self, args):
    context = Context()
    context.event = self
    for key in self.args:
      self.args[key].value = args.get(key)
 
    return transaction.Engine.run(context)
 
  
class Engine:
  
  @classmethod
  def run(cls, action_key, args):
    
    action = get_system_action(action_key)
    if not action:
      action = Action.get_action(action_key)
    
    if action:
      action.run(args)