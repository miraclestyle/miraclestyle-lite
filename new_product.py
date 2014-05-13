# -*- coding: utf-8 -*-
'''
Created on May 12, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import itertools
import hashlib
import collections
import copy
import json
import os

from app import ndb, settings
from app.srv.event import Action
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.srv import log as ndb_log
from app.srv import blob as ndb_blob
from app.plugins import common, rule, log, callback, blob, product

from app.srv import uom

__SYSTEM_CATEGORIES = collections.OrderedDict()

def search_system_categories(query=None, limit=100):
  # Missing search logic!
  items = get_system_category().values()
  return items[:limit]

def get_system_category(category_key=None):
  global __SYSTEM_CATEGORIES
  if category_key == None:
    return __SYSTEM_CATEGORIES
  return __SYSTEM_CATEGORIES.get(category_key.urlsafe())

def register_system_categories(*categories):
  global __SYSTEM_CATEGORIES
  for category in categories:
    __SYSTEM_CATEGORIES[category.key.urlsafe()] = category

##### instead of using virtaulkey properties + validator for Category and Units, 
##### perhaps we should use custom property that will check their existance accordingly?
#### currently this function and property is unused until decided what should be used
def _validate_category(prop, value):
  return get_system_category(value)


class CategoryKeyProperty(ndb.SuperVirtualKeyProperty):
  
  def format(self):
    category_key = super(CategoryKeyProperty, self).format()
    if not get_system_category(category_key):
      raise ndb.PropertyError('invalid_category')


class Content(ndb.BaseModel):
  
  _kind = 43
  
  title = ndb.SuperStringProperty('1', required=True, indexed=False)
  body = ndb.SuperTextProperty('2', required=True)


class Variant(ndb.BaseModel):
  
  _kind = 42
  
  name = ndb.SuperStringProperty('1', required=True, indexed=False)
  description = ndb.SuperTextProperty('2')
  options = ndb.SuperStringProperty('3', repeated=True, indexed=False)
  allow_custom_value = ndb.SuperBooleanProperty('4', required=True, indexed=False, default=False)


class Image(ndb_blob.Image):
  
  _kind = 76
  
  def get_output(self):
    dic = super(Image, self).get_output()
    dic['_image_240'] = self.get_serving_url(240)
    dic['_image_600'] = self.get_serving_url(600)
    return dic


class Images(ndb.BaseModel):
  
  _kind = 73
  
  images = ndb.SuperLocalStructuredProperty(Image, '1', repeated=True)  # Soft limit 100 instances.


class Variants(ndb.BaseModel):
  
  _kind = 74
  
  variants = ndb.SuperLocalStructuredProperty(Variant, '1', repeated=True)  # Soft limit 100 instances.


class Contents(ndb.BaseModel):
  
  _kind = 75
  
  contents = ndb.SuperLocalStructuredProperty(Content, '1', repeated=True)  # Soft limit 100 instances.


class Category(ndb.BaseModel):
  
  _kind = 17
  
  parent_record = ndb.SuperKeyProperty('1', kind='17', indexed=False)
  name = ndb.SuperStringProperty('2', required=True)  # @todo indexed=False?
  complete_name = ndb.SuperTextProperty('3')
  state = ndb.SuperStringProperty('4', required=True, default='searchable', choices=[])


class Template(ndb.BaseExpando):
  
  _kind = 38
  
  product_category = ndb.SuperKeyProperty('1', kind='17', required=True, indexed=False)
  name = ndb.SuperStringProperty('2', required=True)
  description = ndb.SuperTextProperty('3', required=True)  # Soft limit 64kb.
  product_uom = ndb.SuperKeyProperty('4', kind='19', required=True, indexed=False)
  unit_price = ndb.SuperDecimalProperty('5', required=True)  # @todo indexed=False?
  availability = ndb.SuperStringProperty('6', required=True, indexed=False, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock'])
  code = ndb.SuperStringProperty('7', required=True)
  # availability: - ovo cemo pojasniti
  # 'in stock'
  # 'available for order'
  # 'out of stock'
  # 'preorder'
  # 'auto manage inventory - available for order' (poduct is 'available for order' when inventory balance is <= 0)
  # 'auto manage inventory - out of stock' (poduct is 'out of stock' when inventory balance is <= 0)
  # https://support.google.com/merchants/answer/188494?hl=en&ref_topic=2473824
  
  _default_indexed = False
  
  _expando_fields = {
    'weight': ndb.SuperDecimalProperty('8'),
    'weight_uom': ndb.SuperKeyProperty('9', kind='19'),
    'volume': ndb.SuperDecimalProperty('10'),
    'volume_uom': ndb.SuperKeyProperty('11', kind='19'),
    'low_stock_quantity': ndb.SuperDecimalProperty('12', default='0.00')  # Notify store manager when quantity drops below X quantity.
    }
  
  _virtual_fields = {
    '_images': ndb.SuperLocalStructuredProperty(Image, repeated=True),
    '_contents': ndb.SuperLocalStructuredProperty(Content, repeated=True),
    '_variants': ndb.SuperLocalStructuredProperty(Variant, repeated=True),
    '_records': ndb_log.SuperLocalStructuredRecordProperty('38', repeated=True)
    }
  
  _global_role = GlobalRole(
    permissions=[
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('38', 'prepare'),
      arguments={
        'catalog': ndb.SuperKeyProperty(kind='35', required=True),
        'upload_url': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        product.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        blob.URL(gs_bucket_name=settings.PRODUCT_TEMPLATE_BUCKET),
        common.Set('output.entity': 'entities.38')
        ]
      ),
    Action(
      key=Action.build_key('38', 'create'),
      arguments={
        'product_category': ndb.SuperVirtualKeyProperty(kind='17', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'description': ndb.SuperTextProperty(required=True),
        'product_uom': ndb.SuperVirtualKeyProperty(kind='19', required=True),
        'unit_price': ndb.SuperDecimalProperty(required=True),
        'availability': ndb.SuperStringProperty(required=True, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
        'code': ndb.SuperStringProperty(required=True),
        'weight': ndb.SuperDecimalProperty(required=True),
        'weight_uom': ndb.SuperVirtualKeyProperty(kind='19', required=True),
        'volume': ndb.SuperDecimalProperty(required=True),
        'volume_uom': ndb.SuperVirtualKeyProperty(kind='19', required=True),
        'low_stock_quantity': ndb.SuperDecimalProperty(default='0.00'),
        'catalog': ndb.SuperKeyProperty(kind='35', required=True)
        },
      _plugins=[
        common.Context(),
        product.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values{'values.38.product_category': 'input.product_category',
                                  'values.38.name': 'input.name',
                                  'values.38.description': 'input.description',
                                  'values.38.product_uom': 'input.product_uom',
                                  'values.38.unit_price': 'input.unit_price',
                                  'values.38.availability': 'input.availability',
                                  'values.38.code': 'input.code',
                                  'values.38.weight': 'input.weight',
                                  'values.38.weight_uom': 'input.weight_uom',
                                  'values.38.volume': 'input.volume',
                                  'values.38.volume_uom': 'input.volume_uom',
                                  'values.38.low_stock_quantity': 'input.low_stock_quantity'}),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.38'}),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.38.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.38'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'update'),
      arguments={
        '_variants': ndb.SuperLocalStructuredProperty(Variant, repeated=True),
        '_contents': ndb.SuperLocalStructuredProperty(Content, repeated=True),
        '_images': ndb.SuperLocalStructuredProperty(Image, repeated=True),
        'product_category': ndb.SuperVirtualKeyProperty(kind='17', required=True),
        'name': ndb.SuperStringProperty(required=True),
        'description': ndb.SuperTextProperty(required=True),
        'product_uom': ndb.SuperVirtualKeyProperty(kind='19', required=True),
        'unit_price': ndb.SuperDecimalProperty(required=True),
        'availability': ndb.SuperStringProperty(required=True, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
        'code': ndb.SuperStringProperty(required=True),
        'weight': ndb.SuperDecimalProperty(required=True),
        'weight_uom': ndb.SuperVirtualKeyProperty(kind='19', required=True),
        'volume': ndb.SuperDecimalProperty(required=True),
        'volume_uom': ndb.SuperVirtualKeyProperty(kind='19', required=True),
        'low_stock_quantity': ndb.SuperDecimalProperty(default='0.00'),
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Set(dynamic_values{'values.38.product_category': 'input.product_category',
                                  'values.38.name': 'input.name',
                                  'values.38.description': 'input.description',
                                  'values.38.product_uom': 'input.product_uom',
                                  'values.38.unit_price': 'input.unit_price',
                                  'values.38.availability': 'input.availability',
                                  'values.38.code': 'input.code',
                                  'values.38.weight': 'input.weight',
                                  'values.38.weight_uom': 'input.weight_uom',
                                  'values.38.volume': 'input.volume',
                                  'values.38.volume_uom': 'input.volume_uom',
                                  'values.38.low_stock_quantity': 'input.low_stock_quantity',
                                  'values.38._images': 'input._images',
                                  'values.38._variants': 'input._variants',
                                  'values.38._contents': 'input._contents'}),
        product.UpdateSet(),
        rule.Write(transactional=True),
        common.Write(transactional=True),
        log.Entity(transactional=True),
        product.WriteImages(transactional=True),
        product.WriteVariants(transactional=True),
        product.WriteContents(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.38'}),
        blob.Delete(transactional=True, keys_location='delete_blobs'),
        callback.Payload(transactional=True, queue = 'notify',
                         static_data = {'action_id': 'initiate', 'action_model': '61'},
                         dynamic_data = {'caller_entity': 'entities.38.key_urlsafe'}),
        callback.Exec(transactional=True,
                      dynamic_data = {'caller_user': 'user.key_urlsafe', 'caller_action': 'action.key_urlsafe'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'search'),
      arguments={
        'catalog': ndb.SuperKeyProperty(kind='35', required=True),
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "name", "operator": "desc"}},
          filters={
            'name': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()},
            'product_category': {'operators': ['==', '!='], 'type': ndb.SuperVirtualKeyProperty(kind='17')}
            },
          indexes=[
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['product_category'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name', 'product_category'],
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
        product.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        log.Read(),
        rule.Read(),
        common.Set(dynamic_values={'output.entity': 'entities.38', 'output.next_cursor': 'next_cursor', 'output.more': 'more'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'upload_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True),
        '_images': ndb.SuperLocalStructuredImageProperty(Image, repeated=True)
        },
      _plugins=[
        common.Context(),
        common.Read(),
        product.Read(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        product.UploadImagesSet(),
        rule.Write(transactional=True),
        product.WriteImages(transactional=True),
        log.Write(transactional=True),
        rule.Read(transactional=True),
        common.Set(transactional=True, dynamic_values={'output.entity': 'entities.38'})
        ]
      ),
    Action(
      key=Action.build_key('38', 'duplicate'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='38', required=True)
        },
      _plugins=[]
      )
    ]


class Instance(ndb.BaseExpando):
  
  _kind = 39
  
  _default_indexed = False
  
  _expando_fields = {
    'code': ndb.SuperStringProperty('1', required=True),
    'availability': ndb.SuperStringProperty('2', required=True, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
    'description': ndb.SuperTextProperty('3', required=True),
    'unit_price': ndb.SuperDecimalProperty('4', required=True),
    'low_stock_quantity': ndb.SuperDecimalProperty('5', default='0.00'),
    'weight': ndb.SuperDecimalProperty('6'),
    'weight_uom': ndb.SuperKeyProperty('7', kind='19'),
    'volume': ndb.SuperDecimalProperty('8'),
    'volume_uom': ndb.SuperKeyProperty('9', kind='19')
    }
  
  _global_role = GlobalRole(
    permissions=[
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('39', 'read'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='39', required=True)
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('39', 'update'),
      arguments={
        'code': ndb.SuperStringProperty(required=True),
        'availability': ndb.SuperStringProperty(required=True, default='in stock', choices=['in stock', 'available for order', 'out of stock', 'preorder', 'auto manage inventory - available for order', 'auto manage inventory - out of stock']),
        'description': ndb.SuperTextProperty(required=True),
        'unit_price': ndb.SuperDecimalProperty(required=True),
        '_contents': ndb.SuperLocalStructuredProperty(Content, repeated=True),
        '_variants': ndb.SuperLocalStructuredProperty(Variant, repeated=True),
        '_images': ndb.SuperLocalStructuredProperty(Image, repeated=True),
        'weight': ndb.SuperDecimalProperty(required=True),
        'weight_uom': ndb.SuperVirtualKeyProperty(kind='19', required=True),
        'volume': ndb.SuperDecimalProperty(required=True),
        'volume_uom': ndb.SuperVirtualKeyProperty(kind='19', required=True),
        'key': ndb.SuperKeyProperty(kind='39', required=True)
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('39', 'search'),
      arguments={
        'search': ndb.SuperSearchProperty(
          default={"filters": [], "order_by": {"field": "code", "operator": "desc"}},
          filters={
            'code': {'operators': ['==', '!='], 'type': ndb.SuperStringProperty()}
            },
          indexes=[
            {'filter': [],
             'order_by': [['code', ['asc', 'desc']]]},
            {'filter': ['code'],
             'order_by': [['code', ['asc', 'desc']]]}
            ],
          order_by={
            'code': {'operators': ['asc', 'desc']}
            }
          ),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('39', 'read_records'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='39', required=True),
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[]
      ),
    Action(
      key=Action.build_key('39', 'upload_images'),
      arguments={
        'key': ndb.SuperKeyProperty(kind='39', required=True),
        'images': ndb.SuperLocalStructuredImageProperty(Image, repeated=True),
        'upload_url': ndb.SuperStringProperty()
        },
      _plugins=[]
      )
    ]

def build_categories():
  # this code builds leaf categories for selection with complete names, 3.8k of them
  root_path = os.path.abspath('.')
  data = []
  with file(os.path.join(root_path, 'google_taxonomy.txt')) as f:
    for line in f:
      if not line.startswith('#'):
        data.append(line.replace("\n", ''))
  write_data = []
  sep = ' > '
  parent = None
  dig = 0
  for ii, item in enumerate(data):
    new_cat = {}
    current = item.split(sep)
    try:
      next = data[ii+1].split(sep)
    except IndexError as e:
      next = current
    if len(next) == len(current):
      current_total = len(current) - 1
      last = current[current_total]
      parent = current[current_total - 1]
      new_cat['id'] = hashlib.md5(last).hexdigest()
      new_cat['parent_record'] = Category.build_key(hashlib.md5(parent).hexdigest())
      new_cat['name'] = last
      new_cat['complete_name'] = " / ".join(current[:current_total+1])
      new_cat['state'] = 'active'
      write_data.append(new_cat)
    """    
    This old code builds entire list of categories, 5.8k of them
    for i,s in enumerate(cats):
      if s:
        new_cat['id'] = hashlib.md5(s).hexdigest()
        parent = None
        if i != 0:
          try:
            parent = Category.build_key(hashlib.md5(cats[i-1]).hexdigest())
          except IndexError as e:
            pass
        new_cat['parent_record'] = parent
        new_cat['name'] = s
        new_cat['complete_name'] = " / ".join(cats[:i+1])
        new_cat['state'] = 'active'
    __write_data.append(new_cat)
    """
  return write_data

register_system_categories(*(Category(**d) for d in build_categories()))
