# -*- coding: utf-8 -*-
'''
Created on Oct 13, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb


class SelfReference(ndb.BaseModel):
    
      ref = ndb.KeyProperty(kind='SelfReference')
      name = ndb.StringProperty()