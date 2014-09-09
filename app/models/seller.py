# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import hashlib
import os

from app import orm, mem, settings
from app.models import *
from app.plugins import *


class SellerContentDocument(orm.BaseModel):  # @todo This is taken from catalog product, so it is a duplicate! Shall we optimize for DRY?
  
  _kind = 20
  
  _use_rule_engine = False
  
  title = orm.SuperStringProperty('1', required=True, indexed=False)
  body = orm.SuperTextProperty('2', required=True)


class SellerContent(orm.BaseModel):
  
  _kind = 21
  
  _use_rule_engine = False
  
  documents = orm.SuperLocalStructuredProperty(SellerContentDocument, '1', repeated=True)  # @todo Or we could call it pages?
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    seller_key = input.get('seller')
    return cls.build_key(seller_key._id_str, parent=seller_key)


class SellerPluginGroup(orm.PluginGroup):  # @todo This need discussion!
  
  _kind = 22
  
  _use_rule_engine = False
  
  subscriptions = orm.SuperKeyProperty('2', kind='1', repeated=True)
  plugins = orm.SuperPluginStorageProperty(('0',), '6', required=True, default=[], compressed=False)  # First arg is list of plugin kind ids that user can create, e.g. ('1', '2', '3').


class Seller(orm.BaseExpando):
  
  _kind = 23
  
  _use_memcache = True
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = orm.SuperStringProperty('3', required=True)
  logo = SuperImageLocalStructuredProperty(Image, '4', required=True)
  
  _default_indexed = False
  
  _expando_fields = {
    'address': orm.SuperLocalStructuredProperty(Address, '5', repeated=True)  # @todo Not sure if this should be required?
    }
  
  _virtual_fields = {
    '_content': SuperRemoteStructuredProperty(SellerContent),
    '_plugin_group': SuperRemoteStructuredProperty(),
    '_records': orm.SuperRecordProperty('23')
    }
  
  _global_role = GlobalRole(
    permissions=[
      orm.ActionPermission('22', [orm.Action.build_key('22', 'prepare'),
                                  orm.Action.build_key('22', 'create')], True, 'not account._is_guest'),
      orm.ActionPermission('22', orm.Action.build_key('22', 'update'), True,
                           'entity._original.key_parent == account.key and not account._is_guest'),
      
      
      orm.FieldPermission('22', ['created', 'updated'], False, True, 'True'),
      
      orm.FieldPermission('22', ['name', 'logo', 'address', '_content', '_records'], False, None,
                          'entity._original.state != "active"'),
      orm.FieldPermission('22', ['state'], True, None,
                          '(action.key_id_str == "activate" and entity.state == "active") or (action.key_id_str == "suspend" and entity.state == "suspended")'),
      # Domain is unit of administration, hence root admins need control over it!
      # Root admins can always: read domain; search for domains (exclusively);
      # read domain history; perform sudo operations (exclusively); log messages; read _records.note field (exclusively).
      orm.ActionPermission('22', [orm.Action.build_key('22', 'read'),
                                 orm.Action.build_key('22', 'search'),
                                 orm.Action.build_key('22', 'sudo'),
                                 orm.Action.build_key('22', 'log_message')], True, 'user._root_admin'),
      orm.ActionPermission('22', [orm.Action.build_key('22', 'search'),
                                 orm.Action.build_key('22', 'sudo')], False, 'not user._root_admin'),
      orm.FieldPermission('22', ['created', 'updated', 'name', 'primary_contact', 'state', 'logo', '_records',
                                '_primary_contact_email'], None, True, 'user._root_admin'),
      orm.FieldPermission('22', ['_records.note'], True, True,
                          'user._root_admin'),
      orm.FieldPermission('22', ['_records.note'], False, False,
                          'not user._root_admin'),
      orm.FieldPermission('22', ['state'], True, None,
                          '(action.key_id_str == "sudo") and user._root_admin and (entity.state == "active" or entity.state == "su_suspended")'),
      orm.FieldPermission('22', ['created', 'updated', 'name', 'state', 'logo'], None, True, 'entity._original.state == "active"')
      ]
    )
  
  _actions = [
    orm.Action(
      key=orm.Action.build_key('23', 'prepare'),
      arguments={
        'upload_url': orm.SuperStringProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            BlobURL(cfg={'bucket': settings.BUCKET_PATH}),
            Set(cfg={'d': {'output.entity': '_seller',
                           'output.upload_url': '_blob_url'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('23', 'create'),
      arguments={
        'name': orm.SuperStringProperty(required=True),
        'logo': SuperImageLocalStructuredProperty(Image, required=True,
                                                  process_config={'measure': False, 'transform': True,
                                                                  'width': 240, 'height': 100,
                                                                  'crop_to_fit': True}),
        'address': orm.SuperLocalStructuredProperty(Address)
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
            DomainCreateWrite(),
            Set(cfg={'d': {'output.entity': '_seller'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('23', 'read'),
      arguments={
        'key': orm.SuperKeyProperty(kind='23', required=True),
        'read_arguments': orm.SuperJsonProperty()
        },
      _plugin_groups=[
        orm.PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': '_seller'}})
            ]
          )
        ]
      ),
    orm.Action(
      key=orm.Action.build_key('23', 'update'),
      arguments={
        'key': orm.SuperKeyProperty(kind='23', required=True),
        'name': orm.SuperStringProperty(required=True),
        'logo': SuperImageLocalStructuredProperty(Image, process_config={'measure': False, 'transform': True,
                                                                         'width': 240, 'height': 100,
                                                                         'crop_to_fit': True}),
        'address': orm.SuperLocalStructuredProperty(Address),
        '_content': orm.SuperLocalStructuredProperty(SellerContent),
        '_plugin_group': orm.SuperLocalStructuredProperty(),
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
            Set(cfg={'d': {'output.entity': '_domain'}})
            ]
          )
        ]
      )
    ]
  
  @classmethod
  def prepare_key(cls, input, **kwargs):
    account_key = input.get('account')
    return cls.build_key(account_key._id_str, parent=account_key)
