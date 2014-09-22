# -*- coding: utf-8 -*-
'''
Created on Sep 22, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from frontend import frontend_settings
from frontend.handler import base
    
frontend_settings.ROUTES.append((r'/', base.AngularBlank, 'admin'))