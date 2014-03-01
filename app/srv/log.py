# -*- coding: utf-8 -*-
'''
Created on Dec 25, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
from google.appengine.datastore.datastore_query import Cursor

from app import ndb


class Context():
  
  def __init__(self):
    self.entities = []

"""
This class Record overrides some methods because it needs to accomplish proper deserialization of the logged entity.
It uses Model._clone_properties() in Record.log_entity() and Record._get_property_for() - that is because 
if we do not call that method, the class(cls) scope - Record._properties will be altered which will cause variable leak,
meaning that simultaneously based on user actions, new properties will be appended to Record._properties and that will 
cause complete inconsistency and errors while fetching, storing and deleting data. (This was noticed upon testing)

Same approach must be done with the transaction / entry / entry line scenario, which implements its own logic for new
properties.

This implementation will not cause any performance issues or variable leak whatsoever, the _properties will be adjusted to
be available in `self` - not `cls`. 

In the begining i forgot to look into the Model._fix_up_properties, which explicitly sets cls._properties to {} which then
allowed mutations to class(cls) scope.
"""

class Record(ndb.BaseExpando):
  
  _kind = 5
  # Letters for field aliases are provided in order not to conflict with logged object fields, and alow scaling!
  logged = ndb.SuperDateTimeProperty('l', auto_now_add=True)
  agent = ndb.SuperKeyProperty('u', kind='0', required=True)
  action = ndb.SuperKeyProperty('a', kind='56', required=True)
  
  _expando_fields = {
                     'message' : ndb.SuperTextProperty('m'),
                     'note' : ndb.SuperTextProperty('n'),
                     }
  
  
  @classmethod
  def get_logs(cls, entity, urlsafe_cursor, items_per_page=10):
    
    from app.srv import rule
    
    cursor = Cursor(urlsafe=urlsafe_cursor)
    query = cls.query(ancestor=entity.key).order(-cls.logged)
    
    @ndb.tasklet
    def async(entity):
      
        new_entity = entity.__todict__()
      
        if entity.key_namespace:
           domain_user_key = rule.DomainRole.build_key(entity.agent.key_id_str, namespace=entity.key_namespace)
           agent = yield domain_user_key.get_async()
           agent = agent.name
        else:
           agent = yield entity.agent.get_async()
           agent = agent.primary_email
           
        new_entity['agent'] = agent
 
        action_key_id = str(entity.action.id()).split('-')
 
        if len(action_key_id) == 2:
           kind_id, action_id = action_key_id
           
           modelclass = entity._kind_map.get(kind_id)
           
           if modelclass and hasattr(modelclass, '_actions'):
              for action_key, action in modelclass._actions.items():
                  if entity.action == action.key:
                     new_entity['action'] = '%s.%s' % (modelclass.__name__, action_key)
                     break
        else:
           new_entity['action'] = entity.action.id()
                  
        raise ndb.Return(new_entity)
         
    # query.map and fetch_page wont work in conjunction ---- query.map(fetch_agent)
    # entities = pager.fetch_page(query, _async, page_size=items_per_page, start_cursor=cursor)
    
    entities, next_cursor, more = query.fetch_page(items_per_page, start_cursor=cursor)
     
    @ndb.tasklet 
    def helper(entities):
        
       results = yield map(async, entities)
       
       raise ndb.Return(results)
    
    entities = helper(entities)
    entities = [entity for entity in entities.get_result()]
      
    return {'entities' : entities, 'next_cursor' : next_cursor.urlsafe(), 'more' : more}
  
  
  def _get_property_for(self, p, indexed=True, depth=0):
    """Overrides ndb.BaseExpando._get_property_for. 
       Only way to merge properties from its parent kind to log entity.
    """
    name = p.name()
    parts = name.split('.')
    if len(parts) <= depth:
      # Apparently there's an unstructured value here.
      # Assume it is a None written for a missing value.
      # (It could also be that a schema change turned an unstructured
      # value into a structured one.  In that case, too, it seems
      # better to return None than to return an unstructured value,
      # since the latter doesn't match the current schema.)
      return None
    next = parts[depth]

    prop = self._properties.get(next)
    if prop is None:
       # this loads up proper class to deal with the expandos
       kind = self.key_parent.kind()
       modelclass = self._kind_map.get(kind)
       
       # adds properties from parent class to the log entity making it possible to deserialize properties properly
       prop = modelclass._properties.get(next)
       if prop:
          self._clone_properties() # clone properties, because if we dont, the Record._properties will be overriden
          self._properties[next] = prop
 
    return super(Record, self)._get_property_for(p, indexed, depth)
  
  # Log entity's each property
  def log_entity(self, entity):
    self._clone_properties() # clone properties, because if we dont, the Record._properties will be overriden
    for p in entity._properties:
      prop = entity._properties.get(p)
      value = prop._get_value(entity)
      self._properties[prop._name] = prop
      prop._set_value(self, value)
    return self


class Engine:
  
  @classmethod
  def run(cls, context, transaction=False):
    
    def log(context):
      if len(context.log.entities):
        records = []
        for config in context.log.entities:
          entity = config[0]
          try:
            kwargs = config[1]
          except:
            kwargs = None
          
          if not kwargs:
            kwargs = {}
          
          log_entity = kwargs.pop('log_entity', True)
          record = Record(parent=entity.key, agent=context.auth.user.key, action=context.action.key, **kwargs)
          if log_entity is True:
            log_entity = entity
          if log_entity:
            record.log_entity(log_entity)
          records.append(record)
          
        if len(records):
          recorded = ndb.put_multi(records)
          context.log.entities = []
    
    if (transaction):
      ndb.transaction(lambda: log(context))
    else:
      log(context)
