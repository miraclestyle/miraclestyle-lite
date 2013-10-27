# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

class Content(ndb.BaseModel):
    
    KIND_ID = 14
    # root
    # composite index: ancestor:no - category,active,sequence
    updated = ndb.SuperDateTimeProperty('1', auto_now=True, required=True)
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
    
 
# done!
class Image(ndb.BaseModel):
    
    # base class/structured class
    image = ndb.SuperBlobKeyProperty('1', required=True, indexed=False)# blob ce se implementirati na GCS
    content_type = ndb.SuperStringProperty('2', required=True, indexed=False)
    size = ndb.SuperFloatProperty('3', required=True, indexed=False)
    width = ndb.SuperIntegerProperty('4', required=True, indexed=False)
    height = ndb.SuperIntegerProperty('5', required=True, indexed=False)
    sequence = ndb.SuperIntegerProperty('6', required=True)

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
 
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
     

# done! - tryton ima CountrySubdivision za skoro sve zemlje!
class CountrySubdivision(ndb.BaseModel):
    
    KIND_ID = 16
    
    # ancestor Country
    # http://hg.tryton.org/modules/country/file/tip/country.py#l52
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_country.py#L86
    # koliko cemo drilldown u ovoj strukturi zavisi od kasnijih odluka u vezi povezivanja lokativnih informacija sa informacijama ovog modela..
    # composite index: ancestor:yes - name; ancestor:yes - active,name
    
    #  kind='app.core.misc.CountrySubdivision',
    parent_record = ndb.SuperKeyProperty('1', indexed=False)
    
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


# done!
class Location(ndb.BaseExpando):
    
    # base class/structured class
    country = ndb.SuperKeyProperty('1', kind=Country, required=True, indexed=False)
    _default_indexed = False
 
    # Expando
    # region = ndb.KeyProperty('2', kind=CountrySubdivision)# ako je potreban string val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje
    # region = ndb.StringProperty('2')# ako je potreban key val onda se ovo preksace / tryton ima CountrySubdivision za skoro sve zemlje
    # postal_code_from = ndb.StringProperty('3')
    # postal_code_to = ndb.StringProperty('4')
    # city = ndb.StringProperty('5')# ako se javi potreba za ovim ??

# done!
class ProductCategory(ndb.BaseModel):
    
    KIND_ID = 17
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/category.py#l8
    # https://support.google.com/merchants/answer/1705911
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L227
    # composite index: ancestor:no - status,name
    
    #  kind='app.core.misc.ProductCategory',
    parent_record = ndb.SuperKeyProperty('1', indexed=False)
    name = ndb.SuperStringProperty('2', required=True)
    complete_name = ndb.SuperTextProperty('3', required=True)# da je ovo indexable bilo bi idealno za projection query
    status = ndb.SuperIntegerProperty('4', required=True)
  
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    } 

# done!
class ProductUOMCategory(ndb.BaseModel):
    
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
     

# done!
class ProductUOM(ndb.BaseModel):
    
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

# done!
class Currency(ndb.BaseModel):
    
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
     

# done!
# ostaje da se ispita u preprodukciji!!
class Message(ndb.BaseModel):
    
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
    
class BillingCreditAdjustment(ndb.BaseModel):
    
    KIND_ID = 22
    
    # root (namespace Domain)
    # not logged
    adjusted = ndb.SuperDateTimeProperty('2', auto_now_add=True, required=True, indexed=False)
    agent = ndb.SuperKeyProperty('3', kind='app.core.acl.User', required=True, indexed=False)
    amount = ndb.SuperDecimalProperty('4', required=True, indexed=False)
    message = ndb.SuperTextProperty('5')# soft limit 64kb - to determine char count
    note = ndb.SuperTextProperty('6')# soft limit 64kb - to determine char count
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
    }    
     
     
class FeedbackRequest(ndb.Model):
    
    KIND_ID = 23
    
    # ancestor User
    # ako hocemo da dozvolimo sva sortiranja, i dodatni filter po state-u uz sortiranje, onda nam trebaju slecedi indexi
    # composite index:
    # ancestor:yes - updated:desc; ancestor:yes - created:desc;
    # ancestor:yes - state,updated:desc; ancestor:yes - state,created:desc
    reference = ndb.SuperStringProperty('1', required=True, indexed=False)
    state = ndb.SuperIntegerProperty('2', required=True)
    updated = ndb.SuperDateTimeProperty('3', auto_now=True, required=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True, required=True)
 
    
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
  

# done! - sudo kontrolisan model
class SupportRequest(ndb.Model):
    
    KIND_ID = 24
    
    # ancestor User
    # ako uopste bude vidljivo useru onda mozemo razmatrati indexing
    # ako hocemo da dozvolimo sva sortiranja, i dodatni filter po state-u uz sortiranje, onda nam trebaju slecedi indexi
    # composite index:
    # ancestor:yes - updated:desc; ancestor:yes - created:desc;
    # ancestor:yes - state,updated:desc; ancestor:yes - state,created:desc
    reference = ndb.SuperStringProperty('1', required=True, indexed=False)
    state = ndb.SuperIntegerProperty('2', required=True)
    updated = ndb.SuperDateTimeProperty('3', auto_now=True, required=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True, required=True)
 
    
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
   