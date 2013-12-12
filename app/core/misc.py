# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

# done 80%

class Content(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 14
    # root
    # composite index: ancestor:no - category,active,sequence
    updated = ndb.SuperDateTimeProperty('1', auto_now=True)
    title = ndb.SuperStringProperty('2', required=True)
    category = ndb.SuperIntegerProperty('3', required=True)
    body = ndb.SuperTextProperty('4', required=True)
    sequence = ndb.SuperIntegerProperty('5', required=True)
    active = ndb.SuperBooleanProperty('6', default=False)
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @property
    def is_usable(self):
        return self.active
    
    # def delete inherits from BaseModel see `ndb.BaseModel.delete()`
    
    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls)
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
             
            if not create:
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response  

     
 
# done!
class Image(ndb.BaseModel):
    
    # base class/structured class
    image = ndb.SuperImageKeyProperty('1', required=True, indexed=False)# blob ce se implementirati na GCS
    content_type = ndb.SuperStringProperty('2', required=True, indexed=False)
    size = ndb.SuperFloatProperty('3', required=True, indexed=False)
    width = ndb.SuperIntegerProperty('4', required=True, indexed=False)
    height = ndb.SuperIntegerProperty('5', required=True, indexed=False)
    sequence = ndb.SuperIntegerProperty('6', required=True)
 
 
# done!
class Country(ndb.BaseModel, ndb.Workflow):
    
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
 
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @property
    def is_usable(self):
        # makes a check wether is this possible to be used somewhere
        return self.action
    
    @classmethod
    def import_countries_and_subdivisions(cls, values):
        
        # this function cannot do all this many imports because the appengine hangs
        
        url = 'https://raw.github.com/tryton/country/develop/country.xml'
        
        from xml.etree import ElementTree
        from google.appengine.api import urlfetch
         
        text = urlfetch.fetch(url) 
         
        tree = ElementTree.fromstring(text.content)
        root = tree.findall('data')
        
        response = ndb.Response()
         
        for child in root[1]:
            dat = dict()
            dat['id'] = child.attrib['id']
            for child2 in child:
                name = child2.attrib.get('name')
                if name is None:
                   continue
               
                if child2.text:
                   dat[name] = child2.text
        
            cls.manage(name=dat['name'], id=dat['id'], code=dat['code'], active=True)
         
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
             
            CountrySubdivision.manage(**kw) 
  
        return response.status('ok')
        
    
    @classmethod
    def list(cls, values):
        
        response = ndb.Response()
        
        response['items'] = cls.query().fetch()
        
        return response
    
    @classmethod
    def delete(cls, values):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
                  else:
                     return response.not_authorized()
               else:
                  response.not_found()      
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        return response
    
    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls)
            
            if response.has_error():
               return response
           
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
             
            if not create:
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity):
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response
         
        

# done! - tryton ima CountrySubdivision za skoro sve zemlje!
class CountrySubdivision(ndb.BaseModel, ndb.Workflow):
    
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
    type = ndb.SuperIntegerProperty('4', required=True, indexed=False)
    active = ndb.SuperBooleanProperty('5', default=True)
     
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    } 
    
    @property
    def is_usable(self):
        return self.active
    
    @classmethod
    def delete(cls, values):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
                  else:
                     return response.not_authorized()
               else:
                  response.not_found()      
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        return response
    
    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls)
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
             
            if not create:
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response  
 


# done!
class Location(ndb.BaseExpando):
    
    # base class/structured class
    country = ndb.SuperKeyProperty('1', kind=Country, required=True, indexed=False)
    
    _default_indexed = False
    
    EXPANDO_FIELDS = {
      'region' : ndb.SuperKeyProperty('2', kind=CountrySubdivision), # ako je potreban string val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje
      'postal_code_from' : ndb.SuperStringProperty('3'),
      'postal_code_to' : ndb.SuperStringProperty('4'),
      'city' : ndb.SuperStringProperty('5')# ako se javi potreba za ovim ??                      
    }
 

