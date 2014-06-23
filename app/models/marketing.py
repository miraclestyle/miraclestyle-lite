# -*- coding: utf-8 -*-
'''
Created on May 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import datetime

from app import ndb, settings
from app.models.base import *
from app.plugins.base import *
from app.plugins import marketing


class CatalogPricetag(ndb.BaseModel):
  
  _kind = 34
  
  product_template = ndb.SuperKeyProperty('1', kind='38', required=True, indexed=False)
  position_top = ndb.SuperFloatProperty('2', required=True, indexed=False)
  position_left = ndb.SuperFloatProperty('3', required=True, indexed=False)
  value = ndb.SuperStringProperty('4', required=True, indexed=False)


class CatalogImage(Image):
  
  _kind = 36
  
  pricetags = ndb.SuperLocalStructuredProperty(CatalogPricetag, '8', repeated=True)


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
    '_records': SuperLocalStructuredRecordProperty('35', repeated=True)
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
                              Action.build_key('35', 'process_cover'),
                              Action.build_key('35', 'process_duplicate'),
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
                              Action.build_key('35', 'process_cover'),
                              Action.build_key('35', 'process_duplicate'),
                              Action.build_key('35', 'index'),
                              Action.build_key('35', 'unindex'),
                              Action.build_key('35', 'cron')], True, 'context.user._is_taskqueue'),
      FieldPermission('35', ['created', 'updated', 'state', 'cover'], False, None, 'True'),
      FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_records'], False, False,
                      'context.entity.namespace_entity.state != "active"'),
      FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_records'], False, None,
                      'context.entity.state != "unpublished"'),
      FieldPermission('35', ['state'], True, None,
                      '(context.action.key_id_str == "create" and context.value and context.value.state == "unpublished") or (context.action.key_id_str == "lock" and context.value and context.value.state == "locked") or (context.action.key_id_str == "publish" and context.value and context.value.state == "published") or (context.action.key_id_str == "discontinue" and context.value and context.value.state == "discontinued") or (context.action.key_id_str == "sudo" and context.value and (context.value.state == "published" or context.value.state == "discontinued"))'),
      FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', '_images'], None, True,
                      'context.entity.state == "published" or context.entity.state == "discontinued"'),
      FieldPermission('35', ['_records.note'], True, True,
                      'context.user._root_admin'),
      FieldPermission('35', ['_records.note'], False, False,
                      'not context.user._root_admin'),
      FieldPermission('35', ['created', 'updated', 'name', 'publish_date', 'discontinue_date', 'state', 'cover', 'cost', '_images', '_records'], None, True,
                      'context.user._is_taskqueue or context.user._root_admin'),
      FieldPermission('35', ['_images'], True, None,
                      'context.action.key_id_str == "process_images" and (context.user._is_taskqueue or context.user._root_admin)'),
      FieldPermission('35', ['cover'], True, None,
                      'context.action.key_id_str == "process_cover" and (context.user._is_taskqueue or context.user._root_admin)')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('35', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'upload_url': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(),
            RuleExec(),
            BlobURL(cfg={'bucket': settings.CATALOG_IMAGE_BUCKET}),
            Set(cfg={'d': {'output.entity': 'entities.35',
                           'output.upload_url': 'blob_url'}})
            ]
          )
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
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            Set(cfg={'s': {'entities.35.state': 'unpublished'},
                     'd': {'entities.35.name': 'input.name',
                           'entities.35.publish_date': 'input.publish_date',
                           'entities.35.discontinue_date': 'input.discontinue_date'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RecordWrite(cfg={'paths': ['entities.35']}),
            Set(cfg={'d': {'output.entity': 'entities.35'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'search_cursor': ndb.SuperIntegerProperty(default=0)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            marketing.Read(catalog_page=settings.CATALOG_PAGE),
            Set(cfg={'d': {'output.entity': 'entities.35',
                           'output.search_cursor': 'search_cursor',
                           'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'sort_images': ndb.SuperStringProperty(repeated=True),
        'pricetags': ndb.SuperLocalStructuredProperty(CatalogImage, repeated=True),  # must be like this because we need to match the pricetags with order.....
        'publish_date': ndb.SuperDateTimeProperty(required=True),
        'discontinue_date': ndb.SuperDateTimeProperty(required=True),
        'search_cursor': ndb.SuperIntegerProperty(default=0)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            marketing.Read(read_from_start=True, catalog_page=settings.CATALOG_PAGE),
            marketing.UpdateSet()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            marketing.UpdateWrite(),
            Write(),
            RecordWrite(cfg={'paths': ['entities.35']}),
            Set(cfg={'d': {'output.entity': 'entities.35',
                           'output.search_cursor': 'search_cursor',
                           'output.search_more': 'search_more'}}),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'process_cover', 'action_model': '35'},
                               {'key': 'entities.35.key_urlsafe'})])
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'upload_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        '_images': ndb.SuperLocalStructuredImageProperty(CatalogImage, repeated=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            marketing.UploadImagesSet()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            marketing.UploadImagesWrite(),
            RecordWrite(),
            Set(cfg={'d': {'output.entity': 'entities.35'}}),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'process_images', 'action_model': '35'},
                               {'catalog_image_keys': 'tmp.catalog_image_keys',
                                'key': 'entities.35.key_urlsafe'})])
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'process_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'catalog_image_keys': ndb.SuperKeyProperty(kind='36', repeated=True)
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
            marketing.ProcessImages(),
            RecordWrite(),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'process_cover', 'action_model': '35'},
                               {'key': 'entities.35.key_urlsafe'})])
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'process_cover'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            marketing.Read(read_from_start=True, catalog_page=settings.CATALOG_PAGE),
            marketing.ProcessCoverSet()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Set(cfg={'d': {'tmp.original_cover': 'entities.35.cover'}}),
            Set(cfg={'d': {'tmp.new_cover': 'entities.35.cover'}}),
            marketing.ProcessCoverTransform(),
            BlobAlterImage(cfg={'read': 'blob_transform',
                                'write': 'entities.35.cover',
                                'config': {'copy': True, 'sufix': 'cover', 'transform': True,
                                           'width': 240, 'height': 360, 'crop_to_fit': True,
                                           'crop_offset_x': 0.0, 'crop_offset_y': 0.0}}),
            Write(),
            RecordWrite(cfg={'paths': ['entities.35']}),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      # marketing.Delete() plugin deems this action to allways execute in taskqueue!
      key=Action.build_key('35', 'delete'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
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
            marketing.Delete(),
            Delete(),
            RecordWrite(cfg={'paths': ['entities.35']}),
            Set(cfg={'d': {'output.entity': 'entities.35'}}),
            BlobUpdate(),
            CallbackNotify(),
            CallbackExec()
            ]
          )
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
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(),
            RuleExec(),
            Search(cfg={'page': settings.SEARCH_PAGE}),
            RulePrepare(cfg={'to': 'entities'}),
            Set(cfg={'d': {'output.entities': 'entities',
                           'output.search_cursor': 'search_cursor',
                           'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            RecordRead(cfg={'page': settings.RECORDS_PAGE}),
            Set(cfg={'d': {'output.entity': 'entities.35',
                           'output.search_cursor': 'search_cursor',
                           'output.search_more': 'search_more'}})
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'lock'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'message': ndb.SuperTextProperty(required=True)
        #'note': ndb.SuperTextProperty()  # @todo Decide on this!
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'entities.35.state': 'locked'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RulePrepare(),  # @todo Should run out of transaction!!!
            RecordWrite(cfg={'paths': ['entities.35'], 'd': {'message': 'input.message'}}),
            Set(cfg={'d': {'output.entity': 'entities.35'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'publish'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'message': ndb.SuperTextProperty(required=True)
        #'note': ndb.SuperTextProperty()  # @todo Decide on this!
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'entities.35.state': 'published'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RulePrepare(),  # @todo Should run out of transaction!!!
            RecordWrite(cfg={'paths': ['entities.35'], 'd': {'message': 'input.message'}}),
            Set(cfg={'d': {'output.entity': 'entities.35'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'index', 'action_model': '35'},
                               {'key': 'entities.35.key_urlsafe'})])
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'discontinue'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'message': ndb.SuperTextProperty(required=True)
        #'note': ndb.SuperTextProperty()  # @todo Decide on this!
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'s': {'entities.35.state': 'discontinued'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RulePrepare(),  # @todo Should run out of transaction!!!
            RecordWrite(cfg={'paths': ['entities.35'], 'd': {'message': 'input.message'}}),
            Set(cfg={'d': {'output.entity': 'entities.35'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'unindex', 'action_model': '35'},
                               {'key': 'entities.35.key_urlsafe'})])
            ]
          )
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
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            Set(cfg={'d': {'entities.35.state': 'input.state'}}),
            RulePrepare(),
            RuleExec()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            Write(),
            RulePrepare(),  # @todo Should run out of transaction!!!
            RecordWrite(cfg={'paths': ['entities.35'],
                             'd': {'message': 'input.message',
                                   'note': 'input.note'}}),  # 'index_state': 'input.index_state',  # @todo We embed this field on the fly, to indicate what administrator has chosen!
            Set(cfg={'d': {'output.entity': 'entities.35'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_model': '35'},
                               {'action_id': 'input.index_state', 'key': 'entities.35.key_urlsafe'})])  # @todo What happens if input.index_state is not supplied (e.g. None)?
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'log_message'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty()
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
            Write(),
            RecordWrite(cfg={'paths': ['entities.35'],
                             'd': {'message': 'input.message', 'note': 'input.note'}}),
            Set(cfg={'d': {'output.entity': 'entities.35'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      # marketing.SearchWrite() plugin deems this action to allways execute in taskqueue!
      key=Action.build_key('35', 'index'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            marketing.SearchWrite(index_name=settings.CATALOG_INDEX,
                                  documents_per_index=settings.CATALOG_DOCUMENTS_PER_INDEX)
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RecordWrite(cfg={'paths': ['entities.35'],
                             's': {'log_entity': False},  # @todo Perhaps entity should be logged in order to refresh updated field?
                             'd': {'message': 'tmp.message'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      # marketing.SearchDelete() plugin deems this action to allways execute in taskqueue!
      key=Action.build_key('35', 'unindex'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            marketing.SearchDelete(index_name=settings.CATALOG_INDEX,
                                   documents_per_index=settings.CATALOG_DOCUMENTS_PER_INDEX)
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            RecordWrite(cfg={'paths': ['entities.35'],
                             's': {'log_entity': False},  # @todo Perhaps entity should be logged in order to refresh updated field?
                             'd': {'message': 'tmp.message'}}),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'cron'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)  # @todo This is unlikely to be a definitive solution (how are we gonna run cron per domain?)!
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Prepare(),
            RulePrepare(),
            RuleExec(),
            marketing.CronPublish(page_size=10),
            marketing.CronDiscontinue(page_size=10),
            marketing.CronDelete(page_size=10,
                                 catalog_unpublished_life=settings.CATALOG_UNPUBLISHED_LIFE,
                                 catalog_discontinued_life=settings.CATALOG_DISCONTINUED_LIFE),
            CallbackExec()
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'duplicate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            Set(cfg={'d': {'output.entity': 'entities.35'}}),
            CallbackNotify(),
            CallbackExec(cfg=[('callback',
                               {'action_id': 'process_duplicate', 'action_model': '35'},
                               {'key': 'entities.35.key_urlsafe'})])
            ]
          )
        ]
      ),
    Action(
      key=Action.build_key('35', 'process_duplicate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugin_groups=[
        PluginGroup(
          plugins=[
            Context(),
            Read(),
            RulePrepare(),
            RuleExec(),
            marketing.DuplicateRead()
            ]
          ),
        PluginGroup(
          transactional=True,
          plugins=[
            marketing.DuplicateWrite(),
            RecordWrite(),
            CallbackNotify(),
            CallbackExec()
            ]
          )
        ]
      )
    ]
  
  # @todo Since Catalog.delete is called via callback this validator isn't required as long as CronDelete plugin respects these rules!
  @property
  def _has_expired(self):
    if not self.created or not self.updated:
      return False
    if self.state == 'unpublished':
      return self.created < (datetime.datetime.now() - datetime.timedelta(days=settings.CATALOG_UNPUBLISHED_LIFE))
    elif self.state == 'discontinued':
      return self.updated < (datetime.datetime.now() - datetime.timedelta(days=settings.CATALOG_DISCONTINUED_LIFE))
    elif self.state == 'locked' and self.namespace_entity.state != 'active':
      return True
    else:
      return False
  
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
            'created': {'operators': ['asc', 'desc'],
                        'default_value': {'asc': datetime.datetime.now(), 'desc': datetime.datetime(1990, 1, 1)}},
            'update': {'operators': ['asc', 'desc'],
                       'default_value': {'asc': datetime.datetime.now(), 'desc': datetime.datetime(1990, 1, 1)}}
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
            Search(cfg={'index': settings.CATALOG_INDEX, 'page': settings.SEARCH_PAGE, 'document': True}),
            DocumentDictConverter(),
            #DocumentEntityConverter(),
            #RulePrepare(cfg={'path': 'entities'}),
            Set(cfg={'d': {'output.entities': 'entities',
                           'output.search_documents_total_matches': 'search_documents_total_matches',
                           'output.search_documents_count': 'search_documents_count',
                           'output.search_cursor': 'search_cursor',
                           'output.search_more': 'search_more'}})
            ]
          )
        ]
      )
    ]
