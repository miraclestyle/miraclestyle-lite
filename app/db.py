# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''

# Google Appengine Datastore
from google.appengine.ext.db import *

class Model(Model):
    
      def loaded(self):
          return self.has_key()