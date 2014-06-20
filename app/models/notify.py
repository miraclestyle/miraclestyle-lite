# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import math

from jinja2.sandbox import SandboxedEnvironment


from app import ndb, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins import notify


sandboxed_jinja = SandboxedEnvironment()

def render_template(template_as_string, values={}):
  from_string_template = sandboxed_jinja.from_string(template_as_string)
  return from_string_template.render(values)


class Template(ndb.BasePolyExpando):
  
  _kind = 81
  
  _default_indexed = False


class CustomTemplate(Template):
  
  _kind = 59
  
  message_recievers = ndb.SuperPickleProperty('1', required=True, indexed=False)
  message_subject = ndb.SuperStringProperty('2', required=True, indexed=False)
  message_body = ndb.SuperTextProperty('3', required=True)
  outlet = ndb.SuperStringProperty('4', required=True, default='send_mail', indexed=False)
  
  def run(self, context):
    template_values = {'entity': context.tmp['caller_entity']}
    data = {'action_id': self.outlet,
            'action_model': '61',
            'recipient': self.message_recievers(context.tmp['caller_entity'], context.tmp['caller_user']),
            'body': render_template(self.message_body, template_values),
            'subject': render_template(self.message_subject, template_values),
            'caller_entity': context.tmp['caller_entity'].key.urlsafe()}
    context.callbacks.append(('send', data))


class MailTemplate(Template):
  
  _kind = 58
  
  message_reciever = ndb.SuperKeyProperty('1', kind='60', required=True, indexed=False)  # All users that have this role.
  message_subject = ndb.SuperStringProperty('2', required=True, indexed=False)
  message_body = ndb.SuperTextProperty('3', required=True)
  
  def run(self, context):
    DomainUser = context.models['8']
    domain_users = DomainUser.query(DomainUser.roles == self.message_reciever,
                                    namespace=self.message_reciever.namespace()).fetch()
    recievers = ndb.get_multi([ndb.Key('0', long(reciever.key.id())) for reciever in domain_users])
    template_values = {'entity': context.tmp['caller_entity']}
    data = {'action_id': 'send_mail',
            'action_model': '61',
            'recipient': [reciever._primary_email for reciever in recievers],
            'body': render_template(self.message_body, template_values),
            'subject': render_template(self.message_subject, template_values),
            'caller_entity': context.tmp['caller_entity'].key.urlsafe()}
    recipients_per_task = int(math.ceil(len(data['recipient']) / settings.RECIPIENTS_PER_TASK))
    data_copy = data.copy()
    del data_copy['recipient']
    for i in range(0, recipients_per_task+1):
      recipients = data['recipient'][settings.RECIPIENTS_PER_TASK*i:settings.RECIPIENTS_PER_TASK*(i+1)]
      if recipients:
        new_data = data_copy.copy()
        new_data['recipient'] = recipients
        context.callbacks.append(('send', new_data))


class HttpTemplate(Template):
  
  _kind = 63
  
  message_reciever = ndb.SuperStringProperty('1', required=True, indexed=False)
  message_subject = ndb.SuperStringProperty('2', required=True, indexed=False)
  message_body = ndb.SuperTextProperty('3', required=True)
  
  def run(self, context):
    template_values = {'entity': context.tmp['caller_entity']}
    data = {'action_id': 'send_http',
            'action_model': '61',
            'recipient': self.message_reciever,
            'body': render_template(self.message_body, template_values),
            'subject': render_template(self.message_subject, template_values),
            'caller_entity': context.tmp['caller_entity'].key.urlsafe()}
    context.callbacks.append(('send', data))