# done!
class ProductCategory(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 17
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/category.py#l8
    # https://support.google.com/merchants/answer/1705911
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L227
    # composite index: ancestor:no - status,name
    
    #  kind='app.core.misc.ProductCategory',
    parent_record = ndb.SuperKeyProperty('1', kind='17', indexed=False)
    name = ndb.SuperStringProperty('2', required=True)
    complete_name = ndb.SuperTextProperty('3', required=True)# da je ovo indexable bilo bi idealno za projection query
    status = ndb.SuperIntegerProperty('4', required=True)
  
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @property
    def is_usable(self):
        return self.status
    
    @classmethod
    def delete(cls, values):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
                  else:
                     return response.not_authorized()
               else:
                  response.not_found()      
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        return response

    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls)
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
             
            if not create:
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response   

 
# done!
class UOM(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 19
    
    # ancestor ProductUOMCategory
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l28
    # http://hg.tryton.org/modules/product/file/tip/uom.xml#l63 - http://hg.tryton.org/modules/product/file/tip/uom.xml#l312
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L89
    # mozda da ovi entiteti budu non-deletable i non-editable ??
    # composite index: ancestor:no - active,name
    name = ndb.SuperStringProperty('1', required=True)
    symbol = ndb.SuperStringProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    rate = ndb.SuperDecimalProperty('3', required=True, indexed=False)# The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12)
    factor = ndb.SuperDecimalProperty('4', required=True, indexed=False)# The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12)
    rounding = ndb.SuperDecimalProperty('5', required=True, indexed=False)# Rounding Precision - digits=(12, 12)
    digits = ndb.SuperIntegerProperty('6', required=True, indexed=False)
    active = ndb.SuperBooleanProperty('7', default=True)
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }

    
    @classmethod
    def delete(cls, values):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
                  else:
                     return response.not_authorized()
               else:
                  response.not_found()      
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        return response

    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls, only=('name',), convert=[('measurement', Measurement, not create)])
            
            if response.has_error():
               return response
             
            entity = cls.prepare(create, values, parent=values.get('measurement'))
            
            if entity is None:
               return response.not_found()
             
            if not create:
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response
    

    
# done!
class Measurement(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 18
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l16
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L81
    # mozda da ovi entiteti budu non-deletable i non-editable ??
    name = ndb.SuperStringProperty('1', required=True)
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }

    @classmethod
    def delete(cls, values):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
                  else:
                     return response.not_authorized()
               else:
                  response.not_found()      
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        return response

    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls, only=('name',))
            
            if response.has_error():
               return response
             
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
             
            if not create:
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response



# done!
class Currency(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 20
    
    # root
    # http://hg.tryton.org/modules/currency/file/tip/currency.py#l14
    # http://en.wikipedia.org/wiki/ISO_4217
    # http://hg.tryton.org/modules/currency/file/tip/currency.xml#l107
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_currency.py#L32
    # composite index: ancestor:no - active,name
    name = ndb.SuperStringProperty('1', required=True)
    symbol = ndb.SuperStringProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    code = ndb.SuperStringProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    numeric_code = ndb.SuperStringProperty('4', indexed=False)
    rounding = ndb.SuperDecimalProperty('5', required=True, indexed=False)
    digits = ndb.SuperIntegerProperty('6', required=True, indexed=False)
    active = ndb.SuperBooleanProperty('7', default=True)
    #formating
    grouping = ndb.SuperStringProperty('8', required=True, indexed=False)
    decimal_separator = ndb.SuperStringProperty('9', required=True, indexed=False)
    thousands_separator = ndb.SuperStringProperty('10', indexed=False)
    positive_sign_position = ndb.SuperIntegerProperty('11', required=True, indexed=False)
    negative_sign_position = ndb.SuperIntegerProperty('12', required=True, indexed=False)
    positive_sign = ndb.SuperStringProperty('13', indexed=False)
    negative_sign = ndb.SuperStringProperty('14', indexed=False)
    positive_currency_symbol_precedes = ndb.SuperBooleanProperty('15', default=True, indexed=False)
    negative_currency_symbol_precedes = ndb.SuperBooleanProperty('16', default=True, indexed=False)
    positive_separate_by_space = ndb.SuperBooleanProperty('17', default=True, indexed=False)
    negative_separate_by_space = ndb.SuperBooleanProperty('18', default=True, indexed=False)
    
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    @property
    def is_usable(self):
        return self.active
    
    @classmethod
    def delete(cls, values):
 
        response = ndb.Response()
 
        @ndb.transactional(xg=True)
        def transaction():
                       
               current = ndb.get_current_user()
               
               entity = cls.prepare(False, values, get_only=True)
               
               if entity and entity.loaded():
                  if current.has_permission('delete', entity):
                     entity.new_action('delete', log_object=False)
                     entity.record_action()
                     entity.key.delete()
                      
                     response.status(entity)
                  else:
                     return response.not_authorized()
               else:
                  response.not_found()      
            
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
           
        return response

    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls)
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
             
            if not create:
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity): 
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response
 
     

