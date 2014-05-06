# -*- coding: utf-8 -*-
'''
Created on Jan 21, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import math

from jinja2.sandbox import SandboxedEnvironment

from app import ndb, settings
from app.lib.safe_eval import safe_eval
from app.srv.event import Action
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.srv import auth as ndb_auth
from app.srv import log as ndb_log
from app.plugins import common, rule, log, callback, notify


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
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('61', Action.build_key('61', 'prepare').urlsafe(), False,
                       "context.entities['61'].namespace_entity.state != 'active'"),
      ActionPermission('61', Action.build_key('61', 'search').urlsafe(), False,
                       "context.entities['61'].namespace_entity.state != 'active'"),
      ActionPermission('61', Action.build_key('61', 'initiate').urlsafe(), False,
                       "context.entities['61'].namespace_entity.state != 'active'"),
      ActionPermission('61', Action.build_key('61', 'initiate').urlsafe(), True,
                       "context.entities['61'].namespace_entity.state == 'active' and context.user._is_taskqueue"),
      FieldPermission('61', ['name', 'action', 'condition', 'active'], False, False,
                      "context.entities['61'].namespace_entity.state != 'active'")
      # @todo Field permissions should be reviewed!
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('61', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'output.entity': 'entities.61'})
        ]
      ),
    Action(
      key=Action.build_key('61', 'search'),
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
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('61', 'initiate'),
      arguments={
        'caller_entity': ndb.SuperKeyProperty(required=True),
        'caller_user': ndb.SuperKeyProperty(required=True, kind='0'),
        'caller_action' : ndb.SuperVirtualKeyProperty(required=True)
        },
      _plugins=[
        common.Context(),
        notify.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        notify.Initiate(),
        callback.Exec(dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      )
    ]


class CustomNotify(Template):
  
  _kind = 59
  
  message_sender = ndb.SuperStringProperty('5', required=True)
  message_recievers = ndb.SuperPickleProperty('6')
  message_subject = ndb.SuperStringProperty('7', required=True)
  message_body = ndb.SuperTextProperty('8', required=True)
  outlet = ndb.SuperStringProperty('9', required=True, default='58')
  
  def run(self, context):
    template_values = {'entity' : context.entities['caller_entity']}
    data = {'action_key': 'send',
            'action_model': self.outlet,
            'recipient': self.message_recievers(context.entities['caller_entity'], context.entities['caller_user']),
            'sender': self.message_sender,
            'body': render_template(self.message_body, template_values),
            'subject': render_template(self.message_subject, template_values),
            'caller_entity': context.entities['caller_entity'].key.urlsafe()}
    context.callback_payloads.append(('send', data))


class MailNotify(Template):
  
  _kind = 58
  
  message_sender = ndb.SuperKeyProperty('6', kind='8', required=True)
  message_reciever = ndb.SuperKeyProperty('7', kind='60', required=True)  # All users that have this role.
  message_subject = ndb.SuperStringProperty('8', required=True)
  message_body = ndb.SuperTextProperty('9', required=True)
  
  _virtual_fields = {
    '_records': ndb_log.SuperLocalStructuredRecordProperty('58', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('58', Action.build_key('58', 'prepare').urlsafe(), False,
                       "context.entities['58'].namespace_entity.state != 'active'"),
      ActionPermission('58', Action.build_key('58', 'create').urlsafe(), False,
                       "context.entities['58'].namespace_entity.state != 'active'"),
      ActionPermission('58', Action.build_key('58', 'read').urlsafe(), False,
                       "context.entities['58'].namespace_entity.state != 'active'"),
      ActionPermission('58', Action.build_key('58', 'update').urlsafe(), False,
                       "context.entities['58'].namespace_entity.state != 'active'"),
      ActionPermission('58', Action.build_key('58', 'delete').urlsafe(), False,
                       "context.entities['58'].namespace_entity.state != 'active'"),
      ActionPermission('58', Action.build_key('58', 'read_records').urlsafe(), False,
                       "context.entities['58'].namespace_entity.state != 'active'"),
      ActionPermission('58', Action.build_key('58', 'send').urlsafe(), False,
                       "context.entities['58'].namespace_entity.state != 'active'"),
      ActionPermission('58', Action.build_key('58', 'send').urlsafe(), True,
                       "context.entities['58'].namespace_entity.state == 'active' and context.user._is_taskqueue"),
      FieldPermission('58', ['name', 'action', 'condition', 'active', 'message_sender',
                             'message_reciever', 'message_subject', 'message_body', '_records'], False, False,
                      "context.entities['58'].namespace_entity.state != 'active'")
      # @todo Field permissions should be reviewed!
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('58', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'output.entity': 'entities.58'})
        ]
      ),
    Action(
      key=Action.build_key('58', 'create'),
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
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'values.58.name': 'input.name',
                                   'values.58.action': 'input.action',
                                   'values.58.condition': 'input.condition',
                                   'values.58.active': 'input.active',
                                   'values.58.message_sender': 'input.message_sender',
                                   'values.58.message_subject': 'input.message_subject',
                                   'values.58.message_reciever': 'input.message_reciever',
                                   'values.58.message_body': 'input.message_body'}),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.58'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.58.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('58', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='61', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.58'})
        ]
      ),
    Action(
      key=Action.build_key('58', 'update'),
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
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'values.58.name': 'input.name',
                                   'values.58.action': 'input.action',
                                   'values.58.condition': 'input.condition',
                                   'values.58.active': 'input.active',
                                   'values.58.message_sender': 'input.message_sender',
                                   'values.58.message_subject': 'input.message_subject',
                                   'values.58.message_reciever': 'input.message_reciever',
                                   'values.58.message_body': 'input.message_body'}),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.58'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.58.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('58', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(required=True, kind='61')
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Delete(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.58'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.58.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('58', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='61', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.58', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('58', 'send'),
      arguments={
        'recipient': ndb.SuperStringProperty(repeated=True),  # @todo This field is mandatory in mail.send_mail() function, which this action eventually calls!
        'sender': ndb.SuperStringProperty(required=True),
        'subject': ndb.SuperTextProperty(required=True),
        'body': ndb.SuperTextProperty(required=True),
        'caller_entity': ndb.SuperKeyProperty(required=True)
        },
      _plugins=[
        common.Context(),
        notify.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        notify.MailSend()
        ]
      )
    ]
  
  def run(self, context):
    values = {'entity': context.entities['caller_entity'], 'user': context.entities['caller_user']}
    if safe_eval(self.condition, values):
      from app.srv.rule import DomainUser
      domain_users = DomainUser.query(DomainUser.roles == self.message_reciever,
                                           namespace=self.message_reciever.namespace()).fetch()
      recievers = ndb.get_multi([ndb_auth.User.build_key(long(reciever.key.id())) for reciever in domain_users])
      sender_key = ndb_auth.User.build_key(long(self.message_sender.id()))
      sender = sender_key.get()
      template_values = {'entity': context.entities['caller_entity']}
      data = {'action_key': 'send',
              'action_model': '58',
              'recipient': [reciever._primary_email for reciever in recievers],
              'sender': sender._primary_email,
              'body': render_template(self.message_body, template_values),
              'subject': render_template(self.message_subject, template_values),
              'caller_entity': context.entities['caller_entity'].key.urlsafe()}
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
    '_records': ndb_log.SuperLocalStructuredRecordProperty('63', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('63', Action.build_key('63', 'prepare').urlsafe(), False,
                       "context.entities['63'].namespace_entity.state != 'active'"),
      ActionPermission('63', Action.build_key('63', 'create').urlsafe(), False,
                       "context.entities['63'].namespace_entity.state != 'active'"),
      ActionPermission('63', Action.build_key('63', 'read').urlsafe(), False,
                       "context.entities['63'].namespace_entity.state != 'active'"),
      ActionPermission('63', Action.build_key('63', 'update').urlsafe(), False,
                       "context.entities['63'].namespace_entity.state != 'active'"),
      ActionPermission('63', Action.build_key('63', 'delete').urlsafe(), False,
                       "context.entities['63'].namespace_entity.state != 'active'"),
      ActionPermission('63', Action.build_key('63', 'read_records').urlsafe(), False,
                       "context.entities['63'].namespace_entity.state != 'active'"),
      ActionPermission('63', Action.build_key('63', 'send').urlsafe(), False,
                       "context.entities['63'].namespace_entity.state != 'active'"),
      ActionPermission('63', Action.build_key('63', 'send').urlsafe(), True,
                       "context.entities['63'].namespace_entity.state == 'active' and context.user._is_taskqueue"),
      FieldPermission('63', ['name', 'action', 'condition', 'active', 'message_sender',
                             'message_reciever', 'message_subject', 'message_body', '_records'], False, False,
                      "context.entities['63'].namespace_entity.state != 'active'")
      # @todo Field permissions should be reviewed!
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('63', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'output.entity': 'entities.63'})
        ]
      ),
    Action(
      key=Action.build_key('63', 'create'),
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
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'values.63.name': 'input.name',
                                   'values.63.action': 'input.action',
                                   'values.63.condition': 'input.condition',
                                   'values.63.active': 'input.active',
                                   'values.63.message_sender': 'input.message_sender',
                                   'values.63.message_subject': 'input.message_subject',
                                   'values.63.message_reciever': 'input.message_reciever',
                                   'values.63.message_body': 'input.message_body'}),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.63'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.63.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('63', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='61', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.63'})
        ]
      ),
    Action(
      key=Action.build_key('63', 'update'),
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
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values={'values.63.name': 'input.name',
                                   'values.63.action': 'input.action',
                                   'values.63.condition': 'input.condition',
                                   'values.63.active': 'input.active',
                                   'values.63.message_sender': 'input.message_sender',
                                   'values.63.message_subject': 'input.message_subject',
                                   'values.63.message_reciever': 'input.message_reciever',
                                   'values.63.message_body': 'input.message_body'}),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.63'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.63.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('63', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(required=True, kind='61')
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Delete(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.63'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_key': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.63.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('63', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='61', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.63', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('63', 'send'),
      arguments={
        'recipient': ndb.SuperStringProperty(required=True),
        'sender': ndb.SuperStringProperty(required=True),
        'subject': ndb.SuperTextProperty(required=True),
        'body': ndb.SuperTextProperty(required=True),
        'caller_entity': ndb.SuperKeyProperty(required=True)
        },
      _plugins=[
        common.Context(),
        notify.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        notify.HttpSend()
        ]
      )
    ]
  
  def run(self, context):
    values = {'entity': context.entities['caller_entity'], 'user': context.entities['caller_user']}
    if safe_eval(self.condition, values):
      sender_key = ndb_auth.User.build_key(long(self.message_sender.id()))
      sender = sender_key.get()
      template_values = {'entity': context.entities['caller_entity']}
      data = {'action_key': 'send',
              'action_model': '63',
              'recipient': self.message_reciever,
              'sender': sender._primary_email,
              'body': render_template(self.message_body, template_values),
              'subject': render_template(self.message_subject, template_values),
              'caller_entity': context.entities['caller_entity'].key.urlsafe()}
      context.callback_payloads.append(('send', data))
