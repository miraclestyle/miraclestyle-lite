"""
Logic Fragemntation Introspective

Logic fragemntation aims to improve code reusability and therefore reduce code base.
The main problem of this technique is that code readability is severely impaired!
Second problem arrises since the original architecture convention "Model defines everything" is impossbile to retain!
In current situation there are two posible aproaches (that are most efficient) to deal with fragemntation.


First approach is to define aditional (helper/complementary) independent services that can handle parts of the logic, 
and call them from inside the model functions (the same way, other services, such as rule, log, callback, etc, are hadled).
This approach is easy to implement, and retains current pattern, where models define their own functions (trying to convey "Model defines everything"). 
These hosted functions retain partial logic, and call external services as needed. This affects architecture in such way that 
as fragmentation scales so does the logic decentralization (logic is not placed in one place where it can be easily readed), 
and thus impairs code readability. 


Second aproach is to imeplemnt scalable pipeline model. This approach is more dificult to implement than first one,
and brakes the current pattern by hosting logic outside model definitions, ("Model defines everything except logic"). 
In this scenario logic is tightly contained and controled in one place, outside model definitions space. 
Decupling logic from model definitions, would allow logic reuse from multiple models, and give freedom to logic scaling. 
This affects architecture in such way logic is by default decentralised and fragmentation scaling doesn't affect the pattern however, 
code readability remains impaired.

Second aproach changes:

app/ndb.py would require get_pipes, or simmilar function so that model pipelines can be obtained.
app/srv/io.py changes in get_action, realtime_run and possibly other functions, and implement get_pipeline. 
app/srv/event.py should implement Pipe (or Plugin) class, from transaction.py.
app/pipes (or app/plugins) directory implements individual pipes, and all of the logic from models gets moved here, example:
/app/pipes/read.py (read.py implements Pipe/Plugin class with run() function inside of it).

each model implements '_pipelines' (or '_plugins') dictionary where instantiates pipes, example:

_pipelines = [read.Pipe(kind=6, subscriptions=[6-5]), create.Pipe(kind=6, subscriptions=[6-3])]

each model removes hosted logic functions.

"""

# omoguciti da se u jednoj domeni trasakciona definicija konfigurise sa pluginovima koji mogu raditi notify na http tako da se moze raditi centralizacija
# user inputa sa vise domena na jednu, a pre svega u implementaciji notify engine-a napraviti da pored templeta za slanje ima i template-e za primanje http postova
# ovo je koncept sa transakcionim definicijama, a moglo bi se i resavati na journal definicijama, u zavisnosti kako odlucimo da resavamo cross entry processing.


# few ideas:

# Each class should have _virtual_fields = {}, which will be similar to _expando_fields = {}, i the way
# that _virtual_fields will store ndb properties (referenced by a key/name) that will define features of the value stored
# in the field, and will serve rule engine in eveluating field permissions. 
# _virtual_fields will be retreaved by get_fields() function along with _properties and _expando_fields.
# For the purposes of output class _BaseModel will have _output instead of _virtual_properties list, and this list will be
# used in __todict__() function for selectively building the output for the client.
# The _virtual_fields concept can go perhaps further, where each library (e.g. auth.py) will have each own properties 
# defined that will maybe use async ndb features in custom functions for retreaving values, etc.

# As for the input permissions it's a separate concept taht can be solved similar way the field permissions can be solved
# with io.py using rule engine for prebuilding rules for action input.

# Examples

class _BaseModel(object):
  
  _output = None
  
  def __todict__(self):
    dic = {}
    
    if self.key:
      dic['key'] = self.key.urlsafe()
      dic['id'] = self.key.id()
 
    names = self._output
    
    for name in names:
        value = getattr(self, name, None)
        dic[name] = value
     
    for k, v in dic.items():
      if isinstance(v, Key):
        dic[k] = v.urlsafe()
         
    return dic

class Domain(ndb.BaseExpando):
  
  _kind = 6
  
  _use_memcache = True
  
  name = ndb.SuperStringProperty('1', required=True)
  primary_contact = ndb.SuperKeyProperty('2', kind=User, required=True, indexed=False)
  state = ndb.SuperStringProperty('3', required=True, choices=['active', 'suspended', 'su_suspended'])
  created = ndb.SuperDateTimeProperty('4', required=True, auto_now_add=True)
  updated = ndb.SuperDateTimeProperty('5', required=True, auto_now=True)
  
  _default_indexed = False
  
  _expando_fields = {}
  
  _virtual_fields = {'_primary_email': ndb.SuperStringProperty('6', required=True)}
  


 

