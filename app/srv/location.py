# -*- coding: utf-8 -*-
'''
Created on Jan 9, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb
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
        common.Prepare(domain_model=False),
        rule.Prepare(skip_user_roles=True, strict=False),
        rule.Exec(),
        location.CountryUpdate()
        ]
      ),
    Action(
      key=Action.build_key('15', 'search'),
      arguments={
        'search': ndb.SuperSearchProperty(
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['=='], 'type': ndb.SuperKeyProperty(kind='15')},
            'name': {'operators': ['==', '!=', 'contains'], 'type': ndb.SuperStringProperty(value_filters=[lambda p,s: s.capitalize()])},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty(choices=[True])}
            },
          indexes=[
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['key']},
            {'filter': ['active'],
             'order_by': [['name', ['asc', 'desc']]]},
            {'filter': ['name', 'active'],
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
        common.Prepare(domain_model=False),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(page_size=-1),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'search_cursor', 'output.more': 'search_more'})
        ]
      )
    ]


class CountrySubdivision(ndb.BaseModel):
  
  _kind = 16
  
  _use_cache = True
  _use_memcache = True
  
  TYPES = {'unknown': 1,
           'municipalities': 81,
           'included for completeness': 36,
           'autonomous municipality': 53,
           'overseas region/department': 33,
           'london borough': 38,
           'commune': 21,
           'two-tier county': 37,
           'district council area': 42,
           'municipality': 10,
           'arctic region': 70,
           'entity': 12,
           'county': 5,
           'metropolitan region': 32,
           'capital territory': 69,
           'unitary authority (wales)': 44,
           'overseas territorial collectivity': 34,
           'rayon': 11,
           'borough': 82,
           'economic region': 61,
           'chains (of islands)': 66,
           'autonomous republic': 9,
           'administrative region': 46,
           'autonomous district': 78,
           'city': 6,
           'city with county rights': 49,
           'outlying area': 84,
           'capital metropolitan city': 57,
           'district': 13,
           'federal district': 19,
           'development region': 71,
           'parish': 1,
           'capital city': 50,
           'autonomous sector': 48,
           'administration': 31,
           'federal territories': 68,
           'canton': 25,
           'area': 75,
           'state': 7,
           'republic': 76,
           'indigenous region': 73,
           'department': 17,
           'territorial unit': 64,
           'territory': 8,
           'union territory': 52,
           'republican city': 59,
           'council area': 41,
           'province': 3,
           'division': 14,
           'emirate': 2,
           'quarter': 62,
           'island council': 83,
           'island group': 54,
           'geographical region': 28,
           'metropolitan cities': 58,
           'governorate': 16,
           'popularates': 60,
           'metropolitan district': 39,
           'capital district': 24,
           'local council': 67,
           'special island authority': 72,
           'self-governed part': 47,
           'autonomous region': 26,
           'federal dependency': 85,
           'autonomous city': 30,
           'prefecture': 22,
           'autonomous province': 65,
           'special municipality': 18,
           'autonomous territorial unit': 63,
           'autonomous community': 29,
           'administrative territory': 77,
           'country': 35,
           'region': 15,
           'economic prefecture': 23,
           'oblast': 20,
           'geographical unit': 51,
           'dependency': 4,
           'special zone': 45,
           'special administrative region': 27,
           'island': 55,
           'town council': 79,
           'geographical entity': 80,
           'city corporation': 40,
           'unitary authority (england)': 43,
           'constitutional province': 74,
           'special city': 56}
  
  parent_record = ndb.SuperKeyProperty('1', kind='16', indexed=False)
  code = ndb.SuperStringProperty('2', required=True, indexed=False)
  name = ndb.SuperStringProperty('3', required=True)
  complete_name = ndb.SuperTextProperty('4')
  type = ndb.SuperIntegerProperty('5', required=True, indexed=False)  # @todo Shall we make this string property and use choices prop for allowed values?
  active = ndb.SuperBooleanProperty('6', required=True, default=True)
  
  _virtual_fields = {
    'type_text': ndb.ComputedProperty(lambda self: self.type_into_text())
    }
  
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
          default={'filters': [], 'order_by': {'field': 'name', 'operator': 'asc'}},
          filters={
            'key': {'operators': ['=='], 'type': ndb.SuperKeyProperty(kind='16')},
            'name': {'operators': ['==', '!=', 'contains'], 'type': ndb.SuperStringProperty(value_filters=[lambda p, s: s.capitalize()])},
            'active': {'operators': ['==', '!='], 'type': ndb.SuperBooleanProperty(choices=[True])},
            'ancestor': {'operators': ['=='], 'type': ndb.SuperKeyProperty(kind='15')}
            },
          indexes=[
            {'filter': [],
             'order_by': [['name', ['asc', 'desc']]]},
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
        'next_cursor': ndb.SuperStringProperty()
        },
      _plugins=[
        common.Context(),
        common.Prepare(domain_model=False),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Exec(),
        common.Search(page_size=settings.SEARCH_PAGE),
        rule.Prepare(skip_user_roles=False, strict=False),
        rule.Read(),
        common.Set(dynamic_values={'output.entities': 'entities', 'output.next_cursor': 'search_cursor', 'output.more': 'search_more'})
        ]
      )
    ]
  
  def type_into_text(self):
    for name, key in self.TYPES.items():
      if key == self.type:
        return name
    return self.type


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
