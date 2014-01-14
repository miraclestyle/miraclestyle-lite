# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import os
import cgi
import json
import webapp2
import collections
  
from jinja2 import FileSystemLoader
from webapp2_extras import jinja2

from app.memcache import _local
from app.srv import auth
from app import settings, util
 
from webclient import webclient_settings
from webclient.util import JSONEncoderHTML, Jinja
from webclient.route import get_routes

from google.appengine.ext import blobstore
 
__WSGI_CONFIG = None
 
def wsgi_config(as_tuple=False):
    
    """ Config function. Prepares all variables and routes for webapp2 WSGI startup """
    
    global __WSGI_CONFIG
 
    if __WSGI_CONFIG:
       if not as_tuple:
          return __WSGI_CONFIG
       return tuple(__WSGI_CONFIG.items())
  
    TEMPLATE_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'),)
      
    for a in webclient_settings.ACTIVE_CONTROLLERS:
        util.import_module('webclient.controllers.%s' % a)
          
    JINJA_FILTERS = Jinja.filters
    JINJA_GLOBALS = Jinja.globals         
    # It won't change, so convert it to a tuple to save memory.   
    ROUTES = tuple(get_routes())
   
    JINJA_GLOBALS.update({'uri_for' : webapp2.uri_for, 'ROUTES' : ROUTES, 'settings' : settings, 'webclient_settings' : webclient_settings})
    TEMPLATE_LOADER = FileSystemLoader(TEMPLATE_DIRS)
    
    util.logger('Webapp2 started, compiling stuff')
    
    WSGI_CONFIG = {}
    WSGI_CONFIG.update(webclient_settings.WEBAPP2_EXTRAS)
    WSGI_CONFIG['webapp2_extras.jinja2'] = {
                 'template_path': 'templates',
                 'globals' : JINJA_GLOBALS,
                 'filters' : JINJA_FILTERS,
                 'environment_args': {
                   'extensions': ['jinja2.ext.autoescape', 'jinja2.ext.loopcontrols'],
                   'autoescape' : True, 
                   'loader' : TEMPLATE_LOADER,
                   'cache_size' : webclient_settings.TEMPLATE_CACHE
         }
    }
     
    
    __WSGI_CONFIG = dict(WSGI_CONFIG=WSGI_CONFIG,
                        ROUTES=ROUTES,
                        JINJA_GLOBALS=JINJA_GLOBALS,
                        JINJA_FILTERS=JINJA_FILTERS,
                        TEMPLATE_DIRS=TEMPLATE_DIRS,
                        TEMPLATE_LOADER=TEMPLATE_LOADER
                       )
    if not as_tuple:
       return __WSGI_CONFIG
    else:
       return tuple(__WSGI_CONFIG.items())
   
class RequestData():
    
    # webapp2 request class `webapp2.Request`
    request = None
    
    def __init__(self, request):
        self.request = request
        
    def request_get(self, argument_name, default_value='', allow_multiple=False):
        """Returns the query or POST argument with the given name.

        We parse the query string and POST payload lazily, so this will be a
        slower operation on the first call.

        :param argument_name:
            The name of the query or POST argument.
        :param default_value:
            The value to return if the given argument is not present.
        :param allow_multiple:
            Return a list of values with the given name (deprecated).
        :returns:
            If allow_multiple is False (which it is by default), we return
            the first value with the given name given in the request. If it
            is True, we always return a list.
        """
        param_value = self.get_all(argument_name)
 
        if len(param_value) > 0:
            if allow_multiple:
                return param_value

            return param_value[0]
        else:
            if allow_multiple and not default_value:
                return []

            return default_value
        
    def request_get_all(self, argument_name, default_value=None):
        """Returns a list of query or POST arguments with the given name.

        We parse the query string and POST payload lazily, so this will be a
        slower operation on the first call.

        :param argument_name:
            The name of the query or POST argument.
        :param default_value:
            The value to return if the given argument is not present,
            None may not be used as a default, if it is then an empty
            list will be returned instead.
        :returns:
            A (possibly empty) list of values.
        """
        if self.request.charset:
            argument_name = argument_name.encode(self.request.charset)

        if default_value is None:
            default_value = []

        param_value = self.request.params.getall(argument_name)

        if param_value is None or len(param_value) == 0:
            return default_value
  
        return param_value
         
    def _pack(self, v, t):
        if isinstance(v, (list, tuple)):
           li = list()
           for k in v:
               if isinstance(k, (list, tuple)):
                  li.append(self._pack(k, t))
               else:
                  li.append(t(k))
           return li
       
        if isinstance(v, dict):
             cdict = v
             for b,l in v.items():
                 cdict[b] = t(l)
             return cdict
        else:
            return t(v)
  
    def get_str(self, k, d=None):                  
        return self.get_type(k, str, d)
    
    def get_str_all(self, k, d=None):                  
        return self.get_type(k, str, d, True)

    def get_int(self, k, d=None):                  
        return self.get_type(k, int, d)
    
    def get_int_all(self, k, d=None):                  
        return self.get_type(k, int, d, True)
 
    def get_type(self, k, t, d=None, multiple=False):
        if isinstance(t, (int, long)):
           if multiple:
              return self._pack(self.request_get_all(k, d), t)
           else:
              return self._pack(self.request_get(k, d), t)
        
    def get_all(self, k, d=None):
        if d == None:
           d = []
        if isinstance(k, (list, tuple)):
           x = dict()
           for i in k:
               x[i] = self.request_get_all(i, d)
           return x
        return self.request_get_all(k, d)
    
    def get_combined_params(self):
        return self.get_combined(None)
    
    def get_combined(self, k, d=None):
        
        if k == None:
           k = self.request.params.keys()
 
        if d == None:
           d = []
        if isinstance(k, (list, tuple)):
           x = dict()
           for i in k:
               dx = self.request_get_all(i, d)
               if isinstance(dx, (tuple, list)) and len(dx) == 1:
                  dx = dx[0]
               x[i] = dx
            
           return x
        dx = self.request_get_all(k, d)
        if isinstance(dx, (tuple, list)) and len(dx) == 1:
           dx = dx[0]
        return dx
    
    def get(self, k, d=None):
        if isinstance(k, (list, tuple)):
           x = dict()
           for i in k:
               x[i] = self.request.get(k, d)
           return x
        return self.request.get(k, d)  
    
    def params_all(self):
        return self.get_all(self.request.params.keys())
    
    def params(self):
        return self.get(self.request.params.keys())
  
  