# Note: register_system_* can be elminitaed on most modules, by forcing setup engine to create ndb stored instances,
# which will have predefined id parets of the key, and then use _global_role to make sure that those autogenerated
# instances are not editable by users.

# primer funkcije za filtering
# projection query should be enforced whenever posible
def view(cls, context): # filter() i list() su built in funkcije pythona, pa bi mozda bilo bolje da ovu funkciju nazovemo view ili search, ili nesto trece
  entity = cls(state='active', primary_contact=context.auth.user.key)
  context.rule.entity = entity
  rule.Engine.run(context, True)
  if not rule.executable(context):
    raise rule.ActionDenied(context)
  cursor = Cursor(urlsafe=context.input.get('cursor'))
  page_size = context.input.get('page_size')
  filters = context.input.get('filters') # some extraction processing required
  orders = context.input.get('orders') # some extraction processing required
  q = cls.query()
  q = q.filter(filters)
  q = q.order(orders)
  entities, next_cursor, more = q.fetch_page_async(page_size, start_cursor=cursor)
  context.output['entities'] = entities
  context.output['next_cursor'] = next_cursor
  context.output['more'] = more

class PayPalQuery(transaction.Plugin):
  
  def run(self, journal, context):
    ipns = log.Record.query(log.Record.txn_id == context.args['txn_id']).fetch()
    if len(ipns):
      for ipn in ipns:
        if (ipn.payment_status == ccontext.args['payment_status']):
          raise PluginValidationError('duplicate_entry')
      entry = ipns[0].parent_entity
      if not context.args['custom']:
        raise PluginValidationError('invalid_ipn')
      else:
        if not (entry.key.urlsafe() == context.args['custom']):
        raise PluginValidationError('invalid_ipn')
    else:    
      if not context.args['custom']:
        raise PluginValidationError('invalid_ipn')
      else:
        entry = ndb.Key(urlsafe=context.args['custom'])    
    if not entry:
      raise PluginValidationError('invalid_ipn')
    context.transaction.entities[journal.key.id()] = entry
    

class PayPalValidate(transaction.Plugin):
  
  validators = ndb.SuperPickleProperty('5') # [('validate_value', 'receiver_email', 'store@gmail.com'), ('validate_order', 'business', 'paypal_email')]
  
  def run(self, journal, context):
    
    entry = context.transaction.entities[journal.key.id()]
    
    if not (self.validate(entry, context.args)):
      raise PluginValidationError('fraud_ipn')
  
  def validate(entry, ipn):
    mismatches = []
    for validator in self.validators:
      if (validator[0] == 'validate_value'):
        val_1 = getattr(ipn, validator[1], None)
        val_2 = validator[2]
      elif (validator[0] == 'validate_entry'):
        val_1 = getattr(ipn, validator[1], None)
        val_2 = getattr(entry, validator[2], None)
      elif (validator[0] == 'validate_lines'):
        for line in entry._lines:
          attr_1 = validator[1] % str(line.sequence) # ovo bi opet trebalo da se cuva u tuple zbog vece fleksibilnosti code-a
          val_1 = getattr(ipn, attr_1, None)
          val_2 = getattr(line, validator[2], None)
          if (val_1 != None) and (val_2 != None):
            if (val_1 != val_2):
              mismatches.append(validator[1])
              
      if (validator[0] != 'validate_lines') and ((val_1 != None) and (val_2 != None)):
        if (val_1 != val_2):
          mismatches.append(validator[1])
    if (len(mismatches) > 0):
      return False
    return True

