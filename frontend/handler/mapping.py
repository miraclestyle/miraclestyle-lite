# -*- coding: utf-8 -*-
'''
Created on Feb 26, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
from handler import base
    
settings.ROUTES.extend(((r'/', base.AngularBlank, 'admin'),
                       (r'/sell/catalogs', base.AngularBlank, 'admin'),
                       (r'/admin/search/<kind>/<filter>', base.AngularBlank, 'admin')))