# @todo
class Message(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 21
    
    # root
    outlet = ndb.SuperIntegerProperty('1', required=True, indexed=False)
    group = ndb.SuperIntegerProperty('2', required=True, indexed=False)
    state = ndb.SuperIntegerProperty('3', required=True)
 
    OBJECT_DEFAULT_STATE = 'composing'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'composing' : (1, ),
        'processing' : (2, ),
        'completed' : (3, ),
        'canceled' : (4, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'send' : 3,
       'complete' : 4,
       'cancel' : 5,
    }
    
    OBJECT_TRANSITIONS = {
        'send' : {
            'from' : ('composing',),
            'to' : ('processing',),
         },
        'complete' : {
           'from' : ('processing',),
           'to'   : ('completed',),
        },
        'cancel' : {
           'from' : ('composing',),
           'to'   : ('canceled',),
        },
    }
    
# @todo
class BillingCreditAdjustment(ndb.BaseModel):
    
    KIND_ID = 22
    
    # root (namespace Domain)
    # not logged
    adjusted = ndb.SuperDateTimeProperty('2', auto_now_add=True, indexed=False)
    agent = ndb.SuperKeyProperty('3', kind='app.core.acl.User', required=True, indexed=False)
    amount = ndb.SuperDecimalProperty('4', required=True, indexed=False)
    message = ndb.SuperTextProperty('5')# soft limit 64kb - to determine char count
    note = ndb.SuperTextProperty('6')# soft limit 64kb - to determine char count
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
    }    
     
     
class FeedbackRequest(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 23
    
    # ancestor User
    # ako hocemo da dozvolimo sva sortiranja, i dodatni filter po state-u uz sortiranje, onda nam trebaju slecedi indexi
    # composite index:
    # ancestor:yes - updated:desc; ancestor:yes - created:desc;
    # ancestor:yes - state,updated:desc; ancestor:yes - state,created:desc
    reference = ndb.SuperStringProperty('1', required=True, indexed=False)
    state = ndb.SuperIntegerProperty('2', required=True)
    updated = ndb.SuperDateTimeProperty('3', auto_now=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True)
 
    
    OBJECT_DEFAULT_STATE = 'new'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za state none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'new' : (1, ),
        'su_reviewing' : (2, ),
        'su_duplicate' : (3, ),
        'su_accepted' : (4, ),
        'su_dismissed' : (5, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'log_message' : 2,
       'sudo' : 3,
    }
    
    OBJECT_TRANSITIONS = {
        'su_review' : {
            'from' : ('new',),
            'to' : ('su_reviewing',),
         },
        'su_close' : {
           'from' : ('su_reviewing', ),
           'to'   : ('su_duplicate', 'su_accepted', 'su_dismissed',),
        },
    }

    @classmethod
    def manage(cls, create, values, **kwdss):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls, only=('reference',))
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values)
            
            if entity is None:
               return response.not_found()
      
            if create:
               if not current.is_guest:
                   entity.set_state(cls.OBJECT_DEFAULT_STATE)
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response 
  
    @classmethod
    def sudo(cls, values, **kwds):
        
        response = ndb.Response()
        
        @ndb.transactional(xg=True) 
        def transaction(): 
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
               # check if user can do this
 
               action = values.get('action')
               
               if not action.startswith('su_'):
                  return response.not_authorized()
               
               current = ndb.get_current_user()
               if current.has_permission(action, entity):
                      state = values.get('state')
                      entity.new_action(action, state=state, message=values.get('message'), note=values.get('note'))
                      entity.put()
                      entity.record_action()
                      response.status(entity)
               else:
                   return response.not_authorized()
            else:
                response.not_found()
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)   
               
        return response
    
    @classmethod
    def log_message(cls, values, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)  
        def transaction(): 
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
               # check if user can do this
               current = ndb.get_current_user()
               if current.has_permission('log_message', entity):
                      entity.new_action('log_message', message=values.get('message'), note=values.get('note'))
                      entity.record_action()
                      response.status(entity)
               else:
                   return response.not_authorized()
            else:
                response.not_found()
                
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
               
        return response

