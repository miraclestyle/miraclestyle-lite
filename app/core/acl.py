# -*- coding: utf-8 -*-
# -- every comment that begins with "--" (including this one) is to be removed after applied corrections sugested
# -- this file is not PEP 8 compliant http://www.python.org/dev/peps/pep-0008/#indentation
'''
Created on Oct 11, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import datetime
import hashlib

from app.util import random_chars
from app import ndb, settings, oauth2, memcache
 
  
class Session(ndb.BaseModel):
    
      session_id = ndb.SuperStringProperty(indexed=False)# -- add property datastore name
      updated = ndb.SuperDateTimeProperty(auto_now_add=True, indexed=False)# -- add property datastore name
 
     
class Identity(ndb.BaseModel):
    
    KIND_ID = 2
    
    # StructuredProperty model
    identity = ndb.StringProperty('1', required=True)# spojen je i provider name sa id-jem
    email = ndb.StringProperty('2', required=True)
    associated = ndb.BooleanProperty('3', default=True)
    primary = ndb.BooleanProperty('4', default=True)
          
          
class User(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 0
    
    _use_cache = True
    _use_memcache = True
    
    identities = ndb.StructuredProperty(Identity, '1', repeated=True)# soft limit 100x
    emails = ndb.SuperStringProperty('2', repeated=True)# soft limit 100x
    state = ndb.SuperIntegerProperty('3', required=True)
    sessions = ndb.LocalStructuredProperty(Session, '4', repeated=True)
    
    _default_indexed = False
  
    EXPANDO_FIELDS = {
      'roles' : ndb.KeyProperty('4', repeated=True)# -- property name duplicate (line 43)!               
    }
 
    OBJECT_DEFAULT_STATE = 'su_active'
  
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'su_active' : (1, ),
        'su_suspended' : (2, ),
    }
    
    OBJECT_ACTIONS = {
       'register' : 1,
       'update' : 2,
       'login' : 3,
       'logout' : 4,
       'sudo' : 5,
    }
    
    OBJECT_TRANSITIONS = {
        'su_activate' : {
             # from where to where this transition can be accomplished?
            'from' : ('su_suspended',),
            'to' : ('su_active',),
         },
        'su_suspend' : {
           'from' : ('su_active', ),
           'to'   : ('su_suspended',),
        },
    }  
    
    def __json__(self):
        d = super(User, self).__json__()
        
        d['logout_code'] = self.logout_code
        d['is_guest'] = self.is_guest
        
        return d 
    
    @property
    def logout_code(self):
        session = self.current_user_session
        if not session:
           return None
        return hashlib.md5(session.session_id).hexdigest()
 
    
    @property
    def entity_is_authenticated(self):
        """ Checks if the loaded model is an authenticated entity user. """
        return self.key.id() == settings.USER_AUTHENTICATED_KEYNAME
    
    @property
    def entity_is_anonymous(self):
        """ Checks if the loaded model is an anonymous user. """
        return self.key.id() == settings.USER_ANONYMOUS_KEYNAME
    
    @property
    def is_guest(self):
        return self.entity_is_anonymous
 
    @classmethod
    def auth_or_anon(cls, what):
        key_name = getattr(settings, 'USER_%s_KEYNAME' % what.upper())
        if key_name:
           # always query these models from memory if any
           result = cls.get_by_id(key_name)
           if result is None:
              result = cls(id=key_name, state=cls.default_state())
              result.put()
           return result
        return None
    
    @classmethod
    def authenticated_user(cls):
        """ Returns authenticated user entity. """
        return cls.auth_or_anon('AUTHENTICATED')
    
    @classmethod
    def anonymous_user(cls):
        """ Returns anonymous user entity """
        return cls.auth_or_anon('ANONYMOUS')
    
    @classmethod
    def set_current_user(cls, user, session=None):
        memcache.temp_memory_set('_current_user', user)
        memcache.temp_memory_set('_current_user_session', session)
        
    @classmethod
    def current_user(cls):
        return memcache.temp_memory_get('_current_user', cls.anonymous_user())
    
    def generate_authorization_code(self, session):
        return '%s|%s' % (self.key.urlsafe(), session.session_id)
    
    def new_session(self):
        session_id = self.generate_session_id()
        session = Session(session_id=session_id)
        self.sessions.append(session)
        
        return session
  
    def session_by_id(self, sid):
        for s in self.sessions:
            if s.session_id == sid:
               return s
        return None
    
    def generate_session_id(self):
        sids = [s.session_id for s in self.sessions]
        while True:
              random_str = hashlib.md5(random_chars(30)).hexdigest()
              if random_str not in sids:
                  break
        return random_str
    
    @property
    def current_user_session(self):
        return memcache.temp_memory_get('_current_user_session')
    
    @classmethod
    def login_from_authorization_code(cls, auth):
        
        if not auth:
           return
        
        user_key_urlsafe, session_id = auth.split('|')
        
        if not session_id:
           return
        
        user = ndb.Key(urlsafe=user_key_urlsafe).get()
        if user:
           session = user.session_by_id(session_id)
           if session:
              User.set_current_user(user, session)
              
              
    def has_identity(self, identity_id):
        for i in self.identities:
            if i.identity == identity_id:
               return True
        return False
            
    def record_ip(self, ip):
        addr = IPAddress(ip_address=ip, parent=self.key)
        addr.put()
        return addr
    
    def has_permission(self, action, obj, **kwds):
        return self.permission_check(self, action, obj, **kwds)
    
    @classmethod
    def permission_check(cls, usr, action, obj, **kwds):
        
        """ 
           Checks if user can perform certian action on supplied object. 
           :param usr: user on which the permission check will be performed
           :param action: action which user wants to perform
           :param obj: loaded entity of an object
           :param kwds: keyword arguments needed for additional checks.
        """
        if usr.emails:
           for e in usr.emails:
               if e in settings.ROOT_ADMINS:
                  return True
        
        if not kwds.get('anonymous_check') and not usr.entity_is_anonymous:
           yes = cls.permission_check(User.anonymous_user(), action, obj, anonymous_check=1, **kwds)
           if yes:
              return yes
          
        if not kwds.get('authenticated_check') and not usr.entity_is_authenticated:
           yes = cls.permission_check(User.authenticated_user(), action, obj, authenticated_check=1, **kwds)
           if yes:
              return yes
 
        namespace = obj.key.namespace()
         
        permissions = []
        if isinstance(action, basestring):
           action = (action, )
       
        for a in action:
            permissions.append(Role.format_permission(a, obj))
          
        keys = list()
        
        for role in usr.roles:
            if role.namespace() == namespace or role.kind() == Role._get_kind():
               keys.append(role)
               
        roles = ndb.get_multi(keys, use_cache=True)
        perms = dict()
        for role in roles:
            for p in role.permissions:
                perms[p] = p
                
        strict = kwds.pop('strict', False)
        for p in permissions:
            if not strict:
                if p in perms:
                   return True
            else:
                if p not in perms:
                   return False
      
        return strict
     
    def logout(self, **kwds):
        
        response = ndb.Response()
        
        if self.is_guest:
           return response.error('logout', 'already_logged_out')
       
        if not self.logout_code == kwds.get('code'):
           return response.error('logout', 'invalid_code')
        
        @ndb.transactional(xg=True)
        def transaction():
            if self.sessions:
               self.sessions = []
                
            self.new_action('logout', agent=self.key)
            self.record_action()
            
            self.put()
            
            User.set_current_user(User.anonymous_user())
        
        try:    
            transaction()
            response['logout'] = True
        except Exception as e:
            response['logout'] = False
            response.error('logout', 'failed_logout')
            
        return response
    
    
    @classmethod
    def login(cls, **kwds):
        
        response = ndb.Response() 
        current_user = User.current_user()
  
        login_method = kwds.get('login_method')
        
        response['providers'] = settings.LOGIN_METHODS
         
        if login_method in settings.LOGIN_METHODS:
           cfg = getattr(settings, '%s_OAUTH2' % login_method.upper())
           cfg['redirect_uri'] = kwds.get('redirect_uri')
           
           code = kwds.get('code')
           error = kwds.get('error')
           cli = oauth2.Client(**cfg)
           
           if error:
              return response.error('oauth2_error', 'rejected_account_access')
           
           if code:
              cli.get_token(code)
          
              if not cli.access_token:
                 return response.error('oauth2_error', 'failed_access_token')
              
              response['access_token'] = cli.access_token
              
              userinfo = getattr(settings, '%s_OAUTH2_USERINFO' % login_method.upper())
              info = cli.resource_request(url=userinfo)
               
              if info and 'email' in info:
                 auth_id = settings.LOGIN_METHODS[login_method]
                 identity_id = '%s-%s' % (info['id'], auth_id)
                 email = info['email']
                 
                 usr = cls.query(cls.identities.identity == identity_id).get()
                 if not usr:
                    usr = cls.query(cls.emails == email).get()
                 
                 if usr and usr.get_state != 'su_active':
                    return response.error('user', 'user_not_active')
                    
                 if not usr and current_user:
                    usr = current_user
                        
                 @ndb.transactional(xg=True)
                 def trans(usr): 
                     if not usr.is_guest:
                         if email not in usr.emails:
                            usr.emails.append(email)
                     
                         if not usr.has_identity(identity_id):
                            usr.identities.append(Identity(identity=identity_id, email=email, primary=False))
                            
                         session = usr.new_session()
                         response['session'] = session
                         usr.put()
                         usr.new_action('update', agent=usr.key)
                     else:
                        new_user = cls.register(email=email, identity_id=identity_id, do_not_record=True, create_session=True)
                        usr = new_user.get('user')
                        session = new_user.get('session')
                      
                     response['authorization_code'] = usr.generate_authorization_code(session)
                      
                     usr.record_ip(kwds.get('ip'))
                     usr.new_action('login', agent=usr.key)
                     usr.record_action() 
                     
                     return usr         
                     
                 usr = trans(usr)
                 
                 response['logged_in'] = usr
              else:
                 response.error('oauth2_error', 'failed_data_fetch')
           else:
              response['authorization_url'] = cli.get_authorization_code_uri()
        else:
           response.error('login_method', 'invalid_login_method')
           
        return response
    
    @classmethod
    def register(cls, **kwds):
        
         response = ndb.Response()
         
         create_session = kwds.pop('create_session')
         
         usr = cls()
         email = kwds.get('email')
         identity_id = kwds.get('identity_id')
         do_not_record = kwds.pop('do_not_record', False)
     
         usr.emails.append(email)
         usr.identities.append(Identity(identity=identity_id, email=email, primary=True))
         usr.set_state('su_active')
         
         if create_session:
            session = usr.new_session()
            response['session'] = session
         
         usr.put()
         usr.new_action('register', agent=usr.key)
         
         if do_not_record:
            usr.record_action()
         
         response['user'] = usr
         
         return response
 
      
class IPAddress(ndb.BaseModel):
    
    KIND_ID = 4
    
    # ancestor User
    # not logged
    # ako budemo radili per user istragu loga onda nam treba composite index: ancestor:yes - logged:desc
    logged = ndb.SuperDateTimeProperty('1', auto_now_add=True, required=True)
    ip_address = ndb.SuperStringProperty('2', required=True, indexed=False)
 
class Role(ndb.BaseModel):
    
    # root
    # mozda bude trebalo jos indexa u zavistnosti od potreba u UIUX
    # composite index: ancestor:yes - name
    name = ndb.StringProperty('1', required=True)
    permissions = ndb.StringProperty('2', repeated=True, indexed=False)# soft limit 1000x - action-Model - create-Store
    readonly = ndb.BooleanProperty('3', default=True, indexed=False)
    
    KIND_ID = 13
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }  
    
    @staticmethod
    def format_permission(action, obj):
        return '%s-%s' % (obj._get_kind(), obj.resolve_action_code_by_name(action))
    
    @classmethod
    def list_roles(cls):
        return cls.query().fetch()  
  
    @classmethod
    def create(cls, **kwds):
        response = ndb.Response()
        response.required_values(kwds, 'current_user', 'name', 'actions', 'kind_id')
        
        if not response.has_error():
               usr = kwds.get('current_user')
               if usr.has_permission('create', cls):
 
                  perms = []
                  obj = ndb.BaseModel._kind_map.get(kwds.get('kind_id'))
                   
                  for action in kwds.get('actions'):
                      perms.append(Role.format_permission(action, obj))
                   
                  @ndb.transactional 
                  def transaction():
                      create = cls(name=kwds.get('name'), permissions=perms)
                      create.put()
                      return create
                  
                  create = transaction()
                  response['create'] = create
        
        return response
    
    