################################################################################
# /domain/transaction.py - ako ce se sve transakcije raditi iz perspektive
# company, tj. iz perspektive domain-a onda ima smisla da se nadje u /domain/ folderu
################################################################################


class Journal(ndb.Model):
  
  # root (namespace Domain)
  # key.id() = code.code
  company = ndb.KeyProperty('1', kind=Company, required=True)
  sequence = ndb.IntegerProperty('2', required=True)
  active = ndb.BooleanProperty('3', default=True)
  subscriptions = ndb.StringProperty('4', repeated=True)
  code = ndb.PickleProperty('5', required=True, compressed=False)
  # sequencing counter....

  
class Bot(ndb.Model):
  
  # ancestor Journal (namespace Domain)
  # composite index: ancestor:yes - sequence
  sequence = ndb.IntegerProperty('1', required=True)
  active = ndb.BooleanProperty('2', default=True)
  subscriptions = ndb.StringProperty('3', repeated=True)
  code = ndb.PickleProperty('4', required=True, compressed=False)

  
class Engine:
  
  @staticmethod
  def run(company, event):
    # event bi trebao da je dict ili neki drugi objekat sa argumentima
    # verovatno da treba neki mehanizam da prepozna da li se radi recording ili reading
    # sto se tice entry-ja, iz crud operacija se izbacuje delete,
    # tako da ce imati samo read = ndb.Query() i create/update = write = ndb.put()
    # dole je prikazan neki basic za write operacije.
    entries = []
    # prvo se ucitavaju svi hard-coded journals
    all_journals = defaults.Journals()
    journals = Journal.query(
                             Journal.active == True, 
                             Journal.company == company, 
                             Journal.subscriptions == event.id).order(Journal.sequence).fetch()
    all_journals.extend(journals)
    for journal in all_journals:
      # ovde bi trebala da postoji logika koja iz return vrednosti uzima akcije koje se trebaju naknadno pozvati
      # napr: ako je neki bot upisao callback koji se treba izvrsiti
      # callback se treba inicirati nakon transackije i treba mu se proslediti group_key kao i entries kako bi 
      # callback znao gde da commita nove entrije...
      entries.append(journal.run(company, event))
    
    result = slef.transaction(entries)
    # eventualni callback-ovi se pozivaju i prosledjuje im se result
    return result
    
    
  @ndb.transactional
  def transaction(entries):
    group = Group()
    group_key = group.put()
    for entry in entries:
      #..... entry se procesira, eventualne pripreme pre toga, ako vec nesto treba...
      entry.parent = group_key
      entry_key = entry.put()
      for line in entry.lines:
        line.parent = entry_key
        line.put()
        # object log....
      # object log....
 
  
class Master:
  
  def __init__(self, name, code, workflow, entry_fields, line_fields, bot_groups, subscriptions):
    self.name = name
    self.code = code
    self.workflow = workflow
    self.entry_fields = entry_fields
    self.line_fields = line_fields
    self.bot_groups = bot_groups
    self.subscriptions = subscriptions
    # entry_fields = {'field_name': Field(writable=Eval(entry.state == 'cart'), visible=True), 'another_field':}
    # uradi query na CompanyLogic
    # pokupi sve picle-ove i onda ih zaloopa
    # i u svakom item-u pokrene run() funkciju, prilikom cega prosledjuje parametre
    
  def run(company, event):
    master_key = ndb.Key('Journal', self.code)
    bots = Bot.query(ancestor= master_key, Bot.active == True, Bot.subscriptions == self.subscriptions).order(Bot.sequence).fetch()
    for group in self.bot_groups:
      for bot in bots:
        if (group == bot.group):
          bot.run(self, company, event, context)
    self.workflow.run(company, event, context) # mozda pre kraja proslediti parametre na workflow
    return context.entries # mozda tako nekako....
  
