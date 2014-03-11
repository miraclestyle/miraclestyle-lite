# -*- coding: utf-8 -*-
'''
Created on Mar 11, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient import handler

from app.srv import io

class Default(handler.Angular):
  
  def respond(self, *args, **kwds):
      return {}  
 
handler.register((r'/app/<app_id>', Default, 'app_view'),
                 (r'/app/<app_id>/search/<widget_id>/<filter>', Default, 'app_view_search'))