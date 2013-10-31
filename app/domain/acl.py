# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

class Domain(ndb.BaseExpando, ndb.Workflow):
    
    KIND_ID = 6
    
    # root
    # composite index: ancestor:no - state,name
    name = ndb.SuperStringProperty('1', required=True)
    primary_contact = ndb.SuperKeyProperty('2', kind='app.core.acl.User', required=True, indexed=False)
    updated = ndb.SuperDateTimeProperty('3', auto_now=True, required=True)
    created = ndb.SuperDateTimeProperty('4', auto_now_add=True, required=True)
    state = ndb.SuperIntegerProperty('5', required=True)
    
    _default_indexed = False
  
    OBJECT_DEFAULT_STATE = 'active'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'active' : (1, ),
        'suspended' : (2, ),
        'su_suspended' : (3, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'suspend' : 3,
       'activate' : 4,
       'sudo' : 5,
       'log_message' : 6,
    }
    
    OBJECT_TRANSITIONS = {
        'activate' : {
            'from' : ('suspended',),
            'to' : ('active',),
         },
        'suspend' : {
           'from' : ('active', ),
           'to'   : ('suspended',),
        },
        'su_activate' : {
            'from' : ('su_suspended', 'suspended',),
            'to' : ('active',),
         },
        'su_suspend' : {
           'from' : ('active', 'suspended',),
           'to'   : ('su_suspended',),
        },
    }
    
    @classmethod
    def generate_public_permissions(cls):
        return ('update', 'log_message')
    
    @classmethod
    def generate_admin_permissions(cls):
        return ('suspend', 'activate', 'sudo')
    
    @classmethod
    def list_domains(cls):
        response = ndb.Response()
        
        # test the query and data
        
        items = []
        
        for item in cls.query().fetch():
            namespace = item.key.urlsafe()
            items.append({
                'entity' : item,
                'roles' : Role.query(namespace=namespace).fetch(),
                'users' : User.query(namespace=namespace).fetch(),
            })
        
        response['items'] = items
        
        return response 
    
    @classmethod
    def manage_entity(cls, **kwds):
        
        from app import core
        
        current = core.acl.User.current_user()
        
        response = ndb.Response()
        
        if current.is_guest:
           return response.not_authorized()
       
        if not len(kwds.get('name')):
           return response.error('name', 'required')
        
        # this transaction handles domain, role, objectlog, domain user, and user entity groups
        @ndb.transactional(xg=True)
        def transaction():
            if 'state' in kwds:
               kwds['state'] = cls.resolve_state_code_by_name(kwds['state'])
               
            entity = cls.load_from_values(kwds, only=('name',), get=True)
        
            if not entity or entity.key is None: # if entity is not found or its a new one
               entity.primary_contact = current.key
               entity.set_state('active')
               entity.put()
               entity.new_action('create')
               entity.record_action()
               
               # begin namespace
               namespace = entity.key.urlsafe()
               # lower the module namespace to avoid loop
               from app.domain import marketing, product, sale
               
               # compile all public permissions provided by objects for this domain
               perms = ndb.compile_public_permissions(cls, marketing.Catalog,
                                                      marketing.CatalogImage,
                                                      marketing.CatalogPricetag,
                                                      product.Content,
                                                      product.Instance,
                                                      product.InventoryAdjustment,
                                                      product.InventoryLog,
                                                      product.Template,
                                                      product.Variant,
                                                      sale.Carrier,
                                                      sale.CarrierLine,
                                                      sale.Store,
                                                      sale.StoreContent,
                                                      sale.StoreFeedback,
                                                      sale.StoreShippingExclusion,
                                                      sale.Tax,
                                                      )
                
               # crete role
               role = Role(namespace=namespace, name='Domain Admins', permissions=perms, readonly=True)
               role.put()
               role.new_action('create')
               role.record_action()
               
               # create user
               user = User(namespace=namespace, id=str(current.key.id()), name='Administrator', user=current.key, roles=[role.key,], state=User.resolve_state_code_by_name('accepted'))
               user.put()
               user.new_action('accept')
               user.record_action()
               
               # update current user roles
               current.roles.append(role)
               current.put()
       
               current.new_action('update')
               current.record_action()
              
            else:
               # entity is updating
               if current.has_permission('update', entity, namespace=entity.key.urlsafe()) and entity.get_state != 'active':
                  entity.name = kwds.get('name')
                  entity.put()
                  entity.new_action('update')
                  entity.record_action()
               else:
                  response.not_authorized()
                  
            return entity
        
        response['item'] = transaction()
        
        return response
                
                
class Role(ndb.BaseModel, ndb.Workflow):
    
    # root (namespace Domain)
    # mozda bude trebalo jos indexa u zavistnosti od potreba u UIUX
    # composite index: ancestor:yes - name
    name = ndb.SuperStringProperty('1', required=True)
    permissions = ndb.SuperStringProperty('2', repeated=True, indexed=False)# soft limit 1000x - action-Model - create-Store
    readonly = ndb.SuperBooleanProperty('3', default=True, indexed=False)
    
    KIND_ID = 7
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
     
     
class User(ndb.BaseExpando, ndb.Workflow):
    
    # root (namespace Domain) - id = str(user_key.id())
    # mozda bude trebalo jos indexa u zavistnosti od potreba u UIUX
    # composite index: ancestor:no - name
    name = ndb.SuperStringProperty('1', required=True)# ovo je deskriptiv koji administratoru sluzi kako bi lakse spoznao usera
    user = ndb.SuperKeyProperty('2', kind='app.core.acl.User', required=True)
    roles = ndb.SuperKeyProperty('3', kind='app.domain.acl.Role', repeated=True)# vazno je osigurati da se u ovoj listi ne nadju duplikati rola, jer to onda predstavlja security issue!!
    state = ndb.SuperIntegerProperty('4', required=True)# invited/accepted
    
    _default_indexed = False
 
    KIND_ID = 8
    
    OBJECT_DEFAULT_STATE = 'invited'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'invited' : (1, ),
        'accepted' : (2, ),
    }
    
    OBJECT_ACTIONS = {
       'invite' : 1,
       'remove' : 2,
       'accept' : 3,
       'update' : 4,
    }
    
    OBJECT_TRANSITIONS = {
        'accept' : {
            'from' : ('invited',),
            'to' : ('accepted',),
        },
    } 