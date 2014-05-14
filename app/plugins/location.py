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
      
      def make_complete_name_for_subdivision(entity, parent_id, process):
        separator = unicode(' / ')
        parent_property = 'parent_record'
        name_property = 'name'
        path = entity
        names = []
        while True:
          parent = None
          if parent_property is None:
            parent_key = path.key.parent()
            parent = parent_key.get()
          else:
            parent_key = getattr(path, parent_property)
            if parent_key:
              parent = process.get(parent_key.urlsafe())
          if not parent:
            names.append(getattr(path, name_property))
            break
          else:
            names.append(getattr(path, name_property))
            path = parent
        names.reverse()
        return separator.join(names)
      
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
      
      processed_keys = {}
      processed_ids = {}
      for child in [c for c in root[2]] + [c for c in root[3]]:
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
            
        
        kw = dict(name=dat['name'], id=dat['id'], type=CountrySubdivision.TYPES.get(dat['type'], 1), code=dat['code'], active=True)
        
        if 'country' in dat:
          kw['parent'] = Country.build_key(dat['country'])
        
        if 'parent' in dat:
          parent = processed_ids.get(dat['parent'])
          if parent:
            kw['parent_record'] = parent.key
           
        new_sub_divison = CountrySubdivision(**kw)
         
        if 'parent' in dat:
          new_sub_divison.complete_name = make_complete_name_for_subdivision(new_sub_divison, dat['parent'], processed_keys)
          
        processed_keys[new_sub_divison.key_urlsafe] = new_sub_divison
        processed_ids[dat['id']] = new_sub_divison
      
        to_put.append(new_sub_divison)
      
      ndb.put_multi(to_put)
          
      Country._use_memcache = False
      Country._use_cache = False
      
      CountrySubdivision._use_memcache = False
      CountrySubdivision._use_cache = False
                      
      