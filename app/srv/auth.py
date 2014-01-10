# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
class Context():
  
  def __init__(self):
    self.user = get_current_user()
    
    
def get_current_user():
    
    from app.core.acl import User
    return User.current_user()