# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import collections

from app import ndb
from app.core import rule
 
class Context:
  
  def __init__(self, **kwargs):
    
      self.callbacks = []
      self.group = None
      self.entries = collections.OrderedDict()
      
      for k,v in kwargs.items():
          setattr(k, v)
 
      
  def new_callback(self, callback, **kwargs):
     self.callbacks.append((callback, kwargs)) # something like this?
 
  def do_callbacks(self):
      for c in self.callbacks:
          callback, config = c
          
          if config.get('use_task_que'):
             # import taskque
             # tasque.add(...)
             pass
          else:
            # self is passed to the callback, because `self` contains all entries, configurations, and arguments
            callback(self)
          
          # etc
 

################################################################################
# /domain/transaction.py - ako ce se sve transakcije raditi iz perspektive
# company, tj. iz perspektive domain-a onda ima smisla da se nadje u /domain/ folderu
################################################################################

# upiti sa strane usera, ako je na grupi postavljen namespace, ce se resavati odvojenim recordima
# koji ce cuvati kljuceve na recorde a biti vezani ancestor pathom na usera.

# ima uticaj na class-e: Order, BillingOrder, BillingLog, BillingCreditAdjustment
# analytical account entry lines should be treated as expense/revenue lines, where debit is expense, credit is revenue, 
# and no counter entry lines will exist, that is entry will be allowed to remain unbalanced!

# prvo definisati minimalne pasivne modele: category
# definisati im osnovne funkcije i indexe
# potom definisati transakcione modele: group, entry, line
# definisati im osnovne funkcije i indexe
# nakon toga definisati aktivne kompozitne indexe
# pregledati order modele i prepraviti ih da rade sa transakcionim modelima

# App Engine clock times are always expressed in coordinated universal time (UTC). 
# This becomes relevant if you use the current date or time (datetime.datetime.now()) 
# as a value or convert between datetime objects and POSIX timestamps or time tuples. 
# However, no explicit time zone information is stored in the Datastore, 
# so if you are careful you can use these to represent local times in any timezone—if you use the current time or the conversions.
# https://developers.google.com/appengine/docs/python/ndb/properties#Date_and_Time

__SYSTEM_JOURNALS = []

def get_system_journals(action=None):
    # gets registered system journals
    global __SYSTEM_JOURNALS
    
    returns = []
    
    if action:
      for journal in __SYSTEM_JOURNALS:
          if action in journal[0]:
             returns.append(journal[1])
    else:
      returns = [journal[1] for journal in __SYSTEM_JOURNALS]
              
    return returns
  
def register_system_journals(*args):
    global __SYSTEM_JOURNALS
    __SYSTEM_JOURNALS.extend(args)


class Address(ndb.BaseExpando):
    
    # local structured
    name = ndb.SuperStringProperty('1', required=True)
    country = ndb.SuperKeyProperty('2', kind='app.core.misc.Country', required=True, indexed=False)
    city = ndb.SuperStringProperty('3', required=True, indexed=False)
    postal_code = ndb.SuperStringProperty('4', required=True, indexed=False)
    street_address = ndb.SuperStringProperty('5', required=True, indexed=False)
 
    _default_indexed = False
 
    EXPANDO_FIELDS = {
        'region' :  ndb.SuperKeyProperty('8', kind='app.core.misc.CountrySubdivision'),
        'street_address2' : ndb.SuperStringProperty('9'),
        'email' : ndb.SuperStringProperty('10'),
        'telephone' : ndb.SuperStringProperty('11'),
    }
            

class UOM(ndb.BaseExpando):
 
    
    # Local structured
    measurement = ndb.SuperStringProperty('1', required=True)
    name = ndb.SuperStringProperty('2', required=True)
    symbol = ndb.SuperStringProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    rate = ndb.SuperDecimalProperty('4', required=True, indexed=False)# The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12)
    factor = ndb.SuperDecimalProperty('5', required=True, indexed=False)# The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12)
    rounding = ndb.SuperDecimalProperty('6', required=True, indexed=False)# Rounding Precision - digits=(12, 12)
    digits = ndb.SuperIntegerProperty('7', required=True, indexed=False)
    
    EXPANDO_FIELDS = {
        'code' : ndb.SuperStringProperty('8', required=True, indexed=False),# ukljuciti index ako bude trebao za projection query
        'numeric_code' : ndb.SuperStringProperty('9', indexed=False),
        'grouping' : ndb.SuperStringProperty('10', required=True, indexed=False),
        'decimal_separator' : ndb.SuperStringProperty('11', required=True, indexed=False),
        'thousands_separator' : ndb.SuperStringProperty('12', indexed=False),
        'positive_sign_position' : ndb.SuperIntegerProperty('13', required=True, indexed=False),
        'negative_sign_position' : ndb.SuperIntegerProperty('14', required=True, indexed=False),
        'positive_sign' : ndb.SuperStringProperty('15', indexed=False),
        'negative_sign' : ndb.SuperStringProperty('16', indexed=False),
        'positive_currency_symbol_precedes' : ndb.SuperBooleanProperty('17', default=True, indexed=False),
        'negative_currency_symbol_precedes' : ndb.SuperBooleanProperty('18', default=True, indexed=False),
        'positive_separate_by_space' : ndb.SuperBooleanProperty('19', default=True, indexed=False),
        'negative_separate_by_space' : ndb.SuperBooleanProperty('20', default=True, indexed=False),
    }

