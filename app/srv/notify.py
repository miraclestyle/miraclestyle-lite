# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import math
import json

from jinja2.sandbox import SandboxedEnvironment

from google.appengine.api import mail, urlfetch

from app import ndb, settings
from app.lib.safe_eval import safe_eval
from app.srv import callback
 
__SYSTEM_TEMPLATES = []

def get_system_templates(action_key):
  global __SYSTEM_TEMPLATES
  templates = []
  if action_key:
    for template in __SYSTEM_TEMPLATES:
      if action_key == template.action:
         templates.append(template)
  return templates

def register_system_templates(*args):
  global __SYSTEM_TEMPLATES
  __SYSTEM_TEMPLATES.extend(args)


class Context():
  
  def __init__(self):
    self.entity = None
    self.transactional = None

sandboxed_jinja = SandboxedEnvironment()    
    
def render_template(template_as_string, values={}):
    from_string_template = sandboxed_jinja.from_string(template_as_string)
    return from_string_template.render(values)
 
    
class Template(ndb.BasePoly):
  
  _kind = 61
 
  action = ndb.SuperKeyProperty('1', kind='56', required=True) # action to which it subscribes
  condition = ndb.SuperStringProperty('2', required=True) # condition which has to be satisfied in order for template to generate message instance
  active = ndb.SuperBooleanProperty('3', required=True, default=True) # usefull for turnig it on/of
 
  @classmethod
  def get_local_templates(cls, entity, action_key):
    templates = cls.query(cls.active == True,
                          cls.action == action_key,
                          namespace=entity.key_namespace).fetch()
    return templates
  
  @classmethod
  def initiate(cls, context):
    
    entity_key = context.input.get('entity_key')
    user_key = context.input.get('user_key')
    
    action_key = context.action
    entity, user = ndb.get_multi(entity_key, user_key)
    
    templates = cls.get_local_templates(entity, action_key)
    if templates:
      for template in templates:
         template.run(entity, user, context)
    
    callback.Engine.run(context)
 
  
class CustomNotify(Template):
  
  _kind = 59
  
  name = ndb.SuperStringProperty('5', required=True)
  message_sender = ndb.SuperStringProperty('6', required=True) # domain user who will be impersonated as the message sender
  message_recievers = ndb.SuperPickleProperty('7') # this is a function that will be called to retrieve all relevant information regarding the recievers
  message_subject = ndb.SuperStringProperty('8', required=True) # non compiled version of message subject
  message_body = ndb.SuperTextProperty('9', required=True) # non compiled version of message body
  outlet = ndb.SuperStringProperty('10', required=True, default='58')
 
  def run(self, entity, user, context):
    
      template_values = {'entity' : entity}
      
      data = {
        'action_key' : 'send',
        'action_model' : self.outlet,
        'recipient' : self.message_recievers(entity, user),
        'sender' :  self.message_sender,
        'body' : render_template(self.message_body, template_values),
        'subject' : render_template(self.message_subject, template_values),
      }
      
      context.callbacks.payloads.append(data)
      
       
class MailNotify(Template):
  
  _kind = 58
  
  name = ndb.SuperStringProperty('5', required=True) # description for template editors
  message_sender = ndb.SuperKeyProperty('6', kind='8', required=True) # domain user who will be impersonated as the message sender
  message_reciever = ndb.SuperKeyProperty('7', kind='60', required=True) # DomainRole.key
  message_subject = ndb.SuperStringProperty('8', required=True) # non compiled version of message subject
  message_body = ndb.SuperTextProperty('9', required=True) # non compiled version of message body
  
  @classmethod
  def send(cls, context):
    
    input = context.input
    
    mail.send_mail(input['sender'], input['recipient'],
                      input['subject'], input['body'])
 
  def run(self, entity, user, context):
    
    from app.srv import auth, rule # circular avoid, this will be avoided by placing these templates in app.etc.setup
    
    values = {'entity' : entity, 'user' : user}
    
    if safe_eval(self.condition, values):
      
      domain_users = rule.DomainUser.query(rule.DomainUser.roles.IN(self.message_reciever), 
                                           namespace=self.message_reciever.namespace()).fetch()
      
      users_async = ndb.get_multi_async([auth.User.build_key(long(reciever.key.id())) for reciever in domain_users])
 
      domain_sender_user_key = auth.User.build_key(long(self.message_sender.id()))
      domain_sender_user_async = domain_sender_user_key.get_async()
      
      users = users_async.get_result()
      domain_sender_user = domain_sender_user_async.get_result()
      
      template_values = {'entity' : entity}
      
      data = {
        'action_key' : 'send',
        'action_model' : '58',
        'recipient' : [user._primary_email for user in users],
        'sender' : domain_sender_user._primary_email,
        'body' : render_template(self.message_body, template_values),
        'subject' : render_template(self.message_subject, template_values),
      }
      
      how_many_recipients = int(math.ceil(len(data['recipient']) / settings.OUTLET_RECIPIENTS_PER_TASK))
      copy_outlet_command = data.copy()
      del copy_outlet_command['recipient']
             
      for i in range(0, how_many_recipients+1):
               
       new_recipient_list = data['recipient'][settings.OUTLET_RECIPIENTS_PER_TASK*i:settings.OUTLET_RECIPIENTS_PER_TASK*(i+1)]
       
       if new_recipient_list:
         new_outlet_command = copy_outlet_command.copy()
         new_outlet_command['recipient'] = new_recipient_list
         context.callbacks.payloads.append(new_outlet_command)
       
       
class HttpNotify(Template):
  
  _kind = 63
  
  name = ndb.SuperStringProperty('5', required=True) # description for template editors
  message_sender = ndb.SuperKeyProperty('6', kind='8', required=True) # domain user who will be impersonated as the message sender
  message_reciever = ndb.SuperStringProperty('7', required=True) # DomainRole.key
  message_subject = ndb.SuperStringProperty('8', required=True) # non compiled version of message subject
  message_body = ndb.SuperTextProperty('9', required=True) # non compiled version of message body
  
  @classmethod
  def send(cls, context):
    urlfetch.fetch(context.input.get('recipient'), json.dumps(context.input), 'POST')
 
  def run(self, entity, user, context):
    
    from app.srv import auth
    
    values = {'entity' : entity, 'user' : user}
    
    if safe_eval(self.condition, values):
 
      domain_sender_user_key = auth.User.build_key(long(self.message_sender.id()))
      domain_sender_user = domain_sender_user_key.get()
 
      template_values = {'entity' : entity}
      
      data = {
        'action_key' : 'send',
        'action_model' : '63',
        'recipient' : self.message_reciever,
        'sender' : domain_sender_user._primary_email,
        'body' : render_template(self.message_body, template_values),
        'subject' : render_template(self.message_subject, template_values),
      }
      
      context.callbacks.payloads.append(data)