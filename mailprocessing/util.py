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

import hashlib
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


def sha1sum(fp):
    sha_obj = hashlib.sha1()
    while True:
        data = fp.read(4096)
        if not data:
            break
        sha_obj.update(data)
    return sha_obj.hexdigest()


def safe_write(fp, s):
    line = s + "\n"
    try:
        fp.write(line)
    except UnicodeEncodeError:
        fp.write(ascii(line))
