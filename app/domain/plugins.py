# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
__SYSTEM_PLUGINS = []

def get_system_plugins(action=None, journal_code=None):
    # gets registered system journals
    global __SYSTEM_PLUGINS
    
    returns = []
    
    if action:
      for plugin in __SYSTEM_PLUGINS:
          if action in plugin[1] and journal_code == plugin[0]:
             returns.append(plugin[2])
    else:
      returns = [plugin[2] for plugin in __SYSTEM_PLUGINS]
              
    return returns
  
def register_system_plugins(*args):
    global __SYSTEM_PLUGINS
    __SYSTEM_PLUGINS.extend(args)
    

class Base:
  'Base class for plugins'
  
  category = ''
