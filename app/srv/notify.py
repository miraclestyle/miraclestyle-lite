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
  kind = ndb.SuperStringProperty('2', required=True) # kind to which action belongs
  action = ndb.SuperKeyProperty('3', kind='56', required=True) # action to which it subscribes
  condition = ndb.SuperStringProperty('4', required=True) # condition which has to be satisfied in order for template to generate message instance
  active = ndb.SuperBooleanProperty('5', required=True, default=True) # usefull for turnig it on/of
  outlet = ndb.SuperStringProperty('6', required=True, default='mail')
  message_sender = ndb.SuperKeyProperty('7', kind='8', required=True) # domain user who will be impersonated as the message sender
  message_recievers = ndb.SuperKeyProperty('8', kind='8', repeated=True) # non compiled version of message receiver / not sure if it should be pickle
  message_subject = ndb.SuperStringProperty('9', required=True) # non compiled version of message subject
  message_body = ndb.SuperTextProperty('10', required=True) # non compiled version of message body
  
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
  