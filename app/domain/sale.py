# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.core.misc import Location

class Store(ndb.BaseExpando, ndb.Workflow):
    
    KIND_ID = 44
    
    # root (namespace Domain)
    # composite index: ancestor:no - state,name
    name = ndb.SuperStringProperty('1', required=True)
    logo = ndb.SuperBlobKeyProperty('2', required=True)# blob ce se implementirati na GCS
    updated = ndb.SuperDateTimeProperty('3', auto_now=True, required=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True, required=True)
    state = ndb.SuperIntegerProperty('5', required=True)
    
    _default_indexed = False
 
    #Expando
 
    # company_name = ndb.StringProperty('6', required=True)
    # company_country = ndb.KeyProperty('7', kind=Country, required=True)
    # company_region = ndb.KeyProperty('8', kind=CountrySubdivision, required=True)# ako je potreban string val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje
    # company_region = ndb.StringProperty('9', required=True)# ako je potreban key val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje
    # company_city = ndb.StringProperty('10', required=True)
    # company_postal_code = ndb.StringProperty('11', required=True)
    # company_street_address = ndb.StringProperty('12', required=True)
    # company_street_address2 = ndb.StringProperty('13')
    # company_email = ndb.StringProperty('14')
    # company_telephone = ndb.StringProperty('15')
    #
    # Payment
    # currency = ndb.KeyProperty('16', kind=Currency, required=True)
    # tax_buyer_on ?
    # paypal_email = ndb.StringProperty('17')
    # paypal_shipping ?
    #
    # Analytics 
    # tracking_id = ndb.StringProperty('18')
    #
    # Feedback
    # feedbacks = ndb.LocalStructuredProperty(StoreFeedback, '19', repeated=True)# soft limit 120x
    #
    # Shipping Exclusion Settings
    # Shipping everywhere except at the following locations: location_exclusion = False
    # Shipping only at the following locations: location_exclusion = True
    # location_exclusion = ndb.BooleanProperty('20', default=False)
 
    
    OBJECT_DEFAULT_STATE = 'open'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'open' : (1, ),
        'closed' : (2, ),
        'su_closed' : (3, ), # Ovo je samo ako nam bude trebala kontrola nad DomainStore. 
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'close' : 3,
       'open' : 4,
       'sudo' : 5, # Ovo je samo ako nam bude trebala kontrola nad DomainStore. 
       'log_message' : 6, # Ovo je samo ako nam bude trebala kontrola nad DomainStore. 
    }
    
    OBJECT_TRANSITIONS = {
        'open' : {
            'from' : ('closed',),
            'to' : ('open',),
         },
        'close' : {
           'from' : ('open', ),
           'to'   : ('closed',),
        },
        # Ovo je samo ako nam bude trebala kontrola nad DomainStore. 
        'su_open' : {
            'from' : ('su_closed', 'closed',),
            'to' : ('open',),
         },
         # Ovo je samo ako nam bude trebala kontrola nad DomainStore. 
        'su_close' : {
           'from' : ('open', 'closed',),
           'to'   : ('su_closed',),
        },
    }
     

# done!
class StoreFeedback(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 45
    
    # LocalStructuredProperty model
    # ovaj model dozvoljava da se radi feedback trending per month per year
    # mozda bi se mogla povecati granulacija per week, tako da imamo oko 52 instance per year, ali mislim da je to nepotrebno!
    # ovde treba voditi racuna u scenarijima kao sto je napr. promena feedback-a iz negative u positive state,
    # tako da se za taj record uradi negative_feedback_count - 1 i positive_feedback_count + 1
    # najbolje je raditi update jednom dnevno, ne treba vise od toga, tako da bi mozda cron ili task queue bilo resenje za agregaciju
    month = ndb.SuperIntegerProperty('1', required=True, indexed=False)
    year = ndb.SuperIntegerProperty('2', required=True, indexed=False)
    positive_feedback_count = ndb.SuperIntegerProperty('3', required=True, indexed=False)
    negative_feedback_count = ndb.SuperIntegerProperty('4', required=True, indexed=False)
    neutral_feedback_count = ndb.SuperIntegerProperty('5', required=True, indexed=False)

# done!
class StoreContent(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 46
    
    # ancestor DomainStore (Catalog, for caching) (namespace Domain)
    # composite index: ancestor:yes - sequence
    title = ndb.SuperStringProperty('1', required=True)
    body = ndb.SuperTextProperty('2', required=True)
    sequence = ndb.SuperIntegerProperty('3', required=True)
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
     

# done!
class StoreShippingExclusion(Location, ndb.Workflow):
    
    KIND_ID = 47
    
    # ancestor DomainStore (DomainCatalog, for caching) (namespace Domain)
    # ovde bi se indexi mozda mogli dobro iskoristiti?
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
   

# done!
class Tax(ndb.BaseExpando, ndb.Workflow):
    
    KIND_ID = 48
    
    # root (namespace Domain)
    # composite index: ancestor:no - active,sequence
    name = ndb.SuperStringProperty('1', required=True)
    sequence = ndb.SuperIntegerProperty('2', required=True)
    amount = ndb.SuperStringProperty('3', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: 17.00[%] ili 10.00[c] gde je [c] = currency
    location_exclusion = ndb.SuperBooleanProperty('4', default=False, indexed=False)# applies to all locations except/applies to all locations listed below
    active = ndb.SuperBooleanProperty('5', default=True)
    
    _default_indexed = False
 
    # Expando
    # locations = ndb.LocalStructuredProperty(Location, '6', repeated=True)# soft limit 300x
    # product_categories = ndb.KeyProperty('7', kind=ProductCategory, repeated=True)# soft limit 100x
    # carriers = ndb.KeyProperty('8', kind=DomainCarrier, repeated=True)# soft limit 100x
 
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    

# done!
class Carrier(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 49
    
    # root (namespace Domain)
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L27
    # http://hg.tryton.org/modules/carrier/file/tip/carrier.py#l10
    # composite index: ancestor:no - active,name
    name = ndb.SuperStringProperty('1', required=True)
    active = ndb.SuperBooleanProperty('2', default=True)
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
     

# done!
class CarrierLine(ndb.BaseExpando, ndb.Workflow):
    
    KIND_ID = 50
    
    # ancestor DomainCarrier (namespace Domain)
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L170
    # composite index: ancestor:yes - sequence; ancestor:yes - active,sequence
    name = ndb.SuperStringProperty('1', required=True)
    sequence = ndb.SuperIntegerProperty('2', required=True)
    location_exclusion = ndb.SuperBooleanProperty('3', default=False, indexed=False)
    active = ndb.SuperBooleanProperty('4', default=True)
    
    _default_indexed = False
  
    # Expando
    # locations = ndb.LocalStructuredProperty(Location, '5', repeated=True)# soft limit 300x
    # rules = ndb.LocalStructuredProperty(CarrierLineRule, '6', repeated=True)# soft limit 300x
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
     

# done!
class CarrierLineRule(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 51
    
    # LocalStructuredProperty model
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L226
    # ovde se cuvaju dve vrednosti koje su obicno struktuirane kao formule, ovo je mnogo fleksibilnije nego hardcoded struktura informacija koje se cuva kao sto je bio prethodni slucaj
    condition = ndb.SuperStringProperty('1', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: True ili weight[kg] >= 5 ili volume[m3] = 0.002
    price = ndb.SuperStringProperty('2', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: amount = 35.99 ili amount = weight[kg]*0.28
    # weight - kg; volume - m3; ili sta vec odlucimo, samo je bitno da se podudara sa measurementsima na ProductTemplate/ProductInstance
