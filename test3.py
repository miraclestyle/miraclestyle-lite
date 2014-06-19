def normalize(source):
  if isinstance(source, basestring):
    return [source]
  if isinstance(source, (list, tuple)):
    return source
  if isinstance(source, dict):
    return [v for k,v in source.items()]
  try:
    iterate = iter(source)
    return [item for item in iterate]
  except ValueError as e:
    pass
  finally:
    return [source]