class Notification(ndb.BaseExpando):
  
  _kind = 61
  
  name = ndb.SuperStringProperty('1', required=True)
  action = ndb.SuperKeyProperty('2', kind='56', required=True)
  condition = ndb.SuperStringProperty('3', required=True, indexed=False)
  active = ndb.SuperBooleanProperty('4', required=True, default=True)
  templates = ndb.SuperPickleProperty('5', required=True, indexed=False, compressed=False)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_records': SuperLocalStructuredRecordProperty('61', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('61', [Action.build_key('61', 'prepare'),
                              Action.build_key('61', 'create'),
                              Action.build_key('61', 'read'),
                              Action.build_key('61', 'update'),
                              Action.build_key('61', 'delete'),
                              Action.build_key('61', 'search'),
                              Action.build_key('61', 'read_records'),
                              Action.build_key('61', 'initiate'),
                              Action.build_key('61', 'send_mail'),
                              Action.build_key('61', 'send_http')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('61', [Action.build_key('61', 'initiate'),
                              Action.build_key('61', 'send_mail'),
                              Action.build_key('61', 'send_http')], False, 'True'),
      ActionPermission('61', [Action.build_key('61', 'initiate'),
                              Action.build_key('61', 'send_mail'),
                              Action.build_key('61', 'send_http')], True,
                       'context.entity.namespace_entity.state == "active" and context.user._is_taskqueue'),
      FieldPermission('61', ['name', 'action', 'condition', 'active', 'templates', '_records'], False, False,
                      'context.entity.namespace_entity.state != "active"')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('61', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(),
            RuleExec(),
            Set(config={'d': {'output.entity': 'entities.61'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('61', 'create'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'action': ndb.SuperVirtualKeyProperty(required=True, kind='56'),
        'condition': ndb.SuperTextProperty(required=True),
        'active': ndb.SuperBooleanProperty(),
        'templates': ndb.SuperJsonProperty(required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(),
            RuleExec(),
            notify.Set()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(config={'paths': ['entities.61']}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.61'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('61', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='61', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.61'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('61', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(required=True, kind='61'),
        'name': ndb.SuperStringProperty(required=True),
        'action': ndb.SuperVirtualKeyProperty(required=True, kind='56'),
        'condition': ndb.SuperTextProperty(required=True),
        'active': ndb.SuperBooleanProperty(),
        'templates': ndb.SuperJsonProperty(required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            notify.Set()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RuleWrite(),
            Write(),
            RecordWrite(config={'paths': ['entities.61']}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.61'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('61', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(required=True, kind='61')
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Delete(),
            RecordWrite(config={'paths': ['entities.61']}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.61'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('61', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'action': {'operators': ['==', '!='], 'type': ndb.SuperVirtualKeyProperty(kind='56')},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty()}
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
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(),
            RuleExec(),
            Search(config={'page': settings.SEARCH_PAGE}),
            RulePrepare(config={'to': 'entities'}),
            RuleRead(config={'path': 'entities'}),
            Set(config={'d': {'output.entities': 'entities',
                              'output.search_cursor': 'search_cursor',
                              'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('61', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='61', required=True),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            RecordRead(config={'page': settings.RECORDS_PAGE}),
            RuleRead(),
            Set(config={'d': {'output.entity': 'entities.61',
                              'output.search_cursor': 'search_cursor',
                              'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('61', 'initiate'),
      arguments={
        'caller_entity': ndb.SuperKeyProperty(required=True),
        'caller_user': ndb.SuperKeyProperty(required=True, kind='0'),
        'caller_action': ndb.SuperVirtualKeyProperty(required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Set(config={'d': {'tmp.caller_entity': 'input.caller_entity.entity'}}),
            Prepare(config=[{'model': 'models.61', 'parent': None,
                             'namespace': 'tmp.caller_entity.key_namespace',
                             'save': 'entities.61', 'copy': 'values.61'}]),
            RulePrepare(),
            RuleExec(),
            notify.Initiate(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('61', 'send_mail'),
      arguments={
        'recipient': ndb.SuperStringProperty(repeated=True),
        'subject': ndb.SuperTextProperty(required=True),
        'body': ndb.SuperTextProperty(required=True),
        'caller_entity': ndb.SuperKeyProperty(required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Set(config={'d': {'tmp.caller_entity': 'input.caller_entity.entity'}}),
            Prepare(config=[{'model': 'models.61', 'parent': None,
                             'namespace': 'tmp.caller_entity.key_namespace',
                             'save': 'entities.61', 'copy': 'values.61'}]),
            RulePrepare(),
            RuleExec(),
            notify.MailSend(message_sender=settings.NOTIFY_EMAIL)
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('61', 'send_http'),
      arguments={
        'recipient': ndb.SuperStringProperty(required=True),
        'subject': ndb.SuperTextProperty(required=True),
        'body': ndb.SuperTextProperty(required=True),
        'caller_entity': ndb.SuperKeyProperty(required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Set(config={'d': {'tmp.caller_entity': 'input.caller_entity.entity'}}),
            Prepare(config=[{'model': 'models.61', 'parent': None,
                             'namespace': 'tmp.caller_entity.key_namespace',
                             'save': 'entities.61', 'copy': 'values.61'}]),
            RulePrepare(),
            RuleExec(),
            notify.HttpSend()
            ]
          )
        ]
      )
    ]