class Entry(ndb.Expando):
  
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
  name = ndb.StringProperty('1', required=True)
  journal = ndb.KeyProperty('2', kind=Journal, required=True)
  company = ndb.KeyProperty('3', kind=Company, required=True)
  state = ndb.IntegerProperty('4', required=True)
  date = ndb.DateTimeProperty('5', required=True)# updated on specific state or manually
  created = ndb.DateTimeProperty('6', auto_now_add=True, required=True)
  updated = ndb.DateTimeProperty('7', auto_now=True, required=True)
  # Expando
  # 
  # party = ndb.KeyProperty('8') mozda ovaj field vratimo u Model ukoliko query sa expando ne bude zadovoljavao performanse
  # expando indexi se programski ukljucuju ili gase po potrebi
  
class Line(ndb.Expando):
  
  # ancestor Entry (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_move_line.py#L432
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_analytic_line.py#L29
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l486
  # http://hg.tryton.org/modules/analytic_account/file/d06149e63d8c/line.py#l14
  # uvek se prvo sekvencionisu linije koje imaju debit>0 a onda iza njih slede linije koje imaju credit>0
  # u slucaju da je Entry balanced=True, zbir svih debit vrednosti u linijama mora biti jednak zbiru credit vrednosti
  # composite index: 
  # ancestor:yes - sequence;
  # ancestor:no - categories ? upiti bi verovatno morali da obuhvataju i polja iz Entry-ja
  sequence = ndb.IntegerProperty('1', required=True)
  categories = ndb.KeyProperty('2', kind=Category, repeated=True) # ? mozda staviti samo jednu kategoriju i onda u expando prosirivati
  debit = DecimalProperty('3', required=True, indexed=False)# debit=0 u slucaju da je credit>0, negativne vrednosti su zabranjene
  credit = DecimalProperty('4', required=True, indexed=False)# credit=0 u slucaju da je debit>0, negativne vrednosti su zabranjene
  uom = # jedinica mere za debit/credit polja... verovatno cemo ovako implementirati
  # Expando
  # neki upiti na Line zahtevaju "join" sa Entry poljima
  # taj problem se mozda moze resiti map-reduce tehnikom ili kopiranjem polja iz Entry-ja u Line-ove
################################################################################
# /domain/transaction.py - end
################################################################################

class Field:
    
    def __init__(self, writable, visible):
      self.writable = writable
      self.visible = visible

    
class Transition:
  
  def __init__(self, name, from_state, to_state, condition):
    self.name = name # ??
    self.from_state = from_state
    self.to_state = to_state
    self.condition = condition
    
  def run(self, journal, entry, state):
    # prvo se radi matching state-ova
    if (entry.state == self.from_state and state == self.to_state):
      # onda se radi validacija uslova
      if (validate_condition(self, journal, entry)):
        entry.state = state
        return entry
      else:
        return 'ABORT'
    else:
      # ovde se radi samo skip bez aborta 
    
  def validate_condition(self, journal, entry):
    # ovde se self.condition mora extract u python formulu koja ce da uporedi neku vrednost iz entry-ja ili
    # entry.line-a sa vrednostima u condition-u
    
    
class Location:
  
  def __init__(self, country, region=None, postal_code_from=None, postal_code_to=None, city=None):
    self.country = country
    self.region = region
    self.postal_code_from = postal_code_from
    self.postal_code_to = postal_code_to
    self.city = city


class CartInit:
  
  def run(user_key, catalog_key):
    # ucitaj postojeci entry na kojem ce se raditi write
    catalog = catalog_key.get()
    company = catalog.company.get()
    entry = Entry.query(Entry.journal == ndb.Key('Journal', 'order'), 
                        Entry.company == company, Entry.state.IN(['cart', 'checkout', 'processing']),
                        Entry.party == user_key
                        ).get()
    # ako entry ne postoji onda ne pravimo novi entry na kojem ce se raditi write
    if not (entry):
      entry = Entry()
      entry.journal = ndb.Key('Journal', 'order')
      entry.company = company
      entry.state = 'cart'
      entry.date = datetime.datetime.today()
      entry.party = user_key
    # proveravamo da li je entry u state-u 'cart'
    if (entry.state != 'cart'):
      # ukoliko je entry u drugom state-u od 'cart' satate-a, onda abortirati pravljenje entry-ja
      # taj abortus bi trebala da verovatno da bude neka "error" class-a koju client moze da interpretira useru
      return 'ABORT'
    else:
      return entry

      
