# -*- coding: utf-8 -*-
'''
Created on Jan 9, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
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
                  street_address=location.street_address, 
                  street_address2=location.street_address2, 
                  email=location.email, 
                  telephone=location.telephone)

# done!
class Country(ndb.BaseModel):
    
    KIND_ID = 15
    
    # root
    # http://hg.tryton.org/modules/country/file/tip/country.py#l8
    # http://en.wikipedia.org/wiki/ISO_3166
    # http://hg.tryton.org/modules/country/file/tip/country.xml
    # http://downloads.tryton.org/2.8/trytond_country-2.8.0.tar.gz
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_country.py#L42
    # composite index: ancestor:no - active,name
    code = ndb.SuperStringProperty('1', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    name = ndb.SuperStringProperty('2', required=True)
    active = ndb.SuperBooleanProperty('3', default=True)
    
 
# done! - tryton ima CountrySubdivision za skoro sve zemlje!
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
    
        
    KIND_ID = 16
    
    # ancestor Country
    # http://hg.tryton.org/modules/country/file/tip/country.py#l52
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_country.py#L86
    # koliko cemo drilldown u ovoj strukturi zavisi od kasnijih odluka u vezi povezivanja lokativnih informacija sa informacijama ovog modela..
    # composite index: ancestor:yes - name; ancestor:yes - active,name
    
    #  kind='app.core.misc.CountrySubdivision',
    parent_record = ndb.SuperKeyProperty('1', kind='16', indexed=False)
     
    code = ndb.SuperStringProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    name = ndb.SuperStringProperty('3', required=True)
    complete_name = ndb.SuperTextProperty('4')
    type = ndb.SuperIntegerProperty('5', required=True, indexed=False)
    active = ndb.SuperBooleanProperty('6', default=True)
 
 
class Location(ndb.BaseExpando):
    
    # local structured
    name = ndb.SuperStringProperty('1', required=True)
    country = ndb.SuperKeyProperty('2', kind=Country, required=True, indexed=False)
    city = ndb.SuperStringProperty('3', required=True, indexed=False)
    postal_code = ndb.SuperStringProperty('4', required=True, indexed=False)
    street = ndb.SuperStringProperty('5', required=True, indexed=False)
 
    _default_indexed = False
 
    EXPANDO_FIELDS = {
        'region' :  ndb.SuperKeyProperty('8', kind=CountrySubdivision),
        'email' : ndb.SuperStringProperty('10'),
        'telephone' : ndb.SuperStringProperty('11'),
    }