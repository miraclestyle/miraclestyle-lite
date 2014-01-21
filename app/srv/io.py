from google.appengine.ext.db import datastore_errors

from app import ndb


class DescriptiveError(Exception):
      # executes an exception in a way that it will have its own meaning instead of just "invalid"
      pass

class Context():
  
  def __init__(self):
    
    from app.srv import auth, log, rule, transaction # circular imports @auth
  
    self.action = None
    self.transaction = transaction.Context()
    self.rule = rule.Context()
  
    self.log = log.Context()
    self.auth = auth.Context()
    self.response = {}
    self.args = {}
    
  def transaction_error(self, e):
     """
     This function needs to be used in fashion:
     
     @ndb.transacitonal
     def transaction():
         user.put()
         ...
         
     try:
        transaction()
     except Exception as e:
        response.transaction_error(e)
        
     It will automatically set if the transaction failed because of google network.
     
     """
     if isinstance(e, datastore_errors.Timeout):
        return self.transaction_timeout()
     if isinstance(e, datastore_errors.TransactionFailedError):
        return self.transaction_failed()
     
     raise
 
  def not_implemented(self):
     return self.error('system', 'not_implemented')

  def transaction_timeout(self):
     # sets error in the response that the transaction that was taking place has timed out
     return self.error('transaction_error', 'timeout')
 
  def transaction_failed(self):
     # sets error in the response that the transaction that was taking place has failed
     return self.error('transaction_error', 'failed')
 
  def required(self, k):
     # sets error that the field is required with name `k`
     return self.error(k, 'required')
     
  def invalid(self, k):
     # sets error that the field is not in proper format with name `k`
     return self.error(k, 'invalid_input')
 
  def status(self, m):
     self.response['status'] = m
     return self
 
  def not_found(self):
     # shorthand for informing the response that the entity, object, thing or other cannot be found with the provided params
     self.error('status', 'not_found')
     return self
 
  def not_authorized(self):
     # shorthand for informing the response that the user is not authorize to perform the operation
     return self.error('user', 'not_authorized')
     
  def not_logged_in(self):
     # shorthand for informing the response that the user needs to login in order to perform the operation
     return self.error('user', 'not_logged_in')
 
  def has_error(self, k=None):
     
     if 'errors' not in self.response:
        return False
     
     if k is None:
        return len(self.response['errors'].keys())
     else:
        return len(self.response['errors'][k])
 
  def error(self, f, m):
     
     if 'errors' not in self.response:
        self.response['errors'] = {}
        
     if f not in self.response['errors']:
         self.response['errors'][f] = list()
         
     self.response['errors'][f].append(m)
     return self
 
  
class Action(ndb.BaseExpando):
  
  _kind = 56
  
  # root (namespace Domain)
  # key.id() = code.code
  
  name = ndb.SuperStringProperty('1', required=True)
  arguments = ndb.SuperPickleProperty('2') # dict
  active = ndb.SuperBooleanProperty('3', default=True)
  service = ndb.SuperStringProperty('4') # transaction, notify, log....
  operation = ndb.SuperStringProperty('5') # read/write
  realtime = ndb.SuperBooleanProperty('6', default=True) # if False, execute in task queue
 
  
  @classmethod
  def get_local_action(cls, action_key):
      action = ndb.Key(urlsafe=action_key).get()
      if action.active:
         return action
      else:
         return None
       
  def process(self, args):
  
    context = Context()
    context.action = self
    context.args = {}
 
    for key, argument in self.arguments.items():
      
      value = args.get(key)
     
      if argument._required:
         if key not in args:
            context.required(key)
            continue 
          
      if key not in args and not argument._required: 
         if argument._default is not None:
            value = argument._default
          
      if argument and hasattr(argument, 'format'):
         if value is None:
            continue # if value is not set at all, always consider it none?
         try:
            value = argument.format(value)
         except (DescriptiveError, ndb.DescriptiveError) as e:
            context.error(key, e)   
         except Exception as e:
            context.invalid(key)
               
      context.args[key] = value
    
    # important convention: if domain is provided externaly, always name it `domain`
    # if `id` is provided, and it's key is a part of domain, it will be retrieved and set
    # building of context.auth.domain sequence:
    
    if not context.has_error():  
      if 'domain' in context.args:
         context.auth.domain = context.args.get('domain').get()
      elif 'key' in context.args:
         key = context.args.get('key')
         if key.namespace():
            context.auth.domain = ndb.Key(urlsafe=key.namespace()).get()
          
    # end context.auth.domain sequence
    
    return context