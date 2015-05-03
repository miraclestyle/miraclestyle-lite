# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from decimal import Decimal
from xml.etree import ElementTree

import orm
from util import *


class UnitCurrencyUpdateWrite(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    update_file_path = self.cfg.get('file', None)
    if not update_file_path:
      raise orm.TerminateAction()
    Unit = context.models['17']
    with file(update_file_path) as f:
      tree = ElementTree.fromstring(f.read())
      root = tree.findall('data')
      uoms = []
      
      def __text(item, key, op=None):
        if op == None:
          op = str
        gets = item.get(key)
        if gets != None:
          if gets.text == 'None' or gets.text is None:
            return None
          return op(gets.text)
        return gets
      
      def __eval(item, key):
        gets = item.get(key)
        if gets == 'None':
          gets = None
        if gets != None:
          evaled = gets.attrib.get('eval')
          if evaled == 'None' or evaled is None:
            return None
          return eval(evaled)
        return gets
      
      for child in root[1]:
        if child.attrib.get('model') == 'currency.currency':
          new_uom = {'id': child.attrib.get('id')}
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
          if digits is None:
            digits = 3
          new_uom.update({
            'measurement': 'Currency',
            'name': new_uom_data['name'].text,
            'code': new_uom_data['code'].text,
            'numeric_code': new_uom_data['numeric_code'].text,
            'symbol': new_uom_data['symbol'].text,
            'rounding': rounding,
            'digits': digits,
            'grouping': grouping,
            'decimal_separator': __text(new_uom_data, 'mon_decimal_point'),
            'thousands_separator': __text(new_uom_data, 'mon_thousands_sep'),
            'positive_sign_position': __eval(new_uom_data, 'p_sign_posn'),
            'negative_sign_position': __eval(new_uom_data, 'n_sign_posn'),
            'positive_sign': __text(new_uom_data, 'positive_sign'),
            'negative_sign': __text(new_uom_data, 'negative_sign'),
            'positive_currency_symbol_precedes': __eval(new_uom_data, 'p_cs_precedes'),
            'negative_currency_symbol_precedes': __eval(new_uom_data, 'n_cs_precedes'),
            'positive_separate_by_space': __eval(new_uom_data, 'p_sep_by_space'),
            'negative_separate_by_space': __eval(new_uom_data, 'n_sep_by_space'),
            'active': True
            })
          uoms.append(new_uom)
      to_put = [Unit(**d) for d in uoms]
      for entity in to_put:
        entity._use_rule_engine = False
      orm.put_multi(to_put)


class UnitUpdateWrite(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    update_file_path = self.cfg.get('file', None)
    if not update_file_path:
      raise orm.TerminateAction()
    Unit = context.models['17']
    with file(update_file_path) as f:
      tree = ElementTree.fromstring(f.read())
      root = tree.findall('data')
      measurements = {}
      uoms = []
      for child in root[0]:
        if child.attrib.get('model') == 'product.uom.category':
          for child2 in child:
            name = child2.text
          measurements[child.attrib.get('id')] = name
      for child in root[0]:
        if child.attrib.get('model') == 'product.uom':
          new_uom = {'id': child.attrib.get('id')[4:]}
          new_uom_data = {}
          for child2 in child:
            new_uom_data[child2.attrib.get('name')] = child2
          rounding = new_uom_data.get('rounding')
          digits = new_uom_data.get('digits')
          if rounding != None:
            rounding = Decimal(eval(rounding.attrib.get('eval')))
          if digits != None:
            digits = long(eval(digits.attrib.get('eval')))
          if digits is None:
            digits = 3
          new_uom.update({'name': new_uom_data['name'].text,
                          'active': True,
                          'symbol': new_uom_data['symbol'].text,
                          'measurement': measurements.get(new_uom_data['category'].attrib.get('ref')),
                          'factor': Decimal(eval(new_uom_data['factor'].attrib.get('eval'))),
                          'rate': Decimal(eval(new_uom_data['rate'].attrib.get('eval'))),
                          'rounding': rounding,
                          'digits': digits})
          uoms.append(new_uom)
      to_put = [Unit(**d) for d in uoms]
      for entity in to_put:
        entity._use_rule_engine = False
      orm.put_multi(to_put)


class UnitRemoveCurrencies(orm.BaseModel):
  
  def run(self, context):
    context._entities = filter(lambda x: x.measurement != 'Currency', context._entities)
