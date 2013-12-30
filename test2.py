# -*- coding: utf-8 -*-
'''
Created on Dec 29, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import webapp2
from app import ndb

class Model(ndb.BaseModel):
  
      name = ndb.SuperStringProperty()

class Expando(ndb.BaseExpando):
  
      name = ndb.SuperStringProperty()
      
class Poly(ndb.BasePoly):
  
      name = ndb.SuperStringProperty()
      
      
class PolyExpando(ndb.BasePolyExpando):
     
      name = ndb.SuperStringProperty()
    

  
class MainHandler(webapp2.RequestHandler):
  
  def get(self):
    
      if self.request.get('delete'):
         ndb.delete_multi( Model.query().fetch(keys_only=True)
                         + Expando.query().fetch(keys_only=True)
                         + Poly.query().fetch(keys_only=True)
                         + PolyExpando.query().fetch(keys_only=True))
         return
      
      if self.request.get('get'):
         self.response.write(Model.query().fetch())
         self.response.write(Expando.query().fetch())
         self.response.write(Poly.query().fetch())
         self.response.write(PolyExpando.query().fetch())
      else:
         self.response.write(Model(id='one', name='Foo').put())
         self.response.write(Expando(id='one', name='Foo').put())
         self.response.write(Poly(id='one', name='Foo').put())
         self.response.write(PolyExpando(id='one', name='Foo').put())
    
      self.response.write('Hello')
 
    
     
app = webapp2.WSGIApplication([
    ('/.*', MainHandler),
], debug=True)