# done!
class CategoryBalance(ndb.BaseModel):
  # LocalStructuredProperty model
  # ovaj model dozvoljava da se radi feedback trending per month per year
  # mozda bi se mogla povecati granulacija per week, tako da imamo oko 52 instance per year, ali mislim da je to nepotrebno!
  # ovde treba voditi racuna u scenarijima kao sto je napr. promena feedback-a iz negative u positive state,
  # tako da se za taj record uradi negative_feedback_count - 1 i positive_feedback_count + 1
  # najbolje je raditi update jednom dnevno, ne treba vise od toga, tako da bi mozda cron ili task queue bilo resenje za agregaciju
  from_date = ndb.SuperDateTimeProperty('1', auto_now_add=True, required=True)
  to_date = ndb.SuperDateTimeProperty('2', auto_now_add=True, required=True)
  debit = ndb.SuperDecimalProperty('3', required=True, indexed=False)# debit=0 u slucaju da je credit>0, negativne vrednosti su zabranjene
  credit = ndb.SuperDecimalProperty('4', required=True, indexed=False)
  balance = ndb.SuperDecimalProperty('5', required=True, indexed=False)
  uom = ndb.SuperLocalStructuredProperty(UOM, '6', required=True)


class Category(ndb.BaseExpando):
    
  KIND_ID = 47

  # root (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L448
  # http://hg.tryton.org/modules/account/file/933f85b58a36/account.py#l525
  # http://hg.tryton.org/modules/analytic_account/file/d06149e63d8c/account.py#l19
  # composite index: 
  # ancestor:no - active,name;
  # ancestor:no - active,code;
  # ancestor:no - active,company,name; ?
  # ancestor:no - active,company,code; ?
  parent_record = ndb.SuperKeyProperty('1', kind='47', required=True)
  name = ndb.SuperStringProperty('2', required=True)
  code = ndb.SuperStringProperty('3', required=True)
  active = ndb.SuperBooleanProperty('4', default=True)
  company = ndb.SuperKeyProperty('5', kind='app.domain.business.Company', required=True)
  complete_name = ndb.SuperTextProperty('6', required=True)# da je ovo indexable bilo bi idealno za projection query
  # Expando
  # description = ndb.TextProperty('7', required=True)# soft limit 16kb
  # balances = ndb.LocalStructuredProperty(CategoryBalance, '8', repeated=True)# soft limit 120x
  
  EXPANDO_FIELDS = {
     'description' : ndb.SuperTextProperty('7'),
     'balances' : ndb.SuperLocalStructuredProperty(CategoryBalance, '8', repeated=True)  
  }
 
  
class Group(ndb.BaseExpando):
  
  KIND_ID = 48  
 
  # root (namespace Domain)
  # verovatno cemo ostaviti da bude expando za svaki slucaj!
  
class Journal(ndb.BaseModel):
  
  KIND_ID = 49
  
  # root (namespace Domain)
  # key.id() = code.code
  
  name = ndb.SuperStringProperty('1', required=True)
  code = ndb.SuperStringProperty('2', repeated=True)
  company = ndb.SuperKeyProperty('3', kind='app.domain.business.Company', required=True)
  sequence = ndb.SuperIntegerProperty('4', required=True)
  active = ndb.SuperBooleanProperty('5', default=True)
  subscriptions = ndb.SuperStringProperty('6', repeated=True) # verovatno ce ovo biti KeyProperty, repeated, i imace reference na akcije
  
  entry_fields = ndb.SuperPickleProperty('7', required=True, compressed=False)
  line_fields = ndb.SuperPickleProperty('8', required=True, compressed=False)
  plugin_groups = ndb.SuperStringProperty('9', repeated=True)
   
  # sequencing counter....
  
  def run(self, context):
    # proverava da li je context instanca Context klase
    rule.Engine.run(context)
    plugins = Plugin.query(ancestor=self.key, Plugin.active == True, Plugin.subscriptions == context.action).order(Plugin.sequence).fetch()
    for group in self.plugin_groups:
      for plugin in plugins:
        if group == plugin.group:
            plugin.code.run(self, context)
  
  @classmethod
  def get_journals_by_context(cls, context):
       
      query_journals = Journal.query(
                               Journal.active == True, 
                               Journal.company == context.args.get('company'), 
                               Journal.subscriptions == context.action).order(Journal.sequence).fetch()
         
      return [journal.code for journal in query_journals]
  
  
