# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import math

from jinja2.sandbox import SandboxedEnvironment


from app import orm, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.notify import *


sandboxed_jinja = SandboxedEnvironment()

def render_template(template_as_string, values={}):
  from_string_template = sandboxed_jinja.from_string(template_as_string)
  return from_string_template.render(values)


class Template(orm.BasePolyExpando):
  
  _kind = 81
  
  _default_indexed = False


class CustomTemplate(Template):
  
  _kind = 59
  
  message_recievers = orm.SuperPickleProperty('1', required=True, indexed=False)
  message_subject = orm.SuperStringProperty('2', required=True, indexed=False)
  message_body = orm.SuperTextProperty('3', required=True)
  outlet = orm.SuperStringProperty('4', required=True, default='send_mail', indexed=False)
  
  def run(self, **kwargs):
    callbacks = []
    template_values = {'entity': kwargs['caller_entity']}
    data = {'action_id': self.outlet,
            'action_model': '61',
            'recipient': self.message_recievers(kwargs['caller_entity'], kwargs['caller_user']),
            'body': render_template(self.message_body, template_values),
            'subject': render_template(self.message_subject, template_values),
            'caller_entity': kwargs['caller_entity'].key.urlsafe()}
    callbacks.append(('send', data))
    return callbacks


class MailTemplate(Template):
  
  _kind = 58
  
  message_reciever = orm.SuperKeyProperty('1', kind='60', required=True, indexed=False)  # All users that have this role.
  message_subject = orm.SuperStringProperty('2', required=True, indexed=False)
  message_body = orm.SuperTextProperty('3', required=True)
  
  def run(self, **kwargs):
    callbacks = []
    DomainUser = kwargs['models']['DomainUser']
    domain_users = DomainUser.query(DomainUser.roles == self.message_reciever,
                                    namespace=self.message_reciever.namespace()).fetch()
    recievers = orm.get_multi([orm.Key('0', long(reciever.key.id())) for reciever in domain_users])
    template_values = {'entity': kwargs['caller_entity']}
    data = {'action_id': 'send_mail',
            'action_model': '61',
            'recipient': [reciever._primary_email for reciever in recievers],
            'body': render_template(self.message_body, template_values),
            'subject': render_template(self.message_subject, template_values),
            'caller_entity': kwargs['caller_entity'].key.urlsafe()}
    recipients_per_task = int(math.ceil(len(data['recipient']) / settings.RECIPIENTS_PER_TASK))
    data_copy = data.copy()
    del data_copy['recipient']
    for i in range(0, recipients_per_task+1):
      recipients = data['recipient'][settings.RECIPIENTS_PER_TASK*i:settings.RECIPIENTS_PER_TASK*(i+1)]
      if recipients:
        new_data = data_copy.copy()
        new_data['recipient'] = recipients
        callbacks.append(('send', new_data))
    return callbacks


class HttpTemplate(Template):
  
  _kind = 63
  
  message_reciever = orm.SuperStringProperty('1', required=True, indexed=False)
  message_subject = orm.SuperStringProperty('2', required=True, indexed=False)
  message_body = orm.SuperTextProperty('3', required=True)
  
  def run(self, **kwargs):
    callbacks = []
    template_values = {'entity': kwargs['caller_entity']}
    data = {'action_id': 'send_http',
            'action_model': '61',
            'recipient': self.message_reciever,
            'body': render_template(self.message_body, template_values),
            'subject': render_template(self.message_subject, template_values),
            'caller_entity': kwargs['caller_entity'].key.urlsafe()}
    callbacks.append(('send', data))
    return callbacks


