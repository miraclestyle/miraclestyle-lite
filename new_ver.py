# ima uticaj na class-e: Order, BillingOrder, BillingLog, BillingCreditAdjustment
# analytical account entry lines should be treated as expense/revenue lines, where debit is expense, credit is revenue, 
# and no counter entry lines will exist, that is entry will be allowed to remain unbalanced!

class Journal(ndb.Model):
  # root (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L709
  # http://hg.tryton.org/modules/account/file/933f85b58a36/journal.py#l92
  name = ndb.StringProperty('1', required=True)
  code = ndb.StringProperty('2', required=True)
  active = ndb.BooleanProperty('4', default=True)
  type = 
  view = 
  sequence = 
  update_posted = 

class Period(ndb.Model):
  # http://hg.tryton.org/modules/account/file/933f85b58a36/fiscalyear.py
  # http://hg.tryton.org/modules/account/file/933f85b58a36/period.py
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L861
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L957
  name = 

class Category(ndb.Expando):
  # root (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L448
  # http://hg.tryton.org/modules/account/file/933f85b58a36/account.py#l525
  # http://hg.tryton.org/modules/analytic_account/file/d06149e63d8c/account.py#l19
  parent_record = ndb.KeyProperty('1', kind=Account, required=True)
  name = ndb.StringProperty('1', required=True)
  code = ndb.StringProperty('2', required=True)
  active = ndb.BooleanProperty('7', default=True)
  company = ndb.KeyProperty('6', kind=Company, required=True)
  currency = ndb.LocalStructuredProperty(Currency, '3', required=True)
  second_currency = ndb.LocalStructuredProperty(Currency, '3', required=True)
  type = ndb.KeyProperty('4', kind=AccountType, required=True)
  reconcile = 
  deferral = 

class Group(ndb.Model):
  # root (namespace Domain)
  
class Entry(ndb.Expando):
  # ancestor Group (namespace Domain)
  # domain = ndb.KeyProperty('5', kind=Domain, required=True) ??
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account.py#L1279
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l38
  # composite index: 
  # ancestor:no - journal,company,state,updated:desc; ancestor:no - company,state,date:desc
  # ancestor:no - state,updated:desc; ancestor:no - state,date:desc
  # ancestor:yes - state,updated:desc; ancestor:yes - state,order_date:desc
  journal = ndb.KeyProperty('1', kind=Journal, required=True)
  company = ndb.KeyProperty('2', kind=Company, required=True)
  period = ndb.KeyProperty('3', kind=Period, required=True)
  state = ndb.IntegerProperty('4', required=True)
  created = ndb.DateTimeProperty('5', auto_now_add=True, required=True)
  updated = ndb.DateTimeProperty('6', auto_now=True, required=True)
  date = ndb.DateTimeProperty('7', required=True)# updated on specific state or manually
  party = ndb.KeyProperty('2')
  # Expando
  

class Line(ndb.Expando):
  # ancestor Entry (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_move_line.py#L432
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_analytic_line.py#L29
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l486
  # http://hg.tryton.org/modules/analytic_account/file/d06149e63d8c/line.py#l14
  # composite index: ancestor:yes - sequence
  sequence = ndb.IntegerProperty('1', required=True)
  categories = ndb.KeyProperty('2', kind=Category, repeated=True)
  debit = DecimalProperty('3', required=True, indexed=False)
  credit = DecimalProperty('4', required=True, indexed=False)