class AddressRule:
  
  def __init__(self, exclusion, address_type, locations, allowed_states=None):
    self.exclusion = exclusion
    self.address_type = address_type
    self.locations = locations
    self.allowed_states = allowed_states
  
  def run(self, entry):
    buyer_addresses = []
    valid_addresses = []
    default_address = None
    p = entry._properties
    if (self.address_type == 'billing'):
      if (p['billing_address_reference']):
        buyer_addresses.append(entry.billing_address_reference.get())
      else:
        buyer_addresses = buyer.Address.query(ancestor=user_key).fetch()
      for buyer_address in buyer_addresses:
        if (validate_address(self, buyer_address)):
          valid_addresses.append(buyer_address)
          if (buyer_address.default_billing):
            default_address = buyer_address
      
      if not (default_address) and (valid_addresses):
        default_address = valid_addresses[0]
      if (default_address):
        if (p['billing_address_reference']):
          entry.billing_address_reference = default_address.key
        if (p['billing_address']):
          address = default_address
          address_country = default_address.country.get()
          address_region = default_address.region.get()
          entry.billing_address = OrderAddress(
                                    name=address.name, 
                                    country=address_country.name, 
                                    country_code=address_country.code, 
                                    region=address_region.name, 
                                    region_code=address_region.code, 
                                    city=address.city, 
                                    postal_code=address.postal_code, 
                                    street_address=address.street_address, 
                                    street_address2=address.street_address2, 
                                    email=address.email, 
                                    telephone=address.telephone
                                    )
        return entry
      else:
        return 'ABORT'
    elif (self.address_type == 'shipping'):
      if (p['shipping_address_reference']):
        buyer_addresses.append(entry.shipping_address_reference.get())
      else:
        buyer_addresses = buyer.Address.query(ancestor=user_key).fetch()
      for buyer_address in buyer_addresses:
        if (validate_address(self, buyer_address)):
          valid_addresses.append(buyer_address)
          if (buyer_address.default_shipping):
            default_address = buyer_address
      if not (default_address) and (valid_addresses):
        default_address = valid_addresses[0]
      if (default_address):
        if (p['shipping_address_reference']):
          entry.shipping_address_reference = default_address.key
        if (p['shipping_address']):
          address = default_address
          address_country = default_address.country.get()
          address_region = default_address.region.get()
          entry.shipping_address = OrderAddress(
                                     name=address.name, 
                                     country=address_country.name, 
                                     country_code=address_country.code, 
                                     region=address_region.name, 
                                     region_code=address_region.code, 
                                     city=address.city, 
                                     postal_code=address.postal_code, 
                                     street_address=address.street_address, 
                                     street_address2=address.street_address2, 
                                     email=address.email, 
                                     telephone=address.telephone
                                     )
        return entry
      else:
        return 'ABORT'
  
  def validate_address(rule, address):
    allowed = False
    # Shipping everywhere except at the following locations
    if not (rule.exclusion):
      allowed = True
      for loc in rule.locations:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = False
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = False
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code_from >= loc.postal_code_from and address.postal_code_to <= loc.postal_code_to)):
            allowed = False
            break
    # Shipping only at the following locations
    else:
      for loc in rule.locations:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = True
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = True
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code_from >= loc.postal_code_from and address.postal_code_to <= loc.postal_code_to)):
            allowed = True
            break
    return allowed


  
