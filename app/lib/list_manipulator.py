# -*- coding: utf-8 -*-
'''
Created on May 31, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app.lib.attribute_manipulator import get_attr
 
def sort_by_list(for_sorting, sort_list, field):
  total = len(for_sorting)+1
  to_delete = []
  def sorting_function(item):
    try:
      ii = sort_list.index(get_attr(item, field))+1
    except ValueError as e:
      to_delete.append(item)
      ii = total
    return ii
  return (sorted(for_sorting, key=sorting_function), to_delete)