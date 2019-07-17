# -*- coding: utf-8; mode: python -*-

# Copyright (C) 2006-2010 Joel Rosdahl <joel@rosdahl.net>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301, USA.

import fcntl
import hashlib
import os
import sys
import time

basestring = str


def offset_to_timezone(offset):
    if offset <= 0:
        sign = "+"
        offset = -offset
    else:
        sign = "-"
    return "{0}{1:0>2}{2:0>2}".format(
        sign, offset // 3600, (offset % 3600) // 60)


def iso_8601_now():
    now = time.time()
    milliseconds = int(1000 * (now - int(now)))
    first = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
    return "{0}.{1:0>3} {2}".format(
        first,
        milliseconds,
        offset_to_timezone(time.altzone))


def batch_list(to_batch, batchsize=1000):
    """
    Divide large lists. Returns a list of lists with batchsize or fewer items.
    """

    cur = 0
    batches = []

    while cur <= len(to_batch):
        increment = min(len(to_batch) - (cur - 1), batchsize)
        batches.append(to_batch[cur:cur + increment])
        cur += increment

    return batches


def sha1sum(fp):
    sha_obj = hashlib.sha1()
    while True:
        data = fp.read(4096)
        if not data:
            break
        sha_obj.update(data)
    return sha_obj.hexdigest()


def write_pidfile(pidfile):
    """
    Write and acquire a PID file this process' PID is recorded
    in pidfile must be a writeable, seekable file descriptor
    i.e. it must point to a regular file we've got write
    access to.
    """

    lock_acquired = False

    while not lock_acquired:
        try:
            fcntl.flock(pidfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            lock_acquired = True
        except OSError as e:
            print("Couldn't acquire lock on pid file %s, sleeping for 5s" % pidfile.name, file=sys.stderr)
        time.sleep(5)

    pidfile.seek(0)
    pidfile.truncate()
    print(os.getpid(), file=pidfile)
    pidfile.flush()


def safe_write(fp, s):
    line = s + "\n"
    try:
        fp.write(line)
    except UnicodeEncodeError:
        fp.write(ascii(line))
