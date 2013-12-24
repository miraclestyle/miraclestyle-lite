# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import datetime

from app.srv import transaction
from app.srv import rule

Entry = transaction.Entry
Journal = transaction.Journal
Context = transaction.Context

class PluginValidationError(Exception):
  pass

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
  
  
class CartInit(Base):
  
  category = 'sys_cart_init'
  
  def run(self, journal, context):
    # ucitaj postojeci entry na kojem ce se raditi write
    catalog_key = context.args.get('catalog')
    user_key = context.user.key
    catalog = catalog_key.get()
    company = catalog.company.get()
    company_key = company.key
    journal_key = journal.get_journal_key(journal.code, namespace=catalog.key.namespace())
 
    entry = Entry.query(Entry.journal == journal_key, 
                        Entry.company == company_key, Entry.state.IN(['cart', 'checkout', 'processing']),
                        Entry.party == user_key
                        ).get()
    # ako entry ne postoji onda ne pravimo novi entry na kojem ce se raditi write
    if not (entry):
      entry = Entry()
      entry.journal = journal_key
      entry.company = company_key
      entry.state = 'cart'
      entry.date = datetime.datetime.today()
      entry.party = user_key
    # proveravamo da li je entry u state-u 'cart'
    
    context.entity = entry
    rule.Engine.run(context)
    
    if not context.entity._rule_action_permissions[context.action]['executable']:
      # ukoliko je entry u drugom state-u od 'cart' satate-a, onda abortirati pravljenje entry-ja
      # taj abortus bi trebala da verovatno da bude neka "error" class-a koju client moze da interpretira useru
      raise PluginValidationError('entry_not_in_cart_state')
    else:
      context.entries[entry.journal.code] = entry
