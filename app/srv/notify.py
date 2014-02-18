# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.api import mail
from google.appengine.api import taskqueue
from app import ndb


__SYSTEM_TEMPLATES = []

def get_system_templates(context):
  global __SYSTEM_TEMPLATES
  templates = []
  if context.action:
    for template in __SYSTEM_TEMPLATES:
      if context.action.key in template.action:
        templates.append(template)
  return templates

def register_system_templates(*args):
  global __SYSTEM_TEMPLATES
  __SYSTEM_TEMPLATES.extend(args)


class Context():
  
  def __init__(self):
    self.entity = None
    self.transactional = None


class Message():
  
  def __init__(self):
    self.sender = None
    self.reciever = None
    self.body = None
    self.subject = None


class Template(ndb.BaseModel):
  
  _kind = 57
  
  name = ndb.SuperStringProperty('1', required=True) # description for template editors
  action = ndb.SuperKeyProperty('2', kind='56', required=True) # action to which it subscribes
  kind = ndb.SuperStringProperty('3') # not sure if this is usefull or not ?
  condition = ndb.SuperPickleProperty('4', required=True) # condition which has to be satisfied in order for template to generate message instance
  active = ndb.SuperBooleanProperty('5', default=True) # usefull for turnig it on/of
  outlet = ndb.SuperStringProperty('6') # not sure if this should be here or should we create separate template classes for each outlet
  message_sender = ndb.SuperPickleProperty('7') # not sure if this is usefull or not ?
  message_reciever = ndb.SuperPickleProperty('8') # non compiled version of message receiver / not sure if it should be pickle
  message_subject = ndb.SuperStringProperty('9', required=True) # non compiled version of message subject / not sure if it should be pickle
  message_body = ndb.SuperTextProperty('10') # non compiled version of message body / not sure if it should be pickle
  
  @classmethod
  def get_local_templates(cls, context):
    templates = cls.query(cls.active == True,
                          cls.action == context.action.key).fetch()
    return templates
  
  def run(self, context):
    # Template.run() builds context callbacks
    pass


class Engine:
  
  @classmethod
  def notify(cls):
    pass
  
  def prepare():
    pass
  
  @classmethod
  def run(cls, context):
    pass
  