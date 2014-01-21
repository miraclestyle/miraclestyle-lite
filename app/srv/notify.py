# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

__SYSTEM_TEMPLATES = {}

def get_system_template(template):
    global __SYSTEM_TEMPLATES
 
    return __SYSTEM_TEMPLATES.get(template.key.urlasfe())
 
  
def register_system_template(*args):
    global __SYSTEM_TEMPLATES
    
    for template in args:
        __SYSTEM_TEMPLATES[template.key.urlsafe()] = template
        
class Context():
  
  def __init__(self):
    
    self.message = None
    self.templates = []
    self.args = {}
    self.entity = None
    
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
 
  
  @classmethod
  def get_local_templates(cls, template):
      action = ndb.Key(urlsafe=action_key).get()
      if action.active:
         return action
      else:
         return None
       
  def process(self, args):
      pass
 
class Engine:
 
  @classmethod
  def run(cls, context):
   
    template = get_system_template(context.notify.template)
    if not template:
      template = Template.get_local_template(context.notify.template)
   
    if template:
       template.process(context)
       if (context.notify.message.outlet == "email"):
          mail.send_mail(sender=context.notify.message.sender, to=context.notify.message.reciever, subject=context.notify.message.subject, body=context.notify.message.body)
    