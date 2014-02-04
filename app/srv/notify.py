# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from google.appengine.api import mail

__SYSTEM_TEMPLATES = []

def get_system_templates(context):
    # gets registered system templates
    global __SYSTEM_TEMPLATES
    
    templates = []
    
    if context.action:
      for template in __SYSTEM_TEMPLATES:
          if context.action.key in template.subscriptions:
             templates.append(template)
 
    return templates
  
  
def register_system_templates(*args):
    global __SYSTEM_TEMPLATES
    __SYSTEM_TEMPLATES.extend(args)
        
class Context():
  
  def __init__(self):
    
    self.messages = []
    
class Message():
  
  def __init__(self):
    
    self.sender = None
    self.reciever = None
    self.body = None
    self.subject = None
    
class Template(ndb.BaseModel):
  
  _kind = 57
 
  name = ndb.SuperStringProperty('1', required=True)
  message = ndb.SuperPickleProperty('2') # class Message
  active = ndb.SuperBooleanProperty('3', default=True)
  outlet = ndb.SuperStringProperty('4')
  company = ndb.SuperKeyProperty('5', kind='44', required=True) # ?
  subscriptions = ndb.SuperKeyProperty('6', kind='56', repeated=True)
 
  
  @classmethod
  def get_local_templates(cls, context):
    templates = cls.query(cls.active == True, 
                           cls.company == context.input.get('company'), 
                           cls.subscriptions == context.action.key).fetch()
         
    return templates
    
       
  def run(self, context):
      # Template.process builds context callbacks
      pass
 
class Engine:
  
  
  @classmethod
  def notify(cls):
      pass
 
  @classmethod
  def run(cls, context):
   
    templates = get_system_templates(context)
    templates.extend(Template.get_local_templates(context))
    for template in templates:
      template.run(context)
 
    for message in context.notify.messages:
      if (message.outlet == "email"):
         mail.send_mail(sender=message.sender, to=message.reciever, subject=message.subject, body=message.body)
    