class ProductToLine:
    
  def run(self, journal, entry, catalog_pricetag_key, product_template_key, product_instance_key, variant_signature, custom_variants):
    # svaka komponenta mora postovati pravila koja su odredjena u journal-u
    # izmene na postojecim entry.lines ili dodavanje novog entry.line zavise od state-a 
    line_exists = False
    for line in entry.lines:
      if ('catalog_pricetag_reference' in line._properties
          and catalog_pricetag_key == line.catalog_pricetag_reference
          and 'product_instance_reference' in line._properties
          and product_instance_key == line.product_instance_reference):
        line.quantity = line.quantity + 1 # decmail formating required
        line_exists = True
        break
    if not (line_exists):
      product_template = product_template_key.get()
      product_instance = product_instance_key.get()
      product_category = product_template.product_category.get()
      product_category_complete_name = product_category.complete_name
      product_uom = product_template.product_uom.get()
      product_uom_category = product_uom.key.parent().get()
      
      new_line = Line()
      new_line.sequence = entry.lines[-1].sequence + 1
      new_line.categories.append('Sales Account') # ovde ide ndb.Key('Category', 'key')
      new_line.description = product_template.name
      if ('product_instance_count' in product_template._properties and product_template.product_instance_count > 1000):
        new_line.description # += '\n' + variant_signature
      else:
        if (custom_variants):
          new_line.description # += '\n' + variant_signature
      new_line.uom = LineUOM(
                             category=uom_category.name, 
                             name=uom.name, 
                             symbol=uom.symbol, 
                             rounding=uom.rounding, 
                             digits=uom.digits
                             ) # currency uom!!
      new_line.product_uom = LineUOM(
                                     category=product_uom_category.name, 
                                     name=product_uom.name, 
                                     symbol=product_uom.symbol, 
                                     rounding=product_uom.rounding, 
                                     digits=product_uom.digits
                                     )
      new_line.product_category_complete_name = product_category_complete_name
      new_line.product_category_reference = product_template.product_category
      new_line.catalog_pricetag_reference = catalog_pricetag_key
      new_line.product_instance_reference = product_instance_key
      if ('unit_price' in product_instance._properties):
        new_line.unit_price = product_instance.unit_price
      else:
        new_line.unit_price = product_template.unit_price
      new_line.quantity = 1 # decimal formating required
      new_line.discount = 0.0 # decimal formating required
      entry.lines.append(new_line)

      
class ProductSubtotalCalculate:
  
  def run(self, journal, entry):
    for line in entry.lines:
      if ('product_instance_reference' in line._properties):
        line.subtotal = line.unit_price * line.quantity # decimal formating required
        line.discount_subtotal = line.subtotal - (line.subtotal * line.discount) # decimal formating required
        line.debit = 0.0 # decimal formating required
        line.credit = new_line.discount_subtotal # decimal formating required
      
      
      
      
# done!
class OrderLine(ndb.Expando):
    
    
    description = ndb.TextProperty('1', required=True)# soft limit 64kb

    
    
    
    _default_indexed = False
    pass
    # Expando
    # taxes = ndb.LocalStructuredProperty(OrderLineTax, '7', repeated=True)# soft limit 500x
    
    # tax_references = ndb.KeyProperty('12', kind=StoreTax, repeated=True)# soft limit 500x
    
    
    
