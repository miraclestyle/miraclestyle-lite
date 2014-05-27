# -*- coding: utf-8 -*-
'''
Created on Jan 9, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb, settings
from app.srv.event import Action
from app.srv.rule import GlobalRole, ActionPermission, FieldPermission
from app.plugins import common, rule, callback, log, location


def get_location(location):
  if isinstance(location, ndb.Key):
    location = location.get()
  location_country = location.country.get()
  location_region = location.region.get()
  return Location(name=location.name,
                  country=location_country.name,
                  country_code=location_country.code,
                  region=location_region.name,
                  region_code=location_region.code,
                  city=location.city,
                  postal_code=location.postal_code,
                  street=location.street,
                  email=location.email,
                  telephone=location.telephone)


class Country(ndb.BaseModel):
  
  _kind = 15
  
  _use_cache = True
  _use_memcache = True
  
  code = ndb.SuperStringProperty('1', required=True, indexed=False)
  name = ndb.SuperStringProperty('2', required=True)
  active = ndb.SuperBooleanProperty('3', required=True, default=True)
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('15', Action.build_key('15', 'update'), True, 'context.user._root_admin or context.user._is_taskqueue'),
      ActionPermission('15', Action.build_key('15', 'search'), True, 'True'),
      FieldPermission('15', ['code', 'name', 'active'], True, True, 'True')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('15', 'update'),
      arguments={},
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        location.CountryUpdate(file_path=settings.LOCATION_DATA_FILE)
        ]
      ),
    Action(
      key=Action.build_key('15', 'search'),
      arguments={
        'search': ndb.SuperSearchProperty(
          default={'filters': [{'field': 'active', 'value': True, 'operator': '=='}], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['IN'], 'type': ndb.SuperKeyProperty(kind='15', repeated=True)},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty(choices=[True])}
            },
          indexes=[
            {'filter': ['key']},
            {'filter': ['active'],
             'order_by': [['name', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
            }
          ),
        'search_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(page_size=-1),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities',
                                   'output.search_cursor': 'search_cursor',
                                   'output.search_more': 'search_more'})
        ]
      )
    ]


class CountrySubdivision(ndb.BaseModel):
  
  _kind = 16
  
  _use_cache = True
  _use_memcache = True
  
  parent_record = ndb.SuperKeyProperty('1', kind='16', indexed=False)
  code = ndb.SuperStringProperty('2', required=True, indexed=False)
  name = ndb.SuperStringProperty('3', required=True)
  complete_name = ndb.SuperTextProperty('4')
  type = ndb.SuperStringProperty('5', required=True, indexed=False)
  active = ndb.SuperBooleanProperty('6', required=True, default=True)
  
  _global_role = GlobalRole(
    permissions=[
      ActionPermission('16', Action.build_key('16', 'search'), True, 'True'),
      FieldPermission('16', ['parent_record', 'code', 'name', 'complete_name', 'type', 'type_text', 'active'], True, True, 'True')
      ]
    )
  
  _actions = [
    Action(
      key=Action.build_key('16', 'search'),
      arguments={
        'search': ndb.SuperSearchProperty(
          default={'filters': [{'field': 'active', 'value': True, 'operator': '=='}], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['IN'], 'type': ndb.SuperKeyProperty(kind='16', repeated=True)},
            'name': {'operators': ['==', '!=', 'contains'], 'type': ndb.SuperStringProperty(value_filters=[lambda p, s: s.capitalize()])},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty(choices=[True])},
            'ancestor': {'operators': ['=='], 'type': ndb.SuperKeyProperty(kind='15')}
            },
          indexes=[
            {'filter': ['key']},
            {'filter': ['active'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name', 'active'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['active', 'ancestor'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name', 'active', 'ancestor'],
             'order_by': [['name', ['asc', 'desc']]]}
            ],
          order_by={
            'name': {'operators': ['asc', 'desc']}
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
      )
    ]


class Location(ndb.BaseExpando):
  
  _kind = 68
  
  name = ndb.SuperStringProperty('1', required=True, indexed=False)
  country = ndb.SuperStringProperty('2', required=True, indexed=False)
  country_code = ndb.SuperStringProperty('3', required=True, indexed=False)
  city = ndb.SuperStringProperty('4', required=True, indexed=False)
  postal_code = ndb.SuperStringProperty('5', required=True, indexed=False)
  street = ndb.SuperStringProperty('6', required=True, indexed=False)
  
  _default_indexed = False
  
  _expando_fields = {
    'region': ndb.SuperStringProperty('7'),
    'region_code': ndb.SuperStringProperty('8'),
    'email': ndb.SuperStringProperty('9'),
    'telephone': ndb.SuperStringProperty('10')
    }