class Entry(ndb.BaseExpando):
    
  KIND_ID = 50
  
  # ancestor Group (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L1279
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l38
  # composite index: 
  # ancestor:no - journal,company,state,date:desc;
  # ancestor:no - journal,company,state,created:desc;
  # ancestor:no - journal,company,state,updated:desc;
  # ancestor:no - journal,company,state,party,date:desc; ?
  # ancestor:no - journal,company,state,party,created:desc; ?
  # ancestor:no - journal,company,state,party,updated:desc; ?
  name = ndb.SuperStringProperty('1', required=True)
  journal = ndb.SuperKeyProperty('2', kind=Journal, required=True)
  company = ndb.SuperKeyProperty('3', kind='app.domain.business.Company', required=True)
  state = ndb.SuperIntegerProperty('4', required=True)
  date = ndb.SuperDateTimeProperty('5', required=True)# updated on specific state or manually
  created = ndb.SuperDateTimeProperty('6', auto_now_add=True, required=True)
  updated = ndb.SuperDateTimeProperty('7', auto_now=True, required=True)
  # Expando
  # 
  # party = ndb.KeyProperty('8') mozda ovaj field vratimo u Model ukoliko query sa expando ne bude zadovoljavao performanse
  # expando indexi se programski ukljucuju ili gase po potrebi
 

  EXPANDO_FIELDS = {
     'party' : ndb.SuperKeyProperty('8'),
  }
  
class Line(ndb.BaseExpando):
  
  KIND_ID = 51  
  
  # ancestor Entry (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_move_line.py#L432
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_analytic_line.py#L29
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l486
  # http://hg.tryton.org/modules/analytic_account/file/d06149e63d8c/line.py#l14
  # uvek se prvo sekvencionisu linije koje imaju debit>0 a onda iza njih slede linije koje imaju credit>0
  # u slucaju da je Entry balanced=True, zbir svih debit vrednosti u linijama mora biti jednak zbiru credit vrednosti
  # composite index: 
  # ancestor:yes - sequence;
  # ancestor:no - journal, company, state, categories, uom, date
  journal = ndb.SuperKeyProperty('1', kind=Journal, required=True)
  company = ndb.SuperKeyProperty('2', kind='app.domain.business.Company', required=True)
  state = ndb.SuperIntegerProperty('3', required=True)
  date = ndb.SuperDateTimeProperty('4', required=True)# updated on specific state or manually
  sequence = ndb.SuperIntegerProperty('5', required=True)
  categories = ndb.SuperKeyProperty('6', kind=Category, repeated=True) # ? mozda staviti samo jednu kategoriju i onda u expando prosirivati
  debit = ndb.SuperDecimalProperty('7', required=True, indexed=False)# debit=0 u slucaju da je credit>0, negativne vrednosti su zabranjene
  credit = ndb.SuperDecimalProperty('8', required=True, indexed=False)# credit=0 u slucaju da je debit>0, negativne vrednosti su zabranjene
  uom = ndb.SuperLocalStructuredProperty(UOM, '9', required=True)
  # Expando
  # neki upiti na Line zahtevaju "join" sa Entry poljima
  # taj problem se mozda moze resiti map-reduce tehnikom ili kopiranjem polja iz Entry-ja u Line-ove
 
 
class Plugin(ndb.BaseModel):
  
  KIND_ID = 52
  
  # ancestor Journal (namespace Domain)
  # composite index: ancestor:yes - sequence
  sequence = ndb.SuperIntegerProperty('1', required=True)
  active = ndb.SuperBooleanProperty('2', default=True)
  subscriptions = ndb.SuperStringProperty('3', repeated=True)
  code = ndb.SuperPickleProperty('4', required=True, compressed=False) # ovde ce se cuvati instanca plugin.py (Neke base klase)


class Engine:
  
  @classmethod
  def run(cls, context):
    
      if isinstance(context, Context):
        
        journals = get_system_journals(context.action)
        journals.extend(Journal.get_journals_by_context(context))
        
        for journal in journals:
            journal.run(context)
                
        
        # `operation` param in Context class determines which callback of the `Engine` class will be called
        call = getattr(cls, context.operation)
        
        result = call(context)
        
        context.do_callbacks()
        
        return result
    
  @classmethod
  @ndb.transactional(xg=True)
  def transaction(cls, context):
    group = context.group
    if not group:
       group = Group()
       group.put()
    
    group_key = group.key # - put main key
    for journal_code, entry in context.entries.items():
        entry.set_key(parent=group_key) # parent key for entry
        entry_key = entry.put()
        
        """
         notice the `_` before `lines` that is because 
         if you set it without underscore it will be considered as new property in expando
         so all operations should use the following paradigm:
         entry._lines = []
         entry._lines.append(Line(...))
         etc..
        """
        for line in entry._lines:
            line.journal = entry.journal
            line.company = entry.company
            line.state = entry.state
            line.date = entry.date
            line.set_key(parent=entry_key) # parent key for line
            line.put()
             
    return context
            
  