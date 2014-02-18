import math
total = 1000
list1 = range(0, total)
per_page = 12
pages = int(math.ceil(total / per_page))
 
for i in range(0, pages+1):
    print '%s:%s' % (i*per_page, per_page*(i+1))
    print list1[i*per_page:per_page*(i+1)]