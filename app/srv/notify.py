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
from app.plugins import common
from app.plugins import rule as plugin_rule
from app.plugins import log as plugin_log
from app.plugins import callback as plugin_callback
from app.plugins import notify


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
      rule.ActionPermission('61', event.Action.build_key('61-0').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('61', event.Action.build_key('61-1').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('61', event.Action.build_key('61-2').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('61', event.Action.build_key('61-2').urlsafe(), True,
                            "context.rule.entity.namespace_entity.state == 'active' and context.auth.user._is_taskqueue"),
      rule.FieldPermission('61', ['name', 'action', 'condition', 'active'], False, False,
                           "not context.rule.entity.namespace_entity.state == 'active'")
      # @todo Field permissions should be reviewed!
      ]
    )
  
  _actions = {
    'prepare': event.Action(
      id='61-0',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
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
    'initiate': event.Action(
      id='61-2',
      arguments={
        'caller_entity': ndb.SuperKeyProperty(required=True),
        'caller_user': ndb.SuperKeyProperty(required=True, kind='0'),
        'caller_action' : ndb.SuperVirtualKeyProperty(required=True)
        }
      )
    }
  
  _plugins = [
    common.Prepare(
      subscriptions=[
        event.Action.build_key('61-0'),
        event.Action.build_key('61-1')
        ],
      domain_model=True
      ),
    notify.Prepare(
      subscriptions=[
        event.Action.build_key('61-2')
        ]
      ),
    plugin_rule.Prepare(
      subscriptions=[
        event.Action.build_key('61-0'),
        event.Action.build_key('61-1'),
        event.Action.build_key('61-2')
        ],
      skip_user_roles=False,
      strict=False
      ),
    plugin_rule.Exec(
      subscriptions=[
        event.Action.build_key('61-0'),
        event.Action.build_key('61-1'),
        event.Action.build_key('61-2')
        ]
      ),
    notify.Initiate(
      subscriptions=[
        event.Action.build_key('61-2')
        ]
      ),
    plugin_callback.Exec(
      subscriptions=[
        event.Action.build_key('61-2')
        ],
      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'}
      ),
    common.Search(
      subscriptions=[
        event.Action.build_key('61-1')
        ]
      ),
    plugin_rule.Prepare(
      subscriptions=[
        event.Action.build_key('61-1')
        ],
      skip_user_roles=False,
      strict=False
      ),
    plugin_rule.Read(
      subscriptions=[
        event.Action.build_key('61-1')
        ]
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('61-0')
        ],
      output_data={'entity': 'entities.61'}
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('61-1')
        ],
      output_data={'entities': 'entities', 'next_cursor': 'next_cursor', 'more': 'more'}
      )
    ]
  
  """@classmethod
  def initiate(cls, context):
    caller_entity_key = context.input.get('caller_entity')
    caller_user_key = context.input.get('caller_user')
    caller_action_key = context.input.get('caller_action')
    caller_entity, caller_user = ndb.get_multi([caller_entity_key, caller_user_key])
    entity = cls(namespace=caller_entity.key_namespace)
    context.rule.entity = entity
    rule.Engine.run(context)  # @todo If user is taskqueue (as is expected to be) how do we handle it here?
    if not rule.executable(context):
      raise rule.ActionDenied(context)
    templates = cls.query(cls.active == True,
                          cls.action == caller_action_key,
                          namespace=caller_entity.key_namespace).fetch()
    if templates:
      for template in templates:
        template.run(context, caller_user, caller_entity)
    callback.Engine.run(context)
  
  @classmethod
  def search(cls, context):
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    cruds.Engine.search(context)
  
  @classmethod
  def prepare(cls, context):
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    cruds.Engine.prepare(context)"""


