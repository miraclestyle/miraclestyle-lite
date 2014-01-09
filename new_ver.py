
class AddressRule(transaction.Plugin):
  
  KIND_ID = 54
  
  exclusion = ndb.SuperBooleanProperty('5', default=False)
  address_type = ndb.SuperStringProperty('6')
  locations = ndb.SuperPickleProperty('7')
  
  def run(self, journal, context):
    
    entry = context.transaction.entities[journal.key.id()]
    
    buyer_addresses = []
    valid_addresses = {}
    default_address = None
    address_reference_key = '%s_address_reference' % self.address_type
    address_key = '%s_address' % self.address_type
    addresses_key = '%s_addresses' % self.address_type
    default_address_key = 'default_%s' % self.address_type
    
    input_address_reference = context.event.args.get(address_reference_key)
    entry_address_reference = getattr(entry, address_reference_key, None)
    entry_address = getattr(entry, address_key, None)
    
    buyer_addresses = buyer.Address.query(ancestor=entry.partner).fetch()
    
    for buyer_address in buyer_addresses:
      if self.validate_address(buyer_address):
         valid_addresses[buyer_address.key.urlsafe()] = buyer_address
         if getattr(buyer_address, default_address_key):
             default_address = buyer_address
    
    context.response[addresses_key] = valid_addresses
    
    if not default_address and valid_addresses:
      default_address = valid_addresses[0]
    
    if input_address_reference and input_address_reference in valid_addresses:
       default_address = input_address_reference.get()
    elif entry_address_reference and entry_address_reference in valid_addresses:
       default_address = entry_address_reference.get()
    
    if default_address:
      setattr(entry, address_reference_key, default_address.key)
      setattr(entry, address_key, location.get_location(default_address))
      context.response[default_address_key] = default_address
    else:
      raise PluginValidationError('no_address_found')
     
  
  
