# -*- coding: utf-8 -*-
'''
Created on May 13, 2014

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

from xml.etree import ElementTree

import orm


class CountryUpdateWrite(orm.BaseModel):

  cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

  def run(self, context):
    if not isinstance(self.cfg, dict):
      self.cfg = {}
    update_file_path = self.cfg.get('file', None)
    production_environment = self.cfg.get('prod_env', False)
    if not update_file_path:
      raise orm.TerminateAction()
    Country = context.models['12']
    CountrySubdivision = context.models['13']
    with file(update_file_path) as f:
      tree = ElementTree.fromstring(f.read())
      root = tree.findall('data')
      put_entities = []

      def make_complete_name_for_subdivision(entity, parent_id, process):
        path = entity
        names = []
        while True:
          parent = None
          parent_key = getattr(path, 'parent_record')
          if parent_key:
            parent = process.get(parent_key.urlsafe())
          if not parent:
            names.append(getattr(path, 'name'))
            break
          else:
            names.append(getattr(path, 'name'))
            path = parent
        names.reverse()
        return unicode(' / ').join(names)

      i = 0
      for child in root[1]:
        i += 1
        dic = dict()
        dic['id'] = child.attrib['id']
        for sub_child in child:
          name = sub_child.attrib.get('name')
          if name is None:
            continue
          if sub_child.text:
            dic[name] = sub_child.text
        country = Country(name=dic['name'], id=dic['id'], code=dic['code'], active=True)
        country._use_rule_engine = False
        put_entities.append(country)
      processed_keys = {}
      processed_ids = {}
      i = 0
      for child in [c for c in root[2]] + [c for c in root[3]]:
        i += 1
        dic = dict()
        dic['id'] = child.attrib['id']
        for sub_child in child:
          name = sub_child.attrib.get('name')
          if name is None:
            continue
          if sub_child.text:
            dic[name] = sub_child.text
          if 'ref' in sub_child.attrib:
            dic[name] = sub_child.attrib['ref']
        country_sub_division_values = dict(name=dic['name'], id=dic['id'], type=dic['type'], code=dic['code'], active=True)
        if 'country' in dic:
          country_sub_division_values['parent'] = Country.build_key(dic['country'])
        if 'parent' in dic:
          parent = processed_ids.get(dic['parent'])
          if parent:
            country_sub_division_values['parent_record'] = parent.key
        country_sub_division = CountrySubdivision(**country_sub_division_values)
        country_sub_division.complete_name = ''
        if 'parent' in dic:
          country_sub_division.complete_name = make_complete_name_for_subdivision(country_sub_division, dic['parent'], processed_keys)
        processed_keys[country_sub_division.key_urlsafe] = country_sub_division
        processed_ids[dic['id']] = country_sub_division
        country_sub_division._use_rule_engine = False
        put_entities.append(country_sub_division)
        if i == 100:  # all instances nowonly import 100 items
          break
      orm.put_multi(put_entities)
