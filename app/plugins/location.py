# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from xml.etree import ElementTree

from app import ndb, settings, util
from app.srv import event


class CountryUpdate(event.Plugin):
  
  def run(self, context):
    
    # parses currency.xml from etc/data folder.
    # the .xml must be a source from tryton for now.
    # we could migrate to .json for better readability, but let it be as it is for now
    
    from app.srv.location import Country, CountrySubdivision
    
    # makes life easier for context cache
    
    Country._use_memcache = False
    Country._use_cache = False
    
    CountrySubdivision._use_memcache = False
    CountrySubdivision._use_cache = False
 
    with file(settings.LOCATION_DATA_FILE) as f:
      tree = ElementTree.fromstring(f.read())
      root = tree.findall('data')
      
      to_put = []
      
      for child in root[1]:
        dat = dict()
        dat['id'] = child.attrib['id']
        for child2 in child:
          name = child2.attrib.get('name')
          if name is None:
            continue
          if child2.text:
            dat[name] = child2.text
            
        to_put.append(Country(name=dat['name'], id=dat['id'], code=dat['code'], active=True))
      
      for child in root[2]:
        dat = dict()
        dat['id'] = child.attrib['id']
        for child2 in child:
          k = child2.attrib.get('name')
          if k is None:
            continue
          if child2.text:
            dat[k] = child2.text
          if 'ref' in child2.attrib:
            dat[k] = child2.attrib['ref']
        
        kw = dict(name=dat['name'], id=dat['id'], type=CountrySubdivision.TYPES.get(dat['type'], 'unknown'), code=dat['code'], active=True)
        
        if 'country' in dat:
          kw['parent'] = Country.build_key(dat['country'])
        
        if 'parent' in dat:
          kw['parent_record'] = CountrySubdivision.build_key(dat['parent'])
        
        to_put.append(CountrySubdivision(**kw))
      
      total = len(to_put)
      offset = 50
      by = (total / offset) + 2
      util.logger('Total countries to process: %s. Separated into %s batches.' % (total, by))
      start = 0
      for __ in range(0, by):
        # do the protobuffs 50 at the time, not 4020 at once because it causes extremely high cpu usage.
        end = start+offset
        get = to_put[start:end]
        util.logger('Offset at %s:%s. Found: %s items.' % (end, offset, len(get)))
        if get:
          ndb.put_multi(get)
          start += offset
          
      Country._use_memcache = False
      Country._use_cache = False
      
      CountrySubdivision._use_memcache = False
      CountrySubdivision._use_cache = False
                      
      