################################################################################
# /core/rule.py
################################################################################

class Engine:
  
  @staticmethod
  def run(cls, context):

  
class FieldPermission():
  
  
  def __init__(self, kind, field, writable=False, visible=False, condition=None):
    
    self.kind = kind
    self.field = field
    self.writable = writable
    self.visible = visible
    self.condition = condition
    
  def run(self, context):
    
    if (self.kind == context.entity._get_kind()) and (self.field in context.entity._properties):
      if (eval(condition)):
        context.entity._field_permissions[self.field] = self
        
################################################################################
# /core/rule.py - end
################################################################################

# instance ove klase su journal
# moze se zvati Master, Matrix, Process
class Master():
  
  def __init__(self, name, code, rule, entry_fields, line_fields, slave_groups):
    self.name = name
    self.code = code
    self.rule = rule
    self.entry_fields = entry_fields
    self.line_fields = line_fields
    self.slave_groups = slave_groups
    self.subscriptions = subscriptions
    # name = string name for description purposes
    # code = short string (example max_size = 32) that servers as Jounral.key.id and is used for key building ndb.Key(...)
    # workflow = instance of Workflow class that contains instances of Transition class and list of states
    # only one workflow is allowed per Journal
    # entry_fields = dictionary of instances of Field class that are allowed on entry
    # example {'field_name': Field(writable=Eval(entry.state == 'cart'), visible=True), 'another_field':}
    # line_fields = dictionary of instances of Field class that are allowed on line
    # example {'field_name': Field(writable=Eval(entry.state == 'cart'), visible=True), 'another_field':}
    # slave_groups = list of strings that defines the order of execution of Slave instances
    # subscriptions = list of strings that name applicable events/actions to which Master is subscribed
    
  def run(company, event):
    # mora postojati konzistentna struktura parametara koje primaju run funkcije
    master_key = ndb.Key('Journal', self.code)
    slaves = Bot.query(ancestor= master_key, Bot.active == True, Bot.subscriptions == self.subscriptions).order(Bot.sequence).fetch()
    for group in self.slave_groups:
      for slave in slaves:
        if (group == slave.group):
          slave.run(self, company, event, context)
    self.workflow.run(company, event, context) # mozda pre kraja proslediti parametre na workflow
    return context.entries # mozda tako nekako....

# instance ove klase su bots
# moze se zvati Slave, Element, Component, Task, Plugin...
class Slave():
  
  def __init__(self):
    # ovo treba da bude base klasa za sve botove
    # guidelines:
    # ova klasa treba da implementira sistem postovanja pravila koja izviru iz mastera
    # pre svega: svojstva entry i line polja u odnosu na workflow (states)
  
  def run(self, journal, context...):
    
    # mora postojati konzistentna struktura parametara koje primaju run funkcije


# ovi modeli ne moraju da budu u transaction.py, ali bi mozda imalo smisla da su sva polja definisana gde su definisani 
# Entry i Line...

# done!
class UOM(ndb.Expando):
    
    # LocalStructuredProperty model
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l28
    # http://hg.tryton.org/modules/product/file/tip/uom.xml#l63 - http://hg.tryton.org/modules/product/file/tip/uom.xml#l312
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L89
    measurement = ndb.StringProperty('1', required=True, indexed=False) # ili mozda category ili tome slicno
    name = ndb.StringProperty('2', required=True, indexed=False)
    symbol = ndb.StringProperty('3', required=True, indexed=False)
    rounding = DecimalProperty('4', required=True, indexed=False)
    digits = ndb.IntegerProperty('5', required=True, indexed=False) 
    _default_indexed = False
    pass
    # Expando

# done!
class Address(ndb.Expando):
    
    # LocalStructuredProperty model
    name = ndb.StringProperty('1', required=True, indexed=False)
    country = ndb.StringProperty('2', required=True, indexed=False)
    country_code = ndb.StringProperty('3', required=True, indexed=False)
    region = ndb.StringProperty('4', required=True, indexed=False)
    region_code = ndb.StringProperty('5', required=True, indexed=False)
    city = ndb.StringProperty('6', required=True, indexed=False)
    postal_code = ndb.StringProperty('7', required=True, indexed=False)
    street_address = ndb.StringProperty('8', required=True, indexed=False)
    _default_indexed = False
    pass
    # Expando
    # street_address2 = ndb.StringProperty('9') # ovo polje verovatno ne treba, s obzirom da je u street_address dozvoljeno 500 karaktera 
    # email = ndb.StringProperty('10')
    # telephone = ndb.StringProperty('11')



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
      new_line.uom = UOM(
                             category=uom_category.name, 
                             name=uom.name, 
                             symbol=uom.symbol, 
                             rounding=uom.rounding, 
                             digits=uom.digits
                             ) # currency uom!!
      new_line.product_uom = UOM(
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
