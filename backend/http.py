# -*- coding: utf-8 -*-
'''
Created on Sep 22, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
import webapp2
import json
import datetime
import inspect
import copy
import sys
import urllib

import orm, mem, iom, settings, util

sys.setrecursionlimit(2147483647) # we need recursion stack because most of our code relies on recursion
# however, we could rewrite the code to not use recursion in future

CSRF_KEY = '_csrf'
COOKIE_USER_KEY = 'auth'


def json_output(s, **kwargs):
  '''Converts all known and complex values generated by the application to json format.
  '''
  defaults = {'indent': 2, 'check_circular': False, 'cls': JSONEncoder}
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

  def iterencode(self, o, _one_shot=False):
    chunks = super(JSONEncoder, self).iterencode(o, _one_shot)
    for chunk in chunks:
      chunk = chunk.replace('&', '\\u0026')
      chunk = chunk.replace('<', '\\u003c')
      chunk = chunk.replace('>', '\\u003e')
      yield chunk


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
          util.log('error parsing __body__ %s' % e, 'error')
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
  
  def load_current_account(self):
    ''' Loads current user from the local thread and sets it as self.current_account for easier handler access to it.
    Along with that, also sets if the request came from taskqueue or cron, based on app engine headers.
    '''
    if self.current_account is None and self.autoload_current_account:
      from models.account import Account
      Account.set_current_account_from_auth_code(self.request.cookies.get(COOKIE_USER_KEY))
      current_account = Account.current_account()
      current_account.set_taskqueue(self.request.headers.get('X-AppEngine-QueueName', None) != None) # https://developers.google.com/appengine/docs/python/taskqueue/overview-push#Python_Task_request_headers
      current_account.set_cron(self.request.headers.get('X-Appengine-Cron', None) != None) # https://developers.google.com/appengine/docs/python/config/cron#Python_app_yaml_Securing_URLs_for_cron
      self.current_account = current_account
  
  def load_csrf(self):
    if self.current_csrf is None and self.autoload_current_account:
      input = self.get_input()
      csrf_cookie_value = input.get(CSRF_KEY)
      self.current_csrf = csrf_cookie_value
  
  def validate_csrf(self):
    if self.autoload_current_account and self.autovalidate_csrf:
      if not self.current_account._is_guest and (self.current_account._csrf != self.current_csrf):
        self.abort(403)
  
  @orm.toplevel
  def dispatch(self):
    self.load_current_account()
    self.load_csrf()
    self.validate_csrf()
    try:
      self.before()
      super(RequestHandler, self).dispatch()
      self.after()
    finally:
      # support our memcache wrapper lib temporary variables, and release them upon request complete
      util.log('Release In-memory Cache')
      mem._local.__release_local__()
      

class Endpoint(RequestHandler):
  
  def respond(self):
    output = iom.Engine.run(self.get_input())
    self.send_json(output)
    
    
class ModelMeta(RequestHandler):
  
  def respond(self):
    # @todo include cache headers here
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
    util.log('Begin IOEngineRun execute')
    input = self.get_input()
    iom.Engine.run(input)
    util.log('End IOEngineRun execute')
  

class AccountLogin(RequestHandler):
  
  def respond(self, provider=None):
    if provider is None:
       provider = 'google'
    data = self.get_input()
    data['login_method'] = provider
    data.update({'action_model' : '11',
                 'action_id' : 'login'})
    output = iom.Engine.run(data)
    if 'authorization_code' in output:
      self.response.set_cookie('auth', output.get('authorization_code'), httponly=True)
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
    self.response.delete_cookie('auth')
    self.redirect('/')
            
            
class OrderComplete(RequestHandler):
  
  def respond(self, order_key):
    params = ['body', 'content_type', 'method', 'url', 'scheme', 'host', 'host_url', 'path_url',
              'path', 'path_qs', 'query_string', 'headers', 'GET', 'POST', 'params', 'cookies']
    data = {'action_model': '34', 'key': order_key, 'action_id': 'complete', 'request': {},
            'read_arguments': {'_lines': {'config': {'search': {'options': {'limit': 0}}}}}}
    for param in params:
      data['request'][param] = getattr(self.request, param)
    output = iom.Engine.run(data)
    return output
            
    
ROUTES = [('/api/endpoint', Endpoint),
          ('/api/model_meta', ModelMeta),
          ('/api/task/io_engine_run', IOEngineRun),
          ('/api/install', Install),
          ('/api/account/login', AccountLogin),
          ('/api/account/login/<provider>', AccountLogin),
          ('/api/account/logout', AccountLogout),
          ('/api/order/complete/<order_key>', OrderComplete)] # this will be the path on which all orders are marked complete


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
    kinds = ['0', '6', '83', '5', '35', '36', '62', '61', '39', '38', '60', '8', '57', '77', '10', '15', '16', '17', '18', '19', '49', '47']
    namespaces = metadata.get_namespaces()
    indexes = []
    keys_to_delete = []
    if self.request.get('kinds'):
      kinds = self.request.get('kinds').split(',')
    if self.request.get('all_kinds'):
      kinds = []
      for kind_id in models:
        if len(kind_id) < 4 and not kind_id.startswith('__'):
          try:
            kinds.append(str(int(kind_id)))
          except ValueError:
            pass
    util.log('DELETE KINDS %s' % kinds)
    ignore = ['15', '16', '17', '18', '19']
    if self.request.get('ignore'):
      ignore = self.request.get('ignore')
    @orm.tasklet
    def wipe(kind):
      util.log('DELETE ENTITY KIND %s' % kind)
      @orm.tasklet
      def generator():
        model = models.get(kind)
        if model and not kind.startswith('__'):
          keys = yield model.query().fetch_async(keys_only=True)
          keys_to_delete.extend(keys)
          indexes.append(search.Index(name=kind))
          for namespace in namespaces:
            util.log('DELETE NAMESPACE %s' % namespace)
            keys = yield model.query(namespace=namespace).fetch_async(keys_only=True)
            keys_to_delete.extend(keys)
            indexes.append(search.Index(name=kind, namespace=namespace))
      yield generator()
    if self.request.get('delete'):
      futures = []
      for kind in kinds:
        if kind not in ignore:
          futures.append(wipe(kind))
      orm.Future.wait_all(futures)
    if self.request.get('and_system'):
      futures = []
      for kind in kinds:
        if kind in ignore:
          futures.append(wipe(kind))
      orm.Future.wait_all(futures)
    if keys_to_delete:
      datastore.Delete([key.to_old_key() for key in keys_to_delete])
    indexes.append(search.Index(name='catalogs'))
    # empty catalog index!
    for index in indexes:
      while True:
        document_ids = [document.doc_id for document in index.get_range(ids_only=True)]
        if not document_ids:
          break
        try:
          index.delete(document_ids)
        except:
          pass
    # delete all blobs
    blobstore.delete(blobstore.BlobInfo.all().fetch(keys_only=True))
    mem.flush_all()

      
class TestAsync(BaseTestHandler):
  
  def respond(self):
    paths = ['http://example.com', 'http://example.com', 'http://example.com']
    if self.request.get('async'):
      futures = []
      ctx = orm.get_context()
      for path in paths:
        print 'async', path
        ctx.urlfetch(path)
      orm.Future.wait_all(futures)
    else:
      from google.appengine.api import urlfetch
      for path in paths:
        print 'sync', path
        urlfetch.fetch(path)
    
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