# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from xml.etree import ElementTree

from app import orm, util, settings  # @todo settings has to GET OUT OF HERE!!!


class CountryUpdateWrite(orm.BaseModel):
  
  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})
  
  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    update_file_path = self.cfg.get('file', None)
    if not update_file_path:
      raise orm.TerminateAction()
    Country = context.models['15']
    CountrySubdivision = context.models['16']
    with file(update_file_path) as f:
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
      
      i = 0
      for child in root[1]:
        i += 1
        dat = dict()
        dat['id'] = child.attrib['id']
        for child2 in child:
          name = child2.attrib.get('name')
          if name is None:
            continue
          if child2.text:
            dat[name] = child2.text
        to_put.append(Country(name=dat['name'], id=dat['id'], code=dat['code'], active=True))
        if i == 100 and settings.DEBUG:
          break
      processed_keys = {}
      processed_ids = {}
      i = 0
      for child in [c for c in root[2]] + [c for c in root[3]]:
        i += 1
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
        kw = dict(name=dat['name'], id=dat['id'], type=dat['type'], code=dat['code'], active=True)
        if 'country' in dat:
          kw['parent'] = Country.build_key(dat['country'])
        if 'parent' in dat:
          parent = processed_ids.get(dat['parent'])
          if parent:
            kw['parent_record'] = parent.key
        new_sub_divison = CountrySubdivision(**kw)
        new_sub_divison.complete_name = ''
        if 'parent' in dat:
          new_sub_divison.complete_name = make_complete_name_for_subdivision(new_sub_divison, dat['parent'], processed_keys)
        processed_keys[new_sub_divison.key_urlsafe] = new_sub_divison
        processed_ids[dat['id']] = new_sub_divison
        new_sub_divison._use_rule_engine = False
        to_put.append(new_sub_divison)
        if i == 100 and settings.DEBUG:
          break
      orm.put_multi(to_put)
