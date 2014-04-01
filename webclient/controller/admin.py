# -*- coding: utf-8 -*-
'''
Created on Feb 26, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient import handler
    
handler.register((r'/admin/search/<kind>/<filter>', handler.AngularBlank, 'admin'))