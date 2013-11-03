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
    def suspend(cls, **kwds):
        response = ndb.Response() 
        entity = cls.load_from_values(kwds, get=True)
        if entity and entity.key:
           # check if user can do this
           current = cls.get_current_user()
           if current.has_permission('suspend', entity, namespace=entity.key.namespace()):
              @ndb.transactional(xg=True)  
              def transaction(): 
                  entity.new_action('suspend', state='suspend', message=kwds.get('message'), note=kwds.get('note'))
                  entity.record_action()
                  response['suspended'] = entity
              try:
                  transaction()
              except Exception as e:
                  response.transaction_error(e)
           else:
               response.not_authorized()
        else:
            response.not_found()
               
        return response


    @classmethod
    def activate(cls, **kwds):
        response = ndb.Response()
        entity = cls.load_from_values(kwds, get=True)
        if entity and entity.key:
           # check if user can do this
           current = cls.get_current_user()
           if current.has_permission('activate', entity, namespace=entity.key.namespace()):
              @ndb.transactional(xg=True)
              def transaction(): 
                  entity.new_action('activate', state='activate', message=kwds.get('message'), note=kwds.get('note'))
                  entity.record_action()
                  response['activate'] = entity
              try:
                  transaction()
              except Exception as e:
                  response.transaction_error(e)
           else:
               response.not_authorized()
        else:
            response.not_found()
               
        return response
    
    # Ova akcija suspenduje ili aktivira domenu. Ovde cemo dalje opisati posledice suspenzije
    @classmethod
    def sudo(cls, **kwds):
        response = ndb.Response()
        entity = cls.load_from_values(kwds, get=True)
        if entity and entity.key:
           # check if user can do this
           current = cls.get_current_user()
           if current.has_permission('sudo', entity, namespace=entity.key.namespace()): 
              @ndb.transactional(xg=True) 
              def transaction(): 
                  entity.new_action('sudo', state=kwds.get('state'), message=kwds.get('message'), note=kwds.get('note'))
                  entity.record_action()
                  response['sudo'] = entity
              try:
                  transaction()
              except Exception as e:
                  response.transaction_error(e)
           else:
               response.not_authorized()
        else:
            response.not_found()
               
        return response
    
    @classmethod
    def log_message(cls, kwds):
        response = ndb.Response()
        entity = cls.load_from_values(kwds, get=True)
        if entity and entity.key:
           # check if user can do this
           current = cls.get_current_user()
           if current.has_permission('log_message', entity, namespace=entity.key.namespace()):
              @ndb.transactional(xg=True)  
              def transaction(): 
                  entity.new_action('log_message', message=kwds.get('message'), note=kwds.get('note'))
                  entity.record_action()
                  response['log_message'] = entity
              try:
                  transaction()
              except Exception as e:
                  response.transaction_error(e)
           else:
               response.not_authorized()
        else:
            response.not_found()
               
        return response
            
    @classmethod
    def manage_entity(cls, **kwds):
        
        current = cls.get_current_user()
        
        response = ndb.Response()
        
        if current.is_guest:
           return response.not_authorized()
       
        if not len(kwds.get('name')):
           return response.required('name')
        
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
        
        # we really need to handle transaction errors, webclient needs to handle this, to warn user if the submission failed etc.
        try:
            response['item'] = transaction()
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
    def invite(cls, domain_key, user_key, role_keys, name, **kwds):
   
        response = ndb.Response()
        
        if not name:
           response.required('name')
           
        if not role_keys:
           response.required('roles')
           
        if response.has_error():
           return response
        
        current = cls.get_current_user()
        domain, usr = ndb.get_multi([ndb.Key(urlsafe=domain_key), ndb.Key(urlsafe=user_key)])
         
        if domain and usr:
            
           if not current.has_permission('invite', domain, namespace=domain.key.namespace()):
              return response.not_authorized()
          
           if domain.get_state != 'active':
              return response.error('domain', 'not_active')
            
           roles = []
           get_roles = ndb.get_multi([ndb.Key(urlsafe=k) for k in role_keys])
           for role in get_roles:
               if role.key.namespace() == domain.key.namespace():
                  roles.append(role.key)
           
           @ndb.transactional(xg=True)       
           def transaction():
               domain_user_key = ndb.Key(namespace=domain.key.namespace(), id=str(usr.key.id()))
               domain_user = domain_user_key.get()
               if domain_user:
                  response.status('already_invited')
               else:
                  domain_user = User(namespace=domain.key.namespace(), id=str(usr.key.id()), name=name, user=usr.key, roles=roles)
                  domain_user.put()
                  domain_user.new_action('invite')
                  domain_user.record_action()
                  response['invited'] = domain_user
           try:
               transaction()
           except Exception as e:
               response.transaction_error(e)
        else:
            response.not_found()       
               
        return response
           
            
    
    # Uklanja postojeceg usera iz domene
    @classmethod
    def remove(cls, domain_key, user_key, **kwds):
        """
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'remove-DomainUser', ili agent koji je referenciran u entitetu (domain_user.user == agent).
        # agent koji je referenciran u domain.primary_contact prop. ne moze biti izbacen iz domene i izgubiti dozvole za upravljanje domenom.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        user = domain_user.user.get()
        for role in domain_user.roles:
            user.roles.remove(role)
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent=agent_key, action='update', state=user.state, log=user)
        object_log.put()
        object_log = ObjectLog(parent=domain_user_key, agent=agent_key, action='remove', state=domain_user.state)
        object_log.put()
        domain_user_key.delete()
        """
        
        response = ndb.Response()
  
        current = cls.get_current_user()
        domain, usr = ndb.get_multi([ndb.Key(urlsafe=domain_key), ndb.Key(urlsafe=user_key)])
        
        if domain and usr:
            
           if domain.get_state != 'active':
              return response.error('domain', 'not_active') 
            
           if current.has_permission('remove', domain, namespace=domain.key.namespace()) or usr.key == current.key:
              if domain.primary_contact != usr.user:
                  
                 @ndb.transactional(xg=True) 
                 def transaction(): 
                     far_user = usr.user.get()
                     for role in usr.roles:
                         far_user.roles.remove(role)
                   
                     usr.new_action('remove', log_object=False)
                     usr.record_action()
                     usr.key.delete()
                     
                     far_user.put()
                     far_user.new_action('update')
                     far_user.record_action()
                     
                 try:
                    transaction()
                    response['removed'] = usr
                 except Exception as e:
                    response.transaction_error(e)
              else:
                  return response.error('user', 'is_primary_contact')
           else:
              return response.not_authorized()
        
    
    # Prihvata poziv novog usera u domenu
    @classmethod
    def accept(cls, user_key, **kwds):
        """
        # ovu akciju moze izvrsiti samo agent koji je referenciran u entitetu (domain_user.user == agent).
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        domain_user.state = 'accepted'
        domain_user_key = domain_user.put()
        object_log = ObjectLog(parent=domain_user_key, agent=agent_key, action='accept', state=domain_user.state)
        object_log.put()
        user = domain_user.user.get()
        for role in domain_user.roles:
            user.roles.append(role)
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent=agent_key, action='update', state=user.state, log=user)
        object_log.put()
        """
        response = ndb.Response()
  
        current = cls.get_current_user()
        user_key = ndb.Key(urlsafe=user_key)
        usr, domain = ndb.get_multi([user_key, ndb.Key(urlsafe=user_key.namespace())])
        
        if domain and usr:
            
           if domain.get_state != 'active':
              return response.error('domain', 'not_active') 
          
           if current.key == usr.user:
              @ndb.transactional(xg=True)
              def transaction(): 
                  usr.new_action('accept', state='accept', log_object=False)
                  usr.record_action()
                  user = usr.user.get()
                  for role in usr.roles:
                      user.roles.append(role)
                      
                  user.put()
                  user.new_action('update')
                  user.record_action()
                  
              try:
                  transaction()
                  response['accept'] = usr
              except Exception as e:
                  response.transaction_error(e)
           else:
               response.error('user', 'invalid_reciever')
                  
        return response
    
    # Azurira postojeceg usera u domeni
    @classmethod
    def update(cls, **kwds):
        """
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainUser'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        old_roles = domain_user.roles
        domain_user.name = var_name
        domain_user.roles = var_roles
        domain_user_key = domain_user.put()
        object_log = ObjectLog(parent=domain_user_key, agent=agent_key, action='update', state=domain_user.state, log=domain_user)
        object_log.put()
        user = domain_user.user.get()
        for role in old_roles:
            user.roles.remove(role)
        for role in domain_user.roles:
            user.roles.append(role)
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent=agent_key, action='update', state=user.state, log=user)
        object_log.put()
        """