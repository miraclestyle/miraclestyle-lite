# -*- coding: utf-8 -*-
'''
Created on Jun 14, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import copy
import time
import zlib
import base64
import hashlib

import orm
import tools


class Context(orm.BaseModel):

  _kind = 86

  def run(self, context):
    context.cache = None
    context.account = context.models['11'].current_account()
    caller_account_key = context.input.get('caller_account')
    if context.account._is_taskqueue:
      if caller_account_key:
        caller_account = caller_account_key.get()
        if caller_account:
          caller_account.read()
          context.account = caller_account
      else:
        context.account = context.models['11'].system_account()
    context._callbacks = []
    context.output['is_guest'] = context.account._is_guest
    action = context.action
    if not action.skip_csrf and not (context.account._is_taskqueue or context.account._is_cron):
      csrf = context.raw_input.get('_csrf')
      if csrf != '_____skipcsrf_____' and context.account._csrf != context.raw_input.get('_csrf'):
        tools.log.warn('Invalid csrf sent, expected %s got %s' % (context.account._csrf, context.raw_input.get('_csrf')))
        raise ValueError({'invalid_csrf': True})



class Set(orm.BaseModel):

  _kind = 87

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    static_values = self.cfg.get('s', {})
    dynamic_values = self.cfg.get('d', {})
    remove_values = self.cfg.get('rm', [])
    function_values = self.cfg.get('f', {})
    remove_structured_values = self.cfg.get('rms', [])
    for key, f in function_values.iteritems():
      tools.set_attr(context, key, f())
    for key, value in static_values.iteritems():
      tools.set_attr(context, key, value)
    for key, value in dynamic_values.iteritems():
      set_value = tools.get_attr(context, value, tools.Nonexistent)
      if set_value is not tools.Nonexistent:
        tools.set_attr(context, key, set_value)
    for key in remove_values:
      tools.del_attr(context, key)
    for key in remove_structured_values:
      items = tools.get_attr(context, key)
      if isinstance(items, list):
        for item in items:
          item._state = 'removed'
      else:
        items._state = 'removed'


class Read(orm.BaseModel):

  _kind = 88

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default=[])
  
  @tools.detail_profile('Read.%s slow %s', satisfy=lambda profiler, ctime: ctime.miliseconds > 1000)
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    source_path = self.cfg.get('source', 'input.key')
    model_path = self.cfg.get('model', 'model')
    parent_path = self.cfg.get('parent', None)
    namespace_path = self.cfg.get('namespace', 'namespace')
    read_arguments_path = self.cfg.get('read', 'input.read_arguments')
    save_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    source = tools.get_attr(context, source_path, None)
    model = tools.get_attr(context, model_path)
    parent = tools.get_attr(context, parent_path)
    namespace = tools.get_attr(context, namespace_path)
    if isinstance(read_arguments_path, dict):
      read_arguments = copy.deepcopy(read_arguments_path)
    else:
      read_arguments = tools.get_attr(context, read_arguments_path, {})
    if parent is not None:
      namespace = None
    if source and isinstance(source, orm.Key):
      entity = source.get()
      entity.read(read_arguments)
    elif hasattr(model, 'prepare_key'):
      model_key = model.prepare_key(context.input, parent=parent, namespace=namespace)  # @note Perhaps, all context system wide variables should be passed to prepare_key (input, output, action, model, models, domain, namespace...)
      if model_key.id() is not None:
        entity = model_key.get()
        if entity is None:
          entity = model(key=model_key)
        else:
          entity.read(read_arguments)
      else:
        entity = model(key=model_key)
    else:
      entity = model(parent=parent, namespace=namespace)
    entity.make_original()
    tools.set_attr(context, save_path, entity)

class Write(orm.BaseModel):

  _kind = 89

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    static_record_arguments = self.cfg.get('sra', {})
    dynamic_record_arguments = self.cfg.get('dra', {})
    entity = tools.get_attr(context, entity_path)
    condition = self.cfg.get('condition', None)
    condition_kwargs = self.cfg.get('condition_kwargs', {})
    if condition:
      default_condition_kwargs = {'entity': entity}
      for key, value in condition_kwargs.iteritems():
        default_condition_kwargs[key] = tools.get_attr(context, value)
      if not condition(**default_condition_kwargs):
        return  # skip run if condition does not satisfy
    if entity and isinstance(entity, orm.Model):
      record_arguments = {'agent': context.account.key, 'action': context.action.key}
      record_arguments.update(static_record_arguments)
      for key, value in dynamic_record_arguments.iteritems():
        record_arguments[key] = tools.get_attr(context, value)
      entity.write(record_arguments)


class Delete(orm.BaseModel):

  _kind = 90

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    static_record_arguments = self.cfg.get('sra', {})
    dynamic_record_arguments = self.cfg.get('dra', {})
    entity = tools.get_attr(context, entity_path)
    if entity and isinstance(entity, orm.Model):
      record_arguments = {'agent': context.account.key, 'action': context.action.key}
      record_arguments.update(static_record_arguments)
      for key, value in dynamic_record_arguments.iteritems():
        record_arguments[key] = tools.get_attr(context, value)
      entity.delete(record_arguments)
      entity._state = 'deleted' # signal the response that this is no longer existing


class Duplicate(orm.BaseModel):

  _kind = 91

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('source', '_' + context.model.__name__.lower())
    save_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    duplicate_path = self.cfg.get('duplicate_path')
    entity = tools.get_attr(context, entity_path)
    if duplicate_path:
      # state entity._images.value.0.pricetags.value.0
      split_duplicate_path = duplicate_path.split('.')
      child_entity = tools.get_attr(entity, duplicate_path)
      duplicated_child_entity = child_entity.duplicate()
      context.duplicated_entity = duplicated_child_entity
      duplicate_entity = entity
      # gets _images.value.0.pricetags
      child_entity_path = ".".join(split_duplicate_path[:-2])
      # sets entity._images.value.0.pricetags => [duplicated_child_entity]
      try:
        int(split_duplicate_path[-1])  # this is a case of repeated property, put the duplicated child into list
        duplicated_child_entity = [duplicated_child_entity]
      except ValueError:
        pass
      if isinstance(duplicated_child_entity, list):
        length = len(tools.get_attr(entity, '%s.value' % child_entity_path))
        duplicated_child_entity[0]._sequence = length
      tools.set_attr(entity, child_entity_path, duplicated_child_entity)
    else:
      if entity and isinstance(entity, orm.Model):
        duplicate_entity = entity.duplicate()
        context.duplicated_entity = duplicate_entity
    tools.set_attr(context, save_path, duplicate_entity)


class UploadImages(orm.BaseModel):

  _kind = 92

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    images_path = self.cfg.get('images_path')
    property_value = tools.get_attr(context, entity_path)
    if property_value is not None and hasattr(property_value, 'add') and callable(property_value.add):
      property_value.add(tools.get_attr(context, images_path))


class RulePrepare(orm.BaseModel):

  _kind = 93

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  #@tools.detail_profile('RulePrepare.%s %s')
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    static_kwargs = self.cfg.get('s', {})
    dynamic_kwargs = self.cfg.get('d', {})
    kwargs = {'account': context.account, 'action': context.action, 'input': context.input}
    kwargs.update(static_kwargs)
    for key, value in dynamic_kwargs.iteritems():
      kwargs[key] = tools.get_attr(context, value)
    entity = tools.get_attr(context, entity_path)
    tools.rule_prepare(entity, **kwargs)


class RuleExec(orm.BaseModel):

  _kind = 94

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    action_path = self.cfg.get('action', 'action')
    entity = tools.get_attr(context, entity_path)
    action = tools.get_attr(context, action_path)
    tools.rule_exec(entity, action)


class Search(orm.BaseModel):

  _kind = 95

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  @tools.detail_profile('Search.%s slow %s', satisfy=lambda profiler, ctime: ctime.miliseconds > 1000)
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    static_arguments = self.cfg.get('s', {})
    dynamic_arguments = self.cfg.get('d', {})
    search_arguments = context.input.get('search')
    overide_arguments = {}
    overide_arguments.update(static_arguments)
    for key, value in dynamic_arguments.iteritems():
      overide_arguments[key] = tools.get_attr(context, value)
    tools.override_dict(search_arguments, overide_arguments)
    result = context.model.search(search_arguments)
    if search_arguments.get('keys'):
      context._entities = result
      context._cursor = None
      context._more = False
    elif context.model._use_search_engine:
      context._total_matches = result.number_found
      context._entities_count = len(result.results)
      context._entities = map(context.model.search_document_to_entity, result.results)
      more = False
      cursor = result.cursor
      if cursor is not None:
        cursor = cursor.web_safe_string
        more = True
      context._cursor = cursor
      context._more = more
    else:
      context._entities_count = len(result[0])
      context._entities = result[0]
      cursor = result[1]
      if cursor is not None:
        cursor = cursor.urlsafe()
      context._cursor = cursor
      context._more = result[2]
    # if we dont call .read() it wont load any properties that depend on it. e.g. localstructured ones.
    make_original = {'self_reference': True}
    map(lambda ent: ent.read(make_original=make_original), context._entities)


class CallbackExec(orm.BaseModel):

  _kind = 97

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default=[])

  def run(self, context):
    if not isinstance(self.cfg, list):
      self.cfg = []
    queues = {}
    for config in self.cfg:
      queue_name, static_values, dynamic_values, condition = config
      values = {}
      values.update(static_values)
      for key, value in dynamic_values.iteritems():
        values[key] = tools.get_attr(context, value)
      if condition is None or condition(**values):
        context._callbacks.append((queue_name, values))
    for callback in context._callbacks:
      if callback[1].get('caller_account') is None:
        callback[1]['caller_account'] = context.account.key_urlsafe
      if callback[1].get('caller_action') is None:
        callback[1]['caller_action'] = context.action.key_urlsafe
    tools.callback_exec('/api/task/io_engine_run', context._callbacks)
    context._callbacks = []


class BlobURL(orm.BaseModel):

  _kind = 98

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    gs_bucket = self.cfg.get('bucket', None)
    sufix = self.cfg.get('sufix', '/' + context.account.key_urlsafe)
    upload_url = context.input.get('upload_url')
    if upload_url and gs_bucket:
      gs_bucket_name = gs_bucket + sufix
      context._blob_url = tools.blob_create_upload_url(upload_url, gs_bucket_name)


class CreateChannel(orm.BaseModel):

  _kind = 128

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    dynamic_token_reference = self.cfg.get('dynamic_token_reference', 'account.key_urlsafe')
    static_token_reference = self.cfg.get('static_token_refere', None)
    if static_token_reference is None:
      token_reference = 'channel_%s' % tools.get_attr(context, dynamic_token_reference)
    else:
      token_reference = 'channel_%s' % static_token_reference
    token = tools.mem_rpc_get(token_reference)
    if token and token[1] > time.time():
      context._token = token[0]
    else:
      context._token = tools.channel_create(token_reference)
      tools.mem_rpc_set(token_reference, [context._token, time.time() + 6000], 9600)


class Notify(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    entity_path = self.cfg.get('path', '_' + context.model.__name__.lower())
    method = self.cfg.get('method', ['mail'])
    if not isinstance(method, (list, tuple)):
      method = [method]
    condition = self.cfg.get('condition', None)
    static_values = self.cfg.get('s', {})
    dynamic_values = self.cfg.get('d', {})
    entity = tools.get_attr(context, entity_path)
    values = {'account': context.account, 'input': context.input, 'action': context.action, 'entity': entity}
    values.update(static_values)
    for key, value in dynamic_values.iteritems():
      values[key] = tools.get_attr(context, value)
    if condition is None or condition(**values):
      if 'mail' in method:
        tools.mail_send(values)
      if 'http' in method:
        tools.http_send(values)
      if 'channel' in method:
        tools.channel_send(values)


class BaseCache(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    active = self.cfg.get('active', True)
    if not active:
      return
    CacheGroup = context.models[self.cfg.get('kind', '135')]
    cache = self.cfg.get('cache', [])
    group_id = self.cfg.get('group', None)
    if not isinstance(group_id, (list, tuple)) and group_id is not None:
      group_id = [group_id]
    if group_id is not None:
      group_ids = group_id[:]
      for i, g in enumerate(group_ids):
        if callable(g):
          thing = g(context)
          if thing is not None:
            group_ids[i] = g(context)
          else:
            group_ids.remove(g)
      group_id = group_ids
    dcache_driver = self.cfg.get('dcache', [])
    cache_drivers = []
    all_prequesits = ['auth', 'guest', context.account.key_id_str]
    for driver in cache:
      if callable(driver):
        driver = driver(context)
        if driver is None:
          continue
      user = driver == 'account'
      if not context.account._is_guest:
        if user and not context.account._is_guest:
          cache_drivers.append(context.account.key_id_str)
        if driver == 'auth':
          cache_drivers.append('auth')
        if driver == 'admin' and context.account._root_admin:
          cache_drivers.append('admin')
      elif driver == 'guest':
        cache_drivers.append('guest')
      if driver == 'all' and not any(baddie in cache_drivers for baddie in all_prequesits):
        cache_drivers.append('all')
    for d in dcache_driver:
      cache_drivers.append(tools.get_attr(context, d))
    cache_drivers = set(cache_drivers)
    key = self.cfg.get('key')
    if callable(key):
      key = key(context)
    if not key:
      key = hashlib.md5(tools.json_dumps(context.raw_input)).hexdigest()
    data = None

    def build_key(driver, key, group_key):
      out = '%s_%s' % (driver, key)
      if group_key:
        out += '_%s' % group_key._id_str
      return hashlib.md5(out).hexdigest()

    if self.getter:
      group_key = None
      if group_id:
        first_group_id = group_id[0]
        group_key = CacheGroup.build_key(first_group_id)

      def do_save(data):
        queue = {}
        saved_keys = []
        for driver in cache_drivers:
          k = build_key(driver, key, group_key)
          queue[k] = zlib.compress(data)
        try:
          tools.mem_set_multi(queue)
        except ValueError as e:
          tools.log.error('Failed saving response because it\'s over 1mb, with queue keys %s, using group %s, with drivers %s. With input %s' % (queue, group_key, cache_drivers, context.input))
          write = False  # failed writing this one, because size is over 1mb -- this can be fixed by chunking the `data`, but for now we dont need it
      saver = {'do_save': do_save}
      found = None
      for driver in cache_drivers:
        k = build_key(driver, key, group_key)
        active_k = '%s_active' % k
        data = tools.mem_get_multi([active_k, k])
        if data:
          cache_hit = k in data
          if not cache_hit:
            continue
          if group_key and cache_hit and not data.get(active_k):
            tools.log.debug('Cache hit at %s but waiting for %s' % (k, active_k))
            return # this means that taskqueue did not finish storing the key and cache will be available as soon as possible
          try:
            found = zlib.decompress(data[k])
          except Exception as e:
            found = None
            tools.log.warn('Failed upacking memcache data for key %s in context of: using group %s, with driver %s. With input %s. Memory key deleted.' % (k, group_key, driver, context.input))
            tools.mem_delete_multi([k, active_k])
          break
      if found:
        context.cache = {'value': found}
        raise orm.TerminateAction('Got cache with key %s from %s drivers using group %s.' % (k, cache_drivers, group_key))
      else:
        keys = []
        for driver in cache_drivers:
          keys.append(build_key(driver, key, group_key))
        if keys:
          keys = base64.b64encode(zlib.compress(','.join(keys))) # we compress keys because of taskqueues limit of 100k request payload
          if group_key:
            tools.log.info('Scheduling group cache storage for group %s and cache drivers %s' % (group_key, cache_drivers))
            context._callbacks.append(('callback', {'action_id': 'update', 'keys': keys, 'ids': [group_key._id_str], 'action_model': '135'}))
        else:
          tools.log.warn('No cache for group %s with cache drivers %s' % (group_key, cache_drivers))
      context.cache = saver
    else:
      tools.mem_delete_multi([build_key(driver, key, None) for driver in cache_drivers])
      if hasattr(context, 'delete_cache_groups'):
        if not group_id:
          group_id = []
        group_id.extend(context.delete_cache_groups)
      if group_id:
        keys = []
        satisfy = self.cfg.get('satisfy', {})
        for spec in satisfy:
          groups, callback = spec
          for group in group_id[:]:
            if group in groups:
              if not callback(context, group):
                group_id.remove(group)
        group_keys = [CacheGroup.build_key(id) for id in group_id]
        groups = orm.get_multi(group_keys) # this can cause operating on multiple groups error
        # however if that happens, just move the DeleteCache plugin away from the transaction, since it does not need it
        # anyway 25 entity groups is the limit and usually we operate on max 5 groups per flush
        for group in groups:
          if group:
            keys.extend(group.keys)
        for k in keys[:]:
          keys.append('%s_active' % k)
        tools.mem_delete_multi(keys)
        tools.log.info('Deleted cache for group %s' % group_id)
        orm.delete_multi(group_keys)


class GetCache(BaseCache):

  getter = True


class DeleteCache(BaseCache):

  getter = False
