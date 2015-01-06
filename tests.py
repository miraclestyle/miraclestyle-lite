import datetime
import calendar

def subtract_one_month(dt0):
    dt1 = dt0.replace(days=1)
    dt2 = dt1 - datetime.timedelta(days=1)
    dt3 = dt2.replace(days=1)
    return dt3

today = datetime.datetime.now()
start_of_this_month = datetime.datetime(today.year, today.month, today.day)
year_start = start_of_this_month - datetime.timedelta(days=365)
gets = start_of_this_month
for i in xrange(0, 12):
  print gets
  first = datetime.date(day=1, month=gets.month, year=gets.year)
  lastMonth = first - datetime.timedelta(days=1)
  gets = datetime.datetime(lastMonth.year, lastMonth.month, 1)