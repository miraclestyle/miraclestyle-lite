# -*- coding: utf-8 -*-
'''
Created on Feb 26, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient import handler
    
handler.register((r'/sell/catalogs', handler.AngularBlank, 'admin'))