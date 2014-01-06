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



class LineFieldUpdate(transaction.Plugin):
  
  fields = ndb.SuperPickleProperty('5')
  
  
  def run(self, journal, context):
    
    entry = context.entries[journal.code]
    context.entity = entry
    rule.Engine.run(context)
    
    if not context.entity._rule_action_permissions[context.action]['executable']:
      raise PluginValidationError('action_forbidden')
    
    for field_name, field_value in context.args.items():
      for line in entry._lines:
        if field_name not in ['journal', 'company', 'state', 'date', 'sequence', 'categories', 'debit', 'credit', 'uom']:
          if context.entity._rule_field_permissions[field_name]['writable']:
            setattr(line, field_name, field_value)
          else:
            raise PluginValidationError('field_not_writable')
