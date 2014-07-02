# -*- coding: utf-8 -*-
'''
Created on Dec 29, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from google.appengine.ext import ndb

class ModelRef(ndb.Model):
  
      name = ndb.StringProperty(required=True)

class Model2(ndb.Model):
  
      ref = ndb.StructuredProperty(ModelRef)
      ref2 = ndb.StructuredProperty(ModelRef, repeated=True)
      
a = Model2(ref=ModelRef(), ref2=[ModelRef()])
a.put()