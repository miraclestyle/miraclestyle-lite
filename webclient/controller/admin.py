# -*- coding: utf-8 -*-
'''
Created on Feb 26, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient import handler

from app.srv import io

class Admin(handler.AngularSegments):
  
  def segment_apps(self):
      pass
  
  def segment_users(self):
      pass

    
handler.register((r'/admin/<segment>', Admin, 'admin'))