class Bot:
  
  def __init__(self):
    # uradi query na CompanyLogic
    # pokupi sve picle-ove i onda ih zaloopa
    # i u svakom item-u pokrene run() funkciju, prilikom cega prosledjuje parametre
    

class Location:
  
  def __init__(self, country, region=None, postal_code_from=None, postal_code_to=None, city=None):
    self.country = country
    self.region = region
    self.postal_code_from = postal_code_from
    self.postal_code_to = postal_code_to
    self.city = city


class CartInit:
  
  def run(user_key, catalog_key):
    catalog = catalog_key.get()
    company = catalog.company.get()
    entry = Entry.query(Entry.journal == ndb.Key('Journal', 'order'), 
                        Entry.company == company, Entry.state.IN(['cart', 'checkout', 'processing']),
                        Entry.party == user_key
                        ).get()
    # ako entry postoji onda ne pravimo novi entry
    if (entry):
      # proveravamo da li je entry u state-u 'cart'
      if (entry.state != 'cart'):
        # ukoliko je entry u drugom state-u od 'cart' satate-a, onda abortirati pravljenje entry-ja
        # taj abortus bi trebala da verovatno da bude neka "error" class-a koju client moze da interpretira useru
        return None
      else:
        return entry
    # ako entry ne postoji, instancirati novi entry
    else:
      entry = Entry()
      entry.journal = ndb.Key('Journal', 'order')
      entry.company = company
      entry.state = 'cart'
      entry.date = datetime.datetime.today()
      entry.party = user_key
      return entry

      
class AddressRule:
  
  def __init__(self, exclusion, address_type, locations):
    self.exclusion = exclusion
    self.address_type = address_type
    self.locations = locations
  
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
        return None
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
        return None
  
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
  # taj problem se mozda moze resiti map-reduce tehnikom ili kopitranjem polja iz Entry-ja u Line-ove