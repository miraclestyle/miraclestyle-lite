# -*- coding: utf-8 -*-
'''
Created on May 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

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
    'cover': ndb.SuperKeyProperty('7', kind='36'),
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
                              Action.build_key('35', 'search'),
                              Action.build_key('35', 'read_records'),
                              Action.build_key('35', 'lock'),
                              Action.build_key('35', 'publish'),
                              Action.build_key('35', 'discontinue'),
                              Action.build_key('35', 'log_message'),
                              Action.build_key('35', 'duplicate'),
                              Action.build_key('35', 'upload_images')], False, 'context.entity.namespace_entity.state != "active"'),
      ActionPermission('35', Action.build_key('35', 'process_images'), True, 'context.user._is_taskqueue')
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
        common.Prepare(domain_model=True),
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
        common.Prepare(domain_model=True),
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
        marketing.UpdateRead(),
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
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=True),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(page_size=settings.SEARCH_PAGE),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'search_cursor', 'output.more': 'search_more'})
        ]
      ),
    Action(
      key=Action.build_key('35', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(page_size=settings.RECORDS_PAGE),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.35', 'output.next_cursor': 'log_read_cursor', 'output.more': 'log_read_more'})
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
      key=Action.build_key('35', 'duplicate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugins=[]
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
                         dynamic_data={'catalog_image_keys': 'tmp.catalog_image_keys', 'key': 'entities.35.key_urlsafe'}),
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
      )
    ]
