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
from app.srv import rule
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
 
  
class CustomNotify(Template):
  
  _kind = 59
  
  name = ndb.SuperStringProperty('5', required=True)
  message_sender = ndb.SuperStringProperty('6', required=True) # domain user who will be impersonated as the message sender
  message_recievers = ndb.SuperPickleProperty('7') # this is a function that will be called to retrieve all relevant information regarding the recievers
  message_subject = ndb.SuperStringProperty('8', required=True) # non compiled version of message subject
  message_body = ndb.SuperTextProperty('9', required=True) # non compiled version of message body
  outlet = ndb.SuperStringProperty('10', required=True, default='mail')
 
  def run(self, entity, user):
    
      template_values = {'entity' : entity}
      
      return {
              'recipients' : self.message_recievers(entity, user),
              'sender' :  self.message_sender,
              'body' : render_template(self.message_body, template_values),
              'subject' : render_template(self.message_subject, template_values),
              'outlet' : self.outlet,
             }

class MailNotify(Template):
  
  _kind = 58
  
  name = ndb.SuperStringProperty('5', required=True) # description for template editors
  message_sender = ndb.SuperKeyProperty('6', kind='8', required=True) # domain user who will be impersonated as the message sender
  message_reciever = ndb.SuperKeyProperty('7', kind='60', required=True) # DomainRole.key
  message_subject = ndb.SuperStringProperty('8', required=True) # non compiled version of message subject
  message_body = ndb.SuperTextProperty('9', required=True) # non compiled version of message body
 
  def run(self, entity, user):
    
    from app.srv import auth # circular avoid, this will be avoided by placing these templates in app.etc.setup
    
    values = {'user' : user, 'entity' : entity}
    
    if safe_eval(self.condition, values):
      
      domain_users = rule.DomainUser.query(rule.DomainUser.roles.IN(self.message_reciever), 
                                           namespace=self.message_reciever.namespace()).fetch()
      
      users_async = ndb.get_multi_async([auth.User.build_key(long(reciever.key.id())) for reciever in domain_users])
 
      domain_sender_user_key = auth.User.build_key(long(self.message_sender.id()))
      domain_sender_user_async = domain_sender_user_key.get_async()
      
      users = users_async.get_result()
      domain_sender_user = domain_sender_user_async.get_result()
      
      template_values = {'entity' : entity}
      
      return {
              'recipients' : [user.primary_email for user in users],
              'sender' : domain_sender_user.primary_email,
              'body' : render_template(self.message_body, template_values),
              'subject' : render_template(self.message_subject, template_values),
              'outlet' : 'mail',
             }
       
       
class HttpNotify(Template):
  
  _kind = 62
  
  name = ndb.SuperStringProperty('5', required=True) # description for template editors
  message_sender = ndb.SuperKeyProperty('6', kind='8', required=True) # domain user who will be impersonated as the message sender
  message_reciever = ndb.SuperStringProperty('7', kind='60', required=True) # DomainRole.key
  message_subject = ndb.SuperStringProperty('8', required=True) # non compiled version of message subject
  message_body = ndb.SuperTextProperty('9', required=True) # non compiled version of message body
 
  def run(self, entity, user):
    
    from app.srv import auth # circular avoid, this will be avoided by placing these templates in app.etc.setup
    
    values = {'user' : user, 'entity' : entity}
    
    if safe_eval(self.condition, values):
 
      domain_sender_user_key = auth.User.build_key(long(self.message_sender.id()))
      domain_sender_user = domain_sender_user_key.get()
 
      template_values = {'entity' : entity}
      
      return {
              'recipients' : [self.message_reciever], # must be a list to comply to Engine._templates
              'sender' : domain_sender_user.primary_email,
              'body' : render_template(self.message_body, template_values),
              'subject' : render_template(self.message_subject, template_values),
              'entity_key' : entity.key.urlsafe(),
              'outlet' : 'http_notify',
             }
 
    
class Engine:

  @classmethod
  def execute_http_notify(cls, outlet_command):
      pass 
  
  @classmethod
  def execute_mail(cls, outlet_command):
      mail.send_mail(outlet_command['sender'], outlet_command['recipients'],
                      outlet_command['subject'], outlet_command['body'])
  
  @classmethod
  def send(cls, input):
    
    outlet_command = input.get('data')
    
    callback = getattr(cls, 'execute_%s' % outlet_command['outlet'])
    
    if callback:
       callback(outlet_command)

   
  @classmethod
  def _templates(cls, queue, tasks, entity, user, templates):
    
    outlet_commands = []
    
    for template in templates:
        command = template.run(entity, user)
        if command:
           outlet_commands.append(command)
    
    total_outlet_commands = len(outlet_commands)
    
    if total_outlet_commands:      
       commands_per_task = int(math.ceil(total_outlet_commands / settings.OUTLET_TEMPLATES_PER_TASK))
       
       for i in range(0, commands_per_task+1):
         
           cursored_outlet_commands = outlet_commands[settings.OUTLET_TEMPLATES_PER_TASK*i:settings.OUTLET_TEMPLATES_PER_TASK*(i+1)]
            
           for outlet_command in cursored_outlet_commands:
             
               how_many_recipients = int(math.ceil(len(outlet_command['recipients']) / settings.OUTLET_RECIPIENTS_PER_TASK))
               
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
   
    user_key_str = input.get('user_key')
    user = None
    
    if user_key_str:
       user_key = ndb.Key(urlsafe=input.get('user_key'))
       user = user_key.get()
    
    
    queue = taskqueue.Queue(name='notify-send')
    tasks = []
    
    # we are sending payload instead of "params", our server will parse that if it's formatted as json
    templates = get_system_templates(action_key)
    
    cls._templates(queue, tasks, entity, user, templates)
    
    # instead of DomainTemplate it should run Template cuz its polymodel?
    templates = Template.get_local_templates(entity, action_key)
    
    cls._templates(queue, tasks, entity, user, templates)
    
    if tasks:
       queue.add(tasks)
     
     
  @classmethod
  def run(cls, context):
    
    if context.notify.transactional is None:
       context.notify.transacitonal = ndb.in_transaction()
    
    params = {'action_key' : context.action.key.urlsafe(),
              'entity_key' : context.notify.entity.key.urlsafe()}
    
    if context.auth.user.key:
       params['user_key'] = context.auth.user.key.urlsafe()
    
    new_task = taskqueue.add(queue_name='notify', url='/task/notify_prepare',
                             transactional=context.notify.transactional,
                             params=params)
      
    return new_task
