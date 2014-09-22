# -*- coding: utf-8 -*-
'''
Created on Feb 26, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from frontend import frontend_settings
from frontend import handler
    
frontend_settings.ROUTES.append((r'/sell/catalogs', handler.AngularBlank, 'admin'))