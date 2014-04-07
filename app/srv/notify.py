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
from app.srv import auth, callback, rule, event, cruds, log

sandboxed_jinja = SandboxedEnvironment()    
    
def render_template(template_as_string, values={}):
    from_string_template = sandboxed_jinja.from_string(template_as_string)
    return from_string_template.render(values)
 
    
class Template(ndb.BasePoly):
  
  _kind = 61
 
  action = ndb.SuperKeyProperty('1', kind='56', required=True) # action to which it subscribes
  condition = ndb.SuperStringProperty('2', required=True) # condition which has to be satisfied in order for template to generate message instance
  active = ndb.SuperBooleanProperty('3', required=True, default=True) # usefull for turnig it on/of
  
  _global_role = rule.GlobalRole(permissions=[
      # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
      rule.ActionPermission('61', event.Action.build_key('61-0').urlsafe(), True, "context.auth.user._is_taskqueue"),                        
   ])  
  
  _actions = {
     'initiate' : event.Action(id='61-0',
                                  arguments={
                                    'entity_key' : ndb.SuperKeyProperty(required=True),
                                    'caller_user' : ndb.SuperKeyProperty(required=True, kind='0'),
                                    'caller_action' : ndb.SuperStringProperty(required=True),
                                }),
   }
 
  @classmethod
  def get_local_templates(cls, entity, action_key):
    templates = cls.query(cls.active == True,
                          cls.action == action_key,
                          namespace=entity.key_namespace).fetch()
    return templates
  
  @classmethod
  def initiate(cls, context):
    
    entity_key = context.input.get('entity_key')
    user_key = context.input.get('caller_user')
    action_key = ndb.Key(urlsafe=context.input.get('caller_action'))
 
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
      
      context.callbacks.payloads.append(('notify', data))
      
       
