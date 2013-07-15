# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import six
import sys
import os

from webapp2 import uri_for
from webapp2_extras import i18n
from jinja2 import FileSystemLoader, Environment

from app import settings
from app.core import import_module

# At compile time, cache the directories to search.
if not six.PY3:
    fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()

app_template_dirs = []
for a in settings.APPLICATIONS_INSTALLED:
    module = import_module(a)
    template_dir = os.path.join(os.path.dirname(module.__file__), 'templates')
    if os.path.isdir(template_dir):
       if not six.PY3:
          template_dir = template_dir.decode(fs_encoding)
       app_template_dirs.append(template_dir)
       
# It won't change, so convert it to a tuple to save memory.           
app_template_dirs = tuple(app_template_dirs)       

# global environment
env = Environment(extensions=['jinja2.ext.i18n'], loader=FileSystemLoader(app_template_dirs), autoescape=True, cache_size=settings.TEMPLATE_CACHE)
env.install_gettext_translations(i18n)
env.globals['settings'] = settings
env.globals['uri_for'] = uri_for


def render_template(f, data=None):
    if not data:
       data = dict()
    template = env.get_template(f)
    return template.render(data)