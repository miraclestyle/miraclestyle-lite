# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

from app.srv import log, rule, transaction, auth
 
class Context():
  
  def __init__(self, **kwargs):
    
    def gets(k):
        return kwargs.pop(k, {})
    
    self.event = gets('action')
    self.transaction = transaction.Context(**gets('transaction'))
    self.rule = rule.Context(**gets('rule'))
        
    self.log = log.Context()
    self.auth = auth.Context()
    self.response = kwargs.pop('response', ndb.Response())
 
    for k,v in kwargs.items():
        setattr(k, v)