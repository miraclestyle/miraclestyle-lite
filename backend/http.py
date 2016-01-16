# -*- coding: utf-8 -*-
'''
Created on Sep 22, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import os
import webapp2
import datetime
import inspect
import urllib
import time
import json

import orm
import iom
import settings
import tools

HTTP_PERFORMANCE_TEXT = 'HTTP.%s in %sms'


class RequestHandler(webapp2.RequestHandler):

  '''General-purpose handler from which all other handlers must derrive from.'''

  autoload_current_account = True
  autovalidate_csrf = False  # generally all requests for authenticated users should be carrying _csrf

  def __init__(self, *args, **kwargs):
    super(RequestHandler, self).__init__(*args, **kwargs)
    self.current_account = None
    self.current_csrf = None
    self._input = None

  def secure_cookie_get(self, key):
    return tools.secure_cookie.deserialize(key, self.request.cookies.get(key))

  def secure_cookie_set(self, key, value, **kwargs):
    secure = tools.secure_cookie.serialize(key, value)
    return self.response.set_cookie(key, secure, **kwargs)

  @tools.profile(HTTP_PERFORMANCE_TEXT)
  def get_input(self):
    if self._input is not None:
      return self._input
    if self.request.method == 'POST' and not len(self.request.POST):
      input = self.request.json_body
      input.update(self.request.GET)
    else:
      value_key = '__body__'
      value = self.request.get(value_key)
      if value:
        try:
          input = tools.json_loads(value)
        except Exception as e:
          input = {}
      else:
        input = {}
      new_params = {}
      for param_key in self.request.params.keys():
        if param_key == value_key:
          continue
        value = self.request.params.getall(param_key)
        if len(value) == 1:
          value = value[0]
        new_params[param_key] = value
      input.update(new_params)
    input['__request__'] = self.request
    self._input = input
    return self._input

  @tools.profile(HTTP_PERFORMANCE_TEXT)
  def json_output(self, obj, **kwargs):
    '''Wrapper for json output for self usage to avoid imports from backend http.'''
    return tools.json_dumps(obj, **kwargs)

  def send_json(self, data, json=False):
    '''Sends `data` to be serialized in json format, and sets content type application/json utf8.'''
    content_type = 'application/json;charset=utf-8'
    if self.response.headers.get('Content-Type') != content_type:
      self.response.headers['Content-Type'] = content_type
    if not json:
      data = self.json_output(data)
    self.response.write(data)

  def before(self):
    '''This function is fired just before the handler logic is executed.'''
    pass

  def after(self):
    '''This function is fired just after the handler is executed.'''
    pass

  def get(self, *args, **kwargs):
    return self.respond(*args, **kwargs)

  def post(self, *args, **kwargs):
    return self.respond(*args, **kwargs)

  def respond(self, *args, **kwargs):
    self.abort(404)
    self.response.write('<h1>404 Not found</h1>')

  @tools.profile(HTTP_PERFORMANCE_TEXT)
  def load_current_account(self):
    '''Loads current user from the local thread and sets it as self.current_account for easier handler access to it.
    Along with that, also sets if the request came from taskqueue or cron, based on app engine headers.
    '''
    if self.current_account is None and self.autoload_current_account:
      from models.account import Account
      unsecure = self.secure_cookie_get(settings.COOKIE_AUTH_KEY)
      if not unsecure:
        unsecure = headers.get('Authorization')
      headers = self.request.headers
      Account.set_current_account_from_access_token(unsecure)
      current_account = Account.current_account()
      current_account.set_taskqueue(headers.get('X-AppEngine-QueueName', None) != None)  # https://developers.google.com/appengine/docs/python/taskqueue/overview-push#Python_Task_request_headers
      current_account.set_cron(headers.get('X-Appengine-Cron', None) != None)  # https://developers.google.com/appengine/docs/python/config/cron#Python_app_yaml_Securing_URLs_for_cron
      current_account.set_location_data({'_country': headers.get('X-AppEngine-Country'), '_city': headers.get('X-AppEngine-City'), '_region': headers.get('X-AppEngine-Region')})
      self.current_account = current_account

  def load_csrf(self):
    if self.current_csrf is None and self.autoload_current_account:
      input = self.get_input()
      csrf_cookie_value = input.get(settings.CSRF_TOKEN_KEY)
      self.current_csrf = csrf_cookie_value

  def validate_csrf(self):
    if self.autoload_current_account and self.autovalidate_csrf:
      if not self.current_account._is_guest and (self.current_account._csrf != self.current_csrf):
        self.abort(403)

  @orm.toplevel
  def dispatch(self):
    # @tools.detail_profile(HTTP_PERFORMANCE_TEXT)
    dispatch_time = tools.Profile()
    if settings.LAG:
      time.sleep(settings.LAG)
    self.load_current_account()
    self.load_csrf()
    self.validate_csrf()
    if not (self.request.headers.get('X-AppEngine-QueueName', None) != None or self.request.headers.get('X-Appengine-Cron', None) != None) and (settings.FORCE_SSL and not os.environ.get('HTTPS') == 'on'):
      return self.redirect(self.request.url.replace('http://', 'https://'))
    try:
      self.before()
      super(RequestHandler, self).dispatch()
      self.after()
    finally:
      tools.log.debug('Finished request in %s ms' % dispatch_time.miliseconds)


class Endpoint(RequestHandler):

  def respond(self):
    output = iom.Engine.run(self.get_input(), 'json')
    self.send_json(output, True)


class ModelMeta(RequestHandler):

  def respond(self):
    # @todo include cache headers here
    # @todo implement only the list of kinds that get out by config
    output = {}
    kinds = []
    models = iom.Engine.get_schema()
    version_key = 'ModelMeta_CURRENT_VERSION_ID'
    version = tools.mem_rpc_get(version_key)
    real_version = str(os.environ.get('CURRENT_VERSION_ID'))
    key = 'ModelMeta_%s' % real_version
    current_key = 'ModelMeta_%s' % version
    cached_output = tools.mem_get(key)
    new_version = version != real_version
    if not cached_output or new_version:
      for kind, model in models.iteritems():
        if kind:
          try:
            int(kind)
            output[kind] = model
          except:
            pass
      output = self.json_output(output)
      if new_version:
        tools.mem_delete_multi([version_key, current_key])
      tools.mem_set_multi({key: output, version_key: real_version})
      self.send_json(output, True)
    else:
      self.send_json(cached_output, True)


class Install(RequestHandler):

  def respond(self):
    output = []
    input = self.get_input()
    only = input.get('only')
    if only:
      only = only.split(',')
    for model, action in [('12', 'update'), ('24', 'update'), ('17', 'update_unit'), ('17', 'update_currency')]:
      if only and model not in only:
        continue
      input.update({'action_model': model, 'action_id': action})
      output.append(iom.Engine.run(input))
    self.send_json(output)


class IOEngineRun(RequestHandler):

  def respond(self):
    tools.log.debug('Begin IOEngineRun execute')
    iom.Engine.run(self.get_input())
    tools.log.debug('End IOEngineRun execute')


class AccountLogin(RequestHandler):

  def respond(self, provider=None):
    redirect_to_key = 'redirect_to'
    do_redirect = False
    if provider is None:
      provider = 'google'
    input = self.get_input()
    input.update({'action_model': '11',
                  'login_method': provider,
                  'action_id': 'login'})
    output = iom.Engine.run(input)
    if redirect_to_key in input:
      self.secure_cookie_set(redirect_to_key, input.get(redirect_to_key), httponly=True)
    if 'access_token' in output:
      self.secure_cookie_set(settings.COOKIE_AUTH_KEY, output.get('access_token'), httponly=True)
      do_redirect = True
    if output.get('taken_by_other_account'):
      do_redirect = True
    if do_redirect:
      redirect_to = self.secure_cookie_get(redirect_to_key)
      if redirect_to and not redirect_to.startswith('http') and not redirect_to == 'popup':
        return self.redirect(redirect_to)
      self.redirect('/login/status?success=true%s' % ('&popup=true' if redirect_to == 'popup' else '',))
    elif 'errors' in output:
      self.redirect('/login/status?errors=%s' % urllib.quote(self.json_output(output['errors'])))
    self.send_json(output)


class AccountLogout(RequestHandler):

  def respond(self):
    input = self.get_input()
    input.update({'action_model': '11',
                  'action_key': 'logout'})
    output = iom.Engine.run(input)
    self.response.delete_cookie(settings.COOKIE_AUTH_KEY)
    self.redirect('/')


class CatalogCron(RequestHandler):

  def respond(self):
    input = self.get_input()
    input.update({'action_model': '31', 'action_id': 'cron'})
    iom.Engine.run(input)


class OrderNotify(RequestHandler):

  def respond(self, payment_method):
    params = ['body', 'content_type', 'method', 'url', 'scheme', 'host', 'host_url', 'path_url',
              'path', 'path_qs', 'query_string', 'headers', 'GET', 'POST', 'params', 'cookies']
    input = self.get_input()
    input.update({'action_model': '34', 'payment_method': payment_method, 'action_id': 'notify', 'request': {}})
    for param in params:
      input['request'][param] = getattr(self.request, param)
    iom.Engine.run(input)


class OrderCron(RequestHandler):

  def respond(self):
    input = self.get_input()
    input.update({'action_model': '34', 'action_id': 'cron'})
    iom.Engine.run(input)

class OrderCronNotify(RequestHandler):

  def respond(self):
    input = self.get_input()
    input.update({'action_model': '34', 'action_id': 'cron_notify'})
    iom.Engine.run(input)


ROUTES = [('/api/endpoint', Endpoint),
          ('/api/model_meta', ModelMeta),
          ('/api/task/io_engine_run', IOEngineRun),
          ('/api/install', Install),
          ('/api/account/login', AccountLogin),
          ('/api/account/login/<provider>', AccountLogin),
          ('/api/account/logout', AccountLogout),
          ('/api/catalog/cron', CatalogCron),
          ('/api/order/notify/<payment_method>', OrderNotify),
          ('/api/order/cron', OrderCron),
          ('/api/order/cron_notify', OrderCronNotify)]


# Test Handlers
class BaseTestHandler(RequestHandler):

  autoload_current_account = False

  def before(self):
    self.response.headers['Content-Type'] = 'text/plain;charset=utf8;'

  def out_json(self, s):
    self.out(self.json_output(s))

  def out(self, s, a=0, before=True):
    sp = "\n"
    if before:
      self.response.write(sp * a)
    self.response.write(s)
    self.response.write(sp * a)


class Reset(BaseTestHandler):

  def respond(self):
    from google.appengine.ext.ndb import metadata
    from google.appengine.api import search, datastore
    from google.appengine.ext import blobstore
    # @todo THIS DELETES EVERYTHING FROM DATASTORE AND BLOBSTORE, AND CURRENTLY EXISTS ONLY FOR TESTING PURPOSES!
    models = iom.Engine.get_schema()
    kinds = [str(i) for i in xrange(200)]
    namespaces = metadata.get_namespaces()
    indexes = []
    if not self.request.get('do_not_delete_datastore'):
      if self.request.get('kinds'):
        kinds = self.request.get('kinds').split(',')
      ignore = []
      if self.request.get('ignore'):
        ignore = self.request.get('ignore')
      tools.log.debug('Delete kinds %s' % kinds)
      for kind in kinds:
        for namespace in namespaces:
          if kind in ignore:
            continue
          p = tools.Profile()
          gets = datastore.Query(kind, namespace=namespace, keys_only=True).Run()
          keys = list(gets)
          total_keys = len(keys)
          if total_keys:
            tools.log.debug('Delete kind %s. Found %s keys. Took %sms to get.' % (kind, total_keys, p.miliseconds))
            p = tools.Profile()
            datastore.Delete(keys)
            tools.log.debug('Deleted all records for kind %s. Took %sms.' % (kind, p.miliseconds))
    indexes.extend((search.Index(name='catalogs'), search.Index(name='24')))
    # empty catalog index!
    if not self.request.get('do_not_delete_indexes'):
      docs = 0
      for index in indexes:
        while True:
          document_ids = [document.doc_id for document in index.get_range(ids_only=True)]
          if not document_ids:
            break
          try:
            index.delete(document_ids)
            docs += len(document_ids)
          except:
            pass
      tools.log.debug('Deleted %s indexes. With total of %s documents.' % (len(indexes), docs))
    # delete all blobs
    if not self.request.get('do_not_delete_blobs'):
      keys = blobstore.BlobInfo.all().fetch(None, keys_only=True)
      blobstore.delete(keys)
      tools.log.debug('Deleted %s blobs.' % len(keys))
    if not self.request.get('do_not_delete_memcache'):
      tools.mem_flush_all()


class LoginAs(BaseTestHandler):

  def respond(self):
    models = iom.Engine.get_schema()
    Account = models['11']
    if self.request.get('email'):
      account = Account.query(Account.identities.email == self.request.get('email')).get()
      if account:
        account.read()
        session = account.new_session()
        account._use_rule_engine = False
        account.put()
        Account.set_current_account(account, session)
        self.secure_cookie_set(settings.COOKIE_AUTH_KEY, '%s|%s' % (account.key_urlsafe, session.session_id), httponly=True)
        self.redirect('/')

if settings.DEBUG:
  for k, o in globals().items():
    if inspect.isclass(o) and issubclass(o, BaseTestHandler):
      ROUTES.append(('/api/tests/%s' % o.__name__, o))

# due development server bug, make additional routing with proxy prefix
if settings.DEVELOPMENT_SERVER:
  for route in list(ROUTES):
    proxy_route = (route[0].replace('/api/', '/api/proxy/'), route[1])
    ROUTES.append(proxy_route)

ROUTES[:] = map(lambda args: webapp2.Route(*args), ROUTES)

# expose app to app.yaml
app = webapp2.WSGIApplication(ROUTES, debug=settings.DEBUG)