class CustomNotify(Template):
  
  _kind = 59
  
  message_sender = ndb.SuperStringProperty('5', required=True)
  message_recievers = ndb.SuperPickleProperty('6')
  message_subject = ndb.SuperStringProperty('7', required=True)
  message_body = ndb.SuperTextProperty('8', required=True)
  outlet = ndb.SuperStringProperty('9', required=True, default='58')
  
  """def run(self, context, user, entity):
    template_values = {'entity' : entity}
    data = {'action_key': 'send',
            'action_model': self.outlet,
            'recipient': self.message_recievers(entity, user),
            'sender': self.message_sender,
            'body': render_template(self.message_body, template_values),
            'subject': render_template(self.message_subject, template_values),
            'caller_entity': entity.key.urlsafe()}
    context.callback.payloads.append(('send', data))"""
  
  def run(self, context):
    template_values = {'entity' : context.caller_entity}
    data = {'action_key': 'send',
            'action_model': self.outlet,
            'recipient': self.message_recievers(context.caller_entity, context.caller_user),
            'sender': self.message_sender,
            'body': render_template(self.message_body, template_values),
            'subject': render_template(self.message_subject, template_values),
            'caller_entity': context.caller_entity.key.urlsafe()}
    context.callback_payloads.append(('send', data))


