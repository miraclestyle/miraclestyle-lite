##################### start ####################
# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import ndb


__SYSTEM_WIDGETS = {}

def get_system_widgets(role_keys):
  global __SYSTEM_WIDGETS
  widgets = []
  for role_key in role_keys:
    widgets.append(__SYSTEM_WIDGETS.get(role_key.urlsafe()))

def register_system_widgets(*widgets):
  global __SYSTEM_WIDGETS
  for widget in widgets:
    __SYSTEM_WIDGETS[widget.role.urlsafe()] = widget

class Widget(ndb.BaseExpando):
  
  _kind = 56
  
  # root (namespace Domain)
  
  name = ndb.SuperStringProperty('1', required=True) # name of the fieldset
  sequence = ndb.SuperIntegerProperty('2', required=True) # global sequence for ordering purposes
  active = ndb.SuperBooleanProperty('3', default=True) # whether this item is active or not
  role = ndb.SuperKeyProperty('4', kind=DomainRole, required=True) # to which role this group is attached
  search_form = ndb.SuperBooleanProperty('5', default=True) # whether this group is search form or set of filter buttons/links
  filters = ndb.SuperLocalStructuredProperty(Filter, '6', repeated=True)
  
  @classmethod
  def get_local_widgets(cls, roles):
    return cls.query(cls.active == True,
                     cls.role IN (roles)).order(cls.sequence).fetch()
  
class Filter(ndb.BaseExpando):
  
  _kind = 56
  
  # Local structured property
  
  name = ndb.SuperStringProperty('1', required=True) # name that is visible on the link
  kind = ndb.SuperStringProperty('3', required=True) # which model (entity kind) this filter affects
  query = ndb.SuperJsonProperty('4', required=True) # query parameters that are passed to search function of the model
  
class Engine:
  
  @classmethod
  def run(cls, context):
    domain_key = context.input.get('domain')
    domain = domain_key.get()
    domain_user_key = rule.DomainUser.build_key(context.auth.user.key_id_str, namespace=domain.key.urlsafe())
    domain_user = domain_user_key.get()
    context.output['menu'] = get_system_widgets(domain_user.roles)
    context.output['menu'].extend(Widget.get_local_widgets(domain_user.roles))

#################################################################### end #####################################


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