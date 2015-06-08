# -*- coding: utf-8 -*-
'''
Created on Sep 22, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import webapp2
import json
import datetime
import time
import inspect
import copy
import urllib

import performance
import orm
import mem
import iom
import settings
import util

HTTP_PERFORMANCE_TEXT = 'HTTP.%s in %sms'


def json_output(s, **kwargs):
  '''Converts all known and complex values generated by the application to json format.
  '''
  defaults = {'check_circular': False, 'cls': JSONEncoder}
  defaults.update(kwargs)
  return json.dumps(s, **defaults)


class JSONEncoder(json.JSONEncoder):
  '''An encoder that produces JSON safe to embed in HTML.
  To embed JSON content in, say, a script tag on a web page, the
  characters &, < and > should be escaped. They cannot be escaped
  with the usual entities (e.g. &amp;) because they are not expanded
  within <script> tags.
  Also its `default` function will properly format data that is usually not serialized by json standard.
  '''
  def default(self, o):
    if isinstance(o, datetime.datetime):
       return o.strftime(settings.DATETIME_FORMAT)
    if isinstance(o, orm.Key):
       return o.urlsafe()
    if hasattr(o, 'get_output'):
      try:
        return o.get_output()
      except TypeError as e:
        pass
    if hasattr(o, 'get_meta'):
      try:
       return o.get_meta()
      except TypeError as e:
       pass
    try:
      out = str(o)
      return out
    except TypeError as e:
      pass
    return json.JSONEncoder.default(self, o)


class RequestHandler(webapp2.RequestHandler):
  '''General-purpose handler from which all other handlers must derrive from.
  '''
  autoload_current_account = True
  autovalidate_csrf = False # generally all requests for authenticated users should be carrying _csrf
 
  def __init__(self, *args, **kwargs):
    super(RequestHandler, self).__init__(*args, **kwargs)
    self.current_account = None
    self.current_csrf = None
    self._input = None
  
  @performance.profile(HTTP_PERFORMANCE_TEXT)
  def get_input(self):
    if self._input is not None:
      return self._input
    if self.request.method == 'POST' and not len(self.request.POST):
      dicts = self.request.json_body
      dicts.update(self.request.GET)
    else:
      special = '__body__'
      special_data = self.request.get(special)
      if special_data:
        try:
          dicts = json.loads(special_data)
        except Exception as e:
          dicts = {}
      else:
        dicts = {}
      newparams = {}
      for param_key in self.request.params.keys():
        if param_key == special:
          continue
        value = self.request.params.getall(param_key)
        if len(value) == 1:
           value = value[0]
        newparams[param_key] = value
      dicts.update(newparams)
    self._input = dicts
    return self._input
  
  @performance.profile(HTTP_PERFORMANCE_TEXT)
  def json_output(self, s, **kwargs):
    ''' Wrapper for json output for self usage to avoid imports from backend http '''
    return json_output(s, **kwargs)
  
  def send_json(self, data):
    ''' sends `data` to be serialized in json format, and sets content type application/json utf8'''
    ent = 'application/json;charset=utf-8'
    if self.response.headers.get('Content-Type') != ent:
       self.response.headers['Content-Type'] = ent
    self.response.write(self.json_output(data))
  
  def before(self):
    '''
    This function is fired just before the handler logic is executed
    '''
    pass
  
  def after(self):
    '''
    This function is fired just after the handler is executed
    '''
    pass
  
  def get(self, *args, **kwargs):
    return self.respond(*args, **kwargs)
  
  def post(self, *args, **kwargs):
    return self.respond(*args, **kwargs)
  
  def respond(self, *args, **kwargs):
    self.abort(404)
    self.response.write('<h1>404 Not found</h1>')
  
  @performance.profile(HTTP_PERFORMANCE_TEXT)
  def load_current_account(self):
    ''' Loads current user from the local thread and sets it as self.current_account for easier handler access to it.
    Along with that, also sets if the request came from taskqueue or cron, based on app engine headers.
    '''
    if self.current_account is None and self.autoload_current_account:
      from models.account import Account
      Account.set_current_account_from_access_token(self.request.cookies.get(settings.COOKIE_AUTH_KEY))
      current_account = Account.current_account()
      current_account.set_taskqueue(self.request.headers.get('X-AppEngine-QueueName', None) != None) # https://developers.google.com/appengine/docs/python/taskqueue/overview-push#Python_Task_request_headers
      current_account.set_cron(self.request.headers.get('X-Appengine-Cron', None) != None) # https://developers.google.com/appengine/docs/python/config/cron#Python_app_yaml_Securing_URLs_for_cron
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
    dispatch_time = performance.Profile()
    self.load_current_account()
    self.load_csrf()
    self.validate_csrf()
    try:
      self.before()
      super(RequestHandler, self).dispatch()
      self.after()
    finally:
      util.log.debug('Release In-memory Cache')
      mem.storage.__release_local__()
      util.log.debug('Finished request in %s ms' % dispatch_time.miliseconds)
      

class Endpoint(RequestHandler):
  
  def respond(self):
    output = iom.Engine.run(self.get_input())
    self.send_json(output)
    
    
class ModelMeta(RequestHandler):
  
  def respond(self):
    # @todo include cache headers here
    # @todo implement only the list of kinds that get out by config
    models = iom.Engine.get_schema()
    send = {}
    for kind, model in models.iteritems():
      if kind:
        try:
          int(kind)
          send[kind] = model
        except:
          pass
    self.send_json(send)
    
  
class Install(RequestHandler):
  
  def respond(self):
    out = []
    only = self.request.get('only')
    if only:
      only = only.split(',')
    for model, action in [('12', 'update'), ('24', 'update'), ('17', 'update_unit'), ('17', 'update_currency')]:
      if only and model not in only:
        continue
      out.append(iom.Engine.run({'action_model' : model, 'action_id' : action}))
    self.send_json(out)
    
    
class IOEngineRun(RequestHandler):
  
  def respond(self):
    util.log.debug('Begin IOEngineRun execute')
    input = self.get_input()
    iom.Engine.run(input)
    util.log.debug('End IOEngineRun execute')
  

class AccountLogin(RequestHandler):
  
  def respond(self, provider=None):
    if provider is None:
       provider = 'google'
    data = self.get_input()
    data.update({'action_model' : '11',
                 'login_method': provider,
                 'action_id' : 'login'})
    output = iom.Engine.run(data)
    if 'access_token' in output:
      self.response.set_cookie(settings.COOKIE_AUTH_KEY, output.get('access_token'), httponly=True)
      self.redirect('/login/status?success=true') # we need to see how we can handle continue to link behaviour, generally this needs more work
    elif 'errors' in output:
      self.redirect('/login/status?errors=%s' % urllib.quote(self.json_output(output['errors'])))
    self.send_json(output)
 
class AccountLogout(RequestHandler):
    
  def respond(self):
    data = self.get_input()
    data.update({'action_model' : '11',
                 'action_key' : 'logout'})
    output = iom.Engine.run(data)
    self.response.delete_cookie(settings.COOKIE_AUTH_KEY)
    self.redirect('/')
            
            
class OrderComplete(RequestHandler):
  
  def respond(self, payment_method):
    params = ['body', 'content_type', 'method', 'url', 'scheme', 'host', 'host_url', 'path_url',
              'path', 'path_qs', 'query_string', 'headers', 'GET', 'POST', 'params', 'cookies']
    data = {'action_model': '34', 'payment_method': payment_method, 'action_id': 'complete', 'request': {}}
    for param in params:
      data['request'][param] = getattr(self.request, param)
    output = iom.Engine.run(data)
    return output
            
    
ROUTES = [('/api/endpoint', Endpoint),
          ('/api/model_meta', ModelMeta),
          ('/api/task/io_engine_run', IOEngineRun),
          ('/api/cron/seller', IOEngineRun),
          ('/api/install', Install),
          ('/api/account/login', AccountLogin),
          ('/api/account/login/<provider>', AccountLogin),
          ('/api/account/logout', AccountLogout),
          ('/api/order/complete/<payment_method>', OrderComplete)] # this will be the path on which all orders are marked complete


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
      self.response.write(sp*a)
    self.response.write(s)
    self.response.write(sp*a)
    
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
    if self.request.get('kinds'):
      kinds = self.request.get('kinds').split(',')
    ignore = []
    if self.request.get('ignore'):
      ignore = self.request.get('ignore')
    util.log.debug('Delete kinds %s' % kinds)
    for kind in kinds:
      for namespace in namespaces:
        if kind in ignore:
          continue
        p = performance.Profile()
        gets = datastore.Query(kind, namespace=namespace, keys_only=True).Run()
        keys = list(gets)
        total_keys = len(keys)
        if total_keys:
          util.log.debug('Delete kind %s. Found %s keys. Took %sms to get.' % (kind, total_keys, p.miliseconds))
          p = performance.Profile()
          datastore.Delete(keys)
          util.log.debug('Deleted all records for kind %s. Took %sms.' % (kind, p.miliseconds))
    indexes.extend((search.Index(name='catalogs'), search.Index(name='24')))
    # empty catalog index!
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
    util.log.debug('Deleted %s indexes. With total of %s documents.' % (len(indexes), docs))
    # delete all blobs
    keys = blobstore.BlobInfo.all().fetch(None, keys_only=True)
    blobstore.delete(keys)
    util.log.debug('Deleted %s blobs.' % len(keys))
    mem.flush_all()

class BeginMemTest(BaseTestHandler):

  def respond(self):
    ctx = orm.get_context()
    i = 0
    while True:
      i += 1
      if i == 100:
        break
      ctx.urlfetch('http://128.65.105.64:9982/api/tests/MemTest')
      ctx.urlfetch('http://128.65.105.64:9982/api/tests/AssertTest')

class MemTest(BaseTestHandler):

  def respond(self):
    mem.temp_set('cuser', 1)


class AssertTest(BaseTestHandler):

  def respond(self):
    if mem.temp_get('cuser') is not None:
      util.log.debug('cuser failed, got %s' % mem.temp_get('cuser'))


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
        self.response.set_cookie(settings.COOKIE_AUTH_KEY, '%s|%s' % (account.key_urlsafe, session.session_id), httponly=True)
        self.redirect('/')

    
for k,o in globals().items():
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