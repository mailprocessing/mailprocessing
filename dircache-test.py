import dircache
import os
import sys
import time

dir_cache = {}
def caching_listdir(x):
    (cached_mtime, entries) = dir_cache.get(x, (-1, []))
    mtime = os.path.getmtime(x)
    if mtime != cached_mtime:
        entries = os.listdir(x)
        if mtime < time.time():
            dir_cache[x] = (mtime, entries)
    return entries

n = int(sys.argv[1])
d = sys.argv[2]

t0 = time.time()
for i in range(n):
    os.listdir(d)
print "os.listdir:", (time.time() - t0)

t0 = time.time()
for i in range(n):
    dircache.listdir(d)
print "dircache.listdir:", (time.time() - t0)

t0 = time.time()
for i in range(n):
    caching_listdir(d)
print "caching_listdir:", (time.time() - t0)
