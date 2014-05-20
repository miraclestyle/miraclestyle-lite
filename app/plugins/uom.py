# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from decimal import Decimal
from xml.etree import ElementTree

from app import ndb, settings, memcache, util
from app.srv import event
from app.lib.attribute_manipulator import set_attr, get_attr

def cache_control(decide):
  
  # dry method of enable/disable context/memcache for faster puts
  
  from app.srv.uom import Measurement, Unit
  
  Measurement._use_memcache = decide
  Measurement._use_cache = decide
    
  Unit._use_memcache = decide
  Unit._use_cache = decide
      
class CurrencyUpdate(event.Plugin):
  
  def run(self, context):
    
    from app.srv.uom import Measurement, Unit
    
    cache_control(False)
    
    with file(settings.CURRENCY_DATA_FILE) as f:
      tree = ElementTree.fromstring(f.read())
      root = tree.findall('data')
      measurements = [{'name' : 'Currency', 'id' : 'currency'}]
      uoms = []
      
      def __text(item, key, op=None):
        if op == None:
          op = str
        gets = item.get(key)
        if gets != None:
          return op(gets.text)
        return gets
      
      def __eval(item, key):
        gets = item.get(key)
        if gets != None:
          return eval(gets.attrib.get('eval'))
        return gets
            
      for child in root[1]:
    
        if child.attrib.get('model') == 'currency.currency':
          
           new_uom = {'id' : child.attrib.get('id')}
           new_uom_data = {}
           for child2 in child:
             new_uom_data[child2.attrib.get('name')] = child2
             
           rounding = new_uom_data.get('rounding')
           digits = new_uom_data.get('digits')
           grouping = new_uom_data.get('mon_grouping')
          
           if rounding != None:
              rounding = Decimal(eval(rounding.attrib.get('eval')))
           if digits != None:
              digits = long(eval(digits.attrib.get('eval')))
           if grouping != None:
             grouping = eval(grouping.text)
           else:
             grouping = []
       
           new_uom.update({
             'parent' : Measurement.build_key('currency'),
             'name' : new_uom_data['name'].text,
             'code' : new_uom_data['code'].text,
             'numeric_code' : new_uom_data['numeric_code'].text,
             'symbol' : new_uom_data['symbol'].text,
             'rounding' : rounding,
             'digits' : digits,
             'grouping' : grouping,
             'decimal_separator' : __text(new_uom_data, 'mon_decimal_point'),
             'thousands_separator' : __text(new_uom_data, 'mon_thousands_sep'),
             'positive_sign_position' : __eval(new_uom_data, 'p_sign_posn'),
             'negative_sign_position' : __eval(new_uom_data, 'n_sign_posn'),
             'positive_sign' : __text(new_uom_data, 'positive_sign'),
             'negative_sign' : __text(new_uom_data, 'negative_sign'),
             'positive_currency_symbol_precedes' : __eval(new_uom_data, 'p_cs_precedes'),
             'negative_currency_symbol_precedes' : __eval(new_uom_data, 'n_cs_precedes'),
             'positive_separate_by_space' : __eval(new_uom_data, 'p_sep_by_space'),
             'negative_separate_by_space' : __eval(new_uom_data, 'n_sep_by_space'),
             'active' : True,
           })
           uoms.append(new_uom)
           
      ndb.put_multi([Measurement(**d) for d in measurements] + [Unit(**d) for d in uoms])    
      
      cache_control(True)
           
class UnitUpdate(event.Plugin):
  
  def run(self, context):
    
    from app.srv.uom import Measurement, Unit
    
    cache_control(False)
    
    with file(settings.UOM_DATA_FILE) as f:
      tree = ElementTree.fromstring(f.read())
      root = tree.findall('data')
      measurements = []
      uoms = []
      for child in root[0]:
        if child.attrib.get('model') == 'product.uom.category':
          the_id = child.attrib.get('id')[8:]
          new_uom_category = {'id' : the_id}
          for child2 in child:
            new_uom_category['name'] = child2.text
          measurements.append(new_uom_category)
          
        if child.attrib.get('model') == 'product.uom':
           new_uom = {'id' : child.attrib.get('id')[4:]}
           new_uom_data = {}
           for child2 in child:
             new_uom_data[child2.attrib.get('name')] = child2
           
           rounding = new_uom_data.get('rounding')
           digits = new_uom_data.get('digits')
           if rounding != None:
              rounding = Decimal(eval(rounding.attrib.get('eval')))
           if digits != None:
              digits = long(eval(digits.attrib.get('eval')))
              
           new_uom.update({'name' : new_uom_data['name'].text, 
                           'active' : True,
                           'symbol' : new_uom_data['symbol'].text,
                           'parent' : Measurement.build_key(new_uom_data['category'].attrib.get('ref')[8:]),
                           'factor' : Decimal(eval(new_uom_data['factor'].attrib.get('eval'))),
                           'rate' : Decimal(eval(new_uom_data['rate'].attrib.get('eval'))),
                           'rounding' : rounding,
                           'digits' : digits,
                           })
           uoms.append(new_uom)
           
      ndb.put_multi([Measurement(**d) for d in measurements] + [Unit(**d) for d in uoms])
      
      cache_control(True)
      
      
class RemoveCurrencies(event.Plugin):
  
  def run(self, context):
    for i,entity in enumerate(context.entities):
      if entity.key.parent().id() == 'currency':
        context.entities.remove(entity)