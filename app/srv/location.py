# -*- coding: utf-8 -*-
'''
Created on Jan 9, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb


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
  
  # root
  # http://hg.tryton.org/modules/country/file/tip/country.py#l8
  # http://en.wikipedia.org/wiki/ISO_3166
  # http://hg.tryton.org/modules/country/file/tip/country.xml
  # http://downloads.tryton.org/2.8/trytond_country-2.8.0.tar.gz
  # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_country.py#L42
  # composite index: ancestor:no - active,name
  code = ndb.SuperStringProperty('1', required=True, indexed=False) # Turn on index if projection query is required.
  name = ndb.SuperStringProperty('2', required=True)
  active = ndb.SuperBooleanProperty('3', default=True)
  
  @classmethod
  def import_countries_and_subdivisions(cls, args):
    url = 'https://raw.github.com/tryton/country/develop/country.xml'
    from xml.etree import ElementTree
    from google.appengine.api import urlfetch
    text = urlfetch.fetch(url) 
    tree = ElementTree.fromstring(text.content)
    root = tree.findall('data')
    
    to_put = []
    
    for child in root[1]:
      dat = dict()
      dat['id'] = child.attrib['id']
      for child2 in child:
        name = child2.attrib.get('name')
        if name is None:
          continue
        if child2.text:
          dat[name] = child2.text
          
      to_put.append(cls(name=dat['name'], id=dat['id'], code=dat['code'], active=True))
    
    for child in root[2]:
      dat = dict()
      dat['id'] = child.attrib['id']
      for child2 in child:
        k = child2.attrib.get('name')
        if k is None:
          continue
        if child2.text:
          dat[k] = child2.text
        if 'ref' in child2.attrib:
          dat[k] = child2.attrib['ref']
      
      kw = dict(name=dat['name'], id=dat['id'], type=CountrySubdivision.TYPES.get(dat['type'], 'unknown'), code=dat['code'], active=True)
      
      if 'country' in dat:
        kw['parent'] = ndb.Key(Country, dat['country'])
      
      if 'parent' in dat:
        kw['parent_record'] = ndb.Key(CountrySubdivision, dat['parent'])
      
      to_put.append(CountrySubdivision(**kw))
    
    ndb.put_multi(to_put)
    return {'response' : {'items' : [put.key.id() for put in to_put]}}


class CountrySubdivision(ndb.BaseModel):
  
  TYPES = {
           'unknown' : 1,
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
           'special city': 56
           }
  
  _kind = 16
  
  # ancestor Country
  # http://hg.tryton.org/modules/country/file/tip/country.py#l52
  # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_country.py#L86
  # composite index: ancestor:yes - name; ancestor:yes - active,name
  # kind='app.core.misc.CountrySubdivision',
  parent_record = ndb.SuperKeyProperty('1', kind='16', indexed=False)
  code = ndb.SuperStringProperty('2', required=True, indexed=False) # Turn on index if projection query is required.
  name = ndb.SuperStringProperty('3', required=True)
  complete_name = ndb.SuperTextProperty('4')
  type = ndb.SuperIntegerProperty('5', required=True, indexed=False)
  active = ndb.SuperBooleanProperty('6', default=True)


class Location(ndb.BaseExpando):
  
  # Local structured property
  name = ndb.SuperStringProperty('1', required=True, indexed=False)
  country = ndb.SuperStringProperty('2', required=True, indexed=False)
  country_code = ndb.SuperStringProperty('3', required=True, indexed=False)
  city = ndb.SuperStringProperty('4', required=True, indexed=False)
  postal_code = ndb.SuperStringProperty('5', required=True, indexed=False)
  street = ndb.SuperStringProperty('6', required=True, indexed=False)
  
  _default_indexed = False
  
  EXPANDO_FIELDS = {
                    'region' :  ndb.SuperStringProperty('7'),
                    'region_code' :  ndb.SuperStringProperty('8'),
                    'email' : ndb.SuperStringProperty('9'),
                    'telephone' : ndb.SuperStringProperty('10'),
                    }
