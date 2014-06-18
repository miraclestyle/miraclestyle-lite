import cProfile, pstats, StringIO, time
pr = cProfile.Profile()
pr.enable()
time.sleep(1.5)
pr.disable()
s = StringIO.StringIO()
sortby = 'cumulative'
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()
print s.getvalue()