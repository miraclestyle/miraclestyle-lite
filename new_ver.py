"""
context: proposed organized structure
context.action.name
context.action.args
context.transaction.group
context.transaction.entries
context.transaction.callbacks
context.log.entities
context.rule.entity
context.user
context.response
"""



class UpdateProductLine(transaction.Plugin):
  
  fields = ndb.SuperPickleProperty('5')
  
  
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
    context.entity = entry
    rule.Engine.run(context)
    
    if not context.entity._rule_action_permissions[context.action]['executable']:
      raise PluginValidationError('action_forbidden')
    
    i = 0
    for line in entry._lines:
      if (hasattr(line, 'catalog_pricetag_reference')
          and hasattr(line, 'product_instance_reference'):
        if context.entity._rule_field_permissions['quantity']['writable']:
          if context.args.get('quantity')[i] <= 0:
            entry._lines.pop(i)
          else:
            line.quantity = uom.format_value(context.args.get('quantity')[i], line.product_uom)
        if context.entity._rule_field_permissions['discount']['writable']:
          line.discount = uom.format_value(context.args.get('discount')[i], uom.UOM(digits=4))
      i += 1
      
      
