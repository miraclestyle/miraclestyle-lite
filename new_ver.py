
################################################################################
# /domain/plugins.py
################################################################################


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