class Notification(orm.BaseExpando):
  
  _kind = 61
  
  name = orm.SuperStringProperty('1', required=True)
  action = orm.SuperKeyProperty('2', kind='56', required=True)
  condition = orm.SuperStringProperty('3', required=True, indexed=False)
  active = orm.SuperBooleanProperty('4', required=True, default=True)
  templates = orm.SuperPickleProperty('5', required=True, indexed=False, compressed=False)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': orm.SuperRecordProperty('61')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('61', [orm.Action.build_key('61', 'prepare'),
                                  orm.Action.build_key('61', 'create'),
                                  orm.Action.build_key('61', 'read'),
                                  orm.Action.build_key('61', 'update'),
                                  orm.Action.build_key('61', 'delete'),
                                  orm.Action.build_key('61', 'search')], False, 'entity._original.namespace_entity._original.state != "active"'),
      orm.ActionPermission('61', [orm.Action.build_key('61', 'initiate'),
                                  orm.Action.build_key('61', 'send_mail'),
                                  orm.Action.build_key('61', 'send_http')], False, 'True'),
      orm.ActionPermission('61', [orm.Action.build_key('61', 'initiate'),
                                  orm.Action.build_key('61', 'send_mail'),
                                  orm.Action.build_key('61', 'send_http')], True,
                           'entity._original.namespace_entity._original.state == "active" and user._is_taskqueue'),
      orm.FieldPermission('61', ['name', 'action', 'condition', 'active', 'templates', '_records'], False, False,
                          'entity._original.namespace_entity._original.state != "active"')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('61', 'prepare'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_notification'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('61', 'create'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'name': orm.SuperStringProperty(required=True),
        'action': orm.SuperVirtualKeyProperty(required=True, kind='56'),
        'condition': orm.SuperTextProperty(required=True),
        'active': orm.SuperBooleanProperty(),
        'templates': orm.SuperJsonProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            NotificationSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_notification'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('61', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='61', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_notification'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('61', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(required=True, kind='61'),
        'name': orm.SuperStringProperty(required=True),
        'action': orm.SuperVirtualKeyProperty(required=True, kind='56'),
        'condition': orm.SuperTextProperty(required=True),
        'active': orm.SuperBooleanProperty(),
        'templates': orm.SuperJsonProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            NotificationSet(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_notification'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('61', 'delete'),
      arguments={
        'key': orm.SuperKeyProperty(required=True, kind='61')
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Delete(),
            Set(cfg={'d': {'output.entity': '_notification'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('61', 'search'),
      arguments={
        'domain': orm.SuperKeyProperty(kind='6', required=True),
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'name': {'operators': ['==', '!='], 'type': orm.SuperStringProperty()},
            'action': {'operators': ['==', '!='], 'type': orm.SuperVirtualKeyProperty(kind='56')},
            'active': {'operators': ['==', '!='], 'type': orm.SuperBooleanProperty()}
            },
          indexes=[
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']]]},
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
        'cursor': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Search(cfg={'page': settings.SEARCH_PAGE}),
            RulePrepare(cfg={'path': '_entities'}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('61', 'initiate'),
      arguments={
        'caller_entity': orm.SuperKeyProperty(required=True),
        'caller_user': orm.SuperKeyProperty(required=True, kind='0'),
        'caller_action': orm.SuperVirtualKeyProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Set(cfg={'d': {'_caller_entity': 'input.caller_entity.entity'}}),
            Read(cfg={'namespace': '_caller_entity.key_namespace'}),
            RulePrepare(),
            RuleExec(),
            NotificationInitiate(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('61', 'send_mail'),
      arguments={
        'recipient': orm.SuperStringProperty(repeated=True),
        'subject': orm.SuperTextProperty(required=True),
        'body': orm.SuperTextProperty(required=True),
        'caller_entity': orm.SuperKeyProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Set(cfg={'d': {'_caller_entity': 'input.caller_entity.entity'}}),
            Read(cfg={'namespace': '_caller_entity.key_namespace'}),
            RulePrepare(),
            RuleExec(),
            NotificationMailSend(cfg={'sender': settings.NOTIFY_EMAIL})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('61', 'send_http'),
      arguments={
        'recipient': orm.SuperStringProperty(required=True),
        'subject': orm.SuperTextProperty(required=True),
        'body': orm.SuperTextProperty(required=True),
        'caller_entity': orm.SuperKeyProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Set(cfg={'d': {'_caller_entity': 'input.caller_entity.entity'}}),
            Read(cfg={'namespace': '_caller_entity.key_namespace'}),
            RulePrepare(),
            RuleExec(),
            NotificationHttpSend()
            ]
          )
        ]
      )
    ]
