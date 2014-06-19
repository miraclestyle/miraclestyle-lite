# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb


class TerminateAction(Exception):
  pass


class Action(ndb.BaseExpando):
  
  _kind = 56
  
  name = ndb.SuperStringProperty('1', required=True)
  arguments = ndb.SuperPickleProperty('2', required=True, default={}, compressed=False)
  active = ndb.SuperBooleanProperty('3', required=True, default=True)
  
  _default_indexed = False
  
  @classmethod
  def build_key(cls, kind, action_id):
    return ndb.Key(kind, 'action', cls._get_kind(), action_id)


class PluginGroup(ndb.BaseExpando):
  
  _kind = 52
  
  name = ndb.SuperStringProperty('1', required=True)
  subscriptions = ndb.SuperKeyProperty('2', kind='56', repeated=True)
  active = ndb.SuperBooleanProperty('3', required=True, default=True)
  sequence = ndb.SuperIntegerProperty('4', required=True)  # @todo Not sure if we are gonna need this?
  transactional = ndb.SuperBooleanProperty('5', required=True, default=False, indexed=False)
  plugins = ndb.SuperPickleProperty('6', required=True, default=[], compressed=False)
  
  _default_indexed = False
