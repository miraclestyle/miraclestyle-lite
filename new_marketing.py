# -*- coding: utf-8 -*-
'''
Created on May 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from google.appengine.api import images

from app import ndb, settings, memcache, util
from app.srv.event import Action
from app.srv import blob
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.srv import log as ndb_log, blob
from app.plugins import common, rule, log, callback, marketing


# this is LocalStructuredProperty and is repeated per catalog image.
# properties to remain in this class are:
# product_template, position_top (former source_position_top), position_left (former source_position_left), value
class CatalogPricetag(ndb.BaseModel):
  
  _kind = 34
  
  product_template = ndb.SuperKeyProperty('1', kind='38', required=True, indexed=False)
  position_top = ndb.SuperFloatProperty('2', required=True, indexed=False)
  position_left = ndb.SuperFloatProperty('3', required=True, indexed=False)
  value = ndb.SuperStringProperty('4', required=True, indexed=False)


class CatalogImage(blob.Image):
  
  _kind = 36
  
  pricetags = ndb.SuperLocalStructuredProperty(CatalogPricetag, '6', repeated=True)
  
  def get_output(self):
    dic = super(CatalogImage, self).get_output()
    dic['_image_240'] = images.get_serving_url(self.image, 240)
    dic['_image_600'] = images.get_serving_url(self.image, 600)
    return dic


class Catalog(ndb.BaseExpando):
  
  _kind = 35
  
  created = ndb.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = ndb.SuperStringProperty('3', required=True)
  publish_date = ndb.SuperDateTimeProperty('4', required=True)
  discontinue_date = ndb.SuperDateTimeProperty('5', required=True)
  state = ndb.SuperStringProperty('6', required=True, default='unpublished', choices=['unpublished', 'published'])
  
  _expando_fields = {
    'cover': ndb.SuperKeyProperty('7', kind='36'),
    'cost': ndb.SuperDecimalProperty('8')
    }
  
  _virtual_fields = {
    '_images': ndb.SuperLocalStructuredProperty(CatalogImage, repeated=True),
    '_records': log.SuperLocalStructuredRecordProperty('35', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('35', Action.build_key('35', 'create').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
      ActionPermission('35', Action.build_key('35', 'lock').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
      ActionPermission('35', Action.build_key('35', 'update').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
      ActionPermission('35', Action.build_key('35', 'discontinue').urlsafe(), False, "context.rule.entity.namespace_entity.state != 'active' and context.rule.entity.state == 'unpublished'"),
      ActionPermission('35', Action.build_key('35', 'publish').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
      ActionPermission('35', Action.build_key('35', 'log_message').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
      ActionPermission('35', Action.build_key('35', 'duplicate').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')"),
      ActionPermission('35', Action.build_key('35-6').urlsafe(), False, "not (context.rule.entity.namespace_entity.state == 'active' and context.rule.entity.state == 'unpublished')")
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('35', 'create'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'publish_date': ndb.SuperDateTimeProperty(required=True),
        'discontinue_date': ndb.SuperDateTimeProperty(required=True)
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('35', 'lock'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty(required=True)
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('35', 'discontinue'),
      arguments={
        'key'  : ndb.SuperKeyProperty(kind='35', required=True),
        'message' : ndb.SuperTextProperty(required=True),
        'note' : ndb.SuperTextProperty(required=True)
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('35', 'publish'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty(required=True)
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('35', 'log_message'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'message': ndb.SuperTextProperty(required=True),
        'note': ndb.SuperTextProperty(required=True)
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('35', 'duplicate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('35', 'update'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'name': ndb.SuperStringProperty(required=True),
        '_images': ndb.SuperLocalStructuredProperty(CatalogImage, repeated=True),
        'publish_date': ndb.SuperDateTimeProperty(required=True),
        'discontinue_date': ndb.SuperDateTimeProperty(required=True),
        'start_images': ndb.SuperIntegerProperty(default=0)
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('35', 'upload_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'images': ndb.SuperLocalStructuredImageProperty(CatalogImage, repeated=True),
        'upload_url': ndb.SuperStringProperty()
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('35', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'start_images': ndb.SuperIntegerProperty(default=0)
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('35', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='35', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('35', 'prepare'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True)
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('35', 'search'),
      arguments={
        'domain': ndb.SuperKeyProperty(kind='6', required=True),
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "created", "operator": "desc"}},
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
      _plugins=[]
      )
    ]