# done!
class PayPalTransactionLog(ndb.Expando):
    
    # ancestor Order, BillingOrder
    # not logged
    # ako budemo radili analizu sa pojedinacnih ordera onda nam treba composite index: ancestor:yes - logged:desc
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    txn_id = ndb.StringProperty('2', required=True)
    _default_indexed = False
    pass
    # Expando
    # ipn_message = ndb.TextProperty('3', required=True)
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
    }
    
    @ndb.transactional
    def create():
        # ipn algoritam
        # **Preamble**
        # https://docs.google.com/document/d/1cHymrH2q6pHH19XOtOyLLsznR0tEb0-pkcU5ZGfS1hQ/edit#bookmark=id.fmp7h260u37l
        # na raspolaganju imamo kompletan ipn objekat, ili mozda skup variabla, kako se vec bude to formatiralo.
        # **Duplicate Check**
        if not (ipn.verified):
            # samo verifikovane ipn poruke dolaze u obzir
            return None
        # Kada stigne novi ipn, prvo se radi upit na PayPalTransactionLog i izvlace se svi entiteti koji imaju istu vrednost txn_id kao i primljeni ipn.
        transactions = PayPalTransactionLog.query(PayPalTransactionLog.txn_id == ipn.txn_id).fetch()
        if (transactions):
            # Ukoliko ima rezultata, radi se provera da pristigla ipn poruka nije duplikat nekog od snimljenih entiteta.
            for transaction in transactions:
                # Provera duplikata se vrsi tako sto se uporedjuje payment_status.
                # Za sve upisane transakcije sa istim txn_id, vrednosti payment_status moraju biti razlicite.
                # za sada se uzdamo u payment_status da garantuje uniqueness, ali mozda otkrijemo da to nije dobro resenje...
                if (transaction.payment_status == ipn.payment_status):
                    # Ukoliko je pristigla ipn poruka duplikat onda se tiho odbacuje i algoritam se prekida.
                    return None
        # Ukoliko nema rezultata iz upita na PayPalTransactionLog, ili je pristigla poruka unikatna, onda se prelazi na IPN Algoritam - Fraud Check.
        # **Fraud check**
        # Prvo ipn polje koje se proverava je custom koje bi trebalo da nosi referencu na Order entitet.
        # Ukoliko ovo polje nema vrednosti ili vrednost ne referencira Order entitet,
        # radi se dispatch na notification engine sa detaljima sta se dogodilo (kako bi se obavestilo da je pristigla 
        # validna poruka sa nevazecom referencom na Order), radi se logging i algoritam se prekida.
        if not (ipn.custom):
            return None
        order = ipn.custom.get()
        if not (order):
            return None
        paypal_transaction = PayPalTransactionLog(parent=order.key, txn_id=ipn.txn_id, ipn_message=ipn)
        paypal_transaction_key = paypal_transaction.put()
        # Ukoliko je poredjenje receiver_email sa paypal emailom prodavca kojem je transakcija
        # isla u korist bilo neuspesno, a poredjenje business sa paypal emailom prodavca 
        # kojem je transakcija isla u korist bilo uspesno, onda se radi dispatch na 
        # notification engine sa detaljima sta se dogodilo, radi se logging i prelazi se na IPN Algoritam - Actions.
        if (order_fraud_check):
            if not (match_order(order=order)):
                return None
        # Ukoliko je doslo do fail-ova u poredjenjima, 
        # radi se dispatch na notification engine sa detaljima sta se dogodilo, radi se logging i algoritam se prekida.
        if (billing_fraud_check):
            if not (match_billing(miraclestyle_settings=miraclestyle_settings)):
                return None
        # Ukoliko su sve komparacije prosle onda se prelazi na IPN Algoritam - Actions.
        # **Actions**
        if (order.paypal_payment_status == ipn.payment_status):
            return None
        if (order.paypal_payment_status == 'Pending'):
            if (ipn.payment_status == 'Completed' or ipn.payment_status == 'Denied')):
                update_paypal_payment_status = True
        elif (order.paypal_payment_status == 'Completed'):
            if (ipn.payment_status == 'Refunded' or ipn.payment_status == 'Reversed')):
                update_paypal_payment_status = True
        if (update_paypal_payment_status):
            # ovo se verovatno treba jos doterati..
            if (order.state == 'processing' and ipn.payment_status == 'Completed'):
                order.state = 'completed'
                order.paypal_payment_status = ipn.payment_status
                order_key = order.put()
                object_log = ObjectLog(parent=order_key, agent=kwargs.get('user_key'), action='update_order', state=order.state, log=order)
                object_log.put()
            elif (order.state == 'processing' and ipn.payment_status == 'Denied'): # ovo cemo jos da razmotrimo
                order.state = 'canceled'
                order.paypal_payment_status = ipn.payment_status
                order_key = order.put()
                object_log = ObjectLog(parent=order_key, agent=kwargs.get('user_key'), action='update_order', state=order.state, log=order)
                object_log.put()
            elif (order.state == 'completed'):
                order.paypal_payment_status = ipn.payment_status
                order_key = order.put()
                object_log = ObjectLog(parent=order_key, agent=kwargs.get('user_key'), action='update_order', state=order.state, log=order)
                object_log.put()
        # Feedback kupca se suspenduje/sprecva u slucajevima kada je order: 
        # Canceled_Reversal (treba dalje ispitati), 
        # Denied, 
        # Failed, 
        # Pending, 
        # Refunded (Moguci problem prilikom refunda je taj sto tu prodavac moze umanjiti iznos refunda, 
        # tako da se to treba proveravati i handlati na odgovarajuci nacin...).
        # Feedback od kupca je aktivan u slucajevima kada je order: 
        # Completed, 
        # Reversed (treba dalje ispitati).
        # Ova funkcija jos uvek ne dokumentuje sve detalje iz dokumenta, tako da je dokument supplement ovome..
    
    @ndb.transactional
    def match_order(**kwargs):
        order = kwargs.get('order')
        mismatches = []
        if (order.paypal_email != ipn.receiver_email):
            mismatches.append('receiver_email')
        if (order.paypal_email != ipn.business):
            mismatches.append('business')
        if (order.currency.code != ipn.mc_currency):
            mismatches.append('mc_currency')
        if (order.total_amount != ipn.mc_gross):
            mismatches.append('mc_gross')
        if (order.tax_amount != ipn.tax):
            mismatches.append('tax')
        if (order.reference != ipn.invoice): # order.reference bi mozda mogao da bude user.key.id-order.key.id ili mozda order.key.id ?
            mismatches.append('invoice')
        if (order.shipping_address.country != ipn.address_country):
            mismatches.append('address_country')
        if (order.shipping_address.country_code != ipn.address_country_code):
            mismatches.append('address_country_code')
        if (order.shipping_address.city != ipn.address_city):
            mismatches.append('address_city')
        if (order.shipping_address.name != ipn.address_name):
            mismatches.append('address_name')
        if (order.shipping_address.region != ipn.address_state):
            mismatches.append('address_state')
        if (order.shipping_address.street_address != ipn.address_street): 
            # PayPal spaja vrednosti koje su prosledjene u cart upload procesu (address1 i address2), 
            # tako da u povratu putem IPN-a, polje address_street izgleda ovako address1\r\naddress2. 
            # Primer: u'address_street': [u'1 Edi St\r\nApartment 7'], gde je vrednost Street Address 
            # od kupca bilo "Edi St", a vrednost Street Address (Optional) "Apartment 7".
            mismatches.append('address_street')
        if (order.shipping_address.postal_code != ipn.address_zip):
            mismatches.append('address_zip')
        for line in order.lines:
            if (line.code != ipn['item_number%s' % str(line.sequence])): # ovo nije u order funkcijama implementirano tako da ne znamo da li cemo to imati..
                mismatches.append('item_number%s' % str(line.sequence]))
            if (line.description != ipn['item_name%s' % str(line.sequence])):
                mismatches.append('item_name%s' % str(line.sequence]))
            if (line.quantity != ipn['quantity%s' % str(line.sequence)]):
                mismatches.append('quantity%s' % str(line.sequence]))
            if ((line.subtotal + line.tax_subtotal) != ipn['mc_gross%s' % str(line.sequence])):
                mismatches.append('mc_gross%s' % str(line.sequence]))
        # Ukoliko je doslo do fail-ova u poredjenjima (izuzev receiver_email slucaja), 
        # radi se dispatch na notification engine sa detaljima sta se dogodilo, radi se logging i algoritam se prekida.
        if (len(mismatches) > 1):
            return False
        elif ((len(mismatches) == 1) and (mismatches.count('receiver_email') == 0)):
            return False
        return True
    
    @ndb.transactional
    def match_billing(**kwargs):
        miraclestyle_settings = kwargs.get('miraclestyle_settings')
        mismatches = []
        if (miraclestyle_settings.paypal_email != ipn.receiver_email):
            mismatches.append('receiver_email')
        if (miraclestyle_settings.paypal_email != ipn.business):
            mismatches.append('business')
        if (miraclestyle_settings.currency_code != ipn.mc_currency):
            mismatches.append('mc_currency')
        if (miraclestyle_settings.amounts.count(ipn.mc_gross - ipn.tax) == 0):
            mismatches.append('mc_gross')
        if (len(mismatches) > 0):
            return False
        return True