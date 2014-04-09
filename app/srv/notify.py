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
  
  name = ndb.SuperStringProperty('1', required=True)
  action = ndb.SuperKeyProperty('2', kind='56', required=True)
  condition = ndb.SuperStringProperty('3', required=True)
  active = ndb.SuperBooleanProperty('4', required=True, default=True)
  
  _global_role = rule.GlobalRole(
    permissions=[
      # Is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles.
      rule.ActionPermission('61', event.Action.build_key('61-0').urlsafe(), True, "context.auth.user._is_taskqueue")
      ]
    )
  
  _actions = {
    'initiate': event.Action(
      id='61-0',
      arguments={
        'entity_key': ndb.SuperKeyProperty(required=True),
        'caller_user': ndb.SuperKeyProperty(required=True, kind='0'),
        'caller_action' : ndb.SuperVirtualKeyProperty(required=True)
        }
      ),
    'search': event.Action(
      id='61-1',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "name", "operator": "asc"}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'action': {'operators': ['==', '!='], 'type': ndb.SuperVirtualKeyProperty(kind='56')},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty()}
            },
          indexes=[
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['action'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['active'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['action', 'active'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name', 'active'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['action', 'name', 'active'],
             'order_by': [['name', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
            }
          ),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    'prepare': event.Action(
      id='61-2',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      )
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
    action_key = context.input.get('caller_action')
    entity, user = ndb.get_multi([entity_key, user_key])
    templates = cls.get_local_templates(entity, action_key)
    if templates:
      for template in templates:
        template.run(context, user, entity)
    callback.Engine.run(context)
  
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


class CustomNotify(Template):
  
  _kind = 59
  
  message_sender = ndb.SuperStringProperty('5', required=True)
  message_recievers = ndb.SuperPickleProperty('6')
  message_subject = ndb.SuperStringProperty('7', required=True)
  message_body = ndb.SuperTextProperty('8', required=True)
  outlet = ndb.SuperStringProperty('9', required=True, default='58')
  
  def run(self, context, user, entity):
    template_values = {'entity' : entity}
    data = {'action_key': 'send',
            'action_model': self.outlet,
            'recipient': self.message_recievers(entity, user),
            'sender':  self.message_sender,
            'body': render_template(self.message_body, template_values),
            'subject': render_template(self.message_subject, template_values)}
    context.callback.payloads.append(('notify', data))


class MailNotify(Template):
  
  _kind = 58
  
  message_sender = ndb.SuperKeyProperty('6', kind='8', required=True)
  message_reciever = ndb.SuperKeyProperty('7', kind='60', required=True)  # All users that have this role.
  message_subject = ndb.SuperStringProperty('8', required=True)
  message_body = ndb.SuperTextProperty('9', required=True)
  
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
  
  _global_role = rule.GlobalRole(
    permissions=[
      # Is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles.
      # Missing rule action permissions here.
      rule.ActionPermission('58', event.Action.build_key('58-0').urlsafe(), True, "context.auth.user._is_taskqueue")
      ]
    )
  
  _actions = {
    'send': event.Action(
      id='58-0',
      arguments={
        'recipient': ndb.SuperStringProperty(repeated=True),
        'sender': ndb.SuperStringProperty(required=True),
        'subject': ndb.SuperTextProperty(required=True),
        'body': ndb.SuperTextProperty(required=True)
        }
      ),
    'create': event.Action(
      id='58-1',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'action': ndb.SuperVirtualKeyProperty(required=True, kind='56'),
        'condition': ndb.SuperTextProperty(required=True),
        'active': ndb.SuperBooleanProperty(),
        'message_reciever': ndb.SuperKeyProperty(required=True, kind='60'),
        'message_sender': ndb.SuperKeyProperty(required=True, kind='8'),
        'message_subject': ndb.SuperTextProperty(required=True),
        'message_body': ndb.SuperTextProperty(required=True)
        }
      ),
    'update': event.Action(
      id='58-2',
      arguments={
        'key': ndb.SuperKeyProperty(required=True, kind='61'),
        'name': ndb.SuperStringProperty(required=True),
        'action': ndb.SuperVirtualKeyProperty(required=True, kind='56'),
        'condition': ndb.SuperTextProperty(required=True),
        'active': ndb.SuperBooleanProperty(),
        'message_reciever': ndb.SuperKeyProperty(required=True, kind='60'),
        'message_sender': ndb.SuperKeyProperty(required=True, kind='8'),
        'message_subject': ndb.SuperTextProperty(required=True),
        'message_body': ndb.SuperTextProperty(required=True)
        }
      ),
    'delete': event.Action(id='58-3', arguments={'key': ndb.SuperKeyProperty(required=True, kind='61')}),
    'read': event.Action(id='58-5', arguments={'key': ndb.SuperKeyProperty(kind='61', required=True)}),
    'prepare': event.Action(
      id='58-6',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      ),
    'read_records': event.Action(
      id='58-7',
      arguments={
        'key': ndb.SuperKeyProperty(kind='61', required=True),
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
              'action': context.input.get('action'),
              'condition': context.input.get('condition'),
              'active': context.input.get('active'),
              'message_sender': context.input.get('message_sender'),
              'message_subject': context.input.get('message_subject'),
              'message_reciever': context.input.get('message_reciever'),
              'message_body': context.input.get('message_body')}
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
  def prepare(cls, context):
    domain_key = context.input.get('domain')
    context.cruds.domain_key = domain_key
    context.cruds.model = cls
    cruds.Engine.prepare(context)
    # @ todo This is temporary because we will implement ajax widgets for this.
    context.output['users'] = rule.DomainUser.query(namespace=context.output['entity'].key_namespace).fetch()
    context.output['roles'] = rule.DomainRole.query(namespace=context.output['entity'].key_namespace).fetch()
  
  @classmethod
  def read(cls, context):
    context.cruds.model = cls
    cruds.Engine.read(context)
    # @ todo This is temporary because we will implement ajax widgets for this.
    context.output['users'] = rule.DomainUser.query(namespace=context.output['entity'].key_namespace).fetch()
    context.output['roles'] = rule.DomainRole.query(namespace=context.output['entity'].key_namespace).fetch()
  
  @classmethod
  def read_records(cls, context):
    context.cruds.model = cls
    cruds.Engine.read_records(context)
  
  @classmethod
  def send(cls, context):
    mail.send_mail(context.input['sender'], context.input['recipient'],
                   context.input['subject'], context.input['body'])
  
  def run(self, context, user, entity):
    values = {'entity': entity, 'user': user}
    if safe_eval(self.condition, values):
      domain_users = rule.DomainUser.query(rule.DomainUser.roles == self.message_reciever,
                                           namespace=self.message_reciever.namespace()).fetch()
      recievers = ndb.get_multi([auth.User.build_key(long(reciever.key.id())) for reciever in domain_users])
      sender_key = auth.User.build_key(long(self.message_sender.id()))
      sender = sender_key.get()
      template_values = {'entity': entity}
      data = {'action_key': 'send',
              'action_model': '58',
              'recipient': [reciever._primary_email for reciever in recievers],
              'sender': sender._primary_email,
              'body': render_template(self.message_body, template_values),
              'subject': render_template(self.message_subject, template_values)}
      recipients_per_task = int(math.ceil(len(data['recipient']) / settings.RECIPIENTS_PER_TASK))
      data_copy = data.copy()
      del data_copy['recipient']
      for i in range(0, recipients_per_task+1):
        recipients = data['recipient'][settings.RECIPIENTS_PER_TASK*i:settings.RECIPIENTS_PER_TASK*(i+1)]
        if recipients:
          new_data = data_copy.copy()
          new_data['recipient'] = recipients
          context.callback.payloads.append(('notify', new_data))


class HttpNotify(Template):
  
  _kind = 63
  
  message_sender = ndb.SuperKeyProperty('6', kind='8', required=True)
  message_reciever = ndb.SuperStringProperty('7', required=True)
  message_subject = ndb.SuperStringProperty('8', required=True)
  message_body = ndb.SuperTextProperty('9', required=True)
  
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
  
  _global_role = rule.GlobalRole(
    permissions=[
      # Is guest check is not needed on other actions because it requires a loaded domain which then will be checked with roles.
      # Missing rule action permissions here.
      rule.ActionPermission('63', event.Action.build_key('63-0').urlsafe(), True, "context.auth.user._is_taskqueue")
      ]
    )
  
  _actions = {
    'send': event.Action(
      id='63-0',
      arguments={
        'recipient': ndb.SuperStringProperty(repeated=True),
        'sender': ndb.SuperStringProperty(required=True),
        'subject': ndb.SuperTextProperty(required=True),
        'body': ndb.SuperTextProperty(required=True)
        }
      ),
    'create': event.Action(
      id='63-1',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'action': ndb.SuperVirtualKeyProperty(required=True, kind='56'),
        'condition': ndb.SuperTextProperty(required=True),
        'active': ndb.SuperBooleanProperty(),
        'message_reciever': ndb.SuperStringProperty(repeated=True),
        'message_sender': ndb.SuperKeyProperty(required=True, kind='8'),
        'message_subject': ndb.SuperTextProperty(required=True),
        'message_body': ndb.SuperTextProperty(required=True)
        }
      ),
    'update': event.Action(
      id='63-2',
      arguments={
        'key': ndb.SuperKeyProperty(required=True, kind='61'),
        'name': ndb.SuperStringProperty(required=True),
        'action': ndb.SuperVirtualKeyProperty(required=True, kind='56'),
        'condition': ndb.SuperTextProperty(required=True),
        'active': ndb.SuperBooleanProperty(),
        'message_reciever': ndb.SuperStringProperty(repeated=True),
        'message_sender': ndb.SuperKeyProperty(required=True, kind='8'),
        'message_subject': ndb.SuperTextProperty(required=True),
        'message_body': ndb.SuperTextProperty(required=True)
        }
      ),
    'delete': event.Action(id='63-3', arguments={'key': ndb.SuperKeyProperty(required=True, kind='61')}),
    'read': event.Action(id='63-5', arguments={'key': ndb.SuperKeyProperty(kind='61', required=True)}),
    'prepare': event.Action(
      id='63-6',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        }
      ),
    'read_records': event.Action(
      id='63-7',
      arguments={
        'key': ndb.SuperKeyProperty(kind='61', required=True),
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
              'action': context.input.get('action'),
              'condition': context.input.get('condition'),
              'active': context.input.get('active'),
              'message_sender': context.input.get('message_sender'),
              'message_subject': context.input.get('message_subject'),
              'message_reciever': context.input.get('message_reciever'),
              'message_body': context.input.get('message_body')}
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
  def prepare(cls, context):
    domain_key = context.input.get('domain')
    context.cruds.domain_key = domain_key
    context.cruds.model = cls
    cruds.Engine.prepare(context)
    # @ todo This is temporary because we will implement ajax widgets for this.
    context.output['users'] = rule.DomainUser.query(namespace=context.output['entity'].key_namespace).fetch()
    context.output['roles'] = rule.DomainRole.query(namespace=context.output['entity'].key_namespace).fetch()
  
  @classmethod
  def read(cls, context):
    context.cruds.model = cls
    cruds.Engine.read(context)
    # @ todo This is temporary because we will implement ajax widgets for this.
    context.output['users'] = rule.DomainUser.query(namespace=context.output['entity'].key_namespace).fetch()
    context.output['roles'] = rule.DomainRole.query(namespace=context.output['entity'].key_namespace).fetch()
  
  @classmethod
  def read_records(cls, context):
    context.cruds.model = cls
    cruds.Engine.read_records(context)
  
  @classmethod
  def send(cls, context):
    urlfetch.fetch(context.input.get('recipient'), json.dumps(context.input), method=urlfetch.POST)
  
  def run(self, context, user, entity):
    values = {'entity' : entity, 'user' : user}
    if safe_eval(self.condition, values):
      sender_key = auth.User.build_key(long(self.message_sender.id()))
      sender = sender_key.get()
      template_values = {'entity': entity}
      data = {'action_key': 'send',
              'action_model': '63',
              'recipient': self.message_reciever,
              'sender': sender._primary_email,
              'body': render_template(self.message_body, template_values),
              'subject': render_template(self.message_subject, template_values)}
      context.callback.payloads.append(('notify', data))
