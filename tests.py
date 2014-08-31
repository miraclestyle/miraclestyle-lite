# -*- coding: utf-8 -*-
'''
Created on Jul 8, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import uuid
a = []
for x in xrange(10000):
  i = str(uuid.uuid4())
  if i in a:
    print 'collision! at %s with %s' % (x, i)
    break
  a.append(i)
a = None