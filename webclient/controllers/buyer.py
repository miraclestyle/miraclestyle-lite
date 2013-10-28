# -*- coding: utf-8 -*-
'''
Created on Oct 27, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import core

from webclient.route import register
from webclient.handler import Angular

class BuyerAddressList(Angular):
    
    def respond(self):
        return core.buyer.Address.list()

class BuyerAddressManage(Angular):
    
    def respond(self):
        args = ('id', 'name', 'country', 'city', 'postal_code', 'street_address',
                'default_shipping', 'default_billing', 'region', 'street_address2',
                'email', 'telephone')
        return core.buyer.Address.manage(**self.reqdata.get_all(args))
    
class BuyerAddressDelete(Angular):
    
    def respond(self):
        return core.buyer.Address.delete(**self.reqdata.get_all(('id', )))
    
    
register(('/buyer_address/list', BuyerAddressList, 'buyer_list'),
         ('/buyer_address/manage', BuyerAddressManage, 'buyer_manage'),
         ('/buyer_address/delete', BuyerAddressDelete, 'buyer_delete'))