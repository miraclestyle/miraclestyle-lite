class Foo():
  
  def __init__(self, id):
    self.id = id
    
  def __repr__(self):
    return str(self)
    
  def __str__(self):
    return 'Foo-%s' % self.id
    

sorting_list = [
"3",
"1",
"4",
"2",
"5",
]
 

foos = [Foo(id='1'), Foo(id='2'), Foo(id='3'), Foo(id='4'), Foo(id='5'), Foo(id='6')]
total = len(foos)+1
delete_items = []

def sortem(i):
  try:
    ii = sorting_list.index(i.id)+1
  except ValueError as e:
    delete_items.append(i)
    ii = total
  return ii

print sorted(foos, key=sortem)
print 'to delete', delete_items
print 'after sort', foos