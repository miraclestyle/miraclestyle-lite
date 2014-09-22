# -*- coding: utf-8 -*-
'''
Created on Feb 26, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from frontend import frontend_settings
from frontend.handler import base
    
frontend_settings.ROUTES.append((r'/sell/catalogs', base.AngularBlank, 'admin'))