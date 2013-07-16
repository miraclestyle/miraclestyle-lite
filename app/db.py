# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

import json
import decimal

# Google Appengine Datastore
from google.appengine.ext.db import *

class Model(Model):
    
      def to_json(self):
          return to_dict(self)
    
      def loaded(self):
          return self.has_key()
  
SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)

def to_dict(model):
    output = {}

    for key, prop in model.properties().iteritems():
        value = getattr(model, key)

        if value is None or isinstance(value, SIMPLE_TYPES):
            output[key] = value
        elif isinstance(value, datetime.date):
            # Convert date/datetime to MILLISECONDS-since-epoch (JS "new Date()").
            ms = time.mktime(value.utctimetuple()) * 1000
            ms += getattr(value, 'microseconds', 0) / 1000
            output[key] = int(ms)
        elif isinstance(value, GeoPt):
            output[key] = {'lat': value.lat, 'lon': value.lon}
        elif isinstance(value, Model):
            output[key] = to_dict(value)
        else:
            raise ValueError('cannot encode ' + repr(prop))

    return output      
  
class DecimalProperty(Property):
  
  data_type = decimal.Decimal

  def get_value_for_datastore(self, model_instance):
    return str(super(DecimalProperty, self).get_value_for_datastore(model_instance))

  def make_value_from_datastore(self, value):
    return decimal.Decimal(value)

  def validate(self, value):
    value = super(DecimalProperty, self).validate(value)
    if value is None or isinstance(value, decimal.Decimal):
      return value
    elif isinstance(value, basestring):
      return decimal.Decimal(value)
    raise BadValueError("Property %s must be a Decimal or string." % self.name)    
   
class JSONProperty(TextProperty):
    
    def validate(self, value):
        return value

    def get_value_for_datastore(self, model_instance):
        result = super(JSONProperty, self).get_value_for_datastore(model_instance)
        result = json.dumps(result)
        return Text(result)

    def make_value_from_datastore(self, value):
        try:
            value = json.loads(str(value))
        except:
            pass

        return super(JSONProperty, self).make_value_from_datastore(value)