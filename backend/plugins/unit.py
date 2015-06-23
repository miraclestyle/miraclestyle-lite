# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
from decimal import Decimal
from xml.etree import ElementTree

import orm


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

      def __text(item, key):
        value = item.get(key)
        if value is not None:
          if value.text == 'None' or value.text is None:
            return None
          return str(value.text)
        return value

      def __eval(item, key):
        value = item.get(key)
        if value == 'None':
          value = None
        if value is not None:
          evaled = value.attrib.get('eval')
          if evaled == 'None' or evaled is None:
            return None
          return eval(evaled)
        return value

      for child in root[1]:
        if child.attrib.get('model') == 'currency.currency':
          uom = {'id': child.attrib.get('id')}
          uom_data = {}
          for sub_child in child:
            uom_data[sub_child.attrib.get('name')] = sub_child
          rounding = uom_data.get('rounding')
          digits = uom_data.get('digits')
          grouping = uom_data.get('mon_grouping')
          if rounding is not None:
            rounding = Decimal(eval(rounding.attrib.get('eval')))
          if digits is not None:
            digits = long(eval(digits.attrib.get('eval')))
          if grouping is not None:
            grouping = eval(grouping.text)
          else:
            grouping = []
          if digits is None:
            digits = 3
          uom.update({
              'measurement': 'Currency',
              'name': uom_data['name'].text,
              'code': uom_data['code'].text,
              'numeric_code': uom_data['numeric_code'].text,
              'symbol': uom_data['symbol'].text,
              'rounding': rounding,
              'digits': digits,
              'grouping': grouping,
              'decimal_separator': __text(uom_data, 'mon_decimal_point'),
              'thousands_separator': __text(uom_data, 'mon_thousands_sep'),
              'positive_sign_position': __eval(uom_data, 'p_sign_posn'),
              'negative_sign_position': __eval(uom_data, 'n_sign_posn'),
              'positive_sign': __text(uom_data, 'positive_sign'),
              'negative_sign': __text(uom_data, 'negative_sign'),
              'positive_currency_symbol_precedes': __eval(uom_data, 'p_cs_precedes'),
              'negative_currency_symbol_precedes': __eval(uom_data, 'n_cs_precedes'),
              'positive_separate_by_space': __eval(uom_data, 'p_sep_by_space'),
              'negative_separate_by_space': __eval(uom_data, 'n_sep_by_space'),
              'active': True
          })
          uoms.append(uom)
      put_entities = [Unit(**d) for d in uoms]
      for entity in put_entities:
        entity._use_rule_engine = False
      orm.put_multi(put_entities)


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
          for sub_child in child:
            name = sub_child.text
          measurements[child.attrib.get('id')] = name
      for child in root[0]:
        if child.attrib.get('model') == 'product.uom':
          uom = {'id': child.attrib.get('id')[4:]}
          uom_data = {}
          for sub_child in child:
            uom_data[sub_child.attrib.get('name')] = sub_child
          rounding = uom_data.get('rounding')
          digits = uom_data.get('digits')
          if rounding is not None:
            rounding = Decimal(eval(rounding.attrib.get('eval')))
          if digits is not None:
            digits = long(eval(digits.attrib.get('eval')))
          if digits is None:
            digits = 3
          uom.update({'name': uom_data['name'].text,
                      'active': True,
                      'symbol': uom_data['symbol'].text,
                      'measurement': measurements.get(uom_data['category'].attrib.get('ref')),
                      'factor': Decimal(eval(uom_data['factor'].attrib.get('eval'))),
                      'rate': Decimal(eval(uom_data['rate'].attrib.get('eval'))),
                      'rounding': rounding,
                      'digits': digits})
          uoms.append(uom)
      put_entities = [Unit(**d) for d in uoms]
      for entity in put_entities:
        entity._use_rule_engine = False
      orm.put_multi(put_entities)


class UnitRemoveCurrencies(orm.BaseModel):

  def run(self, context):
    context._entities = filter(lambda x: x.measurement != 'Currency', context._entities)
