# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json
import inspect

from webclient import handler
  
class BaseTestHandler(handler.Base):
   
  LOAD_CURRENT_USER = False
  
  def before(self):
    self.response.headers['Content-Type'] = 'text/plain;charset=utf8;'
  
  def out_json(self, s):
    self.out(json.dumps(s, indent=2, cls=handler.JSONEncoderHTML))
  
  def out(self, s, a=0):
    sp = "\n"
    self.response.write(sp*a)
    self.response.write(s)
    self.response.write(sp*a)

class Test1(BaseTestHandler):
 
  def respond(self):
    self.out('Hello World')
    
    
for k,o in globals().items():
  if inspect.isclass(o) and issubclass(o, BaseTestHandler):
    handler.register(('/Tests/%s' % o.__name__, o))