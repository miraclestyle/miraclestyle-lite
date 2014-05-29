# -*- coding: utf-8 -*-
'''
Created on May 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime

from app import ndb, settings
from app.srv.event import Action
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.srv import log as ndb_log
from app.srv import blob as ndb_blob
from app.plugins import common, rule, log, callback, blob, marketing


class CatalogPricetag(ndb.BaseModel):
  
  _kind = 34
  
  product_template = ndb.SuperKeyProperty('1', kind='38', required=True, indexed=False)
  position_top = ndb.SuperFloatProperty('2', required=True, indexed=False)
  position_left = ndb.SuperFloatProperty('3', required=True, indexed=False)
  value = ndb.SuperStringProperty('4', required=True, indexed=False)


class CatalogImage(ndb_blob.Image):
  
  _kind = 36
  
  pricetags = ndb.SuperLocalStructuredProperty(CatalogPricetag, '8', repeated=True)
  
  def get_output(self):
    dic = super(CatalogImage, self).get_output()
    dic['_image_240'] = self.get_serving_url(240)
    dic['_image_600'] = self.get_serving_url(600)
    return dic


class Catalog(ndb.BaseExpando):
  
  _kind = 35
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = ndb.SuperStringProperty('3', required=True)
  publish_date = ndb.SuperDateTimeProperty('4', required=True)
  discontinue_date = ndb.SuperDateTimeProperty('5', required=True)
  state = ndb.SuperStringProperty('6', required=True, default='unpublished', choices=['unpublished', 'locked', 'published', 'discontinued'])
  
  _default_indexed = False
  
  _expando_fields = {
    'cover': ndb.SuperLocalStructuredProperty(CatalogImage, '7'),
    'cost': ndb.SuperDecimalProperty('8')
    }
  
  _virtual_fields = {
    '_images': ndb.SuperLocalStructuredProperty(CatalogImage, repeated=True),
    '_records': ndb_log.SuperLocalStructuredRecordProperty('35', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('35', [Action.build_key('35', 'prepare'),
                              Action.build_key('35', 'create'),
                              Action.build_key('35', 'read'),
                              Action.build_key('35', 'update'),
                              Action.build_key('35', 'upload_images'),
                              Action.build_key('35', 'search'),
                              Action.build_key('35', 'read_records'),
                              Action.build_key('35', 'lock'),
                              Action.build_key('35', 'discontinue'),
                              Action.build_key('35', 'log_message'),
                              Action.build_key('35', 'duplicate')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('35', [Action.build_key('35', 'update'),
                              Action.build_key('35', 'lock'),
                              Action.build_key('35', 'upload_images')], False, 'context.entity.state != "unpublished"'),
      ActionPermission('35', [Action.build_key('35', 'process_images'),
                              Action.build_key('35', 'delete'),
                              Action.build_key('35', 'publish'),
                              Action.build_key('35', 'sudo'),
                              Action.build_key('35', 'index'),
                              Action.build_key('35', 'unindex'),
                              Action.build_key('35', 'cron')], False, 'True'),
      ActionPermission('35', [Action.build_key('35', 'discontinue'),
                              Action.build_key('35', 'duplicate')], False, 'context.entity.state != "published"'),
      ActionPermission('35', [Action.build_key('35', 'read')], True, 'context.entity.state == "published" or context.entity.state == "discontinued"'),
      ActionPermission('35', [Action.build_key('35', 'delete')], True, 'context.user._is_taskqueue and context.entity._has_expired'),
      ActionPermission('35', [Action.build_key('35', 'publish')], True, 'context.user._is_taskqueue and context.entity.state != "published" and context.entity._is_eligible'),
      ActionPermission('35', [Action.build_key('35', 'discontinue')], True, 'context.user._is_taskqueue and context.entity.state != "discontinued"'),
      ActionPermission('35', [Action.build_key('35', 'sudo')], True, 'context.user._root_admin'),
      ActionPermission('35', [Action.build_key('35', 'process_images'),
                              Action.build_key('35', 'index'),
                              Action.build_key('35', 'unindex'),
                              Action.build_key('35', 'cron')], True, 'context.user._is_taskqueue'),
      FieldPermission('35', ['created', 'updated', 'state'], False, None, 'True'),
      FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_records'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_records'], False, None,
                      'context.entity.state != "unpublished"'),
      FieldPermission('35', ['state'], True, None,
                      '(context.action.key_id_str == "create" and context.value and context.value.state == "unpublished") or (context.action.key_id_str == "lock" and context.value and context.value.state == "locked") or (context.action.key_id_str == "publish" and context.value and context.value.state == "published") or (context.action.key_id_str == "discontinue" and context.value and context.value.state == "discontinued") or (context.action.key_id_str == "sudo" and context.value and (context.value.state == "published" or context.value.state == "discontinued")'),
      FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', '_images'], None, True,
                      'context.entity.state == "published" or context.entity.state == "discontinued"'),
      FieldPermission('35', ['_records.note'], True, True,
                      'context.user._root_admin'),
      FieldPermission('35', ['_records.note'], False, False,
                      'not context.user._root_admin'),
      FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_records'], None, True,
                      'context.user._is_taskqueue or context.user._root_admin')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('35', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'upload_url': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        blob.URL(gs_bucket_name=settings.CATALOG_IMAGE_BUCKET),
        common.Set(dynamic_values={'output.entity': 'entities.35'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'create'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'publish_date': ndb.SuperDateTimeProperty(required=True),
        'discontinue_date': ndb.SuperDateTimeProperty(required=True)
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(static_values={'values.35.state': 'unpublished'},
                   dynamic_values={'values.35.name': 'input.name',
                                   'values.35.publish_date': 'input.publish_date',
                                   'values.35.discontinue_date': 'input.discontinue_date'}),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.35'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'images_cursor': ndb.SuperIntegerProperty(default=0)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        marketing.Read(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.35',
                                   'output.images_cursor': 'tmp.images_cursor',
                                   'output.images_more': 'tmp.images_more'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'name': ndb.SuperStringProperty(required=True),
        '_images': ndb.SuperLocalStructuredProperty(CatalogImage, repeated=True),
        'publish_date': ndb.SuperDateTimeProperty(required=True),
        'discontinue_date': ndb.SuperDateTimeProperty(required=True),
        'images_cursor': ndb.SuperIntegerProperty(default=0)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        marketing.Read(read_from_start=True),
        marketing.UpdateSet(),
        rule.Write(transactional=True),
        marketing.UpdateWrite(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.35',
                                                       'output.images_cursor': 'tmp.images_cursor',
                                                       'output.images_more': 'tmp.images_more'}),
        blob.Update(transactional=True),  # @todo Not sure if the workflow is ok. Take a look at marketing.py plugins!
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'upload_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        '_images': ndb.SuperLocalStructuredImageProperty(CatalogImage, repeated=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        marketing.UploadImagesSet(),
        rule.Write(transactional=True),
        marketing.UploadImagesWrite(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.35'}),
        blob.Update(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Payload(transactional=True, queue='callback',
                         static_data={'action_id': 'process_images', 'action_model': '35'},
                         dynamic_data={'catalog_image_keys': 'tmp.catalog_image_keys',
                                       'key': 'entities.35.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'process_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'catalog_image_keys': ndb.SuperKeyProperty(kind='36', repeated=True),
        'caller_user': ndb.SuperKeyProperty(kind='0', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        marketing.ProcessImages(transactional=True),
        log.Write(transactional=True),
        blob.Update(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      # marketing.Delete() plugin deems this action to allways execute in taskqueue!
      key=Action.build_key('35', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        marketing.Delete(transactional=True),
        common.Delete(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.35'}),
        blob.Update(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'created', 'operator': 'desc'}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()}
            },
          indexes=[
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['state'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['name', 'state'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']},
            'created': {'operators': ['asc', 'desc']},
            'update': {'operators': ['asc', 'desc']}
            }
          ),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(page_size=settings.SEARCH_PAGE),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities',
                                   'output.search_cursor': 'search_cursor',
                                   'output.search_more': 'search_more'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'log_read_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(page_size=settings.RECORDS_PAGE),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.35',
                                   'output.log_read_cursor': 'log_read_cursor',
                                   'output.log_read_more': 'log_read_more'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'lock'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'message': ndb.SuperTextProperty(required=True)
        #'note': ndb.SuperTextProperty()  # @todo Decide on this!
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(static_values={'values.35.state': 'locked'}),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        rule.Prepare(transactional=True, skip_user_roles=False, strict=False),
        log.Entity(transactional=True, dynamic_arguments={'message': 'input.message'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.35'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'publish'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'message': ndb.SuperTextProperty(required=True)
        #'note': ndb.SuperTextProperty()  # @todo Decide on this!
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(static_values={'values.35.state': 'published'}),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        rule.Prepare(transactional=True, skip_user_roles=True, strict=False),
        log.Entity(transactional=True, dynamic_arguments={'message': 'input.message'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.35'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Payload(transactional=True, queue='callback',
                         static_data={'action_id': 'index', 'action_model': '35'},
                         dynamic_data={'key': 'entities.35.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'discontinue'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'message': ndb.SuperTextProperty(required=True)
        #'note': ndb.SuperTextProperty()  # @todo Decide on this!
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(static_values={'values.35.state': 'discontinued'}),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        rule.Prepare(transactional=True, skip_user_roles=False, strict=False),
        log.Entity(transactional=True, dynamic_arguments={'message': 'input.message'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.35'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Payload(transactional=True, queue='callback',
                         static_data={'action_id': 'unindex', 'action_model': '35'},
                         dynamic_data={'key': 'entities.35.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'sudo'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'state': ndb.SuperStringProperty(required=True, choices=['published', 'discontinued']),
        'index_state': ndb.SuperStringProperty(choices=['index', 'unindex']),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        common.Set(dynamic_values={'values.35.state': 'input.state'}),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        rule.Prepare(transactional=True, skip_user_roles=True, strict=False),
        log.Entity(transactional=True,
                   dynamic_arguments={'index_state': 'input.index_state',  # @todo We embed this field on the fly, to indicate what administrator has chosen!
                                      'message': 'input.message',
                                      'note': 'input.note'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.35'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Payload(transactional=True, queue='callback',
                         static_data={'action_model': '35'},
                         dynamic_data={'action_id': 'input.index_state', 'key': 'entities.35.key_urlsafe'}),  # @todo What happens if input.index_state is not supplied (e.g. None)?
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'log_message'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Write(transactional=True),
        log.Entity(transactional=True, dynamic_arguments={'message': 'input.message', 'note': 'input.note'}),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.35'}),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      # marketing.SearchWrite() plugin deems this action to allways execute in taskqueue!
      key=Action.build_key('35', 'index'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        marketing.SearchWrite(index_name=settings.CATALOG_INDEX,
                              documents_per_index=settings.CATALOG_DOCUMENTS_PER_INDEX),
        log.Entity(transactional=True,
                   static_arguments={'log_entity': False},  # @todo Perhaps entity should be logged in order to refresh updated field?
                   dynamic_arguments={'message': 'tmp.message'}),
        log.Write(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      # marketing.SearchDelete() plugin deems this action to allways execute in taskqueue!
      key=Action.build_key('35', 'unindex'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        marketing.SearchDelete(index_name=settings.CATALOG_INDEX,
                               documents_per_index=settings.CATALOG_DOCUMENTS_PER_INDEX),
        log.Entity(transactional=True,
                   static_arguments={'log_entity': False},  # @todo Perhaps entity should be logged in order to refresh updated field?
                   dynamic_arguments={'message': 'tmp.message'}),
        log.Write(transactional=True),
        callback.Payload(transactional=True, queue='notify',
                         static_data={'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data={'caller_entity': 'entities.35.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'cron'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)  # @todo This is unlikely to be a definitive solution (how are we gonna run cron per domain?)!
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        marketing.CronPublish(page_size=10),
        marketing.CronDiscontinue(page_size=10),
        marketing.CronDelete(page_size=10, catalog_life=settings.CATALOG_LIFE),
        callback.Exec(dynamic_data={'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'duplicate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugins=[]
      )
    ]
  
  @property
  def _has_expired(self):
    if not self.updated:
      return False
    return self.updated < (datetime.datetime.now() - datetime.timedelta(days=settings.CATALOG_LIFE))
  
  @property
  def _is_eligible(self):
    # @todo Here we implement the logic to validate if catalog publisher has funds to support catalog publishing!
    return True


class CatalogIndex(ndb.BaseExpando):
  
  _kind = 82
  
  _default_indexed = False
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('82', [Action.build_key('82', 'search')], True, 'True')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('82', 'search'),
      arguments={
        'search': ndb.SuperSearchProperty(
          default={'filters': [{'field': 'kind', 'value': '35', 'operator': '=='}], 'order_by': {'field': 'created', 'operator': 'desc'}},
          filters={
            'query_string': {'operators': ['=='], 'type': ndb.SuperStringProperty()},
            'kind': {'operators': ['=='], 'type': ndb.SuperStringProperty()},
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'state': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()}
            },
          indexes=[
            {'filter': ['kind'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['state'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]},
            {'filter': ['name', 'state'],
             'order_by': [['name', ['asc', 'desc']],
                          ['created', ['asc', 'desc']],
                          ['updated', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']},
            'created': {'operators': ['asc', 'desc']},
            'update': {'operators': ['asc', 'desc']}
            }
          ),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        search.Search(index_name=settings.CATALOG_INDEX, page_size=settings.SEARCH_PAGE),
        #search.Entities(),
        #rule.Prepare(skip_user_roles=True, strict=False),
        #rule.Read(),
        common.Set(dynamic_values={'output.entities': 'search_documents',
                                   'output.search_documents_total_matches': 'search_documents_total_matches',
                                   'output.search_documents_count': 'search_documents_count',
                                   'output.search_cursor': 'search_cursor',
                                   'output.search_more': 'search_more'})
        ]
      )
    ]
