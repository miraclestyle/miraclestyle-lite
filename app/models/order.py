# -*- coding: utf-8 -*-
'''
Created on Aug 30, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from app import orm, util, settings


class OrderLineTax(orm.BaseModel):
  
  _kind = 116
  
  _use_rule_engine = False
  
  name = orm.SuperStringProperty('1', required=True, indexed=False)
  code = orm.SuperStringProperty('2', required=True, indexed=False)
  formula = orm.SuperPickleProperty('3', required=True, indexed=False)


class OrderLine(orm.BaseExpando):
  
  _kind = 51
  
  _use_rule_engine = False
  
  sequence = orm.SuperIntegerProperty('1', required=True)
  description = orm.SuperTextProperty('2', required=True)
  product_reference = orm.SuperKeyProperty('3', kind='38', required=True, indexed=False)
  product_variant_signature = orm.SuperJsonProperty('4', required=True)
  product_category_complete_name = orm.SuperTextProperty('5', required=True)
  product_category_reference = orm.SuperKeyProperty('6', kind='17', required=True, indexed=False)
  code = orm.SuperStringProperty('7', required=True, indexed=False)
  unit_price = orm.SuperDecimalProperty('8', required=True, indexed=False)
  product_uom = orm.SuperLocalStructuredProperty('19', '9', required=True)
  quantity = orm.SuperDecimalProperty('10', required=True, indexed=False)
  discount = orm.SuperDecimalProperty('11', required=True, indexed=False)
  taxes = orm.SuperLocalStructuredProperty('116', '12', repeated=True)
  subtotal = orm.SuperDecimalProperty('13', required=True, indexed=False)
  discount_subtotal = orm.SuperDecimalProperty('14', required=True, indexed=False)
  total = orm.SuperDecimalProperty('15', required=True, indexed=False)
  
  _default_indexed = False


class Order(orm.BaseExpando):
  
  _kind = xx
  
  created = orm.SuperDateTimeProperty('1', required=True, auto_now_add=True)
  updated = orm.SuperDateTimeProperty('2', required=True, auto_now=True)
  name = orm.SuperStringProperty('3', required=True)
  state = orm.SuperStringProperty('4', required=True)
  date = orm.SuperDateTimeProperty('5', required=True)
  seller = orm.SuperKeyProperty('6', kind='23', required=True, indexed=False)  # @todo buyer_reference ??
  company_address = orm.SuperLocalStructuredProperty('68', '7', required=True)
  billing_address_reference = orm.SuperKeyProperty('8', kind='9', required=True, indexed=False)
  shipping_address_reference = orm.SuperKeyProperty('9', kind='9', required=True, indexed=False)
  billing_address = orm.SuperLocalStructuredProperty('68', '10', required=True)
  shipping_address = orm.SuperLocalStructuredProperty('68', '11', required=True)
  currency = orm.SuperLocalStructuredProperty('19', '12', required=True)
  untaxed_amount = orm.SuperDecimalProperty('13', required=True, indexed=False)
  tax_amount = orm.SuperDecimalProperty('14', required=True, indexed=False)
  total_amount = orm.SuperDecimalProperty('15', required=True, indexed=False)
  paypal_reciever_email = orm.SuperStringProperty('16', required=True, indexed=False)
  paypal_business = orm.SuperStringProperty('17', required=True, indexed=False)
  
  _default_indexed = False
  
  _virtual_fields = {
    '_lines': orm.SuperRemoteStructuredProperty(OrderLine, repeated=True),
    '_records': orm.SuperRecordProperty('xx')
    }

