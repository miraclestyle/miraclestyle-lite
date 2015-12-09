# -*- coding: utf-8 -*-
'''
Created on May 6, 2015

@authors:  Edis Sehalic (edis.sehalic@gmail.com), Elvin Kosova (elvinkosova@gmail.com)
'''

import time
import cStringIO
import cProfile
import pstats

from .debug import log

__all__ = ['Profile', 'profile', 'detail_profile', 'detail_profile_stop', 'detail_profile_start']


def compute(start):
  return round((time.time() - start) * 1000, 3)


class Profile():

  def __init__(self):
    self.start = time.time()

  @property
  def miliseconds(self):
    return compute(self.start)


def profile(message=None):
  def decorator(func):
    def inner(*args, **kwargs):
      start = time.time()
      result = func(*args, **kwargs)
      log.debug(message % (func.__name__, compute(start)))
      return result
    return inner
  return decorator

def detail_profile_start():
  profiler = cProfile.Profile()
  profiler.enable()
  return profiler

def detail_profile_stop(profiler, limit=None):
  profiler.disable()
  string_io = cStringIO.StringIO()
  stats = pstats.Stats(profiler, stream=string_io).sort_stats('cumulative')
  stats.print_stats(limit)
  return string_io

def detail_profile(message=None, limit=None, satisfy=None, logger=None):
  def decorator(func):
    def inner(*args, **kwargs):
      ctime = Profile()
      profiler = cProfile.Profile()
      profiler.enable()
      result = func(*args, **kwargs)
      profiler.disable()
      if satisfy is not None:
        if not satisfy(profiler, ctime):
          return
      string_io = cStringIO.StringIO()
      stats = pstats.Stats(profiler, stream=string_io).sort_stats('cumulative')
      stats.print_stats(limit)
      getattr(log, 'debug' if logger is None else logger)(message % (func.__name__, string_io.getvalue()))
      return result
    return inner
  return decorator
