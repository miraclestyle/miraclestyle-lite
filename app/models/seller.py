# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import os

from app import orm, mem, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins.auth import *


class Seller(orm.BaseExpando):
  
  _kind = 6
  
  _use_memcache = True
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = orm.SuperStringProperty('3', required=True)
  primary_contact = orm.SuperKeyProperty('4', kind='8', indexed=False)  # This field is required, and is handeled in update action via argument!
  state = orm.SuperStringProperty('5', required=True, choices=['active', 'suspended', 'su_suspended'])
  logo = SuperImageLocalStructuredProperty(Image, '6', required=True)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_primary_contact_email': orm.SuperReferenceProperty(target_field='primary_contact',
                                                         format_callback=lambda self, value: value._primary_email),
    '_records': orm.SuperRecordProperty('6')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('6', [orm.Action.build_key('6', 'prepare'),
                                 orm.Action.build_key('6', 'create')], True, 'not user._is_guest'),
      orm.ActionPermission('6', orm.Action.build_key('6', 'update'), False,
                           'entity._original.state != "active"'),
      orm.ActionPermission('6', orm.Action.build_key('6', 'suspend'), False,
                           'entity._original.state != "active"'),
      orm.ActionPermission('6', orm.Action.build_key('6', 'activate'), False,
                           'entity._original.state == "active" or entity._original.state == "su_suspended"'),
      orm.FieldPermission('6', ['created', 'updated', 'state'], False, None, 'True'),
      orm.FieldPermission('6', ['name', 'primary_contact', 'logo', '_records', '_primary_contact_email'], False, None,
                          'entity._original.state != "active"'),
      orm.FieldPermission('6', ['state'], True, None,
                          '(action.key_id_str == "activate" and entity.state == "active") or (action.key_id_str == "suspend" and entity.state == "suspended")'),
      # Domain is unit of administration, hence root admins need control over it!
      # Root admins can always: read domain; search for domains (exclusively);
      # read domain history; perform sudo operations (exclusively); log messages; read _records.note field (exclusively).
      orm.ActionPermission('6', [orm.Action.build_key('6', 'read'),
                                 orm.Action.build_key('6', 'search'),
                                 orm.Action.build_key('6', 'sudo'),
                                 orm.Action.build_key('6', 'log_message')], True, 'user._root_admin'),
      orm.ActionPermission('6', [orm.Action.build_key('6', 'search'),
                                 orm.Action.build_key('6', 'sudo')], False, 'not user._root_admin'),
      orm.FieldPermission('6', ['created', 'updated', 'name', 'primary_contact', 'state', 'logo', '_records',
                                '_primary_contact_email'], None, True, 'user._root_admin'),
      orm.FieldPermission('6', ['_records.note'], True, True,
                          'user._root_admin'),
      orm.FieldPermission('6', ['_records.note'], False, False,
                          'not user._root_admin'),
      orm.FieldPermission('6', ['state'], True, None,
                          '(action.key_id_str == "sudo") and user._root_admin and (entity.state == "active" or entity.state == "su_suspended")'),
      orm.FieldPermission('6', ['created', 'updated', 'name', 'state', 'logo'], None, True, 'entity._original.state == "active"')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('6', 'prepare'),
      arguments={
        'upload_url': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            BlobURL(cfg={'bucket': settings.BUCKET_PATH}),
            Set(cfg={'d': {'output.entity': '_domain',
                           'output.upload_url': '_blob_url'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'create'),
      arguments={
        'name': orm.SuperStringProperty(required=True),
        'logo': SuperImageLocalStructuredProperty(Image, required=True,
                                                  process_config={'measure': False, 'transform': True,
                                                                  'width': 240, 'height': 100,
                                                                  'crop_to_fit': True})
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            DomainCreateWrite(),
            Set(cfg={'d': {'output.entity': '_domain'}}),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'install', 'action_model': '57'},
                               {'key': '_config.key_urlsafe'})])
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_domain'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'name': orm.SuperStringProperty(required=True),
        'primary_contact': orm.SuperKeyProperty(required=True, kind='8', validator=primary_contact_validator),
        'logo': SuperImageLocalStructuredProperty(Image, process_config={'measure': False, 'transform': True,
                                                                         'width': 240, 'height': 100,
                                                                         'crop_to_fit': True}),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_domain.name': 'input.name',
                           '_domain.primary_contact': 'input.primary_contact',
                           '_domain.logo': 'input.logo'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            Set(cfg={'d': {'output.entity': '_domain'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'search'),
      arguments={
        'search': orm.SuperSearchProperty(
          default={'filters': [], 'orders': [{'field': 'created', 'operator': 'desc'}]},
          cfg={
            'search_arguments': {'kind': '6', 'options': {'limit': settings.SEARCH_PAGE}},
            'filters': {'name': orm.SuperStringProperty(),
                        'state': orm.SuperStringProperty()},
            'indexes': [{'orders': [('name', ['asc', 'desc'])]},
                        {'orders': [('created', ['asc', 'desc'])]},
                        {'orders': [('updated', ['asc', 'desc'])]},
                        {'filters': [('name', ['==', '!='])],
                         'orders': [('created', ['asc', 'desc'])]},
                        {'filters': [('state', ['==', '!='])],
                         'orders': [('created', ['asc', 'desc'])]}]
            }
          )
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec(),
            Search(),
            RulePrepare(cfg={'path': '_entities', 'skip_user_roles': True}),
            Set(cfg={'d': {'output.entities': '_entities',
                           'output.cursor': '_cursor',
                           'output.more': '_more'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'suspend'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'message': orm.SuperTextProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_domain.state': 'suspended'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_domain'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'activate'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'message': orm.SuperTextProperty(required=True)
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'_domain.state': 'active'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          ),
        orm.PluginGroup(
          plugins=[
            RulePrepare(),
            Set(cfg={'d': {'output.entity': '_domain'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'sudo'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'state': orm.SuperStringProperty(required=True, choices=['active', 'suspended', 'su_suspended']),
        'message': orm.SuperTextProperty(required=True),
        'note': orm.SuperTextProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'_domain.state': 'input.state'}}),
            RulePrepare(cfg={'skip_user_roles': True}),
            RuleExec()
            ]
          ),
        orm.PluginGroup(
          transactional=True,
          plugins=[
            Write(cfg={'dra': {'message': 'input.message', 'note': 'input.note'}}),
            RulePrepare(cfg={'skip_user_roles': True}),
            Set(cfg={'d': {'output.entity': '_domain'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('6', 'log_message'),
      arguments={
        'key': orm.SuperKeyProperty(kind='6', required=True),
        'message': orm.SuperTextProperty(required=True),
        'note': orm.SuperTextProperty()
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
            Write(cfg={'dra': {'message': 'input.message', 'note': 'input.note'}}),
            Set(cfg={'d': {'output.entity': '_domain'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      )
    ]
  
  @property
  def key_namespace(self):
    return self.key.urlsafe()
  
  @property
  def namespace_entity(self):
    return self
