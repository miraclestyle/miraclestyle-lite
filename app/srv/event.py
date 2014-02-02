# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb


__SYSTEM_ACTIONS = {}

def get_system_action(action_key):
  global __SYSTEM_ACTIONS
  action_key = ndb.Key(Action, action_key)
  return __SYSTEM_ACTIONS.get(action_key.urlasfe())

def register_system_action(*actions):
  global __SYSTEM_ACTIONS
  for action in actions:
    __SYSTEM_ACTIONS[action.key.urlsafe()] = action


class Action(ndb.BaseExpando):
  
  _kind = 56
  
  # root (namespace Domain)
  # key.id() = code.code
  
  name = ndb.SuperStringProperty('1', required=True)
  arguments = ndb.SuperPickleProperty('2') # This is dictionary.
  active = ndb.SuperBooleanProperty('3', default=True)
  service = ndb.SuperStringProperty('4') # Service name, such as log, notify, transaction, etc.
  operation = ndb.SuperStringProperty('5') # Operation name, that is being called inside a service, such as, read, write, etc.
  realtime = ndb.SuperBooleanProperty('6', default=True) # If False, action will be added in task queue for later execution.
  
  @classmethod
  def get_local_action(cls, action_key):
    action = ndb.Key(urlsafe=action_key).get()
    if action.active:
      return action
    else:
      return None
