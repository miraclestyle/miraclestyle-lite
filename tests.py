import re

def format_value(value):
  def run_format(match):
    matches = match.groups()
    return 'Decimal("%s") %s' % (matches[0], matches[1])
    # this regex needs more work
  value = re.sub('unit\((.*)\,\s*(.*)\)', run_format, value)
  return value

print "print format_value('unit(100, kilogram)')"
print format_value('unit(100, kilogram)')

print "print format_value('unit(100.000,       meter)')"
print format_value('unit(100.000,       meter)')

print "print format_value('unit(143,kilogram)')"
print format_value('unit(143,kilogram)')