class MailNotify(Template):
  
  _kind = 58
  
  name = ndb.SuperStringProperty('5', required=True) # description for template editors
  message_sender = ndb.SuperKeyProperty('6', kind='8', required=True) # domain user who will be impersonated as the message sender
  message_reciever = ndb.SuperKeyProperty('7', kind='60', required=True) # DomainRole.key
  message_subject = ndb.SuperStringProperty('8', required=True) # non compiled version of message subject
  message_body = ndb.SuperTextProperty('9', required=True) # non compiled version of message body
  
  _virtual_fields = {
    '_records': log.SuperLocalStructuredRecordProperty('58', repeated=True)
  }
  # 0 send
  # 1 create
  # 2 update
  # 3 delete
  # 4 search
  # 5 read
  # 6 prepare
  # 7 read records 
  
  _global_role = rule.GlobalRole(permissions=[
      # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles    
      # missing rule action permissions here
      rule.ActionPermission('58', event.Action.build_key('58-0').urlsafe(), True, "context.auth.user._is_taskqueue"),                             
   ])  
  
  _actions = {
     'send' : event.Action(id='58-0',
                                  arguments={
                                    'recipient' : ndb.SuperStringProperty(required=True, repeated=True),
                                    'sender' : ndb.SuperStringProperty(required=True),
                                    'subject' : ndb.SuperTextProperty(required=True),
                                    'body' : ndb.SuperTextProperty(required=True)
                                }),
     'create' : event.Action(id='58-1',
                                  arguments={
                                    'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                                    'recipient' : ndb.SuperStringProperty(required=True, repeated=True),
                                    'sender' : ndb.SuperStringProperty(required=True),
                                    'subject' : ndb.SuperTextProperty(required=True),
                                    'body' : ndb.SuperTextProperty(required=True)
                                }),
     'update' : event.Action(id='58-2',
                                  arguments={
                                    'key' : ndb.SuperKeyProperty(required=True, kind='58'),
                                    'recipient' : ndb.SuperStringProperty(required=True, repeated=True),
                                    'sender' : ndb.SuperStringProperty(required=True),
                                    'subject' : ndb.SuperTextProperty(required=True),
                                    'body' : ndb.SuperTextProperty(required=True)
                                }),
     'delete' : event.Action(id='58-3',
                                  arguments={
                                    'key' : ndb.SuperKeyProperty(required=True, kind='58')
                                }),
     'search': event.Action(
       id='58-4',
       arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "name", "operator": "asc"}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            },
          indexes=[
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']]]},
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
            }
          ),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
     'read': event.Action(id='58-5', arguments={'key': ndb.SuperKeyProperty(kind='58', required=True)}),
     'prepare': event.Action(
        id='58-6',
        arguments={
          'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      ),
     'read_records': event.Action(
        id='58-7',
        arguments={
          'key': ndb.SuperKeyProperty(kind='58', required=True),
          'next_cursor': ndb.SuperStringProperty()
        }
      )
   }
  
  @classmethod
  def delete(cls, context):
    context.cruds.model = cls
    cruds.Engine.delete(context)
  
  @classmethod
  def complete_save(cls, context):
 
    values = {'name': context.input.get('name'),
              'message_sender': context.input.get('message_sender'),
              'message_subject': context.input.get('message_subject'),
              'message_reciever': context.input.get('message_reciever'),
              'message_body': context.input.get('message_body'),
              }
    return values
  
  @classmethod
  def create(cls, context):
    values = cls.complete_save(context)
    context.cruds.domain_key = context.input.get('domain')
    context.cruds.model = cls
    context.cruds.values = values
    cruds.Engine.create(context)
  
  @classmethod
  def update(cls, context):
    values = cls.complete_save(context)
    context.cruds.model = cls
    context.cruds.values = values
    cruds.Engine.update(context)
  
  @classmethod
  def search(cls, context):
    context.cruds.model = cls
    context.cruds.domain_key = context.input.get('domain')
    cruds.Engine.search(context)
  
  @classmethod
  def prepare(cls, context):
    domain_key = context.input.get('domain')
    context.cruds.domain_key = domain_key
    context.cruds.model = cls
    cruds.Engine.prepare(context)
  
  @classmethod
  def read(cls, context):
    context.cruds.model = cls
    cruds.Engine.read(context)
  
  @classmethod
  def read_records(cls, context):
    context.cruds.model = cls
    cruds.Engine.read_records(context)
     
  @classmethod
  def send(cls, context):
    
    input = context.input
    
    mail.send_mail(input['sender'], input['recipient'],
                      input['subject'], input['body'])
 
  def run(self, entity, user, context):
 
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
         context.callbacks.payloads.append(('notify', new_outlet_command))
       
       
class HttpNotify(Template):
  
  _kind = 63
  
  name = ndb.SuperStringProperty('5', required=True) # description for template editors
  message_sender = ndb.SuperKeyProperty('6', kind='8', required=True) # domain user who will be impersonated as the message sender
  message_reciever = ndb.SuperStringProperty('7', required=True) # DomainRole.key
  message_subject = ndb.SuperStringProperty('8', required=True) # non compiled version of message subject
  message_body = ndb.SuperTextProperty('9', required=True) # non compiled version of message body
  
  _virtual_fields = {
    '_records': log.SuperLocalStructuredRecordProperty('63', repeated=True)
    }
  
  # 0 send
  # 1 create
  # 2 update
  # 3 delete
  # 4 search
  # 5 read
  # 6 prepare
  # 7 read records 
  
  _global_role = rule.GlobalRole(permissions=[
      # is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles   
      # missing rule action permissions here 
      rule.ActionPermission('63', event.Action.build_key('63-0').urlsafe(), True, "context.auth.user._is_taskqueue"),                              
   ])  
  
  _actions = {
     'send' : event.Action(id='63-0',
                                  arguments={
                                    'recipient' : ndb.SuperStringProperty(required=True, repeated=True),
                                    'sender' : ndb.SuperStringProperty(required=True),
                                    'subject' : ndb.SuperTextProperty(required=True),
                                    'body' : ndb.SuperTextProperty(required=True)
                                }),
     'create' : event.Action(id='63-1',
                                  arguments={
                                    'domain' : ndb.SuperKeyProperty(kind='6', required=True),
                                    'recipient' : ndb.SuperStringProperty(required=True, repeated=True),
                                    'sender' : ndb.SuperStringProperty(required=True),
                                    'subject' : ndb.SuperTextProperty(required=True),
                                    'body' : ndb.SuperTextProperty(required=True)
                                }),
     'update' : event.Action(id='63-2',
                                  arguments={
                                    'key' : ndb.SuperKeyProperty(required=True, kind='63'),
                                    'recipient' : ndb.SuperStringProperty(required=True, repeated=True),
                                    'sender' : ndb.SuperStringProperty(required=True),
                                    'subject' : ndb.SuperTextProperty(required=True),
                                    'body' : ndb.SuperTextProperty(required=True)
                                }),
     'delete' : event.Action(id='63-3',
                                  arguments={
                                    'key' : ndb.SuperKeyProperty(required=True, kind='63')
                                }),
     'search': event.Action(
       id='63-4',
       arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "name", "operator": "asc"}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            },
          indexes=[
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']]]},
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
            }
          ),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
     'read': event.Action(id='63-5', arguments={'key': ndb.SuperKeyProperty(kind='63', required=True)}),
     'prepare': event.Action(
        id='63-6',
        arguments={
          'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      ),
     'read_records': event.Action(
        id='63-7',
        arguments={
          'key': ndb.SuperKeyProperty(kind='63', required=True),
          'next_cursor': ndb.SuperStringProperty()
        }
      )
   }
  
  @classmethod
  def delete(cls, context):
    context.cruds.model = cls
    cruds.Engine.delete(context)
  
  @classmethod
  def complete_save(cls, context):
 
    values = {'name': context.input.get('name'),
              'message_sender': context.input.get('message_sender'),
              'message_subject': context.input.get('message_subject'),
              'message_reciever': context.input.get('message_reciever'),
              'message_body': context.input.get('message_body'),
              }
    return values
  
  @classmethod
  def create(cls, context):
    values = cls.complete_save(context)
    context.cruds.domain_key = context.input.get('domain')
    context.cruds.model = cls
    context.cruds.values = values
    cruds.Engine.create(context)
  
  @classmethod
  def update(cls, context):
    values = cls.complete_save(context)
    context.cruds.model = cls
    context.cruds.values = values
    cruds.Engine.update(context)
  
  @classmethod
  def search(cls, context):
    context.cruds.model = cls
    context.cruds.domain_key = context.input.get('domain')
    cruds.Engine.search(context)
  
  @classmethod
  def prepare(cls, context):
    domain_key = context.input.get('domain')
    context.cruds.domain_key = domain_key
    context.cruds.model = cls
    cruds.Engine.prepare(context)
  
  @classmethod
  def read(cls, context):
    context.cruds.model = cls
    cruds.Engine.read(context)
  
  @classmethod
  def read_records(cls, context):
    context.cruds.model = cls
    cruds.Engine.read_records(context)
    
  @classmethod
  def send(cls, context):
    urlfetch.fetch(context.input.get('recipient'), json.dumps(context.input), method=urlfetch.POST)
 
  def run(self, entity, user, context):
 
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
      
      context.callbacks.payloads.append(('notify', data))