# done! - sudo kontrolisan model
class SupportRequest(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 24
    
    # ancestor User
    # ako uopste bude vidljivo useru onda mozemo razmatrati indexing
    # ako hocemo da dozvolimo sva sortiranja, i dodatni filter po state-u uz sortiranje, onda nam trebaju slecedi indexi
    # composite index:
    # ancestor:yes - updated:desc; ancestor:yes - created:desc;
    # ancestor:yes - state,updated:desc; ancestor:yes - state,created:desc
    reference = ndb.SuperStringProperty('1', required=True, indexed=False)
    state = ndb.SuperIntegerProperty('2', required=True)
    updated = ndb.SuperDateTimeProperty('3', auto_now=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True)
 
    
    OBJECT_DEFAULT_STATE = 'new'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za state none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'new' : (1, ),
        'su_opened' : (2, ),
        'su_awaiting_closure' : (3, ),
        'closed' : (4, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'log_message' : 2,
       'sudo' : 3,
       'close' : 4,
    }
    
    OBJECT_TRANSITIONS = {
        'su_open' : {
            'from' : ('new',),
            'to' : ('su_opened',),
         },
        'su_propose_close' : {
           'from' : ('su_opened', ),
           'to'   : ('su_awaiting_closure',),
        },
        'close' : {
           'from' : ('su_opened', 'su_awaiting_closure',),
           'to'   : ('closed',),
        },
    }
    
    @classmethod
    def list(cls, **kwds):
        response = ndb.Response()
        
        response['items'] = cls.query().order(-cls.created).fetch()
        
        return response
  
    @classmethod
    def manage(cls, create, values, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = ndb.get_current_user()
     
            response.process_input(values, cls, only=('reference',))
            
            if response.has_error():
               return response
            
            entity = cls.prepare(create, values, parent=current.key)
            
            if entity is None:
               return response.not_found()
      
            if not entity or not entity.loaded():
               if not current.is_guest:
                   entity.set_state(cls.OBJECT_DEFAULT_STATE)
                   entity.put()
                   entity.new_action('create')
                   entity.record_action()
               else:
                   return response.not_authorized()
               
            response.status(entity)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
        return response 
  
    @classmethod
    def sudo(cls, values, **kwds):
        
        response = ndb.Response()
        
        @ndb.transactional(xg=True) 
        def transaction(): 
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
               # check if user can do this
 
               action = values.get('action')
               
               if not action.startswith('su_'):
                  return response.not_authorized()
               
               current = ndb.get_current_user()
               if current.has_permission(action, entity):
                      state = values.get('state')
                      entity.new_action(action, state=state, message=values.get('message'), note=values.get('note'))
                      entity.put()
                      entity.record_action()
                      response.status(entity)
               else:
                   return response.not_authorized()
            else:
                response.not_found()
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)   
               
        return response
    
    @classmethod
    def log_message(cls, values, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)  
        def transaction(): 
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
               # check if user can do this
               current = ndb.get_current_user()
              
               if entity.get_state not in ('new', 'su_opened'):
                  return response.not_authorized()
              
               if current.has_permission('log_message', entity):
                      entity.new_action('log_message', message=values.get('message'), note=values.get('note'))
                      entity.record_action()
                      response.status(entity)
               else:
                   return response.not_authorized()
            else:
                response.not_found()
                
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
               
        return response
    
    @classmethod
    def close(cls, values, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)
        def transaction(): 
            entity = cls.prepare(False, values, get_only=True)
            if entity and entity.loaded():
               # check if user can do this
               current = ndb.get_current_user()
               """
               su_opened
               su_awaiting_closure
               """
               if entity.get_state not in ('su_opened', 'su_awaiting_closure'):
                  return response.not_authorized()
               
               if current.has_permission('close', entity) or current.key == entity.key.parent():
                      entity.new_action('close', state='closed', message=values.get('message'), note=values.get('note'))
                      entity.put()
                      entity.record_action()
                      response.status(entity)
               else:
                   return response.not_authorized()
            else:
                response.not_found()
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)   
                       
        return response
   