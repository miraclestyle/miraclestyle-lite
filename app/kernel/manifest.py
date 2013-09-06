# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json

from app.routes import register
from app.core import JSONEncoderForHTML

# DEFINE ROUTES FOR THIS MODULE

ROUTES = register('app.kernel.controller',
     (r'/app.js', 'AppConfig', 'appconfig'),
     (r'/login/<segment>', 'Login', 'login'),
     (r'/login/<segment>/<provider>', 'Login', 'login'),
)

# DEFINE FILTERS FOR THIS MODULE

def to_json(s):
    return json.dumps(s, cls=JSONEncoderForHTML)

def from_json(s):
    return json.loads(s)
  
JINJA_FILTERS = (
    to_json,
    from_json,
)