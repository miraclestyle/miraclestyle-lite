# -*- coding: utf-8 -*-
'''
Created on Oct 11, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb, memcache, settings, oauth2
 
class Session(ndb.BaseExpando):
    """A model to store session data. This is required for authenticating users."""
    
    KIND_ID = 3

    #: Save time.
    updated = ndb.SuperDateTimeProperty(auto_now=True)
    #: Session data, pickled.
    data = ndb.PickleProperty()

    @classmethod
    def get_by_sid(cls, sid):
        """Returns a ``Session`` instance by session id.

        :param sid:
            A session id.
        :returns:
            An existing ``Session`` entity.
        """
        data = memcache.get(sid)
        if not data:
            session = ndb.Key(cls, sid).get()
            if session:
                data = session.data
                memcache.set(sid, data)

        return data

    def _put(self):
        """Saves the session and updates the memcache entry."""
        memcache.set(self._key.id(), self.data)
        super(Session, self).put()
 
     
class Identity(ndb.BaseModel):
    
    KIND_ID = 2
    
    # StructuredProperty model
    identity = ndb.StringProperty('1', required=True)# spojen je i provider name sa id-jem
    email = ndb.StringProperty('2', required=True)
    associated = ndb.BooleanProperty('3', default=True)
    primary = ndb.BooleanProperty('4', default=True)
          
          
class User(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 0
    
    identities = ndb.StructuredProperty(Identity, '1', repeated=True)# soft limit 100x
    emails = ndb.SuperStringProperty('2', repeated=True)# soft limit 100x
    state = ndb.SuperIntegerProperty('3', required=True)
    
    _default_indexed = False
  
    EXPANDO_FIELDS = {
      'roles' : ndb.KeyProperty('4', kind='domain.acl.Role', repeated=True)                 
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
    
    def is_anonymous(self):
        """ Checks if the loaded model is an anonymous user. """
        return self.key.id == settings.USER_ANONYMOUS_KEYNAME
 
    @classmethod
    def auth_or_anon(cls, what):
        key_name = getattr(settings, 'USER_%s_KEYNAME' % what.upper())
        if key_name:
           # always query these models from memory if any
           result = cls.get_by_id(key_name, use_memcache=True, use_cache=True)
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
    def current_user_read(cls, key):
        """ Performs `read` for current user """
        if key is None:
           return cls.anonymous_user()
        else:
           usr = key.get() 
  
        return usr
    
    def has_identity(self, identity_id):
        for i in self.identities:
            if i.identity == identity_id:
               return True
        return False
            
    def record_ip(self, ip):
        addr = IPAddress(ip_address=ip, parent=self.key)
        addr.put()
        return addr
    
    def has_permission(self, action, obj):
        return self.permission_check(self, action, obj)
    
    @classmethod
    def permission_check(cls, usr, action, obj):
        action_code = obj.resolve_action_code_by_name(action)
        kind_id = obj._get_kind()
        
        perm = '%s-%s' % (action_code, kind_id)
      
        return False
    
    @classmethod
    def login(cls, **kwds):
        response = ndb.Response()
        login_method = kwds.get('login_method')
        current_user = kwds.get('current_user')
        
        if login_method in settings.LOGIN_METHODS:
           cfg = getattr(settings, '%s_OAUTH2' % login_method.upper())
           cfg['redirect_uri'] = kwds.get('redirect_uri')
           
           code = kwds.get('code')
           error = kwds.get('error')
           cli = oauth2.Client(**cfg)
           
           if error:
              response.error('oauth2_error', 'rejected_account_access')
              return response
           
           if code:
              cli.get_token(code)
          
              if not cli.access_token:
                 response.error('oauth2_error', 'failed_access_token')
                 return response
              
              response['access_token'] = cli.access_token
              
              userinfo = getattr(settings, '%s_OAUTH2_USERINFO' % login_method.upper())
              info = cli.resource_request(url=userinfo)
               
              if info and 'email' in info:
                 auth_id = settings.LOGIN_METHODS[login_method]
                 identity_id = '%s-%s' % (info['id'], auth_id)
                 email = info['email']
                 
                 usr = cls.query(cls.identities.identity == identity_id).get()
                 if not usr:
                    usr = usr = cls.query(cls.emails == email).get()
                 
                 if usr and usr.get_state != 'su_active':
                        response.error('user', 'user_not_active')
                        return response
                    
                 if not usr and current_user:
                    usr = current_user
                        
                 @ndb.transactional
                 def trans(usr): 
                     put = False
                     if usr:
                         if email not in usr.emails:
                            usr.emails.append(email)
                            put = True
                         if not usr.has_identity(identity_id):
                            usr.identities.append(Identity(identity=identity_id, email=email, primary=False))
                            put = True
                            
                         if put:
                            usr.put()
                            usr.new_action('update', agent=usr.key)
                     else:
                        usr = cls.register(email=email, identity=identity_id)
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
        
         usr = cls()
         email = kwds.get('email')
         identity = kwds.get('identity')
     
         usr.emails.append(email)
         usr.identities.append(Identity(identity=identity, email=email, primary=True))
         usr.set_state('su_active')
         usr.put()
         usr.new_action('register', agent=usr.key)
         usr.record_action()
         
         return usr
 
      
class IPAddress(ndb.BaseModel):
    
    KIND_ID = 4
    
    # ancestor User
    # not logged
    # ako budemo radili per user istragu loga onda nam treba composite index: ancestor:yes - logged:desc
    logged = ndb.SuperDateTimeProperty('1', auto_now_add=True, required=True)
    ip_address = ndb.SuperStringProperty('2', required=True, indexed=False)
    
    