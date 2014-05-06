# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb


class Action(ndb.BaseExpando):
  
  _kind = 56
  
  name = ndb.SuperStringProperty('1', required=True)
  arguments = ndb.SuperPickleProperty('2', required=True, default={})
  active = ndb.SuperBooleanProperty('3', required=True, default=True)
  
  @classmethod
  def build_key(cls, kind, action_id):
    return ndb.Key(kind, 'action', cls._get_kind(), action_id)


class Plugin(ndb.BasePolyExpando):
  
  _kind = 52
  
  sequence = ndb.SuperIntegerProperty('1', required=True)
  subscriptions = ndb.SuperKeyProperty('2', kind='56', repeated=True)
  active = ndb.SuperBooleanProperty('3', required=True, default=True)
  transactional = ndb.SuperBooleanProperty('4', required=True, default=False, indexed=False)
