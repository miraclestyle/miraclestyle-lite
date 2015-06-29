# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import sys
import logging
import pdb
import traceback

import settings

__all__ = ['noop', 'debug', 'log', 'trace']


def noop(*args, **kwargs):
  pass


class LoggingWrapper(object):

  def __getattr__(self, name, default=None):
    if name and name.startswith('_'):
      return super(LoggingWrapper, self).__getattr__(self, name, default)
    if settings.DO_LOGS:
      logger = getattr(logging, name)
      if name == 'exception':
        def decide(error):
          if hasattr(error, 'LOG'):
            if error.LOG:
              return logger
            else:
              return noop
          # always log exceptions that do not have `LOG` constant
          return logger
        return decide
      return logger
    else:
      return noop

log = LoggingWrapper()


def debug():
  """ Enter pdb in App Engine

  Renable system streams for it.
  """
  pdb.Pdb(stdin=getattr(sys, '__stdin__'), stdout=getattr(
      sys, '__stderr__')).set_trace(sys._getframe().f_back)


def trace():
  traceback.print_stack()
