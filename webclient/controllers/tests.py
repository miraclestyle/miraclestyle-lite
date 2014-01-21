# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient.route import register
from webclient.handler import Angular, Handler
 
from app import ndb
from app.srv import auth, rule

class Submitter(Angular):
  
    def respond(self):
        
        if self.request.get('make'):
          for i in range(1,6):
              email = 'a%s@gmail.com' % i
              auth.User(id='test_%s' % i, emails=[email],state='active',identities=[auth.Identity(id='foo_%s', identity='11-%s' % i, primary=True, email=email)]).put()
       
        if self.request.get('invite'):
           domain = ndb.Key(urlsafe='agpkZXZ-YnViZWZkcg4LEgE2GICAgICAgMAJDA').get()
            
           for i in range(1, 6):
               infodata = {'name' : 'test_%s' % i, 'roles' : ['agpkZXZ-YnViZWZkcg8LEgI1NhiAgICAgICACgyiASZhZ3BrWlhaLVluVmlaV1prY2c0TEVnRTJHSUNBZ0lDQWdNQUpEQQ'], 'domain' : domain.key.urlsafe(), 'user' : auth.User.build_key('test_%s' % i).urlsafe()}
               print infodata
               print rule.DomainUser.invite(infodata).response
               
        return self.render('submitter.html')

class Welcome(Angular):
    
    def respond(self):
        return {'user' : auth.User.current_user()}
 
class Endpoint(Angular):
    
    def respond(self):
        
        model_path = self.request.get('model')
        method = self.request.get('method')
        
        model = ndb.factory(model_path)
        data = self.reqdata.get_combined_params()
      
        del data['method'], data['model']
         
        # cruel way of calling methods, but this is just for testing purposes to avoid creating individual controllers.
        # there is no absolute final decision on how the controllers will behave, except we know they will be dumb.
        return getattr(model, method)(data).response
         
 
register(('/endpoint', Endpoint), ('/', Welcome), ('/submitter', Submitter))