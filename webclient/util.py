# -*- coding: utf-8 -*-
'''
Created on Oct 8, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import imp
import os
import json
 
from app import core

from webapp2_extras import sessions

class Jinja():
    
    filters = {}
    globals = {}
    
    @classmethod
    def register_filter(cls, name, funct):
        cls.filters[name] = funct
    
    @staticmethod
    def register_global(cls, name, value):
        cls.globals[name] = value
 
class JSONEncoderHTML(json.JSONEncoder):
    """An encoder that produces JSON safe to embed in HTML.

    To embed JSON content in, say, a script tag on a web page, the
    characters &, < and > should be escaped. They cannot be escaped
    with the usual entities (e.g. &amp;) because they are not expanded
    within <script> tags.
    """
    
    def default(self, o):
        if hasattr(o, '__json__'):
           return o.__json__()
        else:
           return json.JSONEncoder.default(self, o)
  
    def iterencode(self, o, _one_shot=False):
        chunks = super(JSONEncoderHTML, self).iterencode(o, _one_shot)
        for chunk in chunks:
            chunk = chunk.replace('&', '\\u0026')
            chunk = chunk.replace('<', '\\u003c')
            chunk = chunk.replace('>', '\\u003e')
            yield chunk
            


MODULE_EXTENSIONS = ('.py',)

def package_contents(package_name):
    file, pathname, description = imp.find_module(package_name)
    if file:
        raise ImportError('Not a package: %r', package_name)
    # Use a set because some may be both source and compiled.
    return set([os.path.splitext(module)[0]
        for module in os.listdir(pathname)
        if module.endswith(MODULE_EXTENSIONS)])
    

class DatastoreSessionFactory(sessions.CustomBackendSessionFactory):
    """A session factory that stores data serialized in datastore.

    To use datastore sessions, pass this class as the `factory` keyword to
    :meth:`webapp2_extras.sessions.SessionStore.get_session`::

        from webapp2_extras import sessions_ndb

        # [...]

        session = self.session_store.get_session(
            name='db_session', factory=sessions_ndb.DatastoreSessionFactory)

    See in :meth:`webapp2_extras.sessions.SessionStore` an example of how to
    make sessions available in a :class:`webapp2.RequestHandler`.
    """

    #: The session model class.
    session_model = core.acl.Session

    def _get_by_sid(self, sid):
        """Returns a session given a session id."""
        if self._is_valid_sid(sid):
            data = self.session_model.get_by_sid(sid)
            if data is not None:
                self.sid = sid
                data, updated = data
                self.session_updated = updated
                return sessions.SessionDict(self, data=data)

        self.sid = self._get_new_sid()
        return sessions.SessionDict(self, new=True)

    def save_session(self, response):
        if self.session is None or not self.session.modified:
            return

        self.session_model(id=self.sid, data=dict(self.session))._put()
        self.session_store.save_secure_cookie(
            response, self.name, {'_sid': self.sid}, **self.session_args)