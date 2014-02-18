# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import math
import json

from jinja2.sandbox import SandboxedEnvironment

from google.appengine.api import mail
from google.appengine.api import taskqueue
from app import ndb, settings
from app.lib.safe_eval import safe_eval


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
 
    
class Template(ndb.BaseModel):
  
  kind = ndb.SuperStringProperty('1', required=True) # kind to which action belongs
  action = ndb.SuperKeyProperty('2', kind='56', required=True) # action to which it subscribes
  condition = ndb.SuperStringProperty('3', required=True) # condition which has to be satisfied in order for template to generate message instance
  active = ndb.SuperBooleanProperty('4', required=True, default=True) # usefull for turnig it on/of
  outlet = ndb.SuperStringProperty('5', required=True, default='mail')
 
  @classmethod
  def get_local_templates(cls, action_key):
    templates = cls.query(cls.active == True,
                          cls.action == action_key).fetch()
    return templates
  
  def run(self, entity, user):
    pass

class DomainTemplate(Template):
  
  _kind = 58
  
  name = ndb.SuperStringProperty('6', required=True) # description for template editors
  message_sender = ndb.SuperKeyProperty('7', kind='8', required=True) # domain user who will be impersonated as the message sender
  message_recievers = ndb.SuperKeyProperty('8', kind='8', repeated=True) # non compiled version of message receiver / not sure if it should be pickle
  message_subject = ndb.SuperStringProperty('9', required=True) # non compiled version of message subject
  message_body = ndb.SuperTextProperty('10', required=True) # non compiled version of message body
 
  def run(self, entity, user):
    
    values = {'user' : user, 'entity' : entity}
    
    if safe_eval(self.condition, values):
      
      domain_users = ndb.get_multi(self.message_recievers)
      
      users = ndb.get_multi([reciever.user for reciever in domain_users])
 
      domain_sender = self.message_sender.get()
      domain_sender_user = domain_sender.user.get()
      
      template_values = {'entity' : entity}
      
      return {
              'recipients' : [user.primary_email for user in users],
              'sender' : domain_sender_user.primary_email,
              'body' : render_template(self.message_body, template_values),
              'subject' : render_template(self.message_subject, template_values),
              'outlet' : self.outlet,
             }
 
    
class Engine:
  
  @classmethod
  def send(cls, input):
    
    outlet_command = input.get('data')
    
    if outlet_command['outlet'] == 'mail':
       mail.send_mail(outlet_command['sender'], outlet_command['recipients'],
                      outlet_command['subject'], outlet_command['body'])
  
  
  @classmethod
  def _templates(cls, queue, tasks, entity, user, templates):
    
    outlet_commands = []
    
    for template in templates:
        command = template.run(entity, user)
        if command:
           outlet_commands.append(command)
    
    total_outlet_commands = len(outlet_commands)
    
    if total_outlet_commands:      
       commands_per_task = math.ceil(total_outlet_commands / settings.OUTLET_TEMPLATES_PER_TASK)
       
       for i in range(0, commands_per_task+1):
         
           cursored_outlet_commands = outlet_commands[settings.OUTLET_TEMPLATES_PER_TASK*i:settings.OUTLET_TEMPLATES_PER_TASK*(i+1)]
            
           for outlet_command in cursored_outlet_commands:
             
               how_many_recipients = math.ceil(len(outlet_command['recipients']) / settings.OUTLET_RECIPIENTS_PER_TASK)
               
               copy_outlet_command = outlet_command.copy()
               
               del copy_outlet_command['recipients']
               
               for _i in range(0, how_many_recipients+1):
                 
                 new_recipient_list = outlet_command['recipients'][settings.OUTLET_RECIPIENTS_PER_TASK*_i:settings.OUTLET_RECIPIENTS_PER_TASK*(_i+1)]
                 
                 if new_recipient_list:
                   new_outlet_command = copy_outlet_command.copy()
                   new_outlet_command['recipients'] = new_recipient_list
                   
                   payload = {'data' : new_outlet_command}
    
                   task = taskqueue.Task(url='/task/notify_send', payload=json.dumps(payload))
                   tasks.append(task)
             
  
  @classmethod
  def prepare(cls, input):
    
    entity_key = ndb.Key(urlsafe=input.get('entity_key'))
    entity = entity_key.get()
    
    action_key = ndb.Key(urlsafe=input.get('action_key'))
   
    
    user_key = ndb.Key(urlsafe=input.get('user_key'))
    user = user_key.get()
    
    
    queue = taskqueue.Queue(name='notify_send')
    tasks = []
    
    # we are sending payload instead of "params", our server will parse that if it's formatted as json
    templates = get_system_templates(action_key)
    
    cls._templates(queue, tasks, entity, user, templates)
     
    templates = DomainTemplate.get_local_templates(action_key)
    
    cls._templates(queue, tasks, entity, user, templates)
    
    if tasks:
       queue.add(tasks)
     
     
  @classmethod
  def run(cls, context):
    
    if context.notify.transacitonal is None:
       context.notify.transacitonal = ndb.in_transaction()
    
    new_task = taskqueue.add(queue_name='notify', url='/task/notify_prepare',
                             transactional=context.notify.transactional,
                             params={'action_key' : context.action.key.urlsafe(),
                                     'user_key' : context.auth.key.urlsafe(),
                                     'entity_key' : context.notify.entity.key.urlsafe()})
      
    return new_task
      
  