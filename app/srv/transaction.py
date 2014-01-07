# -*- coding: utf-8 -*-
'''
Created on Dec 17, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import collections

from app import ndb
from app.srv import uom
 
class Context:
  
  def __init__(self, **kwargs):
 
      self.group = None
      self.entities = collections.OrderedDict()
      self.callbacks = []
      self.operation = None
 
      
  def new_callback(self, callback, **kwargs):
     self.callbacks.append((callback, kwargs)) # something like this?
 
  def run_callbacks(self):
      for c in self.callbacks:
          callback, config = c
          
          if config.get('use_task_que'):
             # import taskque
             # tasque.add(...)
             pass
          else:
            # self is passed to the callback, because `self` contains all entries, configurations, and arguments
            callback(self)
            
__SYSTEM_JOURNALS = []

def get_system_journals(context):
    # gets registered system journals
    global __SYSTEM_JOURNALS
    
    journals = []
    
    if context.event:
      for journal in __SYSTEM_JOURNALS:
          if context.event.key in journal.subscriptions:
             journals.append(journal)
 
    return journals
  
  
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

# done!
class CategoryBalance(ndb.BaseExpando):
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
  uom = ndb.SuperLocalStructuredProperty(uom.UOM, '6', required=True)


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

  
class Journal(ndb.BaseExpando):
  
  KIND_ID = 49
  
  # root (namespace Domain)
  # key.id() = code.code
  
  name = ndb.SuperStringProperty('1', required=True)
  company = ndb.SuperKeyProperty('3', kind='app.domain.business.Company', required=True)
  sequence = ndb.SuperIntegerProperty('4', required=True)
  active = ndb.SuperBooleanProperty('5', default=True)
  subscriptions = ndb.SuperKeyProperty('6', kind='app.srv.event.Action', repeated=True) # verovatno ce ovo biti KeyProperty, repeated, i imace reference na akcije
  
  entry_fields = ndb.SuperPickleProperty('7', required=True, compressed=False)
  line_fields = ndb.SuperPickleProperty('8', required=True, compressed=False)
  plugin_categories = ndb.SuperStringProperty('9', repeated=True)
   
  # sequencing counter....
  
  def get_key(self, *args, **kwargs):
      if not self.key:
         return self.set_key(*args, **kwargs)
      else:
         return self.key
  
  def get_kind(self):
      return 'j_%s' % self.journal.key.id()
  
  def run(self, context):
    plugins = Plugin.get_local_plugins(self, context)
    for category in self.plugin_categories:
      for plugin in plugins:
        if category == plugin.__class__.__name__:
            plugin.run(self, context)
             
    context.rule.entity = None
  
  @classmethod
  def get_local_journals(cls, context):
       
      journals = cls.query(cls.active == True, 
                           cls.company == context.event.args.get('company'), 
                           cls.subscriptions == context.event.key).order(cls.sequence).fetch()
         
      return journals
     
class Group(ndb.BaseExpando):
  
  KIND_ID = 48  
 
  # root (namespace Domain)
  # verovatno cemo ostaviti da bude expando za svaki slucaj!
  
  
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
  state = ndb.SuperStringProperty('4', required=True)
  date = ndb.SuperDateTimeProperty('5', required=True)# updated on specific state or manually
  created = ndb.SuperDateTimeProperty('6', auto_now_add=True, required=True)
  updated = ndb.SuperDateTimeProperty('7', auto_now=True, required=True)
  # Expando
  # 
  # party = ndb.KeyProperty('8') mozda ovaj field vratimo u Model ukoliko query sa expando ne bude zadovoljavao performanse
  # expando indexi se programski ukljucuju ili gase po potrebi
 
  def get_actions(self):
      return {}
  
  def get_kind(self):
      return 'e_%s' % self.journal.key.id()
    
  def get_fields(self):
      fields = super(Entry, self).get_fields()
      journal = self.journal.get()
      fields.extend(journal.entry_fields)
      return fields
          
  
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
  uom = ndb.SuperLocalStructuredProperty(uom.UOM, '9', required=True)
  # Expando
  # neki upiti na Line zahtevaju "join" sa Entry poljima
  # taj problem se mozda moze resiti map-reduce tehnikom ili kopiranjem polja iz Entry-ja u Line-ove
  
  def get_actions(self):
      return {}

  def get_kind(self):
      return 'l_%s' % self.journal.key.id()
  
  def get_fields(self):
      fields = super(Line, self).get_fields()
      journal = self.journal.get()
      fields.extend(journal.line_fields)
      return fields
          

 
class Plugin(ndb.BasePolyExpando):
  
  KIND_ID = 52
  
  # ancestor Journal (namespace Domain)
  # composite index: ancestor:yes - sequence
  sequence = ndb.SuperIntegerProperty('1', required=True)
  active = ndb.SuperBooleanProperty('2', default=True)
  subscriptions = ndb.SuperStringProperty('3', repeated=True)
  company = ndb.SuperKeyProperty('4', kind='app.domain.business.Company', required=True)

  @classmethod
  def get_local_plugins(cls, journal, context):
      plugins = cls.query(ancestor=journal.key, 
                          cls.active == True, 
                          cls.subscriptions == context.key.urlsafe(),
                          cls.company == context.event.args.get('company')
                         ).order(cls.sequence).fetch()
      return plugins

class Engine:
 
  @classmethod
  def run(cls, context):
    
      if isinstance(context, Context):
        
        journals = get_system_journals(context)
        journals.extend(Journal.get_journals_by_context(context))
        
        for journal in journals:
            journal.run(context)
                
        
        # `operation` param in Context class determines which callback of the `Engine` class will be called
        call = getattr(cls, context.transaction.operation)
        
        call(context)
        
        context.run_callbacks()
 
  @classmethod
  @ndb.transactional(xg=True)
  def transaction(cls, context):
    group = context.transaction.group
    if not group:
       group = Group()
       group.put()
    
    group_key = group.key # - put main key
    for journal_code, entry in context.transaction.entities.items():
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
        lines = []
        
        for line in entry._lines:
            line.journal = entry.journal
            line.company = entry.company
            line.state = entry.state
            line.date = entry.date
            line.set_key(parent=entry_key) # parent key for line
            lines.append(line)
        
        ndb.put_multi(lines)
 
            
  