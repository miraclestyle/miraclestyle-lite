# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''
from .base import *
from .base import _BaseProperty

__all__ = ['SuperComputedProperty']


class SuperComputedProperty(_BaseProperty, ComputedProperty):
  pass