class Handler(webapp2.RequestHandler):
    
    """
    General-purpose handler that comes with:
    self.template to send variables to render template
    and other hooks like `after`, `before` etc.
    
    """
    
    LOAD_CURRENT_USER = True
 
    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.data = {}
        self.template = {'base' : 'index.html'}
        self.__uploads = None
        self.__file_infos = None
        
        
    def get_uploads(self, field_name=None):
        """Get uploads sent to this handler.
    
        Args:
          field_name: Only select uploads that were sent as a specific field.
    
        Returns:
          A list of BlobInfo records corresponding to each upload.
          Empty list if there are no blob-info records for field_name.
        """
        if self.__uploads is None:
          self.__uploads = collections.defaultdict(list)
          for key, value in self.request.params.items():
            if isinstance(value, cgi.FieldStorage):
              if 'blob-key' in value.type_options:
                self.__uploads[key].append(blobstore.parse_blob_info(value))
    
        if field_name:
          return list(self.__uploads.get(field_name, []))
        else:
          results = []
          for uploads in self.__uploads.itervalues():
            results.extend(uploads)
          return results

    def get_file_infos(self, field_name=None):
        """Get the file infos associated to the uploads sent to this handler.
    
        Args:
          field_name: Only select uploads that were sent as a specific field.
            Specify None to select all the uploads.
    
        Returns:
          A list of FileInfo records corresponding to each upload.
          Empty list if there are no FileInfo records for field_name.
        """
        if self.__file_infos is None:
          self.__file_infos = collections.defaultdict(list)
          for key, value in self.request.params.items():
            if isinstance(value, cgi.FieldStorage):
              if 'blob-key' in value.type_options:
                self.__file_infos[key].append(blobstore.parse_file_info(value))
    
        if field_name:
          return list(self.__file_infos.get(field_name, []))
        else:
          results = []
          for uploads in self.__file_infos.itervalues():
            results.extend(uploads)
          return results    
 
        
    def initialize(self, request, response):
        super(Handler, self).initialize(request, response)
        # this class is helper class used to retrieve data from GET and POST
        # its just bunch of shorthands that are useful for parsing input
        self.reqdata = RequestData(self.request)
        
        for param in self.request.params.items():
            # register all blobs that got uploaded
            # ndb.BlobManager.field_storage_unused_blob(param)
            pass
        
  
    def send_json(self, data):
        """ sends `data` to json format, accepts anything json compatible """
        ent = 'application/json;charset=utf-8'
        if self.response.headers.get('Content-Type') != ent:
           self.response.headers['Content-Type'] = ent
        self.response.write(json.dumps(data, indent=2, cls=JSONEncoderHTML))
     
    def is_post(self):
        """
        Checks if current request is post method
        """
        return self.request.method == 'POST'
    
    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)
    
    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.
        rv = self.jinja2.render_template(_template, **context)
        self.response.write(rv) 
  
    def render(self, tpl, data=None):
        if data == None:
           data = {}
        self.template.update(data)
        return self.render_response(tpl, **self.template)
    
    def before(self):
        """
        This function is fired just before the handler, usefull for setting variables
        """
        pass
    
    def after(self):
        """
        This function is fired just after the handler is executed
        """
        pass
    
    def get(self, *args, **kwargs):
        return self.respond(*args, **kwargs)
        
    def post(self, *args, **kwargs):
        return self.respond(*args, **kwargs)
        
    def respond(self, *args, **kwargs):
        self.abort(404)
        self.response.write('<h1>404 Not found</h1>')
 
    def dispatch(self):
        
        if self.LOAD_CURRENT_USER:
           auth.User.login_from_authorization_code(self.request.cookies.get('auth'))
 
        try:
            self.before()
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
            
            self.after()
            
        finally:
            
            # delete all blobs that did not got used in the application execution
            # ndb.BlobManager.delete_unused_blobs()
            
            # support the core's locals, and release them upon request complete
            _local.__release_local__()
         
 
     
class Segments(Handler):
      """
       Segments handler behaves in the way that you can construct multi-function "view"
      """
      def respond(self, *args, **kwargs):
          segment = kwargs.pop('segment')
          f = 'segment_%s' % segment
          if hasattr(self, f):
             return getattr(self, f)(*args, **kwargs)
         
         
class Angular(Handler):
    
     # angular handles data differently, `respond` method can return value and that value will be force-set into self.data
    
      def get(self, *args, **kwargs):
        data = self.respond(*args, **kwargs)
        if data:
           self.data['data'] = data
        
      def post(self, *args, **kwargs):
        data = self.respond(*args, **kwargs)
        if data:
           self.data['data'] = data
 
      def after(self):
          if self.request.headers.get('X-Requested-With', '').lower() ==  'xmlhttprequest' or self.request.get('force_ajax'):
             if not self.data:
                self.data = {}
                if self.response.status == 200:
                   self.response.status = 204
             self.send_json(self.data)
             return
         
          self.render('angular/index.html', {'initdata' : self.data})
          
          
class AngularSegments(Segments, Angular):
      pass
