class Field:
  
  def __init__(self, name, value):
    
    self.name = name
    self.value = value
    

class EntryFieldAutoUpdate(transaction.Plugin):
  
  fields = ndb.SuperPickleProperty('5')
  
  
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
    context.entity = entry
    rule.Engine.run(context)
    
    if not context.entity._rule_action_permissions[context.action]['executable']:
      raise PluginValidationError('action_forbidden')
    
    for field in self.fields:
      if field.name not in ['name', 'company', 'journal', 'created', 'updated']:
        if context.entity._rule_field_permissions[field.name]['writable']:
          setattr(entry, field.name, field.value)
        else:
          raise PluginValidationError('field_not_writable')
          
        

class CarrierLine:
  
  def __init__(self, name, exclusion=False, active=True, locations=None, rules=None):
    self.name = name
    self.exclusion = exclusion
    self.active = active
    self.locations = locations
    self.rules = rules
  
class CarrierLineRule:
  
  def __init__(self, condition, price):
    self.condition = condition
    self.price = price


class Carrier(transaction.Plugin):
  
  name = ndb.SuperStringProperty('5')
  lines = ndb.SuperPickleProperty('6')
  
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
    
    for carrier_line in self.lines:
      self.validate_line(carrier_line, entry)
      
    
  def validate_line(self, carrier_line, entry):
 
    address_key = '%s_address' % self.address_type
    address = getattr(entry, address_key) 
    
    # Shipping everywhere except at the following locations
    if not (carrier_line.exclusion):
      allowed = True
      for loc in carrier_line.locations:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = False
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = False
            break
        elif not (loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
            allowed = False
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
            allowed = False
            break
    # Shipping only at the following locations
    else:
      allowed = False
      for loc in self.locations:
        if not (loc.region and loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country):
            allowed = True
            break
        elif not (loc.postal_code_from and loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region):
            allowed = True
            break
        elif not (loc.postal_code_to):
          if (address.country == loc.country and address.region == loc.region and address.postal_code == loc.postal_code_from):
            allowed = True
            break
        else:
          if (address.country == loc.country and address.region == loc.region and (address.postal_code >= loc.postal_code_from and address.postal_code <= loc.postal_code_to)):
            allowed = True
            break


    if (allowed):
      weight = uom.format_value('0')
      volume = uom.format_value('0')
      price = entry.amount_total
      for line in entry._lines:
        weight += uom.convert_value(line._product_weight, line._product_weight_uom, x)
        volume += uom.convert_value(line.product_volume, line._product_volume_uom, x)
      
      for rule in carrier_line.rules:
        total_weight = uom.convert_value(weight, x, rule.weight_uom)
        total_volume = uom.convert_value(volume, x, rule.volume_uom)
        total_price = uom.convert_value(price, entry.currency, rule.currecy_uom)
        
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
    
    
      


  