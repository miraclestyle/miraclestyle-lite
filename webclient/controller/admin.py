# -*- coding: utf-8 -*-
'''
Created on Feb 26, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webclient import handler

from app.srv import io

class Admin(handler.AngularSegments):
  
  def segment_apps(self):
 
      data = self.get_input()
      data.update({
                   'action_model' : 'srv.auth.Domain',
                   'action_key' : 'sudo_search',   
                  })

      output = io.Engine.run(data)  
 
      return output  
  
  def segment_users(self):
 
      data = self.get_input()
      data.update({
                   'action_model' : 'srv.auth.User',
                   'action_key' : 'sudo_search',   
                  })

      output = io.Engine.run(data)  
 
      return output

    
handler.register((r'/admin/<segment>', Admin, 'admin'))