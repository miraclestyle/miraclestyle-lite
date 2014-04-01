# -*- coding: utf-8 -*-
'''
Created on Mar 11, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient import handler

from app.srv import io
 
handler.register((r'/app/<app_id>', handler.AngularBlank, 'app_view'),
                 (r'/app/<app_id>/search/<kind>/<filter>', handler.AngularBlank, 'app_view_search'))