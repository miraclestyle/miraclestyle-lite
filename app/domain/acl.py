# -*- coding: utf-8 -*-
'''
Created on Oct 14, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

# acl domain is 90% done.

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
    def list(cls, **kwds):
        
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
    def suspend(cls, **kwds):
        
        response = ndb.Response() 
         
        @ndb.transactional(xg=True)  
        def transaction():
            entity = cls.get_or_prepare(kwds, populate=False, only=False)
            if entity and entity.loaded():
               # check if user can do this
               current = cls.get_current_user()
               if current.has_permission('suspend', entity, namespace=entity.key.urlsafe()):
                      entity.new_action('suspend', state='suspended', message=kwds.get('message'), note=kwds.get('note'))
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
    def activate(cls, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)
        def transaction(): 
            entity = cls.get_or_prepare(kwds, populate=False, only=False)
            if entity and entity.loaded():
               # check if user can do this
               current = cls.get_current_user()
               if current.has_permission('activate', entity, namespace=entity.key.urlsafe()):
                      entity.new_action('activate', state='active', message=kwds.get('message'), note=kwds.get('note'))
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
    
    # Ova akcija suspenduje ili aktivira domenu. Ovde cemo dalje opisati posledice suspenzije
    @classmethod
    def sudo(cls, **kwds):
        
        response = ndb.Response()
        
        @ndb.transactional(xg=True) 
        def transaction(): 
            entity = cls.get_or_prepare(kwds, populate=False, only=False)
            if entity and entity.loaded():
               # check if user can do this
               current = cls.get_current_user()
               if current.has_permission('sudo', entity, namespace=entity.key.urlsafe()):
                      state = kwds.get('state')
                      entity.new_action('sudo', state=state, message=kwds.get('message'), note=kwds.get('note'))
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
    def log_message(cls, **kwds):
        
        response = ndb.Response()
         
        @ndb.transactional(xg=True)  
        def transaction(): 
            entity = cls.get_or_prepare(kwds, populate=False, only=False)
            if entity and entity.loaded():
               # check if user can do this
               current = cls.get_current_user()
               if current.has_permission('log_message', entity, namespace=entity.key.urlsafe()):
                      entity.new_action('log_message', message=kwds.get('message'), note=kwds.get('note'))
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
    def manage(cls, **kwds):
 
        response = ndb.Response()
          
        # this transaction handles domain, role, objectlog, domain user, and user entity groups
        @ndb.transactional(xg=True)
        def transaction():
            
            current = cls.get_current_user()
         
            if current.is_guest:
               return response.not_authorized()
           
            response.validate_input(kwds, cls, only=('name',))
            
            if response.has_error():
               return response
            
            if 'state' in kwds:
               kwds['state'] = cls.resolve_state_code_by_name(kwds['state'])
               
            entity = cls.get_or_prepare(kwds, only=('name',))
        
            if not entity or not entity.loaded(): # if entity is not found or its a new one
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
               perms = ndb.compile_public_permissions(cls, Role, User, marketing.Catalog,
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
               if entity.get_state != 'active':
                  return response.error('domain', 'not_active')
               # entity is updating
               if current.has_permission('update', entity, namespace=entity.key.urlsafe()):
                  entity.put()
                  entity.new_action('update')
                  entity.record_action()
               else:
                  return response.not_authorized()
                  
            response.status(entity)
        
        # we really need to handle transaction errors, webclient needs to handle this, to warn user if the submission failed etc.
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
            
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
    
    # def delete inherits from BaseModel see `ndb.BaseModel.delete()`
    
    @classmethod
    def manage(cls, **kwds):
        
        response = ndb.Response()

        @ndb.transactional(xg=True)
        def transaction():
             
            current = cls.get_current_user()
     
            response.validate_input(kwds, cls, convert=[('domain', ndb.Key)])
          
            if response.has_error():
               return response
           
              
            # this must be domain otherwise it must throw err
            domain = kwds.get('domain').get()
            
            if domain is None:
               return response.not_found()
           
            domain_namespace = domain.key.urlsafe()
            
            entity = cls.get_or_prepare(kwds, namespace=domain_namespace)
             
            if entity and entity.loaded():
               if current.has_permission('update', entity):
                   entity.put()
                   entity.new_action('update')
                   entity.record_action()
               else:
                   return response.not_authorized()
            else:
               if current.has_permission('create', entity, namespace=domain_namespace): 
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
 
    
    # Poziva novog usera u domenu, al čime da ga poziva? po mailu?
    @classmethod
    def invite(cls, **kwds):
   
        response = ndb.Response()
             
        response.validate_input(kwds, cls, skip=('state',), convert=[('domain', ndb.Key)])
 
        if response.has_error():
           return response
            
        name = kwds.get('name') 
        get_roles = kwds.get('roles')
        domain_key = kwds.get('domain')
        user_key = kwds.get('user')
         
        get_roles = ndb.get_multi(get_roles)
                
        @ndb.transactional(xg=True)       
        def transaction():
             
            current = cls.get_current_user()
          
            domain, usr = ndb.get_multi([domain_key, user_key])
             
            if domain and usr:
                
               domain_namespace = domain.key.urlsafe()
                
               if not current.has_permission('invite', domain, namespace=domain_namespace):
                  return response.not_authorized()
              
               if domain.get_state != 'active':
                  return response.error('domain', 'not_active')
                
               roles = []
              
               for role in get_roles:
                   if role.key.namespace() == domain_namespace:
                      roles.append(role.key)
                
                   domain_user_key = ndb.Key(User, str(usr.key.id()), namespace=domain_namespace)
                   domain_user = domain_user_key.get()
                   if domain_user:
                      response.status('already_invited')
                   else:
                      domain_user = User(namespace=domain_namespace, id=str(usr.key.id()), name=name, user=usr.key, roles=roles)
                      domain_user.set_state('invited')
                      domain_user.put()
                      domain_user.new_action('invite')
                      domain_user.record_action()
                      response.status(domain_user)
            else:
                response.not_found()       
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
                      
        return response
           
            
    
    # Uklanja postojeceg usera iz domene
    @classmethod
    def remove(cls, **kwds):
 
        response = ndb.Response()
   
        @ndb.transactional(xg=True) 
        def transaction(): 
            
            current = cls.get_current_user()
            
            response.validate_input(kwds, cls, only=False, convert=[('user', ndb.Key)])
            
            if response.has_error():
               return response
            
            user_key = kwds.get('user')
            domain_key = ndb.Key(urlsafe=user_key.namespace())
        
            domain, usr = ndb.get_multi([domain_key, user_key])
            
            if domain and usr:
                
               if domain.get_state != 'active':
                  return response.error('domain', 'not_active') 
                
               if current.has_permission('remove', usr) or usr.key == current.key:
                  if domain.primary_contact != usr.user:
               
                         far_user = usr.user.get()
            
                         for role in usr.roles:
                             if role in far_user.roles:
                                 far_user.roles.remove(role)
                       
                         usr.new_action('remove', log_object=False)
                         usr.record_action()
                         usr.key.delete()
                         
                         far_user.put()
                         far_user.new_action('update')
                         far_user.record_action()
                         response.status(usr)
                         
                  else:
                      return response.error('user', 'is_primary_contact')
               else:
                  return response.not_authorized()
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)  
           
        return response
        
    
    # Prihvata poziv novog usera u domenu
    @classmethod
    def accept(cls, **kwds):
     
        response = ndb.Response()
   
        @ndb.transactional(xg=True)
        def transaction():
            
            current = cls.get_current_user()
            
            response.validate_input(kwds, cls, only=False, convert=[('user', ndb.Key)])
            
            if response.has_error():
               return response
            
            user_key = kwds.get('user')
            domain_key = ndb.Key(urlsafe=user_key.namespace())
            
            usr, domain = ndb.get_multi([user_key, domain_key])
            
            if domain and usr:
                
               if domain.get_state != 'active':
                  return response.error('domain', 'not_active') 
              
               if usr.get_state == 'accepted':
                  return response.error('user', 'already_accepted')
              
               if current.key == usr.user:
                      usr.new_action('accept', state='accepted', log_object=False)
                      usr.put()
                      usr.record_action()
                      user = usr.user.get()
                      
                      for role in usr.roles:
                          if role not in usr.roles:
                             user.roles.append(role)
                          
                      user.put()
                      user.new_action('update')
                      user.record_action()
                      response.status(usr)
                      
               else:
                   response.error('user', 'invalid_reciever')
            else:
                response.not_found()
                      
        try:
           transaction()
        except Exception as e:
           response.transaction_error(e)
               
                  
        return response
    
    # Azurira postojeceg usera u domeni
    @classmethod
    def update(cls, **kwds):
 
        response = ndb.Response()
         
        response.validate_input(kwds, cls, only=('roles', 'name'), convert=[('user', ndb.Key)])
            
        if response.has_error():
           return response
        
        _new_roles = ndb.get_multi(kwds.get('roles'))
        
        @ndb.transactional(xg=True)
        def transaction():
                
            current = cls.get_current_user()
          
            domain_user_key = kwds.get('user')
             
            if domain_user_key:
                   domain_user, domain = ndb.get_multi([domain_user_key, ndb.Key(urlsafe=domain_user_key.namespace())])
                   if domain_user and domain:
                      if current.has_permission('update', domain_user):
                         domain_user.name = kwds.get('name')
                         old_roles = domain_user.roles
                         
                         new_roles = []
                         
                         for new in _new_roles:
                             if new.key.namespace() == domain.key.urlsafe():
                                new_roles.append(new.key)
                                
                         user = domain_user.user.get()       
                         for old in old_roles:
                             if old in user.roles:
                                user.roles.remove(old)
                         
                         domain_user.roles = []
                         for new in new_roles:
                             if new not in user.roles:
                                user.roles.append(new)
                                
                             if new not in domain_user.roles:   
                                domain_user.roles.append(new)
                             
                         user.put()
                         user.new_action('update')
                         user.record_action()
                         
                         domain_user.put()
                         domain_user.new_action('update')
                         domain_user.record_action()
                         
                         response.status(domain_user)
           
        try:
            transaction()
        except Exception as e:
            response.transaction_error(e)
               
        return response          
 
        