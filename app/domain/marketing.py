# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb
from app.core.misc import Image

class Catalog(ndb.BaseExpando, ndb.Workflow):
    
    KIND_ID = 35
    
    # root (namespace Domain)
    # https://support.google.com/merchants/answer/188494?hl=en&hlrm=en#other
    # composite index: ???
    company = ndb.KeyProperty('1', kind='domain.sale.Company', required=True)
    name = ndb.StringProperty('2', required=True)
    publish = ndb.DateTimeProperty('3', required=True)# today
    discontinue = ndb.DateTimeProperty('4', required=True)# +30 days
    updated = ndb.DateTimeProperty('5', auto_now=True, required=True)
    created = ndb.DateTimeProperty('6', auto_now_add=True, required=True)
    state = ndb.IntegerProperty('7', required=True)
 
    # Expando
    # cover = blobstore.BlobKeyProperty('8', required=True)# blob ce se implementirati na GCS
    # cost = DecimalProperty('9', required=True)
    # Search improvements
    # product count per product category
    # rank coefficient based on store feedback
 
    
    OBJECT_DEFAULT_STATE = 'unpublished'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'unpublished' : (1, ),
        'locked' : (2, ),
        'published' : (3, ),
        'discontinued' : (4, ),
    }
    
    # nedostaju akcije za dupliciranje catalog-a, za clean-up, etc...
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'lock' : 3,
       'publish' : 4,
       'discontinue' : 5,
       'log_message' : 6,
    }
    
    OBJECT_TRANSITIONS = {
        'lock' : {
            'from' : ('unpublished',),
            'to' : ('locked',),
         },
        'publish' : {
           'from' : ('locked', ),
           'to'   : ('published',),
        },
        'discontinue' : {
           'from' : ('locked', 'published', ),
           'to'   : ('discontinued',),
        },
    }
     

# done!
class CatalogImage(Image, ndb.Workflow):
    
    KIND_ID = 36
    
    # ancestor DomainCatalog (namespace Domain)
    # composite index: ancestor:yes - sequence
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    

# done!
class CatalogPricetag(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 34
    
    # ancestor DomainCatalog (namespace Domain)
    product_template = ndb.KeyProperty('1', kind='domain.product.Template', required=True, indexed=False)
    container_image = ndb.BlobKeyProperty('2', required=True, indexed=False)# blob ce se implementirati na GCS
    source_width = ndb.FloatProperty('3', required=True, indexed=False)
    source_height = ndb.FloatProperty('4', required=True, indexed=False)
    source_position_top = ndb.FloatProperty('5', required=True, indexed=False)
    source_position_left = ndb.FloatProperty('6', required=True, indexed=False)
    value = ndb.StringProperty('7', required=True, indexed=False)# $ 19.99 - ovo se handla unutar transakcije kada se radi update na unit_price od ProductTemplate ili ProductInstance
   
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
 

    