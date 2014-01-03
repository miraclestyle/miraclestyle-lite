class Carrier(transaction.Plugin):
  
  name = ndb.SuperStringProperty('5')
  lines = ndb.SuperPickleProperty('6')
  
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
    
    for carrier_line in self.lines:
      self.validate_line(carrier_line, entry)
      
  def validate_line(self, carrier_line, entry):
    
    
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