class Tax:
  
  def __init__(self, name, formula, loacation_exclusion, locations=None, product_categories=None, carrieres=None, address_type=False):
    self.key = # neki auto generated string
    self.name = name
    self.formula = formula
    self.loacation_exclusion = loacation_exclusion
    self.locations = locations
    self.product_categories = product_categories
    self.carreires = carreires
    # if address_type=True tax calcualtion is based on billing address, if False, it is based on shipping address
    self.address_type = address_type
  
  def run (self, entry):
    allowed = validate_tax(self, entry)
    for line in entry.lines:
      if (self.carriers):
        if (self.carriers.count(line.product_instance_reference)):
          if (self.key in line.tax_references):
            if not (allowed):
              line.tax_references.remove(self.key)
          else:
            if (allowed):
              line.tax_references.append(self.key)  
      if (self.product_categories):
        if (self.product_categories.count(line.product_category)):
          if (self.key in line.tax_references):
            if not (allowed):
              line.tax_references.remove(self.key)
          else:
            if (allowed):
              line.tax_references.append(self.key)
  
  def validate_tax(self, entry):
    valid_taxes = []
    allowed = False
    if (self.address_type):
      address = entry.billing_address_reference
    else:
      address = entry.shipping_address_reference
    if (self.locations):
      # Tax everywhere except at the following locations
      if not (self.loacation_exclusion):
        allowed = True
        for loc in self.locations:
          if not (loc.region and loc.postal_code_from and loc.postal_code_to):
            if (address.country == loc.country):
              allowed = False
              break
          elif not (loc.postal_code_from and loc.postal_code_to):
            if (address.country == loc.country and address.region == loc.region):
              allowed = False
              break
          else:
            if (address.country == loc.country and address.region == loc.region and (address.postal_code_from >= loc.postal_code_from and address.postal_code_to <= loc.postal_code_to)):
              allowed = False
              break
      # Tax only at the following locations
      else:
        for loc in self.locations:
          if not (loc.region and loc.postal_code_from and loc.postal_code_to):
            if (address.country == loc.country):
              allowed = True
              break
          elif not (loc.postal_code_from and loc.postal_code_to):
            if (address.country == loc.country and address.region == loc.region):
              allowed = True
              break
          else:
            if (address.country == loc.country and address.region == loc.region and (address.postal_code_from >= loc.postal_code_from and address.postal_code_to <= loc.postal_code_to)):
              allowed = True
              break
    else:
      # u slucaju da taxa nema konfigurisane location exclusions-e onda se odnosi na sve lokacije/onda je to globalna taxa
      allowed = True
    if (allowed):
      # ako je taxa konfigurisana za carriers onda se proverava da li entry ima carrier na kojeg se taxa odnosi
      if (self.carriers):
        allowed = False
        if ((entry.carrier_reference) and (self.carrieres.count(entry.carrier_reference))):
          allowed = True
      # ako je taxa konfigurisana za kategorije proizvoda onda se proverava da li entry ima liniju na koju se taxa odnosi
      elif (self.product_categories):
        allowed = False
        for line in entry.lines:
          if (self.product_categories.count(line.product_category)):
            allowed = True
    return allowed

    
class Entry(ndb.Expando):
  
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
  name = ndb.StringProperty('1', required=True)
  journal = ndb.KeyProperty('2', kind=Journal, required=True)
  company = ndb.KeyProperty('3', kind=Company, required=True)
  state = ndb.IntegerProperty('4', required=True)
  date = ndb.DateTimeProperty('5', required=True)# updated on specific state or manually
  created = ndb.DateTimeProperty('6', auto_now_add=True, required=True)
  updated = ndb.DateTimeProperty('7', auto_now=True, required=True)
  # Expando
  # 
  # party = ndb.KeyProperty('8') mozda ovaj field vratimo u Model ukoliko query sa expando ne bude zadovoljavao performanse
  # expando indexi se programski ukljucuju ili gase po potrebi
  
class Line(ndb.Expando):
  
  # ancestor Entry (namespace Domain)
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_move_line.py#L432
  # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/account/account_analytic_line.py#L29
  # http://hg.tryton.org/modules/account/file/933f85b58a36/move.py#l486
  # http://hg.tryton.org/modules/analytic_account/file/d06149e63d8c/line.py#l14
  # uvek se prvo sekvencionisu linije koje imaju debit>0 a onda iza njih slede linije koje imaju credit>0
  # u slucaju da je Entry balanced=True, zbir svih debit vrednosti u linijama mora biti jednak zbiru credit vrednosti
  # composite index: 
  # ancestor:yes - sequence;
  # ancestor:no - categories ? upiti bi verovatno morali da obuhvataju i polja iz Entry-ja
  sequence = ndb.IntegerProperty('1', required=True)
  categories = ndb.KeyProperty('2', kind=Category, repeated=True) # ? mozda staviti samo jednu kategoriju i onda u expando prosirivati
  debit = DecimalProperty('3', required=True, indexed=False)# debit=0 u slucaju da je credit>0, negativne vrednosti su zabranjene
  credit = DecimalProperty('4', required=True, indexed=False)# credit=0 u slucaju da je debit>0, negativne vrednosti su zabranjene
  uom = # jedinica mere za debit/credit polja... verovatno cemo ovako implementirati
  # Expando
  # neki upiti na Line zahtevaju "join" sa Entry poljima
  # taj problem se mozda moze resiti map-reduce tehnikom ili kopiranjem polja iz Entry-ja u Line-ove