class MailNotify(Template):
  
  _kind = 58
  
  message_sender = ndb.SuperKeyProperty('6', kind='8', required=True)
  message_reciever = ndb.SuperKeyProperty('7', kind='60', required=True)  # All users that have this role.
  message_subject = ndb.SuperStringProperty('8', required=True)
  message_body = ndb.SuperTextProperty('9', required=True)
  
  _virtual_fields = {
    '_records': log.SuperLocalStructuredRecordProperty('58', repeated=True)
    }
  
  _global_role = rule.GlobalRole(
    permissions=[
      rule.ActionPermission('58', event.Action.build_key('58-0').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('58', event.Action.build_key('58-1').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('58', event.Action.build_key('58-2').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('58', event.Action.build_key('58-3').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('58', event.Action.build_key('58-4').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('58', event.Action.build_key('58-5').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('58', event.Action.build_key('58-6').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('58', event.Action.build_key('58-6').urlsafe(), True,
                            "context.rule.entity.namespace_entity.state == 'active' and context.auth.user._is_taskqueue"),
      rule.FieldPermission('58', ['name', 'action', 'condition', 'active', 'message_sender',
                                  'message_reciever', 'message_subject', 'message_body', '_records'], False, False,
                           "not context.rule.entity.namespace_entity.state == 'active'")
      # @todo Field permissions should be reviewed!
      ]
    )
  
  _actions = {
    'prepare': event.Action(
      id='58-0',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
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
    'read': event.Action(id='58-2', arguments={'key': ndb.SuperKeyProperty(kind='61', required=True)}),
    'update': event.Action(
      id='58-3',
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
    'delete': event.Action(id='58-4', arguments={'key': ndb.SuperKeyProperty(required=True, kind='61')}),
    'read_records': event.Action(
      id='58-5',
      arguments={
        'key': ndb.SuperKeyProperty(kind='61', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    'send': event.Action(
      id='58-6',
      arguments={
        'recipient': ndb.SuperStringProperty(repeated=True),  # @todo This field is mandatory in mail.send_mail() function, which this action eventually calls!
        'sender': ndb.SuperStringProperty(required=True),
        'subject': ndb.SuperTextProperty(required=True),
        'body': ndb.SuperTextProperty(required=True),
        'caller_entity': ndb.SuperKeyProperty(required=True)
        }
      )
    }
  
  _plugins = [
    common.Prepare(
      subscriptions=[
        event.Action.build_key('58-0'),
        event.Action.build_key('58-1')
        ],
      domain_model=True
      ),
    notify.Prepare(
      subscriptions=[
        event.Action.build_key('58-6')
        ]
      ),
    common.Read(
      subscriptions=[
        event.Action.build_key('58-2'),
        event.Action.build_key('58-3'),
        event.Action.build_key('58-4'),
        event.Action.build_key('58-5')
        ]
      ),
    plugin_rule.Prepare(
      subscriptions=[
        event.Action.build_key('58-0'),
        event.Action.build_key('58-1'),
        event.Action.build_key('58-2'),
        event.Action.build_key('58-3'),
        event.Action.build_key('58-4'),
        event.Action.build_key('58-5'),
        event.Action.build_key('58-6')
        ],
      skip_user_roles=False,
      strict=False
      ),
    plugin_rule.Exec(
      subscriptions=[
        event.Action.build_key('58-0'),
        event.Action.build_key('58-1'),
        event.Action.build_key('58-2'),
        event.Action.build_key('58-3'),
        event.Action.build_key('58-4'),
        event.Action.build_key('58-5'),
        event.Action.build_key('58-6')
        ]
      ),
    notify.MailSend(
      subscriptions=[
        event.Action.build_key('58-6')
        ]
      ),
    common.SetValue(
      subscriptions=[
        event.Action.build_key('58-1'),
        event.Action.build_key('58-3')
        ],
      fields={
        'name': 'name',
        'action': 'action',
        'condition': 'condition',
        'active': 'active',
        'message_sender': 'message_sender',
        'message_subject': 'message_subject',
        'message_reciever': 'message_reciever',
        'message_body': 'message_body'
        }
      ),
    plugin_rule.Write(
      subscriptions=[
        event.Action.build_key('58-1'),
        event.Action.build_key('58-3')
        ],
      transactional=True
      ),
    common.Write(
      subscriptions=[
        event.Action.build_key('58-1'),
        event.Action.build_key('58-3')
        ],
      transactional=True
      ),
    common.Delete(
      subscriptions=[
        event.Action.build_key('58-4')
        ],
      transactional=True
      ),
    plugin_log.Entity(
      subscriptions=[
        event.Action.build_key('58-1'),
        event.Action.build_key('58-3'),
        event.Action.build_key('58-4')
        ],
      transactional=True
      ),
    plugin_log.Write(
      subscriptions=[
        event.Action.build_key('58-1'),
        event.Action.build_key('58-3'),
        event.Action.build_key('58-4')
        ],
      transactional=True
      ),
    plugin_rule.Read(
      subscriptions=[
        event.Action.build_key('58-1'),
        event.Action.build_key('58-3'),
        event.Action.build_key('58-4')
        ],
      transactional=True
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('58-1'),
        event.Action.build_key('58-3'),
        event.Action.build_key('58-4')
        ],
      transactional=True,
      output_data={'entity': 'entities.58'}
      ),
    plugin_callback.Payload(
      subscriptions=[
        event.Action.build_key('58-1'),
        event.Action.build_key('58-3'),
        event.Action.build_key('58-4')
        ],
      transactional=True,
      queue = 'notify',
      static_data = {'action_key': 'initiate', 'action_model': '61'},
      dynamic_data = {'caller_entity': 'entities.58.key_urlsafe'}
      ),
    plugin_callback.Exec(
      subscriptions=[
        event.Action.build_key('58-1'),
        event.Action.build_key('58-3'),
        event.Action.build_key('58-4')
        ],
      transactional=True,
      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'}
      ),
    plugin_log.Read(
      subscriptions=[
        event.Action.build_key('58-5')
        ]
      ),
    plugin_rule.Read(
      subscriptions=[
        event.Action.build_key('58-2'),
        event.Action.build_key('58-5')
        ]
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('58-0'),
        event.Action.build_key('58-2')
        ],
      output_data={'entity': 'entities.58'}
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('58-5')
        ],
      output_data={'entity': 'entities.58', 'next_cursor': 'next_cursor', 'more': 'more'}
      )
    ]
  
  """@classmethod
  def delete(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.delete(context)
  
  @classmethod
  def complete_save(cls, context):
    values = {'name': context.input.get('name'),
              'action': context.input.get('action'),
              'condition': context.input.get('condition'),
              'active': context.input.get('active'),
              'message_sender': context.input.get('message_sender'),
              'message_subject': context.input.get('message_subject'),
              'message_reciever': context.input.get('message_reciever'),  # @todo In nav.py we do "if role.key_namespace != entity.key_namespace:". Shall we do the same with this variable?
              'message_body': context.input.get('message_body')}
    return values
  
  @classmethod
  def create(cls, context):
    values = cls.complete_save(context)
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    context.cruds.values = values
    cruds.Engine.create(context)
  
  @classmethod
  def update(cls, context):
    values = cls.complete_save(context)
    context.cruds.entity = context.input.get('key').get()
    context.cruds.values = values
    cruds.Engine.update(context)
  
  @classmethod
  def prepare(cls, context):
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    cruds.Engine.prepare(context)
    # @ todo This is temporary because we will implement ajax widgets for this.
    context.output['users'] = rule.DomainUser.query(namespace=context.output['entity'].key_namespace).fetch()
    context.output['roles'] = rule.DomainRole.query(namespace=context.output['entity'].key_namespace).fetch()
  
  @classmethod
  def read(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.read(context)
    # @ todo This is temporary because we will implement ajax widgets for this.
    context.output['users'] = rule.DomainUser.query(namespace=context.output['entity'].key_namespace).fetch()
    context.output['roles'] = rule.DomainRole.query(namespace=context.output['entity'].key_namespace).fetch()
  
  @classmethod
  def read_records(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.read_records(context)
  
  @classmethod
  def send(cls, context):
    caller_entity_key = context.input.get('caller_entity')
    caller_entity = caller_entity_key.get()
    entity = cls(namespace=caller_entity.key_namespace)
    context.rule.entity = entity
    rule.Engine.run(context)  # @todo If user is taskqueue (as is expected to be) how do we handle it here?
    if not rule.executable(context):
      raise rule.ActionDenied(context)
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
              'subject': render_template(self.message_subject, template_values),
              'caller_entity': entity.key.urlsafe()}
      recipients_per_task = int(math.ceil(len(data['recipient']) / settings.RECIPIENTS_PER_TASK))
      data_copy = data.copy()
      del data_copy['recipient']
      for i in range(0, recipients_per_task+1):
        recipients = data['recipient'][settings.RECIPIENTS_PER_TASK*i:settings.RECIPIENTS_PER_TASK*(i+1)]
        if recipients:
          new_data = data_copy.copy()
          new_data['recipient'] = recipients
          context.callback.payloads.append(('send', new_data))"""
  
  def run(self, context):
    values = {'entity': context.caller_entity, 'user': context.caller_user}
    if safe_eval(self.condition, values):
      domain_users = rule.DomainUser.query(rule.DomainUser.roles == self.message_reciever,
                                           namespace=self.message_reciever.namespace()).fetch()
      recievers = ndb.get_multi([auth.User.build_key(long(reciever.key.id())) for reciever in domain_users])
      sender_key = auth.User.build_key(long(self.message_sender.id()))
      sender = sender_key.get()
      template_values = {'entity': context.caller_entity}
      data = {'action_key': 'send',
              'action_model': '58',
              'recipient': [reciever._primary_email for reciever in recievers],
              'sender': sender._primary_email,
              'body': render_template(self.message_body, template_values),
              'subject': render_template(self.message_subject, template_values),
              'caller_entity': context.caller_entity.key.urlsafe()}
      recipients_per_task = int(math.ceil(len(data['recipient']) / settings.RECIPIENTS_PER_TASK))
      data_copy = data.copy()
      del data_copy['recipient']
      for i in range(0, recipients_per_task+1):
        recipients = data['recipient'][settings.RECIPIENTS_PER_TASK*i:settings.RECIPIENTS_PER_TASK*(i+1)]
        if recipients:
          new_data = data_copy.copy()
          new_data['recipient'] = recipients
          context.callback_payloads.append(('send', new_data))


class HttpNotify(Template):
  
  _kind = 63
  
  message_sender = ndb.SuperKeyProperty('6', kind='8', required=True)
  message_reciever = ndb.SuperStringProperty('7', required=True)
  message_subject = ndb.SuperStringProperty('8', required=True)
  message_body = ndb.SuperTextProperty('9', required=True)
  
  _virtual_fields = {
    '_records': log.SuperLocalStructuredRecordProperty('63', repeated=True)
    }
  
  _global_role = rule.GlobalRole(
    permissions=[
      rule.ActionPermission('63', event.Action.build_key('63-0').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('63', event.Action.build_key('63-1').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('63', event.Action.build_key('63-2').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('63', event.Action.build_key('63-3').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('63', event.Action.build_key('63-4').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('63', event.Action.build_key('63-5').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('63', event.Action.build_key('63-6').urlsafe(), False,
                            "not context.rule.entity.namespace_entity.state == 'active'"),
      rule.ActionPermission('63', event.Action.build_key('63-6').urlsafe(), True,
                            "context.rule.entity.namespace_entity.state == 'active' and context.auth.user._is_taskqueue"),
      rule.FieldPermission('63', ['name', 'action', 'condition', 'active', 'message_sender',
                                  'message_reciever', 'message_subject', 'message_body', '_records'], False, False,
                           "not context.rule.entity.namespace_entity.state == 'active'")
      # @todo Field permissions should be reviewed!
      ]
    )
  
  _actions = {
    'prepare': event.Action(
      id='63-0',
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
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
        'message_reciever': ndb.SuperStringProperty(required=True),
        'message_sender': ndb.SuperKeyProperty(required=True, kind='8'),
        'message_subject': ndb.SuperTextProperty(required=True),
        'message_body': ndb.SuperTextProperty(required=True)
        }
      ),
    'read': event.Action(id='63-2', arguments={'key': ndb.SuperKeyProperty(kind='61', required=True)}),
    'update': event.Action(
      id='63-3',
      arguments={
        'key': ndb.SuperKeyProperty(required=True, kind='61'),
        'name': ndb.SuperStringProperty(required=True),
        'action': ndb.SuperVirtualKeyProperty(required=True, kind='56'),
        'condition': ndb.SuperTextProperty(required=True),
        'active': ndb.SuperBooleanProperty(),
        'message_reciever': ndb.SuperStringProperty(required=True),
        'message_sender': ndb.SuperKeyProperty(required=True, kind='8'),
        'message_subject': ndb.SuperTextProperty(required=True),
        'message_body': ndb.SuperTextProperty(required=True)
        }
      ),
    'delete': event.Action(id='63-4', arguments={'key': ndb.SuperKeyProperty(required=True, kind='61')}),
    'read_records': event.Action(
      id='63-5',
      arguments={
        'key': ndb.SuperKeyProperty(kind='61', required=True),
        'next_cursor': ndb.SuperStringProperty()
        }
      ),
    'send': event.Action(
      id='63-6',
      arguments={
        'recipient': ndb.SuperStringProperty(required=True),
        'sender': ndb.SuperStringProperty(required=True),
        'subject': ndb.SuperTextProperty(required=True),
        'body': ndb.SuperTextProperty(required=True),
        'caller_entity': ndb.SuperKeyProperty(required=True)
        }
      )
    }
  
  _plugins = [
    common.Prepare(
      subscriptions=[
        event.Action.build_key('63-0'),
        event.Action.build_key('63-1')
        ],
      domain_model=True
      ),
    notify.Prepare(
      subscriptions=[
        event.Action.build_key('63-6')
        ]
      ),
    common.Read(
      subscriptions=[
        event.Action.build_key('63-2'),
        event.Action.build_key('63-3'),
        event.Action.build_key('63-4'),
        event.Action.build_key('63-5')
        ]
      ),
    plugin_rule.Prepare(
      subscriptions=[
        event.Action.build_key('63-0'),
        event.Action.build_key('63-1'),
        event.Action.build_key('63-2'),
        event.Action.build_key('63-3'),
        event.Action.build_key('63-4'),
        event.Action.build_key('63-5'),
        event.Action.build_key('63-6')
        ],
      skip_user_roles=False,
      strict=False
      ),
    plugin_rule.Exec(
      subscriptions=[
        event.Action.build_key('63-0'),
        event.Action.build_key('63-1'),
        event.Action.build_key('63-2'),
        event.Action.build_key('63-3'),
        event.Action.build_key('63-4'),
        event.Action.build_key('63-5'),
        event.Action.build_key('63-6')
        ]
      ),
    notify.HttpSend(
      subscriptions=[
        event.Action.build_key('63-6')
        ]
      ),
    common.SetValue(
      subscriptions=[
        event.Action.build_key('63-1'),
        event.Action.build_key('63-3')
        ],
      fields={
        'name': 'name',
        'action': 'action',
        'condition': 'condition',
        'active': 'active',
        'message_sender': 'message_sender',
        'message_subject': 'message_subject',
        'message_reciever': 'message_reciever',
        'message_body': 'message_body'
        }
      ),
    plugin_rule.Write(
      subscriptions=[
        event.Action.build_key('63-1'),
        event.Action.build_key('63-3')
        ],
      transactional=True
      ),
    common.Write(
      subscriptions=[
        event.Action.build_key('63-1'),
        event.Action.build_key('63-3')
        ],
      transactional=True
      ),
    common.Delete(
      subscriptions=[
        event.Action.build_key('63-4')
        ],
      transactional=True
      ),
    plugin_log.Entity(
      subscriptions=[
        event.Action.build_key('63-1'),
        event.Action.build_key('63-3'),
        event.Action.build_key('63-4')
        ],
      transactional=True
      ),
    plugin_log.Write(
      subscriptions=[
        event.Action.build_key('63-1'),
        event.Action.build_key('63-3'),
        event.Action.build_key('63-4')
        ],
      transactional=True
      ),
    plugin_rule.Read(
      subscriptions=[
        event.Action.build_key('63-1'),
        event.Action.build_key('63-3'),
        event.Action.build_key('63-4')
        ],
      transactional=True
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('63-1'),
        event.Action.build_key('63-3'),
        event.Action.build_key('63-4')
        ],
      transactional=True,
      output_data={'entity': 'entities.63'}
      ),
    plugin_callback.Payload(
      subscriptions=[
        event.Action.build_key('63-1'),
        event.Action.build_key('63-3'),
        event.Action.build_key('63-4')
        ],
      transactional=True,
      queue = 'notify',
      static_data = {'action_key': 'initiate', 'action_model': '61'},
      dynamic_data = {'caller_entity': 'entities.63.key_urlsafe'}
      ),
    plugin_callback.Exec(
      subscriptions=[
        event.Action.build_key('63-1'),
        event.Action.build_key('63-3'),
        event.Action.build_key('63-4')
        ],
      transactional=True,
      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'}
      ),
    plugin_log.Read(
      subscriptions=[
        event.Action.build_key('63-5')
        ]
      ),
    plugin_rule.Read(
      subscriptions=[
        event.Action.build_key('63-2'),
        event.Action.build_key('63-5')
        ]
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('63-0'),
        event.Action.build_key('63-2')
        ],
      output_data={'entity': 'entities.63'}
      ),
    common.Output(
      subscriptions=[
        event.Action.build_key('63-5')
        ],
      output_data={'entity': 'entities.63', 'next_cursor': 'next_cursor', 'more': 'more'}
      )
    ]
  
  """@classmethod
  def delete(cls, context):
    context.cruds.entity = context.input.get('key').get()
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
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    context.cruds.values = values
    cruds.Engine.create(context)
  
  @classmethod
  def update(cls, context):
    values = cls.complete_save(context)
    context.cruds.entity = context.input.get('key').get()
    context.cruds.values = values
    cruds.Engine.update(context)
  
  @classmethod
  def prepare(cls, context):
    context.cruds.entity = cls(namespace=context.input.get('domain').urlsafe())
    cruds.Engine.prepare(context)
    # @ todo This is temporary because we will implement ajax widgets for this.
    context.output['users'] = rule.DomainUser.query(namespace=context.output['entity'].key_namespace).fetch()
    context.output['roles'] = rule.DomainRole.query(namespace=context.output['entity'].key_namespace).fetch()
  
  @classmethod
  def read(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.read(context)
    # @ todo This is temporary because we will implement ajax widgets for this.
    context.output['users'] = rule.DomainUser.query(namespace=context.output['entity'].key_namespace).fetch()
    context.output['roles'] = rule.DomainRole.query(namespace=context.output['entity'].key_namespace).fetch()
  
  @classmethod
  def read_records(cls, context):
    context.cruds.entity = context.input.get('key').get()
    cruds.Engine.read_records(context)
  
  @classmethod
  def send(cls, context):
    caller_entity_key = context.input.get('caller_entity')
    caller_entity = caller_entity_key.get()
    entity = cls(namespace=caller_entity.key_namespace)
    context.rule.entity = entity
    rule.Engine.run(context)  # @todo If user is taskqueue (as is expected to be) how do we handle it here?
    if not rule.executable(context):
      raise rule.ActionDenied(context)
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
              'subject': render_template(self.message_subject, template_values),
              'caller_entity': entity.key.urlsafe()}
      context.callback.payloads.append(('send', data))"""
  
  def run(self, context):
    values = {'entity': context.caller_entity, 'user': context.caller_user}
    if safe_eval(self.condition, values):
      sender_key = auth.User.build_key(long(self.message_sender.id()))
      sender = sender_key.get()
      template_values = {'entity': context.caller_entity}
      data = {'action_key': 'send',
              'action_model': '63',
              'recipient': self.message_reciever,
              'sender': sender._primary_email,
              'body': render_template(self.message_body, template_values),
              'subject': render_template(self.message_subject, template_values),
              'caller_entity': context.caller_entity.key.urlsafe()}
      context.callback_payloads.append(('send', data))
